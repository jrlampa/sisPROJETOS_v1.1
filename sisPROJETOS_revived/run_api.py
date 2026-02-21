"""
Ponto de entrada para o servidor REST do sisPROJETOS.

Inicia a API FastAPI via uvicorn para integração Half-way BIM.

Uso:
    python run_api.py
    python run_api.py --host 0.0.0.0 --port 8080
"""

import argparse
import sys
import os

# Adiciona src/ ao path para importações dos módulos
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

import uvicorn


def main():
    parser = argparse.ArgumentParser(description="sisPROJETOS REST API")
    parser.add_argument("--host", default="127.0.0.1", help="Endereço de escuta (padrão: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="Porta de escuta (padrão: 8000)")
    parser.add_argument("--reload", action="store_true", help="Modo reload para desenvolvimento")
    args = parser.parse_args()

    uvicorn.run(
        "api.app:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="info",
    )


if __name__ == "__main__":
    main()
