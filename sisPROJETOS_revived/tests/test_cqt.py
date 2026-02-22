"""
Testes do módulo cqt (Cálculo de Queda de Tensão e BDI).
"""

import pytest

from src.modules.cqt.logic import CQTLogic


class TestCQTLogic:
    """Suite de testes para CQTLogic."""

    @pytest.fixture
    def cqt(self):
        """Fixture que retorna uma instância de CQTLogic."""
        return CQTLogic()

    def test_init_has_required_attributes(self, cqt):
        """Testa que CQTLogic inicializa com atributos necessários."""
        assert hasattr(cqt, "db")
        assert hasattr(cqt, "UNIT_DIVISOR")
        assert hasattr(cqt, "TABELA_DEMANDA")
        assert hasattr(cqt, "CABOS_COEFS")
        assert cqt.UNIT_DIVISOR == 100.0
        assert cqt.CQT_LIMIT_PERCENT == pytest.approx(5.0)

    def test_tabela_demanda_structure(self, cqt):
        """Testa estrutura da tabela de demanda."""
        assert len(cqt.TABELA_DEMANDA) == 6
        for row in cqt.TABELA_DEMANDA:
            assert len(row) == 6  # (min, max, A, B, C, D)
            assert row[0] <= row[1]  # min <= max

    def test_get_cable_coefs_returns_dict(self, cqt):
        """Testa que get_cable_coefs retorna dicionário."""
        coefs = cqt.get_cable_coefs()
        assert isinstance(coefs, dict)
        assert len(coefs) > 0

    def test_get_cable_coefs_has_valid_values(self, cqt):
        """Testa que coeficientes são números positivos."""
        coefs = cqt.get_cable_coefs()
        for cabo, coef in coefs.items():
            assert isinstance(cabo, str)
            assert isinstance(coef, (int, float))
            assert coef > 0

    def test_get_fator_demanda_class_a(self, cqt):
        """Testa fator de demanda para classe A."""
        # 1-5 clientes classe A = 1.50
        fd = cqt.get_fator_demanda(3, "A")
        assert fd == 1.50

        # 6-10 clientes classe A = 1.20
        fd = cqt.get_fator_demanda(8, "A")
        assert fd == 1.20

    def test_get_fator_demanda_class_b(self, cqt):
        """Testa fator de demanda para classe B."""
        # 1-5 clientes classe B = 2.50
        fd = cqt.get_fator_demanda(5, "B")
        assert fd == 2.50

        # 11-20 clientes classe B = 1.60
        fd = cqt.get_fator_demanda(15, "B")
        assert fd == 1.60

    def test_get_fator_demanda_class_c(self, cqt):
        """Testa fator de demanda para classe C."""
        # 21-30 clientes classe C = 2.30
        fd = cqt.get_fator_demanda(25, "C")
        assert fd == 2.30

    def test_get_fator_demanda_class_d(self, cqt):
        """Testa fator de demanda para classe D."""
        # 31-50 clientes classe D = 3.00
        fd = cqt.get_fator_demanda(40, "D")
        assert fd == 3.00

    def test_get_fator_demanda_large_network(self, cqt):
        """Testa fator de demanda para rede grande (>50 clientes)."""
        # >50 clientes classe B = 0.80
        fd = cqt.get_fator_demanda(100, "B")
        assert fd == 0.80

    def test_get_fator_demanda_invalid_class(self, cqt):
        """Testa fator de demanda para classe inválida (default A)."""
        fd = cqt.get_fator_demanda(10, "X")
        # Deve retornar valor da classe A (1.20 para 6-10)
        assert fd == 1.20

    def test_validate_and_sort_empty_segments(self, cqt):
        """Testa validação com lista vazia."""
        valid, msg, order = cqt.validate_and_sort([])
        assert valid is False
        assert "Nenhum dado" in msg
        assert order == []

    def test_validate_and_sort_no_trafo(self, cqt):
        """Testa validação sem ponto TRAFO."""
        segments = [
            {"ponto": "P1", "montante": "P2"},
            {"ponto": "P2", "montante": "P3"},
        ]
        valid, msg, order = cqt.validate_and_sort(segments)
        assert valid is False
        assert "TRAFO" in msg

    def test_validate_and_sort_missing_montante(self, cqt):
        """Testa validação com montante ausente."""
        segments = [
            {"ponto": "TRAFO", "montante": ""},
            {"ponto": "P1", "montante": ""},  # Missing montante
        ]
        valid, msg, order = cqt.validate_and_sort(segments)
        assert valid is False
        assert "sem montante" in msg

    def test_validate_and_sort_valid_simple(self, cqt):
        """Testa validação com topologia simples válida."""
        segments = [
            {"ponto": "TRAFO", "montante": ""},
            {"ponto": "P1", "montante": "TRAFO"},
            {"ponto": "P2", "montante": "P1"},
        ]
        valid, msg, order = cqt.validate_and_sort(segments)
        assert valid is True
        assert msg == ""
        assert len(order) == 3
        assert order[0] == "TRAFO"
        assert order.index("TRAFO") < order.index("P1")
        assert order.index("P1") < order.index("P2")

    def test_validate_and_sort_branched_network(self, cqt):
        """Testa validação com rede ramificada."""
        segments = [
            {"ponto": "TRAFO", "montante": ""},
            {"ponto": "P1", "montante": "TRAFO"},
            {"ponto": "P2", "montante": "P1"},
            {"ponto": "P3", "montante": "P1"},  # Branch
        ]
        valid, msg, order = cqt.validate_and_sort(segments)
        assert valid is True
        assert len(order) == 4
        assert order[0] == "TRAFO"

    def test_calculate_empty_segments(self, cqt):
        """Testa cálculo com segmentos vazios."""
        result = cqt.calculate([], trafo_kva=75, social_class="B")
        assert result["success"] is False
        assert "error" in result

    def test_calculate_simple_network(self, cqt):
        """Testa cálculo com rede simples."""
        segments = [
            {
                "ponto": "TRAFO",
                "montante": "",
                "metros": 0,
                "cabo": "2#16(25)mm² Al",
                "mono": 0,
                "bi": 0,
                "tri": 0,
                "tri_esp": 0,
                "carga_esp": 0,
            },
            {
                "ponto": "P1",
                "montante": "TRAFO",
                "metros": 50,
                "cabo": "3x35+54.6mm² Al",
                "mono": 5,
                "bi": 3,
                "tri": 2,
                "tri_esp": 0,
                "carga_esp": 0,
            },
        ]
        result = cqt.calculate(segments, trafo_kva=75, social_class="B")

        assert result["success"] is True
        assert "results" in result
        assert "summary" in result
        assert "TRAFO" in result["results"]
        assert "P1" in result["results"]

    def test_calculate_summary_contains_required_fields(self, cqt):
        """Testa que summary contém campos obrigatórios."""
        segments = [
            {
                "ponto": "TRAFO",
                "montante": "",
                "metros": 0,
                "cabo": "2#16(25)mm² Al",
                "mono": 0,
                "bi": 0,
                "tri": 0,
                "tri_esp": 0,
                "carga_esp": 0,
            },
            {
                "ponto": "P1",
                "montante": "TRAFO",
                "metros": 100,
                "cabo": "3x50+54.6mm² Al",
                "mono": 10,
                "bi": 5,
                "tri": 3,
                "tri_esp": 1,
                "carga_esp": 5.0,
            },
        ]
        result = cqt.calculate(segments, trafo_kva=112.5, social_class="C")

        assert result["success"] is True
        summary = result["summary"]
        assert "fd" in summary
        assert "total_clients" in summary
        assert "max_cqt" in summary
        assert "total_kva" in summary

        # Validações
        assert summary["total_clients"] == 19  # 10+5+3+1
        assert summary["fd"] > 0
        assert summary["max_cqt"] >= 0

    def test_calculate_local_load_distribution(self, cqt):
        """Testa cálculo de carga local distribuída."""
        segments = [
            {
                "ponto": "TRAFO",
                "montante": "",
                "metros": 0,
                "cabo": "2#16(25)mm² Al",
                "mono": 0,
                "bi": 0,
                "tri": 0,
                "tri_esp": 0,
                "carga_esp": 0,
            },
            {
                "ponto": "P1",
                "montante": "TRAFO",
                "metros": 50,
                "cabo": "3x35+54.6mm² Al",
                "mono": 5,
                "bi": 0,
                "tri": 0,
                "tri_esp": 0,
                "carga_esp": 0,
            },
        ]
        result = cqt.calculate(segments, trafo_kva=75, social_class="A")

        assert result["success"] is True
        p1_data = result["results"]["P1"]
        # 5 clientes classe A = fd 1.50
        expected_local = 5 * 1.50
        assert abs(p1_data["local_dist"] - expected_local) < 0.01

    def test_calculate_accumulated_load(self, cqt):
        """Testa cálculo de carga acumulada."""
        segments = [
            {
                "ponto": "TRAFO",
                "montante": "",
                "metros": 0,
                "cabo": "2#16(25)mm² Al",
                "mono": 0,
                "bi": 0,
                "tri": 0,
                "tri_esp": 0,
                "carga_esp": 0,
            },
            {
                "ponto": "P1",
                "montante": "TRAFO",
                "metros": 50,
                "cabo": "3x35+54.6mm² Al",
                "mono": 5,
                "bi": 0,
                "tri": 0,
                "tri_esp": 0,
                "carga_esp": 0,
            },
            {
                "ponto": "P2",
                "montante": "P1",
                "metros": 50,
                "cabo": "3x35+54.6mm² Al",
                "mono": 5,
                "bi": 0,
                "tri": 0,
                "tri_esp": 0,
                "carga_esp": 0,
            },
        ]
        result = cqt.calculate(segments, trafo_kva=75, social_class="B")

        assert result["success"] is True
        # P2 deve ter apenas carga local
        # P1 deve ter carga local + carga de P2
        # TRAFO deve ter todas as cargas
        p2_accum = result["results"]["P2"]["accumulated"]
        p1_accum = result["results"]["P1"]["accumulated"]
        trafo_accum = result["results"]["TRAFO"]["accumulated"]

        assert p2_accum > 0
        assert p1_accum > p2_accum
        assert trafo_accum >= p1_accum

    def test_calculate_cqt_trecho(self, cqt):
        """Testa cálculo de CQT por trecho."""
        segments = [
            {
                "ponto": "TRAFO",
                "montante": "",
                "metros": 0,
                "cabo": "2#16(25)mm² Al",
                "mono": 0,
                "bi": 0,
                "tri": 0,
                "tri_esp": 0,
                "carga_esp": 0,
            },
            {
                "ponto": "P1",
                "montante": "TRAFO",
                "metros": 100,
                "cabo": "3x35+54.6mm² Al",
                "mono": 10,
                "bi": 0,
                "tri": 0,
                "tri_esp": 0,
                "carga_esp": 0,
            },
        ]
        result = cqt.calculate(segments, trafo_kva=75, social_class="B")

        assert result["success"] is True
        p1_data = result["results"]["P1"]
        assert "cqt_trecho" in p1_data
        assert p1_data["cqt_trecho"] >= 0

    def test_calculate_with_special_load(self, cqt):
        """Testa cálculo com carga especial pontual."""
        segments = [
            {
                "ponto": "TRAFO",
                "montante": "",
                "metros": 0,
                "cabo": "2#16(25)mm² Al",
                "mono": 0,
                "bi": 0,
                "tri": 0,
                "tri_esp": 0,
                "carga_esp": 0,
            },
            {
                "ponto": "P1",
                "montante": "TRAFO",
                "metros": 50,
                "cabo": "3x50+54.6mm² Al",
                "mono": 0,
                "bi": 0,
                "tri": 0,
                "tri_esp": 0,
                "carga_esp": 15.0,  # Carga pontual
            },
        ]
        result = cqt.calculate(segments, trafo_kva=75, social_class="B")

        assert result["success"] is True
        p1_data = result["results"]["P1"]
        assert p1_data["local_pontual"] == 15.0
        assert p1_data["total_local"] == 15.0

    def test_calculate_branched_network_topology(self, cqt):
        """Testa cálculo em rede ramificada."""
        segments = [
            {
                "ponto": "TRAFO",
                "montante": "",
                "metros": 0,
                "cabo": "2#16(25)mm² Al",
                "mono": 0,
                "bi": 0,
                "tri": 0,
                "tri_esp": 0,
                "carga_esp": 0,
            },
            {
                "ponto": "P1",
                "montante": "TRAFO",
                "metros": 50,
                "cabo": "3x35+54.6mm² Al",
                "mono": 5,
                "bi": 0,
                "tri": 0,
                "tri_esp": 0,
                "carga_esp": 0,
            },
            {
                "ponto": "P2",
                "montante": "P1",
                "metros": 50,
                "cabo": "3x35+54.6mm² Al",
                "mono": 3,
                "bi": 0,
                "tri": 0,
                "tri_esp": 0,
                "carga_esp": 0,
            },
            {
                "ponto": "P3",
                "montante": "P1",
                "metros": 50,
                "cabo": "3x35+54.6mm² Al",
                "mono": 2,
                "bi": 0,
                "tri": 0,
                "tri_esp": 0,
                "carga_esp": 0,
            },
        ]
        result = cqt.calculate(segments, trafo_kva=112.5, social_class="B")

        assert result["success"] is True
        assert len(result["results"]) == 4
        # P1 deve acumular cargas de P2 e P3
        p1_accum = result["results"]["P1"]["accumulated"]
        p2_total = result["results"]["P2"]["total_local"]
        p3_total = result["results"]["P3"]["total_local"]
        p1_total = result["results"]["P1"]["total_local"]

        assert abs(p1_accum - (p1_total + p2_total + p3_total)) < 0.01

    def test_calculate_case_insensitive_points(self, cqt):
        """Testa que pontos são case-insensitive."""
        segments = [
            {
                "ponto": "trafo",
                "montante": "",
                "metros": 0,
                "cabo": "2#16(25)mm² Al",
                "mono": 0,
                "bi": 0,
                "tri": 0,
                "tri_esp": 0,
                "carga_esp": 0,
            },
            {
                "ponto": "p1",
                "montante": "TRAFO",
                "metros": 50,
                "cabo": "3x35+54.6mm² Al",
                "mono": 5,
                "bi": 0,
                "tri": 0,
                "tri_esp": 0,
                "carga_esp": 0,
            },
        ]
        result = cqt.calculate(segments, trafo_kva=75, social_class="B")

        assert result["success"] is True
        # Deve ter normalizado para uppercase
        assert "TRAFO" in result["results"]
        assert "P1" in result["results"]

    def test_validate_and_sort_cycle_detection(self, cqt):
        """Testa detecção de ciclo na topologia."""
        # P1 → P2 → P1 (ciclo), sem TRAFO como raiz direta
        segments = [
            {"ponto": "TRAFO", "montante": ""},
            {"ponto": "P1", "montante": "P2"},
            {"ponto": "P2", "montante": "P1"},
        ]
        ok, msg, _ = cqt.validate_and_sort(segments)
        assert ok is False
        assert "Ciclo" in msg or "isolado" in msg

    def test_get_cable_coefs_db_exception(self, cqt, mocker):
        """Testa fallback de get_cable_coefs quando banco de dados lança exceção."""
        mocker.patch.object(cqt.db, "get_connection", side_effect=Exception("DB error"))
        coefs = cqt.get_cable_coefs()
        assert isinstance(coefs, dict)
        assert "2#16(25)mm² Al" in coefs
        assert coefs["2#16(25)mm² Al"] == pytest.approx(0.7779)
