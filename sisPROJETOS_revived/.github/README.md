# GitHub Workflows - sisPROJETOS

Este diretório contém workflows do GitHub Actions para automação de CI/CD.

## 📋 Workflows Disponíveis

### 1. **Continuous Integration** (`ci.yml`)

**Trigger**: Push ou PR para `main`, `develop`, `feature/*`, `fix/*`

**Funcionalidades**:
- ✅ Lint code (flake8, black, isort)
- ✅ Testes no Windows e Linux
- ✅ Security scan (Bandit, Safety)
- ✅ Dependency audit
- ✅ Code quality metrics (radon)
- ✅ Coverage report (Codecov)

**Jobs**:
1. `lint` - Verificação de estilo de código
2. `test-windows` - Testes em Windows (Python 3.12)
3. `test-linux` - Testes em Linux (Python 3.12)
4. `security-scan` - Análise de segurança
5. `dependency-check` - Verifica dependências desatualizadas
6. `code-quality` - Métricas de complexidade e manutenibilidade
7. `coverage-report` - Upload de coverage para Codecov
8. `notify-status` - Notificação de status geral

**Status Badges**:
```markdown
![CI](https://github.com/jrlampa/sisPROJETOS_v1.1/workflows/Continuous%20Integration/badge.svg)
```

---

### 2. **Build and Release** (`build-release.yml`)

**Trigger**:
- Tags `v*` (e.g., `v2.0.1`)
- Manual dispatch (workflow_dispatch)

**Funcionalidades**:
- ✅ Execute testes completos
- ✅ Build executável com PyInstaller
- ✅ Cria instalador com Inno Setup
- ✅ Cria GitHub Release automaticamente
- ✅ Upload de assets (exe, LICENSE, CHANGELOG)

**Jobs**:
1. `test` - Executa suite de testes completa
2. `build` - Compila executável com PyInstaller
3. `create-installer` - Cria instalador Windows (.exe)
4. `create-release` - Cria release no GitHub
5. `notify` - Notificação de conclusão

**Como Criar um Release**:

```bash
# 1. Atualize a versão
# Em src/__version__.py:
__version__ = "2.0.2"

# 2. Atualize CHANGELOG.md
# Adicione entry para v2.0.2

# 3. Commit e crie tag
git add .
git commit -m "chore: bump version to 2.0.2"
git tag v2.0.2
git push origin main --tags

# O workflow será disparado automaticamente!
```

**Trigger Manual**:

1. Vá para Actions > Build and Release
2. Clique em "Run workflow"
3. Digite a versão (e.g., `2.0.2`)
4. Clique em "Run workflow"

---

### 3. **Dependency Update** (`dependency-update.yml`)

**Trigger**:
- Schedule: Toda segunda-feira, 9:00 AM UTC
- Manual dispatch

**Funcionalidades**:
- ✅ Verifica dependências desatualizadas
- ✅ Atualiza requirements.txt
- ✅ Executa testes com novas versões
- ✅ Cria PR automaticamente

**Jobs**:
1. `update-dependencies` - Atualiza deps e cria PR

**Processo**:
1. Detecta pacotes desatualizados
2. Atualiza requirements.txt
3. Executa testes de regressão
4. Cria PR com changelog de atualizações
5. Requer revisão manual antes de merge

---

## 🔐 Secrets Necessários

Configure estes secrets no GitHub (Settings > Secrets):

| Secret | Descrição | Obrigatório |
|--------|-----------|-------------|
| `GROQ_API_KEY` | Chave API do Groq (para testes do AI Assistant) | Sim |
| `CODECOV_TOKEN` | Token do Codecov (para coverage reports) | Não |
| `GITHUB_TOKEN` | Criado automaticamente pelo GitHub | Auto |

**Como adicionar secrets**:

1. Vá para: `https://github.com/jrlampa/sisPROJETOS_v1.1/settings/secrets/actions`
2. Clique em "New repository secret"
3. Nome: `GROQ_API_KEY`
4. Valor: Sua chave do Groq Console
5. Clique em "Add secret"

---

## 📊 Status Atual

### Badges Disponíveis

Adicione ao README.md principal:

```markdown
<!-- CI Status -->
![CI](https://github.com/jrlampa/sisPROJETOS_v1.1/workflows/Continuous%20Integration/badge.svg)

<!-- Build Status -->
![Build](https://github.com/jrlampa/sisPROJETOS_v1.1/workflows/Build%20and%20Release/badge.svg)

<!-- Coverage -->
[![codecov](https://codecov.io/gh/jrlampa/sisPROJETOS_v1.1/branch/main/graph/badge.svg)](https://codecov.io/gh/jrlampa/sisPROJETOS_v1.1)

<!-- Python Version -->
![Python](https://img.shields.io/badge/Python-3.12-blue.svg)

<!-- License -->
![License](https://img.shields.io/badge/License-MIT-green.svg)
```

---

## 🚀 Roadmap de CI/CD

### ✅ Implementado

- [x] Lint automático (flake8, black, isort)
- [x] Testes multi-plataforma (Windows, Linux)
- [x] Build automatizado (PyInstaller)
- [x] Instalador automatizado (Inno Setup)
- [x] GitHub Releases automáticas
- [x] Security scanning (Bandit, Safety)
- [x] Dependency updates automáticos
- [x] Code coverage (Codecov)

### 🔜 Próximos Passos

- [ ] Code signing (certificado comercial)
- [ ] Deploy para Microsoft Store
- [ ] Testes de integração E2E
- [ ] Performance benchmarking
- [ ] Docker container para testes
- [ ] Slack/Discord notifications
- [ ] Automated changelog generation
- [ ] Semantic versioning enforcement

---

## 🐛 Troubleshooting

### Workflow falha no job `test`

**Problema**: Testes falham devido a falta de GROQ_API_KEY

**Solução**:
```bash
# Adicione o secret GROQ_API_KEY no repositório
# ou desabilite testes do AI Assistant temporariamente
```

### Workflow falha no job `create-installer`

**Problema**: Inno Setup download falha

**Solução**:
```yaml
# Use cache para Inno Setup installer
- name: Cache Inno Setup
  uses: actions/cache@v3
  with:
    path: innosetup.exe
    key: innosetup-6
```

### Build é muito lento

**Solução**:
```yaml
# Habilite caching de pip
- uses: actions/setup-python@v5
  with:
    python-version: '3.12'
    cache: 'pip'  # ← Caching habilitado
```

---

## 📚 Documentação Adicional

- [GitHub Actions Docs](https://docs.github.com/en/actions)
- [PyInstaller Manual](https://pyinstaller.org/en/stable/)
- [Inno Setup Help](https://jrsoftware.org/ishelp/)
- [Codecov Docs](https://docs.codecov.com/)

---

## 📞 Contato

Para problemas com CI/CD:
- Abra uma [Issue](https://github.com/jrlampa/sisPROJETOS_v1.1/issues)
- Tag: `ci/cd`, `github-actions`
