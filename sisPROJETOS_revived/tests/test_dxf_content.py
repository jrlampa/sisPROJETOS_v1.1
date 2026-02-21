"""
Validação estrutural headless de arquivos DXF — sisPROJETOS.

Objetivo: verificar o conteúdo e a estrutura dos arquivos DXF gerados
pelo DXFManager sem depender de interface gráfica de CAD.

Estratégia de validação headless
---------------------------------
O AutoCAD fornece ``accoreconsole.exe`` para execução headless em Windows.
Em ambiente Linux/macOS (CI/Docker), a validação equivalente é feita com
a biblioteca ``ezdxf``, que lê e inspeciona qualquer arquivo DXF sem GUI,
com suporte a todas as versões desde R12 até R2018+.

Coordenadas de referência (fornecidas pelo cliente):
    - Ponto 1: UTM 23K  E=788547  N=7634925
    - Ponto 2: graus decimais  lat=-22.15018  lon=-42.92185
                → UTM 23S  E≈714315.7  N≈7549084.2  (pyproj EPSG:32723)

Vãos testados: 100 m, 500 m e 1000 m (NBR 5422).
"""

import os

import ezdxf
import numpy as np
import pandas as pd
import pytest

from src.modules.catenaria.logic import CatenaryLogic
from src.utils.dxf_manager import DXFManager

# ---------------------------------------------------------------------------
# Constantes de coordenadas de referência
# ---------------------------------------------------------------------------

# Ponto 1 — Google Earth Pro 23K 788547 7634925
UTM_P1_EASTING: float = 788547.0
UTM_P1_NORTHING: float = 7634925.0
UTM_P1_ELEVATION: float = 720.0  # altitude típica da região

# Ponto 2 — lat=-22.15018 lon=-42.92185 (convertido via pyproj EPSG:4326→32723)
UTM_P2_EASTING: float = 714315.7
UTM_P2_NORTHING: float = 7549084.2
UTM_P2_ELEVATION: float = 580.0

# Parâmetros de condutor típico (556MCM-CA — dados do banco)
CONDUCTOR_WEIGHT_KG_M: float = 1.60  # kg/m
CONDUCTOR_TENSION_DAN: float = 2000.0  # daN
SUPPORT_HEIGHT_M: float = 10.0  # metros


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def catenary_logic():
    """Instância de CatenaryLogic para os testes."""
    return CatenaryLogic()


@pytest.fixture
def two_point_df():
    """DataFrame com os dois pontos de referência do cliente."""
    return pd.DataFrame(
        {
            "Easting": [UTM_P1_EASTING, UTM_P2_EASTING],
            "Northing": [UTM_P1_NORTHING, UTM_P2_NORTHING],
            "Name": ["Ponto_1_23K", "Ponto_2_Decimal"],
            "Elevation": [UTM_P1_ELEVATION, UTM_P2_ELEVATION],
        }
    )


# ---------------------------------------------------------------------------
# Testes: conteúdo estrutural do DXF de pontos UTM (2.5D)
# ---------------------------------------------------------------------------


class TestDXFPointsStructure:
    """Valida estrutura e conteúdo do DXF de pontos UTM gerado por create_points_dxf."""

    def test_layer_points_exists_with_correct_color(self, tmp_path, two_point_df):
        """Layer POINTS deve existir com cor 1 (vermelho — convenção de levantamento)."""
        filepath = str(tmp_path / "pts.dxf")
        DXFManager.create_points_dxf(filepath, two_point_df)

        doc = ezdxf.readfile(filepath)
        layer = doc.layers.get("POINTS")
        assert layer is not None, "Layer 'POINTS' não encontrado"
        assert layer.dxf.color == 1, f"Cor da layer POINTS deve ser 1 (vermelho), encontrado: {layer.dxf.color}"

    def test_entity_count_matches_dataframe(self, tmp_path, two_point_df):
        """Número de entidades POINT no DXF deve coincidir com linhas do DataFrame."""
        filepath = str(tmp_path / "pts_count.dxf")
        DXFManager.create_points_dxf(filepath, two_point_df)

        doc = ezdxf.readfile(filepath)
        msp = doc.modelspace()
        points = list(msp.query("POINT"))
        assert len(points) == len(two_point_df), f"Esperado {len(two_point_df)} POINTs, encontrado {len(points)}"

    def test_text_labels_match_names(self, tmp_path, two_point_df):
        """Entidades TEXT devem conter os nomes dos pontos."""
        filepath = str(tmp_path / "pts_text.dxf")
        DXFManager.create_points_dxf(filepath, two_point_df)

        doc = ezdxf.readfile(filepath)
        msp = doc.modelspace()
        text_values = {t.dxf.text for t in msp.query("TEXT")}
        assert "Ponto_1_23K" in text_values, "Rótulo 'Ponto_1_23K' não encontrado no DXF"
        assert "Ponto_2_Decimal" in text_values, "Rótulo 'Ponto_2_Decimal' não encontrado no DXF"

    def test_2_5d_point_xy_coordinates_match_utm(self, tmp_path, two_point_df):
        """Posição XY dos POINTs deve corresponder às coordenadas UTM (precisão < 0.01 m)."""
        filepath = str(tmp_path / "pts_coords.dxf")
        DXFManager.create_points_dxf(filepath, two_point_df)

        doc = ezdxf.readfile(filepath)
        msp = doc.modelspace()
        points = sorted(list(msp.query("POINT")), key=lambda p: p.dxf.location.x)

        # Ponto 2 tem menor Easting (714315.7)
        assert abs(points[0].dxf.location.x - UTM_P2_EASTING) < 0.01
        assert abs(points[0].dxf.location.y - UTM_P2_NORTHING) < 0.01

        # Ponto 1 tem maior Easting (788547.0)
        assert abs(points[1].dxf.location.x - UTM_P1_EASTING) < 0.01
        assert abs(points[1].dxf.location.y - UTM_P1_NORTHING) < 0.01

    def test_2_5d_elevation_in_location_z(self, tmp_path, two_point_df):
        """Z da posição dos POINTs deve armazenar a altitude (2.5D survey — ABNT NBR 13133)."""
        filepath = str(tmp_path / "pts_z_elev.dxf")
        DXFManager.create_points_dxf(filepath, two_point_df)

        doc = ezdxf.readfile(filepath)
        msp = doc.modelspace()
        points = sorted(list(msp.query("POINT")), key=lambda p: p.dxf.location.x)

        # Ponto 2 → elevation=580.0 no Z
        assert abs(points[0].dxf.location.z - UTM_P2_ELEVATION) < 0.01

        # Ponto 1 → elevation=720.0 no Z
        assert abs(points[1].dxf.location.z - UTM_P1_ELEVATION) < 0.01

    def test_2_5d_text_placement_flat_in_xy_plane(self, tmp_path, two_point_df):
        """Rótulos TEXT devem estar em Z=0 (plano XY) para leitura limpa em vista em planta."""
        filepath = str(tmp_path / "pts_text_flat.dxf")
        DXFManager.create_points_dxf(filepath, two_point_df)

        doc = ezdxf.readfile(filepath)
        msp = doc.modelspace()
        texts = list(msp.query("TEXT"))
        assert len(texts) == 2, f"Esperado 2 TEXTs, encontrado {len(texts)}"
        for txt in texts:
            assert txt.dxf.insert.z == 0.0, f"TEXT deve ter Z=0 (plano XY, 2.5D), encontrado {txt.dxf.insert.z}"

    def test_dxf_version_is_r2010(self, tmp_path, two_point_df):
        """Versão do DXF gerado deve ser R2010 (compatibilidade BIM)."""
        filepath = str(tmp_path / "pts_ver.dxf")
        DXFManager.create_points_dxf(filepath, two_point_df)

        doc = ezdxf.readfile(filepath)
        assert doc.dxfversion == "AC1024", f"Esperado R2010 (AC1024), encontrado: {doc.dxfversion}"


# ---------------------------------------------------------------------------
# Testes: conteúdo estrutural do DXF de catenária por vão
# ---------------------------------------------------------------------------


class TestCatenaryDXFContent:
    """Valida DXF de catenária para 3 vãos padrão: 100 m, 500 m e 1000 m (NBR 5422)."""

    def _build_catenary_dxf(self, tmp_path: str, span: float, filename: str) -> ezdxf.document.Drawing:
        """Helper: calcula catenária, exporta DXF e lê de volta."""
        logic = CatenaryLogic()
        result = logic.calculate_catenary(
            span=span,
            ha=SUPPORT_HEIGHT_M,
            hb=SUPPORT_HEIGHT_M,
            tension_daN=CONDUCTOR_TENSION_DAN,
            weight_kg_m=CONDUCTOR_WEIGHT_KG_M,
        )
        assert result is not None, f"Cálculo de catenária para vão {span}m retornou None"

        dxf_path = os.path.join(str(tmp_path), filename)
        logic.export_dxf(dxf_path, result["x_vals"], result["y_vals"], result["sag"])
        return ezdxf.readfile(dxf_path), result

    # --- Camadas ---

    def test_required_layers_exist_100m(self, tmp_path):
        """Layers CATENARY_CURVE, SUPPORTS, ANNOTATIONS devem existir no DXF de 100m."""
        doc, _ = self._build_catenary_dxf(tmp_path, span=100.0, filename="cat_100m.dxf")
        layer_names = {layer.dxf.name for layer in doc.layers}
        assert "CATENARY_CURVE" in layer_names
        assert "SUPPORTS" in layer_names
        assert "ANNOTATIONS" in layer_names

    def test_catenary_curve_layer_color(self, tmp_path):
        """Layer CATENARY_CURVE deve ter cor 3 (verde — convenção de curvas de flecha)."""
        doc, _ = self._build_catenary_dxf(tmp_path, span=100.0, filename="cat_color.dxf")
        layer = doc.layers.get("CATENARY_CURVE")
        assert layer.dxf.color == 3, f"Cor esperada 3 (verde), encontrada: {layer.dxf.color}"

    # --- Entidades geométricas ---

    def test_lwpolyline_entity_exists(self, tmp_path):
        """Deve existir exatamente 1 LWPOLYLINE (curva da catenária)."""
        doc, _ = self._build_catenary_dxf(tmp_path, span=100.0, filename="cat_poly.dxf")
        msp = doc.modelspace()
        polylines = list(msp.query("LWPOLYLINE"))
        assert len(polylines) == 1, f"Esperado 1 LWPOLYLINE, encontrado {len(polylines)}"

    def test_pole_circles_exist(self, tmp_path):
        """Devem existir pelo menos 2 entidades CIRCLE (marcadores de postes)."""
        doc, _ = self._build_catenary_dxf(tmp_path, span=100.0, filename="cat_circles.dxf")
        msp = doc.modelspace()
        circles = list(msp.query("CIRCLE"))
        assert len(circles) >= 2, f"Esperado ≥2 CIRCLEs (postes), encontrado {len(circles)}"

    def test_sag_annotation_text_present(self, tmp_path):
        """Deve existir uma entidade TEXT com o valor da flecha ('Sag:')."""
        doc, _ = self._build_catenary_dxf(tmp_path, span=100.0, filename="cat_text.dxf")
        msp = doc.modelspace()
        sag_texts = [t for t in msp.query("TEXT") if "Sag:" in t.dxf.text]
        assert len(sag_texts) == 1, "TEXT com 'Sag:' não encontrado no DXF de catenária"

    def test_lwpolyline_has_100_points(self, tmp_path):
        """LWPOLYLINE deve ter exatamente 100 pontos (linspace padrão do CatenaryLogic)."""
        doc, _ = self._build_catenary_dxf(tmp_path, span=100.0, filename="cat_pts_count.dxf")
        msp = doc.modelspace()
        poly = list(msp.query("LWPOLYLINE"))[0]
        pts = [(p[0], p[1]) for p in poly]
        assert len(pts) == 100, f"Esperado 100 pontos, encontrado {len(pts)}"

    # --- Geometria por vão ---

    def test_span_length_100m(self, tmp_path):
        """Extensão horizontal da LWPOLYLINE deve ser ≈100 m para vão de 100m."""
        doc, _ = self._build_catenary_dxf(tmp_path, span=100.0, filename="span_100.dxf")
        msp = doc.modelspace()
        poly = list(msp.query("LWPOLYLINE"))[0]
        pts = [(p[0], p[1]) for p in poly]
        span_length = abs(pts[-1][0] - pts[0][0])
        assert abs(span_length - 100.0) < 0.1, f"Extensão esperada ≈100m, encontrada {span_length:.3f}m"

    def test_span_length_500m(self, tmp_path):
        """Extensão horizontal da LWPOLYLINE deve ser ≈500 m para vão de 500m."""
        doc, _ = self._build_catenary_dxf(tmp_path, span=500.0, filename="span_500.dxf")
        msp = doc.modelspace()
        poly = list(msp.query("LWPOLYLINE"))[0]
        pts = [(p[0], p[1]) for p in poly]
        span_length = abs(pts[-1][0] - pts[0][0])
        assert abs(span_length - 500.0) < 0.1, f"Extensão esperada ≈500m, encontrada {span_length:.3f}m"

    def test_span_length_1000m(self, tmp_path):
        """Extensão horizontal da LWPOLYLINE deve ser ≈1000 m para vão de 1000m."""
        doc, _ = self._build_catenary_dxf(tmp_path, span=1000.0, filename="span_1000.dxf")
        msp = doc.modelspace()
        poly = list(msp.query("LWPOLYLINE"))[0]
        pts = [(p[0], p[1]) for p in poly]
        span_length = abs(pts[-1][0] - pts[0][0])
        assert abs(span_length - 1000.0) < 0.1, f"Extensão esperada ≈1000m, encontrada {span_length:.3f}m"

    def test_sag_100m_reasonable_value(self, tmp_path):
        """Flecha para vão de 100m deve estar entre 0.1m e 5m (condutor típico, NBR 5422)."""
        _, result = self._build_catenary_dxf(tmp_path, span=100.0, filename="sag_100.dxf")
        sag = result["sag"]
        assert 0.1 <= sag <= 5.0, f"Flecha de 100m fora do range esperado: {sag:.3f}m"

    def test_sag_500m_greater_than_100m(self, tmp_path):
        """Flecha de 500m deve ser maior que a de 100m (vão maior → maior flecha)."""
        _, result_100 = self._build_catenary_dxf(tmp_path, span=100.0, filename="sag_cmp_100.dxf")
        _, result_500 = self._build_catenary_dxf(tmp_path, span=500.0, filename="sag_cmp_500.dxf")
        assert (
            result_500["sag"] > result_100["sag"]
        ), f"Flecha 500m ({result_500['sag']:.2f}m) deve ser maior que 100m ({result_100['sag']:.2f}m)"

    def test_sag_1000m_greater_than_500m(self, tmp_path):
        """Flecha de 1000m deve ser maior que a de 500m (monotônica com o vão)."""
        _, result_500 = self._build_catenary_dxf(tmp_path, span=500.0, filename="sag_cmp2_500.dxf")
        _, result_1000 = self._build_catenary_dxf(tmp_path, span=1000.0, filename="sag_cmp2_1000.dxf")
        assert (
            result_1000["sag"] > result_500["sag"]
        ), f"Flecha 1000m ({result_1000['sag']:.2f}m) deve ser maior que 500m ({result_500['sag']:.2f}m)"

    def test_sag_annotation_text_matches_calculation_100m(self, tmp_path):
        """Texto de anotação 'Sag: X.XXm' no DXF deve corresponder ao valor calculado (100m)."""
        doc, result = self._build_catenary_dxf(tmp_path, span=100.0, filename="sag_annot_100.dxf")
        msp = doc.modelspace()
        sag_texts = [t for t in msp.query("TEXT") if "Sag:" in t.dxf.text]
        assert len(sag_texts) == 1
        expected_text = f"Sag: {result['sag']:.2f}m"
        assert (
            sag_texts[0].dxf.text == expected_text
        ), f"Texto esperado '{expected_text}', encontrado '{sag_texts[0].dxf.text}'"

    def test_support_heights_at_span_ends(self, tmp_path):
        """Extremidades da curva (Y) devem ser iguais à altura dos apoios (vão nivelado)."""
        doc, result = self._build_catenary_dxf(tmp_path, span=100.0, filename="support_h.dxf")
        msp = doc.modelspace()
        poly = list(msp.query("LWPOLYLINE"))[0]
        pts = [(p[0], p[1]) for p in poly]
        assert abs(pts[0][1] - SUPPORT_HEIGHT_M) < 0.01, f"Altura inicial {pts[0][1]:.4f}m ≠ {SUPPORT_HEIGHT_M}m"
        assert abs(pts[-1][1] - SUPPORT_HEIGHT_M) < 0.01, f"Altura final {pts[-1][1]:.4f}m ≠ {SUPPORT_HEIGHT_M}m"

    def test_dxf_files_all_valid_for_three_spans(self, tmp_path):
        """DXF gerado para 100m, 500m e 1000m deve ser legível pelo ezdxf sem erros."""
        for span in (100.0, 500.0, 1000.0):
            fname = f"valid_{int(span)}m.dxf"
            doc, _ = self._build_catenary_dxf(tmp_path, span=span, filename=fname)
            assert doc is not None, f"DXF para vão {span}m não foi lido corretamente"
            assert doc.dxfversion >= "AC1015", f"Versão DXF insuficiente para vão {span}m"
