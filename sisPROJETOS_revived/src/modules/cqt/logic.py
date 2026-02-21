from collections import defaultdict, deque
from typing import Any, Dict, List, Optional, Set, Tuple

from database.db_manager import DatabaseManager
from utils.logger import get_logger
from utils.sanitizer import sanitize_positive, sanitize_string

logger = get_logger(__name__)


class CQTLogic:
    """Lógica para cálculos de CQT (Custo de Qualidade Total) e BDI.

    Implementa metodologia de concessionárias brasileiras para cálculo de
    momento elétrico, fator de demanda, e dimensionamento de redes de distribuição.
    """

    def __init__(self) -> None:
        """Inicializa a lógica de CQT e carrega coeficientes do banco."""
        self.db = DatabaseManager()
        # UNIT_DIVISOR for meters to hectometers (Enel methodology)
        self.UNIT_DIVISOR: float = 100.0

        # DMDI Demand Table (From Enel CNS-OMBR-MAT-19-0285)
        # (Min, Max, Cls A, Cls B, Cls C, Cls D)
        self.TABELA_DEMANDA: List[Tuple[int, int, float, float, float, float]] = [
            (1, 5, 1.50, 2.50, 4.00, 6.00),
            (6, 10, 1.20, 2.00, 3.20, 5.00),
            (11, 20, 1.00, 1.60, 2.50, 4.00),
            (21, 30, 0.90, 1.40, 2.30, 3.50),
            (31, 50, 0.80, 1.20, 2.00, 3.00),
            (51, 9999, 0.50, 0.80, 1.30, 2.00),
        ]

        # Load cable coefficients
        self.CABOS_COEFS: Dict[str, float] = self.get_cable_coefs()

    def get_cable_coefs(self) -> Dict[str, float]:
        """Busca coeficientes de cabo no banco de dados.

        Returns:
            Dicionário {nome_cabo: coeficiente_k}.
        """
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT key_name, value FROM cable_technical_data WHERE category='cqt_k_coef'")
            rows = cursor.fetchall()
            conn.close()
            return {r[0]: r[1] for r in rows}
        except Exception:
            # Fallback
            return {
                "2#16(25)mm² Al": 0.7779,
                "3x35+54.6mm² Al": 0.2416,
                "3x50+54.6mm² Al": 0.1784,
                "3x70+54.6mm² Al": 0.1248,
                "3x95+54.6mm² Al": 0.0891,
                "3x150+70mm² Al": 0.0573,
            }

    def get_fator_demanda(self, client_count: int, social_class: str) -> float:
        """Retorna o fator de demanda DMDI conforme contagem e classe social.

        Args:
            client_count: Número total de unidades consumidoras.
            social_class: Classe social dominante (A, B, C ou D).

        Returns:
            Fator de demanda DMDI correspondente.
        """
        idx = {"A": 0, "B": 1, "C": 2, "D": 3}.get(social_class, 0)
        for mn, mx, *v in self.TABELA_DEMANDA:
            if mn <= client_count <= mx:
                return v[idx]
        return [0.5, 0.8, 1.3, 2.0][idx]

    def validate_and_sort(self, segments: List[Dict[str, Any]]) -> Tuple[bool, str, List[str]]:
        """Valida a topologia da rede e ordena os segmentos topologicamente.

        Args:
            segments: Lista de dicionários com 'ponto' e 'montante'.

        Returns:
            Tupla (válido, mensagem_de_erro, lista_ordenada_de_pontos).
        """
        if not segments:
            return False, "Nenhum dado fornecido.", []

        nodes: Set[str] = set()
        adj: Dict[str, List[str]] = defaultdict(list)
        in_degree: Dict[str, int] = defaultdict(int)

        for s in segments:
            p, m = str(s["ponto"]).upper(), str(s["montante"]).upper()
            nodes.add(p)
            if p != "TRAFO":
                if not m:
                    return False, f"Ponto '{p}' sem montante definido.", []
                adj[m].append(p)
                in_degree[p] += 1

        if "TRAFO" not in nodes:
            return False, "Ponto de origem 'TRAFO' não encontrado.", []

        # Topological sort (BFS)
        queue: deque[str] = deque(["TRAFO"])
        sorted_points: List[str] = []
        while queue:
            u = queue.popleft()
            sorted_points.append(u)
            for v in adj[u]:
                in_degree[v] -= 1
                if in_degree[v] == 0:
                    queue.append(v)

        if len(sorted_points) != len(nodes):
            return False, "Ciclo detectado ou pontos isolados na rede.", []

        return True, "", sorted_points

    def calculate(
        self,
        segments: List[Dict[str, Any]],
        trafo_kva: float,
        social_class: str = "B",
    ) -> Dict[str, Any]:
        """Orquestra o cálculo CQT/BDI para toda a rede.

        Args:
            segments: Lista de trechos com campos (ponto, montante, metros,
                      cabo, mono, bi, tri, tri_esp, carga_esp).
            trafo_kva: Potência do transformador em kVA (deve ser > 0).
            social_class: Classe social dominante (A, B, C ou D; padrão: B).

        Returns:
            Dicionário com 'success', 'results', 'summary' ou 'error'.
        """
        try:
            trafo_kva = sanitize_positive(trafo_kva)
            social_class = sanitize_string(social_class, max_length=1, allow_empty=False).upper()
            if social_class not in ("A", "B", "C", "D"):
                raise ValueError(f"Classe social inválida: '{social_class}'. Use A, B, C ou D.")
        except ValueError as e:
            logger.warning("Valor inválido em calculate (CQT): %s", e)
            return {"success": False, "error": str(e)}

        valid, msg, order = self.validate_and_sort(segments)
        if not valid:
            return {"success": False, "error": msg}

        # Index segments for fast lookup
        pmap = {str(s["ponto"]).upper(): s for s in segments}

        # 1. Calculate Local Loads
        total_clients = sum(
            s.get("mono", 0) + s.get("bi", 0) + s.get("tri", 0) + s.get("tri_esp", 0) for s in segments
        )
        fd = self.get_fator_demanda(total_clients, social_class)

        results: Dict[str, Any] = {}
        for p in order:
            s = pmap[p]
            p_mono = s.get("mono", 0)
            p_bi = s.get("bi", 0)
            p_tri = s.get("tri", 0)
            p_tri_esp = s.get("tri_esp", 0)

            carga_dist = (p_mono + p_bi + p_tri + p_tri_esp) * fd
            carga_pontual = s.get("carga_esp", 0.0)  # Simplified for now (no IP logic yet)

            results[p] = {
                "local_dist": carga_dist,
                "local_pontual": carga_pontual,
                "total_local": carga_dist + carga_pontual,
                "accumulated": 0.0,
                "cqt_trecho": 0.0,
                "cqt_accumulated": 0.0,
            }

        # 2. Accumulated Load (Bottom-Up)
        accum: Dict[str, float] = defaultdict(float)
        for p in reversed(order):
            accum[p] += results[p]["total_local"]
            pai = str(pmap[p]["montante"]).upper()
            if pai and pai in pmap:
                accum[pai] += accum[p]
            results[p]["accumulated"] = accum[p]

        # 3. Accumulated CQT (Top-Down)
        cqt_accum: Dict[str, float] = {"TRAFO": 0.0}
        for p in order:
            if p == "TRAFO":
                continue

            s = pmap[p]
            pai = str(s["montante"]).upper()

            # Momento: (Distribuída/2) + Pontual + Acumulada_Jusante
            carga_jusante = accum[p] - results[p]["total_local"]
            momento = (results[p]["local_dist"] / 2) + results[p]["local_pontual"] + carga_jusante

            cabo = s.get("cabo", "")
            coefs = self.get_cable_coefs()
            coef = coefs.get(cabo, 0.0)
            dist_hm = s.get("metros", 0.0) / self.UNIT_DIVISOR

            q_trecho = momento * dist_hm * coef
            results[p]["cqt_trecho"] = q_trecho
            results[p]["cqt_accumulated"] = cqt_accum.get(pai, 0.0) + q_trecho
            cqt_accum[p] = results[p]["cqt_accumulated"]

        return {
            "success": True,
            "results": results,
            "summary": {
                "fd": fd,
                "total_clients": total_clients,
                "max_cqt": max(r["cqt_accumulated"] for r in results.values()),
                "total_kva": results["TRAFO"]["accumulated"],
            },
        }
