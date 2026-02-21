import pytest
from src.database.db_manager import DatabaseManager


class TestDatabaseSettings:
    def test_default_update_settings(self, tmp_path):
        db_path = tmp_path / "test_settings.db"
        db = DatabaseManager(db_path=str(db_path))

        settings = db.get_update_settings()

        assert settings["enabled"] is True
        assert settings["channel"] == "stable"
        assert settings["interval_days"] == 1

    def test_save_update_settings(self, tmp_path):
        db_path = tmp_path / "test_settings_save.db"
        db = DatabaseManager(db_path=str(db_path))

        db.save_update_settings(enabled=False, channel="beta", interval_days=7, last_checked="2026-02-17T12:00:00")
        settings = db.get_update_settings()

        assert settings["enabled"] is False
        assert settings["channel"] == "beta"
        assert settings["interval_days"] == 7
        assert settings["last_checked"] == "2026-02-17T12:00:00"

    def test_save_update_settings_partial(self, tmp_path):
        """Testa atualização parcial das configurações de update."""
        db_path = tmp_path / "test_partial.db"
        db = DatabaseManager(db_path=str(db_path))

        # Change only channel
        db.save_update_settings(channel="beta")
        settings = db.get_update_settings()

        assert settings["enabled"] is True  # Unchanged
        assert settings["channel"] == "beta"  # Changed

    def test_get_setting_default(self, tmp_path):
        """Testa valor padrão de configuração inexistente."""
        db_path = tmp_path / "test_default.db"
        db = DatabaseManager(db_path=str(db_path))

        val = db.get_setting("nonexistent_key", default="fallback")
        assert val == "fallback"

    def test_set_and_get_setting(self, tmp_path):
        """Testa definição e leitura de configuração."""
        db_path = tmp_path / "test_set_get.db"
        db = DatabaseManager(db_path=str(db_path))

        db.set_setting("my_key", "my_value")
        assert db.get_setting("my_key") == "my_value"

    def test_set_setting_overwrite(self, tmp_path):
        """Testa sobrescrita de configuração existente."""
        db_path = tmp_path / "test_overwrite.db"
        db = DatabaseManager(db_path=str(db_path))

        db.set_setting("my_key", "first_value")
        db.set_setting("my_key", "second_value")
        assert db.get_setting("my_key") == "second_value"

    def test_add_conductor(self, tmp_path):
        """Testa adição de novo condutor."""
        db_path = tmp_path / "test_conductor.db"
        db = DatabaseManager(db_path=str(db_path))

        success, msg = db.add_conductor({"name": "TestConductor", "weight": 0.5, "breaking": 1000})
        assert success is True
        assert "adicionado" in msg.lower()

    def test_add_conductor_duplicate(self, tmp_path):
        """Testa que condutor duplicado retorna erro."""
        db_path = tmp_path / "test_conductor_dup.db"
        db = DatabaseManager(db_path=str(db_path))

        db.add_conductor({"name": "DupConductor", "weight": 0.5, "breaking": 1000})
        success, msg = db.add_conductor({"name": "DupConductor", "weight": 0.5, "breaking": 1000})

        assert success is False
        assert "Erro" in msg

    def test_get_all_conductors(self, tmp_path):
        """Testa listagem de condutores pré-populados."""
        db_path = tmp_path / "test_conductors_list.db"
        db = DatabaseManager(db_path=str(db_path))

        conductors = db.get_all_conductors()
        assert isinstance(conductors, list)
        # Should have pre-populated Light conductors
        assert len(conductors) >= 4
        names = [row[0] for row in conductors]
        assert any("556MCM" in n for n in names)

    def test_get_all_conductors_includes_added(self, tmp_path):
        """Testa que condutor adicionado aparece na listagem."""
        db_path = tmp_path / "test_conductors_added.db"
        db = DatabaseManager(db_path=str(db_path))

        db.add_conductor({"name": "NewConductor_XYZ", "weight": 0.75, "breaking": 1500})
        conductors = db.get_all_conductors()
        names = [row[0] for row in conductors]
        assert "NewConductor_XYZ" in names

    def test_get_all_poles(self, tmp_path):
        """Testa listagem de postes (pode ser vazia se não pré-populado)."""
        db_path = tmp_path / "test_poles.db"
        db = DatabaseManager(db_path=str(db_path))

        poles = db.get_all_poles()
        assert isinstance(poles, list)

    def test_database_is_persistent(self, tmp_path):
        """Testa que dados persistem entre instâncias."""
        db_path = str(tmp_path / "test_persist.db")

        db1 = DatabaseManager(db_path=db_path)
        db1.set_setting("persistent_key", "persistent_value")

        db2 = DatabaseManager(db_path=db_path)
        val = db2.get_setting("persistent_key")
        assert val == "persistent_value"
