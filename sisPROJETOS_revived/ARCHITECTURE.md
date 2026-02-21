# 🏗️ Arquitetura do sisPROJETOS v1.0

## Visão Geral

sisP ROJETOS é uma aplicação desktop para engenharia de distribuição de energia elétrica, desenvolvida em Python com CustomTkinter para interface gráfica.

**Padrão Arquitetural:** MVC (Model-View-Controller)  
**Linguagem:** Python 3.12+  
**Interface:** CustomTkinter (Tk/Tcl)  
**Build:** PyInstaller + Inno Setup

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

### v1.1 (Próxima Release)
- [ ] Plugin system
- [ ] Multi-language support (i18n)
- [ ] Dark mode persistido em configurações

### v1.2
- [ ] Web version (React + FastAPI)
- [ ] Collaborative editing
- [ ] Real-time sync
- [ ] Mobile companion app

---

## Contribuir

Veja [CONTRIBUTING.md](CONTRIBUTING.md) para guidelines de desenvolvimento.

## Licença

MIT License - Veja [LICENSE.txt](LICENSE.txt)
