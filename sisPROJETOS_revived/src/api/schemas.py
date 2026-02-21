"""
Schemas Pydantic para a API REST do sisPROJETOS.

Define modelos de entrada e saída para cada endpoint,
garantindo validação automática e documentação OpenAPI.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

# ── Infraestrutura ────────────────────────────────────────────────────────────


class HealthResponse(BaseModel):
    """Resposta do endpoint de saúde da API."""

    status: str = Field(..., description="Status geral: 'ok' ou 'degraded'")
    version: str = Field(..., description="Versão da aplicação")
    db_status: str = Field(..., description="Status do banco de dados: 'ok' ou 'error'")
    environment: str = Field(..., description="Ambiente de execução: 'development' ou 'production'")
    timestamp: str = Field(..., description="Timestamp UTC da verificação em formato ISO 8601")


# ── Elétrico ─────────────────────────────────────────────────────────────────


class MaterialOut(BaseModel):
    """Dados de um material condutor com sua resistividade."""

    name: str = Field(..., description="Nome do material (ex: Alumínio, Cobre)")
    resistivity_ohm_mm2_m: float = Field(..., description="Resistividade em Ω·mm²/m a 20°C (NBR 5410)")
    description: str = Field(default="", description="Descrição técnica do material")


class VoltageDropRequest(BaseModel):
    """Dados de entrada para cálculo de queda de tensão (NBR 5410 / ANEEL PRODIST)."""

    power_kw: float = Field(..., gt=0, description="Potência ativa em kW")
    distance_m: float = Field(..., gt=0, description="Comprimento do trecho em metros")
    voltage_v: float = Field(..., gt=0, description="Tensão de fornecimento em V")
    material: str = Field(default="Alumínio", description="Material do condutor (Alumínio, Cobre)")
    section_mm2: float = Field(..., gt=0, description="Seção transversal do condutor em mm²")
    cos_phi: float = Field(default=0.92, gt=0, le=1, description="Fator de potência cos φ")
    phases: int = Field(default=3, description="Número de fases (1 ou 3)")
    standard_name: Optional[str] = Field(
        default=None,
        description=(
            "Nome do padrão normativo a aplicar. Se omitido, usa 'NBR 5410' (limite 5%). "
            "Use GET /api/v1/electrical/standards para listar os disponíveis. "
            "Quando uma norma de concessionária é aplicada, ABNT NBR 5410 é ignorada "
            "e a resposta inclui o toast explicativo em pt-BR (ANEEL/PRODIST Módulo 8)."
        ),
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "power_kw": 50.0,
                "distance_m": 200.0,
                "voltage_v": 220.0,
                "material": "Alumínio",
                "section_mm2": 35.0,
                "cos_phi": 0.92,
                "phases": 3,
                "standard_name": "PRODIST Módulo 8 — BT",
            }
        }
    }


class VoltageDropResponse(BaseModel):
    """Resultado do cálculo de queda de tensão com padrão normativo aplicado."""

    current: float = Field(..., description="Corrente calculada em Ampères")
    delta_v_volts: float = Field(..., description="Queda de tensão em Volts")
    percentage_drop: float = Field(..., description="Queda de tensão percentual (%)")
    allowed: bool = Field(..., description="True se dentro do limite do padrão normativo aplicado")
    standard_name: str = Field(..., description="Padrão normativo aplicado (ex: 'NBR 5410')")
    override_toast: Optional[str] = Field(
        default=None,
        description=(
            "Mensagem de aviso em pt-BR quando norma de concessionária ou ANEEL/PRODIST "
            "sobrepõe a ABNT NBR 5410. Exibir como toast na interface."
        ),
    )


# ── Padrões Normativos ────────────────────────────────────────────────────────


class StandardOut(BaseModel):
    """Dados de um padrão regulatório de queda de tensão."""

    name: str = Field(..., description="Nome do padrão (ex: 'NBR 5410', 'PRODIST Módulo 8 — BT')")
    source: str = Field(..., description="Origem normativa (ABNT, ANEEL/PRODIST, CONCESSIONAIRE)")
    max_drop_percent: float = Field(..., description="Limite máximo de queda de tensão em %")
    overrides_abnt: bool = Field(..., description="True quando este padrão substitui a ABNT NBR 5410")
    override_toast_pt_br: Optional[str] = Field(
        default=None,
        description="Mensagem toast em pt-BR a exibir quando ABNT é ignorada (null se não sobrepõe)",
    )


# ── CQT ───────────────────────────────────────────────────────────────────────


class CQTSegment(BaseModel):
    """Trecho de rede para cálculo CQT."""

    ponto: str = Field(..., description="Identificador do ponto (ex: 'P1', 'TRAFO')")
    montante: str = Field(default="", description="Ponto montante (vazio para TRAFO)")
    metros: float = Field(default=0.0, ge=0, description="Comprimento do trecho em metros")
    cabo: str = Field(default="", description="Tipo de cabo (ex: '3x35+54.6mm² Al')")
    mono: int = Field(default=0, ge=0, description="Unidades consumidoras monofásicas")
    bi: int = Field(default=0, ge=0, description="Unidades consumidoras bifásicas")
    tri: int = Field(default=0, ge=0, description="Unidades consumidoras trifásicas")
    tri_esp: int = Field(default=0, ge=0, description="UCs trifásicas especiais")
    carga_esp: float = Field(default=0.0, ge=0, description="Carga pontual especial em kVA")


class CQTRequest(BaseModel):
    """Dados de entrada para cálculo CQT (Metodologia Enel)."""

    segments: List[CQTSegment] = Field(..., min_length=1, description="Trechos de rede")
    trafo_kva: float = Field(..., gt=0, description="Potência do transformador em kVA")
    social_class: str = Field(default="B", description="Classe social dominante (A, B, C, D)")

    model_config = {
        "json_schema_extra": {
            "example": {
                "segments": [
                    {
                        "ponto": "TRAFO",
                        "montante": "",
                        "metros": 0,
                        "cabo": "",
                        "mono": 0,
                        "bi": 0,
                        "tri": 0,
                        "tri_esp": 0,
                        "carga_esp": 0,
                    },
                    {
                        "ponto": "P1",
                        "montante": "TRAFO",
                        "metros": 50,
                        "cabo": "3x35+54.6mm² Al",
                        "mono": 5,
                        "bi": 0,
                        "tri": 0,
                        "tri_esp": 0,
                        "carga_esp": 0,
                    },
                ],
                "trafo_kva": 112.5,
                "social_class": "B",
            }
        }
    }


class CQTResponse(BaseModel):
    """Resultado do cálculo CQT."""

    success: bool
    results: Optional[Dict[str, Any]] = None
    summary: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    segments_over_limit: Optional[List[str]] = Field(
        default=None,
        description=(
            "Identificadores dos trechos com CQT acumulado acima do limite de projeto "
            "(CNS-OMBR-MAT-19-0285). Lista vazia indica rede dentro do critério Enel."
        ),
    )


# ── Catenária ─────────────────────────────────────────────────────────────────


class CatenaryRequest(BaseModel):
    """Dados de entrada para cálculo de catenária."""

    span: float = Field(..., gt=0, description="Vão horizontal em metros")
    ha: float = Field(default=0.0, description="Altura do suporte A em metros")
    hb: float = Field(default=0.0, description="Altura do suporte B em metros")
    tension_daN: float = Field(..., gt=0, description="Tensão horizontal em daN")
    weight_kg_m: float = Field(..., gt=0, description="Peso linear do condutor em kg/m")
    min_clearance_m: Optional[float] = Field(
        default=None,
        gt=0,
        description=(
            "Distância mínima ao solo em metros para verificação de folga (NBR 5422). "
            "BT urbana = 6,0 m; BT rural = 5,5 m; MT = 7,0 m. "
            "Se fornecido, a resposta incluirá 'within_clearance' indicando conformidade."
        ),
    )
    include_curve: bool = Field(
        default=False,
        description=(
            "Se True, inclui os pontos da curva catenária (curve_x, curve_y) na resposta. "
            "Útil para integração BIM e renderização de curvas em ferramentas externas."
        ),
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "span": 80.0,
                "ha": 9.0,
                "hb": 9.0,
                "tension_daN": 500.0,
                "weight_kg_m": 0.779,
                "min_clearance_m": 6.0,
                "include_curve": True,
            }
        }
    }


class CatenaryResponse(BaseModel):
    """Resultado do cálculo de catenária."""

    sag: float = Field(..., description="Flecha máxima em metros")
    tension: float = Field(..., description="Tensão horizontal em daN")
    catenary_constant: float = Field(..., description="Constante catenária 'a' em metros")
    within_clearance: Optional[bool] = Field(
        default=None,
        description=(
            "True se a flecha respeita a distância mínima ao solo (NBR 5422). "
            "Preenchido somente quando 'min_clearance_m' é fornecido na requisição."
        ),
    )
    curve_x: Optional[List[float]] = Field(
        default=None,
        description=(
            "Coordenadas X (distância horizontal em metros) da curva catenária. "
            "Preenchido somente quando 'include_curve=true' é enviado na requisição."
        ),
    )
    curve_y: Optional[List[float]] = Field(
        default=None,
        description=(
            "Coordenadas Y (altura em metros) da curva catenária. "
            "Preenchido somente quando 'include_curve=true' é enviado na requisição."
        ),
    )


class CatenaryDxfRequest(BaseModel):
    """Dados de entrada para geração de DXF de catenária via API."""

    span: float = Field(..., gt=0, description="Vão horizontal em metros")
    ha: float = Field(default=0.0, description="Altura do suporte A em metros")
    hb: float = Field(default=0.0, description="Altura do suporte B em metros")
    tension_daN: float = Field(..., gt=0, description="Tensão horizontal em daN")
    weight_kg_m: float = Field(..., gt=0, description="Peso linear do condutor em kg/m")
    filename: str = Field(
        default="catenaria.dxf",
        min_length=1,
        max_length=100,
        description="Nome sugerido para o arquivo DXF (ex: 'trecho_01.dxf')",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "span": 80.0,
                "ha": 9.0,
                "hb": 9.0,
                "tension_daN": 500.0,
                "weight_kg_m": 0.779,
                "filename": "catenaria_vao80m.dxf",
            }
        }
    }


class CatenaryDxfResponse(BaseModel):
    """DXF de catenária codificado em Base64 para integração BIM."""

    dxf_base64: str = Field(..., description="Conteúdo do arquivo DXF codificado em Base64 (RFC 4648)")
    filename: str = Field(..., description="Nome sugerido para o arquivo DXF")
    sag: float = Field(..., description="Flecha máxima calculada em metros")
    catenary_constant: float = Field(..., description="Constante catenária 'a' em metros")


# ── Esforços em Postes ────────────────────────────────────────────────────────


class CaboInput(BaseModel):
    """Dados de um condutor para cálculo de esforços."""

    condutor: str = Field(..., description="Nome do condutor")
    vao: float = Field(default=0.0, ge=0, description="Vão em metros")
    angulo: float = Field(default=0.0, description="Ângulo de desvio em graus")
    flecha: float = Field(default=1.0, gt=0, description="Flecha (método flecha) em metros")


class PoleLoadRequest(BaseModel):
    """Dados de entrada para cálculo de esforços em postes."""

    concessionaria: str = Field(..., description="Nome da concessionária (Light, Enel)")
    condicao: str = Field(default="Normal", description="Condição de carga (Normal, Vento Forte, Gelo)")
    cabos: List[CaboInput] = Field(..., min_length=1, description="Lista de condutores")

    model_config = {
        "json_schema_extra": {
            "example": {
                "concessionaria": "Light",
                "condicao": "Normal",
                "cabos": [{"condutor": "556MCM-CA, Nu", "vao": 80, "angulo": 30, "flecha": 1.5}],
            }
        }
    }


class PoleLoadResponse(BaseModel):
    """Resultado do cálculo de esforços em postes."""

    resultant_force: float = Field(..., description="Força resultante em daN")
    resultant_angle: float = Field(..., description="Ângulo da resultante em graus")
    total_x: float = Field(..., description="Componente X total em daN")
    total_y: float = Field(..., description="Componente Y total em daN")
    vectors: List[Dict[str, Any]] = Field(..., description="Detalhes de cada condutor")
    suggested_poles: List[Dict[str, Any]] = Field(default_factory=list, description="Postes sugeridos")


class PoleSuggestResponse(BaseModel):
    """Resultado da sugestão de postes por carga."""

    force_daN: float = Field(..., description="Força de consulta em daN")
    suggested_poles: List[Dict[str, Any]] = Field(..., description="Postes adequados ordenados por material")


# ── Dados Mestres (BIM) ───────────────────────────────────────────────────────


class ConductorOut(BaseModel):
    """Dados de um condutor elétrico."""

    name: str = Field(..., description="Nome/código do condutor")
    weight_kg_m: float = Field(..., description="Peso linear em kg/m")


class PoleOut(BaseModel):
    """Dados de um poste de distribuição."""

    material: str = Field(..., description="Material (Concreto, Madeira, Aço)")
    format: str = Field(..., description="Formato (C, D, E, etc.)")
    description: str = Field(..., description="Descrição técnica (altura/carga)")
    nominal_load_daN: float = Field(..., description="Carga nominal em daN")


class ConcessionaireOut(BaseModel):
    """Dados de uma concessionária de energia."""

    name: str = Field(..., description="Nome da concessionária")
    method: str = Field(..., description="Método de cálculo (flecha, tabela)")


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
