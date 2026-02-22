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
**Maturidade:** Produção (v2.1.0 — 841 testes, 100% cobertura, API REST com 24 endpoints, black+isort limpo, type hints completos em todos os módulos, DXF 2.5D, testes DXF headless com coordenadas reais, **camada de domínio DDD completa: 4 value objects + 3 entidades + 3 interfaces de repositório (ports) + 2 serviços de domínio + 3 adaptadores SQLite de infraestrutura + módulo de padrões regulatórios ANEEL/PRODIST com mecanismo de toast + padrões normativos disponíveis via API REST + verificação opcional de folga NBR 5422 no endpoint /catenary/calculate + pontos de curva catenária via include_curve + geração de DXF via API REST Base64 /catenary/dxf + GET /catenary/clearances (tabela de folgas mínimas NBR 5422/PRODIST por tipo de rede) + frontend electrical/gui.py com seletor de norma ANEEL/PRODIST/Concessionária + toast de aviso + catenaria/gui.py com verificação de folga ao solo NBR 5422 + CQT API com campos de conformidade Enel: CQT_LIMIT_PERCENT, within_enel_limit, segments_over_limit (CNS-OMBR-MAT-19-0285) + POST /pole-load/report (relatório PDF em Base64, fpdf2) + POST /converter/utm-to-dxf (pipeline BIM KML→UTM→DXF completo via API) + GET /projects/list (listagem de projetos existentes, BIM discovery) + schemas.py modularizado em schemas_bim.py + 24 testes E2E ponta-a-ponta (test_api_e2e.py) + DatabaseManager.add_pole() + settings/gui.py Postes tab completo (save_pole/refresh_poles) + pole_load/gui.py btn_suggest habilitado após cálculo + test_api_bim.py modularizado → test_api_pole_load.py (regra 500 linhas) + POST /catenary/batch (lote multi-vão BIM, até 20 vãos/chamada) + bug fix pole_load/gui.py project_context para IA + test_converter_edge_cases.py modularizado → test_converter_export.py (regra 500 linhas) + POST /electrical/batch (lote multi-circuito BIM, até 20 circuitos/chamada, per-item standard_name) + converter/gui.py → project_context["converter"] compartilha resultados com IA + POST /pole-load/batch (lote multi-poste BIM, 24º endpoint, completa trifeta de batch: catenary+electrical+pole-load; ConductorOut/PoleOut/ConcessionaireOut movidos de schemas.py para schemas_bim.py mantendo ambos os arquivos < 500 linhas)**) 

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

### Infra-Estrutura DDD (src/infrastructure/)

| Arquivo | Responsabilidade |
|---------|-----------------|
| `__init__.py` | Exporta adaptadores SQLite |
| `repositories.py` | `SQLiteConductorRepository`, `SQLitePoleRepository`, `SQLiteConcessionaireRepository` — implementações concretas dos Protocols de domínio |

### Padrões Regulatórios DDD (src/domain/standards.py)

| Constante | Fonte | Limite | Sobrepõe ABNT? | Toast |
|-----------|-------|--------|----------------|-------|
| `NBR_5410` | ABNT | 5% | Não | — |
| `PRODIST_MODULE8_BT` | ANEEL/PRODIST | 8% | Sim | ⚠️ ANEEL/PRODIST Módulo 8 aplicado (BT)... |
| `PRODIST_MODULE8_MT` | ANEEL/PRODIST | 7% | Sim | ⚠️ ANEEL/PRODIST Módulo 8 aplicado (MT)... |
| `LIGHT_BT` | CONCESSIONAIRE | 8% | Sim | ⚠️ Norma da concessionária Light (BT)... |
| `ENEL_BT` | CONCESSIONAIRE | 8% | Sim | ⚠️ Norma da concessionária Enel (BT)... |

**Regra:** Quando `standard.overrides_abnt=True`, exibir `standard.override_toast_pt_br` como toast na interface (ABNT ignorada).  
**Hierarquia:** CONCESSIONAIRE > ANEEL/PRODIST > ABNT


| Arquivo | Responsabilidade |
|---------|-----------------|
| `app.py` | Fábrica FastAPI + registro de rotas |
| `schemas.py` | Modelos Pydantic core (request/response) — re-exporta `schemas_bim.py` |
| `schemas_bim.py` | Modelos Pydantic BIM: KML, UTM, DXF, Projetos (< 500 linhas, regra de modularização) |
| `routes/electrical.py` | GET `/api/v1/electrical/standards`; GET `/api/v1/electrical/materials`; POST `/api/v1/electrical/voltage-drop` (suporte a ANEEL/PRODIST via `standard_name`); POST `/api/v1/electrical/batch` (até 20 circuitos/chamada) |
| `routes/cqt.py` | POST `/api/v1/cqt/calculate` |
| `routes/catenary.py` | POST `/api/v1/catenary/calculate` (inclui curva com `include_curve`; verificação folga ao solo com `min_clearance_m`); POST `/api/v1/catenary/dxf` (gera DXF em memória, retorna Base64); GET `/api/v1/catenary/clearances` (tabela NBR 5422/PRODIST de folgas mínimas por tipo de rede) |
| `routes/pole_load.py` | POST `/api/v1/pole-load/resultant`; GET `/api/v1/pole-load/suggest?force_daN=...`; POST `/api/v1/pole-load/report` (PDF Base64, fpdf2); POST `/api/v1/pole-load/batch` (lote de até 20 postes; falhas individuais não abortam o lote) |
| `routes/data.py` | GET `/api/v1/data/conductors`, `/data/poles`, `/data/concessionaires` |
| `routes/converter.py` | POST `/api/v1/converter/kml-to-utm`; POST `/api/v1/converter/utm-to-dxf` (completa pipeline BIM KML→UTM→DXF) |
| `routes/health.py` | GET `/health` — status, versão, DB, ambiente, timestamp (Docker HEALTHCHECK) |
| `routes/project_creator.py` | POST `/api/v1/projects/create`; GET `/api/v1/projects/list` (BIM project discovery) |

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
**Total de testes:** 808 (todos passando, 100% cobertura)  
**Cobertura estimada:** **100%** (excluindo GUI/main.py via .coveragerc)

### Mapeamento de Testes

| Arquivo de Teste | Módulo Testado | Status |
|-----------------|---------------|--------|
| `test_electrical.py` | `electrical/logic.py` | ✅ |
| `test_cqt.py` | `cqt/logic.py` (cálculo principal) | ✅ |
| `test_cqt_sanitizer.py` | `cqt/logic.py` (sanitização de entradas: trafo_kva, social_class) | ✅ |
| `test_converter.py` | `converter/logic.py` (principal) | ✅ |
| `test_converter_edge_cases.py` | `converter/logic.py` (edge cases: load_file, UTM) | ✅ |
| `test_converter_export.py` | `converter/logic.py` (export: CSV, DXF, dxf_to_buffer) | ✅ |
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
| `test_api.py` | `api/` (endpoints de cálculo: electrical, cqt, catenary, pole-load, health; + GET /electrical/materials + GET /pole-load/suggest; + `TestCatenaryNBR5422Clearance` — verificação folga ao solo via min_clearance_m) | ✅ |
| `test_api_catenary.py` | `api/routes/catenary.py` (include_curve: 7; POST /catenary/dxf: 11; TestCatenaryNBR5422Clearance: 5; TestCatenaryNBR5422ClearancesTable: 6 testes tabela NBR 5422/PRODIST) | ✅ |
| `test_api_standards.py` | `api/routes/electrical.py` (GET /electrical/standards + POST /voltage-drop com standard_name ANEEL/PRODIST) | ✅ |
| `test_api_bim.py` | `api/routes/data.py`, `api/routes/converter.py` (KML→UTM), `api/routes/project_creator.py` (BIM, GET /projects/list) — modularizado 503→329 linhas | ✅ |
| `test_api_pole_load.py` | `api/routes/pole_load.py` (POST /pole-load/report) + `api/routes/converter.py` (POST /converter/utm-to-dxf) — extraído de test_api_bim.py (regra 500 linhas) | ✅ |
| `test_api_e2e.py` | Testes E2E ponta-a-ponta: 24 testes encadeando chamadas reais de API (pipelines BIM KML→UTM→DXF, PRODIST, catenária, esforços, health, projetos) | ✅ |
| `test_domain.py` | `domain/value_objects.py`, `domain/entities.py` (DDD: UTMCoordinate, CatenaryResult, VoltageDropResult, SpanResult, Conductor, Pole, Concessionaire) | ✅ |
| `test_domain_services.py` | `domain/services.py` (CatenaryDomainService, VoltageDropDomainService) e `domain/repositories.py` (Protocol stubs) | ✅ |
| `test_infrastructure.py` | `infrastructure/repositories.py` (SQLiteConductorRepository, SQLitePoleRepository, SQLiteConcessionaireRepository: Protocol isinstance checks, entity mapping, DDD E2E) | ✅ |
| `test_standards.py` | `domain/standards.py` (VoltageStandard, padrões ANEEL/PRODIST, toast, hierarquia normativa) | ✅ |
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
| 🔄 Planejado | DDD Repository Interfaces (ports) | ✅ Implementado | `src/domain/repositories.py` — 3 Protocol classes: ConductorRepository, PoleRepository, ConcessionaireRepository; `# pragma: no cover` nos stubs Ellipsis |
| 🔄 Planejado | DDD Domain Services | ✅ Implementado | `src/domain/services.py` — CatenaryDomainService (fórmula hiperbólica NBR 5422; is_within_clearance); VoltageDropDomainService (fórmulas mono/trifásica NBR 5410); 59 testes em `tests/test_domain_services.py` |

| ✅ Implementado | ANEEL/PRODIST na API REST (GET /standards + standard_name em /voltage-drop) | ✅ Implementado | `GET /api/v1/electrical/standards` lista 5 padrões; `POST /voltage-drop` aceita `standard_name`; `allowed` usa `standard.check()`; `override_toast` em pt-BR retornado; 22 novos testes |
| 🟡 Média | test_api.py acima de 500 linhas (597 linhas) | ✅ Corrigido | `TestElectricalStandardsEndpoint` + `TestElectricalVoltageDropWithStandard` movidos para `tests/test_api_standards.py` (196 linhas); test_api.py reduzido a 485 linhas |
| 🔄 Implementado | GET /health enriquecido com DB status, environment, ISO 8601 timestamp | ✅ Implementado | `src/api/routes/health.py` — HealthResponse schema; degraded quando DB inacessível; Dockerfile HEALTHCHECK adicionado |
| 🔄 Planejado | CatenaryDomainService.is_within_clearance() não chamada na API | ✅ Implementado | `POST /api/v1/catenary/calculate` aceita `min_clearance_m` opcional → retorna `within_clearance: Optional[bool]` (True se flecha ≤ distância mínima NBR 5422); 5 novos testes em `TestCatenaryNBR5422Clearance` |
| 🔄 Planejado | Frontend GUI sem suporte a normas ANEEL/PRODIST | ✅ Implementado | `electrical/gui.py`: seletor `cmb_standard` (5 normas); cálculo dinâmico de limite; toast amarelo quando concessionária/PRODIST sobrepõe ABNT |
| 🔄 Planejado | Frontend GUI sem verificação de folga ao solo | ✅ Implementado | `catenaria/gui.py`: campo `ent_clearance` opcional (dist. mínima ao solo NBR 5422); cálculo `h_min = min(ha,hb) − sag`; "✅ Folga OK" / "❌ Folga insuficiente" |
| 🟡 Média | CQT GUI usa magic number `5.0` para threshold de bottleneck | ✅ Corrigido | `cqt/gui.py`: substituído por `self.logic.CQT_LIMIT_PERCENT` (DRY principle) |
| 🟡 Média | CQT API não retorna informações de conformidade regulatória | ✅ Corrigido | `CQTLogic.CQT_LIMIT_PERCENT=5.0` (CNS-OMBR-MAT-19-0285); `CQTResponse` com `segments_over_limit`; summary com `within_enel_limit`, `cqt_limit_percent`, `segments_over_limit` |
| 🔴 Alta | `pole_load/gui.py`: `btn_suggest` nunca habilitado após cálculo (bug) | ✅ Corrigido | `self.btn_suggest.configure(state="normal")` adicionado em `calculate()` |
| 🟡 Média | `pole_load/gui.py`: label "Sugerir Melhor Poste (IA)" enganoso (é consulta ao DB) | ✅ Corrigido | Renomeado para "Sugerir Poste Adequado" |
| 🔴 Alta | `settings/gui.py`: `save_pole()` era `pass` — aba Postes não funcionava | ✅ Corrigido | `add_pole()` adicionado ao `DatabaseManager`; `save_pole()` + `refresh_poles()` implementados; `setup_poles_tab()` reescrito com 4 campos + lista |
| 🟡 Média | `test_api_bim.py` acima de 500 linhas (503) | ✅ Corrigido | `TestPoleLoadReportEndpoint` + `TestUTMToDxfEndpoint` extraídos para `tests/test_api_pole_load.py`; test_api_bim.py = 329 linhas |
| 🔄 Planejado | Tabela de folgas mínimas NBR 5422/PRODIST não disponível via API | ✅ Implementado | `GET /api/v1/catenary/clearances` — 7 tipos de rede, clientes BIM usam para `min_clearance_m` |

| 2026-02-22 | 2.1.0 | POST /electrical/batch + cobertura 100% + contexto IA conversor: (1) `POST /api/v1/electrical/batch` adicionado (23º endpoint) — lote de até 20 circuitos; per-item `standard_name` (PRODIST/ANEEL/concessionária); falhas individuais não abortam o lote; 4 novos schemas (`VoltageBatchItem`, `VoltageBatchRequest`, `VoltageBatchResponseItem`, `VoltageBatchResponse`) em `schemas_bim.py`; (2) cobertura 100% recuperada — catenary batch `except Exception` (linhas 257-259) coberto via mocker; electrical batch ramos None+exception cobertos com 2 testes adicionais; (3) `converter/gui.py` agora define `controller.project_context["converter"]` após conversão KML bem-sucedida — era o único módulo sem compartilhamento de contexto; `ai_assistant/logic.py` trata chave "converter" no bloco de contexto; `main.py` inicializa `"converter": None` no dict; 1 novo teste com assert específico "Conversão KML: 7 pontos convertidos para UTM"; (4) todos os 3 comentários de code review corrigidos: teste com itertools.chain para None path ordenado; assertion de IA com string exata; VoltageBatchItem sem texto redundante "(> 0)"; CodeQL: 0 alertas; 831 testes, 100% cobertura, black+isort clean, 23 endpoints |
| 2026-02-22 | 2.1.0 | POST /pole-load/batch — completa trifeta de batch da API REST: (1) `POST /api/v1/pole-load/batch` adicionado (24º endpoint) — lote de até 20 postes; per-item `concessionaria`, `condicao`, `cabos`; falha por `KeyError` (concessionária inválida) ou exceção geral retorna `success=False` sem abortar lote; 4 novos schemas (`PoleLoadBatchItem`, `PoleLoadBatchRequest`, `PoleLoadBatchResponseItem`, `PoleLoadBatchResponse`) adicionados a `schemas.py`; resposta inclui `resultant_force`, `resultant_angle` e `suggested_poles` por item de sucesso; (2) Pre-emptive schema modularization: `ConductorOut`, `PoleOut`, `ConcessionaireOut` movidos de `schemas.py` para `schemas_bim.py` (sem dependências upstream, movim. limpo) — `schemas.py` fica em 495 linhas (< 500 ✅), `schemas_bim.py` em 432 linhas (< 500 ✅) após adicionar schemas de batch; (3) 10 novos testes em `TestPoleLoadBatchEndpoint` em `tests/test_api_pole_load.py` (307 linhas); code review comment corrigido: `original_calc = None` não-usado removido do test helper; CodeQL: 0 alertas; 841 testes, 100% cobertura, black+isort clean, 24 endpoints |

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
| 2026-02-21 | 2.1.0 | DDD completado com ports + services: `src/domain/repositories.py` — 3 Protocol interfaces (ConductorRepository, PoleRepository, ConcessionaireRepository) com `# pragma: no cover` nos stubs; `src/domain/services.py` — CatenaryDomainService (fórmula hiperbólica cosh, NBR 5422, is_within_clearance) + VoltageDropDomainService (mono/trifásico, NBR 5410, is_within_limit); 59 testes em `tests/test_domain_services.py` (incluindo testes com vãos 100m/500m/1km e coords reais); `src/domain/__init__.py` atualizado para exportar novos símbolos; total 588 testes, 100% cobertura |
| 2026-02-21 | 2.1.0 | DDD Infrastructure Layer completada: `src/infrastructure/repositories.py` — 3 adaptadores SQLite (SQLiteConductorRepository, SQLitePoleRepository, SQLiteConcessionaireRepository) implementando os Protocols de domínio; `src/utils.py` removido (código morto — sombreado pelo pacote `src/utils/`, continha função insegura); corrigidos 2 bugs em `db_manager.py` — (a) condutores pré-populados tinham breaking_load_daN=0 → corrigido com valores reais ABNT NBR 7271 (556MCM=7080, 397MCM=5050, 1/0AWG=5430, 4AWG=2655 daN); (b) descriptions de postes não-únicas causavam INSERT OR IGNORE silencioso — corrigido com prefixo de material nas descriptions; 51 testes em `tests/test_infrastructure.py`; CodeQL: 0 alertas; total 639 testes, 100% cobertura |
| 2026-02-21 | 2.1.0 | ANEEL/PRODIST integrado no domínio DDD: `src/domain/standards.py` criado com `VoltageStandard` (frozen dataclass imutável, source∈{ABNT/ANEEL/PRODIST/CONCESSIONAIRE}, `check(drop_percent)`, `override_toast_pt_br` para toast pt-BR); 5 padrões pré-definidos: NBR_5410 (5%), PRODIST_MODULE8_BT (8%, Res. Norm. 956/2021), PRODIST_MODULE8_MT (7%), LIGHT_BT (8%, concessionária), ENEL_BT (8%, concessionária); `ALL_STANDARDS` frozenset + `get_standard_by_name()`; `VoltageDropResult.is_within_standard(standard)` adicionado; `VoltageDropDomainService.calculate(standard=...)` aceita padrão opcional sem alterar o cálculo; `domain/__init__.py` exporta todos os novos símbolos; 46 testes em `tests/test_standards.py`; CodeQL: 0 alertas; total 685 testes, 100% cobertura |
| 2026-02-21 | 2.1.0 | ANEEL/PRODIST integrado na API REST: `GET /api/v1/electrical/standards` — lista 5 padrões normativos (NBR 5410, PRODIST BT/MT, Light, Enel) como `StandardOut` com `Optional[str] override_toast_pt_br`; `POST /api/v1/electrical/voltage-drop` aceita campo opcional `standard_name` — resolve via `get_standard_by_name()`, usa `standard.check()` para `allowed`, retorna `standard_name` e `override_toast` pt-BR; desconhecido → HTTP 422 com referência ao endpoint /standards; `VoltageDropRequest` + `VoltageDropResponse` + `StandardOut` schemas atualizados; 22 novos testes em `test_api.py`; CodeQL: 0 alertas; total 707 testes, 100% cobertura, 15 endpoints REST |
| 2026-02-21 | 2.1.0 | POST /api/v1/catenary/dxf adicionado: gera DXF em memória (StringIO → encode UTF-8) via `DXFManager.create_catenary_dxf_to_buffer()`, retorna Base64 JSON (padrão consistente com converter KML→UTM); `CatenaryRequest` ganhou `include_curve: bool = False` → quando True, `CatenaryResponse` inclui `curve_x`/`curve_y` (100 pontos) para renderização BIM; `CatenaryDxfRequest`/`CatenaryDxfResponse` schemas adicionados; tag "Catenária" em app.py atualizada para mencionar DXF; 18 novos testes em `tests/test_api_catenary.py`; CodeQL: 0 alertas; 735 testes, 100% cobertura |
| 2026-02-21 | 2.1.0 | GET /health enriquecido: `src/api/routes/health.py` criado (SRP); `HealthResponse` schema (status/version/db_status/environment/timestamp); inline health removido de app.py; Dockerfile HEALTHCHECK adicionado (urllib.request, 30s/10s/15s/3); 5 novos testes health (db_status, environment, timestamp, version, degraded via mock); TestCatenaryNBR5422Clearance movido para test_api_catenary.py (test_api.py 523→464 linhas, abaixo de 500); 735 testes, 100% cobertura, CodeQL: 0 alertas |
| 2026-02-21 | 2.1.0 | Frontend + Backend: `electrical/gui.py` — seletor de norma regulatória (NBR 5410/PRODIST BT/MT/Light BT/Enel BT) via `cmb_standard` + `_STANDARD_DISPLAY_MAP`; status dinâmico com limite real da norma (não mais "5%" hardcoded); toast amarelo `lbl_toast` exibido ao usuário quando concessionária/PRODIST sobrepõe ABNT. `catenaria/gui.py` — campo opcional `ent_clearance` (Dist. mínima ao solo NBR 5422); verificação correta `h_min = min(ha,hb) − sag ≥ min_clearance_m`; exibe "✅ Folga OK (h_min=X.XXm ≥ Y.Ym)" ou "❌ Folga insuficiente"; 735 testes, 100% cobertura, CodeQL: 0 alertas |
| 2026-02-21 | 2.1.0 | CQT compliance API: `CQT_LIMIT_PERCENT: float = 5.0` class constant adicionado a `CQTLogic` (CNS-OMBR-MAT-19-0285 — critério de projeto, conservador em relação ao PRODIST 8%); `calculate()` retorna `within_enel_limit: bool` + `segments_over_limit: List[str]` + `cqt_limit_percent: float` no summary; `CQTResponse` schema atualizado com `segments_over_limit` top-level; `cqt/gui.py` magic number `5.0` substituído por `self.logic.CQT_LIMIT_PERCENT` (DRY); `tests/test_cqt_compliance.py` criado (8 novos testes); 2 novos testes em `test_api.py`; 1 assertion adicionada em `test_cqt.py`; 745 testes, 100% cobertura, CodeQL: 0 alertas |
| 2026-02-21 | 2.1.0 | PDF report API + UTM-to-DXF API + fix fpdf2: `fpdf2>=2.8.0` adicionado a `requirements.txt` (dep ausente que tornava `report.py` broken); `report.py` refatorado — `_build_pdf()` extraído; `generate_report_to_buffer() → bytes` adicionado; type hints completos. `converter/logic.py`: `import io` + `save_to_dxf_to_buffer(df) → bytes` (mesmo DXF, sem filesystem). `schemas.py`: 5 novos schemas (`PoleLoadReportRequest`, `PoleLoadReportResponse`, `UTMPointIn`, `UTMToDxfRequest`, `UTMToDxfResponse`). `POST /api/v1/pole-load/report` — calcula resultante + gera PDF em Base64 (conforme padrão /catenary/dxf). `POST /api/v1/converter/utm-to-dxf` — completa o pipeline BIM: KML → /kml-to-utm → /utm-to-dxf → DXF; 28 novos testes em `test_api_bim.py`; 4 novos testes em `test_converter_edge_cases.py`; bug fix: duplicatas de rotas removidas de `pole_load.py` e `converter.py`; CodeQL: 0 alertas; 769 testes, 100% cobertura, black+isort clean, 19 endpoints |
| 2026-02-21 | 2.1.0 | Modularização de schemas + GET /projects/list + 24 testes E2E: `schemas.py` (520→421 linhas) modularizado em `schemas_bim.py` (141 linhas, schemas KML/UTM/DXF/Projetos) — re-export mantém todos os imports de rotas inalterados. `GET /api/v1/projects/list` adicionado a `routes/project_creator.py` — lista subdiretórios de um `base_path`, proteção null-byte/PermissionError/OSError; `ProjectListResponse` schema em `schemas_bim.py`. `tests/test_api_e2e.py` criado com 24 testes E2E ponta-a-ponta: pipeline BIM KML→UTM→DXF; pipeline elétrico PRODIST; pipeline catenária 100m/500m/1km+DXF; pipeline esforços resultante→suggest→PDF; health+catálogo; projetos create→list. `test_api_bim.py` ampliado com 6 testes para GET /projects/list (null-byte 422, PermissionError 403, OSError 500, 404, lista vazia, lista ordenada). CodeQL: 0 alertas; 799 testes, 100% cobertura, black+isort clean, 20 endpoints |
| 2026-02-21 | 2.1.0 | Bug fix + feature completion: (1) `pole_load/gui.py` — `btn_suggest` era inicializado como `disabled` e nunca habilitado após cálculo → corrigido: `self.btn_suggest.configure(state="normal")` adicionado em `calculate()` junto com `btn_report`; rótulo corrigido de "Sugerir Melhor Poste (IA)" para "Sugerir Poste Adequado" (não é IA, é consulta ao catálogo DB). (2) `DatabaseManager.add_pole()` adicionado — seguindo padrão exato de `add_conductor()` com `try/except IntegrityError/finally conn.close()`. (3) `settings/gui.py` — `save_pole()` implementado completamente (era `pass`): valida campos, chama `db.add_pole()`, exibe resultado; `setup_poles_tab()` reescrito com 4 campos (`ent_pole_mat`, `ent_pole_desc`, `ent_pole_height`, `ent_pole_load`) usando `create_input()` helper (consistente com aba Condutores); `refresh_poles()` adicionado para exibir catálogo atual em textbox. 4 novos testes em `test_db_settings.py` (add_pole success, duplicate, default_format + test_get_all_poles atualizado para verificar 13 postes pré-populados). CodeQL: 0 alertas; 802 testes, 100% cobertura, black+isort clean |
| 2026-02-21 | 2.1.0 | Modularização de testes BIM + GET /catenary/clearances: `test_api_bim.py` modularizado (503→329 linhas) — `TestPoleLoadReportEndpoint` + `TestUTMToDxfEndpoint` extraídos para novo `tests/test_api_pole_load.py` (190 linhas); ambos abaixo de 500 linhas. `GET /api/v1/catenary/clearances` adicionado (21º endpoint): retorna tabela NBR 5422 Tabela 6 / PRODIST Módulo 6 com 7 tipos de rede (BT_URBANA=6.0m, BT_RURAL=5.5m, MT_URBANA=7.0m, MT_RURAL=7.0m, AT_69KV=8.5m, AT_138KV=9.5m, AT_230KV=10.5m) + nota sobre hierarquia normativa; clientes BIM usam para obter o `min_clearance_m` correto sem hardcodar a norma. `ClearanceTypeOut` + `ClearancesResponse` schemas adicionados em `schemas_bim.py` e re-exportados via `schemas.py`. 6 novos testes em `TestCatenaryNBR5422ClearancesTable`. CodeQL: 0 alertas; 808 testes, 100% cobertura, black+isort clean, 21 endpoints |
| 2026-02-22 | 2.1.0 | Bug fix + batch + modularização: (1) `pole_load/gui.py` — `self.controller.project_context["pole_load"] = res` adicionado em `calculate()`; era o único módulo que não compartilhava contexto com o assistente IA mesmo com o handler já implementado em `ai_assistant/logic.py`. (2) `test_converter_edge_cases.py` modularizado (495→372 linhas) — `TestConverterCSVExportEdgeCases` + `TestConverterDxfToBuffer` extraídos para novo `tests/test_converter_export.py` (112 linhas); ambos abaixo de 500 linhas; docstrings atualizados. (3) `POST /api/v1/catenary/batch` adicionado (22º endpoint): processa até 20 vãos de catenária em uma chamada; falhas individuais (`success=False`) não abortam os demais itens; suporta `label` e `min_clearance_m` por item; 4 novos schemas (`CatenaryBatchItem`, `CatenaryBatchRequest`, `CatenaryBatchResponseItem`, `CatenaryBatchResponse`) em `schemas_bim.py`; re-exportados via `schemas.py`; docstring documenta que `weight_kg_m=0` falha ao nível do item por design (batch resilience); `catenary.py` tag atualizada; 10 novos testes em `TestCatenaryBatchEndpoint`; CodeQL: 0 alertas; 831 testes, 100% cobertura, black+isort clean, 23 endpoints |



