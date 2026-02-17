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
