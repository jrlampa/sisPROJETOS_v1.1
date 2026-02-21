# 📐 Conversor KMZ/KML → DXF/CSV/XLSX

## Visão Geral

O módulo conversor do sisPROJETOS permite converter arquivos do Google Earth (KMZ/KML) para formatos utilizados em projetos de engenharia elétrica:

- **XLSX** - Excel para análise e planilhas
- **CSV** - Formato universal compatível com Excel BR (separador `;`)
- **DXF** - AutoCAD para desenhos técnicos

## ✅ Funcionalidades Verificadas

### 1. Carregamento de Arquivos
- ✅ Suporte a arquivos `.kml` e `.kmz`
- ✅ Extração recursiva de placemarks em Documents e Folders
- ✅ Tratamento de geometrias: Point, LineString e Polygon

### 2. Conversão de Coordenadas
- ✅ Conversão automática WGS84 (lat/lon) → UTM
- ✅ Detecção automática de zona UTM
- ✅ Detecção de hemisfério (Norte/Sul)
- ✅ Preservação de elevação (coordenada Z)
- ✅ Precisão de 3 casas decimais

### 3. Exportação XLSX (Excel)
- ✅ Formato nativo Excel (.xlsx)
- ✅ Todas as colunas preservadas
- ✅ Compatível com Microsoft Excel e LibreOffice

### 4. Exportação CSV
- ✅ Separador: `;` (ponto e vírgula) - padrão brasileiro
- ✅ Encoding: UTF-8 com BOM (compatível com Excel)
- ✅ Ordem lógica de colunas
- ✅ Headers em português

### 5. Exportação DXF (AutoCAD)
- ✅ Formato: AutoCAD R2010
- ✅ Pontos → Layer "POINTS" com texto de identificação
- ✅ Linhas → Layer "LINES" com polyline 3D
- ✅ Coordenadas em metros (UTM)

## 📊 Estrutura dos Dados

### Colunas do DataFrame/CSV/XLSX:
1. **Name** - Nome do placemark
2. **Description** - Descrição do placemark
3. **Type** - Tipo de geometria (Point, LineString, Polygon)
4. **Longitude** - Coordenada longitude (WGS84)
5. **Latitude** - Coordenada latitude (WGS84)
6. **Easting** - Coordenada Este (UTM, metros)
7. **Northing** - Coordenada Norte (UTM, metros)
8. **Zone** - Zona UTM
9. **Hemisphere** - Hemisfério (N ou S)
10. **Elevation** - Elevação em metros

### Exemplo de Dados:
```
Name;Description;Type;Longitude;Latitude;Easting;Northing;Elevation;Zone;Hemisphere
Poste 1;Poste de concreto;Point;-46.6333;-23.5505;333287.915;7394588.319;720.0;23;S
Poste 2;Poste de madeira;Point;-46.6300;-23.5500;333624.181;7394647.522;725.0;23;S
```

## 🧪 Testes

### Testes Unitários
- **Total**: 31 testes
- **Status**: 31/31 passando (100%)
- **Cobertura**: Funções de conversão, validação e exportação

### Teste End-to-End
Arquivo de teste: `/tmp/test_v012.kml`
- ✅ Carregamento de 3 placemarks (2 pontos + 1 linha)
- ✅ Conversão para UTM (5 linhas no DataFrame)
- ✅ Exportação XLSX (5277 bytes)
- ✅ Exportação CSV (554 bytes)
- ✅ Exportação DXF (16461 bytes)

## 🔧 Dependências

```
fastkml<1.0    # Versão 0.x para compatibilidade de API
pyproj         # Transformação de coordenadas
pandas         # Manipulação de dados
openpyxl       # Exportação Excel
ezdxf          # Exportação DXF
shapely        # Geometrias
```

## 🐛 Correções Aplicadas

### Problema Identificado
O código original foi desenvolvido para `fastkml 1.x`, onde `features` é uma propriedade. A versão `fastkml 1.4` mudou a API mas apresenta problemas de parsing.

### Solução Implementada
Compatibilidade com ambas as versões do fastkml:

```python
# Compatible with both fastkml 0.x (method) and 1.x (property)
features = k.features() if callable(k.features) else k.features
```

Aplicado em 2 locais:
1. `load_file()` - linha 51-52
2. `_extract_placemarks()` - linha 87-88

### Versão Recomendada
`fastkml<1.0` (versão 0.12) - parsing estável e API consistente

## 📖 Uso

```python
from modules.converter.logic import ConverterLogic

# Inicializar conversor
converter = ConverterLogic()

# Carregar arquivo KML/KMZ
placemarks = converter.load_file("meu_projeto.kml")

# Converter para UTM
df = converter.convert_to_utm(placemarks)

# Exportar para diferentes formatos
converter.save_to_excel(df, "saida.xlsx")
converter.save_to_csv(df, "saida.csv")
converter.save_to_dxf(df, "saida.dxf")
```

## ✅ Status: VERIFICADO E FUNCIONANDO

Todas as funcionalidades de conversão KMZ/KML → DXF/CSV/XLSX foram testadas e estão funcionando corretamente.

**Data da Verificação**: 2026-02-17  
**Testes**: 31/31 passando  
**Teste E2E**: ✅ Completo e bem-sucedido
