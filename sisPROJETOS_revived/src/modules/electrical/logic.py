import math
from database.db_manager import DatabaseManager

class ElectricalLogic:
    """Lógica para cálculos elétricos de queda de tensão.
    
    Realiza cálculos de queda de tensão em circuitos elétricos
    considerando resistividade dos materiais, seção dos condutores
    e fator de potência, conforme NBR 5410.
    """
    
    def __init__(self):
        """Inicializa a lógica de cálculos elétricos."""
        self.db = DatabaseManager()

    def get_resistivity(self, material):
        """Busca resistividade do material no banco de dados.
        
        Args:
            material (str): Nome do material (ex: 'Alumínio', 'Cobre')
            
        Returns:
            float: Resistividade em ohm.mm²/m (padrão: 0.0282 para Al)
        """
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM cable_technical_data WHERE category='resistivity' AND key_name=?", (material,))
            row = cursor.fetchone()
            conn.close()
            return row[0] if row else 0.0282 # Default to Al if not found
        except Exception:
            return 0.0282

    def calculate_voltage_drop(self, power_kw, distance_m, voltage_v, material, section_mm2, cos_phi=0.92, phases=3):
        """Calculates the percentage voltage drop."""
        try:
            p = float(power_kw) * 1000
            l = float(distance_m)
            v = float(voltage_v)
            s = float(section_mm2)
            rho = self.get_resistivity(material)
            
            if phases == 3:
                current = p / (math.sqrt(3) * v * cos_phi)
                resistance = rho * l / s
                delta_v = math.sqrt(3) * current * resistance * cos_phi
            else:
                current = p / (v * cos_phi)
                resistance = rho * l / s
                delta_v = 2 * current * resistance * cos_phi
                
            percentage_drop = (delta_v / v) * 100
            
            return {
                'current': current,
                'delta_v_volts': delta_v,
                'percentage_drop': percentage_drop,
                'allowed': percentage_drop <= 5.0
            }
        except (ValueError, ZeroDivisionError):
            return None
