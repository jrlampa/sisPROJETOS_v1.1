# AUDITORIA FASE 1: Mapear Estrutura e Tecnologias
**sisPROJETOS v2.0 - Engenharia e Projetos**

## Resumo Executivo

Projeto de aplicação desktop em Python para cálculos de engenharia de distribuição de energia elétrica. Utiliza GUI com customtkinter e interlace com módulos especializados de cálculo.

**Estatísticas:**
- 24 arquivos Python (src/)
- 5 arquivos de teste
- 9 módulos independentes + Core (Database, Utils, Styles)
- 73+ pacotes Python instalados
- 1 executable distribuível (PyInstaller)
- 1 installer Windows (Inno Setup)

---

## 1. Estrutura do Projeto

### 1.1 Diretórios Principais

```
sisPROJETOS_revived/
├── src/
│   ├── main.py                          # Aplicação principal
│   ├── styles.py                        # Sistema de Design
│   ├── utils.py                         # Utilitários globais
│   ├── modules/                         # 9 módulos de negócio
│   ├── database/                        # Gerenciamento DB SQLite
│   ├── utils/                           # Utilitários adicionais
│   └── resources/                       # Assets (DB, templates, models)
├── tests/                               # Testes unitários (pytest)
├── build/                               # Artefatos PyInstaller
├── dist/                                # Executável compilado
├── installer_output/                    # Instalador Windows
├── requirements.txt                     # Dependências pip
├── sisPROJETOS.iss                     # Script Inno Setup
├── sisprojetos.spec                     # Spec PyInstaller (legado)
├── verify_setup.py                      # Verificação setup
└── README.md

Resources Directory:
├── models/                              # Modelos de dados
├── sisprojetos.db                       # Database SQLite
└── templates/
    ├── prancha.dwg                      # Template AutoCAD
    ├── cqt.xlsx                         # Template planilha CQT
    └── ambiental.xlsx                   # Template ambiental
```

### 1.2 Arquivos Python por Diretório

| Diretório | Arquivos | Propósito |
|-----------|----------|----------|
| src/ | main.py | Ponto de entrada, MainApp, MenuFrame |
| src/ | styles.py | DesignSystem, temas, cores, tipografia |
| src/ | utils.py | resource_path(), helpers globais |
| database/ | db_manager.py (167 linhas) | DatabaseManager - gerenciador SQLite |
| modules/ | __init__.py | Package marker |
| **9 Módulos** | gui.py, logic.py, report.py | Interface, lógica, relatórios |

---

## 2. Arquitetura dos 9 Módulos

### 2.1 Padrão MVC (Model-View-Controller)

Cada módulo segue estrutura padrão:
```
modulo/
├── __init__.py      # Imports e inicialização
├── gui.py           # View - Interface customtkinter
├── logic.py         # Model - Cálculos/processamento
└── report.py        # Report - Exportação resultados (se aplicável)
```

### 2.2 Descrição Detalhada de Módulos

#### 1. **CONVERTER** (Conversor de Coordenadas)
- **Arquivo:** `modules/converter/`
- **Linhas:** ~116 (logic.py)
- **Função:** Converter KMZ/KML → UTM → XLSX/DXF
- **Dependências:** zipfile, pandas, ezdxf, pyproj, fastkml
- **Classe Principal:** ConverterLogic
  - `load_file(filepath)` - Carrega KMZ/KML
  - `convert_coordinates(lat, lon, from_crs, to_crs)` - Converte coords
  - `export_dataframe(df, output_path, format)` - Exporta XLSX/DXF
- **Entrada:** Arquivos KMZ (Google Earth)
- **Saída:** Pontos UTM em Excel/DXF

#### 2. **CATENÁRIA** (Cálculos de Catenária)
- **Arquivo:** `modules/catenaria/`
- **Linhas:** ~181 (logic.py)
- **Função:** Cálculos de flecha, tração e curva catenária
- **Dependências:** numpy, DatabaseManager
- **Classe Principal:** CatenaryLogic
  - `load_conductors()` - Carrega condutores do BD
  - `calculate_profile(L, T0, theta)` - Calcula perfil catenário
  - `calculate_sag(L, T0, P)` - Calcula flecha
  - `calculate_tension(P, L, sag)` - Calcula tração
  - `conductor_loading(conductor_name, ambient_conditions)` - Carrega do condutor
- **Normas:** NBR 5422 (Linhas aéreas)
- **Entrada:** Comprimento, tração, temperatura, condutor
- **Saída:** Flecha, tração, curva catenária

#### 3. **POLE LOAD** (Esforços em Postes)
- **Arquivo:** `modules/pole_load/`
- **Linhas:** ~198 (logic.py) + report.py
- **Função:** Cálculo de resultante de forças em postes
- **Dependências:** math, DatabaseManager
- **Classe Principal:** PoleLoadLogic
  - `load_poles()` - Carrega especificações de postes
  - `load_concessionaires_data()` - Padrões Light/Enel
  - `calculate_resultant(angle1, trac1, angle2, trac2, ...)` - Soma vetorial
  - `apply_safety_factor(force, concessionaire)` - Fator de segurança
  - `get_enel_method()` / `get_light_method()` - Métodos específicos
- **Padrões:** Light e Enel
- **Entrada:** Ângulos, trações de condutores
- **Saída:** Força resultante, ângulo, direção

#### 4. **ELECTRICAL** (Cálculos Elétricos)
- **Arquivo:** `modules/electrical/`
- **Linhas:** ~63 (logic.py)
- **Função:** Queda de tensão em circuitos
- **Dependências:** math, DatabaseManager (sem testes específicos)
- **Classe Principal:** ElectricalLogic
  - `get_resistivity(material)` - Busca resistividade
  - `calculate_voltage_drop(current, length, section)` - Queda tensão
  - `calculate_current(power, voltage, pf)` - Calcula corrente
  - `get_cable_data(cable_name)` - Dados do cabo
- **Normas:** NBR 5410
- **Entrada:** Corrente, comprimento, seção, material
- **Saída:** Queda de tensão (%)

#### 5. **CQT** (Qualidade e Tensão de Cabos)
- **Arquivo:** `modules/cqt/`
- **Linhas:** ~172 (logic.py)
- **Função:** Análise de qualidade e tensão de cabos
- **Dependências:** math, collections, DatabaseManager
- **Classe Principal:** CQTLogic
  - Tabela DMDI (Demanda por classe)
  - `get_cable_coefs()` - Coeficientes de cabos
  - `calculate_demand(distance, cable_class)` - Demanda
  - `analyze_tension_profile(cable_profile)` - Análise tensão
- **Normas:** CNS-OMBR-MAT-19-0285 (Enel)
- **Entrada:** Cabo, classe, distância
- **Saída:** Qualidade, tensão, parâmetros

#### 6. **PROJECT CREATOR** (Gerenciador de Projetos)
- **Arquivo:** `modules/project_creator/`
- **Linhas:** ~80+ (logic.py)
- **Função:** Criar estrutura de pastas e templates de projeto
- **Dependências:** os, shutil, datetime
- **Classe Principal:** ProjectCreatorLogic
  - `create_structure(project_name, base_path)` - Cria estrutura
  - Cria pastas: 1_Documentos, 2_Desenhos, 3_Calculos, 4_Fotos
  - Copia templates: prancha.dwg, cqt.xlsx, ambiental.xlsx
- **Entrada:** Nome projeto, caminho base
- **Saída:** Diretório estruturado com templates

#### 7. **AI ASSISTANT** (Consultoria com IA)
- **Arquivo:** `modules/ai_assistant/`
- **Linhas:** ~83 (logic.py)
- **Função:** Consultor técnico via Groq API (llama-3.3-70b)
- **Dependências:** groq, python-dotenv
- **Classe Principal:** AIAssistantLogic
  - `get_response(question, project_context)` - chat IA
  - Conhecimento de: NBR 15688, NBR 15214, NBR 5422, padrões Light/Enel
  - Contexto de projeto (pole_load, catenária, elétrica, CQT)
- **Entrada:** Pergunta, contexto técnico
- **Saída:** Resposta consultoria técnica

#### 8. **SETTINGS** (Configurações)
- **Arquivo:** `modules/settings/`
- **Função:** Interface de configurações do aplicativo
- **Dependências:** yaml, json (TBD)
- **GUI:** Tela de settings

#### 9. **DATABASE** (Gerenciador Centralizado)
- **Arquivo:** `src/database/db_manager.py` (167 linhas)
- **Classe:** DatabaseManager
- **Função:** Gerenciar SQLite de forma centralizada
- **Características Principais:**
  - AppData path para escrita garantida em PyInstaller
  - Cópia automática da DB de resources se necessário
  - Suporte a fallback de criação de DB vazia
  - Get connection com sqlite3
  - Inicialização de schema automática
- **Tabelas:**
  - `conductors` - Dados de condutores (nome, peso, tração)
  - `poles` - Especificações de postes
  - `concessionaires` - Padrões Light, Enel, etc
  - `cable_technical_data` - Parâmetros elétricos

---

## 3. Tecnologias e Dependências

### 3.1 Stack Tecnológico

| Categoria | Tecnologia | Versão | Propósito |
|-----------|-----------|--------|----------|
| **Linguagem** | Python | 3.12.10 | Desenvolvimento |
| **GUI** | customtkinter | 5.2.2 | Interface moderna |
| **Compilação** | PyInstaller | 6.19.0 | Gerar .exe standalone |
| **Installer** | Inno Setup | 6.7.0 | Windows installer |
| **Database** | SQLite3 | Integrado | Dados técnicos |
| **Numerics** | NumPy | 2.4.2 | Cálculos vetoriais |
| **Data** | Pandas | 3.0.0 | DataFrames, análise |
| **Geolocal** | pyproj | 3.7.2 | Transformação coords |
| **GIS** | fastkml | Integrado | Parse KML/KMZ |
| **CAD** | ezdxf | 1.4.3 | Exportração DXF |
| **Graphics** | Matplotlib | 3.10.8 | Gráficos/visualização |
| **AI** | Groq | Integrado | Consultor IA |
| **Configuration** | python-dotenv | Integrado | .env support |
| **Testing** | pytest | 9.0.2 | Testes unitários |
| **Testing** | pytest-mock | Integrado | Mock/fixtures |

### 3.2 Dependências Completas (requirements.txt)

```
# Core GUI
customtkinter          # Modern CTk framework

# Geolocation & Conversion
pyproj                 # Coordinate transformations
fastkml                # KML/KMZ parsing
shapely                # Geometry operations

# Data Processing
pandas                 # DataFrames
openpyxl               # Excel read/write
matplotlib             # Plotting

# CAD Export
ezdxf                  # DXF file handling

# AI Integration
groq                   # LLM API client
python-dotenv          # .env file support

# Testing
pytest                 # Unit testing
pytest-mock            # Mocking fixtures

# Supportive (transitive & bundled)
numpy (2.2.6)          # Numeric computing
Pillow                 # Image processing
pyproj-3.7.2           # Coordinate math
kiwisolver, contourpy  # Matplotlib deps
```

### 3.3 Estrutura de Venv

```
.venv/
├── Lib/site-packages/
│   ├── customtkinter/
│   ├── numpy/
│   ├── pandas/
│   ├── matplotlib/
│   ├── pyproj/
│   ├── groq/
│   └── [71 more packages]
├── Scripts/
│   ├── python.exe
│   ├── pip.exe
│   └── pytest.exe
└── [config files]
```

---

## 4. Fluxos de Dados

### 4.1 Fluxo Principal (Aplicação)

```
main.py (MainApp)
    ↓
MenuFrame (seleção de módulo)
    ↓
┌─────────────────────────────────────────────────┐
│  MÓDULO SELECIONADO (gui.py)                   │
│  └─ CriaDados (GUI customtkinter)              │
│     └─ Chama logic.py para cálculos            │
│        └─ DatabaseManager.get_connection()     │
│           └─ SQLite sisprojetos.db             │
└─────────────────────────────────────────────────┘
    ↓
Resultado (exibe na GUI)
    ↓
Exportação (XLSX, DXF, PDF via report.py)
```

### 4.2 Integração de Contexto (AI)

```
MainApp.project_context = {
    "pole_load": {...},
    "catenary": {...},
    "electrical": {...},
    "cqt": {...}
}
    ↓
AIAssistantGUI.get_response(question)
    ↓
AIAssistantLogic.get_response(question, project_context)
    ↓
Groq API (llama-3.3-70b)
    ↓
Resposta técnica contextualizada
```

### 4.3 Pipeline de Compilação

```
src/
    ↓
PyInstaller (--onedir, --windowed, encodings, resources)
    ↓
dist/sisPROJETOS/
├── sisPROJETOS.exe    (main executable)
├── python312.dll
├── encodings/
├── src/resources/     (copied)
└── [dependencies]
    ↓
Inno Setup (sisPROJETOS.iss)
    ↓
installer_output/sisPROJETOS_v2.0_Setup.exe (72 MB)
    ↓
Instalador Windows completo
```

---

## 5. Ciclo de Execução

### 5.1 Startup

1. `python src/main.py` ou `sisPROJETOS.exe`
2. MainApp inicializa com customtkinter
3. Carrega DesignSystem (cores, fontes)
4. Cria MenuFrame com 9 opções de módulos
5. DatabaseManager cria/copia BD no AppData
6. Mostra Menu inicial

### 5.2 Uso de Módulo (Exemplo: Pole Load)

1. Usuário clica em "Esforço no Poste"
2. MainApp.show_frame("PoleLoad")
3. PoleLoadGUI.tkraise() (mostra widget)
4. GUI exibe campos para entrada (ângulos, trações)
5. User clica "Calcular"
6. GUI chama PoleLoadLogic.calculate_resultant(...)
7. Logic acessa DatabaseManager.get_connection()
8. Calcula soma vetorial (math)
9. GUI exibe resultados
10. Usuario pode exportar via report.py → XLSX/PDF

### 5.3 Estrutura de Testes

```
tests/
├── test_ai_assistant.py        # 2 testes
├── test_catenary.py            # 4 testes
├── test_converter.py           # 3 testes
├── test_pole_load.py           # 4 testes
└── test_project_creator.py     # 2 testes
                                = 15 testes (100% passing)
```

---

## 6. Arquivo de Banco de Dados

### 6.1 Localização e Inicialização

```
Desenvolvimento:     src/resources/sisprojetos.db
Executável:          %APPDATA%/sisPROJETOS/sisprojetos.db
                     (copiado de resources no primeiro uso)
```

### 6.2 Schema (db_manager.py)

| Tabela | Colunas | Exemplo Dados |
|--------|---------|---------------|
| conductors | id, name, weight_kg_m, breaking_load_daN | CA-70, 0.35 kg/m, 580 daN |
| poles | id, code, working_load_daN, min_butt_daN | POD-30-3, 300 daN |
| concessionaires | id, name, specifications | Light, Enel |
| cable_technical_data | id, category, key_name, value | resistivity, Alumínio, 0.0282 |

---

## 7. Recursos Estáticos

### 7.1 Imagens/Assets

```
resources/
├── models/              # Modelos 3D/gráficos?
└── templates/
    ├── prancha.dwg      # Template AutoCAD (3D drawing)
    ├── cqt.xlsx         # Planilha CQT (Celeste/Qualidade)
    └── ambiental.xlsx   # Planilha Ambiental
```

### 7.2 Design System (styles.py)

Paleta de cores, tipografia, temas (Light mode):
- Core colors (primário, secundário, acento)
- Espaçamento, border radius
- Font families e sizes
- Estados UI (hover, focus, disabled)

---

## 8. Sistema de Compilação e Release

### 8.1 PyInstaller Configuration

```bash
python -m PyInstaller \
  --onedir \
  --windowed \
  --name sisPROJETOS \
  --add-data "src/resources:src/resources" \
  --add-data "src/database:src/database" \
  --hidden-import=encodings \
  --hidden-import=customtkinter \
  --hidden-import=tkinter \
  --clean \
  --noconfirm \
  src/main.py
```

**Output:** `dist/sisPROJETOS/sisPROJETOS.exe` (~72 MB)

### 8.2 Inno Setup Installer

```
sisPROJETOS.iss (Inno Setup script)
    ↓
ISCC.exe (compiler)
    ↓
installer_output/sisPROJETOS_v2.0_Setup.exe (72 MB)
    ↓
Windows installer com NSIS wrapper
```

---

## 9. Padrões e Convenções

### 9.1 Nomenclatura

- **Classes:** PascalCase (MainApp, PoleLoadGUI)
- **Funções/Métodos:** snake_case (load_conductors, calculate_resultant)
- **Constantes:** UPPER_SNAKE_CASE (UNIT_DIVISOR, BG_WINDOW)
- **Módulos:** Python standard (lowercase)

### 9.2 Organização de Código

- **Imports:** std lib → third party → local
- **Docstrings:** Português, descreve função e parâmetros
- **Type hints:** Progressivamente sendo adicionadas
- **Error handling:** try/except com mensagens úteis

### 9.3 Padrão de Módulo

```python
# 1. Imports
from database.db_manager import DatabaseManager
import numpy as np

# 2. Class Definition
class ModuleLogic:
    """Docstring in Portuguese."""
    
    def __init__(self):
        """Initialize."""
        self.db = DatabaseManager()
    
    def method_name(self, param):
        """Method docstring.
        
        Args:
            param (type): Description
        
        Returns:
            type: Description
        """
        pass
```

---

## 10. Métricas de Projeto

| Métrica | Valor |
|---------|-------|
| Linhas de código Python | ~2000+ |
| Módulos de negócio | 9 |
| Classes principais | 10+ |
| Métodos/Funções | 100+ |
| Testes unitários | 15 (100% passing) |
| Pacotes externos | 73+ |
| Arquivos Python | 24 |
| Arquivos de teste | 5 |
| Tamanho executável | 72 MB |
| Tamanho installer | 72 MB |
| Suporte Plataformas | Windows (10+), Python 3.12 |

---

## 11. Dependências Conhecidas e Atuais

### 11.1 Resolvidas

✅ **Problemas anteriormente corrigidos:**
- AttributeError: DADOS_CONCESSIONARIAS (pole_load) → Resolvido
- ModuleNotFoundError: encodings encoding_hook → Resolvido
- sqlite3.OperationalError: readonly database → Resolvido via AppData
- AttributeError: CABOS_COEFS (CQT) → Resolvido

### 11.2 Observações Técnicas

- **AppData Integration:** Database escrita em %APPDATA%/sisPROJETOS/ para suportar PyInstaller
- **Encoding:** Hidden imports para encodings especificados no PyInstaller
- **GUI Framework:** customtkinter oferece componentes modernos com suporte light/dark mode
- **AI Integration:** Groq API necessita GROQ_API_KEY no .env

---

## Conclusão da Fase 1

✅ **Estrutura:** Bem organizada em 9 módulos MVC independentes
✅ **Hub Central:** DatabaseManager + MainApp (contexto compartilhado)
✅ **Stack Moderno:** Python 3.12 + customtkinter + PyInstaller
✅ **Distribuição:** Executável + Instalador Windows automatizado
✅ **Testes:** 15/15 passing com pytest
✅ **Documentação:** Docstrings em português, normas técnicas claramente referenciadas

**Status:** Pronto para Fase 2 (Auditoria de Qualidade e Erros)
