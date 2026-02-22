"""
Schemas Pydantic para endpoints BIM da API REST do sisPROJETOS.

Contém modelos de entrada/saída para:
- Conversor KML/KMZ → UTM (geoespacial)
- Conversor UTM → DXF (CAD 2.5D)
- Criador de Projetos (estrutura de pastas)
- Folgas mínimas NBR 5422 / PRODIST Módulo 6 (referência catenária)
- Cálculo em lote de catenárias (batch multi-vão)

Importado e re-exportado por ``api.schemas`` para manter compatibilidade
com todos os arquivos de rota existentes.
"""

from typing import List, Optional

from pydantic import BaseModel, Field

# ── Conversor KML/KMZ (BIM) ──────────────────────────────────────────────────


class KmlConvertRequest(BaseModel):
    """Dados de entrada para conversão KML → UTM via API.

    O conteúdo KML deve ser enviado como string Base64 (RFC 4648).
    Tanto arquivos .kml quanto o conteúdo interno de .kmz são aceitos.
    """

    kml_base64: str = Field(
        ...,
        description="Conteúdo do arquivo KML codificado em Base64 (RFC 4648)",
        min_length=1,
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "kml_base64": "PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiPz4K...",
            }
        }
    }


class KmlPointOut(BaseModel):
    """Coordenadas UTM de um ponto extraído do KML."""

    name: str = Field(..., description="Nome do placemark")
    description: str = Field(default="", description="Descrição do placemark")
    type: str = Field(..., description="Tipo de geometria (Point, LineString, Polygon)")
    longitude: float = Field(..., description="Longitude WGS84 em graus decimais")
    latitude: float = Field(..., description="Latitude WGS84 em graus decimais")
    easting: float = Field(..., description="Coordenada Leste UTM em metros")
    northing: float = Field(..., description="Coordenada Norte UTM em metros")
    zone: int = Field(..., description="Zona UTM (1–60)")
    hemisphere: str = Field(..., description="Hemisfério (N ou S)")
    elevation: float = Field(default=0.0, description="Altitude em metros (0 se ausente)")


class KmlConvertResponse(BaseModel):
    """Resposta da conversão KML → UTM."""

    count: int = Field(..., description="Número de pontos convertidos")
    points: List[KmlPointOut] = Field(..., description="Lista de pontos com coordenadas UTM")


# ── Conversor UTM → DXF (BIM) ─────────────────────────────────────────────────


class UTMPointIn(BaseModel):
    """Ponto UTM para conversão a DXF."""

    name: str = Field(..., min_length=1, description="Identificador do ponto (ex: 'P1', 'TRAFO')")
    easting: float = Field(..., description="Coordenada Leste UTM em metros")
    northing: float = Field(..., description="Coordenada Norte UTM em metros")
    elevation: float = Field(default=0.0, description="Altitude em metros (0 se não disponível)")


class UTMToDxfRequest(BaseModel):
    """Dados de entrada para geração de DXF a partir de pontos UTM via API."""

    points: List[UTMPointIn] = Field(..., min_length=1, description="Lista de pontos UTM")
    filename: str = Field(
        default="pontos.dxf",
        min_length=1,
        max_length=100,
        description="Nome sugerido para o arquivo DXF (ex: 'pontos_levantamento.dxf')",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "points": [
                    {"name": "P1", "easting": 788547.0, "northing": 7634925.0, "elevation": 720.0},
                    {"name": "P2", "easting": 714315.7, "northing": 7549084.2, "elevation": 580.0},
                ],
                "filename": "levantamento_topografico.dxf",
            }
        }
    }


class UTMToDxfResponse(BaseModel):
    """DXF gerado a partir de pontos UTM, codificado em Base64 para integração BIM."""

    dxf_base64: str = Field(..., description="Conteúdo do arquivo DXF codificado em Base64 (RFC 4648)")
    filename: str = Field(..., description="Nome sugerido para o arquivo DXF")
    count: int = Field(..., description="Número de pontos incluídos no DXF")


# ── Criador de Projetos ───────────────────────────────────────────────────────


class ProjectCreateRequest(BaseModel):
    """Dados de entrada para criação de estrutura de projeto."""

    project_name: str = Field(..., min_length=1, max_length=100, description="Nome do projeto (pasta raiz)")
    base_path: str = Field(..., min_length=1, description="Diretório pai onde a estrutura será criada")

    model_config = {
        "json_schema_extra": {
            "example": {
                "project_name": "LT_230kV_SP_CAMPINAS",
                "base_path": "/projetos/2026",
            }
        }
    }


class ProjectCreateResponse(BaseModel):
    """Resposta da operação de criação de projeto."""

    success: bool = Field(..., description="True se a estrutura foi criada com sucesso")
    message: str = Field(..., description="Mensagem descritiva do resultado")
    project_path: Optional[str] = Field(default=None, description="Caminho completo do projeto criado")


class ProjectListResponse(BaseModel):
    """Resposta da listagem de projetos em um diretório base."""

    base_path: str = Field(..., description="Diretório base pesquisado")
    projects: List[str] = Field(..., description="Nomes dos diretórios de projeto encontrados")
    count: int = Field(..., description="Número de projetos encontrados")


# ── Folgas Mínimas NBR 5422 / PRODIST (Catenária) ────────────────────────────


class ClearanceTypeOut(BaseModel):
    """Folga mínima ao solo por tipo de rede elétrica (NBR 5422 / PRODIST Módulo 6)."""

    network_type: str = Field(..., description="Código do tipo de rede (ex: 'BT_URBANA')")
    description: str = Field(..., description="Descrição legível do tipo de rede")
    min_clearance_m: float = Field(..., description="Folga mínima ao solo em metros")
    standard_ref: str = Field(..., description="Referência normativa aplicável")


class ClearancesResponse(BaseModel):
    """Tabela de folgas mínimas ao solo por tipo de rede (NBR 5422 / PRODIST Módulo 6).

    Use ``min_clearance_m`` do item correspondente como valor para o campo
    ``min_clearance_m`` no endpoint POST /api/v1/catenary/calculate.
    """

    clearances: List[ClearanceTypeOut] = Field(..., description="Lista de folgas por tipo de rede")
    count: int = Field(..., description="Número de tipos de rede listados")
    note: str = Field(
        default=(
            "Distâncias mínimas de segurança conforme NBR 5422 Tabela 6 e PRODIST Módulo 6. "
            "Aplique a norma da concessionária quando disponível (prevalece sobre ABNT)."
        ),
        description="Nota sobre hierarquia normativa",
    )


# ── Catenária em Lote (Batch) ─────────────────────────────────────────────────


class CatenaryBatchItem(BaseModel):
    """Parâmetros de um vão individual para cálculo de catenária em lote.

    Todos os campos seguem as mesmas regras do endpoint POST /api/v1/catenary/calculate.
    O campo ``label`` é opcional e serve apenas para identificação do item na resposta.
    """

    label: Optional[str] = Field(
        default=None,
        max_length=80,
        description="Rótulo opcional para identificar o vão na resposta (ex: 'Vão P1-P2')",
    )
    span: float = Field(..., gt=0, description="Comprimento do vão em metros (> 0)")
    tension_daN: float = Field(..., gt=0, description="Tensão mecânica horizontal do condutor em daN (> 0)")
    ha: float = Field(..., description="Altura do ponto de fixação A em metros (suporte inicial)")
    hb: float = Field(..., description="Altura do ponto de fixação B em metros (suporte final)")
    weight_kg_m: float = Field(
        ...,
        ge=0,
        description=(
            "Peso linear do condutor em kg/m (≥ 0). "
            "Valor 0 é aceito e resulta em success=False para o item sem abortar os demais vãos do lote."
        ),
    )
    min_clearance_m: Optional[float] = Field(
        default=None,
        gt=0,
        description="Folga mínima ao solo para verificação NBR 5422 (opcional)",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "label": "Vão P1-P2",
                "span": 100.0,
                "tension_daN": 2000.0,
                "ha": 10.0,
                "hb": 10.0,
                "weight_kg_m": 1.6,
                "min_clearance_m": 6.0,
            }
        }
    }


class CatenaryBatchResponseItem(BaseModel):
    """Resultado do cálculo de catenária para um vão individual."""

    index: int = Field(..., description="Índice do item (base 0) na lista de entrada")
    label: Optional[str] = Field(default=None, description="Rótulo fornecido na entrada")
    success: bool = Field(..., description="True se o cálculo foi concluído com sucesso")
    error: Optional[str] = Field(default=None, description="Mensagem de erro caso success=False")
    sag: Optional[float] = Field(default=None, description="Flecha máxima em metros")
    tension: Optional[float] = Field(default=None, description="Tensão mecânica em daN")
    catenary_constant: Optional[float] = Field(default=None, description="Constante de catenária (a = T/w)")
    within_clearance: Optional[bool] = Field(
        default=None,
        description="Resultado da verificação de folga mínima NBR 5422 (None se não solicitado)",
    )


class CatenaryBatchRequest(BaseModel):
    """Dados de entrada para cálculo de catenária em lote (múltiplos vãos).

    Permite calcular sag/tensão/constante para até 20 vãos em uma única chamada,
    evitando N chamadas ao endpoint POST /api/v1/catenary/calculate.
    Ideal para integração BIM com múltiplos vãos de uma linha de distribuição.
    """

    items: List[CatenaryBatchItem] = Field(..., min_length=1, max_length=20, description="Lista de vãos (1–20)")

    model_config = {
        "json_schema_extra": {
            "example": {
                "items": [
                    {
                        "label": "Vão P1-P2",
                        "span": 100.0,
                        "tension_daN": 2000.0,
                        "ha": 10.0,
                        "hb": 10.0,
                        "weight_kg_m": 1.6,
                        "min_clearance_m": 6.0,
                    },
                    {
                        "label": "Vão P2-P3",
                        "span": 500.0,
                        "tension_daN": 2000.0,
                        "ha": 10.0,
                        "hb": 12.0,
                        "weight_kg_m": 1.6,
                    },
                    {
                        "label": "Vão P3-P4",
                        "span": 1000.0,
                        "tension_daN": 2000.0,
                        "ha": 12.0,
                        "hb": 12.0,
                        "weight_kg_m": 1.6,
                        "min_clearance_m": 5.5,
                    },
                ]
            }
        }
    }


class CatenaryBatchResponse(BaseModel):
    """Resposta do cálculo de catenária em lote."""

    count: int = Field(..., description="Número de vãos processados")
    success_count: int = Field(..., description="Número de vãos calculados com sucesso")
    error_count: int = Field(..., description="Número de vãos com erro de cálculo")
    items: List[CatenaryBatchResponseItem] = Field(..., description="Resultados individuais por vão")
