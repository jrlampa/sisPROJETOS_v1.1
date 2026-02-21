# 🤝 Guia de Contribuição - sisPROJETOS

Obrigado por considerar contribuir com o sisPROJETOS! Este documento fornece diretrizes para garantir um processo de contribuição suave e eficiente.

---

## 📋 Índice

1. [Código de Conduta](#-código-de-conduta)
2. [Como Contribuir](#-como-contribuir)
3. [Configuração do Ambiente](#️-configuração-do-ambiente)
4. [Padrões de Código](#-padrões-de-código)
5. [Processo de Pull Request](#-processo-de-pull-request)
6. [Reportando Bugs](#-reportando-bugs)
7. [Sugerindo Features](#-sugerindo-features)
8. [Processo de Review](#-processo-de-review)

---

## 📜 Código de Conduta

Este projeto adota um compromisso de proporcionar um ambiente acolhedor e livre de assédio para todos. Esperamos que todos os contribuidores:

- ✅ Usem linguagem acolhedora e inclusiva
- ✅ Respeitem pontos de vista diferentes
- ✅ Aceitem críticas construtivas
- ✅ Foquem no melhor para a comunidade
- ❌ Evitem linguagem sexualizada ou imagens inadequadas
- ❌ Não façam ataques pessoais ou políticos

Violações podem resultar em banimento temporário ou permanente.

---

## 💡 Como Contribuir

### Tipos de Contribuição

1. **🐛 Correção de Bugs** - Sempre bem-vinda!
2. **✨ Novas Features** - Discuta primeiro em Issues
3. **📚 Documentação** - Melhorias, traduções, exemplos
4. **🧪 Testes** - Aumentar cobertura ou melhorar existentes
5. **🎨 UI/UX** - Design, acessibilidade, usabilidade
6. **⚡ Performance** - Otimizações de código

### Primeiras Contribuições

Se é sua primeira vez contribuindo, procure por issues marcadas com:
- `good first issue` - Problemas simples para iniciantes
- `help wanted` - Problemas que precisam de ajuda
- `documentation` - Melhorias na documentação

---

## 🛠️ Configuração do Ambiente

### 1. Fork e Clone

```powershell
# Fork no GitHub (clique no botão "Fork")
# Clone seu fork
git clone https://github.com/SEU-USUARIO/sisPROJETOS_v1.1.git
cd sisPROJETOS_v1.1/sisPROJETOS_revived

# Adicione o repositório original como upstream
git remote add upstream https://github.com/jrlampa/sisPROJETOS_v1.1.git
```

### 2. Ambiente Virtual

```powershell
# Crie e ative o ambiente virtual
python -m venv venv
.\venv\Scripts\activate

# Instale dependências
pip install -r requirements.txt

# Instale dependências de desenvolvimento
pip install pytest pytest-cov flake8 black isort
```

### 3. Configure o .env

```powershell
Copy-Item .env.example .env
# Edite .env e adicione suas chaves de API (se necessário)
```

### 4. Verifique a Instalação

```powershell
# Execute os testes
pytest tests/ -v

# Execute o linter
flake8 src/ --max-line-length=119

# Execute a aplicação
python run.py
```

---

## 📏 Padrões de Código

### Python Style Guide

Seguimos **PEP 8** com algumas adaptações:

```python
# ✅ BOM
def calcular_queda_tensao(
    corrente: float,
    resistividade: float, 
    distancia: float,
    secao: float
) -> float:
    """
    Calcula a queda de tensão em um circuito.
    
    Args:
        corrente: Corrente em amperes
        resistividade: Resistividade do material (Ω.mm²/m)
        distancia: Distância em metros
        secao: Seção do condutor em mm²
        
    Returns:
        Queda de tensão em volts
    """
    resistencia = (resistividade * distancia) / secao
    return corrente * resistencia

# ❌ RUIM
def calc(i,r,d,s):
    """Calcula QT"""
    return i*(r*d)/s
```

### Regras de Formatação

1. **Line Length**: Máximo 119 caracteres
2. **Indentação**: 4 espaços (não tabs)
3. **Encoding**: UTF-8
4. **Imports**: Ordem alfabética, agrupados (stdlib, third-party, local)
5. **Docstrings**: Google style, sempre em inglês ou português
6. **Type Hints**: Obrigatório em funções públicas

### Ferramentas de Formatação

```powershell
# Black (auto-formatador)
black src/ --line-length 119

# isort (organiza imports)
isort src/ --profile black

# flake8 (linter)
flake8 src/ --max-line-length=119 --extend-ignore=E203,W503
```

### Convenções de Nomenclatura

| Tipo | Convenção | Exemplo |
|------|-----------|---------|
| Variáveis | `snake_case` | `corrente_nominal` |
| Funções | `snake_case` | `calcular_momento()` |
| Classes | `PascalCase` | `ElectricalLogic` |
| Constantes | `UPPER_SNAKE` | `FATOR_POTENCIA` |
| Privadas | `_prefixo` | `_validar_entrada()` |

---

## 🔄 Processo de Pull Request

### 1. Crie uma Branch

```powershell
# Sincronize com upstream
git fetch upstream
git checkout main
git merge upstream/main

# Crie uma branch descritiva
git checkout -b feature/nome-da-feature
# ou
git checkout -b fix/descricao-do-bug
```

### 2. Faça Commits Seguindo Conventional Commits

```powershell
# Formato: <tipo>(<escopo>): <descrição>

git commit -m "feat(electrical): adiciona cálculo de impedância"
git commit -m "fix(converter): corrige conversão de coordenadas negativas"
git commit -m "docs(readme): atualiza instruções de instalação"
git commit -m "test(cqt): adiciona testes para classe D"
```

**Tipos válidos**:
- `feat` - Nova funcionalidade
- `fix` - Correção de bug
- `docs` - Documentação
- `style` - Formatação (sem mudança de lógica)
- `refactor` - Refatoração de código
- `test` - Adição/correção de testes
- `chore` - Tarefas de manutenção

### 3. Escreva Testes

```python
# tests/test_meu_modulo.py
import pytest
from src.modules.meu_modulo.logic import MinhaClasse

def test_calculo_basico():
    """Testa cálculo com valores normais."""
    resultado = MinhaClasse.calcular(10, 20)
    assert resultado == 200

def test_valores_invalidos():
    """Testa comportamento com valores inválidos."""
    with pytest.raises(ValueError):
        MinhaClasse.calcular(-1, 0)

def test_edge_cases():
    """Testa casos limites."""
    assert MinhaClasse.calcular(0, 100) == 0
    assert MinhaClasse.calcular(1e6, 1e-6) == pytest.approx(1.0)
```

**Cobertura mínima**: 70% para novos módulos

### 4. Execute Validações

```powershell
# Testes
pytest tests/ -v --cov=src --cov-report=term-missing

# Linter
flake8 src/ --max-line-length=119

# Formatação
black src/ --check --line-length 119
isort src/ --check --profile black
```

### 5. Push e Abra PR

```powershell
git push origin feature/nome-da-feature
```

No GitHub:
1. Clique em "Create Pull Request"
2. Preencha o template fornecido
3. Aguarde review

---

## 🐛 Reportando Bugs

### Antes de Reportar

1. ✅ Verifique se já existe uma issue aberta
2. ✅ Confirme que é um bug (não uma dúvida de uso)
3. ✅ Teste na versão mais recente

### Template de Bug Report

```markdown
**Descrição do Bug**
Descrição clara do problema.

**Como Reproduzir**
1. Vá para '...'
2. Clique em '...'
3. Role até '...'
4. Veja o erro

**Comportamento Esperado**
O que deveria acontecer.

**Screenshots**
Se aplicável, adicione screenshots.

**Ambiente**
- OS: Windows 10/11
- Versão sisPROJETOS: 1.0.0
- Python: 3.12.1

**Logs**
```
Cole logs relevantes aqui
```

**Contexto Adicional**
Qualquer outra informação relevante.
```

---

## ✨ Sugerindo Features

### Antes de Sugerir

1. ✅ Verifique se já foi sugerido
2. ✅ Confirme que se alinha com os objetivos do projeto
3. ✅ Considere a complexidade vs. benefício

### Template de Feature Request

```markdown
**O Problema**
Descrição clara do problema que a feature resolve.

**Solução Proposta**
Como você imagina a implementação.

**Alternativas Consideradas**
Outras abordagens que você pensou.

**Mockups/Exemplos**
Diagramas, código de exemplo, wireframes.

**Impacto**
- Usuários beneficiados: [muitos/alguns/poucos]
- Complexidade: [baixa/média/alta]
- Breaking changes: [sim/não]
```

---

## 👀 Processo de Review

### O Que Avaliamos

1. **Funcionalidade** - O código faz o que propõe?
2. **Testes** - Tem testes adequados?
3. **Documentação** - Está documentado?
4. **Performance** - Há impacto negativo?
5. **Segurança** - Introduz vulnerabilidades?
6. **Compatibilidade** - Quebra código existente?

### Checklist do Reviewer

- [ ] Código segue PEP 8 e padrões do projeto
- [ ] Testes adicionados/atualizados
- [ ] Cobertura mínima atingida (70%)
- [ ] Documentação atualizada
- [ ] CHANGELOG.md atualizado
- [ ] Não introduz breaking changes (ou justificado)
- [ ] Commit messages seguem Conventional Commits

### Tempo de Review

- Bugs críticos: 24-48h
- Features pequenas: 3-5 dias
- Features grandes: 1-2 semanas

**Seja paciente!** Todos somos voluntários.

---

## 📝 Checklist Completo

Antes de submeter seu PR, confirme:

```markdown
- [ ] Li e segui o guia de contribuição
- [ ] Meu código segue os padrões do projeto
- [ ] Executei os linters sem erros
- [ ] Adicionei testes que provam que minha correção/feature funciona
- [ ] Testes novos e existentes passam localmente
- [ ] Adicionei documentação (docstrings, README, etc.)
- [ ] Atualizei o CHANGELOG.md
- [ ] Meus commits seguem Conventional Commits
- [ ] Não há conflitos com a branch main
```

---

## 🎓 Recursos Adicionais

### Documentação
- [ARCHITECTURE.md](ARCHITECTURE.md) - Entenda a arquitetura
- [BUILD.md](BUILD.md) - Como fazer build
- [README.md](README.md) - Visão geral do projeto

### Python
- [PEP 8](https://peps.python.org/pep-0008/) - Style Guide
- [Type Hints](https://docs.python.org/3/library/typing.html) - Type annotations
- [pytest](https://docs.pytest.org/) - Testing framework

### Git
- [Conventional Commits](https://www.conventionalcommits.org/)
- [GitHub Flow](https://guides.github.com/introduction/flow/)

---

## 🏆 Reconhecimento

Contribuidores serão adicionados ao arquivo AUTHORS.md e mencionados nos release notes.

Top contributors ganham badge especial no README! ⭐

---

## ❓ Dúvidas?

- 💬 Abra uma [Discussion](https://github.com/jrlampa/sisPROJETOS_v1.1/discussions)
- 📧 Envie email para: contato@exemplo.com.br
- 🐛 Para bugs, abra uma [Issue](https://github.com/jrlampa/sisPROJETOS_v1.1/issues)

---

<div align="center">

**Obrigado por contribuir! 🎉**

</div>
