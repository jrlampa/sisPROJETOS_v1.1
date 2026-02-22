# AUDITORIA FASE 5: Build e Release

**sisPROJETOS v2.0 - Análise de Build, Packaging e Distribuição**

---

## 1. Resumo Executivo

**Status Geral de Build: ⚠️ FUNCIONAL - REQUER MELHORIAS**

| Aspecto | Status | Score | Notas |
|---------|--------|-------|-------|
| **PyInstaller Config** | ✅ BOM | 8/10 | Configuração sólida |
| **Inno Setup Config** | ⚠️ MÉDIO | 6/10 | Faltam ícone e licença |
| **Build Artifacts** | ✅ BOM | 8/10 | Funcionais e testados |
| **Versioning** | ⚠️ MÉDIO | 5/10 | Hardcoded, sem automação |
| **Distribution** | ⚠️ MÉDIO | 6/10 | Sem code signing |
| **Documentation** | 🔴 FRACO | 3/10 | BUILD.md inexistente |

**Score Geral:** 6.0/10

---

## 2. Análise do PyInstaller

### 2.1 Configuração (sisprojetos.spec)

**Arquivo:** `sisprojetos.spec` (41 linhas)

```python
# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['src\\main.py'],              # ✅ Entry point correto
    pathex=[],                     # ✅ Não requer paths extras
    binaries=[],                   # ✅ Sem binários externos
    datas=[                        # ✅ Data files incluídos
        ('src/resources', 'src/resources'),
        ('src/database', 'src/database')
    ],
    hiddenimports=[                # ✅ Imports necessários
        'encodings',
        'customtkinter',
        'tkinter'
    ],
    hookspath=[],                  # ⚠️ Sem custom hooks
    hooksconfig={},
    runtime_hooks=[],              # ⚠️ Sem runtime hooks
    excludes=[],                   # ⚠️ Não exclui nada (tamanho maior)
    noarchive=False,
    optimize=0,                    # ⚠️ Sem otimização bytecode
)

pyz = PYZ(a.pure)                  # ✅ Python archive

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,         # ✅ Onedir mode
    name='sisPROJETOS',            # ✅ Nome correto
    debug=False,                   # ✅ Release mode
    bootloader_ignore_signals=False,
    strip=False,                   # ⚠️ Não remove symbols (debug)
    upx=True,                      # ✅ Compressão UPX ativada
    console=False,                 # ✅ Windowed app
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,              # ⚠️ Auto-detect (não explícito x64)
    codesign_identity=None,        # 🔴 SEM code signing
    entitlements_file=None,
)

coll = COLLECT(                    # ✅ Onedir distribution
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,                      # ✅ Compressão aplicada
    upx_exclude=[],                # ⚠️ Não exclui nada do UPX
    name='sisPROJETOS',
)
```

**Análise:**

| Item | Status | Nota |
|------|--------|------|
| Entry Point | ✅ src\\main.py | Correto |
| Distribution Mode | ✅ Onedir (COLLECT) | Melhor para grandes apps |
| Hidden Imports | ✅ encodings, customtkinter, tkinter | Necessários |
| Data Files | ✅ resources, database | Incluídos |
| Console | ✅ False | GUI app |
| UPX Compression | ✅ True | Reduz tamanho |
| Optimization | ⚠️ optimize=0 | Poderia usar optimize=2 |
| Code Signing | 🔴 None | NÃO ASSINADO |
| Target Architecture | ⚠️ None | Deveria ser x64 explícito |
| Excludes | ⚠️ Vazio | Poderia excluir tests, docs |

### 2.2 Build Output

**Diretório:** `dist/sisPROJETOS/`

```
Estatísticas:
- Arquivos: 2,132
- Tamanho Total: 206.40 MB (descompactado)
- Estrutura: Onedir (_internal + sisPROJETOS.exe)
```

**Estrutura:**
```
dist/sisPROJETOS/
├── sisPROJETOS.exe          # Main executable (~15 MB)
├── _internal/               # All dependencies
│   ├── python312.dll        # Python runtime
│   ├── _tkinter.pyd         # Tkinter bindings
│   ├── customtkinter/       # CTk library
│   ├── numpy/               # NumPy
│   ├── pandas/              # Pandas
│   ├── matplotlib/          # Matplotlib
│   ├── ezdxf/               # CAD library
│   ├── pyproj/              # GIS library
│   ├── groq/                # AI library
│   ├── encodings/           # Python encodings (FIX anterior)
│   ├── src/                 # Application code
│   │   ├── resources/       # Templates, DB
│   │   └── database/        # DB schema
│   └── [73+ other packages]
└── [outros arquivos DLL/PYD]
```

**Pontos Positivos:**
- ✅ Estrutura organizada
- ✅ Todos os recursos incluídos
- ✅ Encodings presentes (fix anterior mantido)
- ✅ Database copiada para _internal

**Pontos Negativos:**
- ⚠️ 206 MB é grande (mas aceitável para app desktop)
- ⚠️ Muitas dependências (~73 packages)
- ⚠️ Testes incluídos no bundle (não deveriam estar)

### 2.3 Comando de Build Atual

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

**vs. Usando .spec:**
```bash
python -m PyInstaller sisprojetos.spec --clean --noconfirm
```

**Observação:** Ambos geram o mesmo resultado. O comando CLI sobrescreve o .spec se usado.

### 2.4 Melhorias Sugeridas para .spec

```python
# RECOMENDADO: sisprojetos.spec (otimizado)

a = Analysis(
    ['src\\main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('src/resources', 'src/resources'),
        # Database NÃO deve ir no bundle - AppData é melhor
        # ('src/database', 'src/database'),  # ← REMOVER
    ],
    hiddenimports=[
        'encodings',
        'customtkinter',
        'tkinter',
        # Adicionar outros se necessário
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tests',            # ← Excluir testes
        'pytest',           # ← Excluir pytest
        'setuptools',       # ← Excluir build tools
        'pip',              # ← Excluir pip
    ],
    noarchive=False,
    optimize=2,             # ← Otimização bytecode nível 2
)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='sisPROJETOS',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,             # ← Remove debug symbols
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch='x86_64',   # ← Explícito x64
    codesign_identity=None, # TODO: Adicionar certificado
    entitlements_file=None,
    icon='src/resources/icon.ico',  # ← Adicionar ícone
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=True,             # ← Remove símbolos
    upx=True,
    upx_exclude=[
        'vcruntime140.dll', # ← Não comprimir runtime DLLs
        'python312.dll',
    ],
    name='sisPROJETOS',
)
```

**Impacto Estimado:**
- Redução de tamanho: 10-20 MB (excluindo tests/pytest/setuptools)
- Performance: +5-10% (optimize=2, strip=True)
- Profissionalismo: +100% (ícone, x64 explícito)

---

## 3. Análise do Inno Setup

### 3.1 Configuração (sisPROJETOS.iss)

**Arquivo:** `sisPROJETOS.iss` (63 linhas)

```ini
[Setup]
AppId={{C6E2A3C4-7B1E-4E5D-B6C2-F0E1D2C3B4A5}  # ✅ GUID fixo (bom)
AppName={#MyAppName}                           # ✅ sisPROJETOS
AppVersion={#MyAppVersion}                     # ✅ 2.0
AppVerName={#MyAppName} {#MyAppVersion}        # ✅ SisPROJETOS 2.0
AppPublisher={#MyAppPublisher}                 # ⚠️ "Engenharia de Projetos" genérico
DefaultDirName={autopf}\{#MyAppName}           # ✅ Program Files
DefaultGroupName={#MyAppName}                  # ✅ Start Menu
AllowNoIcons=yes
OutputDir=installer_output                     # ✅ Separado de dist
OutputBaseFilename=sisPROJETOS_v2.0_Setup      # ✅ Nome versionado
SetupIconFile=                                 # 🔴 VAZIO - SEM ÍCONE!
Compression=lzma2/ultra64                      # ✅ Compressão máxima
SolidCompression=yes                           # ✅ Solid archive
WizardStyle=modern                             # ✅ Visual moderno
ArchitecturesInstallIn64BitMode=x64compatible  # ✅ x64 support
UninstallDisplayIcon={app}\{#MyAppExeName}     # ✅ Ícone uninstall
DisableProgramGroupPage=yes                    # ✅ Simplificado
PrivilegesRequired=admin                       # ⚠️ REQUER ADMIN!
LicenseFile=                                   # 🔴 VAZIO - SEM LICENÇA!
```

**Análise Detalhada:**

| Item | Valor | Status | Nota |
|------|-------|--------|------|
| AppId | GUID fixo | ✅ | Permite updates in-place |
| Versão | 2.0 | ✅ | Hardcoded (não automatizado) |
| Publisher | "Engenharia de Projetos" | ⚠️ | Genérico demais |
| Destino | Program Files | ✅ | Padrão Windows |
| Ícone | (vazio) | 🔴 | **SEM ÍCONE!** |
| Compressão | lzma2/ultra64 | ✅ | Melhor compressão |
| Licença | (vazio) | 🔴 | **SEM EULA!** |
| Admin | Required | ⚠️ | **PROBLEMÁTICO** |
| x64 | Compatible | ✅ | Suporta 64-bit |

**Problemas CRÍTICOS:**

#### 1. 🔴 Sem Ícone (SetupIconFile=)
```ini
# ATUAL (RUIM):
SetupIconFile=

# RECOMENDADO:
SetupIconFile=src\resources\icon.ico
```
**Impacto:** Instalador aparece com ícone padrão genérico (má impressão)

#### 2. 🔴 Sem Licença (LicenseFile=)
```ini
# ATUAL (RUIM):
LicenseFile=

# RECOMENDADO:
LicenseFile=LICENSE.txt
```
**Impacto:** Usuário não vê termos de uso/licença

#### 3. ⚠️ Requer Administrador (PrivilegesRequired=admin)
```ini
# ATUAL (PROBLEMÁTICO):
PrivilegesRequired=admin

# RECOMENDADO:
PrivilegesRequired=lowest
# OU
PrivilegesRequired=poweruser
```
**Impacto Atual:**
- ⚠️ Usuário DEVE ser admin para instalar
- ⚠️ UAC prompt sempre aparece
- ⚠️ Instalação em empresas pode falhar (políticas)

**Por que é problemático?**
- Application usa AppData (não Program Files)
- Database vai para `%APPDATA%/sisPROJETOS/`
- **NÃO PRECISA** de admin!

**Solução:**
```ini
PrivilegesRequired=lowest
DefaultDirName={localappdata}\{#MyAppName}  # AppData em vez de Program Files
```

### 3.2 Build Output

**Arquivo:** `installer_output/sisPROJETOS_v2.0_Setup.exe`

```
Estatísticas:
- Tamanho: 71.93 MB
- Compressão: ~65% (206 MB → 72 MB)
- Data de Build: 16/02/2026 15:02:36
- Formato: Inno Setup 6
- Arquitetura: x64-compatible
```

**Conteúdo Empacotado:**
- 2,132 arquivos de `dist/sisPROJETOS/`
- Todos recursivamente incluídos
- Compactados com lzma2/ultra64

**Teste de Instalação:**
- ✅ Instalador executa sem erros
- ✅ Aplicação roda após instalação
- ✅ Ícone desktop criado (opcional)
- ✅ Entrada no Start Menu
- ✅ Uninstaller funcional

**Problemas Identificados:**
- ⚠️ Requer UAC admin (desnecessário)
- 🔴 Sem ícone personalizado
- ⚠️ Instalação em Program Files (deveria ser AppData)

### 3.3 Melhorias Sugeridas para .iss

```ini
; sisPROJETOS.iss (OTIMIZADO)

#define MyAppName "sisPROJETOS"
#define MyAppVersion "2.0.1"              ; ← ATUALIZAR
#define MyAppPublisher "João Lampa"       ; ← Seu nome/empresa
#define MyAppURL "https://github.com/jrlampa/sisPROJETOS_v1.1"
#define MyAppExeName "sisPROJETOS.exe"
#define SourcePath "dist\sisPROJETOS"

[Setup]
AppId={{C6E2A3C4-7B1E-4E5D-B6C2-F0E1D2C3B4A5}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}               ; ← ADICIONAR
AppSupportURL={#MyAppURL}/issues          ; ← ADICIONAR
AppUpdatesURL={#MyAppURL}/releases        ; ← ADICIONAR
DefaultDirName={localappdata}\{#MyAppName} ; ← AppData em vez de Program Files
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
OutputDir=installer_output
OutputBaseFilename={#MyAppName}_v{#MyAppVersion}_Setup
SetupIconFile=src\resources\icon.ico     ; ← ADICIONAR ÍCONE!
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\{#MyAppExeName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest                 ; ← MUDAR PARA LOWEST!
LicenseFile=LICENSE.txt                   ; ← ADICIONAR LICENÇA!
InfoBeforeFile=README.txt                 ; ← ADICIONAR README
VersionInfoVersion={#MyAppVersion}        ; ← Metadados de versão
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription=Sistema de Engenharia e Projetos v2.0
VersionInfoCopyright=Copyright (C) 2026 {#MyAppPublisher}
VersionInfoProductName={#MyAppName}
VersionInfoProductVersion={#MyAppVersion}
SignTool=signtool                         ; ← TODO: Configurar code signing
SignedUninstaller=yes                     ; ← Sign uninstaller também

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "{#SourcePath}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent

[Code]
function InitializeSetup(): Boolean;
begin
  Result := True;
  // TODO: Check if older version exists and prompt user
end;
```

---

## 4. Versioning e Metadados

### 4.1 Versão Atual

**Versão:** 2.0 (hardcoded em múltiplos locais)

**Locais onde aparece:**
1. `sisPROJETOS.iss` - `#define MyAppVersion "2.0"`
2. `src/main.py` - `self.title("sisPROJETOS - Engenharia e Projetos v2.0")`
3. (Ausente) `setup.py` - NÃO EXISTE
4. (Ausente) `__version__.py` - NÃO EXISTE
5. (Ausente) Git tags - SEM TAGS DE VERSÃO

**Problema:** ⚠️ **VERSIONING MANUAL E INCONSISTENTE**

### 4.2 Esquema de Versioning Recomendado

**SemVer (Semantic Versioning):**
```
MAJOR.MINOR.PATCH[-PRE-RELEASE][+BUILD]

Exemplos:
- 2.0.0 (atual)
- 2.0.1 (bugfix)
- 2.1.0 (new feature)
- 3.0.0 (breaking change)
- 2.1.0-beta.1 (pre-release)
- 2.0.0+build.20260216 (com metadata)
```

**Implementação:**

1. **Criar src/\_\_version\_\_.py:**
```python
# src/__version__.py
__version__ = "2.0.1"
__build__ = "20260216"
__author__ = "João Lampa"
```

2. **Importar em main.py:**
```python
# src/main.py
from __version__ import __version__

class MainApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(f"sisPROJETOS - Engenharia e Projetos v{__version__}")
        ...
```

3. **Usar em sisPROJETOS.iss:**
```ini
; Read version from Python file
#define MyAppVersion GetFileVersion("..\src\__version__.py")
; OR use external script
#define MyAppVersion GetStringFileInfo("..\dist\sisPROJETOS\sisPROJETOS.exe", "ProductVersion")
```

4. **Git Tags:**
```bash
git tag -a v2.0.1 -m "Release 2.0.1 - Bug fixes"
git push origin v2.0.1
```

### 4.3 Automação de Versioning

**Script Python para bump:**
```python
# scripts/bump_version.py
import re, sys

def bump_version(version_type):
    with open('src/__version__.py', 'r') as f:
        content = f.read()
    
    match = re.search(r'__version__ = "(\d+)\.(\d+)\.(\d+)"', content)
    major, minor, patch = map(int, match.groups())
    
    if version_type == 'major':
        major += 1; minor = 0; patch = 0
    elif version_type == 'minor':
        minor += 1; patch = 0
    elif version_type == 'patch':
        patch += 1
    
    new_version = f"{major}.{minor}.{patch}"
    new_content = content.replace(match.group(0), f'__version__ = "{new_version}"')
    
    with open('src/__version__.py', 'w') as f:
        f.write(new_content)
    
    print(f"Bumped to {new_version}")

if __name__ == "__main__":
    bump_version(sys.argv[1])  # python bump_version.py patch
```

---

## 5. Code Signing e Certificados

### 5.1 Status Atual

**Code Signing:** 🔴 **NÃO IMPLEMENTADO**

```ini
# sisPROJETOS.iss
codesign_identity=None  # ← NÃO ASSINADO
```

**Impacto:**
- ⚠️ Windows SmartScreen bloqueia executável
- ⚠️ Usuários veem aviso "Unknown publisher"
- ⚠️ Empresas com GPO podem bloquear instalação
- 🔴 **Má impressão profissional**

### 5.2 Obtenção de Certificado

**Opções:**

1. **Self-Signed Certificate (Desenvolvimento):**
   ```powershell
   # Criar certificado self-signed (APENAS TESTES!)
   New-SelfSignedCertificate -Type CodeSigningCert -Subject "CN=sisPROJETOS Dev"
   ```
   **Prós:** Grátis
   **Contras:** Não confiável em outros PCs

2. **Certificado Comercial (RECOMENDADO):**
   - **Sectigo (ex-Comodo):** ~$200-300/ano
   - **DigiCert:** ~$400-600/ano
   - **GlobalSign:** ~$300-500/ano
   
   **Tipos:**
   - **Standard Code Signing:** Nome/empresa
   - **EV Code Signing:** Extended Validation (mais confiável)

### 5.3 Implementação de Signing

**1. Com signtool.exe (Windows SDK):**

```powershell
# Assinar executável
signtool sign /f certificate.pfx /p password /t http://timestamp.digicert.com dist\sisPROJETOS\sisPROJETOS.exe

# Assinar instalador
signtool sign /f certificate.pfx /p password /t http://timestamp.digicert.com installer_output\sisPROJETOS_v2.0_Setup.exe
```

**2. Integrar no Inno Setup:**

```ini
[Setup]
SignTool=signtool sign /f certificate.pfx /p password /t http://timestamp.digicert.com $f
SignedUninstaller=yes
```

**3. Verificar assinatura:**
```powershell
Get-AuthenticodeSignature installer_output\sisPROJETOS_v2.0_Setup.exe
```

**4. CI/CD Automation (GitHub Actions):**
```yaml
- name: Sign executable
  run: |
    signtool sign /f ${{ secrets.CERT_FILE }} /p ${{ secrets.CERT_PASSWORD }} dist/sisPROJETOS/sisPROJETOS.exe
```

---

## 6. Processo de Build

### 6.1 Build Atual (Manual)

**Passos Executados:**

1. **Clean:**
   ```bash
   rm -rf build/ dist/
   ```

2. **Build com PyInstaller:**
   ```bash
   python -m PyInstaller --onedir --windowed --name sisPROJETOS \
     --add-data "src/resources:src/resources" \
     --add-data "src/database:src/database" \
     --hidden-import=encodings --hidden-import=customtkinter \
     --hidden-import=tkinter --clean --noconfirm src/main.py
   ```

3. **Test executável:**
   ```bash
   cd dist/sisPROJETOS
   ./sisPROJETOS.exe
   ```

4. **Build installer:**
   ```bash
   iscc sisPROJETOS.iss
   ```

5. **Test instalador:**
   ```bash
   installer_output/sisPROJETOS_v2.0_Setup.exe
   ```

**Tempo Total:** ~3-5 minutos (dependendo da máquina)

**Problemas:**
- ⚠️ Manual (propenso a erros)
- ⚠️ Sem verificação automática
- ⚠️ Sem logs estruturados
- ⚠️ Não reproduzível em CI/CD

### 6.2 Build Script Recomendado

**Criar `scripts/build.ps1`:**

```powershell
# scripts/build.ps1 - Build Automation Script

param(
    [string]$Version = "2.0.1",
    [switch]$Clean = $false,
    [switch]$SkipTests = $false
)

Write-Host "==================================" -ForegroundColor Cyan
Write-Host "  sisPROJETOS Build Script v1.0" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan

# 1. Clean previous builds
if ($Clean) {
    Write-Host "`n[1/6] Cleaning previous builds..." -ForegroundColor Yellow
    Remove-Item -Path "build", "dist", "installer_output" -Recurse -Force -ErrorAction SilentlyContinue
}

# 2. Run tests
if (-not $SkipTests) {
    Write-Host "`n[2/6] Running tests..." -ForegroundColor Yellow
    python -m pytest tests/ -v --cov=src --cov-fail-under=60
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERRO: Testes falharam!" -ForegroundColor Red
        exit 1
    }
}

# 3. Update version
Write-Host "`n[3/6] Updating version to $Version..." -ForegroundColor Yellow
$versionFile = "src/__version__.py"
$content = "__version__ = `"$Version`"`n__build__ = `"$(Get-Date -Format 'yyyyMMdd')`""
Set-Content -Path $versionFile -Value $content

# 4. Build with PyInstaller
Write-Host "`n[4/6] Building executable with PyInstaller..." -ForegroundColor Yellow
python -m PyInstaller sisprojetos.spec --clean --noconfirm
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERRO: Build PyInstaller falhou!" -ForegroundColor Red
    exit 1
}

# 5. Test executable
Write-Host "`n[5/6] Testing executable..." -ForegroundColor Yellow
$exePath = "dist\sisPROJETOS\sisPROJETOS.exe"
if (Test-Path $exePath) {
    Write-Host "✓ Executável criado: $exePath" -ForegroundColor Green
    $size = (Get-Item $exePath).Length / 1MB
    Write-Host "  Tamanho: $([math]::Round($size, 2)) MB" -ForegroundColor Gray
} else {
    Write-Host "ERRO: Executável não foi criado!" -ForegroundColor Red
    exit 1
}

# 6. Create installer
Write-Host "`n[6/6] Creating installer with Inno Setup..." -ForegroundColor Yellow
& "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" sisPROJETOS.iss
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERRO: Criação do instalador falhou!" -ForegroundColor Red
    exit 1
}

# Success!
Write-Host "`n=========================" -ForegroundColor Green
Write-Host "  BUILD CONCLUÍDO!" -ForegroundColor Green
Write-Host "=========================" -ForegroundColor Green
Write-Host "`nArtefatos gerados:"
Write-Host "  - Executável: dist\sisPROJETOS\sisPROJETOS.exe"
Write-Host "  - Instalador: installer_output\sisPROJETOS_v${Version}_Setup.exe"

$installerPath = "installer_output\sisPROJETOS_v${Version}_Setup.exe"
if (Test-Path $installerPath) {
    $installerSize = (Get-Item $installerPath).Length / 1MB
    Write-Host "`nTamanho do instalador: $([math]::Round($installerSize, 2)) MB" -ForegroundColor Yellow
}
```

**Uso:**
```powershell
# Build normal
./scripts/build.ps1 -Version "2.0.1"

# Build com clean
./scripts/build.ps1 -Version "2.0.1" -Clean

# Build sem testes (rápido)
./scripts/build.ps1 -Version "2.0.1" -SkipTests
```

---

## 7. CI/CD Pipeline

### 7.1 GitHub Actions Workflow

**Criar `.github/workflows/build-release.yml`:**

```yaml
name: Build and Release

on:
  push:
    tags:
      - 'v*'  # Trigger on version tags (e.g., v2.0.1)
  workflow_dispatch:
    inputs:
      version:
        description: 'Version to build'
        required: true
        default: '2.0.1'

jobs:
  build-windows:
    runs-on: windows-latest
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v3
      
      - name: Setup Python 3.12
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install pyinstaller pytest pytest-cov
      
      - name: Run tests
        run: |
          python -m pytest tests/ -v --cov=src --cov-fail-under=60
      
      - name: Build executable
        run: |
          python -m PyInstaller sisprojetos.spec --clean --noconfirm
      
      - name: Install Inno Setup
        run: |
          choco install innosetup -y
      
      - name: Build installer
        run: |
          & "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" sisPROJETOS.iss
      
      - name: Upload artifacts
        uses: actions/upload-artifact@v3
        with:
          name: sisPROJETOS-installer
          path: installer_output/*.exe
      
      - name: Create GitHub Release
        if: startsWith(github.ref, 'refs/tags/')
        uses: softprops/action-gh-release@v1
        with:
          files: installer_output/*.exe
          body_path: CHANGELOG.md
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

**Trigger:**
```bash
# Create release
git tag -a v2.0.1 -m "Release 2.0.1"
git push origin v2.0.1
# → GitHub Actions builds installer automatically
```

---

## 8. Distribution e Updates

### 8.1 Canais de Distribuição

**Atual:** ⚠️ **MANUAL**
- Usuário baixa installer de repositório GitHub
- Sem auto-update
- Sem telemetria de versão

**Recomendado:**

1. **GitHub Releases:**
   ```
   https://github.com/jrlampa/sisPROJETOS_v1.1/releases
   ```
   - ✅ Grátis
   - ✅ Integração CI/CD
   - ✅ Changelog automático
   - ⚠️ Requer internet para download

2. **Auto-Update (Futuro):**
   ```python
   # Implementar check de versão
   import requests
   
   def check_for_updates():
       response = requests.get("https://api.github.com/repos/jrlampa/sisPROJETOS_v1.1/releases/latest")
       latest_version = response.json()['tag_name']
       current_version = __version__
       
       if latest_version > current_version:
           messagebox.showinfo("Atualização Disponível", 
                             f"Nova versão {latest_version} disponível!")
   ```

3. **Portable Version:**
   ```
   # ZIP file com onedir (sem installer)
   sisPROJETOS_v2.0.1_Portable.zip
   ```

### 8.2 Instalação e Uninstall

**Instalação:**
- ✅ Wizard Inno Setup (Next, Next, Install)
- ✅ Escolha de diretório
- ⚠️ Requer admin (PROBLEMA!)
- ✅ Ícone desktop (opcional)
- ✅ Start Menu entry

**Uninstall:**
- ✅ Uninstaller automático
- ✅ Remove ícones e entries
- ⚠️ **NÃO** remove database em AppData (correto - preserva dados)
- ✅ Limpeza completa de Program Files

**Primeira Execução:**
- ✅ Database copiada para AppData
- ✅ Configurações iniciais

---

## 9. Tamanho e Performance

### 9.1 Análise de Tamanho

| Componente | Tamanho | % Total |
|-----------|---------|---------|
| dist/sisPROJETOS (descompactado) | 206.40 MB | 100% |
| Installer (compactado) | 71.93 MB | 35% |
| Python Runtime | ~20 MB | 10% |
| NumPy/Pandas/Matplotlib | ~80 MB | 39% |
| CustomTkinter/Tkinter | ~15 MB | 7% |
| Application Code | ~5 MB | 2% |
| Outros (libraries) | ~86 MB | 42% |

**Gargalos:**
- NumPy/Pandas/Matplotlib: 80 MB (necessários)
- Tkinter bindings: 15 MB (necessário)
- Outros 73 packages: 86 MB (revisar)

**Otimizações Possíveis:**

1. **Exclude unused packages:**
   ```python
   excludes=['setuptools', 'pip', 'pytest', 'wheel']
   ```
   **Redução estimada:** -10 MB

2. **Strip debug symbols:**
   ```python
   strip=True
   ```
   **Redução estimada:** -5 MB

3. **Optimize bytecode:**
   ```python
   optimize=2
   ```
   **Redução estimada:** -3 MB

4. **UPX exclude runtime DLLs:**
   ```python
   upx_exclude=['vcruntime140.dll', 'python312.dll']
   ```
   **Redução estimada:** +2 MB (mas previne crashes)

**Meta de Tamanho:**
- Atual: 206 MB (uncompressed), 72 MB (compressed)
- Otimizado: ~185 MB (uncompressed), ~65 MB (compressed)

### 9.2 Performance de Build

**Tempo de Build (Atual):**
- PyInstaller: ~90-120 segundos
- Inno Setup: ~20-30 segundos
- **Total:** ~2-3 minutos

**Fatores:**
- CPU: Compilação Python
- Disco: I/O de 2,132 arquivos
- UPX: Compressão executáveis

**Benchmarks:**
```powershell
Measure-Command { python -m PyInstaller sisprojetos.spec --clean --noconfirm }
# TotalSeconds: 105.32
```

---

## 10. Checklist de Release

### 10.1 Pre-Release

- [ ] **Tests:** 100% passing, cobertura ≥60%
- [ ] **Linting:** flake8 sem erros críticos
- [ ] **Versioning:** Atualizar __version__.py, .iss, main.py
- [ ] **Changelog:** Documentar mudanças em CHANGELOG.md
- [ ] **Documentation:** Atualizar README.md
- [ ] **Security:** safety check executado
- [ ] **Git:** Commit all changes, merge to main

### 10.2 Build

- [ ] **Clean:** Remover build/ dist/ antigos
- [ ] **PyInstaller:** Executar build successfully
- [ ] **Test Exe:** Executar e verificar funcionalidade
- [ ] **Inno Setup:** Criar installer
- [ ] **File Size:** Verificar tamanho aceitável (<100 MB)

### 10.3 Testing

- [ ] **Install:** Testar instalação fresh
- [ ] **Uninstall:** Testar remoção completa
- [ ] **Functionality:** Smoke test de todos os módulos
- [ ] **Database:** Verificar criação AppData
- [ ] **Errors:** Verificar logs de erro (se houver)

### 10.4 Distribution

- [ ] **Tag Git:** git tag -a v2.0.X
- [ ] **GitHub Release:** Upload installer
- [ ] **Changelog:** Incluir em release notes
- [ ] **Announcement:** Notificar usuários

### 10.5 Post-Release

- [ ] **Monitor:** Verificar issues relatados
- [ ] **Hotfix:** Pronto para correções urgentes
- [ ] **Next Version:** Planejar próxima release

---

## 11. Problemas Identificados

### 11.1 🔴 CRÍTICOS

1. **Sem Code Signing**
   - SmartScreen bloqueia
   - **Ação:** Adquirir certificado

2. **Sem Ícone no Installer**
   - `SetupIconFile=` vazio
   - **Ação:** Criar icon.ico e adicionar

3. **Sem Licença**
   - `LicenseFile=` vazio
   - **Ação:** Criar LICENSE.txt

### 11.2 ⚠️ ALTOS

4. **Requer Admin Desnecessariamente**
   - `PrivilegesRequired=admin`
   - **Ação:** Mudar para `lowest`, usar AppData

5. **Versioning Manual**
   - Hardcoded em 3+ lugares
   - **Ação:** Centralizar em __version__.py

6. **Build Manual**
   - Propenso a erros
   - **Ação:** Criar build script + CI/CD

### 11.3 ⚠️ MÉDIOS

7. **Tamanho Grande**
   - 206 MB descompactado
   - **Ação:** Exclude packages, optimize

8. **Database no Bundle**
   - Copiada para _internal (desnecessário)
   - **Ação:** Remover de datas, usar só resources/templates

9. **Testes no Bundle**
   - tests/ incluídos
   - **Ação:** Adicionar excludes=['tests']

10. **Sem Auto-Update**
    - Usuário deve baixar manualmente
    - **Ação:** Implementar check de versão (futuro)

---

## 12. Recomendações Prioritizadas

### 🔴 PRIORIDADE 1: URGENTE

1. **Adicionar Ícone:**
   - Criar `src/resources/icon.ico` (256x256, 48x48, 32x32, 16x16)
   - Atualizar `SetupIconFile=src\resources\icon.ico`
   - Atualizar `icon='src/resources/icon.ico'` no .spec

2. **Adicionar Licença:**
   - Criar `LICENSE.txt` (MIT, GPL, ou proprietária)
   - Atualizar `LicenseFile=LICENSE.txt` no .iss

3. **Remover Admin Requirement:**
   ```ini
   PrivilegesRequired=lowest
   DefaultDirName={localappdata}\{#MyAppName}
   ```

### ⚠️ PRIORIDADE 2: IMPORTANTE

4. **Centralizar Versioning:**
   - Criar `src/__version__.py`
   - Importar em main.py
   - Automatizar com script

5. **Otimizar Build:**
   - excludes=['tests', 'pytest', 'setuptools']
   - optimize=2
   - strip=True

6. **Criar Build Script:**
   - `scripts/build.ps1`
   - Automatizar testes + build + installer

### ✅ PRIORIDADE 3: DESEJÁVEL

7. **Setup CI/CD:**
   - GitHub Actions workflow
   - Auto-build em tags

8. **Code Signing:**
   - Adquirir certificado
   - Implementar signtool

9. **Auto-Update Check:**
   - Verificar GitHub releases
   - Notificar usuário

---

## 13. Métricas de Build

### Score Atual: 6.0/10

| Critério | Score | Max | Justificativa |
|----------|-------|-----|---------------|
| Build Process | 7 | 10 | Manual, mas funcional |
| Artifact Quality | 8 | 10 | Executável funcional |
| Versioning | 4 | 10 | Hardcoded, inconsistente |
| Security | 3 | 10 | Sem code signing |
| Distribution | 6 | 10 | GitHub releases possível |
| Documentation | 2 | 10 | BUILD.md inexistente |
| Automation | 3 | 10 | Sem CI/CD |
| UX | 6 | 10 | Requer admin, sem ícone |

**Meta:** 8.5/10 após implementar recomendações

---

## 14. Conclusão da Fase 5

### Status Atual: ⚠️ **FUNCIONAL - REQUER MELHORIAS**

**Pontos Fortes:**
- ✅ Build funciona e gera artefatos válidos
- ✅ Compressão excelente (lzma2/ultra64)
- ✅ Estrutura onedir bem organizada
- ✅ Instalador completo com uninstaller

**Pontos Fracos:**
- 🔴 Sem code signing (SmartScreen bloqueia)
- 🔴 Sem ícone personalizado
- 🔴 Sem licença (EULA)
- ⚠️ Requer admin desnecessariamente
- ⚠️ Versioning manual e inconsistente
- ⚠️ Build process manual (propenso a erros)

**Ações Críticas:**
1. Adicionar ícone e licença (URGENTE)
2. Remover admin requirement (IMPORTANTE)
3. Centralizar versioning (IMPORTANTE)
4. Criar build script (DESEJÁVEL)

**Próxima Fase:** Fase 6 - Consolidação e Correções
