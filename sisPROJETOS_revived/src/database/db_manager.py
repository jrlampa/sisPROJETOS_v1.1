import sqlite3
import os
from utils import resource_path

class DatabaseManager:
    def __init__(self, db_path=None):
        if db_path is None:
            # Centralized resource path helper
            self.db_path = resource_path(os.path.join("src", "resources", "sisprojetos.db"))
        else:
            self.db_path = db_path
            
        self.init_db()

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    def init_db(self):
        """Initializes the database schema if it doesn't exist."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Table for Conductors
        cursor.execute('''
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
        ''')
        
        # Table for Poles
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS poles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                material TEXT NOT NULL, -- e.g., Concreto, Fibra, Madeira
                format TEXT, -- e.g., Circular, Duplo T
                description TEXT UNIQUE NOT NULL, -- e.g., 11 m / 600 daN
                height_m REAL,
                nominal_load_daN REAL
            )
        ''')
        
        # Table for Concessionaires
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS concessionaires (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                method TEXT NOT NULL -- 'flecha' or 'tabela'
            )
        ''')

        # Table for Network Definitions (links concessionaires to conductors)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS network_types (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                concessionaire_id INTEGER,
                name TEXT NOT NULL,
                FOREIGN KEY(concessionaire_id) REFERENCES concessionaires(id)
            )
        ''')

        # Table for Cable technical coefficients/resistivity (Smart Backend)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cable_technical_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT, -- 'resistivity', 'cqt_k_coef', 'mechanical'
                key_name TEXT UNIQUE NOT NULL,
                value REAL NOT NULL,
                description TEXT
            )
        ''')

        self.pre_populate_data(cursor)

        conn.commit()
        conn.close()

    def pre_populate_data(self, cursor):
        """Pre-populates the database with initial engineering parameters."""
        # 1. Concessionaires
        concessionaires = [('Light', 'flecha'), ('Enel', 'tabela')]
        cursor.executemany("INSERT OR IGNORE INTO concessionaires (name, method) VALUES (?, ?)", concessionaires)

        # 2. Resistivity & K Coefficients (Migrated from logic modules)
        # 3. Conductors (Light weights)
        light_conductors = [
            ('556MCM-CA, Nu', 'CA', 0.779, 0, 0, 0, 0, 0),
            ('397MCM-CA, Nu', 'CA', 0.558, 0, 0, 0, 0, 0),
            ('1/0AWG-CAA, Nu', 'CAA', 0.217, 0, 0, 0, 0, 0),
            ('4 AWG-CAA, Nu', 'CAA', 0.085, 0, 0, 0, 0, 0)
        ]
        cursor.executemany("INSERT OR IGNORE INTO conductors (name, type, weight_kg_m, breaking_load_daN, modulus_elasticity, coeff_thermal_expansion, section_mm2, diameter_mm) VALUES (?,?,?,?,?,?,?,?)", light_conductors)

        # 4. Load Tables (Enel)
        enel_data = [
            ('Enel', '1/0 CA', 20, 110), ('Enel', '1/0 CA', 30, 120), ('Enel', '1/0 CA', 40, 125),
            ('Enel', '1/0 CA', 50, 140), ('Enel', '1/0 CA', 60, 156), ('Enel', '1/0 CA', 70, 171),
            ('Enel', '1/0 CA', 80, 186),
            ('Enel', 'BT 3x35+54.6', 0, 136) # Tração fixa
        ]
        cursor.executemany("INSERT OR IGNORE INTO load_tables (concessionaire, conductor_name, span_m, load_daN) VALUES (?, ?, ?, ?)", enel_data)

    def add_conductor(self, data):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO conductors (name, weight_kg_m, breaking_load_daN)
                VALUES (?, ?, ?)
            ''', (data['name'], data['weight'], data.get('breaking', 0)))
            conn.commit()
            return True, "Condutor adicionado."
        except sqlite3.IntegrityError:
            return False, "Erro: Condutor já cadastrado."
        finally:
            conn.close()

    def get_all_conductors(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name, weight_kg_m FROM conductors ORDER BY name")
        rows = cursor.fetchall()
        conn.close()
        return rows

    def get_all_poles(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT material, format, description, nominal_load_daN FROM poles ORDER BY material, nominal_load_daN")
        rows = cursor.fetchall()
        conn.close()
        return rows
