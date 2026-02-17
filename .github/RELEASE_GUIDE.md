# 📦 Guia para Criar Release no GitHub

Este guia explica como criar uma release no GitHub para o sisPROJETOS.

## 🎯 Pré-requisitos

- [ ] Código testado e funcionando
- [ ] CHANGELOG.md atualizado
- [ ] Versão atualizada em `src/__version__.py`
- [ ] Build do instalador criado (se aplicável)
- [ ] Release notes preparadas

## 🚀 Passo a Passo

### 1. Preparar a Release

```bash
# Certifique-se de estar na branch main
git checkout main
git pull origin main

# Verifique a versão
cat sisPROJETOS_revived/src/__version__.py
```

### 2. Criar Tag Git

```bash
# Crie uma tag anotada
git tag -a v2.0.1 -m "Release v2.0.1 - Melhorias em testes e documentação"

# Push da tag para o GitHub
git push origin v2.0.1
```

### 3. Criar Release no GitHub (via Interface Web)

1. **Acesse o repositório no GitHub**
   ```
   https://github.com/jrlampa/sisPROJETOS_v1.1
   ```

2. **Vá para a seção Releases**
   - Clique em "Releases" no menu lateral direito
   - Ou acesse: `https://github.com/jrlampa/sisPROJETOS_v1.1/releases`

3. **Clique em "Draft a new release"**

4. **Preencha os dados da Release**

   **Tag version:**
   ```
   v2.0.1
   ```

   **Release title:**
   ```
   sisPROJETOS v2.0.1 - Melhorias em Testes e Documentação
   ```

   **Description:** (use o conteúdo de `RELEASE_NOTES_v2.0.1.md`)
   
   Copie e cole o conteúdo do arquivo `RELEASE_NOTES_v2.0.1.md`

5. **Anexar Binários (Assets)**

   Se houver o instalador compilado:
   - Clique em "Attach binaries"
   - Faça upload de `sisPROJETOS_v2.0.1_Setup.exe`
   - Adicione checksums se disponíveis

6. **Opções Adicionais**

   - [ ] **Set as the latest release** - Marque se for a versão mais recente
   - [ ] **Set as a pre-release** - Marque apenas se for uma versão beta/RC
   - [ ] **Create a discussion for this release** - Opcional

7. **Publish Release**

   - Revise todas as informações
   - Clique em "Publish release"

### 4. Criar Release via GitHub CLI (Alternativa)

```bash
# Instale o GitHub CLI se ainda não tiver
# https://cli.github.com/

# Login
gh auth login

# Criar release
gh release create v2.0.1 \
  --title "sisPROJETOS v2.0.1 - Melhorias em Testes e Documentação" \
  --notes-file RELEASE_NOTES_v2.0.1.md \
  sisPROJETOS_v2.0.1_Setup.exe#"Instalador Windows"

# Verificar
gh release view v2.0.1
```

## 📋 Template de Release Notes

Use este template ao criar releases futuras:

```markdown
# 🎉 Release v{VERSION}

**Data de Lançamento:** {DATA}

## ✨ Novidades
- Feature 1
- Feature 2

## 🐛 Correções
- Fix 1
- Fix 2

## 🚀 Otimizações
- Otimização 1
- Otimização 2

## 📦 Download

- [Instalador Windows](link-para-instalador)
- [Código Fonte](link-para-source)

## 🚧 Instalação

### Usuário Final
1. Download do instalador
2. Execute o instalador
3. Siga as instruções

### Desenvolvedor
\`\`\`bash
git clone https://github.com/jrlampa/sisPROJETOS_v1.1.git
cd sisPROJETOS_v1.1/sisPROJETOS_revived
pip install -r requirements.txt
python run.py
\`\`\`

## 🐛 Problemas Conhecidos
- Issue 1
- Issue 2

## 🙏 Agradecimentos
- Contribuidor 1
- Contribuidor 2
```

## 🔄 Versionamento Semântico

Siga [Semantic Versioning](https://semver.org/):

- **MAJOR** (X.0.0): Mudanças incompatíveis de API
- **MINOR** (0.X.0): Novas funcionalidades (compatível)
- **PATCH** (0.0.X): Correções de bugs (compatível)

Exemplos:
- `2.0.0` → `2.0.1`: Bug fixes
- `2.0.1` → `2.1.0`: Nova funcionalidade
- `2.1.0` → `3.0.0`: Breaking changes

## ✅ Checklist Pós-Release

Após publicar a release:

- [ ] Verificar que a release aparece corretamente
- [ ] Testar download dos assets
- [ ] Atualizar README.md com link para nova release
- [ ] Atualizar landing page (docs/) se necessário
- [ ] Anunciar nas redes sociais / comunidade
- [ ] Fechar issues relacionadas
- [ ] Atualizar CHANGELOG.md se ainda não foi feito

## 🔗 Links Úteis

- [GitHub Releases Documentation](https://docs.github.com/en/repositories/releasing-projects-on-github)
- [Semantic Versioning](https://semver.org/)
- [Keep a Changelog](https://keepachangelog.com/)
- [GitHub CLI](https://cli.github.com/)

## 📞 Problemas?

Se encontrar problemas ao criar a release:

1. Verifique se tem permissões adequadas no repositório
2. Certifique-se de que a tag Git foi criada corretamente
3. Consulte a [documentação do GitHub](https://docs.github.com/en/repositories/releasing-projects-on-github)

---

**Desenvolvido com ❤️ para sisPROJETOS**
