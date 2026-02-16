import math
from database.db_manager import DatabaseManager

class PoleLoadLogic:
    def __init__(self):
        self.db = DatabaseManager()
        self.DADOS_POSTES_NOMINAL = {}
        self.load_poles()

    def get_concessionaires(self):
        """Returns list of concessionaire names from DB."""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM concessionaires")
            rows = cursor.fetchall()
            conn.close()
            return [r[0] for r in rows]
        except Exception:
            return ["Light", "Enel"] # Fallback

    def get_concessionaire_method(self, name):
        """Returns calculation method for a concessionaire."""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT method FROM concessionaires WHERE name=?", (name,))
            row = cursor.fetchone()
            conn.close()
            return row[0] if row else "flecha"
        except Exception:
            return "flecha"

    def load_poles(self):
        """Loads poles from SQLite database."""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT material, description, nominal_load_daN FROM poles")
            rows = cursor.fetchall()
            for r in rows:
                material, desc, load = r[0], r[1], r[2]
                if material not in self.DADOS_POSTES_NOMINAL:
                    self.DADOS_POSTES_NOMINAL[material] = {}
                self.DADOS_POSTES_NOMINAL[material][desc] = load
            conn.close()
        except Exception as e:
            print(f"Error loading poles from DB: {e}")

    def interpolar(self, tabela, vao):
        if not isinstance(tabela, dict): return 0
        vaos_conhecidos = sorted(tabela.keys())
        if not vaos_conhecidos: return 0
        
        if vao in vaos_conhecidos: return tabela[vao]
        if vao < vaos_conhecidos[0]: return tabela[vaos_conhecidos[0]]
        if vao > vaos_conhecidos[-1]: return tabela[vaos_conhecidos[-1]]

        for i in range(len(vaos_conhecidos) - 1):
            vao_inf, vao_sup = vaos_conhecidos[i], vaos_conhecidos[i+1]
            if vao_inf < vao < vao_sup:
                tracao_inf, tracao_sup = tabela[vao_inf], tabela[vao_sup]
                return tracao_inf + (tracao_sup - tracao_inf) * ((vao - vao_inf) / (vao_sup - vao_inf))
        return 0

    def calculate_resultant(self, concessionaria, condicao, cabos_input):
        metodo = self.get_concessionaire_method(concessionaria)
        fator_seguranca = {"Normal": 1.0, "Vento Forte": 1.5, "Gelo": 2.0}.get(condicao, 1.0)
        
        soma_vetor_x, soma_vetor_y = 0.0, 0.0
        details = []

        conn = self.db.get_connection()
        cursor = conn.cursor()

        for cable in cabos_input:
            tracao = 0
            rede = cable.get('rede', '')
            condutor = cable.get('condutor', '')
            vao = cable.get('vao', 0)
            angulo = cable.get('angulo', 0)
            
            if metodo == "flecha":
                flecha = cable.get('flecha', 1.0)
                # Fetch weight from conductors table
                cursor.execute("SELECT weight_kg_m FROM conductors WHERE name=?", (condutor,))
                row = cursor.fetchone()
                p_daN_m = row[0] if row else 0.5
                tracao = (p_daN_m * (vao**2)) / (8 * flecha)
            else:
                # Enel style: table lookup or fixed
                cursor.execute("SELECT span_m, load_daN FROM load_tables WHERE concessionaire=? AND conductor_name=?", (concessionaria, condutor))
                lookup = {r[0]: r[1] for r in cursor.fetchall()}
                if 0 in lookup: # Fixed tracion
                    tracao = lookup[0]
                else:
                    tracao = self.interpolar(lookup, vao)
            
            rad = math.radians(angulo)
            fx = tracao * math.cos(rad)
            fy = tracao * math.sin(rad)
            soma_vetor_x += fx
            soma_vetor_y += fy
            details.append({'name': condutor, 'tracao': tracao, 'angle': angulo, 'fx': fx, 'fy': fy})
        
        conn.close()

        mag = math.sqrt(soma_vetor_x**2 + soma_vetor_y**2) * fator_seguranca
        angle_res = math.degrees(math.atan2(soma_vetor_y, soma_vetor_x))
        if angle_res < 0: angle_res += 360
        
        return {
            'resultant_force': mag,
            'resultant_angle': angle_res,
            'vectors': details,
            'total_x': soma_vetor_x * fator_seguranca,
            'total_y': soma_vetor_y * fator_seguranca
        }

    def suggest_pole(self, resultant_force):
        """AI based suggestion: picks the most efficient pole for the load."""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT material, description, nominal_load_daN 
            FROM poles 
            WHERE nominal_load_daN >= ? 
            ORDER BY nominal_load_daN ASC, material ASC
        """, (resultant_force,))
        
        candidates = cursor.fetchall()
        conn.close()
        
        # Pick one per material
        best_per_material = {}
        for c in candidates:
            if c[0] not in best_per_material:
                best_per_material[c[0]] = {'material': c[0], 'description': c[1], 'load': c[2]}
        
        return list(best_per_material.values())
