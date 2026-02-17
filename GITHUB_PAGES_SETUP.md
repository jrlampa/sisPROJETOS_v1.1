# 🌐 Configuração do GitHub Pages

Este guia explica como configurar o GitHub Pages para hospedar a landing page do sisPROJETOS.

## ✅ Arquivos Necessários

Todos os arquivos já foram criados e estão no diretório `docs/`:

- ✅ `docs/index.html` - Página principal
- ✅ `docs/styles.css` - Estilos
- ✅ `docs/script.js` - Scripts
- ✅ `docs/_config.yml` - Configuração Jekyll
- ✅ `docs/.nojekyll` - Bypass Jekyll
- ✅ `docs/README.md` - Documentação
- ✅ `.github/workflows/pages.yml` - GitHub Actions workflow

## 🚀 Ativando o GitHub Pages

### Método 1: Via Interface Web (Recomendado)

1. **Acesse as configurações do repositório**
   ```
   https://github.com/jrlampa/sisPROJETOS_v1.1/settings
   ```

2. **Navegue até Pages**
   - No menu lateral esquerdo, clique em "Pages"
   - Ou acesse diretamente: `https://github.com/jrlampa/sisPROJETOS_v1.1/settings/pages`

3. **Configure a Source**
   - **Source**: Selecione "Deploy from a branch"
   - **Branch**: Selecione `main`
   - **Folder**: Selecione `/docs`
   - Clique em "Save"

4. **Aguarde o Deploy**
   - O GitHub irá processar e fazer deploy automaticamente
   - Aguarde 1-2 minutos
   - A URL será exibida: `https://jrlampa.github.io/sisPROJETOS_v1.1`

### Método 2: Via GitHub Actions (Automático)

O workflow já está configurado em `.github/workflows/pages.yml` e será executado automaticamente quando:
- Houver push para a branch `main` com mudanças em `docs/**`
- Ou quando executado manualmente via "Actions" → "Deploy to GitHub Pages" → "Run workflow"

## 🔍 Verificando o Deploy

### 1. Via Actions Tab

```
https://github.com/jrlampa/sisPROJETOS_v1.1/actions
```

- Procure pelo workflow "Deploy to GitHub Pages"
- Verifique se a execução foi bem-sucedida (✅)

### 2. Via Settings → Pages

```
https://github.com/jrlampa/sisPROJETOS_v1.1/settings/pages
```

- Verifique se a URL está ativa
- Status deve mostrar "Your site is live at..."

### 3. Acesse a Landing Page

```
https://jrlampa.github.io/sisPROJETOS_v1.1
```

## 🎨 Estrutura da Landing Page

A landing page inclui as seguintes seções:

1. **Navigation** - Menu fixo com links
2. **Hero Section** - Apresentação principal com CTAs
3. **Features** - 9 módulos especializados
4. **Tech Stack** - Tecnologias utilizadas
5. **Download** - Links para releases
6. **Documentation** - Links para docs
7. **About** - Sobre o projeto e autor
8. **Roadmap** - Planejamento futuro
9. **Footer** - Links e informações

## 🔧 Personalizando a Landing Page

### Alterar Cores

Edite `docs/styles.css` e modifique as variáveis CSS:

```css
:root {
    --primary-color: #3B82F6;      /* Cor principal */
    --secondary-color: #10B981;    /* Cor secundária */
    --accent-color: #F59E0B;       /* Cor de destaque */
    /* ... outras variáveis */
}
```

### Alterar Conteúdo

Edite `docs/index.html` e modifique as seções desejadas.

### Adicionar Análise (Google Analytics)

1. Edite `docs/_config.yml`
2. Descomente e adicione seu tracking ID:
   ```yaml
   google_analytics: UA-XXXXXXXXX-X
   ```

## 📱 Testando Localmente

### Opção 1: Python Simple Server

```bash
cd docs
python -m http.server 8000
# Acesse http://localhost:8000
```

### Opção 2: Jekyll (Completo)

```bash
# Instale Jekyll
gem install jekyll bundler

# Execute
cd docs
jekyll serve
# Acesse http://localhost:4000
```

### Opção 3: VS Code Live Server

1. Instale a extensão "Live Server"
2. Abra `docs/index.html`
3. Clique com botão direito → "Open with Live Server"

## 🌍 Domínio Customizado (Opcional)

Se você possui um domínio próprio:

1. **Crie arquivo CNAME**
   ```bash
   echo "seudominio.com" > docs/CNAME
   ```

2. **Configure DNS no seu provedor**
   - Adicione um CNAME record:
     ```
     www.seudominio.com → jrlampa.github.io
     ```
   - Adicione A records para apex domain:
     ```
     185.199.108.153
     185.199.109.153
     185.199.110.153
     185.199.111.153
     ```

3. **Ative HTTPS**
   - Em Settings → Pages
   - Marque "Enforce HTTPS"

## 🔒 Configurações de Segurança

### HTTPS

- Sempre ativado por padrão no GitHub Pages
- Certificados SSL gerenciados automaticamente

### Permissions

O workflow precisa das seguintes permissões (já configuradas):

```yaml
permissions:
  contents: read
  pages: write
  id-token: write
```

## 🐛 Troubleshooting

### Landing Page não aparece

1. Verifique se está na branch correta (`main`)
2. Confirme que os arquivos estão em `docs/`
3. Verifique Actions para erros de build
4. Aguarde alguns minutos (cache pode demorar)

### Estilos não carregam

1. Verifique caminhos relativos no HTML
2. Confirme que `styles.css` está em `docs/`
3. Limpe cache do navegador (Ctrl+F5)

### 404 Error

1. Verifique se o repositório é público
2. Confirme configuração em Settings → Pages
3. Verifique se a branch/folder estão corretos

### Mudanças não aparecem

1. Faça commit e push das alterações
2. Aguarde o workflow executar (1-2 min)
3. Limpe cache do navegador
4. Tente modo incógnito

## 📊 Monitoramento

### GitHub Actions

- Monitore builds em: `https://github.com/jrlampa/sisPROJETOS_v1.1/actions`
- Receba notificações de falhas por email

### Analytics (Opcional)

Adicione Google Analytics ou Plausible para monitorar:
- Visitantes únicos
- Páginas vistas
- Origem de tráfego
- Dispositivos utilizados

## 🔄 Atualizando a Landing Page

```bash
# 1. Edite os arquivos em docs/
vim docs/index.html

# 2. Teste localmente
cd docs && python -m http.server 8000

# 3. Commit e push
git add docs/
git commit -m "Update landing page"
git push origin main

# 4. Aguarde deploy automático (1-2 min)
```

## 📚 Recursos Adicionais

- [GitHub Pages Documentation](https://docs.github.com/en/pages)
- [Jekyll Documentation](https://jekyllrb.com/docs/)
- [GitHub Actions for Pages](https://github.com/actions/deploy-pages)
- [Custom Domains](https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site)

## ✅ Checklist de Verificação

Após configurar o GitHub Pages:

- [ ] Landing page está acessível
- [ ] Todos os links funcionam
- [ ] CSS e JS estão carregando
- [ ] Responsivo em mobile
- [ ] SEO otimizado (meta tags)
- [ ] Performance boa (Lighthouse)
- [ ] HTTPS ativado
- [ ] Domínio customizado (se aplicável)

---

**�� Parabéns! Sua landing page está no ar!**

Acesse: https://jrlampa.github.io/sisPROJETOS_v1.1
