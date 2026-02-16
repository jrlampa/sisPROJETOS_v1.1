# 🔨 Guia de Build - sisPROJETOS v2.0

Este documento descreve como compilar e distribuir o sisPROJETOS a partir do código-fonte.

---

## Pré-requisitos

### Software Necessário

1. **Python 3.12+**
   ```bash
   python --version  # Deve ser 3.12 ou superior
   ```

2. **PyInstaller 6.19+**
   ```bash
   pip install pyinstaller
   ```

3. **Inno Setup 6.7+ (apenas Windows)**
   - Download: https://jrsoftware.org/isdl.php
   - Instalar em: `C:\Program Files (x86)\Inno Setup 6\`

4. **Git** (opcional, para controle de versão)

### Dependências Python

```bash
cd sisPROJETOS_revived
pip install -r requirements.txt
```

---

## Build Manual (Passo a Passo)

### 1. Limpar Builds Anteriores

```powershell
Remove-Item -Path "dist", "build", "installer_output" -Recurse -Force -ErrorAction SilentlyContinue
```

### 2. Executar Testes

```powershell
python -m pytest tests/ -v --cov=src --cov-fail-under=75
```

**Importante:** Build NÃO deve prosseguir se tests falharem!

### 3. Atualizar Versão

Editar `src/__version__.py`:
```python
__version__ = "2.0.2"  # ← Atualizar aqui
__build__ = "20260217"  # ← Data atual (YYYYMMDD)
```

**Versioning Semântico:**
- `MAJOR.MINOR.PATCH`
- `2.0.0` → Versão base
- `2.0.1` → Bugfix
- `2.1.0` → Nova feature
- `3.0.0` → Breaking change

### 4. Compilar com PyInstaller

```powershell
python -m PyInstaller sisprojetos.spec --clean --noconfirm
```

**Tempo estimado:** 2-3 minutos  
**Output:** `dist/sisPROJETOS/` (206 MB, 2132 arquivos)

**Verificar:**
```powershell
Test-Path "dist\sisPROJETOS\sisPROJETOS.exe"  # Deve retornar True
```

### 5. Testar Executável

```powershell
cd dist/sisPROJETOS
.\sisPROJETOS.exe
```

**Checklist de teste:**
- [ ] Aplicação inicia sem erros
- [ ] Janela principal aparece
- [ ] Todos os módulos carregam
- [ ] Database é criado em AppData
- [ ] Cálculos funcionam corretamente

### 6. Criar Instalador (Inno Setup)

```powershell
cd "g:\Meu Drive\backup-02-2026\App\sisPROJETOS_v1.1\sisPROJETOS_revived"
& "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" sisPROJETOS.iss
```

**Tempo estimado:** 30 segundos  
**Output:** `installer_output/sisPROJETOS_v2.0.1_Setup.exe` (~72 MB)

### 7. Testar Instalador

1. Executar `sisPROJETOS_v2.0.1_Setup.exe`
2. Seguir wizard de instalação
3. Verificar instalação em `%LOCALAPPDATA%\sisPROJETOS\`
4. Executar aplicação instalada
5. Testar todas as funcionalidades
6. Desinstalar via "Add/Remove Programs"
7. Verificar se AppData foi preservado

---

## Configuração do Build

### sisprojetos.spec (PyInstaller)

```python
# Configurações otimizadas

a = Analysis(
    ['src\\main.py'],
    datas=[('src/resources', 'src/resources')],  # Resources incluídos
    hiddenimports=['encodings', 'customtkinter', 'tkinter', 'PIL'],
    excludes=['tests', 'pytest', 'setuptools', 'pip'],  # ✨ Reduz tamanho
    optimize=2,  # ✨ Bytecode otimizado
)

exe = EXE(
    ...
    strip=True,  # ✨ Remove debug symbols
    target_arch='x86_64',  # ✨ 64-bit explícito
    upx=True,  # ✨ Compressão UPX
)

coll = COLLECT(
    ...
    upx_exclude=['vcruntime140.dll', 'python312.dll'],  # ✨ Não comprimir DLLs críticas
)
```

### sisPROJETOS.iss (Inno Setup)

```ini
[Setup]
AppVersion=2.0.1  ; ✨ Versão centralizada
PrivilegesRequired=lowest  ; ✨ Não requer admin
DefaultDirName={localappdata}\{#MyAppName}  ; ✨ AppData
LicenseFile=LICENSE.txt  ; ✨ EULA incluído
Compression=lzma2/ultra64  ; ✨ Máxima compressão
```

---

## Build Automatizado (Script PowerShell)

Criar `scripts/build.ps1`:

```powershell
# Build completo automatizado

param(
    [string]$Version = "2.0.1",
    [switch]$Clean = $false,
    [switch]$SkipTests = $false
)

Write-Host "=== sisPROJETOS Build Script v1.0 ===" -ForegroundColor Cyan

# 1. Clean
if ($Clean) {
    Write-Host "[1/6] Cleaning..." -ForegroundColor Yellow
    Remove-Item -Path "dist", "build", "installer_output" -Recurse -Force -ErrorAction SilentlyContinue
}

# 2. Tests
if (-not $SkipTests) {
    Write-Host "[2/6] Running tests..." -ForegroundColor Yellow
    python -m pytest tests/ -v --cov=src --cov-fail-under=75
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERRO: Testes falharam!" -ForegroundColor Red
        exit 1
    }
}

# 3. Update version
Write-Host "[3/6] Updating version to $Version..." -ForegroundColor Yellow
$content = "__version__ = `"$Version`"`n__build__ = `"$(Get-Date -Format 'yyyyMMdd')`""
Set-Content -Path "src\__version__.py" -Value $content

# 4. PyInstaller
Write-Host "[4/6] Building with PyInstaller..." -ForegroundColor Yellow
python -m PyInstaller sisprojetos.spec --clean --noconfirm
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERRO: PyInstaller falhou!" -ForegroundColor Red
    exit 1
}

# 5. Test exe
Write-Host "[5/6] Testing executable..." -ForegroundColor Yellow
if (Test-Path "dist\sisPROJETOS\sisPROJETOS.exe") {
    Write-Host "✓ Executável criado" -ForegroundColor Green
} else {
    Write-Host "ERRO: Executável não criado!" -ForegroundColor Red
    exit 1
}

# 6. Installer
Write-Host "[6/6] Creating installer..." -ForegroundColor Yellow
& "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" sisPROJETOS.iss
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERRO: Instalador falhou!" -ForegroundColor Red
    exit 1
}

Write-Host "`n=== BUILD CONCLUÍDO! ===" -ForegroundColor Green
Write-Host "Artefatos:"
Write-Host "  - dist\sisPROJETOS\sisPROJETOS.exe"
Write-Host "  - installer_output\sisPROJETOS_v${Version}_Setup.exe"
```

**Uso:**
```powershell
.\scripts\build.ps1 -Version "2.0.2" -Clean
```

---

## Troubleshooting

### Problema: "Module not found" durante build

**Solução:**
```bash
pip install -r requirements.txt --force-reinstall
```

### Problema: UPX compression error

**Solução:** Adicionar DLL problemática a `upx_exclude`:
```python
upx_exclude=['vcruntime140.dll', 'python312.dll', 'problema.dll']
```

### Problema: Instalador requer admin

**Solução:** Verificar `sisPROJETOS.iss`:
```ini
PrivilegesRequired=lowest  ; NÃO admin!
DefaultDirName={localappdata}\{#MyAppName}
```

### Problema: Database não encontrado após instalação

**Solução:** Database deve ir para AppData, NÃO para bundle:
```python
# sisprojetos.spec
datas=[('src/resources', 'src/resources')]  # ← SEM src/database
```

### Problema: Build muito grande (>250 MB)

**Soluções:**
1. Verificar `excludes` no .spec
2. Remover packages não utilizados
3. Ativar `strip=True`
4. Verificar se tests não estão sendo incluídos

---

## Checklist de Release

### Pre-Build
- [ ] Tests passando (pytest)
- [ ] Coverage ≥75%
- [ ] flake8 sem erros críticos
- [ ] Versão atualizada em `__version__.py`
- [ ] CHANGELOG.md atualizado
- [ ] README.md atualizado

### Build
- [ ] Clean de builds anteriores
- [ ] PyInstaller executado sem erros
- [ ] Executável testado manualmente
- [ ] Instalador gerado
- [ ] Instalador testado (install + uninstall)

### Post-Build
- [ ] Tag Git criado (`git tag -a v2.0.1`)
- [ ] GitHub Release criado
- [ ] Instalador uploaded
- [ ] Release notes publicadas
- [ ] Usuários notificados

---

## Otimizações de Tamanho

### Atual
- **Executável (dist/)**: 206 MB
- **Instalador (.exe)**: 72 MB
- **Compressão**: ~65%

### Possíveis Melhorias
- Exclude unused packages: -10 MB
- Strip debug symbols: -5 MB
- Optimize bytecode: -3 MB
- **Meta:** 185 MB (dist), 65 MB (installer)

### Pacotes Grandes
| Package | Tamanho | Necessário? |
|---------|---------|-------------|
| NumPy | ~80 MB | ✅ Sim (cálculos) |
| Matplotlib | ~40 MB | ✅ Sim (gráficos) |
| Tkinter | ~15 MB | ✅ Sim (GUI) |
| Tests | ~10 MB | ❌ Não (exclude) |

---

## CI/CD (Futuro)

### GitHub Actions Workflow

```yaml
name: Build Release

on:
  push:
    tags:
      - 'v*'

jobs:
  build-windows:
    runs-on: windows-latest
    
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      
      - name: Install deps
        run: pip install -r requirements.txt
      
      - name: Run tests
        run: pytest tests/ --cov=src --cov-fail-under=75
      
      - name: Build exe
        run: python -m PyInstaller sisprojetos.spec --clean
      
      - name: Build installer
        run: iscc sisPROJETOS.iss
      
      - name: Upload Release
        uses: softprops/action-gh-release@v1
        with:
          files: installer_output/*.exe
```

---

## Segurança

### Code Signing (TODO)

Para evitar bloqueio do SmartScreen:

1. **Adquirir certificado:**
   - Sectigo: ~$200-300/ano
   - DigiCert: ~$400-600/ano

2. **Assinar executável:**
   ```powershell
   signtool sign /f certificate.pfx /p password /t http://timestamp.digicert.com dist\sisPROJETOS\sisPROJETOS.exe
   ```

3. **Assinar instalador:**
   ```powershell
   signtool sign /f certificate.pfx /p password /t http://timestamp.digicert.com installer_output\sisPROJETOS_v2.0.1_Setup.exe
   ```

4. **Configurar .iss:**
   ```ini
   SignTool=signtool sign /f certificate.pfx /p password /t http://timestamp.digicert.com $f
   SignedUninstaller=yes
   ```

---

## Métricas de Build

| Métrica | Tempo | Tamanho |
|---------|-------|---------|
| Clean | 5s | - |
| Tests | 10s | - |
| PyInstaller | 120s | 206 MB |
| Inno Setup | 30s | 72 MB |
| **Total** | **~3min** | **72 MB** |

---

## Versionamento

### Semantic Versioning (SemVer)

```
MAJOR.MINOR.PATCH[-PRE-RELEASE][+BUILD]

Exemplos:
2.0.0       - Release base
2.0.1       - Bugfix
2.1.0       - Nova feature
3.0.0       - Breaking change
2.1.0-beta  - Pre-release
2.0.0+20260216 - Com build metadata
```

### Arquivo Centralizado

**Único local:** `src/__version__.py`

```python
__version__ = "2.0.1"
__build__ = "20260216"
```

**Importar em:**
- `src/main.py` - Título da janela
- `sisPROJETOS.iss` - Versão do instalador
- Outros arquivos que necessitem

---

## Contato e Suporte

- **Issues:** https://github.com/jrlampa/sisPROJETOS_v1.1/issues
- **Documentação:** README.md, ARCHITECTURE.md
- **Licença:** MIT (LICENSE.txt)
