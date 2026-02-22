# 📝 CHANGELOG - sisPROJETOS

Todas as mudanças notáveis do projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Semantic Versioning](https://semver.org/lang/pt-BR/).

---

## [Unreleased]

### Planejado

- [ ] Plugin architecture
- [ ] Multi-language support (i18n)
- [ ] Web version (React + FastAPI)
- [ ] Collaborative editing
- [ ] Mobile companion app (React Native)

---

## [2.1.0] - 2026-02-21

### ✨ Adicionado

#### API REST — Integração Half-way BIM

- **Endpoints de Dados Mestres** (`src/api/routes/data.py`)
  - `GET /api/v1/data/conductors` — catálogo de condutores (nome, peso linear)
  - `GET /api/v1/data/poles` — catálogo de postes (material, formato, carga nominal)
  - `GET /api/v1/data/concessionaires` — concessionárias (nome, método de cálculo)
  - Dados lidos diretamente do SQLite (zero mock, zero custo)

- **`DatabaseManager.get_all_concessionaires()`** — método dedicado com `try/finally`
- **3 novos schemas Pydantic**: `ConductorOut`, `PoleOut`, `ConcessionaireOut`

#### Configuração de Ferramentas

- **`pyproject.toml`** — centraliza configurações de `black` (line-length=119, py312) e `isort` (profile=black)

#### Testes e Qualidade

- **12 novos testes** de integração para os endpoints de dados mestres (happy-path + DB error mocks)
- **Cobertura atingida: 100%** em todos os módulos testáveis

### 🔧 Corrigido

#### Segurança e Sanitização

- **Sanitizer integrado** em todos os módulos logic restantes:
  - `catenaria/logic.py` — `span` (positivo), `tension_daN` (positivo), `ha`/`hb` (numérico), `weight_kg_m` (≥0)
  - `pole_load/logic.py` — `concessionaria`/`condicao` (strings), `vao`/`angulo`/`flecha` por cabo
  - `cqt/logic.py` — `trafo_kva` (positivo), `social_class` (A/B/C/D)
  - `project_creator/logic.py` — `project_name` (não vazio, max 100 chars), `base_path` (filepath válido)
  - `converter/logic.py` — extensão de arquivo em `load_file`, `save_to_excel`, `save_to_dxf`, `save_to_csv`
  - `ai_assistant/logic.py` — `sanitize_string` em `get_response()` (max 4000 chars, não vazio)

- **`ai_assistant/logic.py`** — removido `sys.path.append` anti-pattern; importações diretas
- **Logger** adicionado a `converter/logic.py` e `ai_assistant/logic.py`
- **Versão** em `__version__.py` corrigida de `2.0.0` → `2.1.0`
- **Dockerfile** `LABEL version` corrigido de `2.0.0` → `2.1.0`

#### Qualidade de Código

- **Formatação black** aplicada a 16 arquivos `src/` — CI lint estava bloqueado
- **isort** aplicado a 25 arquivos `src/` — imports padronizados
- **Modularização** de `tests/test_converter.py`: 765 → 390 linhas; extraído `test_converter_edge_cases.py`
- **`api/app.py`**: `sys.path.insert` guard marcado com `# pragma: no cover` (inalcançável em pytest)
- **Stale docs** movidos para `docs/archive/` (22 arquivos de auditoria de sessões anteriores)

#### Type Hints (gradual)

- **`electrical/logic.py`**: type hints em `__init__`, `get_resistivity`, `calculate_voltage_drop`
- **`catenaria/logic.py`**: type hints em todos os métodos públicos; `NDArray` para arrays numpy

### 🎨 Interface

- **Dark mode persistido em DB** (`app_settings`)
  - `get_appearance_settings()` / `save_appearance_settings()` em `db_manager.py`
  - Aba "Aparência" em `settings/gui.py` com toggle dark/light e preview

### 🧪 Testes

- **430 testes** (todos passando, 100% de cobertura)
  - +42 testes em relação à v2.0.0 (388 → 430)
  - `test_converter_edge_cases.py` — edge cases de load_file, UTM, CSV (novo)
  - `test_sanitizer.py` — cobertura de sanitize_filepath, sanitize_string, sanitize_code e todos os demais
  - `test_api.py` — 40 testes (4 endpoints cálculo + 3 dados mestres + branches defensivos)

---

## [2.0.0] - 2026-02-21

> Reescrita completa do sisPROJETOS (Python 2.7 → Python 3.12).
> Esta versão é incompatível com a série 1.x (legacy) e representa um novo produto.

### ✨ Adicionado

#### Módulos de Cálculo

- **🔌 Dimensionamento Elétrico** (`src/modules/electrical/`)
  - Cálculo de queda de tensão trifásico e monofásico
  - Resistividade por material obtida do banco de dados (Alumínio, Cobre)
  - Validação de limite de 5% conforme NBR 5410
  - Sanitização de dados de entrada via `utils/sanitizer`

- **📊 CQT/BDI** (`src/modules/cqt/`)
  - Fator de demanda DMDI por classe social (A, B, C, D) — Metodologia Enel
  - Validação e ordenação topológica da rede (BFS)
  - Acumulação bottom-up de cargas
  - Momento elétrico com coeficientes de cabo por trecho

- **📐 Catenária** (`src/modules/catenaria/`)
  - Cálculo de flecha usando equação parabólica e catenária exata
  - Suporte a vão inclinado (ha ≠ hb)
  - Exportação de curva em DXF (`utils/dxf_manager`)

- **⚖️ Esforços em Postes** (`src/modules/pole_load/`)
  - Resultante vetorial de trações de condutores
  - Suporte aos métodos Light (flecha) e Enel (tabela)
  - Sugestão automática de poste adequado
  - Geração de relatório PDF

- **🌍 Conversor KMZ→UTM→DXF** (`src/modules/converter/`)
  - Conversão completa Google Earth → coordenadas UTM → desenho CAD
  - Exportação em XLSX, CSV e DXF
  - Suporte a pontos, linhas e polígonos (fastkml)

- **📄 Criador de Projetos** (`src/modules/project_creator/`)
  - Cadastro e estrutura de projetos de engenharia
  - Geração de documentação em Excel
  - Cópia automática de templates

- **🤖 Assistente IA** (`src/modules/ai_assistant/`)
  - Integração com Groq API (LLaMA 3.3 70B — gratuito)
  - Consultas técnicas sobre normas brasileiras
  - Histórico de contexto por sessão

#### Utilitários

- **🔐 Logging Centralizado** (`src/utils/logger.py`)
  - Rotating file handler (10 MB, 5 backups)
  - AppData path support (Windows/Linux)
  - LogContext manager para medição de tempo
  - Níveis configuráveis via `.env`

- **🔄 Verificador de Atualizações** (`src/utils/update_checker.py`)
  - Consome GitHub Releases API (zero custo)
  - Suporte a canais: stable e beta
  - Intervalo configurável (1, 3, 7, 14 dias)
  - Thread não bloqueante

- **🛡️ Sanitizador de Dados** (`src/utils/sanitizer.py`)
  - `sanitize_string` — remove controles e normaliza Unicode NFC
  - `sanitize_numeric` — conversão e validação de intervalo
  - `sanitize_positive` — validação de valores positivos
  - `sanitize_power_factor` — validação de cos φ (0, 1]
  - `sanitize_phases` — validação de fases (1 ou 3)
  - `sanitize_filepath` — validação de extensões permitidas
  - `sanitize_code` — código alfanumérico padronizado

- **📦 Gerenciador de Recursos** (`src/utils/resource_manager.py`)
  - Localização de recursos em desenvolvimento e em build PyInstaller
  - Cópia de templates para diretório de projeto

- **🗄️ Gerenciador de Banco de Dados** (`src/database/db_manager.py`)
  - SQLite em AppData (portável e zero custo)
  - Schema inicializado automaticamente
  - Dados pré-populados: postes (NBR 8451), condutores, concessionárias, coeficientes CQT
  - Resistividade de Alumínio e Cobre do banco (sem hardcode)
  - Configurações persistidas em `app_settings`

- **🌐 API REST** (`src/api/`) — Integração Half-way BIM
  - `POST /api/v1/electrical/voltage-drop` — Queda de tensão (NBR 5410)
  - `POST /api/v1/cqt/calculate` — CQT/BDI (Metodologia Enel)
  - `POST /api/v1/catenary/calculate` — Catenária (NBR 5422)
  - `POST /api/v1/pole-load/resultant` — Esforços em postes + sugestão
  - `GET /health` — Health check
  - Documentação OpenAPI automática (Swagger UI em `/docs`)
  - CORS configurável via variável de ambiente `CORS_ORIGINS`

- **🎨 Design System** (`src/styles.py`)
  - Paleta Glassmorphism Light e Dark
  - `set_dark_mode()` / `is_dark_mode()` — toggle global de tema
  - `get_bg_color()`, `get_text_color()`, `get_frame_style()`, `get_entry_style()`

#### Infraestrutura

- **🐳 Docker**
  - `Dockerfile` com usuário não-root e ambiente reproduzível
  - `docker-compose.yml` com serviços: `test`, `test-coverage`, `dev`, `api`
  - Serviço `api` exposto na porta 8000

- **⚙️ CI/CD** (`.github/workflows/`)
  - `ci.yml` — testes, cobertura e qualidade de código
  - `build-release.yml` — build PyInstaller + Inno Setup + GitHub Release
  - `dependency-update.yml` — atualização automática de dependências

- **🔢 Versionamento Centralizado** (`src/__version__.py`)
  - Fonte única da verdade para versão, build, autor, copyright e licença
  - Importado em `main.py`, `settings/gui.py` e `api/app.py`

#### Testes

- **🧪 Suite de testes completa** — 388 testes, 100% de cobertura
  - `test_electrical.py` (24 testes)
  - `test_cqt.py` (26 testes)
  - `test_converter.py` + `test_converter_e2e.py` (53 testes)
  - `test_catenary.py` (7 testes)
  - `test_pole_load.py` (24 testes)
  - `test_project_creator.py` (15 testes)
  - `test_ai_assistant.py` (9 testes)
  - `test_logger.py` (29 testes)
  - `test_update_checker.py` (23 testes)
  - `test_db_settings.py` (15 testes)
  - `test_dxf_manager.py` (19 testes)
  - `test_version_styles.py` (32 testes)
  - `test_sanitizer.py` (64 testes)
  - `test_resource_manager.py` (13 testes)
  - `test_api.py` (27 testes — endpoints REST)

### 🔒 Segurança

- Path traversal bloqueado em `resource_path()` (rejeita `..` e caminhos absolutos)
- SQL injection: todas as queries parametrizadas com `?`
- API keys armazenadas exclusivamente em `.env` (no `.gitignore`)
- Filepath validation em `utils/dxf_manager.py`
- CORS configurável via env var (não exposto por padrão)

### 🚀 Build e Distribuição

- PyInstaller `onedir` com `optimize=2`
- Instalador Inno Setup (Português Brasileiro)
- Instalação sem privilégios de administrador (`{localappdata}`)
- Metadados completos de versão no executável Windows

---

## Tipos de Mudanças

- `✨ Adicionado` — Novas funcionalidades
- `🔧 Corrigido` — Correção de bugs
- `📝 Alterado` — Mudanças em funcionalidades existentes
- `🗑️ Removido` — Funcionalidades removidas
- `🔒 Segurança` — Vulnerabilidades corrigidas
- `🚀 Otimizado` — Melhorias de performance
- `📚 Documentado` — Adições/mudanças na documentação

---

## Guia de Contribuição

Para adicionar entries neste CHANGELOG:

1. Sempre adicione em **[Unreleased]** primeiro
2. Use os emojis de tipo de mudança
3. Seja conciso mas descritivo
4. Referencie issues/PRs quando aplicável: `(#123)`
5. Ao fazer release, mova [Unreleased] → [X.Y.Z] com data

---

## Links

- [Código-fonte](https://github.com/jrlampa/sisPROJETOS_v1.1)
- [Issues](https://github.com/jrlampa/sisPROJETOS_v1.1/issues)
- [Releases](https://github.com/jrlampa/sisPROJETOS_v1.1/releases)


> Reescrita completa do sisPROJETOS (Python 2.7 → Python 3.12).
> Esta versão é incompatível com a série 1.x (legacy) e representa um novo produto.

### ✨ Adicionado

#### Módulos de Cálculo

- **🔌 Dimensionamento Elétrico** (`src/modules/electrical/`)
  - Cálculo de queda de tensão trifásico e monofásico
  - Resistividade por material obtida do banco de dados (Alumínio, Cobre)
  - Validação de limite de 5% conforme NBR 5410
  - Sanitização de dados de entrada via `utils/sanitizer`

- **📊 CQT/BDI** (`src/modules/cqt/`)
  - Fator de demanda DMDI por classe social (A, B, C, D) — Metodologia Enel
  - Validação e ordenação topológica da rede (BFS)
  - Acumulação bottom-up de cargas
  - Momento elétrico com coeficientes de cabo por trecho

- **📐 Catenária** (`src/modules/catenaria/`)
  - Cálculo de flecha usando equação parabólica e catenária exata
  - Suporte a vão inclinado (ha ≠ hb)
  - Exportação de curva em DXF (`utils/dxf_manager`)

- **⚖️ Esforços em Postes** (`src/modules/pole_load/`)
  - Resultante vetorial de trações de condutores
  - Suporte aos métodos Light (flecha) e Enel (tabela)
  - Sugestão automática de poste adequado
  - Geração de relatório PDF

- **🌍 Conversor KMZ→UTM→DXF** (`src/modules/converter/`)
  - Conversão completa Google Earth → coordenadas UTM → desenho CAD
  - Exportação em XLSX, CSV e DXF
  - Suporte a pontos, linhas e polígonos (fastkml)

- **📄 Criador de Projetos** (`src/modules/project_creator/`)
  - Cadastro e estrutura de projetos de engenharia
  - Geração de documentação em Excel
  - Cópia automática de templates

- **🤖 Assistente IA** (`src/modules/ai_assistant/`)
  - Integração com Groq API (LLaMA 3.3 70B — gratuito)
  - Consultas técnicas sobre normas brasileiras
  - Histórico de contexto por sessão

#### Utilitários

- **🔐 Logging Centralizado** (`src/utils/logger.py`)
  - Rotating file handler (10 MB, 5 backups)
  - AppData path support (Windows/Linux)
  - LogContext manager para medição de tempo
  - Níveis configuráveis via `.env`

- **🔄 Verificador de Atualizações** (`src/utils/update_checker.py`)
  - Consome GitHub Releases API (zero custo)
  - Suporte a canais: stable e beta
  - Intervalo configurável (1, 3, 7, 14 dias)
  - Thread não bloqueante

- **🛡️ Sanitizador de Dados** (`src/utils/sanitizer.py`)
  - `sanitize_string` — remove controles e normaliza Unicode NFC
  - `sanitize_numeric` — conversão e validação de intervalo
  - `sanitize_positive` — validação de valores positivos
  - `sanitize_power_factor` — validação de cos φ (0, 1]
  - `sanitize_phases` — validação de fases (1 ou 3)
  - `sanitize_filepath` — validação de extensões permitidas
  - `sanitize_code` — código alfanumérico padronizado

- **📦 Gerenciador de Recursos** (`src/utils/resource_manager.py`)
  - Localização de recursos em desenvolvimento e em build PyInstaller
  - Cópia de templates para diretório de projeto

- **🗄️ Gerenciador de Banco de Dados** (`src/database/db_manager.py`)
  - SQLite em AppData (portável e zero custo)
  - Schema inicializado automaticamente
  - Dados pré-populados: postes (NBR 8451), condutores, concessionárias, coeficientes CQT
  - Resistividade de Alumínio e Cobre do banco (sem hardcode)
  - Configurações persistidas em `app_settings`

- **🌐 API REST** (`src/api/`) — Integração Half-way BIM
  - `POST /api/v1/electrical/voltage-drop` — Queda de tensão (NBR 5410)
  - `POST /api/v1/cqt/calculate` — CQT/BDI (Metodologia Enel)
  - `POST /api/v1/catenary/calculate` — Catenária (NBR 5422)
  - `POST /api/v1/pole-load/resultant` — Esforços em postes + sugestão
  - `GET /health` — Health check
  - Documentação OpenAPI automática (Swagger UI em `/docs`)
  - CORS configurável via variável de ambiente `CORS_ORIGINS`

- **🎨 Design System** (`src/styles.py`)
  - Paleta Glassmorphism Light e Dark
  - `set_dark_mode()` / `is_dark_mode()` — toggle global de tema
  - `get_bg_color()`, `get_text_color()`, `get_frame_style()`, `get_entry_style()`

#### Infraestrutura

- **🐳 Docker**
  - `Dockerfile` com usuário não-root e ambiente reproduzível
  - `docker-compose.yml` com serviços: `test`, `test-coverage`, `dev`, `api`
  - Serviço `api` exposto na porta 8000

- **⚙️ CI/CD** (`.github/workflows/`)
  - `ci.yml` — testes, cobertura e qualidade de código
  - `build-release.yml` — build PyInstaller + Inno Setup + GitHub Release
  - `dependency-update.yml` — atualização automática de dependências

- **🔢 Versionamento Centralizado** (`src/__version__.py`)
  - Fonte única da verdade para versão, build, autor, copyright e licença
  - Importado em `main.py`, `settings/gui.py` e `api/app.py`

#### Testes

- **🧪 Suite de testes completa** — 388 testes, 100% de cobertura
  - `test_electrical.py` (24 testes)
  - `test_cqt.py` (26 testes)
  - `test_converter.py` + `test_converter_e2e.py` (53 testes)
  - `test_catenary.py` (7 testes)
  - `test_pole_load.py` (24 testes)
  - `test_project_creator.py` (15 testes)
  - `test_ai_assistant.py` (9 testes)
  - `test_logger.py` (29 testes)
  - `test_update_checker.py` (23 testes)
  - `test_db_settings.py` (15 testes)
  - `test_dxf_manager.py` (19 testes)
  - `test_version_styles.py` (32 testes)
  - `test_sanitizer.py` (64 testes)
  - `test_resource_manager.py` (13 testes)
  - `test_api.py` (27 testes — endpoints REST)

### 🔒 Segurança

- Path traversal bloqueado em `resource_path()` (rejeita `..` e caminhos absolutos)
- SQL injection: todas as queries parametrizadas com `?`
- API keys armazenadas exclusivamente em `.env` (no `.gitignore`)
- Filepath validation em `utils/dxf_manager.py`
- CORS configurável via env var (não exposto por padrão)

### 🚀 Build e Distribuição

- PyInstaller `onedir` com `optimize=2`
- Instalador Inno Setup (Português Brasileiro)
- Instalação sem privilégios de administrador (`{localappdata}`)
- Metadados completos de versão no executável Windows

---

## Tipos de Mudanças

- `✨ Adicionado` — Novas funcionalidades
- `🔧 Corrigido` — Correção de bugs
- `📝 Alterado` — Mudanças em funcionalidades existentes
- `🗑️ Removido` — Funcionalidades removidas
- `🔒 Segurança` — Vulnerabilidades corrigidas
- `🚀 Otimizado` — Melhorias de performance
- `📚 Documentado` — Adições/mudanças na documentação

---

## Guia de Contribuição

Para adicionar entries neste CHANGELOG:

1. Sempre adicione em **[Unreleased]** primeiro
2. Use os emojis de tipo de mudança
3. Seja conciso mas descritivo
4. Referencie issues/PRs quando aplicável: `(#123)`
5. Ao fazer release, mova [Unreleased] → [X.Y.Z] com data

---

## Links

- [Código-fonte](https://github.com/jrlampa/sisPROJETOS_v1.1)
- [Issues](https://github.com/jrlampa/sisPROJETOS_v1.1/issues)
- [Releases](https://github.com/jrlampa/sisPROJETOS_v1.1/releases)

