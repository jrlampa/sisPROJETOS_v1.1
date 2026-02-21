import math
from typing import Any, Dict, Optional

from database.db_manager import DatabaseManager
from utils.logger import get_logger
from utils.sanitizer import sanitize_phases, sanitize_positive, sanitize_power_factor, sanitize_string

logger = get_logger(__name__)


class ElectricalLogic:
    """Lógica para cálculos elétricos de queda de tensão.

    Realiza cálculos de queda de tensão em circuitos elétricos
    considerando resistividade dos materiais, seção dos condutores
    e fator de potência, conforme NBR 5410.
    """

    def __init__(self) -> None:
        """Inicializa a lógica de cálculos elétricos."""
        self.db = DatabaseManager()

    def get_resistivity(self, material: str) -> float:
        """Busca resistividade do material no banco de dados.

        Args:
            material: Nome do material (ex: 'Alumínio', 'Cobre')

        Returns:
            Resistividade em ohm.mm²/m (padrão: 0.0282 para Al)
        """
        try:
            mat = sanitize_string(material, max_length=100, allow_empty=False)
            conn = self.db.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT value FROM cable_technical_data WHERE category='resistivity' AND key_name=?", (mat,)
            )
            row = cursor.fetchone()
            conn.close()
            return float(row[0]) if row else 0.0282  # Default to Al if not found
        except Exception:
            return 0.0282

    def calculate_voltage_drop(
        self,
        power_kw: float,
        distance_m: float,
        voltage_v: float,
        material: str,
        section_mm2: float,
        cos_phi: float = 0.92,
        phases: int = 3,
    ) -> Optional[Dict[str, Any]]:
        """Calcula a queda de tensão percentual conforme NBR 5410.

        Args:
            power_kw: Potência em quilowatts (deve ser > 0)
            distance_m: Distância em metros (deve ser > 0)
            voltage_v: Tensão em volts (deve ser > 0)
            material: Material do condutor (ex: 'Alumínio', 'Cobre')
            section_mm2: Seção transversal em mm² (deve ser > 0)
            cos_phi: Fator de potência (padrão 0,92; entre 0 e 1)
            phases: Número de fases (1 ou 3)

        Returns:
            Dicionário com resultados do cálculo ou None em caso de erro.
        """
        try:
            p = sanitize_positive(power_kw) * 1000
            distance = sanitize_positive(distance_m)
            v = sanitize_positive(voltage_v)
            s = sanitize_positive(section_mm2)
            phi = sanitize_power_factor(cos_phi)
            n_phases = sanitize_phases(phases)

            rho = self.get_resistivity(material)

            if n_phases == 3:
                current = p / (math.sqrt(3) * v * phi)
                resistance = rho * distance / s
                delta_v = math.sqrt(3) * current * resistance * phi
            else:
                current = p / (v * phi)
                resistance = rho * distance / s
                delta_v = 2 * current * resistance * phi

            percentage_drop = (delta_v / v) * 100

            return {
                "current": current,
                "delta_v_volts": delta_v,
                "percentage_drop": percentage_drop,
                "allowed": percentage_drop <= 5.0,
            }
        except (ValueError, ZeroDivisionError) as exc:
            logger.debug("Erro no cálculo de queda de tensão: %s", exc)
            return None
