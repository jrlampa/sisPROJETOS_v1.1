# 🧠 MEMORY.md — RAG (Retrieval-Augmented Generation) do sisPROJETOS

> **Memória de Trabalho do Agente de Desenvolvimento**
> Atualizado automaticamente a cada sessão de desenvolvimento.
> Serve como fonte primária de contexto para IAs e desenvolvedores.

---

## 📋 Resumo Executivo do Projeto

**Nome:** sisPROJETOS v2.x  
**Tipo:** Aplicação Desktop Python (Windows 10/11)  
**Domínio:** Engenharia Elétrica — Projetos de Redes de Distribuição  
**Idioma da Interface:** Português Brasileiro (pt-BR)  
**Maturidade:** Produção (v2.1.0 — 529 testes, 100% cobertura, API REST com 14 endpoints, black+isort limpo, type hints completos em todos os módulos, DXF 2.5D, testes DXF headless com coordenadas reais, **camada de domínio DDD com 4 value objects + 3 entidades**)

---

## 🏛️ Arquitetura Fundamental

### Padrão: MVC Desacoplado

```
GUI (View) → chama → Logic (Model)
Logic ← consulta → DatabaseManager
Main (Controller) → orquestra → GUIs
```

### Stack Tecnológico

| Camada | Tecnologia | Versão |
|--------|-----------|--------|
| Interface | CustomTkinter | 5.2+ |
| DB | SQLite3 | built-in |
| Cálculos | NumPy | 2.2+ |
| Tabelas | Pandas | 2.2+ |
| Gráficos | Matplotlib | 3.9+ |
| DXF/CAD | ezdxf | 1.3+ |
| Coordenadas | pyproj | 3.7+ |
| KML/KMZ | fastkml | <1.0 |
| IA | Groq (LLaMA 3.3) | 0.13+ |
| Env | python-dotenv | 1.0+ |
| **API REST** | **FastAPI + uvicorn** | **0.129+** |
| **API Schemas** | **Pydantic** | **2.x** |

---

## 📁 Estrutura de Módulos

### Módulos Funcionais (src/modules/)

| Módulo | Arquivo Logic | Arquivo GUI | Responsabilidade |
|--------|--------------|------------|-----------------|
| `project_creator` | `logic.py` | `gui.py` | Cadastro e estrutura de projetos |
| `pole_load` | `logic.py` | `gui.py` + `report.py` | Esforços mecânicos em postes (NBR) |
| `catenaria` | `logic.py` | `gui.py` | Flecha e tração de condutores |
| `electrical` | `logic.py` | `gui.py` | Queda de tensão (NBR 5410) |
| `cqt` | `logic.py` | `gui.py` | CQT/BDI — Metodologia Enel |
| `converter` | `logic.py` | `gui.py` | KMZ→UTM→DXF (Google Earth) |
| `ai_assistant` | `logic.py` | `gui.py` | Assistente IA via Groq API |
| `settings` | — | `gui.py` | Configurações e cadastros |

### API REST (src/api/) — Half-way BIM

| Arquivo | Responsabilidade |
|---------|-----------------|
| `app.py` | Fábrica FastAPI + registro de rotas |
| `schemas.py` | Modelos Pydantic (request/response) |
| `routes/electrical.py` | POST `/api/v1/electrical/voltage-drop`; GET `/api/v1/electrical/materials` |
| `routes/cqt.py` | POST `/api/v1/cqt/calculate` |
| `routes/catenary.py` | POST `/api/v1/catenary/calculate` |
| `routes/pole_load.py` | POST `/api/v1/pole-load/resultant`; GET `/api/v1/pole-load/suggest?force_daN=...` |
| `routes/data.py` | GET `/api/v1/data/conductors`, `/data/poles`, `/data/concessionaires` |
| `routes/converter.py` | POST `/api/v1/converter/kml-to-utm` |
| `routes/project_creator.py` | POST `/api/v1/projects/create` |

### Utilitários (src/utils/)

| Arquivo | Responsabilidade |
|---------|-----------------|
| `logger.py` | Logging centralizado com RotatingFileHandler |
| `update_checker.py` | Verificação de updates via GitHub Releases API |
| `dxf_manager.py` | Criação de arquivos DXF (catenária, pontos UTM) |
| `resource_manager.py` | Gerenciamento de recursos (templates, assets) |
| `sanitizer.py` | Sanitização e validação de dados de entrada (strings, numéricos, caminhos) |
| `__init__.py` | `resource_path()` com proteção path traversal |

---

## 🔒 Decisões de Segurança

### Decisões Já Implementadas

1. **Path Traversal em `resource_path()`**: Validado — rejeita `..` e caminhos absolutos (src/utils/__init__.py)
2. **SQL Injection**: Todas as queries usam parametrização `(?, ?)` — VERIFICADO em db_manager.py
3. **API Keys**: Armazenadas apenas em `.env` (no .gitignore) — NUNCA hardcoded
4. **Secrets**: `.env` está no `.gitignore` root e no `.gitignore` do subprojeto

### Pendências de Segurança

- ✅ **DXF Manager filepath validation**: `_validate_output_path()` implementada em `dxf_manager.py` — rejeita null bytes e resolve o caminho real. Ambos `create_catenary_dxf()` e `create_points_dxf()` chamam esta função.

### Type Hints (evolução gradual)

| Módulo | Estado |
|--------|--------|
| `utils/logger.py` | ✅ Completo |
| `utils/sanitizer.py` | ✅ Completo |
| `utils/update_checker.py` | ✅ Completo |
| `utils/__init__.py` | ✅ Completo |
| `utils/dxf_manager.py` | ✅ Completo |
| `electrical/logic.py` | ✅ Completo (v2.1.0) |
| `catenaria/logic.py` | ✅ Completo (v2.1.0) |
| `cqt/logic.py` | ✅ Completo (v2.1.0) |
| `pole_load/logic.py` | ✅ Completo (v2.1.0) |
| `project_creator/logic.py` | ✅ Completo (v2.1.0) |
| `ai_assistant/logic.py` | ✅ Completo (v2.1.0) |
| `database/db_manager.py` | ✅ Completo (v2.1.0) |
| `api/routes/data.py` | ✅ Completo |
| `converter/logic.py` | ✅ Completo (v2.1.0) |

---

## 🗄️ Banco de Dados

**Tipo:** SQLite3  
**Localização em produção:** `%APPDATA%/sisPROJETOS/sisprojetos.db`  
**Localização em desenvolvimento:** igual ao acima (usa `os.getenv("APPDATA")`)

### Tabelas Principais

```sql
conductors        -- Dados técnicos de condutores (peso, ruptura, seção)
poles             -- Catálogo de postes (material, altura, carga nominal)
concessionaires   -- Concessionárias (Light, Enel) + método de cálculo
network_types     -- Tipos de rede por concessionária
cable_technical_data -- Resistividades, coeficientes K de CQT
load_tables       -- Tabelas de tração por vão (método Enel)
app_settings      -- Configurações persistentes (updates, tema, etc.)
```

### Dados Pré-populados (sem mocks)

- Concessionárias: Light (método flecha), Enel (método tabela)
- Condutores Light: 556MCM-CA, 397MCM-CA, 1/0AWG-CAA, 4AWG-CAA
- Tabela de cargas Enel: 1/0 CA (20–80m) + BT 3x35+54.6
- Coeficientes CQT K: 6 tipos de cabo (2#16 a 3x150mm² Al)

---

## 🧮 Metodologias de Cálculo

### CQT (Cálculo de Queda de Tensão — Metodologia Enel)

- **DMDI**: Tabela de demanda dividida em 4 classes (A, B, C, D) e 6 faixas de UC
- **UNIT_DIVISOR**: 100.0 (metros → hectômetros)
- **Topologia**: Validação bottom-up com ordenação topológica (BFS)
- **Referência**: CNS-OMBR-MAT-19-0285

### Catenária

- Cálculo de flecha usando equação parabólica
- Suporte a vão inclinado (altura diferente nas extremidades)
- Exportação DXF via `dxf_manager.py`

### Esforços em Postes (Pole Load)

- Resultante vetorial de trações (soma de forças)
- Suporte a métodos: flecha (Light) e tabela (Enel)
- Relatório PDF via `report.py`

### Queda de Tensão Elétrica

- Monofásico (phases=1) e trifásico (phases=3)
- Resistividade do banco de dados (fallback: Al=0.0282)
- Limite: 5% (NBR 5410)

---

## 🧪 Estratégia de Testes

**Framework:** pytest + pytest-mock + pytest-cov  
**Total de testes:** 529 (todos passando, 100% cobertura)  
**Cobertura estimada:** **100%** (excluindo GUI/main.py via .coveragerc)

### Mapeamento de Testes

| Arquivo de Teste | Módulo Testado | Status |
|-----------------|---------------|--------|
| `test_electrical.py` | `electrical/logic.py` | ✅ |
| `test_cqt.py` | `cqt/logic.py` (cálculo principal) | ✅ |
| `test_cqt_sanitizer.py` | `cqt/logic.py` (sanitização de entradas: trafo_kva, social_class) | ✅ |
| `test_converter.py` | `converter/logic.py` (principal) | ✅ |
| `test_converter_edge_cases.py` | `converter/logic.py` (edge cases: load_file, UTM, CSV) | ✅ |
| `test_converter_e2e.py` | Pipeline completo KMZ→DXF | ✅ |
| `test_catenary.py` | `catenaria/logic.py` | ✅ |
| `test_pole_load.py` | `pole_load/logic.py` | ✅ |
| `test_project_creator.py` | `project_creator/logic.py` | ✅ |
| `test_ai_assistant.py` | `ai_assistant/logic.py` | ✅ |
| `test_logger.py` | `utils/logger.py` | ✅ |
| `test_update_checker.py` | `utils/update_checker.py` | ✅ |
| `test_db_settings.py` | `database/db_manager.py` | ✅ |
| `test_dxf_manager.py` | `utils/dxf_manager.py` (inclui 2 novos testes 2.5D: Z=elevation em POINT, TEXT flat em XY) | ✅ |
| `test_version_styles.py` | `__version__.py`, `styles.py`, `utils/__init__.py` | ✅ |
| `test_sanitizer.py` | `utils/sanitizer.py` | ✅ |
| `test_resource_manager.py` | `utils/resource_manager.py` | ✅ |
| `test_api.py` | `api/` (endpoints de cálculo: electrical, cqt, catenary, pole-load, health; + GET /electrical/materials + GET /pole-load/suggest) | ✅ |
| `test_api_bim.py` | `api/routes/data.py`, `api/routes/converter.py`, `api/routes/project_creator.py` (endpoints BIM) | ✅ |
| `test_domain.py` | `domain/value_objects.py`, `domain/entities.py` (DDD: UTMCoordinate, CatenaryResult, VoltageDropResult, SpanResult, Conductor, Pole, Concessionaire) | ✅ |
| `test_dxf_content.py` | Validação estrutural headless de DXF (22 testes): coordenadas reais UTM, layers, entidades, 2.5D, vãos 100m/500m/1km | ✅ |

### Executar Testes

```bash
# Local
cd sisPROJETOS_revived
pytest tests/ -v

# Com cobertura
pytest tests/ -v --cov=src --cov-report=html

# Docker
docker compose run --rm test
```

---

## 🐳 Docker

### Contexto de Uso

Como aplicação desktop GUI, o Docker é utilizado para:
1. **Ambiente de desenvolvimento** isolado e reproduzível
2. **Execução de testes** em CI/CD (headless)
3. **Verificação de dependências** cross-platform

### Arquivos Docker

| Arquivo | Localização | Propósito |
|---------|------------|----------|
| `Dockerfile` | `sisPROJETOS_revived/` | Imagem Python com deps instaladas |
| `docker-compose.yml` | `sisPROJETOS_revived/` | Serviços dev + test |
| `.dockerignore` | `sisPROJETOS_revived/` | Otimização do build context |

---

## 🌐 APIs e Integrações Externas

### APIs Utilizadas (Zero Custo)

| API | Endpoint | Limite Gratuito | Uso |
|-----|---------|----------------|-----|
| Groq (LLaMA 3.3 70B) | `api.groq.com` | 14.400 req/dia | Assistente IA |
| GitHub Releases API | `api.github.com/repos/jrlampa/sisPROJETOS_v1.1/releases` | Pública | Auto-update check |

### Notas Importantes

- **GROQ_API_KEY** deve ser obtida em [console.groq.com](https://console.groq.com) (gratuito)
- O sistema funciona completamente sem a Groq API (módulo IA desativado)
- Endpoint do update checker pode ser sobrescrito via `SISPROJETOS_UPDATE_ENDPOINT`

---

## 🔄 Fluxo de Atualização

1. `MainApp.__init__()` → aguarda 1200ms → `check_updates_on_startup()`
2. Consulta `db.get_update_settings()` → verifica se update está habilitado
3. `UpdateChecker.should_check_now()` → verifica intervalo (padrão: 1 dia)
4. Thread daemon → `check_for_updates()` → GitHub Releases API
5. Se disponível → `messagebox.askyesno()` → `webbrowser.open(release_url)`

---

## 📦 Build e Distribuição

### Processo de Build (Windows)

```powershell
# 1. Build executável
python -m PyInstaller sisprojetos.spec --clean --noconfirm

# 2. Gerar instalador
iscc sisPROJETOS.iss

# Output: installer_output/sisPROJETOS_v2.x.x_Setup.exe
```

### Configuração PyInstaller (`sisprojetos.spec`)

- Modo: `onedir` (pasta única, não onefile)
- `optimize=2`, `strip=True`
- Exclui: `tests`, `pytest`, `setuptools`
- Target: x86_64 Windows

---

## 🎨 Design System

**Arquivo:** `src/styles.py` — Classe `DesignSystem`

```python
PRIMARY = "#1E88E5"      # Azul principal
BG_WINDOW = "#F5F7FA"    # Fundo janela
BG_PANEL = "#FFFFFF"     # Fundo painéis
TEXT_MAIN = "#2C3E50"    # Texto principal
SUCCESS = "#27AE60"      # Verde sucesso
ERROR = "#E74C3C"        # Vermelho erro
```

- Tema: Light Mode (glassmorphism)
- Tipografia: Arial (sistema)
- Espaçamento: PADDING_SM=10, PADDING_MD=20, PADDING_LG=30

---

## 📝 Convenções de Código

### PEP 8 com adaptações

- Max line length: 119 caracteres
- Docstrings: Google Style em português
- Type hints: usados nos módulos utils (atualizar gradualmente)

### Commits (Conventional Commits)

```
feat: nova funcionalidade
fix: correção de bug
refactor: refatoração sem mudança de comportamento
test: adição/correção de testes
docs: documentação
chore: tarefas de build/infra
security: correção de vulnerabilidade
```

### Módulo Padrão (Checklist)

Ao criar um novo módulo em `src/modules/novo_modulo/`:
- [ ] `logic.py` — lógica pura, sem GUI, com `get_logger(__name__)`
- [ ] `gui.py` — interface CTkFrame, thin frontend
- [ ] `__init__.py` — importações do módulo
- [ ] Registrar em `src/main.py` → `MainApp`
- [ ] Criar `tests/test_novo_modulo.py` com cobertura ≥70%
- [ ] Documentar no MEMORY.md

---

## 🔍 Problemas Conhecidos e TODOs

| Prioridade | Problema | Status | Arquivo |
|-----------|---------|--------|---------|
| 🔴 Alta | DXF filepath sem validação de traversal | ✅ Corrigido | `src/utils/dxf_manager.py` |
| 🔴 Alta | ezdxf API `set_pos` obsoleta → `set_placement` | ✅ Corrigido | `src/utils/dxf_manager.py` |
| 🔴 Alta | Cobertura de testes < 80% (CI falha) | ✅ Corrigido | `tests/`, `.coveragerc` |
| 🟡 Média | `pytest-cov` ausente em requirements.txt | ✅ Corrigido | `requirements.txt` |
| 🟡 Média | `__init__.py` ausente em módulos (cqt, electrical, etc.) | ✅ Corrigido | `src/modules/*/` |
| 🟡 Média | Tabela `poles` vazia no banco de dados | ✅ Corrigido | `src/database/db_manager.py` |
| 🟡 Média | `resistivity` ausente em `cable_technical_data` | ✅ Corrigido | `src/database/db_manager.py` |
| 🟡 Média | Resistividade do Al hardcoded como fallback | ✅ Corrigido | `electrical/logic.py` (agora do DB) |
| 🟡 Média | Logger ausente em `cqt/logic.py` | ✅ Corrigido | `src/modules/cqt/logic.py` |
| 🟡 Média | Sanitizer não integrado em logic modules | ✅ Corrigido | Todos os módulos logic usam sanitizer |
| 🟡 Média | Versão em `__version__.py` desatualizada (2.0.0 vs 2.1.0) | ✅ Corrigido | `src/__version__.py` |
| 🟡 Média | Comentários excessivos em `catenaria/logic.py` | ✅ Corrigido | `src/modules/catenaria/logic.py` |
| 🟢 Baixa | Dark mode não implementado | ✅ Implementado v2.0.0 | `src/styles.py` |
| 🟡 Média | Logger + sanitizer ausentes em `converter/logic.py` | ✅ Corrigido | `src/modules/converter/logic.py` |
| 🟡 Média | `ai_assistant/logic.py` com `sys.path.append` anti-pattern; sem logger/sanitizer | ✅ Corrigido | `src/modules/ai_assistant/logic.py` |
| 🟡 Média | `test_converter.py` acima de 500 linhas (765) | ✅ Corrigido | `tests/test_converter_edge_cases.py` criado |
| 🟡 Média | Dockerfile LABEL version desatualizado (2.0.0) | ✅ Corrigido | `Dockerfile` |
| 🟡 Média | 16 arquivos src/ não formatados com black (CI lint falha) | ✅ Corrigido | `black src/ --line-length 119` aplicado |
| 🟡 Média | Importações incorretas em ~25 arquivos src/ (isort) | ✅ Corrigido | `isort src/ --profile black` aplicado |
| 🟡 Média | Cobertura real 99% (linhas 64-65 ai_assistant e 39-40 catenary route não cobertas) | ✅ Corrigido | 3 novos testes; `pragma: no cover` em sys.path guard |
| 🟡 Média | Sem `pyproject.toml` (black/isort sem config) | ✅ Corrigido | `pyproject.toml` criado com config black+isort |
| 🟡 Média | API REST incompleta para BIM (sem endpoints de dados mestres) | ✅ Corrigido | `src/api/routes/data.py` criado com 3 endpoints GET |
| 🟡 Média | CHANGELOG.md desatualizado (apenas v2.0.0, sem v2.1.0) | ✅ Corrigido | Seção [2.1.0] adicionada com todas as mudanças da série |
| 🟡 Média | Type hints ausentes em módulos logic | ✅ Completo | Todos os módulos logic + db_manager atualizados |
| 🔄 Planejado | Type hints em `converter/logic.py` | ✅ Completo (v2.1.0) | Todas as anotações + Tuple[float, ...] para coords |
| 🔄 Planejado | POST /api/v1/converter/kml-to-utm | ✅ Implementado (v2.1.0) | Aceita KML Base64, retorna UTM JSON; integração BIM geoespacial |
| 🔄 Planejado | POST /api/v1/projects/create | ✅ Implementado (v2.1.0) | Cria estrutura de pastas de projeto; último módulo sem endpoint REST |
| 🟡 Média | test_api.py acima de 500 linhas (516) | ✅ Corrigido | test_api_bim.py criado; test_api.py reduzido para 334 linhas |
| 🔄 Planejado | GET /api/v1/electrical/materials | ✅ Implementado | Lista materiais e resistividades do catálogo DB para integração BIM |
| 🔄 Planejado | GET /api/v1/pole-load/suggest | ✅ Implementado | Sugestão de postes por força sem cálculo completo (BIM standalone) |
| 🟡 Média | test_cqt.py acima de 500 linhas (após black: 550) | ✅ Corrigido | test_cqt_sanitizer.py criado; test_cqt.py reduzido para 488 linhas |
| 🟡 Média | DXF gerado usa posição 3D para TEXT (sem distinção 2.5D) | ✅ Corrigido | TEXT usa `set_placement((x,y))` — plano XY; POINT usa `(x,y,z)` — Z=altitude |
| 🟡 Média | Type hints ausentes em `dxf_manager.py` (métodos públicos) | ✅ Corrigido | Todos os métodos anotados com tipos corretos |
| 🔄 Planejado | Testes DXF específicos headless com coordenadas reais | ✅ Implementado | `tests/test_dxf_content.py` — 22 testes; ezdxf substitui accoreconsole.exe |
| 🔄 Planejado | Testes de catenária para vãos 100m, 500m, 1km | ✅ Implementado | `tests/test_catenary.py` — 3 novos testes de vão padrão NBR 5422 |
| 🔄 Planejado | Arquitetura orientada DDD | ✅ Implementado | `src/domain/` — 4 value objects (UTMCoordinate, CatenaryResult, VoltageDropResult, SpanResult) + 3 entidades (Conductor, Pole, Concessionaire); 47 testes em `tests/test_domain.py` |
| 🔄 Planejado | ARCHITECTURE.md desatualizado (v2.0, 388 testes, sem DDD, sem API) | ✅ Atualizado | Reescrito com diagrama de camadas DDD+MVC, tabelas de endpoints, convenção DXF 2.5D, instrução de testes |
| 🟢 Baixa | Plugin architecture | Roadmap v2.1 | N/A |

---

## 🗺️ Roadmap

### v2.0.0 (2026-02-21 — Lançamento Inicial da Série 2.x)
- [x] Reescrita completa Python 2.7 → Python 3.12 (breaking change = major bump)
- [x] Interface CustomTkinter (era Tkinter)
- [x] Arquitetura MVC desacoplada
- [x] 8 módulos funcionais com separação GUI/Logic
- [x] Logging centralizado (utils/logger.py)
- [x] Auto-update checker (utils/update_checker.py)
- [x] CI/CD com GitHub Actions
- [x] Docker para desenvolvimento/testes
- [x] MEMORY.md (este arquivo)
- [x] Cobertura de testes **100%** (388 testes)
- [x] Módulo `utils/sanitizer.py` — sanitização centralizada de dados de entrada
- [x] API REST FastAPI para integração Half-way BIM (`src/api/`)
- [x] Dark mode — `src/styles.py` com `set_dark_mode()` / `is_dark_mode()`
- [x] Logger padronizado em todos os módulos logic
- [x] Sanitizer integrado em `electrical/logic.py`
- [x] Sanitizer integrado em `catenaria/logic.py`, `pole_load/logic.py`, `cqt/logic.py`, `project_creator/logic.py`

### v2.1.0 (Q3 2026)
- [x] Dark mode persistido em app_settings (DB) — `get_appearance_settings()` / `save_appearance_settings()` em db_manager.py; aba "Aparência" em settings/gui.py
- [ ] Plugin architecture
- [ ] Multi-language support (i18n)

### v2.2.0 (2027)
- [ ] Web version (React + FastAPI)
- [ ] Collaborative editing
- [ ] Mobile companion app (React Native)

---

## 👥 Roles de Desenvolvimento

| Role | Responsabilidade |
|------|-----------------|
| **Tech Lead** | Arquitetura, decisões técnicas, code review |
| **Dev Fullstack Sênior** | Feature development, refactoring, testes |
| **DevOps/QA** | CI/CD, Docker, testes E2E, qualidade |
| **UI/UX Designer** | Interface pt-BR, design system, UX |
| **Estagiário** | Ideias criativas, protótipos, pesquisa |

---

## 📅 Histórico de Sessões

| Data | Versão | Alterações Principais |
|------|--------|--------------------|
| 2026-02-21 | 2.0.0 | Sessões de desenvolvimento consolidadas na v2.0.0: logging, update checker, CI/CD, Docker, cobertura 100% (388 testes), sanitizer, API REST FastAPI, dark mode, sanitizer integrado em electrical/logic.py, logger em cqt/logic.py |
| 2026-02-21 | 2.0.0 | Análise de maturidade: 1.0.0 incoerente pois legacy Python 2.7 era v1.1.0; reescrita completa Python 3.12 = breaking change = major bump para 2.0.0; badges do README atualizados (125→388 testes, 45%→100% cobertura) |
| 2026-02-21 | 2.1.0 | Dark mode persistido em DB: `get_appearance_settings()` / `save_appearance_settings()` em db_manager.py; aba "Aparência" em settings/gui.py; 5 novos testes (total 393) |
| 2026-02-21 | 2.1.0 | Sanitizer integrado em todos os módulos logic (catenaria, pole_load, cqt, project_creator); versão corrigida em `__version__.py`; comentários excessivos removidos de catenaria/logic.py; 15 novos testes de sanitização (total 410) |
| 2026-02-21 | 2.1.0 | Logger + sanitizer adicionados em converter/logic.py e ai_assistant/logic.py; removido sys.path.append anti-pattern de ai_assistant/logic.py; test_converter.py modularizado (765→390 linhas) → test_converter_edge_cases.py criado; Dockerfile LABEL versão corrigido (2.0.0→2.1.0); 5 novos testes sanitizer para converter; total 415 testes |
| 2026-02-21 | 2.1.0 | pyproject.toml criado (black+isort config); black aplicado a 16 arquivos src/; isort aplicado a 25 arquivos src/; 3 novos testes (ai_assistant empty msg + catenary None-result via mock); api/app.py pragma:no cover em sys.path guard; cobertura real 100%; total 418 testes |
| 2026-02-21 | 2.1.0 | Adicionados 3 endpoints GET de dados mestres para integração BIM: GET /api/v1/data/conductors, /data/poles, /data/concessionaires; src/api/routes/data.py criado; 3 novos schemas Pydantic (ConductorOut, PoleOut, ConcessionaireOut); 12 novos testes (total 430, 100% cobertura) |
| 2026-02-21 | 2.1.0 | CHANGELOG.md atualizado com seção [2.1.0] completa; type hints adicionados em electrical/logic.py e catenaria/logic.py (Optional, Dict, List, NDArray); 22 docs de auditoria stale movidos para docs/archive/ |
| 2026-02-21 | 2.1.0 | GET /api/v1/electrical/materials e GET /api/v1/pole-load/suggest adicionados; get_all_resistivities() em db_manager; get_materials() em ElectricalLogic; MaterialOut + PoleSuggestResponse schemas; 11 novos testes; test_cqt.py modularizado (550→488 linhas) → test_cqt_sanitizer.py criado; black aplicado a 15 test files; total 454 testes, 100% cobertura, 14 endpoints REST |
| 2026-02-21 | 2.1.0 | DXF 2.5D: `create_points_dxf` corrigido — POINT usa `(x,y,z)` onde z=altitude (convenção survey NBR 13133); TEXT usa `set_placement((x,y))` — Z=0, plano XY; type hints completos em dxf_manager.py; test_dxf_content.py criado com 22 testes headless estruturais (ezdxf substitui accoreconsole.exe) com coordenadas reais UTM 23K E=788547 N=7634925 e lat=-22.15018/lon=-42.92185; 3 testes de vão NBR 5422 (100m, 500m, 1km) em test_catenary.py; total 482 testes, 100% cobertura |
| 2026-02-21 | 2.1.0 | Camada de domínio DDD implementada: `src/domain/value_objects.py` (UTMCoordinate, CatenaryResult, VoltageDropResult, SpanResult — frozen dataclasses com invariantes de negócio); `src/domain/entities.py` (Conductor, Pole, Concessionaire — com regras de domínio); `src/domain/__init__.py`; 47 testes em `tests/test_domain.py` (imutabilidade, validações, propriedades calculadas); ARCHITECTURE.md reescrito com diagrama de camadas DDD+MVC, tabela de endpoints, convenção DXF 2.5D; total 529 testes, 100% cobertura |

---

*Este arquivo é mantido automaticamente. Sempre atualize ao finalizar uma sessão de desenvolvimento.*
