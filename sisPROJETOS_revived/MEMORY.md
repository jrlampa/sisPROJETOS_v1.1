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
**Maturidade:** Produção (v2.1.1 — cobertura de testes 90%)

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

### Utilitários (src/utils/)

| Arquivo | Responsabilidade |
|---------|-----------------|
| `logger.py` | Logging centralizado com RotatingFileHandler |
| `update_checker.py` | Verificação de updates via GitHub Releases API |
| `dxf_manager.py` | Criação de arquivos DXF (catenária, pontos UTM) |
| `resource_manager.py` | Gerenciamento de recursos (templates, assets) |
| `__init__.py` | `resource_path()` com proteção path traversal |

---

## 🔒 Decisões de Segurança

### Decisões Já Implementadas

1. **Path Traversal em `resource_path()`**: Validado — rejeita `..` e caminhos absolutos (src/utils/__init__.py)
2. **SQL Injection**: Todas as queries usam parametrização `(?, ?)` — VERIFICADO em db_manager.py
3. **API Keys**: Armazenadas apenas em `.env` (no .gitignore) — NUNCA hardcoded
4. **Secrets**: `.env` está no `.gitignore` root e no `.gitignore` do subprojeto

### Pendências de Segurança

- **DXF Manager filepath validation**: `create_catenary_dxf()` e `create_points_dxf()` aceitam filepath sem validação explícita de traversal

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
**Total de testes:** 244 (todos passando)  
**Cobertura estimada:** ~90% (excluindo GUI/main.py via .coveragerc)

### Mapeamento de Testes

| Arquivo de Teste | Módulo Testado | Status |
|-----------------|---------------|--------|
| `test_electrical.py` | `electrical/logic.py` | ✅ |
| `test_cqt.py` | `cqt/logic.py` | ✅ |
| `test_converter.py` | `converter/logic.py` | ✅ |
| `test_converter_e2e.py` | Pipeline completo KMZ→DXF | ✅ |
| `test_catenary.py` | `catenaria/logic.py` | ✅ |
| `test_pole_load.py` | `pole_load/logic.py` | ✅ |
| `test_project_creator.py` | `project_creator/logic.py` | ✅ |
| `test_ai_assistant.py` | `ai_assistant/logic.py` | ✅ |
| `test_logger.py` | `utils/logger.py` | ✅ |
| `test_update_checker.py` | `utils/update_checker.py` | ✅ |
| `test_db_settings.py` | `database/db_manager.py` | ✅ |
| `test_dxf_manager.py` | `utils/dxf_manager.py` | ✅ |
| `test_version_styles.py` | `__version__.py`, `styles.py`, `utils/__init__.py` | ✅ |
| `test_resource_manager.py` | `utils/resource_manager.py` | ✅ |

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
| 🟡 Média | Resistividade do Al hardcoded como fallback | Aceitável | `electrical/logic.py` |
| 🟢 Baixa | Dark mode não implementado | Roadmap v2.2 | `src/styles.py` |
| 🟢 Baixa | Plugin architecture | Roadmap v2.2 | N/A |

---

## 🗺️ Roadmap

### v2.1.x (Atual)
- [x] Logging centralizado (utils/logger.py)
- [x] Auto-update checker (utils/update_checker.py)
- [x] CI/CD com GitHub Actions
- [x] Docker para desenvolvimento/testes
- [x] MEMORY.md (este arquivo)
- [x] Cobertura de testes ≥ 90% (244 testes)

### v2.2.0 (Q3 2026)
- [ ] Plugin architecture
- [ ] RESTful API (FastAPI) — para integração BIM
- [ ] Dark mode
- [ ] Multi-language support (i18n)

### v3.0.0 (2027)
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
| 2026-02-21 | 2.1.0 | Criação do MEMORY.md, Docker setup, fix DXF security |
| 2026-02-21 | 2.1.0 | Fix ezdxf `set_pos` → `set_placement`; add `pytest-cov` to requirements; add `__init__.py` a todos os módulos; criar `.coveragerc` excluindo GUI de cobertura; aumentar cobertura de 50% → 82% (198 testes); adicionar testes para dxf_manager, __version__, styles, utils, pole_load, project_creator |
| 2026-02-21 | 2.1.1 | Aumentar cobertura de 82% → 90% (244 testes); criar `test_resource_manager.py` (coverage 73% → 100%); expandir `test_update_checker.py` (65% → 100%); expandir `test_ai_assistant.py` (57% → 98%); expandir `test_db_settings.py` (73% → 94%); cobrir: history/context da IA, beta channel, URLError, custom endpoint, add_conductor, get_all_conductors/poles, ResourceManager frozen mode, singleton |

---

*Este arquivo é mantido automaticamente. Sempre atualize ao finalizar uma sessão de desenvolvimento.*
