import zipfile
import pandas as pd
import ezdxf
from pyproj import CRS, Transformer
from fastkml import kml


class ConverterLogic:
    """Lógica para conversão de arquivos KMZ/KML para coordenadas UTM.

    Converte placemarks do Google Earth (KMZ/KML) para coordenadas UTM
    e exporta para Excel (XLSX), AutoCAD (DXF) ou CSV.
    """

    def __init__(self):
        """Inicializa o conversor de coordenadas."""
        pass

    def load_file(self, filepath):
        """Loads KMZ or KML file and returns features.

        Args:
            filepath: Path to KML or KMZ file

        Returns:
            List of placemarks extracted from the file

        Raises:
            ValueError: If file is empty or contains no KML data
            FileNotFoundError: If KML file not found in KMZ archive
        """
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

            if not content:
                raise ValueError("KML file is empty")

            k = kml.KML()
            k.from_string(content)

            # Extract all placemarks recursively (handles nested Documents/Folders)
            placemarks = self._extract_placemarks(list(k.features))

            if not placemarks:
                raise ValueError("No features found in KML file")

            return placemarks

        except zipfile.BadZipFile:
            raise ValueError(f"Invalid KMZ file: {filepath}")
        except Exception as e:
            raise ValueError(f"Error loading file: {str(e)}")

    def _extract_placemarks(self, features, placemarks=None):
        """Recursively extracts placemarks from KML features.

        Handles nested structures: Document → Folder → Placemark

        Args:
            features: List of KML features to process
            placemarks: Accumulator list for placemarks (default: None)

        Returns:
            List of all placemarks found recursively
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
                    self._extract_placemarks(list(feature.features), placemarks)
                elif isinstance(feature, kml.Placemark):
                    # This is a Placemark - add it
                    placemarks.append(feature)
            except Exception:
                # Skip features that can't be processed
                continue

        return placemarks

    def convert_to_utm(self, placemarks):
        """Converts placemarks to a DataFrame with UTM coordinates.

        Args:
            placemarks: List of KML placemarks

        Returns:
            pandas.DataFrame with converted coordinates (rounded to 3 decimals)

        Raises:
            ValueError: If no valid placemarks provided or geometries are malformed
        """
        if not placemarks:
            raise ValueError("No placemarks provided for conversion")

        data = []
        skipped = []

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
                coords = None
                geom_type = None

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

    def save_to_excel(self, df, filepath):
        df.to_excel(filepath, index=False)

    def save_to_dxf(self, df, filepath):
        """Exporta dados para arquivo DXF (AutoCAD).

        Args:
            df: DataFrame com dados convertidos
            filepath: Caminho do arquivo DXF de saída

        Raises:
            ValueError: Se DataFrame vazio ou colunas necessárias faltando
        """
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

    def save_to_csv(self, df, filepath):
        """Exporta dados para CSV com formato otimizado para projetos elétricos.

        Args:
            df: DataFrame com dados convertidos
            filepath: Caminho do arquivo CSV de saída

        Features:
            - Separador: ';' (ponto e vírgula) para compatibilidade com Excel BR
            - Encoding: UTF-8-sig (com BOM para Excel)
            - Precisão: Coordenadas já arredondadas em 3 casas decimais
            - Ordem: Colunas organizadas logicamente

        Raises:
            ValueError: If DataFrame is empty
        """
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
