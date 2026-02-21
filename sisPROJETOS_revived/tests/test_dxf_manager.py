"""
Testes unitários para src/utils/dxf_manager.py.

Cobre:
- Validação de caminhos (segurança / path traversal)
- Criação de arquivos DXF de catenária
- Criação de arquivos DXF de pontos UTM
"""

import os
import pytest
import pandas as pd
import numpy as np

from src.utils.dxf_manager import DXFManager, _validate_output_path


# ---------------------------------------------------------------------------
# Testes de _validate_output_path
# ---------------------------------------------------------------------------

class TestValidateOutputPath:
    def test_valid_path_returns_resolved(self, tmp_path):
        filepath = str(tmp_path / "output.dxf")
        result = _validate_output_path(filepath)
        assert os.path.isabs(result)

    def test_empty_string_raises(self):
        with pytest.raises(ValueError, match="non-empty string"):
            _validate_output_path("")

    def test_none_raises(self):
        with pytest.raises(ValueError, match="non-empty string"):
            _validate_output_path(None)  # type: ignore

    def test_non_string_raises(self):
        with pytest.raises(ValueError, match="non-empty string"):
            _validate_output_path(123)  # type: ignore

    def test_null_byte_raises(self):
        with pytest.raises(ValueError, match="null bytes"):
            _validate_output_path("/tmp/file\x00.dxf")

    def test_valid_path_is_absolute(self, tmp_path):
        result = _validate_output_path(str(tmp_path / "test.dxf"))
        assert os.path.isabs(result)

    def test_relative_path_is_resolved(self):
        result = _validate_output_path("output.dxf")
        assert os.path.isabs(result)


# ---------------------------------------------------------------------------
# Testes de DXFManager.create_catenary_dxf
# ---------------------------------------------------------------------------

class TestCreateCatenaryDXF:
    def _make_catenary(self):
        """Gera dados de catenária simples para testes."""
        x_vals = list(np.linspace(0, 100, 20))
        sag = 2.5
        # Parábola simples: y = 4*sag/L^2 * x*(L-x)
        L = 100
        y_vals = [4 * sag / (L**2) * x * (L - x) for x in x_vals]
        return x_vals, y_vals, sag

    def test_creates_dxf_file(self, tmp_path):
        filepath = str(tmp_path / "catenary.dxf")
        x_vals, y_vals, sag = self._make_catenary()
        DXFManager.create_catenary_dxf(filepath, x_vals, y_vals, sag)
        assert os.path.exists(filepath)
        assert os.path.getsize(filepath) > 0

    def test_invalid_path_raises(self):
        with pytest.raises(ValueError):
            DXFManager.create_catenary_dxf("", [0, 1], [0, 1], 1.0)

    def test_null_byte_in_path_raises(self):
        with pytest.raises(ValueError, match="null bytes"):
            DXFManager.create_catenary_dxf("/tmp/bad\x00.dxf", [0, 1], [0, 1], 1.0)

    def test_file_is_valid_dxf(self, tmp_path):
        import ezdxf
        filepath = str(tmp_path / "catenary_valid.dxf")
        x_vals, y_vals, sag = self._make_catenary()
        DXFManager.create_catenary_dxf(filepath, x_vals, y_vals, sag)
        doc = ezdxf.readfile(filepath)
        assert doc is not None

    def test_minimal_two_points(self, tmp_path):
        filepath = str(tmp_path / "catenary_min.dxf")
        DXFManager.create_catenary_dxf(filepath, [0, 10], [0, 0], 0.5)
        assert os.path.exists(filepath)

    def test_sag_annotation_in_file(self, tmp_path):
        filepath = str(tmp_path / "catenary_sag.dxf")
        x_vals, y_vals, sag = self._make_catenary()
        DXFManager.create_catenary_dxf(filepath, x_vals, y_vals, sag)
        # Check annotation layer exists in DXF
        import ezdxf
        doc = ezdxf.readfile(filepath)
        layer_names = [layer.dxf.name for layer in doc.layers]
        assert "ANNOTATIONS" in layer_names
        assert "CATENARY_CURVE" in layer_names
        assert "SUPPORTS" in layer_names


# ---------------------------------------------------------------------------
# Testes de DXFManager.create_points_dxf
# ---------------------------------------------------------------------------

class TestCreatePointsDXF:
    def _make_dataframe(self):
        return pd.DataFrame({
            "Easting": [691000.0, 691050.0, 691100.0],
            "Northing": [7455000.0, 7455050.0, 7455100.0],
            "Name": ["P1", "P2", "P3"],
            "Elevation": [10.0, 11.0, 12.0],
        })

    def test_creates_dxf_file(self, tmp_path):
        filepath = str(tmp_path / "points.dxf")
        df = self._make_dataframe()
        DXFManager.create_points_dxf(filepath, df)
        assert os.path.exists(filepath)
        assert os.path.getsize(filepath) > 0

    def test_invalid_path_raises(self):
        with pytest.raises(ValueError):
            DXFManager.create_points_dxf("", pd.DataFrame())

    def test_null_byte_in_path_raises(self):
        with pytest.raises(ValueError, match="null bytes"):
            DXFManager.create_points_dxf("/tmp/bad\x00.dxf", pd.DataFrame())

    def test_file_is_valid_dxf(self, tmp_path):
        import ezdxf
        filepath = str(tmp_path / "points_valid.dxf")
        df = self._make_dataframe()
        DXFManager.create_points_dxf(filepath, df)
        doc = ezdxf.readfile(filepath)
        assert doc is not None

    def test_points_layer_exists(self, tmp_path):
        import ezdxf
        filepath = str(tmp_path / "points_layer.dxf")
        df = self._make_dataframe()
        DXFManager.create_points_dxf(filepath, df)
        doc = ezdxf.readfile(filepath)
        layer_names = [layer.dxf.name for layer in doc.layers]
        assert "POINTS" in layer_names

    def test_without_elevation_column(self, tmp_path):
        filepath = str(tmp_path / "points_no_elev.dxf")
        df = pd.DataFrame({
            "Easting": [691000.0, 691050.0],
            "Northing": [7455000.0, 7455050.0],
            "Name": ["A", "B"],
        })
        DXFManager.create_points_dxf(filepath, df)
        assert os.path.exists(filepath)
