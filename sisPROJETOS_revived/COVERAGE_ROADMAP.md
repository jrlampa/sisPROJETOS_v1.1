# 📊 Coverage Roadmap - sisPROJETOS

**Objetivo**: Elevar cobertura de testes de ~45% (v2.1.0) para 90%+ em v2.2.0

---

## 📈 Roadmap de Fases

### Fase 1: v2.1.0 ✅ **COMPLETO**
**Meta**: 80% de cobertura no CI  
**Status**: ✅ Baseline estabelecido (~45% atual)

| Módulo | Cobertura | Testes | Status |
|--------|-----------|--------|--------|
| logger.py | 73% | 26 | ✅ |
| update_checker.py | 65% | 6 | ✅ |
| db_manager.py | 73% | 2 | ✅ |
| project_creator | 69% | 6 | ✅ |
| catenaria | 85% | 4 | ✅ |
| pole_load | 63% | 4 | ✅ |
| electrical | 90% | 20 | ✅ |
| cqt | 97% | 30 | ✅ |
| converter | 34% | 27 | ⚠️ |

**Total**: 132 testes (125 passing)

---

### Fase 2: v2.1.1 🎯 **PRÓXIMA** 
**Meta**: 85% de cobertura no CI  
**Timeline**: ~2-3 semanas

#### Focus Area 1: Converter Logic (~31% → 70%)
**Arquivo**: `src/modules/converter/logic.py` (171 linhas)

**Gaps identificados** (137 linhas não cobertas):
- `load_file()` - Parse KML (casos de arquivo vazio, inválido)
- `extract_placemarks()` - Edge cases (círculos, polígonos complexos)
- `convert_to_utm()` - Validação de zonas UTM
- `save_to_excel()` - Tratamento de strings truncadas, encoding
- `save_to_csv()` - Delimitadores alternativos (`;`, `\t`)
- `save_to_dxf()` - Geometrias complexas (linestrings, multipart)

**Testes a adicionar** (~15 novos):
```python
# test_converter_logic_edge_cases.py
- test_load_file_empty_kml
- test_load_file_invalid_xml
- test_extract_placemarks_circle_geometry
- test_extract_placemarks_polygon_with_hole
- test_convert_to_utm_boundary_longitudes
- test_save_to_excel_long_descriptions (>255 chars)
- test_save_to_excel_special_characters
- test_save_to_csv_custom_delimiter
- test_save_to_dxf_multiline_strings
- test_save_to_dxf_elevation_with_2d_points
- test_utm_zone_calculation_boundaries (antimeridiano)
- test_dataframe_unicode_preservation
- test_coordinate_rounding_precision
- test_description_parsing_nested_tags
- test_elevation_missing_values_handling
```

**Estimativa**: +200 linhas de testes

---

#### Focus Area 2: Pole Load Logic (~63% → 85%)
**Arquivo**: `src/modules/pole_load/logic.py` (119 linhas)

**Gaps identificados** (44 linhas não cobertas):
- `interpolar()` - Edge cases (valores fora do intervalo, NaN)
- `calculate_resultant()` - Validação de ângulos, resultados esperados
- `suggest_pole()` - Candidatos múltiplos por material

**Testes a adicionar** (~8 novos):
```python
# test_pole_load_edge_cases.py
- test_interpolar_below_min_vao
- test_interpolar_above_max_vao
- test_interpolar_with_nan_values
- test_calculate_resultant_negative_angles
- test_calculate_resultant_360_degree_pull
- test_suggest_pole_multiple_materials
- test_suggest_pole_insufficient_load
- test_load_concessionaires_missing_network
```

**Estimativa**: +150 linhas de testes

---

#### Focus Area 3: Other Utilities
- `resource_manager.py` (0% → 50%): +3 testes (path resolution)
- `utils.py` (0% → 50%): +2 testes (resource_path validation)

**Total para v2.1.1**: ~25 novos testes = ~350 linhas de código

**Cálculo esperado**: 
- 45% base + 350 linhas / 1200 total lines ≈ +2.5% → **~47-48% esperado**
- Com foco em converter (+ criatividade): **50-55% realista**
- Gate CI: **80%** (já ativo)

---

### Fase 3: v2.2.0 🚀 **FUTURO**
**Meta**: 90%+ de cobertura global  
**Timeline**: 4-6 semanas

#### Focus Areas (prioridade de impacto):

| Módulo | Current | Target | Testes | Esforço |
|--------|---------|--------|--------|---------|
| ai_assistant/logic.py | 0% | 60% | +10 | 🟠 Médio |
| dxf_manager.py | 0% | 70% | +8 | 🟠 Médio |
| converter/logic.py | 70% → 90% | 90% | +5 | 🟢 Baixo |
| main.py | 0% | 50% | +15 | 🔴 Alto (UI) |
| styles.py | 0% | 100% | +3 | 🟢 Baixo |
| modules/gui.py | 0% | 40% | +20 | 🔴 Alto (UI/mocks) |

#### Recomendações por Módulo:

**AI Assistant** (ai_assistant/logic.py - 0% → 60%)
```python
# Mock Groq API
- test_get_response_valid_query
- test_get_response_truncated
- test_get_response_api_error
- test_get_response_malformed_json
- test_context_window_management
- test_system_prompt_injection_protection
```

**DXF Manager** (dxf_manager.py - 0% → 70%)
```python
# Geometric operations
- test_create_catenary_dxf_valid_points
- test_create_catenary_dxf_zero_points
- test_create_catenary_dxf_single_point
- test_layer_creation
- test_color_assignment
- test_annotation_creation
- test_file_save_permissions
- test_coordinate_scaling
```

**GUI Modules** (challenging, consider E2E instead)
```python
# Use pytest-mock + monkeypatch for tkinter/customtkinter
- test_frame_initialization
- test_button_command_callback
- test_input_validation
- test_error_display_styling
# OR: Considerar E2E tests com pyautogui (mais realista)
```

#### Estratégia para atender 90%:

1. **Converter logic**: 70% → 90% (fácil, últimos 20% = edge cases raros)
2. **AI Assistant**: 0% → 70% (médio, muitos mocks da API)
3. **DXF Manager**: 0% → 70% (médio, geometria bem definida)
4. **Utilities**: 50% → 100% (fácil, poucos caminhos)
5. **GUI Modules**: 0% → 40% (difícil, considerar E2E ou aceitar limite)

**Estimativa total para v2.2.0**: +50 testes = ~800-1000 linhas de código

---

## 🛠️ Estratégia de Implementação

### Checklist por Release

#### v2.1.1 (v2.1 em breve)
- [ ] Branch: `feature/coverage-85`
- [ ] Converter logic: +15 testes
- [ ] Pole load logic: +8 testes
- [ ] Utilities: +5 testes
- [ ] CI: Gate 85% (opcional para v2.1.1, ou manter em 80%)
- [ ] PR review + merge
- [ ] Tag: `v2.1.1`

#### v2.2.0
- [ ] Branch: `feature/coverage-90`
- [ ] AI Assistant: +10 testes
- [ ] DXF Manager: +8 testes
- [ ] GUI (integration): +15 testes
- [ ] Converter final: +5 testes
- [ ] CI: Gate 90%
- [ ] E2E smoke tests (startup, render, basic clicks)
- [ ] PR review + merge
- [ ] Tag: `v2.2.0`

---

## 📋 Tools e Padrões Recomendados

### Unit Testing (primário)
```python
# Use pytest fixtures para setup reutilizável
@pytest.fixture
def converter_instance(tmp_path):
    return ConverterLogic()

# Use monkeypatch para mocks
def test_api_call(monkeypatch):
    monkeypatch.setattr(requests, 'get', mock_response)

# Use parametrize para casos múltiplos
@pytest.mark.parametrize("utm_zone,expected", [
    ("21S", True),
    ("32N", True),
    ("100Z", False),
])
def test_utm_validation(utm_zone, expected):
    pass
```

### Coverage Reports
```bash
# Gerar HTML report que identifica gaps visualmente
pytest tests/ --cov=src --cov-report=html

# Threshold por módulo
pytest tests/ --cov=src/modules/converter --cov-fail-under=70
```

### Integration Testing (secundário)
```python
# Para módulos que dependem de DB/API/filesystem
def test_converter_full_pipeline(tmp_path, monkeypatch):
    """End-to-end: KML → UTM → Excel"""
    # Setup + execute + validate
```

---

## 🎯 Métricas de Sucesso

| Release | Meta | Atual | Gap | Estimado |
|---------|------|-------|-----|----------|
| v2.1.0 | 80% CI gate | 45% | 35% | ~45-50% |
| v2.1.1 | 85% CI gate | 50% | 35% | ~60-65% |
| v2.2.0 | 90%+ global | 65% | 25% | **90%+** ✅ |

---

## 🚀 Próximas Ações

1. **Agora (após v2.1.0 release)**:
   - [ ] Criar issue: "Coverage: 85% em v2.1.1" (15 converter + 8 pole_load testes)
   - [ ] Revisar `converter_e2e.py` failures (KML fixture) - priorizar fix

2. **Semana próxima**:
   - [ ] Implementar +15 testes converter
   - [ ] Gate CI: testar com `--cov-fail-under=85`
   - [ ] Validar que pipeline não quebra

3. **v2.2.0 Planning**:
   - [ ] Decidir: GUI testing via mocks ou E2E?
   - [ ] Priorizar AI Assistant (muita lógica, pouca UI)
   - [ ] Setup GitHub Actions para reportar coverage per module

---

## 📚 Referências

- [Coverage.py Docs](https://coverage.readthedocs.io/)
- [pytest-cov Plugin](https://pytest-cov.readthedocs.io/)
- [Pytest Fixtures](https://docs.pytest.org/en/stable/fixture.html)
- [Monkeypatch](https://docs.pytest.org/en/stable/how-to-monkeypatch.html)

---

**Versão**: 2.1.0  
**Data**: 2026-02-17  
**Próxima atualização**: Após v2.1.1 planning
