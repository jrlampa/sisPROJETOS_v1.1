import numpy as np

from database.db_manager import DatabaseManager
from utils.logger import get_logger
from utils.sanitizer import sanitize_numeric, sanitize_positive

logger = get_logger(__name__)


class CatenaryLogic:
    """Lógica para cálculos de catenária de condutores.

    Realiza cálculos de flecha, tração e curva catenária para condutores
    de linhas aéreas de distribuição elétrica conforme NBR 5422.
    """

    def __init__(self):
        """Inicializa a lógica de catenária e carrega condutores do banco."""
        self.db = DatabaseManager()
        self.conductors = []
        self.load_conductors()

    def load_conductors(self):
        """Loads conductors from the SQLite database."""
        try:
            # We want full details for calculation
            conn = self.db.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT name, weight_kg_m, breaking_load_daN FROM conductors")
            rows = cursor.fetchall()
            self.conductors = [{"nome_cadastro": r[0], "P_kg_m": r[1], "T0_daN": r[2]} for r in rows]
            conn.close()
        except Exception as e:
            logger.exception(f"Error loading conductors from DB: {e}")
            self.conductors = []

    def get_conductor_names(self):
        """Retorna lista de nomes de condutores disponíveis.

        Returns:
            list: Lista de nomes de condutores cadastrados
        """
        return [c["nome_cadastro"] for c in self.conductors]

    def get_conductor_by_name(self, name):
        """Busca condutor por nome.

        Args:
            name (str): Nome do condutor

        Returns:
            dict or None: Dados do condutor ou None se não encontrado
        """
        for c in self.conductors:
            if c["nome_cadastro"] == name:
                return c
        return None

    def calculate_catenary(self, span, ha, hb, tension_daN, weight_kg_m):
        """
        Calculates catenary curve points and properties.

        Args:
            span (float): Horizontal distance (m).
            ha (float): Height of support A (m).
            hb (float): Height of support B (m).
            tension_daN (float): Horizontal tension (daN).
            weight_kg_m (float): Linear weight (kg/m).

        Returns:
            dict: {
                "sag": float,
                "x_vals": np.array,
                "y_vals": np.array,
                "tension": float,
                "catenary_constant": float
            }
            None: Se os dados de entrada forem inválidos ou peso linear for zero.
        """
        try:
            span = sanitize_positive(span)
            tension_daN = sanitize_positive(tension_daN)
            ha = sanitize_numeric(ha)
            hb = sanitize_numeric(hb)
            weight_kg_m = sanitize_numeric(weight_kg_m, min_val=0.0)
        except ValueError as e:
            logger.warning("Valor inválido em calculate_catenary: %s", e)
            return None

        # Convert kg/m to daN/m (1 kgf = 9.80665 N = 0.980665 daN)
        w_daN_m = weight_kg_m * 0.980665

        if w_daN_m == 0:
            return None

        # Constante catenária: a = T / w (NBR 5422)
        a = tension_daN / w_daN_m

        # Define x range
        x = np.linspace(0, span, 100)

        # Flecha de vão nivelado: f = a * (cosh(L/2a) - 1)
        sag_level = a * (np.cosh(span / (2 * a)) - 1)

        # Linha de corda entre os apoios A e B
        y_chord = ha + (hb - ha) * (x / span)

        # Curva catenária centrada no vão, deslocada para baixo da corda
        sag_curve = a * (np.cosh((x - span / 2) / a) - np.cosh(span / (2 * a)))

        y_final = y_chord + sag_curve

        return {"sag": sag_level, "x_vals": x, "y_vals": y_final, "tension": tension_daN, "catenary_constant": a}

    def export_dxf(self, filepath, x_vals, y_vals, sag):
        from utils.dxf_manager import DXFManager

        DXFManager.create_catenary_dxf(filepath, x_vals, y_vals, sag)
