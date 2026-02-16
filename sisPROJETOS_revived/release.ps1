# ========================================================================
# sisPROJETOS - Release Script
# ========================================================================
# Script automatizado para criar releases do sisPROJETOS
# 
# Uso:
#   .\release.ps1 -Version "2.0.1" -Message "Release notes here"
#   .\release.ps1 -Version "2.0.1"  # Usa CHANGELOG.md automaticamente
#
# ========================================================================

param(
    [Parameter(Mandatory=$true)]
    [string]$Version,
    
    [Parameter(Mandatory=$false)]
    [string]$Message = "",
    
    [Parameter(Mandatory=$false)]
    [switch]$SkipTests = $false,
    
    [Parameter(Mandatory=$false)]
    [switch]$DryRun = $false
)

# Cores para output
function Write-Success { Write-Host $args -ForegroundColor Green }
function Write-Info { Write-Host $args -ForegroundColor Cyan }
function Write-Warning { Write-Host $args -ForegroundColor Yellow }
function Write-Error { Write-Host $args -ForegroundColor Red }

Write-Host "========================================" -ForegroundColor Magenta
Write-Host "  sisPROJETOS Release Script v1.0" -ForegroundColor Magenta
Write-Host "========================================" -ForegroundColor Magenta
Write-Host ""

# Validar formato da versão (X.Y.Z)
if ($Version -notmatch '^\d+\.\d+\.\d+$') {
    Write-Error "❌ Formato de versão inválido: $Version"
    Write-Error "   Use formato: X.Y.Z (ex: 2.0.1)"
    exit 1
}

Write-Info "📦 Versão: v$Version"
Write-Info "📁 Diretório: $PWD"
Write-Host ""

# ========================================================================
# ETAPA 1: Verificações Pré-Release
# ========================================================================

Write-Host "🔍 ETAPA 1: Verificações Pré-Release" -ForegroundColor Yellow
Write-Host "──────────────────────────────────────" -ForegroundColor Gray

# 1.1 Verificar se estamos na branch main
$currentBranch = git rev-parse --abbrev-ref HEAD
if ($currentBranch -ne "main") {
    Write-Warning "⚠️  Você está na branch: $currentBranch"
    Write-Warning "    Recomendado criar releases da branch main"
    
    $continue = Read-Host "Continuar mesmo assim? (s/N)"
    if ($continue -ne "s" -and $continue -ne "S") {
        Write-Info "Operação cancelada."
        exit 0
    }
}
Write-Success "✅ Branch: $currentBranch"

# 1.2 Verificar se há mudanças não commitadas
$gitStatus = git status --porcelain
if ($gitStatus) {
    Write-Warning "⚠️  Há mudanças não commitadas:"
    git status --short
    Write-Host ""
    
    $continue = Read-Host "Fazer commit automático? (s/N)"
    if ($continue -eq "s" -or $continue -eq "S") {
        git add .
        git commit -m "chore: prepare release v$Version"
        Write-Success "✅ Commit criado"
    } else {
        Write-Error "❌ Faça commit das mudanças antes de criar release"
        exit 1
    }
} else {
    Write-Success "✅ Sem mudanças pendentes"
}

# 1.3 Verificar se tag já existe
$tagExists = git tag -l "v$Version"
if ($tagExists) {
    Write-Error "❌ Tag v$Version já existe!"
    Write-Error "   Use outra versão ou delete a tag: git tag -d v$Version"
    exit 1
}
Write-Success "✅ Tag v$Version disponível"

# 1.4 Verificar se __version__.py está atualizado
$versionFilePath = "src\__version__.py"
if (Test-Path $versionFilePath) {
    $versionContent = Get-Content $versionFilePath -Raw
    if ($versionContent -notmatch "__version__ = `"$Version`"") {
        Write-Warning "⚠️  src\__version__.py não está com a versão $Version"
        
        $update = Read-Host "Atualizar automaticamente? (s/N)"
        if ($update -eq "s" -or $update -eq "S") {
            $versionContent = $versionContent -replace '__version__ = ".*"', "__version__ = `"$Version`""
            Set-Content $versionFilePath -Value $versionContent
            
            git add $versionFilePath
            git commit -m "chore: bump version to $Version"
            Write-Success "✅ Versão atualizada em __version__.py"
        }
    } else {
        Write-Success "✅ __version__.py atualizado"
    }
}

Write-Host ""

# ========================================================================
# ETAPA 2: Executar Testes
# ========================================================================

if (-not $SkipTests) {
    Write-Host "🧪 ETAPA 2: Execução de Testes" -ForegroundColor Yellow
    Write-Host "──────────────────────────────────────" -ForegroundColor Gray
    
    Write-Info "Executando suite de testes..."
    
    $testResult = python -m pytest tests/ -v --tb=line 2>&1 | Out-String
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "✅ Todos os testes passaram"
    } else {
        # Contar testes passando/falhando
        $testSummary = $testResult | Select-String -Pattern "(\d+) passed"
        Write-Warning "⚠️  Alguns testes falharam"
        Write-Host $testSummary
        
        $continue = Read-Host "Continuar com release mesmo assim? (s/N)"
        if ($continue -ne "s" -and $continue -ne "S") {
            Write-Error "❌ Release cancelado devido a testes falhando"
            exit 1
        }
    }
    
    Write-Host ""
} else {
    Write-Warning "⏭️  Testes pulados (--SkipTests)"
    Write-Host ""
}

# ========================================================================
# ETAPA 3: Extrair Release Notes do CHANGELOG
# ========================================================================

Write-Host "📝 ETAPA 3: Release Notes" -ForegroundColor Yellow
Write-Host "──────────────────────────────────────" -ForegroundColor Gray

$releaseNotes = ""

if ([string]::IsNullOrWhiteSpace($Message)) {
    # Tentar extrair do CHANGELOG.md
    if (Test-Path "CHANGELOG.md") {
        $changelogContent = Get-Content "CHANGELOG.md" -Raw
        
        # Regex para extrair seção da versão
        $pattern = "(?s)## \[$Version\].*?(?=## \[|\z)"
        if ($changelogContent -match $pattern) {
            $releaseNotes = $matches[0]
            Write-Success "✅ Release notes extraídos do CHANGELOG.md"
            Write-Info ($releaseNotes.Substring(0, [Math]::Min(200, $releaseNotes.Length)) + "...")
        } else {
            Write-Warning "⚠️  Versão $Version não encontrada no CHANGELOG.md"
            $releaseNotes = "Release v$Version`n`nVeja CHANGELOG.md para detalhes."
        }
    } else {
        $releaseNotes = "Release v$Version"
    }
} else {
    $releaseNotes = $Message
}

Write-Host ""

# ========================================================================
# ETAPA 4: Criar Tag
# ========================================================================

Write-Host "🏷️  ETAPA 4: Criar Tag Git" -ForegroundColor Yellow
Write-Host "──────────────────────────────────────" -ForegroundColor Gray

if ($DryRun) {
    Write-Info "[DRY RUN] git tag -a v$Version -m '$releaseNotes'"
    Write-Warning "⚠️  Modo Dry Run - Tag NÃO foi criada"
} else {
    # Criar tag anotada
    git tag -a "v$Version" -m $releaseNotes
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "✅ Tag v$Version criada localmente"
    } else {
        Write-Error "❌ Erro ao criar tag"
        exit 1
    }
}

Write-Host ""

# ========================================================================
# ETAPA 5: Push para GitHub
# ========================================================================

Write-Host "🚀 ETAPA 5: Push para GitHub" -ForegroundColor Yellow
Write-Host "──────────────────────────────────────" -ForegroundColor Gray

if ($DryRun) {
    Write-Info "[DRY RUN] git push origin main"
    Write-Info "[DRY RUN] git push origin v$Version"
    Write-Warning "⚠️  Modo Dry Run - Nada foi enviado ao GitHub"
} else {
    # Push commits
    Write-Info "Enviando commits..."
    git push origin $currentBranch
    
    if ($LASTEXITCODE -ne 0) {
        Write-Error "❌ Erro ao fazer push de commits"
        Write-Error "   Tag criada localmente. Delete com: git tag -d v$Version"
        exit 1
    }
    Write-Success "✅ Commits enviados"
    
    # Push tag
    Write-Info "Enviando tag v$Version..."
    git push origin "v$Version"
    
    if ($LASTEXITCODE -ne 0) {
        Write-Error "❌ Erro ao fazer push da tag"
        Write-Error "   Delete tag local: git tag -d v$Version"
        exit 1
    }
    Write-Success "✅ Tag v$Version enviada"
}

Write-Host ""

# ========================================================================
# ETAPA 6: Informações Finais
# ========================================================================

Write-Host "========================================" -ForegroundColor Green
Write-Host "  ✅ RELEASE v$Version CRIADO!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

Write-Info "O que acontece agora:"
Write-Host "  1. GitHub Actions detetará a tag v$Version" -ForegroundColor Gray
Write-Host "  2. Workflow 'Build and Release' será disparado" -ForegroundColor Gray
Write-Host "  3. Testes serão executados" -ForegroundColor Gray
Write-Host "  4. Executável será compilado com PyInstaller" -ForegroundColor Gray
Write-Host "  5. Instalador será criado com Inno Setup" -ForegroundColor Gray
Write-Host "  6. GitHub Release será publicado automaticamente" -ForegroundColor Gray
Write-Host ""

Write-Info "Acompanhe o progresso em:"
Write-Host "  https://github.com/jrlampa/sisPROJETOS_v1.1/actions" -ForegroundColor Cyan
Write-Host ""

Write-Info "Release será publicado em (após ~10-15 minutos):"
Write-Host "  https://github.com/jrlampa/sisPROJETOS_v1.1/releases/tag/v$Version" -ForegroundColor Cyan
Write-Host ""

Write-Success "🎉 Obrigado por usar sisPROJETOS Release Script!"
Write-Host ""

# ========================================================================
# LOGS E DEBUGGING
# ========================================================================

if ($DryRun) {
    Write-Host ""
    Write-Warning "========================================" -ForegroundColor Yellow
    Write-Warning "  MODO DRY RUN - NENHUMA AÇÃO TOMADA" -ForegroundColor Yellow  
    Write-Warning "========================================" -ForegroundColor Yellow
    Write-Host ""
    Write-Info "Execute sem --DryRun para realmente criar o release:"
    Write-Info "  .\release.ps1 -Version $Version"
    Write-Host ""
}
