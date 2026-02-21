import os

from dotenv import load_dotenv
from groq import Groq

from utils import resource_path
from utils.logger import get_logger
from utils.sanitizer import sanitize_string

logger = get_logger(__name__)


class AIAssistantLogic:
    """Lógica do assistente de IA via Groq API (LLaMA 3.3).

    Consulta técnica especializada em engenharia de redes de distribuição
    elétrica, com suporte a contexto de projeto e histórico de conversa.
    """

    def __init__(self):
        """Inicializa o assistente de IA carregando credenciais do .env."""
        dotenv_path = resource_path(".env")
        load_dotenv(dotenv_path)

        self.api_key = os.getenv("GROQ_API_KEY")
        if self.api_key:
            self.client = Groq(api_key=self.api_key)
        else:
            self.client = None
            logger.warning("GROQ_API_KEY não configurada — módulo IA desativado.")

        self.model = "llama-3.3-70b-versatile"

        self.system_prompt = (
            "Você é o Consultor Técnico Sênior do sistema sisPROJETOS, especialista em engenharia de distribuição de energia elétrica. "
            "Seu objetivo é auxiliar engenheiros e projetistas na elaboração de projetos de rede elétrica (MT/BT). "
            "Você possui conhecimento profundo em:\n"
            "1. Normas Técnicas Brasileiras: NBR 15688 (Redes de distribuição aérea), NBR 15214 (Compartilhamento de postes), NBR 5422 (Linhas aéreas).\n"
            "2. Padrões de Concessionárias: Especialmente Light (Rio de Janeiro) e Enel (São Paulo).\n"
            "3. Cálculos de Engenharia: Mecânica de condutores (Catenária/Parábola), Esforços em estruturas (Soma Vetorial de Trações), Flechas e Trações.\n"
            "4. Procedimentos de Segurança e Meio Ambiente (CQT, Licenciamento Ambiental).\n\n"
            "Instruções:\n"
            "- Seja técnico, preciso e profissional.\n"
            "- Cite normas ou procedimentos técnicos sempre que possível para embasar suas respostas.\n"
            "- Responda de forma concisa mas completa, utilizando tabelas ou listas se necessário para clareza."
        )

    def get_response(self, user_message, history=None, project_context=None):
        """Obtém resposta da Groq API com contexto de projeto opcional.

        Args:
            user_message (str): Mensagem do usuário a ser enviada.
            history (list[tuple], optional): Histórico [(user, assistant), ...].
            project_context (dict, optional): Contexto atual do projeto.

        Returns:
            str: Resposta do assistente ou mensagem de erro.
        """
        if not self.client:
            return "Erro: Chave API Groq não configurada no arquivo .env."

        try:
            user_message = sanitize_string(user_message, max_length=4000, allow_empty=False)
        except ValueError:
            return "Erro: Mensagem vazia ou inválida."

        try:
            # Build context string
            ctx_msg = ""
            if project_context:
                ctx_msg = "\n\nCONTEXTO ATUAL DO PROJETO:\n"
                if project_context.get("pole_load"):
                    p = project_context["pole_load"]
                    ctx_msg += f"- Esforço no Poste: {p['resultant_force']:.2f} daN a {p['resultant_angle']:.2f}°\n"
                if project_context.get("catenary"):
                    c = project_context["catenary"]
                    ctx_msg += f"- Catenária: Flecha de {c['sag']:.2f}m, Tração {c['tension']} daN\n"
                if project_context.get("electrical"):
                    e = project_context["electrical"]
                    ctx_msg += f"- Elétrica: Queda de {e['percentage_drop']:.2f}% (Corrente {e['current']:.2f}A)\n"
                if project_context.get("cqt"):
                    c = project_context["cqt"]
                    if c.get("success"):
                        ctx_msg += f"- Rede CQT: CQT Max {c['summary']['max_cqt']:.2f}%, Carga {c['summary']['total_kva']:.2f} kVA\n"

            full_system = self.system_prompt + ctx_msg
            messages = [{"role": "system", "content": full_system}]

            if history:
                for u, a in history:
                    messages.append({"role": "user", "content": u})
                    messages.append({"role": "assistant", "content": a})

            messages.append({"role": "user", "content": user_message})

            completion = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=2048,
            )

            return completion.choices[0].message.content
        except Exception as e:
            logger.error("Erro ao contatar Groq API: %s", e)
            return f"Erro ao contatar Groq AI: {str(e)}"
