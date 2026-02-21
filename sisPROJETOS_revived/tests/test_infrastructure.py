"""
Testes da camada de infraestrutura (DDD) — adaptadores SQLite de repositório.

Verifica que os adaptadores concretos:
1. Satisfazem os Protocolos de domínio (isinstance check)
2. Mapeiam corretamente tuplas SQLite para entidades de domínio
3. Retornam entidades válidas com dados reais pré-populados
4. Ignoram/filtram registros incompletos (breaking_load=0 ou NULL)
5. Retornam None / lista vazia quando não há dados
6. Integram corretamente com os serviços de domínio

Referências:
    - ABNT NBR 7271:2004 — Condutores de alumínio para linhas aéreas
    - ABNT NBR 8451:2011 — Postes de concreto armado
"""

import os
import tempfile

import pytest

from database.db_manager import DatabaseManager
from domain.entities import Concessionaire, Conductor, Pole
from domain.repositories import ConcessionaireRepository, ConductorRepository, PoleRepository
from domain.services import CatenaryDomainService, VoltageDropDomainService
from infrastructure.repositories import (
    SQLiteConcessionaireRepository,
    SQLiteConductorRepository,
    SQLitePoleRepository,
)


@pytest.fixture
def db(tmp_path):
    """DatabaseManager com banco SQLite em disco temporário (dados reais pré-populados)."""
    return DatabaseManager(str(tmp_path / "infra_test.db"))


@pytest.fixture
def conductor_repo(db):
    return SQLiteConductorRepository(db)


@pytest.fixture
def pole_repo(db):
    return SQLitePoleRepository(db)


@pytest.fixture
def concessionaire_repo(db):
    return SQLiteConcessionaireRepository(db)


# ─────────────────────────────────────────────────────────────────────────────
# Conformidade de Protocolo (isinstance checks)
# ─────────────────────────────────────────────────────────────────────────────


class TestProtocolCompliance:
    """Verifica que os adaptadores satisfazem os Protocolos de domínio."""

    def test_conductor_repo_satisfies_protocol(self, conductor_repo):
        assert isinstance(conductor_repo, ConductorRepository)

    def test_pole_repo_satisfies_protocol(self, pole_repo):
        assert isinstance(pole_repo, PoleRepository)

    def test_concessionaire_repo_satisfies_protocol(self, concessionaire_repo):
        assert isinstance(concessionaire_repo, ConcessionaireRepository)


# ─────────────────────────────────────────────────────────────────────────────
# SQLiteConductorRepository
# ─────────────────────────────────────────────────────────────────────────────


class TestSQLiteConductorRepository:
    """Testes do adaptador SQLite para condutores."""

    def test_get_all_returns_list(self, conductor_repo):
        result = conductor_repo.get_all()
        assert isinstance(result, list)

    def test_get_all_returns_conductor_entities(self, conductor_repo):
        conductors = conductor_repo.get_all()
        assert all(isinstance(c, Conductor) for c in conductors)

    def test_get_all_returns_four_pre_populated_conductors(self, conductor_repo):
        """Banco pré-populado tem exatamente 4 condutores Light com dados completos."""
        conductors = conductor_repo.get_all()
        assert len(conductors) == 4

    def test_get_all_contains_556mcm(self, conductor_repo):
        names = [c.name for c in conductor_repo.get_all()]
        assert any("556MCM" in n for n in names)

    def test_get_all_contains_397mcm(self, conductor_repo):
        names = [c.name for c in conductor_repo.get_all()]
        assert any("397MCM" in n for n in names)

    def test_get_all_contains_1_0awg(self, conductor_repo):
        names = [c.name for c in conductor_repo.get_all()]
        assert any("1/0AWG" in n for n in names)

    def test_get_all_contains_4awg(self, conductor_repo):
        names = [c.name for c in conductor_repo.get_all()]
        assert any("4 AWG" in n for n in names)

    def test_556mcm_breaking_load_is_7080(self, conductor_repo):
        """ABNT NBR 7271: carga de ruptura da 556MCM-CA deve ser 7 080 daN."""
        conductors = conductor_repo.get_all()
        conductor = next(c for c in conductors if "556MCM" in c.name)
        assert conductor.breaking_load_daN == pytest.approx(7080.0)

    def test_556mcm_weight_is_0779(self, conductor_repo):
        conductors = conductor_repo.get_all()
        conductor = next(c for c in conductors if "556MCM" in c.name)
        assert conductor.weight_kg_m == pytest.approx(0.779)

    def test_556mcm_section_is_281_7(self, conductor_repo):
        conductors = conductor_repo.get_all()
        conductor = next(c for c in conductors if "556MCM" in c.name)
        assert conductor.section_mm2 == pytest.approx(281.7)

    def test_1_0awg_breaking_load_is_5430(self, conductor_repo):
        """ABNT NBR 7271: carga de ruptura do 1/0AWG-CAA deve ser 5 430 daN."""
        conductors = conductor_repo.get_all()
        conductor = next(c for c in conductors if "1/0AWG" in c.name)
        assert conductor.breaking_load_daN == pytest.approx(5430.0)

    def test_get_by_name_returns_correct_conductor(self, conductor_repo):
        c = conductor_repo.get_by_name("556MCM-CA, Nu")
        assert c is not None
        assert c.name == "556MCM-CA, Nu"
        assert c.breaking_load_daN == pytest.approx(7080.0)

    def test_get_by_name_returns_none_for_unknown(self, conductor_repo):
        assert conductor_repo.get_by_name("CONDUTOR_INEXISTENTE") is None

    def test_get_by_name_returns_none_for_empty_string(self, conductor_repo):
        assert conductor_repo.get_by_name("") is None

    def test_incomplete_conductor_is_filtered_out(self, db, conductor_repo):
        """Condutor com breaking_load=0 não deve aparecer em get_all()."""
        conn = db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO conductors (name, weight_kg_m, breaking_load_daN) VALUES (?,?,?)",
                ("CONDUTOR_SEM_CARGA", 0.5, 0),
            )
            conn.commit()
        finally:
            conn.close()

        conductors = conductor_repo.get_all()
        names = [c.name for c in conductors]
        assert "CONDUTOR_SEM_CARGA" not in names

    def test_get_by_name_returns_none_for_incomplete_conductor(self, db):
        """get_by_name filtra condutor com breaking_load=0."""
        conn = db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO conductors (name, weight_kg_m, breaking_load_daN) VALUES (?,?,?)",
                ("INCOMPLETO", 0.3, 0),
            )
            conn.commit()
        finally:
            conn.close()

        repo = SQLiteConductorRepository(db)
        assert repo.get_by_name("INCOMPLETO") is None

    def test_conductor_with_negative_weight_is_filtered(self, db):
        """Condutor com weight_kg_m negativo passa a checagem de breaking_load mas falha na criação da entidade — cobre branch de ValueError em _row_to_entity (linha 108)."""
        conn = db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO conductors (name, weight_kg_m, breaking_load_daN) VALUES (?,?,?)",
                ("PESO_NEGATIVO", -0.5, 100.0),
            )
            conn.commit()
        finally:
            conn.close()

        # get_all deve ignorar este registro (ValueError na criação da entidade)
        repo = SQLiteConductorRepository(db)
        names = [c.name for c in repo.get_all()]
        assert "PESO_NEGATIVO" not in names

        # get_by_name também deve retornar None
        assert repo.get_by_name("PESO_NEGATIVO") is None


# ─────────────────────────────────────────────────────────────────────────────
# SQLitePoleRepository
# ─────────────────────────────────────────────────────────────────────────────


class TestSQLitePoleRepository:
    """Testes do adaptador SQLite para postes."""

    def test_get_all_returns_list(self, pole_repo):
        assert isinstance(pole_repo.get_all(), list)

    def test_get_all_returns_pole_entities(self, pole_repo):
        poles = pole_repo.get_all()
        assert all(isinstance(p, Pole) for p in poles)

    def test_get_all_returns_all_13_pre_populated_poles(self, pole_repo):
        """Banco pré-populado deve ter exatamente 13 postes (todos materiais)."""
        poles = pole_repo.get_all()
        assert len(poles) == 13

    def test_get_all_contains_concreto(self, pole_repo):
        materials = [p.material for p in pole_repo.get_all()]
        assert "Concreto" in materials

    def test_get_all_contains_fibra_de_vidro(self, pole_repo):
        materials = [p.material for p in pole_repo.get_all()]
        assert "Fibra de Vidro" in materials

    def test_get_all_contains_madeira(self, pole_repo):
        materials = [p.material for p in pole_repo.get_all()]
        assert "Madeira" in materials

    def test_concreto_pole_height_is_valid(self, pole_repo):
        """ABNT NBR 8451: postes de concreto devem ter height_m > 0."""
        concreto = [p for p in pole_repo.get_all() if p.material == "Concreto"]
        assert all(p.height_m > 0 for p in concreto)

    def test_concreto_200dan_pole_exists(self, pole_repo):
        concreto = [p for p in pole_repo.get_all() if p.material == "Concreto"]
        assert any(p.nominal_load_daN == 200.0 for p in concreto)

    def test_suggest_by_force_returns_list(self, pole_repo):
        assert isinstance(pole_repo.suggest_by_force(100.0), list)

    def test_suggest_by_force_returns_pole_entities(self, pole_repo):
        poles = pole_repo.suggest_by_force(100.0)
        assert all(isinstance(p, Pole) for p in poles)

    def test_suggest_by_force_250dan_finds_adequate_poles(self, pole_repo):
        """Força de 250 daN: deve sugerir postes com carga >= 250 daN."""
        poles = pole_repo.suggest_by_force(250.0)
        assert len(poles) > 0
        assert all(p.nominal_load_daN >= 250.0 for p in poles)

    def test_suggest_by_force_ordered_ascending(self, pole_repo):
        """Postes sugeridos devem estar ordenados por carga crescente."""
        poles = pole_repo.suggest_by_force(100.0)
        loads = [p.nominal_load_daN for p in poles]
        assert loads == sorted(loads)

    def test_suggest_by_force_very_high_force_returns_empty(self, pole_repo):
        poles = pole_repo.suggest_by_force(999_999.0)
        assert poles == []

    def test_suggest_by_force_exactly_200dan(self, pole_repo):
        """Força exata de 200 daN: postes de 200 daN devem aparecer."""
        poles = pole_repo.suggest_by_force(200.0)
        assert any(p.nominal_load_daN == 200.0 for p in poles)

    def test_suggest_by_force_201dan_excludes_200dan_pole(self, pole_repo):
        """Força de 201 daN: postes de 200 daN NÃO devem aparecer."""
        poles = pole_repo.suggest_by_force(201.0)
        assert all(p.nominal_load_daN >= 201.0 for p in poles)

    def test_pole_with_zero_height_is_filtered(self, db):
        """Poste com height_m=0 deve ser filtrado pelo early-return em _row_to_entity (linha 200)."""
        conn = db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO poles (material, format, description, height_m, nominal_load_daN) VALUES (?,?,?,?,?)",
                ("Concreto", "Circular", "Poste Altura Zero", 0.0, 200.0),
            )
            conn.commit()
        finally:
            conn.close()

        repo = SQLitePoleRepository(db)
        # O poste com height_m=0 não deve aparecer em get_all()
        poles = repo.get_all()
        descriptions_from_db = [p.material for p in poles]
        # Verifica que a contagem total permanece 13 (não adiciona o inválido)
        assert len(poles) == 13


# ─────────────────────────────────────────────────────────────────────────────
# SQLiteConcessionaireRepository
# ─────────────────────────────────────────────────────────────────────────────


class TestSQLiteConcessionaireRepository:
    """Testes do adaptador SQLite para concessionárias."""

    def test_get_all_returns_list(self, concessionaire_repo):
        assert isinstance(concessionaire_repo.get_all(), list)

    def test_get_all_returns_concessionaire_entities(self, concessionaire_repo):
        concessionaires = concessionaire_repo.get_all()
        assert all(isinstance(c, Concessionaire) for c in concessionaires)

    def test_get_all_returns_two_pre_populated_concessionaires(self, concessionaire_repo):
        assert len(concessionaire_repo.get_all()) == 2

    def test_get_all_contains_light(self, concessionaire_repo):
        names = [c.name for c in concessionaire_repo.get_all()]
        assert "Light" in names

    def test_get_all_contains_enel(self, concessionaire_repo):
        names = [c.name for c in concessionaire_repo.get_all()]
        assert "Enel" in names

    def test_light_method_is_flecha(self, concessionaire_repo):
        concessionaires = concessionaire_repo.get_all()
        light = next(c for c in concessionaires if c.name == "Light")
        assert light.method == "flecha"

    def test_enel_method_is_tabela(self, concessionaire_repo):
        concessionaires = concessionaire_repo.get_all()
        enel = next(c for c in concessionaires if c.name == "Enel")
        assert enel.method == "tabela"

    def test_get_by_name_light(self, concessionaire_repo):
        light = concessionaire_repo.get_by_name("Light")
        assert light is not None
        assert light.name == "Light"
        assert light.method == "flecha"

    def test_get_by_name_enel(self, concessionaire_repo):
        enel = concessionaire_repo.get_by_name("Enel")
        assert enel is not None
        assert enel.method == "tabela"

    def test_get_by_name_returns_none_for_unknown(self, concessionaire_repo):
        assert concessionaire_repo.get_by_name("CONCESSIONARIA_INEXISTENTE") is None

    def test_get_by_name_case_sensitive(self, concessionaire_repo):
        """Busca é case-sensitive (SQLite padrão)."""
        assert concessionaire_repo.get_by_name("light") is None

    def test_concessionaire_with_invalid_method_is_filtered(self, db):
        """Concessionária com método inválido é filtrada por ValueError em _row_to_entity (linha 286)."""
        conn = db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO concessionaires (name, method) VALUES (?,?)",
                ("ConcessionariaInvalida", "metodo_invalido"),
            )
            conn.commit()
        finally:
            conn.close()

        repo = SQLiteConcessionaireRepository(db)
        # A concessionária inválida não deve aparecer em get_all()
        names = [c.name for c in repo.get_all()]
        assert "ConcessionariaInvalida" not in names
        # E get_by_name deve retornar None para ela
        assert repo.get_by_name("ConcessionariaInvalida") is None


# ─────────────────────────────────────────────────────────────────────────────
# Integração DDD: Repository → Entity → Domain Service
# ─────────────────────────────────────────────────────────────────────────────


class TestInfrastructureDomainIntegration:
    """Testa a integração end-to-end entre repositório, entidade e serviço de domínio."""

    def test_conductor_to_catenary_service(self, conductor_repo):
        """Condutor do repositório → CatenaryDomainService calcula flecha correta."""
        conductors = conductor_repo.get_all()
        conductor = next(c for c in conductors if "556MCM" in c.name)

        svc = CatenaryDomainService()
        # Vão de 100 m, tensão de 2000 daN, alturas iguais (10 m)
        result = svc.calculate(
            conductor=conductor,
            span=100.0,
            tension_daN=2000.0,
            ha=10.0,
            hb=10.0,
        )

        assert result.sag >= 0.1  # flecha mínima esperada
        assert result.sag <= 10.0  # flecha máxima razoável para 100 m
        # Constante catenária: a = T / (w × 0.980665) — conversão kg → daN (NBR 5422)
        expected_constant = 2000.0 / (conductor.weight_kg_m * 0.980665)
        assert result.catenary_constant == pytest.approx(expected_constant, rel=1e-4)

    def test_conductor_to_voltage_drop_service(self, conductor_repo):
        """Condutor do repositório → VoltageDropDomainService calcula queda correta."""
        conductors = conductor_repo.get_all()
        # Usa 1/0AWG-CAA com section_mm2=53.5 para calcular queda de tensão
        conductor = next(c for c in conductors if "1/0AWG" in c.name)
        assert conductor.section_mm2 is not None

        svc = VoltageDropDomainService()
        result = svc.calculate(
            material="Alumínio",
            resistivity=0.0282,
            length_m=100.0,
            power_kw=10.0,
            section_mm2=conductor.section_mm2,
            voltage_v=220.0,
            phases=1,
            cos_phi=0.92,
        )

        assert result.drop_percent >= 0.0
        assert result.drop_percent < 100.0

    def test_pole_suggestion_returns_domain_entities_for_catenary_force(self, conductor_repo, pole_repo):
        """Calcula força via CatenaryService e usa como input para sugestão de postes."""
        conductors = conductor_repo.get_all()
        conductor = next(c for c in conductors if "556MCM" in c.name)

        svc = CatenaryDomainService()
        catenary = svc.calculate(
            conductor=conductor,
            span=200.0,
            tension_daN=1000.0,
            ha=11.0,
            hb=11.0,
        )

        # Usa a tensão de tração como força para sugestão de postes
        # (simplificado — em produção seria a resultante real do PoleLoadLogic)
        poles = pole_repo.suggest_by_force(catenary.tension)
        assert isinstance(poles, list)
        # Com tension_daN=1000 e catálogo com postes até 1000 daN, deve haver sugestões
        assert len(poles) > 0
