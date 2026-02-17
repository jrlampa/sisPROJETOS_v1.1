# 🚀 Guia Rápido: Como Criar uma Release

Este guia rápido mostra como criar uma release do sisPROJETOS com binários compilados automaticamente.

## 📋 Pré-requisitos

- [x] Código testado e funcionando
- [x] Branch `main` atualizada
- [x] CHANGELOG.md atualizado (opcional mas recomendado)

## 🎯 Passo a Passo Rápido

### 1️⃣ Preparar o Código

```bash
# Certifique-se de estar na branch main
git checkout main
git pull origin main

# Verifique que está tudo OK
git status
```

### 2️⃣ Criar a Tag de Versão

```bash
# Formato: v{MAJOR}.{MINOR}.{PATCH}
# Exemplos: v2.0.2, v2.1.0, v3.0.0

git tag -a v2.0.2 -m "Release v2.0.2 - Correções de bugs e melhorias"
```

**Regras de Versionamento:**
- **v2.0.X** → Correções de bugs (patch)
- **v2.X.0** → Novas funcionalidades (minor)
- **vX.0.0** → Mudanças incompatíveis (major)

### 3️⃣ Enviar a Tag

```bash
git push origin v2.0.2
```

### 4️⃣ Acompanhar o Build

1. Abra: https://github.com/jrlampa/sisPROJETOS_v1.1/actions
2. Clique no workflow "Build and Release"
3. Aguarde ~5-10 minutos
4. ✅ Build concluído!

### 5️⃣ Verificar a Release

1. Acesse: https://github.com/jrlampa/sisPROJETOS_v1.1/releases
2. Veja sua nova release com os downloads:
   - `sisPROJETOS-v2.0.2-Windows-Portable.zip` (~60-90 MB)
   - `sisPROJETOS-v2.0.2-Windows-Full.zip` (~60-90 MB)
   - `checksums.txt` (hashes SHA256)
   - `sisPROJETOS_v2.0.2_Setup.exe` (~70 MB) - se Inno Setup estiver disponível

## 🔧 Opção Alternativa: Trigger Manual

Se você não quiser criar uma tag:

1. Vá para: https://github.com/jrlampa/sisPROJETOS_v1.1/actions
2. Selecione "Build and Release"
3. Clique em "Run workflow"
4. Digite a versão (ex: `v2.0.2`)
5. Clique em "Run workflow"

**Nota:** Esta opção NÃO cria uma release no GitHub, apenas gera os artifacts.

## ✅ O que Acontece Automaticamente

O GitHub Actions vai:

1. ✅ Fazer checkout do código
2. ✅ Configurar Python 3.12
3. ✅ Instalar dependências
4. ✅ **Executar todos os testes** (build falha se testes falharem!)
5. ✅ Compilar com PyInstaller
6. ✅ Validar que o executável foi criado
7. ✅ Criar arquivos ZIP (Portable + Full)
8. ✅ Calcular checksums SHA256
9. ✅ Tentar criar instalador Inno Setup
10. ✅ Criar release no GitHub com downloads

## 🐛 Troubleshooting

### ❌ Build falha nos testes

**Problema:** Testes estão falhando

**Solução:**
```bash
# Execute os testes localmente primeiro
cd sisPROJETOS_revived
pytest tests/ -v

# Corrija os erros
# Commit e push
git add .
git commit -m "Fix: Correções nos testes"
git push

# Crie a tag novamente (delete a antiga primeiro)
git tag -d v2.0.2
git push --delete origin v2.0.2
git tag -a v2.0.2 -m "Release v2.0.2"
git push origin v2.0.2
```

### ❌ Executável não foi criado

**Problema:** Build do PyInstaller falhou

**Solução:**
1. Veja os logs do GitHub Actions para detalhes
2. Teste o build localmente:
   ```bash
   cd sisPROJETOS_revived
   python -m PyInstaller sisprojetos.spec --clean --noconfirm
   ```
3. Corrija o erro e tente novamente

### ❌ Tag foi criada por engano

**Problema:** Criei a tag errada

**Solução:**
```bash
# Deletar tag local
git tag -d v2.0.2

# Deletar tag remota
git push --delete origin v2.0.2

# Criar tag correta
git tag -a v2.0.3 -m "Release v2.0.3"
git push origin v2.0.3
```

## 📊 Tempo Estimado

- ⏱️ **Total:** ~5-10 minutos
- Testes: ~1 minuto
- Build PyInstaller: ~3-5 minutos
- Criar archives: ~30 segundos
- Upload para release: ~1-2 minutos

## 📝 Checklist Completo

Antes de criar a release:

- [ ] Todos os testes passando (`pytest tests/ -v`)
- [ ] Código commitado e enviado para `main`
- [ ] CHANGELOG.md atualizado com as mudanças
- [ ] Versão correta escolhida (MAJOR.MINOR.PATCH)
- [ ] Tag criada com mensagem descritiva
- [ ] Tag enviada para GitHub (`git push origin v2.0.X`)

Depois da release criada:

- [ ] Verificar downloads funcionando
- [ ] Testar instalador/portable localmente
- [ ] Anunciar release (se aplicável)
- [ ] Fechar issues relacionadas

## 🔗 Links Úteis

- **Workflows:** https://github.com/jrlampa/sisPROJETOS_v1.1/actions
- **Releases:** https://github.com/jrlampa/sisPROJETOS_v1.1/releases
- **Documentação Completa:** [.github/workflows/README.md](README.md)

---

**Pronto! 🎉**

Agora você tem releases automatizadas com binários compilados!
