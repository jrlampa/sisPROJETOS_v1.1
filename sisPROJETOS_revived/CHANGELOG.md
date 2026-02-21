# 📝 CHANGELOG - sisPROJETOS

Todas as mudanças notáveis do projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Semantic Versioning](https://semver.org/lang/pt-BR/).

---

## [Unreleased]

### Planejado

- [ ] Plugin architecture
- [ ] Multi-language support (i18n)
- [ ] Dark mode persistido em configurações
- [ ] Web version (React + FastAPI)
- [ ] Collaborative editing
- [ ] Mobile companion app (React Native)

---

## [1.0.0] - 2026-02-21

> Versão inicial de produção. Consolida todas as funcionalidades desenvolvidas
> durante a fase de revitalização do projeto (Python 2.7 → Python 3.12).

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

### ✨ Adicionado

- **🔐 Sistema de Logging Centralizado** (`src/utils/logger.py`)
  - Configuração unificada com rotating file handlers (10 MB, 5 backups)
  - AppData path support (Windows/Linux/Mac)
  - LogContext manager para operações com medição de tempo
  - Níveis configuráveis via `.env` (DEBUG, INFO, WARNING, ERROR, CRITICAL)
  - Adotado em 4 módulos críticos (catenaria, pole_load, project_creator, db_manager)
  - **Testes**: 26 casos ✅

- **🔄 Verificador de Atualizações Auto** (`src/utils/update_checker.py`)
  - Consome GitHub Releases API
  - Suporte a canais: stable (padrão) e beta
  - Intervalo configurável: 1, 3, 7, 14 dias
  - Não bloqueante (executa em thread separada)
  - Parse de versionamento semântico
  - **Testes**: 6 casos ✅

- **💾 Persistência de Preferências** (`src/database/db_manager.py`)
  - Tabela `app_settings` para configurações globais
  - Métodos: `get_setting()`, `set_setting()`, `get_update_settings()`, `save_update_settings()`
  - Migração automática de schema (backward-compatible)
  - **Testes**: 2 casos ✅

- **⚙️ UI de Configurações** (`src/modules/settings/gui.py`)
  - Nova aba "Atualizações" na tela de configurações
  - Toggle para ativar/desativar verificação automática
  - Seletor de canal (stable/beta)
  - Seletor de intervalo de verificação
  - Botão "Verificar Agora" para verificação manual
  - Botão "Salvar Configurações" com persistência

- **🚀 Bootstrap de Auto-Update** (`src/main.py`)
  - Integração de verificação de updates no MainApp
  - Execução em thread (1.2s após startup para não bloquear)
  - Modal de notificação com link para download
  - Logs de navegação e inicialização

- **📊 CI/CD Melhorado** (`.github/workflows/`)
  - Gate de cobertura progressivo: 80% (v2.1.0) → 85% (v2.1.1) → 90%+ (v2.2.0)
  - Correção de paths de build: `dist/sisPROJETOS` (case-sensitive)
  - Robustez em dependency-update workflow (fallback sem `requirements.in`)
  - Coverage report integrado em CI

### 🔧 Corrigido

- **Warnings de logging em módulos críticos**
  - `catenaria/logic.py`: `print()` → `logger.exception()`
  - `pole_load/logic.py`: `print()` → `logger.exception()` (2 ocorrências)
  - `project_creator/logic.py`: `logging.getLogger()` → `get_logger()` (centralizado)
  - `db_manager.py`: Substituído print em exceção

- **GitHub Actions workflow paths**
  - `build-release.yml`: Ajustado verificação `dist/sisPROJETOS` (era lowercase)
  - `build-release.yml`: Coverage gate adicionado no job test (80%)
  - `dependency-update.yml`: Fallback para upgrade sem `requirements.in`

### 📊 Métricas

- **Cobertura de testes**
  - Atual: ~45% (baseline v2.1.0)
  - Alvo progressivo: 80% → 85% → 90%+
  - Novos testes: 8 (update_checker + db_settings)
  - Testes total: 132 (125 passing, 7 E2E KML)

- **Logs em AppData**
  - Localização: `%APPDATA%/sisPROJETOS/logs/sisprojetos.log`
  - Rotação automática a cada 10 MB
  - Até 5 backups mantidos

### 📚 Documentado

- Guia de configuração de atualização (inline em settings GUI)
- Arquitetura de update checker (notificação-only v2.1.0)
- Roadmap CI/CD com gates progressivos

---

## [2.0.1] - 2026-02-16

### ✨ Adicionado
- **Testes completos para módulo electrical** (`tests/test_electrical.py`)
  - 20+ casos de teste cobrindo todos os cálculos de queda de tensão
  - Validação de parâmetros inválidos
  - Testes de proporcionalidade distância/seção
  
- **Testes completos para módulo CQT** (`tests/test_cqt.py`)
  - 30+ casos de teste para cálculos de BDI
  - Validação de topologia de rede
  - Testes de fator de demanda por classe social
  
- **Testes expandidos para converter** (`tests/test_converter.py`)
  - Cobertura aumentada de 21% → ~80%
  - 30+ casos de teste para conversão KMZ→UTM
  - Validação de zonas UTM e hemisférios
  
- **Versioning centralizado** (`src/__version__.py`)
  - Única fonte de verdade para versão
  - Build date automático
  - Metadados de copyright e licença
  
- **LICENSE.txt**
  - Licença MIT completa
  - Atribuições de dependências third-party
  
- **Documentação técnica**
  - `ARCHITECTURE.md` - Arquitetura completa do sistema
  - `BUILD.md` - Guia de build e distribuição
  - `CHANGELOG.md` - Este arquivo
  
- **API Key Groq atualizada**
  - Nova chave rotacionada por segurança
  - Variável ambiente em .env

### 🔧 Corrigido
- **Import não utilizado** em `src/utils/dxf_manager.py`
  - Removido `import numpy as np` (linha 3)
  
- **Imports fora de ordem** em `src/modules/ai_assistant/logic.py`
  - Movidos imports externos para o topo do arquivo
  - Conformidade com PEP 8
  
- **Admin privileges desnecessário** no instalador
  - `PrivilegesRequired=admin` → `lowest`
  - Instalação em `{localappdata}` em vez de `{autopf}`
  - Permite instalação sem elevação de privilégios

### 🚀 Otimizado
- **PyInstaller build** (`sisprojetos.spec`)
  - `optimize=2` - Bytecode nível 2
  - `strip=True` - Remove debug symbols
  - `target_arch='x86_64'` - 64-bit explícito
  - `excludes=['tests', 'pytest', 'setuptools', 'pip']` - Reduz ~15 MB
  - `upx_exclude=['vcruntime140.dll', 'python312.dll']` - Previne crashes
  
- **Inno Setup configuração** (`sisPROJETOS.iss`)
  - `Compression=lzma2/ultra64` - Máxima compressão
  - `VersionInfo*` - Metadados completos
  - `LicenseFile=LICENSE.txt` - EULA incluído
  
- **Cobertura de testes**
  - Aumentada de 34% → ~75% global
  - electrical: 0% → ~80%
  - cqt: 0% → ~75%
  - converter: 21% → ~80%

### 📚 Documentado
- Arquitetura MVC completa
- Fluxo de build passo a passo
- Troubleshooting de problemas comuns
- Checklist de release
- Roadmap v2.2 e v3.0

### 🔒 Segurança
- API key Groq rotacionada
- SQL injection protegido (todas queries parametrizadas)
- Path traversal: pendente validação (TODO)

---

## [2.0.0] - 2026-02-15

### ✨ Adicionado
- **Módulo Electrical** - Dimensionamento elétrico
  - Cálculo de queda de tensão (trifásico/monofásico)
  - Resistividade por material (Al, Cu)
  - Validação NBR 5410 (≤5% queda)
  
- **Módulo CQT** - Cálculo de BDI
  - Fator de demanda (DMDI) por classe social
  - Validação de topologia (topological sort)
  - Acumulação bottom-up de cargas
  - Momento elétrico com coeficientes de cabo
  
- **Módulo AI Assistant** - Assistente IA
  - Integração com Groq API (LLaMA 3.3 70B)
  - Consultas técnicas sobre normas brasileiras
  - Análise de projetos e recomendações
  - Sistema de prompts especializado
  
- **Sistema de Design** - Glassmorphism UI
  - `styles.py` - DesignSystem centralizado
  - Cores, tipografia, espaçamento padronizados
  - Interface moderna com CustomTkinter

- **Database Manager**
  - SQLite em AppData
  - CRUD operations completas
  - Schema versionado

### 🔧 Migrado
- Python 2.7 → Python 3.12
- Tkinter → CustomTkinter 5.2+
- Estrutura MVC implementada
- Separação GUI/Logic em todos os módulos

### 🐛 Corrigido
- Encoding issues (cp1252 → UTF-8)
- Database path (relativo → AppData absoluto)
- AttributeError em múltiplos módulos
- Import errors após migração Python 3.12

### 📦 Build
- PyInstaller --onedir mode
- Inno Setup installer (Brazilian Portuguese)
- Executável: 206 MB (dist)
- Instalador: 72 MB (compressão 65%)

---

## [1.1.0] - 2025-XX-XX (Legacy)

### Funcionalidades Originais
- Criação de projetos
- Cálculo de esforços em postes
- Cálculo de catenárias
- Conversão KMZ→UTM→DXF
- Exportação DXF/Excel

**Nota:** Versão Python 2.7 (descontinuada)

---

## [Unreleased] - Planejado

### v2.1.0 (Próxima Release)
- [ ] Logging system centralizado
- [ ] Auto-update checker (GitHub API)
- [ ] Code signing (certificado comercial)
- [ ] Error reporting (Sentry integration)
- [ ] Performance profiling
- [ ] Multi-threading para cálculos pesados

### v2.2.0
- [ ] Plugin architecture
- [ ] RESTful API (FastAPI)
- [ ] Cloud sync (opcional)
- [ ] Multi-language support (i18n)
- [ ] Dark mode
- [ ] Ícone personalizado

### v3.0.0 (Breaking)
- [ ] Web version (React frontend)
- [ ] Collaborative editing
- [ ] Real-time sync
- [ ] Mobile companion app (React Native)
- [ ] GraphQL API

---

## Tipos de Mudanças

- `✨ Adicionado` - Novas funcionalidades
- `🔧 Corrigido` - Correção de bugs
- `📝 Alterado` - Mudanças em funcionalidades existentes
- `🗑️ Removido` - Funcionalidades removidas
- `🔒 Segurança` - Vulnerabilidades corrigidas
- `🚀 Otimizado` - Melhorias de performance
- `📚 Documentado` - Adições/mudanças na documentação
- `🧪 Deprecated` - Funcionalidades que serão removidas

---

## Guia de Contribuição

Para adicionar entries neste CHANGELOG:

1. Sempre adicione em **[Unreleased]** primeiro
2. Use os emojis de tipo de mudança
3. Seja conciso mas descritivo
4. Referencie issues/PRs quando aplicável: `(#123)`
5. Ao fazer release, mova [Unreleased] → [X.Y.Z] com data

Exemplo:
```markdown
### ✨ Adicionado
- **Funcionalidade X** - Descrição breve (#42)
  - Detalhe técnico 1
  - Detalhe técnico 2
```

---

## Links
- [Código-fonte](https://github.com/jrlampa/sisPROJETOS_v1.1)
- [Issues](https://github.com/jrlampa/sisPROJETOS_v1.1/issues)
- [Releases](https://github.com/jrlampa/sisPROJETOS_v1.1/releases)
