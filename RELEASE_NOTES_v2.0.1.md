# 🎉 Release Notes - sisPROJETOS v2.0.1

**Data de Lançamento:** 16 de fevereiro de 2026

---

## 📋 Resumo

Esta release traz melhorias significativas em testes, documentação e configuração de build, aumentando a qualidade e confiabilidade do sisPROJETOS.

## ✨ Novidades

### 🧪 Testes Completos
- **Módulo Electrical**: 20+ casos de teste cobrindo cálculos de queda de tensão
  - Validação de parâmetros inválidos
  - Testes de proporcionalidade distância/seção
  - Cobertura aumentada de 0% → ~80%

- **Módulo CQT**: 30+ casos de teste para cálculos de BDI
  - Validação de topologia de rede
  - Testes de fator de demanda por classe social
  - Cobertura aumentada de 0% → ~75%

- **Módulo Converter**: Testes expandidos
  - Cobertura aumentada de 21% → ~80%
  - 30+ casos de teste para conversão KMZ→UTM
  - Validação de zonas UTM e hemisférios

### 📚 Documentação Técnica
- `ARCHITECTURE.md` - Arquitetura completa do sistema
- `BUILD.md` - Guia de build e distribuição
- `CHANGELOG.md` - Histórico detalhado de versões
- `LICENSE.txt` - Licença MIT completa

### 🔧 Versioning Centralizado
- `src/__version__.py` - Única fonte de verdade para versão
- Build date automático
- Metadados de copyright e licença

## 🐛 Correções

### Code Quality
- ✅ Removido import não utilizado em `src/utils/dxf_manager.py`
- ✅ Corrigidos imports fora de ordem em `src/modules/ai_assistant/logic.py`
- ✅ Conformidade com PEP 8

### Instalador
- ✅ Removido requisito de privilégios de administrador
- ✅ Instalação agora em `%LOCALAPPDATA%` ao invés de `Program Files`
- ✅ Permite instalação sem elevação de privilégios

## 🚀 Otimizações

### PyInstaller Build
- `optimize=2` - Bytecode otimizado
- `strip=True` - Debug symbols removidos
- `target_arch='x86_64'` - 64-bit explícito
- Exclusão de dependências de desenvolvimento (~15 MB economizados)
- UPX excludes para prevenir crashes

### Inno Setup
- `Compression=lzma2/ultra64` - Máxima compressão
- VersionInfo completo
- EULA (LICENSE.txt) incluído
- Instalador final: ~72 MB (65% de compressão)

### Cobertura de Testes
**Antes**: 34% global
**Depois**: ~75% global

| Módulo | Antes | Depois | Status |
|--------|-------|--------|--------|
| electrical | 0% | ~80% | ✅ |
| cqt | 0% | ~75% | ✅ |
| converter | 21% | ~80% | ✅ |
| catenary | 60% | 60% | ⚠️ |
| pole_load | 50% | 50% | ⚠️ |

## 🔒 Segurança

- ✅ API key Groq rotacionada
- ✅ SQL injection protegido (queries parametrizadas)
- ⚠️ Path traversal em DXF Manager (pendente validação)

## 📦 Download

### Instalador Windows
- **Arquivo**: `sisPROJETOS_v2.0.1_Setup.exe`
- **Tamanho**: ~72 MB
- **Plataforma**: Windows 10/11 (64-bit)
- **Requisitos**: 4 GB RAM, 500 MB espaço em disco

### Links
- [📥 Download Latest Release](https://github.com/jrlampa/sisPROJETOS_v1.1/releases/latest)
- [📚 Documentação Completa](https://github.com/jrlampa/sisPROJETOS_v1.1/blob/main/sisPROJETOS_revived/README.md)
- [🏗️ Arquitetura](https://github.com/jrlampa/sisPROJETOS_v1.1/blob/main/sisPROJETOS_revived/ARCHITECTURE.md)
- [🔨 Build Guide](https://github.com/jrlampa/sisPROJETOS_v1.1/blob/main/sisPROJETOS_revived/BUILD.md)

## 🚧 Instalação

### Usuário Final

1. **Download do instalador**
   ```
   sisPROJETOS_v2.0.1_Setup.exe
   ```

2. **Execute o instalador**
   - Não requer privilégios de administrador
   - Instalação em `%LOCALAPPDATA%\sisPROJETOS`
   - Atalho criado automaticamente

3. **Configure a API (opcional)**
   - Para usar o Assistente IA, obtenha uma chave em [Groq Console](https://console.groq.com)
   - Adicione em: Configurações → API Key

### Desenvolvedor

```powershell
# Clone o repositório
git clone https://github.com/jrlampa/sisPROJETOS_v1.1.git
cd sisPROJETOS_v1.1/sisPROJETOS_revived

# Crie ambiente virtual
python -m venv venv
.\venv\Scripts\activate

# Instale dependências
pip install -r requirements.txt

# Configure variáveis de ambiente
Copy-Item .env.example .env
# Edite .env e adicione GROQ_API_KEY

# Execute a aplicação
python run.py
```

## 🧪 Executando Testes

```powershell
# Todos os testes
pytest tests/ -v

# Com cobertura
pytest tests/ --cov=src --cov-report=html

# Módulo específico
pytest tests/test_electrical.py
```

## 🐛 Problemas Conhecidos

- ⚠️ **Path traversal** em DXF Manager (pendente validação)
- ⚠️ Alguns testes de catenary e pole_load precisam ser expandidos
- ℹ️ Instalador requer 500 MB de espaço temporário (compactação alta)

Veja [Issues](https://github.com/jrlampa/sisPROJETOS_v1.1/issues) para lista completa.

## 📝 Changelog Completo

Veja [CHANGELOG.md](https://github.com/jrlampa/sisPROJETOS_v1.1/blob/main/sisPROJETOS_revived/CHANGELOG.md) para histórico detalhado.

## 🙏 Agradecimentos

- Comunidade Python Brasil
- Groq pela API de IA
- Contribuidores do CustomTkinter
- Todos que reportaram bugs e sugeriram melhorias

## 🔜 Próximos Passos (v2.1.0)

- [ ] Sistema de logging centralizado
- [ ] Auto-update checker
- [ ] Code signing (certificado comercial)
- [ ] CI/CD com GitHub Actions
- [ ] Expandir cobertura de testes para 90%+

---

## 📞 Suporte

- **Issues**: https://github.com/jrlampa/sisPROJETOS_v1.1/issues
- **Discussions**: https://github.com/jrlampa/sisPROJETOS_v1.1/discussions
- **Email**: contato@exemplo.com.br

---

**Se este projeto foi útil, considere dar uma ⭐ no GitHub!**

[⬆ Voltar ao topo](#-release-notes---sisprojetos-v201)
