# 🏗️ Arquitetura do sisPROJETOS v2.1

## Visão Geral

sisPROJETOS é uma aplicação desktop para engenharia de distribuição de energia elétrica, desenvolvida em Python com CustomTkinter para interface gráfica.

**Padrão Arquitetural:** MVC desacoplado + **Domain-Driven Design (DDD)**  
**Linguagem:** Python 3.12+  
**Interface:** CustomTkinter (Tk/Tcl) — pt-BR  
**API REST:** FastAPI + uvicorn (Half-way BIM)  
**Build:** PyInstaller + Inno Setup

---

## Arquitetura em Camadas (DDD + MVC)

```
┌─────────────────────────────────────────────────────────┐
│              Interface (View — GUI)                       │
│  src/modules/*/gui.py  ←  CustomTkinter CTkFrame         │
└────────────────────────┬────────────────────────────────┘
                         │ thin frontend — chama logic
┌────────────────────────▼────────────────────────────────┐
│           Application Layer (API REST + Logic)            │
│  src/api/routes/*.py   ←  FastAPI routers (BIM endpoints)│
│  src/modules/*/logic.py ← regras de aplicação            │
└────────────────────────┬────────────────────────────────┘
                         │ usa domain objects
┌────────────────────────▼────────────────────────────────┐
│                Domain Layer (DDD)                         │
│  src/domain/value_objects.py  — imutáveis, sem infra     │
│  src/domain/entities.py       — com identidade + regras  │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│              Infrastructure Layer                         │
│  src/database/db_manager.py  — SQLite3 CRUD              │
│  src/utils/dxf_manager.py    — ezdxf 2.5D export         │
│  src/utils/sanitizer.py      — validação de entrada       │
│  src/utils/logger.py         — logging centralizado       │
└─────────────────────────────────────────────────────────┘
```

---

## Estrutura de Diretórios

```
sisPROJETOS_revived/
├── src/                           # Código-fonte principal
│   ├── __version__.py             # Versioning centralizado (v2.1.0)
│   ├── main.py                    # Entry point da aplicação
│   ├── styles.py                  # Design System (cores, fontes, dark mode)
│   │
│   ├── domain/                    # ✨ Camada de Domínio (DDD)
│   │   ├── __init__.py            # Exportações do domínio
│   │   ├── value_objects.py       # Objetos de valor imutáveis
│   │   └── entities.py            # Entidades com regras de negócio
│   │
│   ├── modules/                   # Módulos funcionais (MVC)
│   │   ├── project_creator/       # Criação de projetos
│   │   ├── pole_load/             # Cálculo de esforços em postes
│   │   ├── catenaria/             # Cálculo de catenárias (NBR 5422)
│   │   ├── electrical/            # Queda de tensão (NBR 5410)
│   │   ├── cqt/                   # BDI e Queda de Tensão (Enel)
│   │   ├── converter/             # Conversão KMZ→UTM→DXF
│   │   ├── ai_assistant/          # Assistente IA (Groq LLaMA 3.3)
│   │   └── settings/              # Configurações gerais
│   │
│   ├── api/                       # API REST (Half-way BIM)
│   │   ├── app.py                 # Fábrica FastAPI
│   │   ├── schemas.py             # Modelos Pydantic (request/response)
│   │   └── routes/                # Endpoints por domínio
│   │       ├── electrical.py      # POST voltage-drop; GET materials
│   │       ├── cqt.py             # POST calculate
│   │       ├── catenary.py        # POST calculate
│   │       ├── pole_load.py       # POST resultant; GET suggest
│   │       ├── data.py            # GET conductors, poles, concessionaires
│   │       ├── converter.py       # POST kml-to-utm
│   │       └── project_creator.py # POST create
│   │
│   ├── database/                  # Infraestrutura SQLite
│   │   ├── db_manager.py          # CRUD + dados pré-populados
│   │   └── schema.sql             # Esquema DDL
│   │
│   └── utils/                     # Utilitários transversais
│       ├── __init__.py            # resource_path() + path traversal guard
│       ├── logger.py              # Logging centralizado (RotatingFileHandler)
│       ├── sanitizer.py           # Sanitização/validação de entrada
│       ├── dxf_manager.py         # Exportação DXF 2.5D (ezdxf)
│       ├── update_checker.py      # Auto-update via GitHub Releases API
│       └── resource_manager.py    # Gerenciamento de templates/assets
│
├── tests/                         # Testes (pytest + pytest-cov)
│   ├── test_domain.py             # ✨ 47 testes da camada de domínio DDD
│   ├── test_dxf_content.py        # 22 testes headless DXF (ezdxf)
│   ├── test_api.py                # Endpoints de cálculo
│   ├── test_api_bim.py            # Endpoints BIM (data, converter, projects)
│   └── ...                        # Demais testes (529 total, 100% cobertura)
│
├── docs/                          # Documentação
│   └── archive/                   # Relatórios de auditoria (histórico)
├── Dockerfile                     # Imagem Docker (Python + deps)
├── docker-compose.yml             # Serviços dev + test
├── pyproject.toml                 # Config black + isort
└── pytest.ini                    # Config pytest + cobertura
```

---

## Camada de Domínio (DDD)

### Value Objects (`src/domain/value_objects.py`)

Objetos **imutáveis** (`frozen=True`) definidos pelos seus valores, com validação de invariantes de negócio em `__post_init__`. Não dependem de infraestrutura.

| Value Object | Atributos | Invariantes |
|-------------|-----------|------------|
| `UTMCoordinate` | `easting`, `northing`, `zone`, `elevation` | easting > 0, northing > 0, zone não-vazio |
| `CatenaryResult` | `sag`, `tension`, `catenary_constant` | sag ≥ 0, tension > 0, catenary_constant > 0 |
| `VoltageDropResult` | `drop_v`, `drop_percent`, `material` | drop ≥ 0, material não-vazio; `is_within_limit` → drop ≤ 5% (NBR 5410) |
| `SpanResult` | `vao`, `angulo`, `flecha` | vao ≥ 0, 0 ≤ angulo ≤ 360, flecha ≥ 0 |

```python
# Exemplo: coordenada UTM real do projeto (Google Earth Pro)
from src.domain.value_objects import UTMCoordinate, CatenaryResult

p = UTMCoordinate(easting=788547.0, northing=7634925.0, zone="23K", elevation=720.0)
assert p.easting == 788547.0  # imutável

r = CatenaryResult(sag=1.23, tension=2000.0, catenary_constant=130.5)
# ValueError se sag < 0, tension ≤ 0, etc.
```

### Entities (`src/domain/entities.py`)

Objetos com **identidade** e regras de negócio embutidas.

| Entidade | Atributos | Regras de Negócio |
|---------|-----------|------------------|
| `Conductor` | `name`, `weight_kg_m`, `breaking_load_daN`, `section_mm2` | name não-vazio, weight ≥ 0, breaking_load > 0 |
| `Pole` | `material`, `height_m`, `format`, `nominal_load_daN` | material/format não-vazios, height > 0, load > 0 |
| `Concessionaire` | `name`, `method` | method ∈ {'flecha', 'tabela'} |

```python
from src.domain.entities import Conductor, Concessionaire

c = Conductor(name="556MCM-CA", weight_kg_m=1.594, breaking_load_daN=13750.0)
conc = Concessionaire(name="Light", method="flecha")
# ValueError se method não for 'flecha' ou 'tabela'
```

---

## API REST — Half-way BIM

**Base URL:** `http://localhost:8000/api/v1`  
**Documentação:** `http://localhost:8000/docs` (Swagger UI)

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| POST | `/electrical/voltage-drop` | Queda de tensão (NBR 5410) |
| GET | `/electrical/materials` | Lista materiais/resistividades |
| POST | `/cqt/calculate` | CQT — Metodologia Enel |
| POST | `/catenary/calculate` | Catenária (NBR 5422) |
| POST | `/pole-load/resultant` | Resultante de esforços |
| GET | `/pole-load/suggest?force_daN=` | Sugestão de poste por força |
| GET | `/data/conductors` | Catálogo de condutores |
| GET | `/data/poles` | Catálogo de postes |
| GET | `/data/concessionaires` | Catálogo de concessionárias |
| POST | `/converter/kml-to-utm` | KML Base64 → UTM JSON |
| POST | `/projects/create` | Criação de estrutura de projeto |

---

## DXF 2.5D (ABNT NBR 13133)

O DXF gerado segue a convenção 2.5D:

- **POINT** entities: `location.z = elevation` (altitude em metros)
- **TEXT** entities: `set_placement((x, y))` — plano XY, Z=0
- **LWPOLYLINE** (catenária): entidade flat XY — visão de perfil/seção

Testado via ezdxf (equivalente headless ao accoreconsole.exe):

```bash
pytest tests/test_dxf_content.py -v  # 22 testes estruturais
```

Coordenadas de teste validadas:
- Ponto 1: UTM 23K E=788547 N=7634925 (Google Earth Pro)
- Ponto 2: lat=-22.15018 lon=-42.92185 → UTM E=714315.7 N=7549084.2
- Vãos catenária: 100m, 500m, 1000m (NBR 5422)

---

## Segurança

| Vetor | Mitigação |
|-------|-----------|
| SQL Injection | Todas queries usam `(?, ?)` parametrizado |
| Path Traversal | `resource_path()` e `_validate_output_path()` rejeitam `..` e null bytes |
| Sanitização de entrada | `utils/sanitizer.py` em todos os módulos logic |
| API Keys | Apenas em `.env` (no `.gitignore`), nunca hardcoded |
| Imutabilidade | Value objects `frozen=True` — proteção contra mutação acidental |

---

## Testes

**Framework:** pytest + pytest-cov + pytest-mock  
**Total:** 529 testes, **100% cobertura** (excluindo GUI/main.py via `.coveragerc`)

```bash
# Rodar todos os testes
cd sisPROJETOS_revived
pytest tests/ -v

# Com cobertura HTML
pytest tests/ -v --cov=src --cov-report=html

# Apenas domínio DDD
pytest tests/test_domain.py -v

# Apenas DXF headless
pytest tests/test_dxf_content.py -v

# Docker
docker compose run --rm test
```

---

## Build e Distribuição

### Executável (Windows)

```powershell
python -m PyInstaller sisprojetos.spec --clean --noconfirm
iscc sisPROJETOS.iss
# Output: installer_output/sisPROJETOS_v2.1.0_Setup.exe
```

### Docker

```bash
docker build -t sisprojetos:2.1.0 .
docker compose up dev    # ambiente de desenvolvimento
docker compose run test  # suite de testes
```

---

## Contribuir

Veja [CONTRIBUTING.md](CONTRIBUTING.md) para guidelines de desenvolvimento.

## Licença

MIT License — Veja [LICENSE.txt](LICENSE.txt)


---

## Estrutura de Diretórios

```
sisPROJETOS_revived/
├── src/                           # Código-fonte principal
│   ├── __version__.py             # ✨ Versioning centralizado
│   ├── main.py                    # Entry point da aplicação
│   ├── styles.py                  # Sistema de design (cores, fontes)
│   ├── utils.py                   # Utilidades globais
│   │
│   ├── modules/                   # Módulos funcionais (MVC)
│   │   ├── project_creator/       # Criação de projetos
│   │   ├── pole_load/             # Cálculo de esforços em postes
│   │   ├── catenaria/             # Cálculo de catenárias
│   │   ├── electrical/            # Dimensionamento elétrico
│   │   ├── cqt/                   # BDI e Queda de Tensão
│   │   ├── converter/             # Conversão KMZ→UTM→DXF
│   │   ├── ai_assistant/          # Assistente IA (Groq)
│   │   └── settings/              # Configurações gerais
│   │
│   ├── database/                  # Gerenciamento SQLite
│   │   ├── db_manager.py          # CRUD operations
│   │   └── schema.sql             # Esquema do banco
│   │
│   └── resources/                 # Assets estáticos
│       ├── templates/             # Templates DXF/Excel
│       └── db_template.db         # Database template
│
├── tests/                         # Testes unitários (pytest)
│   ├── test_electrical.py         # ✨ NOVO
│   ├── test_cqt.py               # ✨ NOVO
│   ├── test_converter.py          # ✨ Expandido
│   ├── test_catenary.py
│   ├── test_pole_load.py
│   ├── test_project_creator.py
│   └── test_ai_assistant.py
│
├── dist/                          # Build output (PyInstaller)
├── build/                         # Build artifacts temporários
├── installer_output/              # Instaladores gerados
│
├── sisprojetos.spec              # ✨ Configuração PyInstaller otimizada
├── sisPROJETOS.iss               # ✨ Configuração Inno Setup atualizada
├── LICENSE.txt                    # ✨ NOVO - Licença MIT
├── requirements.txt               # Dependências Python
└── README.md                      # Documentação principal
```

---

## Arquitetura MVC

### Model (Lógica de Negócio)

**Localização:** `src/modules/*/logic.py`

Cada módulo tem uma classe `*Logic` responsável por:
- Cálculos matemáticos/engenharia
- Acesso ao banco de dados
- Processamento de dados
- Validações de negócio

**Exemplo:**
```python
# src/modules/electrical/logic.py
class ElectricalLogic:
    def __init__(self):
        self.db = DatabaseManager()
    
    def calculate_voltage_drop(self, power_kw, distance_m, ...):
        # Lógica pura, sem GUI
        ...
```

### View (Interface Gráfica)

**Localização:** `src/modules/*/gui.py`

CustomTkinter widgets para apresentação:
- Formulários de entrada
- Tabelas de resultados
- Gráficos (matplotlib)
- Exportação de relatórios

**Exemplo:**
```python
# src/modules/electrical/gui.py
class ElectricalGUI(ctk.CTkFrame):
    def __init__(self, parent):
        self.logic = ElectricalLogic()
        # Setup GUI components
```

### Controller (Orquestração)

**Localização:** `src/main.py`

- Gerencia navegação entre módulos
- Compartilha contexto entre módulos
- Inicializa aplicação
- Gerencia lifecycle

---

## Módulos Funcionais

### 1. Project Creator
**Finalidade:** Cadastro e gerenciamento de projetos  
**Tecnologias:** SQLite, Tkinter  
**Principais Funções:**
- Criar novo projeto
- Editar informações
- Vincular documentos
- Gerar código de projeto

### 2. Pole Load (Esforços em Postes)
**Finalidade:** Cálculo de esforços mecânicos em estruturas  
**Tecnologias:** NumPy, Matplotlib  
**Principais Funções:**
- Soma vetorial de trações
- Análise de ancoragens
- Visualização gráfica
- Relatório técnico

### 3. Catenária
**Finalidade:** Cálculo de flechas e trações em condutores  
**Tecnologias:** NumPy, Matplotlib, ezdxf  
**Principais Funções:**
- Cálculo de flecha (equações catenária/parábola)
- Tração no condutor
- Exportação DXF
- Gráfico flecha x comprimento

### 4. Electrical (Dimensionamento Elétrico)
**Finalidade:** Cálculo de queda de tensão  
**Tecnologias:** Math, SQLite  
**Principais Funções:**
- Queda de tensão (MT/BT)
- Resistência por material
- Validação NBR 5410
- Seleção de condutores

### 5. CQT (BDI e Queda de Tensão)
**Finalidade:** Cálculo de CQT (Enel methodology)  
**Tecnologias:** Algoritmos de grafos (topological sort)  
**Principais Funções:**
- Validação de topologia de rede
- Fator de demanda (DMDI)
- Acumulação bottom-up
- Momento elétrico

### 6. Converter (KMZ→UTM→DXF)
**Finalidade:** Conversão de coordenadas geográficas  
**Tecnologias:** pyproj, fastkml, ezdxf, pandas  
**Principais Funções:**
- Parser KMZ/KML (Google Earth)
- Conversão lat/lon → UTM
- Exportação Excel/DXF
- Auto-detecção de zona UTM

### 7. AI Assistant
**Finalidade:** Assistente técnico IA  
**Tecnologias:** Groq API (LLaMA 3.3 70B)  
**Principais Funções:**
- Consultas técnicas de normas
- Análise de projetos
- Recomendações de dimensionamento
- Integração com contexto de outros módulos

### 8. Settings
**Finalidade:** Configurações globais  
**Tecnologias:** JSON, SQLite  
**Principais Funções:**
- Preferências de usuário
- Parâmetros de cálculo
- API keys
- Backup/restore

---

## Banco de Dados

**Tecnologia:** SQLite 3  
**Localização:** `%APPDATA%/sisPROJETOS/sisprojetos.db`

### Schema Principal

```sql
-- Projetos
CREATE TABLE projects (
    id INTEGER PRIMARY KEY,
    code TEXT UNIQUE,
    name TEXT,
    client TEXT,
    created_date TEXT,
    status TEXT
);

-- Dados técnicos de cabos
CREATE TABLE cable_technical_data (
    id INTEGER PRIMARY KEY,
    category TEXT,  -- 'resistivity', 'cqt_k_coef', etc.
    key_name TEXT,
    value REAL,
    unit TEXT
);

-- Configurações
CREATE TABLE settings (
    key TEXT PRIMARY KEY,
    value TEXT
);
```

### Acesso ao Banco

```python
from database.db_manager import DatabaseManager

db = DatabaseManager()
conn = db.get_connection()
cursor = conn.cursor()
cursor.execute("SELECT * FROM projects")
results = cursor.fetchall()
conn.close()
```

---

## Fluxo de Dados

```
┌─────────────┐
│   Usuário   │
└──────┬──────┘
       │
       v
┌─────────────────────────────────┐
│   main.py (MainApp CTk Window) │
│   - Tab Navigation              │
│   - Shared project_context      │
└─────────┬───────────────────────┘
          │
          v
   ┌──────┴───────┐
   │  Module GUI  │ (CTkFrame)
   └──────┬───────┘
          │
          v
   ┌──────┴────────┐
   │ Module Logic  │ (Pure Python)
   └──────┬────────┘
          │
   ┌──────┴────────────────┐
   │                       │
   v                       v
┌─────────┐        ┌──────────────┐
│  SQLite │        │ External API │
│Database │        │ (Groq, etc.) │
└─────────┘        └──────────────┘
```

---

## Sistema de Design (DesignSystem)

**Arquivo:** `src/styles.py`

```python
class DesignSystem:
    # Cores
    PRIMARY = "#1E88E5"       # Azul principal
    BG_WINDOW = "#F5F7FA"     # Fundo janela
    BG_PANEL = "#FFFFFF"      # Fundo painéis
    TEXT_DARK = "#2C3E50"     # Texto escuro
    
    # Tipografia
    FONT_TITLE = ("Arial", 24, "bold")
    FONT_H2 = ("Arial", 18, "bold")
    FONT_BODY = ("Arial", 12)
    
    # Espaçamento
    PADDING_SM = 10
    PADDING_MD = 20
    PADDING_LG = 30
```

**Aplicação:**
```python
frame.configure(fg_color=DesignSystem.BG_PANEL, corner_radius=15)
label.configure(text_color=DesignSystem.TEXT_DARK, font=DesignSystem.FONT_TITLE)
```

---

## Build e Distribuição

### PyInstaller (Executável)

```bash
python -m PyInstaller sisprojetos.spec --clean --noconfirm
```

**Otimizações aplicadas:**
- `optimize=2` - Bytecode otimizado
- `strip=True` - Remove debug symbols
- `excludes=['tests', 'pytest', 'setuptools']` - Reduz tamanho
- `target_arch='x86_64'` - Explícito 64-bit

### Inno Setup (Instalador)

```bash
iscc sisPROJETOS.iss
```

**Configurações:**
- `Compression=lzma2/ultra64` - Máxima compressão
- `PrivilegesRequired=lowest` - ✨ Não requer admin
- `DefaultDirName={localappdata}` - ✨ AppData em vez de Program Files
- `LicenseFile=LICENSE.txt` - ✨ EULA incluído

---

## Dependências Principais

| Package | Versão | Finalidade |
|---------|--------|-----------|
| customtkinter | 5.2.1+ | Interface gráfica moderna |
| numpy | 2.2+ | Cálculos matemáticos |
| pandas | 2.2+ | Manipulação de tabelas |
| matplotlib | 3.9+ | Gráficos técnicos |
| ezdxf | 1.3+ | Exportação CAD |
| pyproj | 3.7+ | Conversão coordenadas |
| fastkml | 1.0+ | Parser KML/KMZ |
| groq | 0.13+ | API IA |
| python-dotenv | 1.0+ | Variáveis ambiente |

**Total:** ~73 packages (incluindo dependências transitivas)

---

## Segurança

### API Keys
- Armazenadas em `.env` (root do projeto)
- **NÃO** commitadas no Git (`.gitignore`)
- Carregadas via `python-dotenv`

```python
from dotenv import load_dotenv
load_dotenv()
api_key = os.getenv("GROQ_API_KEY")
```

### SQL Injection Protection
✅ **TODAS** as queries usam prepared statements:
```python
cursor.execute("SELECT * FROM projects WHERE id=?", (project_id,))
```

### Path Traversal
✅ **IMPLEMENTADO:** `resource_path()` validada contra path traversal (src/utils/__init__.py)
✅ **IMPLEMENTADO:** `_validate_output_path()` em dxf_manager.py rejeita null bytes e caminhos suspeitos
✅ **IMPLEMENTADO:** `sanitize_filepath()` em utils/sanitizer.py para validação de entrada do usuário

---

## Testing Strategy

**Framework:** pytest + pytest-cov

### Cobertura Atual (v1.0.0)
- **Todos os módulos**: 100% ✅
- **Total de testes**: 388

**Meta:** manter 100% global

### Executar Testes
```bash
pytest tests/ -v --cov=src --cov-report=html
```

---

## Performance

### Otimizações Implementadas
1. **Build Size:** 206 MB → ~185 MB (excludes)
2. **Startup Time:** <3s (onedir mode)
3. **Database:** Índices em colunas `id`, `code`
4. **UPX:** Compression ativado (exceto runtime DLLs)

### Benchmarks
- Cálculo de catenária (100 pontos): <100ms
- Conversão KMZ (50 pontos): <500ms
- Query banco (1000 registros): <50ms

---

## Roadmap Arquitetural

### v2.1 (Próxima Release)
- [ ] Plugin system
- [ ] Multi-language support (i18n)
- [ ] Dark mode persistido em configurações

### v2.2
- [ ] Web version (React + FastAPI)
- [ ] Collaborative editing
- [ ] Real-time sync
- [ ] Mobile companion app

---

## Contribuir

Veja [CONTRIBUTING.md](CONTRIBUTING.md) para guidelines de desenvolvimento.

## Licença

MIT License - Veja [LICENSE.txt](LICENSE.txt)
