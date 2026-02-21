import os
import shutil
import sqlite3
from typing import Any, Dict, List, Optional, Tuple

from utils import resource_path
from utils.logger import get_logger

logger = get_logger(__name__)


class DatabaseManager:
    """Gerenciador centralizado de banco de dados SQLite.

    Responsável por criar, inicializar e fornecer acesso ao banco de dados
    que armazena dados técnicos de condutores, postes, concessionárias e
    parâmetros de cálculo.
    """

    def __init__(self, db_path: Optional[str] = None) -> None:
        """Inicializa o gerenciador de banco de dados.

        Args:
            db_path: Caminho personalizado para o banco.
                Se None, usa AppData do usuário para escrita garantida.
        """
        if db_path is None:
            # Use AppData for writable database (supports PyInstaller bundled apps)
            appdata = os.getenv("APPDATA") or os.path.expanduser("~")
            app_dir = os.path.join(appdata, "sisPROJETOS")
            os.makedirs(app_dir, exist_ok=True)
            self.db_path = os.path.join(app_dir, "sisprojetos.db")

            # If DB doesn't exist, copy from resources or create fresh
            if not os.path.exists(self.db_path):
                resource_db = resource_path(os.path.join("src", "resources", "sisprojetos.db"))
                if os.path.exists(resource_db):
                    try:
                        shutil.copy2(resource_db, self.db_path)
                    except Exception as e:
                        logger.warning(f"Could not copy resource DB: {e}")
        else:
            self.db_path = db_path

        self.init_db()

    def get_connection(self) -> sqlite3.Connection:
        """Retorna uma conexão SQLite com o banco de dados.

        Returns:
            Conexão SQLite ativa.
        """
        return sqlite3.connect(self.db_path)

    def init_db(self) -> None:
        """Inicializa o schema do banco de dados se ainda não existir."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = self.get_connection()
        cursor = conn.cursor()

        # Table for Conductors
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conductors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                type TEXT, -- e.g., Nu, XLPE, CAA
                weight_kg_m REAL,
                breaking_load_daN REAL,
                modulus_elasticity REAL,
                coeff_thermal_expansion REAL,
                section_mm2 REAL,
                diameter_mm REAL
            )
        """)

        # Table for Poles
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS poles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                material TEXT NOT NULL, -- e.g., Concreto, Fibra, Madeira
                format TEXT, -- e.g., Circular, Duplo T
                description TEXT UNIQUE NOT NULL, -- e.g., 11 m / 600 daN
                height_m REAL,
                nominal_load_daN REAL
            )
        """)

        # Table for Concessionaires
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS concessionaires (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                method TEXT NOT NULL -- 'flecha' or 'tabela'
            )
        """)

        # Table for Network Definitions (links concessionaires to conductors)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS network_types (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                concessionaire_id INTEGER,
                name TEXT NOT NULL,
                FOREIGN KEY(concessionaire_id) REFERENCES concessionaires(id)
            )
        """)

        # Table for Cable technical coefficients/resistivity (Smart Backend)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cable_technical_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT, -- 'resistivity', 'cqt_k_coef', 'mechanical'
                key_name TEXT UNIQUE NOT NULL,
                value REAL NOT NULL,
                description TEXT
            )
        """)

        # Table for Load Tables (Pole Load calculations)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS load_tables (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                concessionaire TEXT NOT NULL,
                conductor_name TEXT NOT NULL,
                span_m INTEGER,
                load_daN REAL NOT NULL
            )
        """)

        # Table for generic application settings
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS app_settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        self.pre_populate_data(cursor)
        self._ensure_default_settings(cursor)

        conn.commit()
        conn.close()

    def _ensure_default_settings(self, cursor: sqlite3.Cursor) -> None:
        default_settings = [
            ("updates_enabled", "true"),
            ("update_channel", "stable"),
            ("update_last_checked", ""),
            ("update_check_interval_days", "1"),
            ("dark_mode", "false"),
        ]
        cursor.executemany("INSERT OR IGNORE INTO app_settings (key, value) VALUES (?, ?)", default_settings)

    def pre_populate_data(self, cursor: sqlite3.Cursor) -> None:
        """Pré-popula o banco com parâmetros técnicos iniciais de engenharia."""
        # 1. Concessionaires
        concessionaires = [("Light", "flecha"), ("Enel", "tabela")]
        cursor.executemany("INSERT OR IGNORE INTO concessionaires (name, method) VALUES (?, ?)", concessionaires)

        # 2. Resistivity & K Coefficients (Migrated from logic modules)
        # 3. Conductors (Light weights)
        light_conductors = [
            ("556MCM-CA, Nu", "CA", 0.779, 0, 0, 0, 0, 0),
            ("397MCM-CA, Nu", "CA", 0.558, 0, 0, 0, 0, 0),
            ("1/0AWG-CAA, Nu", "CAA", 0.217, 0, 0, 0, 0, 0),
            ("4 AWG-CAA, Nu", "CAA", 0.085, 0, 0, 0, 0, 0),
        ]
        cursor.executemany(
            "INSERT OR IGNORE INTO conductors (name, type, weight_kg_m, breaking_load_daN, modulus_elasticity, coeff_thermal_expansion, section_mm2, diameter_mm) VALUES (?,?,?,?,?,?,?,?)",
            light_conductors,
        )

        # 4. Load Tables (Enel)
        enel_data = [
            ("Enel", "1/0 CA", 20, 110),
            ("Enel", "1/0 CA", 30, 120),
            ("Enel", "1/0 CA", 40, 125),
            ("Enel", "1/0 CA", 50, 140),
            ("Enel", "1/0 CA", 60, 156),
            ("Enel", "1/0 CA", 70, 171),
            ("Enel", "1/0 CA", 80, 186),
            ("Enel", "BT 3x35+54.6", 0, 136),  # Tração fixa
        ]
        cursor.executemany(
            "INSERT OR IGNORE INTO load_tables (concessionaire, conductor_name, span_m, load_daN) VALUES (?, ?, ?, ?)",
            enel_data,
        )

        # 5. Cable Technical Data (CQT K Coefficients + Resistivity)
        cable_coefs = [
            ("cqt_k_coef", "2#16(25)mm² Al", 0.7779, "CQT coefficient for 2#16(25)mm² Al"),
            ("cqt_k_coef", "3x35+54.6mm² Al", 0.2416, "CQT coefficient for 3x35+54.6mm² Al"),
            ("cqt_k_coef", "3x50+54.6mm² Al", 0.1784, "CQT coefficient for 3x50+54.6mm² Al"),
            ("cqt_k_coef", "3x70+54.6mm² Al", 0.1248, "CQT coefficient for 3x70+54.6mm² Al"),
            ("cqt_k_coef", "3x95+54.6mm² Al", 0.0891, "CQT coefficient for 3x95+54.6mm² Al"),
            ("cqt_k_coef", "3x150+70mm² Al", 0.0573, "CQT coefficient for 3x150+70mm² Al"),
            # Resistivity values (ohm.mm²/m @ 20°C) — NBR 5410 / ABNT
            ("resistivity", "Alumínio", 0.0282, "Resistividade do alumínio (ohm.mm²/m)"),
            ("resistivity", "Cobre", 0.0175, "Resistividade do cobre (ohm.mm²/m)"),
        ]
        cursor.executemany(
            "INSERT OR IGNORE INTO cable_technical_data (category, key_name, value, description) VALUES (?, ?, ?, ?)",
            cable_coefs,
        )

        # 6. Poles (Catálogo básico de postes — ABNT NBR 8451 / 8452)
        poles = [
            # (material, format, description, height_m, nominal_load_daN)
            ("Concreto", "Circular", "11 m / 200 daN", 11.0, 200.0),
            ("Concreto", "Circular", "11 m / 400 daN", 11.0, 400.0),
            ("Concreto", "Circular", "11 m / 600 daN", 11.0, 600.0),
            ("Concreto", "Circular", "12 m / 300 daN", 12.0, 300.0),
            ("Concreto", "Circular", "12 m / 600 daN", 12.0, 600.0),
            ("Concreto", "Circular", "13 m / 600 daN", 13.0, 600.0),
            ("Concreto", "Duplo T", "11 m / 1000 daN", 11.0, 1000.0),
            ("Concreto", "Duplo T", "13 m / 1000 daN", 13.0, 1000.0),
            ("Fibra de Vidro", "Circular", "11 m / 200 daN", 11.0, 200.0),
            ("Fibra de Vidro", "Circular", "11 m / 400 daN", 11.0, 400.0),
            ("Fibra de Vidro", "Circular", "11 m / 600 daN", 11.0, 600.0),
            ("Madeira", "Roliço", "11 m / 300 daN", 11.0, 300.0),
            ("Madeira", "Roliço", "11 m / 600 daN", 11.0, 600.0),
        ]
        cursor.executemany(
            "INSERT OR IGNORE INTO poles (material, format, description, height_m, nominal_load_daN) VALUES (?, ?, ?, ?, ?)",
            poles,
        )

    def add_conductor(self, data: Dict[str, Any]) -> Tuple[bool, str]:
        """Adiciona um novo condutor ao banco de dados.

        Args:
            data: Dicionário com 'name', 'weight' e opcionalmente 'breaking'.

        Returns:
            Tupla (sucesso, mensagem).
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO conductors (name, weight_kg_m, breaking_load_daN)
                VALUES (?, ?, ?)
            """,
                (data["name"], data["weight"], data.get("breaking", 0)),
            )
            conn.commit()
            return True, "Condutor adicionado."
        except sqlite3.IntegrityError:
            return False, "Erro: Condutor já cadastrado."
        finally:
            conn.close()

    def get_all_conductors(self) -> List[Tuple]:
        """Retorna todos os condutores cadastrados.

        Returns:
            Lista de tuplas (name, weight_kg_m) ordenada por nome.
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name, weight_kg_m FROM conductors ORDER BY name")
        rows = cursor.fetchall()
        conn.close()
        return rows

    def get_all_poles(self) -> List[Tuple]:
        """Retorna todos os postes cadastrados.

        Returns:
            Lista de tuplas (material, format, description, nominal_load_daN).
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT material, format, description, nominal_load_daN FROM poles ORDER BY material, nominal_load_daN"
        )
        rows = cursor.fetchall()
        conn.close()
        return rows

    def get_all_concessionaires(self) -> List[Tuple]:
        """Retorna todas as concessionárias com nome e método de cálculo.

        Returns:
            Lista de tuplas (name, method) ordenada por nome.
        """
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT name, method FROM concessionaires ORDER BY name")
            return cursor.fetchall()
        finally:
            conn.close()

    def get_setting(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Retorna o valor de uma configuração persistida.

        Args:
            key: Chave da configuração.
            default: Valor padrão se a chave não existir.

        Returns:
            Valor da configuração ou default.
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM app_settings WHERE key = ?", (key,))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else default

    def set_setting(self, key: str, value: Any) -> None:
        """Persiste ou atualiza uma configuração no banco de dados.

        Args:
            key: Chave da configuração.
            value: Valor a persistir (convertido para str).
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO app_settings (key, value, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(key) DO UPDATE SET
                value = excluded.value,
                updated_at = CURRENT_TIMESTAMP
            """,
            (key, str(value)),
        )
        conn.commit()
        conn.close()

    def get_update_settings(self) -> Dict[str, Any]:
        """Retorna as configurações de verificação de atualizações.

        Returns:
            Dicionário com 'enabled', 'channel', 'last_checked', 'interval_days'.
        """
        return {
            "enabled": self.get_setting("updates_enabled", "true") == "true",
            "channel": self.get_setting("update_channel", "stable"),
            "last_checked": self.get_setting("update_last_checked", ""),
            "interval_days": int(self.get_setting("update_check_interval_days", "1") or "1"),
        }

    def save_update_settings(
        self,
        enabled: Optional[bool] = None,
        channel: Optional[str] = None,
        interval_days: Optional[int] = None,
        last_checked: Optional[str] = None,
    ) -> None:
        """Persiste as configurações de atualização no banco de dados.

        Args:
            enabled: Ativa/desativa a verificação de updates.
            channel: Canal de atualização ('stable' ou 'beta').
            interval_days: Intervalo em dias entre verificações.
            last_checked: Data/hora da última verificação (ISO 8601).
        """
        if enabled is not None:
            self.set_setting("updates_enabled", "true" if enabled else "false")
        if channel is not None:
            self.set_setting("update_channel", channel)
        if interval_days is not None:
            self.set_setting("update_check_interval_days", str(interval_days))
        if last_checked is not None:
            self.set_setting("update_last_checked", last_checked)

    def get_appearance_settings(self) -> dict:
        """Retorna as configurações de aparência da aplicação.

        Returns:
            dict: Dicionário com as configurações de aparência.
                  Chave 'dark_mode' é um booleano.
        """
        return {
            "dark_mode": self.get_setting("dark_mode", "false") == "true",
        }

    def save_appearance_settings(self, dark_mode: bool | None = None) -> None:
        """Persiste as configurações de aparência no banco de dados.

        Args:
            dark_mode: True para ativar modo escuro, False para desativar.
                       None mantém o valor atual.
        """
        if dark_mode is not None:
            self.set_setting("dark_mode", "true" if dark_mode else "false")
