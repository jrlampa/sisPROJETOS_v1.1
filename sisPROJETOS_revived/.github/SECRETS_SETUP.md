# 🔐 Configuração de Secrets do GitHub - sisPROJETOS

Este guia explica como configurar os secrets necessários para os workflows de CI/CD funcionarem corretamente.

---

## 📋 Secrets Necessários

| Secret | Prioridade | Descrição | Usado Em |
|--------|-----------|-----------|----------|
| `GROQ_API_KEY` | **OBRIGATÓRIO** | Chave API do Groq para testes do AI Assistant | CI, Build & Release |
| `CODECOV_TOKEN` | Opcional | Token do Codecov para reports de cobertura | CI |

---

## ⚙️ Como Configurar (Passo a Passo)

### 1. Acessar Configurações de Secrets

1. Vá para o repositório no GitHub:
   ```
   https://github.com/jrlampa/sisPROJETOS_v1.1
   ```

2. Clique em **Settings** (⚙️) no menu superior

3. No menu lateral esquerdo, expanda **Secrets and variables** → clique em **Actions**

4. Você verá a página "Actions secrets and variables"

---

### 2. Adicionar GROQ_API_KEY (OBRIGATÓRIO)

**Por que é necessário?**
- Os testes do módulo AI Assistant (`tests/test_ai_assistant.py`) fazem chamadas reais à API do Groq
- Sem essa chave, o CI falhará ao executar testes

**Como obter a chave:**

1. Acesse [Groq Console](https://console.groq.com)
2. Faça login (ou crie uma conta gratuita)
3. Vá para **API Keys** no menu lateral
4. Clique em **Create API Key**
5. Dê um nome: `sisPROJETOS-CI-CD`
6. Copie a chave gerada (formato: `gsk_...`)

**Como adicionar no GitHub:**

1. Na página de Secrets, clique em **New repository secret**
2. Preencha:
   - **Name**: `GROQ_API_KEY`
   - **Value**: Cole a chave do Groq (ex: `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`)
3. Clique em **Add secret**

✅ **Pronto!** O CI agora pode executar testes do AI Assistant.

---

### 3. Adicionar CODECOV_TOKEN (Opcional)

**Por que é necessário?**
- Permite enviar relatórios de cobertura de código para [Codecov.io](https://codecov.io)
- Gera badges e gráficos de cobertura
- **Não é obrigatório** - o CI funciona sem ele

**Como obter o token:**

1. Acesse [Codecov](https://codecov.io) e faça login com GitHub
2. Clique em **Add new repository**
3. Selecione `jrlampa/sisPROJETOS_v1.1`
4. Na página da do repositório, vá para **Settings** → **General**
5. Copie o **Repository Upload Token**

**Como adicionar no GitHub:**

1. Na página de Secrets, clique em **New repository secret**
2. Preencha:
   - **Name**: `CODECOV_TOKEN`
   - **Value**: Cole o token do Codecov
3. Clique em **Add secret**

✅ **Opcional completo!** Coverage reports serão enviados automaticamente.

---

## 🔍 Verificar Secrets Configurados

Após adicionar, você verá os secrets listados:

```
Environment secrets
┌──────────────────┬──────────────┐
│ Name             │ Updated      │
├──────────────────┼──────────────┤
│ GROQ_API_KEY     │ Just now     │
│ CODECOV_TOKEN    │ Just now     │
└──────────────────┴──────────────┘
```

⚠️ **Nota**: Você **NÃO** poderá ver os valores dos secrets após salvá-los (por segurança).

---

## ✅ Testar Configuração

### Teste 1: Executar Workflow Manualmente

1. Vá para **Actions** no repositório
2. Selecione **Continuous Integration** no menu lateral
3. Clique em **Run workflow** → **Run workflow**
4. Aguarde ~3-5 minutos
5. Se tudo estiver OK, você verá ✅ verde

### Teste 2: Verificar Logs do Workflow

1. Clique no workflow que acabou de rodar
2. Expanda o job **test-windows**
3. Clique em **Run tests**
4. Procure por:
   ```
   tests/test_ai_assistant.py::test_ai_assistant_query PASSED
   ```

Se passar, a chave está funcionando! 🎉

---

## 🐛 Troubleshooting

### Erro: "GROQ_API_KEY not found"

**Problema**: Secret não está configurado ou nome incorreto

**Solução**:
1. Verifique se o nome é EXATAMENTE `GROQ_API_KEY` (case-sensitive)
2. Verifique se está em **Repository secrets** (não Environment secrets)
3. Tente remover e adicionar novamente

### Erro: "Invalid API key"

**Problema**: Chave expirou ou está incorreta

**Solução**:
1. Gere uma nova chave no [Groq Console](https://console.groq.com)
2. Atualize o secret no GitHub:
   - Settings → Secrets → Actions
   - Clique em `GROQ_API_KEY`
   - Clique em **Update secret**
   - Cole a nova chave

### Testes do AI Assistant são pulados (skipped)

**Problema**: Chave não está sendo passada para os testes

**Verificação**:
```yaml
# Em .github/workflows/ci.yml
- name: Run tests
  run: pytest tests/ -v
  env:
    GROQ_API_KEY: ${{ secrets.GROQ_API_KEY }}  # ← Esta linha deve existir
```

---

## 📚 Secrets Automáticos do GitHub

Além dos secrets que você configura, o GitHub fornece automaticamente:

| Secret | Descrição |
|--------|-----------|
| `GITHUB_TOKEN` | Token de autenticação gerado automaticamente |
| `GITHUB_REPOSITORY` | Owner/nome do repo (ex: jrlampa/sisPROJETOS_v1.1) |
| `GITHUB_REF` | Referência Git (branch ou tag) |
| `GITHUB_SHA` | Hash do commit |

Esses **NÃO** precisam ser configurados manualmente.

---

## 🔒 Segurança Best Practices

### ✅ Faça:
- Use secrets diferentes para dev/staging/production
- Rotacione chaves API periodicamente (a cada 3-6 meses)
- Use chaves com permissões mínimas necessárias
- Revogue chaves antigas ao gerar novas

### ❌ Não faça:
- Nunca commite secrets no código (use .env e .gitignore)
- Nunca compartilhe secrets em issues/PRs públicas
- Nunca faça echo/print de secrets nos logs do CI
- Nunca use a mesma chave em múltiplos projetos

---

## 📊 Status Esperado Após Configuração

Com todos os secrets configurados:

✅ **CI Workflow (`.github/workflows/ci.yml`)**:
- ✅ Lint: PASSED
- ✅ Tests (Windows): PASSED (107 testes)
- ✅ Tests (Linux): PASSED
- ✅ Security Scan: PASSED
- ✅ Coverage Report: Enviado para Codecov

✅ **Build & Release Workflow (`.github/workflows/build-release.yml`)**:
- ✅ Test: PASSED
- ✅ Build: Executável criado (dist/sisPROJETOS/)
- ✅ Create Installer: .exe criado (installer_output/)
- ✅ Create Release: GitHub Release publicada

---

## 🚀 Próximos Passos

Após configurar os secrets:

1. ✅ **Testar CI/CD**: Faça um commit/push para testar
2. ✅ **Criar Release**: Crie uma tag `v2.0.1` para disparar build automático
3. ✅ **Monitorar**: Acompanhe workflows na aba Actions
4. 📈 **Codecov Badge**: Adicione ao README.md:
   ```markdown
   [![codecov](https://codecov.io/gh/jrlampa/sisPROJETOS_v1.1/branch/main/graph/badge.svg?token=SEU_TOKEN)](https://codecov.io/gh/jrlampa/sisPROJETOS_v1.1)
   ```

---

## 📞 Ajuda Adicional

- **Documentação GitHub Secrets**: https://docs.github.com/en/actions/security-guides/encrypted-secrets
- **Groq API Docs**: https://console.groq.com/docs
- **Codecov Docs**: https://docs.codecov.com/docs

---

## ✔️ Checklist de Configuração

```markdown
- [ ] Criou conta no Groq Console
- [ ] Gerou GROQ_API_KEY
- [ ] Adicionou GROQ_API_KEY no GitHub Secrets
- [ ] (Opcional) Criou conta no Codecov
- [ ] (Opcional) Gerou CODECOV_TOKEN
- [ ] (Opcional) Adicionou CODECOV_TOKEN no GitHub Secrets
- [ ] Testou CI rodando workflow manualmente
- [ ] Verificou que testes passam
```

---

<div align="center">

**🎉 Configuração completa! Seu CI/CD está pronto para uso.**

[⬅️ Voltar para .github/README.md](README.md)

</div>
