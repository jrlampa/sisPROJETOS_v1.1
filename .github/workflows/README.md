# 🚀 GitHub Actions Workflows

Este diretório contém os workflows automatizados do GitHub Actions para o sisPROJETOS.

## 📋 Workflows Disponíveis

### 1. Build and Release (`release.yml`)

Workflow automatizado para criar releases com binários compilados do sisPROJETOS.

**🎯 Objetivo:** Compilar o aplicativo Python em executável Windows usando PyInstaller e criar uma release no GitHub.

**⚙️ Quando é Executado:**
- **Automático:** Quando uma tag de versão é criada (formato `v*.*.*`, ex: `v2.0.1`)
- **Manual:** Via workflow_dispatch na interface do GitHub Actions

**📦 O que é Gerado:**
1. **Arquivos ZIP:**
   - `sisPROJETOS-{version}-Windows-Portable.zip` - Versão portátil (apenas arquivos necessários)
   - `sisPROJETOS-{version}-Windows-Full.zip` - Distribuição completa (com estrutura de pastas dist/)

2. **Instalador (se Inno Setup estiver disponível):**
   - `sisPROJETOS_v{version}_Setup.exe` - Instalador completo para Windows

3. **Checksums:**
   - `checksums.txt` - Hashes SHA256 para verificação de integridade

**🔧 Como Usar:**

#### Opção 1: Criar Release com Tag (Recomendado)

```bash
# 1. Certifique-se que está na branch main
git checkout main
git pull origin main

# 2. Crie uma tag de versão
git tag -a v2.0.2 -m "Release v2.0.2 - Descrição das mudanças"

# 3. Envie a tag para o GitHub
git push origin v2.0.2

# 4. O workflow será executado automaticamente!
# Acompanhe em: https://github.com/jrlampa/sisPROJETOS_v1.1/actions
```

#### Opção 2: Executar Manualmente

1. Vá para: https://github.com/jrlampa/sisPROJETOS_v1.1/actions
2. Selecione o workflow "Build and Release"
3. Clique em "Run workflow"
4. Digite a versão (ex: `v2.0.2`)
5. Clique em "Run workflow"

**📝 Etapas do Workflow:**

1. ✅ **Checkout:** Clona o código do repositório
2. ✅ **Setup Python:** Configura Python 3.12
3. ✅ **Install dependencies:** Instala dependências do `requirements.txt`
4. ✅ **Run tests:** Executa testes com pytest (build falha se testes falharem)
5. ✅ **Build executable:** Compila com PyInstaller usando `sisprojetos.spec`
6. ✅ **Validate build:** Verifica se o executável foi criado corretamente
7. ✅ **Create archives:** Cria arquivos ZIP com checksums SHA256
8. ✅ **Build installer:** Tenta criar instalador Inno Setup (opcional)
9. ✅ **Upload artifacts:** Envia arquivos para GitHub Actions artifacts
10. ✅ **Create Release:** Cria release no GitHub (apenas se tag foi criada)

**🔍 Validações Incluídas:**

- ✅ Executável `sisPROJETOS.exe` foi criado
- ✅ Tamanho do executável (informativo)
- ✅ Total de arquivos na distribuição
- ✅ Recursos necessários estão presentes:
  - `resources/templates/` (arquivos DWG, XLSX)
  - `modules/catenaria/resources/` (condutores.json)

**🛠️ Configuração do Build:**

O build usa o arquivo `sisPROJETOS_revived/sisprojetos.spec` com as seguintes otimizações:

- **Bytecode optimization:** Nível 2
- **Hidden imports:** Customtkinter, Tkinter, PIL, Numpy, Pandas, etc.
- **Resources incluídos:** Templates DWG/XLSX, recursos da catenária
- **Database:** NÃO incluído (será criado em AppData na primeira execução)
- **Target architecture:** x86_64 (64-bit)
- **Console:** Desabilitado (aplicação GUI)

**📊 Métricas Esperadas:**

- **Tempo de build:** ~5-10 minutos
- **Tamanho do executável:** ~3-5 MB
- **Tamanho da distribuição:** ~150-250 MB
- **Tamanho do ZIP Portable:** ~60-90 MB
- **Total de arquivos:** ~2000-2500 arquivos

**❗ Resolução de Problemas:**

**Problema:** Build falha com "Module not found"
```
Solução: Verificar se todas as dependências estão em requirements.txt
```

**Problema:** Testes falham
```
Solução: Corrigir os testes antes de criar a release - o build não continua se os testes falharem
```

**Problema:** Executável não é criado
```
Solução: Verificar logs do PyInstaller no GitHub Actions para detalhes do erro
```

**Problema:** Release não é criada
```
Solução: Verificar se a tag foi criada corretamente (formato v*.*.*) e se o workflow foi acionado
```

---

### 2. CI Pipeline (`ci.yml`)

Workflow de integração contínua que executa em cada push/PR.

**⚙️ Quando é Executado:**
- Push para branches: `main`, `develop`, `copilot/**`
- Pull Requests para: `main`, `develop`

**📝 O que Faz:**
1. Executa linter (flake8) para verificar erros críticos
2. Executa testes com pytest
3. Gera relatório de cobertura
4. Envia cobertura para Codecov

---

### 3. CodeQL Advanced (`codeql.yml`)

Análise de segurança do código.

**⚙️ Quando é Executado:**
- Push para `main`
- Pull Requests para `main`
- Agendado semanalmente (segundas 06:00 UTC)

**📝 O que Faz:**
- Analisa código Python em busca de vulnerabilidades
- Detecta problemas de segurança comuns
- Gera relatórios de segurança no GitHub Security

---

### 4. Deploy to GitHub Pages (`pages.yml`)

Deploy da documentação para GitHub Pages.

**⚙️ Quando é Executado:**
- Push para `main` com mudanças em `docs/`
- Manual via workflow_dispatch

**📝 O que Faz:**
- Publica documentação em https://jrlampa.github.io/sisPROJETOS_v1.1/

---

## 🎓 Melhores Práticas

### Versionamento Semântico

Siga o padrão SemVer: `MAJOR.MINOR.PATCH`

- **MAJOR (X.0.0):** Mudanças incompatíveis de API
- **MINOR (0.X.0):** Novas funcionalidades (compatível)
- **PATCH (0.0.X):** Correções de bugs (compatível)

Exemplos:
```bash
git tag -a v2.0.0 -m "Release 2.0.0 - Versão base"
git tag -a v2.0.1 -m "Release 2.0.1 - Correção de bugs"
git tag -a v2.1.0 -m "Release 2.1.0 - Nova funcionalidade"
git tag -a v3.0.0 -m "Release 3.0.0 - Breaking changes"
```

### Checklist Antes de Criar Release

- [ ] Todos os testes passando localmente
- [ ] CHANGELOG.md atualizado
- [ ] Versão atualizada em `src/__version__.py` (se aplicável)
- [ ] Código commitado e enviado para `main`
- [ ] Branch está limpo (`git status`)
- [ ] Tag criada com mensagem descritiva

### Testando o Build Localmente

Antes de criar uma release, teste o build localmente:

```powershell
cd sisPROJETOS_revived

# 1. Executar testes
pytest tests/ -v

# 2. Build com PyInstaller
python -m PyInstaller sisprojetos.spec --clean --noconfirm

# 3. Testar executável
cd dist/sisPROJETOS
.\sisPROJETOS.exe

# 4. Verificar se funciona corretamente
```

---

## 🔗 Links Úteis

- **GitHub Actions:** https://github.com/jrlampa/sisPROJETOS_v1.1/actions
- **Releases:** https://github.com/jrlampa/sisPROJETOS_v1.1/releases
- **PyInstaller Docs:** https://pyinstaller.org/en/stable/
- **Inno Setup:** https://jrsoftware.org/isinfo.php
- **Semantic Versioning:** https://semver.org/

---

## 📞 Suporte

Se encontrar problemas com os workflows:

1. **Verifique os logs:** Clique no workflow em Actions e veja os logs detalhados
2. **Issues conhecidos:** Verifique a [página de Issues](https://github.com/jrlampa/sisPROJETOS_v1.1/issues)
3. **Reporte problema:** Abra uma nova issue com os logs do erro

---

**Desenvolvido com ❤️ para sisPROJETOS**
