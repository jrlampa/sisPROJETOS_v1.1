# ============================================================
# sisPROJETOS — Dockerfile
# ============================================================
# Propósito: Ambiente de desenvolvimento e execução de testes.
# A aplicação GUI requer DISPLAY para exibição (X11/Wayland).
# Para testes headless, a variável DISPLAY não é necessária.
# ============================================================

FROM python:3.12-slim

LABEL maintainer="João Rodrigo Lampa <contato@exemplo.com.br>"
LABEL description="sisPROJETOS - Sistema Integrado de Projetos Elétricos"
LABEL version="1.0.0"

# Variáveis de ambiente
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    LOG_LEVEL=INFO \
    DEBUG=False \
    API_HOST=0.0.0.0 \
    API_PORT=8000

# Instalar dependências do sistema necessárias para tkinter e matplotlib
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-tk \
    tk-dev \
    libfreetype6-dev \
    && rm -rf /var/lib/apt/lists/*

# Criar usuário não-root para segurança
RUN groupadd --gid 1001 appgroup && \
    useradd --uid 1001 --gid appgroup --shell /bin/bash --create-home appuser

WORKDIR /app

# Copiar e instalar dependências primeiro (cache layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código-fonte
COPY --chown=appuser:appgroup . .

# Trocar para usuário não-root
USER appuser

# Diretório de logs e dados
RUN mkdir -p /home/appuser/.local/share/sisPROJETOS/logs

# Expõe porta da API REST (Half-way BIM)
EXPOSE 8000

# Ponto de entrada padrão: executar testes
CMD ["python", "-m", "pytest", "tests/", "-v", "--tb=short"]
