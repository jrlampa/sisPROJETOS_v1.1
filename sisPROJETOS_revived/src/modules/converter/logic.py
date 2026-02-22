import io
import zipfile
from typing import Any, Dict, List, Optional, Tuple

import ezdxf
import pandas as pd
from fastkml import kml
from pyproj import CRS, Transformer

from utils.logger import get_logger
from utils.sanitizer import sanitize_filepath

logger = get_logger(__name__)


class ConverterLogic:
    """Lógica para conversão de arquivos KMZ/KML para coordenadas UTM.

    Converte placemarks do Google Earth (KMZ/KML) para coordenadas UTM
    e exporta para Excel (XLSX), AutoCAD (DXF) ou CSV.
    """

    def __init__(self) -> None:
        """Inicializa o conversor de coordenadas."""
        pass

    def load_file(self, filepath: str) -> List[Any]:
        """Carrega arquivo KMZ ou KML e retorna lista de placemarks.

        Args:
            filepath: Caminho para o arquivo KML ou KMZ (validado pelo sanitizer).

        Returns:
            Lista de placemarks extraídos do arquivo.

        Raises:
            ValueError: Se o arquivo estiver vazio, sem placemarks ou inválido.
            FileNotFoundError: Se não encontrar arquivo KML no KMZ.
        """
        filepath = sanitize_filepath(filepath, allowed_extensions=[".kmz", ".kml"])
        try:
            if filepath.lower().endswith(".kmz"):
                with zipfile.ZipFile(filepath, "r") as zf:
                    # Find the KML file inside
                    kml_files = [f for f in zf.namelist() if f.endswith(".kml")]
                    if not kml_files:
                        raise FileNotFoundError("No KML file found in KMZ archive")
                    content = zf.read(kml_files[0])
            else:
                with open(filepath, "rb") as f:
                    content = f.read()

            return self.load_kml_content(content)

        except zipfile.BadZipFile:
            raise ValueError(f"Invalid KMZ file: {filepath}")
        except FileNotFoundError as exc:
            raise ValueError(str(exc)) from exc
        except ValueError:
            raise
        except Exception as e:  # pragma: no cover
            raise ValueError(f"Error loading file: {str(e)}")

    def load_kml_content(self, content: bytes) -> List[Any]:
        """Carrega placemarks diretamente de bytes KML (sem acesso a disco).

        Útil para processar conteúdo KML recebido via API (base64 decodificado)
        sem necessidade de criar arquivos temporários.

        Args:
            content: Conteúdo bruto do arquivo KML em bytes.

        Returns:
            Lista de placemarks extraídos.

        Raises:
            ValueError: Se o conteúdo estiver vazio ou sem placemarks válidos.
        """
        if not content:
            raise ValueError("KML file is empty")

        k = kml.KML()
        k.from_string(content)

        # Extract all placemarks recursively (handles nested Documents/Folders)
        # Compatible with both fastkml 0.x (method) and 1.x (property)
        features = k.features() if callable(k.features) else k.features
        placemarks = self._extract_placemarks(list(features))

        if not placemarks:
            raise ValueError("No features found in KML file")

        return placemarks

    def _extract_placemarks(self, features: List[Any], placemarks: Optional[List[Any]] = None) -> List[Any]:
        """Extrai placemarks recursivamente de uma estrutura KML.

        Processa estruturas aninhadas: Document → Folder → Placemark.
        Compatível com fastkml 0.x (método `features()`) e 1.x (propriedade `features`).

        Args:
            features: Lista de features KML a processar.
            placemarks: Acumulador de placemarks (None na primeira chamada).

        Returns:
            Lista de todos os placemarks encontrados recursivamente.
        """
        if placemarks is None:
            placemarks = []

        if not features:
            return placemarks

        for feature in features:
            try:
                # Check Document and Folder types
                if hasattr(feature, "features"):
                    # This is a Document or Folder - recurse into it
                    # Compatible with both fastkml 0.x (method) and 1.x (property)
                    sub_features = feature.features() if callable(feature.features) else feature.features
                    self._extract_placemarks(list(sub_features), placemarks)
                elif isinstance(feature, kml.Placemark):
                    # This is a Placemark - add it
                    placemarks.append(feature)
            except Exception:
                # Skip features that can't be processed
                continue

        return placemarks

    def convert_to_utm(self, placemarks: List[Any]) -> pd.DataFrame:
        """Converte placemarks para um DataFrame com coordenadas UTM.

        A projeção UTM é detectada automaticamente a partir das coordenadas
        geográficas de cada placemark (zona calculada a partir da longitude).

        Args:
            placemarks: Lista de placemarks KML a converter.

        Returns:
            DataFrame com colunas Name, Description, Type, Longitude, Latitude,
            Easting, Northing, Zone, Hemisphere, Elevation; coordenadas arredondadas
            a 3 casas decimais.

        Raises:
            ValueError: Se nenhum placemark fornecido ou geometrias inválidas.
        """
        if not placemarks:
            raise ValueError("No placemarks provided for conversion")

        data: List[Dict[str, Any]] = []
        skipped: List[str] = []

        for idx, p in enumerate(placemarks):
            try:
                # Validate placemark has geometry
                if not hasattr(p, "geometry"):
                    skipped.append(f"Placemark {idx+1}: Missing geometry attribute")
                    continue

                if p.geometry is None:
                    skipped.append(f"Placemark {idx+1} ('{getattr(p, 'name', 'Unnamed')}'): Geometry is None")
                    continue

                # Extract coordinates based on geometry type
                coords: Optional[List[Tuple[float, ...]]] = None
                geom_type: Optional[str] = None

                # Try Point geometry (most common)
                try:
                    if hasattr(p.geometry, "x") and hasattr(p.geometry, "y"):
                        x = float(p.geometry.x)
                        y = float(p.geometry.y)
                        z = 0

                        # Try to get z coordinate
                        if hasattr(p.geometry, "z") and p.geometry.z is not None:
                            try:
                                z = float(p.geometry.z)
                            except (ValueError, TypeError):
                                z = 0

                        coords = [(x, y, z)]
                        geom_type = "Point"
                except Exception:
                    pass

                # Try LineString/Polygon geometry
                if coords is None:
                    try:
                        if hasattr(p.geometry, "coords") and p.geometry.coords:
                            coords = []
                            for coord in p.geometry.coords:
                                try:
                                    if isinstance(coord, (tuple, list)) and len(coord) >= 2:
                                        x, y = float(coord[0]), float(coord[1])
                                        z = float(coord[2]) if len(coord) > 2 and coord[2] is not None else 0
                                        coords.append((x, y, z))
                                except (ValueError, TypeError, IndexError):
                                    continue

                            if coords:
                                geom_type = getattr(p.geometry, "geom_type", "LineString")
                    except Exception:
                        pass

                # If still no coords, try alternative geometry access (__geo_interface__)
                if coords is None and hasattr(p.geometry, "__geo_interface__"):
                    try:
                        geo = p.geometry.__geo_interface__
                        if geo.get("type") == "Point" and "coordinates" in geo:
                            coords_raw = geo["coordinates"]
                            coords = [
                                (
                                    float(coords_raw[0]),
                                    float(coords_raw[1]),
                                    float(coords_raw[2]) if len(coords_raw) > 2 else 0,
                                )
                            ]
                            geom_type = "Point"
                        elif geo.get("type") in ["LineString", "Polygon"] and "coordinates" in geo:
                            coords_raw = geo["coordinates"]
                            if geo.get("type") == "Polygon":
                                coords_raw = coords_raw[0]  # Use exterior ring only

                            coords = []
                            for coord in coords_raw:
                                if isinstance(coord, (tuple, list)) and len(coord) >= 2:
                                    coords.append(
                                        (float(coord[0]), float(coord[1]), float(coord[2]) if len(coord) > 2 else 0)
                                    )
                            geom_type = geo.get("type")
                    except Exception:
                        pass

                # Validate we got coords
                if not coords:
                    skipped.append(
                        f"Placemark {idx+1} ('{getattr(p, 'name', 'Unnamed')}'): Could not extract coordinates"
                    )
                    continue

                # Auto-detect UTM zone from first coordinate
                lon, lat = coords[0][0], coords[0][1]

                # Validate coordinates are reasonable
                if not (-180 <= lon <= 180 and -90 <= lat <= 90):
                    skipped.append(
                        f"Placemark {idx+1} ('{getattr(p, 'name', 'Unnamed')}'): Invalid coordinates ({lon}, {lat})"
                    )
                    continue

                utm_zone = int((lon + 180) / 6) + 1
                is_southern = lat < 0

                res_crs = CRS.from_dict({"proj": "utm", "zone": utm_zone, "south": is_southern, "ellps": "WGS84"})

                transformer = Transformer.from_crs("EPSG:4326", res_crs, always_xy=True)

                # Process each vertex (for LineStrings, this creates one row per vertex)
                for coord_idx, (lon, lat, z) in enumerate(coords):
                    try:
                        easting, northing = transformer.transform(float(lon), float(lat))
                        elev = float(z) if z else 0

                        # Round to 3 decimal places for precision
                        data.append(
                            {
                                "Name": getattr(p, "name", None) or f"Placemark_{idx+1}",
                                "Description": getattr(p, "description", "") or "",
                                "Type": geom_type or "Unknown",
                                "Longitude": round(float(lon), 6),
                                "Latitude": round(float(lat), 6),
                                "Easting": round(easting, 3),
                                "Northing": round(northing, 3),
                                "Zone": utm_zone,
                                "Hemisphere": "S" if is_southern else "N",
                                "Elevation": round(elev, 3),
                            }
                        )
                    except Exception as coord_error:
                        skipped.append(f"Placemark {idx+1} coord {coord_idx + 1}: {str(coord_error)}")
                        continue

            except Exception as placemark_error:
                skipped.append(f"Placemark {idx+1}: {str(placemark_error)}")
                continue

        # If nothing was converted, provide detailed error message
        if not data:
            error_msg = f"No valid geometries found in {len(placemarks)} placemark(s)."
            if skipped:
                error_msg += "\n\nProblemas encontrados:\n" + "\n".join(skipped[:5])
                if len(skipped) > 5:
                    error_msg += f"\n... e {len(skipped)-5} outros problemas"
            raise ValueError(error_msg)

        return pd.DataFrame(data)

    def save_to_excel(self, df: pd.DataFrame, filepath: str) -> None:
        """Exporta dados para arquivo Excel (.xlsx).

        Args:
            df: DataFrame com dados convertidos.
            filepath: Caminho do arquivo XLSX de saída (validado pelo sanitizer).

        Raises:
            ValueError: Se o caminho for inválido ou extensão não permitida.
        """
        filepath = sanitize_filepath(filepath, allowed_extensions=[".xlsx", ".xls"])
        df.to_excel(filepath, index=False)

    def save_to_dxf(self, df: pd.DataFrame, filepath: str) -> None:
        """Exporta dados para arquivo DXF (AutoCAD).

        Pontos viram entidades POINT; séries de pontos com mesmo nome
        viram POLYLINE3D. Todas as entidades ficam na layer POINTS ou LINES.

        Args:
            df: DataFrame com colunas Name, Easting, Northing, Elevation.
            filepath: Caminho do arquivo DXF de saída.

        Raises:
            ValueError: Se DataFrame vazio, colunas necessárias faltando ou caminho inválido.
        """
        filepath = sanitize_filepath(filepath, allowed_extensions=[".dxf"])
        # Validate DataFrame
        if df is None or df.empty:
            raise ValueError("DataFrame vazio. Carregue e converta um arquivo KML/KMZ primeiro.")

        # Validate required columns
        required_cols = ["Name", "Easting", "Northing", "Elevation"]
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Colunas necessárias faltando no DataFrame: {', '.join(missing_cols)}")

        doc = ezdxf.new("R2010")
        msp = doc.modelspace()

        grouped = df.groupby("Name")

        for name, group in grouped:
            # Ensure name is string
            name_str = str(name) if name is not None else "Unnamed"

            if len(group) == 1:
                # Point
                row = group.iloc[0]
                pos = (float(row["Easting"]), float(row["Northing"]), float(row["Elevation"]))
                msp.add_point(pos, dxfattribs={"layer": "POINTS"})
                msp.add_text(name_str, dxfattribs={"height": 2.0, "insert": pos, "layer": "POINTS"})
            else:
                # Line/Polyline
                points = [
                    (float(e), float(n), float(z))
                    for e, n, z in zip(group["Easting"], group["Northing"], group["Elevation"])
                ]
                msp.add_polyline3d(points, dxfattribs={"layer": "LINES"})
                msp.add_text(name_str, dxfattribs={"height": 2.0, "insert": points[0], "layer": "LINES"})

        doc.saveas(filepath)

    def save_to_dxf_to_buffer(self, df: pd.DataFrame) -> bytes:
        """Exporta dados para DXF em memória, sem gravar em disco.

        Pontos viram entidades POINT; séries de pontos com mesmo nome
        viram POLYLINE3D. Todas as entidades ficam na layer POINTS ou LINES.
        Útil para integração via API REST (retorno como Base64 JSON,
        conforme padrão /catenary/dxf).

        Args:
            df: DataFrame com colunas Name, Easting, Northing, Elevation.

        Returns:
            Conteúdo DXF como bytes UTF-8 prontos para codificação Base64.

        Raises:
            ValueError: Se DataFrame vazio ou colunas necessárias faltando.
        """
        if df is None or df.empty:
            raise ValueError("DataFrame vazio. Carregue e converta um arquivo KML/KMZ primeiro.")

        required_cols = ["Name", "Easting", "Northing", "Elevation"]
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Colunas necessárias faltando no DataFrame: {', '.join(missing_cols)}")

        doc = ezdxf.new("R2010")
        msp = doc.modelspace()

        grouped = df.groupby("Name")

        for name, group in grouped:
            name_str = str(name) if name is not None else "Unnamed"

            if len(group) == 1:
                row = group.iloc[0]
                pos = (float(row["Easting"]), float(row["Northing"]), float(row["Elevation"]))
                msp.add_point(pos, dxfattribs={"layer": "POINTS"})
                msp.add_text(name_str, dxfattribs={"height": 2.0, "insert": pos, "layer": "POINTS"})
            else:
                points = [
                    (float(e), float(n), float(z))
                    for e, n, z in zip(group["Easting"], group["Northing"], group["Elevation"])
                ]
                msp.add_polyline3d(points, dxfattribs={"layer": "LINES"})
                msp.add_text(name_str, dxfattribs={"height": 2.0, "insert": points[0], "layer": "LINES"})

        buf = io.StringIO()
        doc.write(buf)
        return buf.getvalue().encode("utf-8")

    def save_to_csv(self, df: pd.DataFrame, filepath: str) -> None:
        """Exporta dados para CSV com formato otimizado para projetos elétricos.

        Separador ';' (compatibilidade com Excel BR) e encoding UTF-8-sig
        (BOM para Excel reconhecer acentos).

        Args:
            df: DataFrame com dados convertidos.
            filepath: Caminho do arquivo CSV de saída.

        Raises:
            ValueError: Se o DataFrame estiver vazio ou o caminho for inválido.
        """
        filepath = sanitize_filepath(filepath, allowed_extensions=[".csv"])
        if df.empty:
            raise ValueError("Cannot export empty DataFrame to CSV")

        try:
            # Ordem padrão de colunas para CSV geoespacial
            columns_order = [
                "Name",
                "Description",
                "Type",
                "Longitude",
                "Latitude",
                "Easting",
                "Northing",
                "Elevation",
                "Zone",
                "Hemisphere",
            ]

            # Manter apenas colunas que existem no DataFrame
            cols_to_export = [col for col in columns_order if col in df.columns]

            # Exportar com separador ';' e UTF-8-sig (BOM para Excel)
            df[cols_to_export].to_csv(filepath, index=False, sep=";", encoding="utf-8-sig")

        except Exception as e:
            raise ValueError(f"Error saving CSV file: {str(e)}")
