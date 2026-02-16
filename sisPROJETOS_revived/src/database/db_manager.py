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
        
        # Table for Concessionaire Load Tables (Enel style)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS load_tables (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                concessionaire TEXT,
                conductor_name TEXT,
                span_m INTEGER,
                load_daN REAL,
                UNIQUE(concessionaire, conductor_name, span_m)
            )
        ''')

        conn.commit()
        conn.close()

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
