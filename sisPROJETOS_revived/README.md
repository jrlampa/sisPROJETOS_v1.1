# ⚡ sisPROJETOS v2.0

> **Sistema Integrado de Projetos Elétricos**  
> Ferramenta profissional para engenharia elétrica e projetos de redes de distribuição

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE.txt)
[![Platform](https://img.shields.io/badge/Platform-Windows%2010/11-lightgrey.svg)]()
[![Build](https://img.shields.io/badge/Build-Passing-brightgreen.svg)]()

---

## 📋 Visão Geral

O **sisPROJETOS** é uma solução completa para projetos de redes elétricas de distribuição, oferecendo cálculos precisos, conversão de coordenadas, geração de desenhos técnicos e assistência por IA.

Desenvolvido por engenheiros para engenheiros, integra 9 módulos especializados em uma interface moderna e intuitiva.

### ✨ Funcionalidades Principais

- 🔌 **Dimensionamento Elétrico** - Queda de tensão, seções de cabo, materiais
- 📊 **Cálculo de BDI/CQT** - Fator de demanda, momento elétrico, topologia de rede
- 📐 **Catenária e Flecha** - Cálculo de vão, tensão de cabos, temperatura
- ⚖️ **Esforços em Postes** - Análise estrutural, momentos, limites NBR
- 🌍 **Conversor KMZ→UTM→DXF** - Google Earth para desenho técnico CAD
- 🤖 **Assistente IA** - Consultas técnicas sobre normas brasileiras (Groq API)
- 📄 **Gerador de Projetos** - Documentação completa em Excel/PDF
- 📏 **Prancha DXF** - Geração automática de desenhos técnicos
- 🔧 **Calculadoras** - Ferramentas auxiliares para engenharia

---

## 🚀 Início Rápido

### 📥 Instalação (Usuário Final)

1. **Download do instalador**:
   - Acesse [Releases](https://github.com/jrlampa/sisPROJETOS_v1.1/releases)
   - Baixe `sisPROJETOS_v2.0.1_Setup.exe` (~72 MB)

2. **Execute o instalador**:
   - Não requer privilégios de administrador
   - Instalação em `%LOCALAPPDATA%\sisPROJETOS`
   - Atalho criado automaticamente

3. **Configure a API (opcional)**:
   - Para usar o Assistente IA, obtenha uma chave em [Groq Console](https://console.groq.com)
   - Adicione em: Configurações → API Key

### 🛠️ Instalação (Desenvolvedor)

```powershell
# Clone o repositório
git clone https://github.com/jrlampa/sisPROJETOS_v1.1.git
cd sisPROJETOS_v1.1/sisPROJETOS_revived

# Crie ambiente virtual
python -m venv venv
.\venv\Scripts\activate

# Instale dependências
pip install -r requirements.txt

# Configure variáveis de ambiente
Copy-Item .env.example .env
# Edite .env e adicione GROQ_API_KEY

# Execute a aplicação
python run.py
```

**Requisitos**:
- Windows 10/11 (64-bit)
- Python 3.12+ (para desenvolvimento)
- 4 GB RAM mínimo
- 500 MB espaço em disco

---

## 📚 Documentação

| Documento | Descrição |
|-----------|-----------|
| [ARCHITECTURE.md](ARCHITECTURE.md) | Arquitetura completa do sistema (MVC, módulos, database) |
| [BUILD.md](BUILD.md) | Guia de build e distribuição (PyInstaller, Inno Setup) |
| [CHANGELOG.md](CHANGELOG.md) | Histórico detalhado de versões e mudanças |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Guia para contribuidores (em breve) |

---

## 🏗️ Arquitetura

```
sisPROJETOS_revived/
├── src/                    # Código-fonte principal
│   ├── main.py            # Aplicação principal (CustomTkinter)
│   ├── styles.py          # Design System (cores, tipografia)
│   ├── __version__.py     # Versioning centralizado
│   ├── database/          # Gerenciamento SQLite
│   ├── modules/           # 9 módulos especializados
│   │   ├── electrical/    # Dimensionamento elétrico
│   │   ├── cqt/          # Cálculo de BDI
│   │   ├── converter/    # KMZ→UTM→DXF
│   │   ├── catenary/     # Catenária e flecha
│   │   ├── pole_load/    # Esforços em postes
│   │   ├── ai_assistant/ # Assistente IA (Groq)
│   │   └── ...
│   └── utils/            # Utilitários reutilizáveis
├── tests/                # Testes unitários (pytest)
├── resources/            # Assets (ícones, modelos DXF)
├── build/                # Build artifacts (temporário)
└── installer_output/     # Instaladores gerados

Padrão MVC:
- gui.py: View (CustomTkinter widgets)
- logic.py: Model (regras de negócio, cálculos)
- Comunicação via callbacks e eventos Tkinter
```

---

## 🔬 Tecnologias

### Core
- **Python 3.12** - Linguagem principal
- **CustomTkinter 5.2+** - UI moderna (glassmorphism)
- **SQLite3** - Database local (AppData)

### Bibliotecas Especializadas
- **ezdxf** - Geração de arquivos DXF (AutoCAD)
- **pyproj** - Conversão de coordenadas (UTM, WGS84)
- **openpyxl** - Manipulação de Excel
- **numpy** - Cálculos científicos
- **matplotlib** - Gráficos e visualizações

### Integrações
- **Groq API** - LLaMA 3.3 70B (assistente IA)
- **python-dotenv** - Variáveis de ambiente

### Build & Deploy
- **PyInstaller** - Empacotamento executável
- **Inno Setup** - Instalador Windows
- **pytest** - Framework de testes

---

## 🧪 Testes

```powershell
# Execute todos os testes
pytest tests/ -v

# Com cobertura
pytest tests/ --cov=src --cov-report=html

# Apenas um módulo
pytest tests/test_electrical.py
```

**Cobertura Atual**: 75% (objetivo: 90%)

| Módulo | Cobertura | Status |
|--------|-----------|--------|
| electrical | 80% | ✅ |
| cqt | 75% | ✅ |
| converter | 80% | ✅ |
| catenary | 60% | ⚠️ |
| pole_load | 50% | ⚠️ |

---

## 🤝 Contribuindo

Contribuições são bem-vindas! Por favor:

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/MinhaFeature`)
3. Commit suas mudanças (`git commit -m 'Adiciona MinhaFeature'`)
4. Push para a branch (`git push origin feature/MinhaFeature`)
5. Abra um Pull Request

**Padrões**:
- Código: PEP 8 (max line length: 119)
- Commits: Conventional Commits
- Testes: Cobertura mínima 70% para novos módulos

---

## 🐛 Problemas Conhecidos

- ⚠️ **Path traversal** em DXF Manager (pendente validação)
- ⚠️ **SQL injection** em queries antigas (migração para parametrizadas em andamento)
- ℹ️ Instalador requer 500 MB de espaço temporário (compactação alta)

Veja [Issues](https://github.com/jrlampa/sisPROJETOS_v1.1/issues) para lista completa.

---

## 📄 Licença

Este projeto está licenciado sob a **MIT License** - veja [LICENSE.txt](LICENSE.txt) para detalhes.

### Third-Party Licenses
O sisPROJETOS utiliza 73+ bibliotecas open-source. Atribuições completas em [LICENSE.txt](LICENSE.txt).

---

## 👨‍💻 Autor

**João Rodrigo Lampa**  
Engenheiro Eletricista  

- GitHub: [@jrlampa](https://github.com/jrlampa)
- Email: contato@exemplo.com.br

---

## 🌟 Roadmap

### v2.1.0 (Q2 2026)
- [ ] Sistema de logging centralizado
- [ ] Auto-update checker
- [ ] Code signing (certificado comercial)
- [ ] CI/CD com GitHub Actions

### v2.2.0 (Q3 2026)
- [ ] Plugin architecture
- [ ] RESTful API (FastAPI)
- [ ] Dark mode
- [ ] Multi-language support

### v3.0.0 (2027)
- [ ] Web version (React)
- [ ] Collaborative editing
- [ ] Mobile app (React Native)

---

## ⭐ Agradecimentos

- Comunidade Python Brasil
- Groq pela API de IA
- Contribuidores do CustomTkinter
- Todos que reportaram bugs e sugeriram melhorias

---

<div align="center">

**Se este projeto foi útil, considere dar uma ⭐!**

[⬆ Voltar ao topo](#-sisprojetos-v20)

</div>
