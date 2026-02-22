"""
Testes de edge cases do módulo converter — separados para manter test_converter.py
abaixo do limite de 500 linhas (regra de modularidade do projeto).

Cobre: load_file (KMZ/KML) e convert_to_utm (geometrias variadas).
Exportação CSV/DXF em test_converter_export.py.
"""

import zipfile

import pandas as pd
import pytest

from src.modules.converter.logic import ConverterLogic

# ── Fixtures KML mínimas ─────────────────────────────────────────────────────

_MINIMAL_KML = b"""<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <Placemark>
      <name>P1</name>
      <Point><coordinates>-46.6333,-23.5505,720</coordinates></Point>
    </Placemark>
  </Document>
</kml>"""

_EMPTY_DOC_KML = b"""<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>Sem Placemarks</name>
  </Document>
</kml>"""


# ── TestConverterLoadFileEdgeCases ───────────────────────────────────────────


class TestConverterLoadFileEdgeCases:
    """Cobertura de edge cases do método load_file (KMZ, erros, vazio)."""

    @pytest.fixture
    def converter(self):
        return ConverterLogic()

    def test_load_valid_kmz(self, converter, tmp_path):
        """Testa carregamento de arquivo KMZ válido (cobre linhas 34-37)."""
        kmz_path = str(tmp_path / "test.kmz")
        with zipfile.ZipFile(kmz_path, "w") as zf:
            zf.writestr("doc.kml", _MINIMAL_KML)

        placemarks = converter.load_file(kmz_path)
        assert len(placemarks) >= 1

    def test_load_kmz_no_kml_inside(self, converter, tmp_path):
        """Testa KMZ sem arquivo KML interno (cobre linhas 37-39, 62-63)."""
        kmz_path = str(tmp_path / "nokml.kmz")
        with zipfile.ZipFile(kmz_path, "w") as zf:
            zf.writestr("readme.txt", b"no kml here")

        with pytest.raises(ValueError):
            converter.load_file(kmz_path)

    def test_load_kmz_bad_zip(self, converter, tmp_path):
        """Testa arquivo KMZ corrompido — não é um zip (cobre linhas 60-61)."""
        kmz_path = str(tmp_path / "bad.kmz")
        with open(kmz_path, "wb") as f:
            f.write(b"this is not a valid zip file at all")

        with pytest.raises(ValueError, match="Invalid KMZ file"):
            converter.load_file(kmz_path)

    def test_load_kml_empty_file(self, converter, tmp_path):
        """Testa arquivo KML vazio (cobre linha 45, 62-63)."""
        kml_path = str(tmp_path / "empty.kml")
        open(kml_path, "wb").close()

        with pytest.raises(ValueError):
            converter.load_file(kml_path)

    def test_load_kml_no_placemarks(self, converter, tmp_path):
        """Testa KML sem placemarks (cobre linha 56, 62-63)."""
        kml_path = str(tmp_path / "no_placemarks.kml")
        with open(kml_path, "wb") as f:
            f.write(_EMPTY_DOC_KML)

        with pytest.raises(ValueError):
            converter.load_file(kml_path)

    def test_load_file_invalid_extension_raises(self, converter, tmp_path):
        """Sanitizer: extensão inválida deve lançar ValueError."""
        bad_path = str(tmp_path / "arquivo.txt")
        with pytest.raises(ValueError, match="Extensão"):
            converter.load_file(bad_path)

    def test_load_file_null_byte_in_path_raises(self, converter):
        """Sanitizer: byte nulo no caminho deve lançar ValueError."""
        with pytest.raises(ValueError):
            converter.load_file("/tmp/file\x00.kml")


# ── TestConverterConvertToUTMEdgeCases ───────────────────────────────────────


class TestConverterConvertToUTMEdgeCases:
    """Cobertura de edge cases do método convert_to_utm e _extract_placemarks."""

    @pytest.fixture
    def converter(self):
        return ConverterLogic()

    def test_extract_placemarks_feature_exception(self, converter):
        """Cobre linhas 94-96: feature que lança exceção ao acessar sub-features."""

        class BrokenContainer:
            def features(self):
                raise RuntimeError("Broken feature")

        result = converter._extract_placemarks([BrokenContainer()])
        assert isinstance(result, list)

    def test_convert_placemark_no_geometry_attr(self, converter):
        """Cobre linhas 122-123: placemark sem atributo geometry."""

        class PlacemarkNoGeom:
            name = "SemGeometria"
            description = ""

        with pytest.raises(ValueError, match="No valid geometries"):
            converter.convert_to_utm([PlacemarkNoGeom()])

    def test_convert_placemark_none_geometry(self, converter):
        """Cobre linhas 126-127: placemark com geometry=None."""

        class PlacemarkNoneGeom:
            name = "GeometriaNula"
            description = ""
            geometry = None

        with pytest.raises(ValueError, match="No valid geometries"):
            converter.convert_to_utm([PlacemarkNoneGeom()])

    def test_convert_z_conversion_error_defaults_to_zero(self, converter):
        """Cobre linhas 144-145: erro na conversão de z usa 0 como padrão."""

        class MockGeomBadZ:
            x = -46.6333
            y = -23.5505
            z = "nao_e_numero"

        class MockPlacemark:
            name = "BadZ"
            description = ""
            geometry = MockGeomBadZ()

        df = converter.convert_to_utm([MockPlacemark()])
        assert len(df) == 1
        assert df.iloc[0]["Elevation"] == 0.0

    def test_convert_geometry_x_float_raises(self, converter):
        """Cobre linhas 149-150: TypeError ao converter p.geometry.x."""

        class MockGeomBadX:
            x = {"nao": "e_float"}
            y = -23.5505

        class MockPlacemark:
            name = "BadX"
            description = ""
            geometry = MockGeomBadX()

        with pytest.raises(ValueError, match="No valid geometries"):
            converter.convert_to_utm([MockPlacemark()])

    def test_convert_linestring_invalid_coord_value(self, converter):
        """Cobre linhas 163-164: ValueError em coord de LineString."""

        class MockGeomBadCoords:
            coords = [("nao_numero", -23.5505, 720)]

        class MockPlacemark:
            name = "BadCoords"
            description = ""
            geometry = MockGeomBadCoords()

        with pytest.raises(ValueError, match="No valid geometries"):
            converter.convert_to_utm([MockPlacemark()])

    def test_convert_linestring_coords_iteration_raises(self, converter):
        """Cobre linhas 168-169: RuntimeError ao iterar coords."""

        class BrokenIterable:
            def __bool__(self):
                return True

            def __iter__(self):
                raise RuntimeError("Iteração impossível")

        class MockGeomBrokenCoords:
            coords = BrokenIterable()

        class MockPlacemark:
            name = "BrokenCoords"
            description = ""
            geometry = MockGeomBrokenCoords()

        with pytest.raises(ValueError, match="No valid geometries"):
            converter.convert_to_utm([MockPlacemark()])

    def test_convert_geo_interface_point(self, converter):
        """Cobre linhas 176-184: extração via __geo_interface__ Point."""

        class MockGeomGeoIface:
            @property
            def __geo_interface__(self):
                return {"type": "Point", "coordinates": (-46.6333, -23.5505, 720.0)}

        class MockPlacemark:
            name = "GeoIfacePoint"
            description = ""
            geometry = MockGeomGeoIface()

        df = converter.convert_to_utm([MockPlacemark()])
        assert len(df) == 1
        assert df.iloc[0]["Name"] == "GeoIfacePoint"

    def test_convert_geo_interface_linestring(self, converter):
        """Cobre linhas 185-196: extração via __geo_interface__ LineString."""

        class MockGeomLineGI:
            @property
            def __geo_interface__(self):
                return {
                    "type": "LineString",
                    "coordinates": [(-46.6333, -23.5505, 720.0), (-46.6300, -23.5500, 725.0)],
                }

        class MockPlacemark:
            name = "GeoIfaceLine"
            description = ""
            geometry = MockGeomLineGI()

        df = converter.convert_to_utm([MockPlacemark()])
        assert len(df) == 2

    def test_convert_geo_interface_polygon(self, converter):
        """Cobre caminho de Polygon via __geo_interface__ (exterior ring)."""

        class MockGeomPolyGI:
            @property
            def __geo_interface__(self):
                return {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            (-46.634, -23.551, 720.0),
                            (-46.634, -23.549, 720.0),
                            (-46.629, -23.549, 720.0),
                            (-46.634, -23.551, 720.0),
                        ]
                    ],
                }

        class MockPlacemark:
            name = "GeoIfacePoly"
            description = ""
            geometry = MockGeomPolyGI()

        df = converter.convert_to_utm([MockPlacemark()])
        assert len(df) == 4

    def test_convert_geo_interface_exception(self, converter):
        """Cobre linhas 197-198: ValueError dentro do bloco __geo_interface__."""

        class MockGeomBadGI:
            @property
            def __geo_interface__(self):
                return {"type": "Point", "coordinates": ("nao_float", "tambem_nao")}

        class MockPlacemark:
            name = "BadGI"
            description = ""
            geometry = MockGeomBadGI()

        with pytest.raises(ValueError, match="No valid geometries"):
            converter.convert_to_utm([MockPlacemark()])

    def test_convert_no_coords_extracted(self, converter):
        """Cobre linhas 202-205: nenhuma estratégia de extração funciona."""

        class MockGeomVazio:
            # Sem atributos x/y, coords ou __geo_interface__ — nenhuma das
            # estratégias de extração consegue coordenadas desse objeto.
            pass

        class MockPlacemark:
            name = "SemCoordenadas"
            description = ""
            geometry = MockGeomVazio()

        with pytest.raises(ValueError, match="No valid geometries"):
            converter.convert_to_utm([MockPlacemark()])

    def test_convert_invalid_lat_lon_range(self, converter):
        """Cobre linhas 212-215: coordenadas fora do range válido (lon > 180)."""

        class MockGeomInvalid:
            x = 999.0
            y = 999.0
            z = None

        class MockPlacemark:
            name = "CoordsInvalidas"
            description = ""
            geometry = MockGeomInvalid()

        with pytest.raises(ValueError, match="No valid geometries"):
            converter.convert_to_utm([MockPlacemark()])

    def test_convert_transformer_raises(self, converter, mocker):
        """Cobre linhas 245-247: exceção no transformer.transform."""
        from pyproj import Transformer as PyProjTransformer

        mock_t = mocker.Mock()
        mock_t.transform.side_effect = RuntimeError("Projeção falhou")
        mocker.patch.object(PyProjTransformer, "from_crs", return_value=mock_t)

        class MockGeomPoint:
            x = -46.6333
            y = -23.5505
            z = None

        class MockPlacemark:
            name = "TransformFail"
            description = ""
            geometry = MockGeomPoint()

        with pytest.raises(ValueError, match="No valid geometries"):
            converter.convert_to_utm([MockPlacemark()])

    def test_convert_crs_creation_fails(self, converter, mocker):
        """Cobre linhas 249-251: exceção ao criar CRS para o placemark."""
        from pyproj import CRS

        mocker.patch.object(CRS, "from_dict", side_effect=RuntimeError("CRS inválido"))

        class MockGeomPoint:
            x = -46.6333
            y = -23.5505
            z = None

        class MockPlacemark:
            name = "CRSFail"
            description = ""
            geometry = MockGeomPoint()

        with pytest.raises(ValueError, match="No valid geometries"):
            converter.convert_to_utm([MockPlacemark()])

    def test_convert_many_skipped_shows_truncated_message(self, converter):
        """Cobre linhas 258-260: mensagem truncada quando há mais de 5 falhas."""

        class FailPlacemark:
            name = "Falha"
            description = ""
            geometry = None

        with pytest.raises(ValueError) as exc_info:
            converter.convert_to_utm([FailPlacemark() for _ in range(7)])

        assert "outros problemas" in str(exc_info.value)
