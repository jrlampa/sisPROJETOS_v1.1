import json
import os
import sqlite3
from src.database.db_manager import DatabaseManager

def migrate():
    db = DatabaseManager()
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 1. Migrate Conductors from Catenaria JSON
    print("Migrating Conductors...")
    json_path = os.path.join(base_dir, "src", "modules", "catenaria", "resources", "condutores.json")
    if os.path.exists(json_path):
        with open(json_path, 'r', encoding='utf-8') as f:
            conductors = json.load(f)
            conn = db.get_connection()
            cursor = conn.cursor()
            for c in conductors:
                try:
                    cursor.execute('''
                        INSERT OR IGNORE INTO conductors (name, weight_kg_m, breaking_load_daN)
                        VALUES (?, ?, ?)
                    ''', (c['nome_cadastro'], c['P_kg_m'], c['T0_daN']))
                except Exception as e:
                    print(f"Error migrating conductor {c['nome_cadastro']}: {e}")
            conn.commit()
            conn.close()
    
    # 2. Migrate Poles from PoleLoad hardcoded data
    print("Migrating Poles...")
    poles_data = {
        "Concreto circular": {"9 m / 150 daN": 150, "9 m / 300 daN": 300, "11 m / 300 daN": 300, "11 m / 600 daN": 600, "11 m / 1000 daN": 1000, "11 m / 1500 daN": 1500, "12 m / 300 daN": 300, "12 m / 600 daN": 600, "12 m / 1000 daN": 1000, "12 m / 2000 daN": 2000, "15 m / 1000 daN": 1000, "18 m / 1000 daN": 1000},
        "Fibra de vidro circular": {"9 m / 300 daN": 300, "11 m / 300 daN": 300, "11 m / 600 daN": 600, "12 m / 600 daN": 600},
        "Concreto Duplo T": {"9 m / 300 daN": 300, "11 m / 300 daN": 300, "11 m / 600 daN": 600, "12 m / 600 daN": 600},
        "Metálico": {"7,5 m / 200 daN": 200}
    }
    
    conn = db.get_connection()
    cursor = conn.cursor()
    for material, models in poles_data.items():
        for desc, load in models.items():
            # Extract height if possible (simple split)
            height = float(desc.split(' ')[0].replace(',', '.'))
            cursor.execute('''
                INSERT OR IGNORE INTO poles (material, description, height_m, nominal_load_daN)
                VALUES (?, ?, ?, ?)
            ''', (material, desc, height, load))
    conn.commit()
    conn.close()
    
    print("Migration complete!")

if __name__ == "__main__":
    migrate()
