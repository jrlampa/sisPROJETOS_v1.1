# ⚡ Guia Rápido - Adicionar GitHub Secrets (2 min)

## 🎯 Tarefa: Adicionar GROQ_API_KEY ao GitHub

Os secrets **NÃO podem ser adicionados programaticamente** por questões de segurança. Você precisa fazer isso manualmente no GitHub.

---

## 📍 Localização no GitHub

```
Repository → Settings ⚙️ → Secrets and variables → Actions
```

URL direta:
```
https://github.com/jrlampa/sisPROJETOS_v1.1/settings/secrets/actions
```

---

## ⚡ Passos Rápidos (2 minutos)

### 1️⃣ Obter GROQ_API_KEY

1. Acesse: https://console.groq.com
2. Login (ou crie conta gratuita)
3. Menu: **API Keys**
4. Clique: **Create API Key**
5. Copie a chave (formato: `gsk_...`)

### 2️⃣ Adicionar no GitHub

1. Vá para: https://github.com/jrlampa/sisPROJETOS_v1.1/settings/secrets/actions
2. Clique: **New repository secret**
3. Preencha:
   - **Name**: `GROQ_API_KEY`
   - **Value**: Cole a chave do Groq
4. Clique: **Add secret**

✅ **Pronto!**

---

## ✅ Verificar Configuração

Depois de adicionar:

1. Vá para: https://github.com/jrlampa/sisPROJETOS_v1.1/actions
2. Selecione: **Continuous Integration**
3. Clique: **Run workflow**
4. Selecione: **main** branch
5. Clique: **Run workflow**
6. Aguarde ~3-5 minutos
7. Procure por ✅ verde nos testes

---

## 🔒 Segurança

⚠️ **IMPORTANTE**:
- Você **NÃO** verá o valor do secret após salvar (por segurança)
- Cada workflow acessa via `${{ secrets.GROQ_API_KEY }}`
- Nunca commite secrets no código

---

## 📊 Resultado Esperado

Após adicionar:

```
✅ Repository secrets
├── GROQ_API_KEY        │ Updated now
└── CODECOV_TOKEN       │ (opcional)
```

---

## 🚀 E agora?

Após adicionar o secret:

1. ✅ CI/CD estará 100% funcional
2. ✅ GitHub Actions poderá rodar testes
3. ✅ Build automático funcionará quando criar próxima tag

**Tempo para aparecer**: ~2 minutos após adicionar

---

## 📞 Precisa de Detalhes?

Veja guia completo em: [.github/SECRETS_SETUP.md](SECRETS_SETUP.md)

Tem dúvidas sobre Groq API? [console.groq.com/docs](https://console.groq.com/docs)

---

<div align="center">

⏱️ **Tempo estimado: 2-3 minutos**

Após fazer isso, seu CI/CD estará **100% operacional!**

</div>
