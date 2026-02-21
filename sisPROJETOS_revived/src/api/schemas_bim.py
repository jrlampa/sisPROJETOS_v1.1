"""
Schemas Pydantic para endpoints BIM da API REST do sisPROJETOS.

Contém modelos de entrada/saída para:
- Conversor KML/KMZ → UTM (geoespacial)
- Conversor UTM → DXF (CAD 2.5D)
- Criador de Projetos (estrutura de pastas)

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
