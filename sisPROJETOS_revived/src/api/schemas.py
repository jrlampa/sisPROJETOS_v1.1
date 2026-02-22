"""
Schemas Pydantic para a API REST do sisPROJETOS.

Define modelos de entrada e saída para cada endpoint,
garantindo validação automática e documentação OpenAPI.

Schemas BIM (KML/UTM/DXF/Projetos) estão em ``api.schemas_bim`` e
são re-exportados aqui para compatibilidade com os arquivos de rota.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

# Re-exporta schemas BIM para que os arquivos de rota não precisem mudar.
from api.schemas_bim import (  # noqa: F401
    CatenaryBatchItem,
    CatenaryBatchRequest,
    CatenaryBatchResponse,
    CatenaryBatchResponseItem,
    ClearancesResponse,
    ClearanceTypeOut,
    ConcessionaireOut,
    ConductorOut,
    KmlConvertRequest,
    KmlConvertResponse,
    KmlPointOut,
    PoleOut,
    ProjectCreateRequest,
    ProjectCreateResponse,
    ProjectListResponse,
    UTMPointIn,
    UTMToDxfRequest,
    UTMToDxfResponse,
    VoltageBatchItem,
    VoltageBatchRequest,
    VoltageBatchResponse,
    VoltageBatchResponseItem,
)

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


# ── Relatório de Esforços em Postes (PDF) ─────────────────────────────────────


class PoleLoadReportRequest(BaseModel):
    """Dados de entrada para geração de relatório PDF de esforços em postes."""

    concessionaria: str = Field(..., description="Nome da concessionária (Light, Enel)")
    condicao: str = Field(default="Normal", description="Condição de carga (Normal, Vento Forte, Gelo)")
    cabos: List[CaboInput] = Field(..., min_length=1, description="Lista de condutores")
    project_name: str = Field(
        default="Projeto sisPROJETOS",
        max_length=100,
        description="Nome do projeto para cabeçalho do relatório",
    )
    filename: str = Field(
        default="relatorio_esforcos.pdf",
        min_length=1,
        max_length=100,
        description="Nome sugerido para o arquivo PDF (ex: 'trecho_01.pdf')",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "concessionaria": "Light",
                "condicao": "Normal",
                "cabos": [{"condutor": "556MCM-CA, Nu", "vao": 80, "angulo": 30, "flecha": 1.5}],
                "project_name": "LT_BT_Centro_SP_2026",
                "filename": "relatorio_esforcos_trecho01.pdf",
            }
        }
    }


class PoleLoadReportResponse(BaseModel):
    """Relatório PDF de esforços em postes codificado em Base64."""

    pdf_base64: str = Field(..., description="Conteúdo do arquivo PDF codificado em Base64 (RFC 4648)")
    filename: str = Field(..., description="Nome sugerido para o arquivo PDF")
    resultant_force: float = Field(..., description="Força resultante calculada em daN")


# ── Esforços em Postes em Lote (Batch) ───────────────────────────────────────


class PoleLoadBatchItem(BaseModel):
    """Parâmetros de um poste individual para cálculo de esforços em lote.

    Todos os campos seguem as mesmas regras do endpoint POST /api/v1/pole-load/resultant.
    O campo ``label`` é opcional e serve apenas para identificação do item na resposta.
    """

    label: Optional[str] = Field(
        default=None,
        max_length=80,
        description="Rótulo opcional para identificar o poste na resposta (ex: 'Poste P1-P2')",
    )
    concessionaria: str = Field(..., description="Nome da concessionária (Light, Enel)")
    condicao: str = Field(default="Normal", description="Condição de carga (Normal, Vento Forte, Gelo)")
    cabos: List[CaboInput] = Field(..., min_length=1, description="Lista de condutores (mínimo 1)")

    model_config = {
        "json_schema_extra": {
            "example": {
                "label": "Poste P1-P2",
                "concessionaria": "Light",
                "condicao": "Normal",
                "cabos": [{"condutor": "556MCM-CA, Nu", "vao": 80.0, "angulo": 30.0, "flecha": 1.5}],
            }
        }
    }


class PoleLoadBatchResponseItem(BaseModel):
    """Resultado do cálculo de esforços para um poste individual."""

    index: int = Field(..., description="Índice do item (base 0) na lista de entrada")
    label: Optional[str] = Field(default=None, description="Rótulo fornecido na entrada")
    success: bool = Field(..., description="True se o cálculo foi concluído com sucesso")
    error: Optional[str] = Field(default=None, description="Mensagem de erro caso success=False")
    resultant_force: Optional[float] = Field(default=None, description="Força resultante em daN")
    resultant_angle: Optional[float] = Field(default=None, description="Ângulo da resultante em graus")
    suggested_poles: Optional[List[Dict[str, Any]]] = Field(
        default=None, description="Postes sugeridos para a carga calculada"
    )


class PoleLoadBatchRequest(BaseModel):
    """Dados de entrada para cálculo de esforços em lote (múltiplos postes).

    Permite calcular a resultante de esforços para até 20 postes em uma única chamada.
    Falhas individuais (concessionária inválida, dados de cabo ausentes) retornam
    ``success=False`` para o item sem abortar os demais postes do lote.
    Ideal para integração BIM com múltiplos postes de uma rede de distribuição.
    """

    items: List[PoleLoadBatchItem] = Field(..., min_length=1, max_length=20, description="Lista de postes (1–20)")

    model_config = {
        "json_schema_extra": {
            "example": {
                "items": [
                    {
                        "label": "Poste P1",
                        "concessionaria": "Light",
                        "condicao": "Normal",
                        "cabos": [{"condutor": "556MCM-CA, Nu", "vao": 80.0, "angulo": 30.0, "flecha": 1.5}],
                    },
                    {
                        "label": "Poste P2",
                        "concessionaria": "Enel",
                        "condicao": "Normal",
                        "cabos": [
                            {"condutor": "397MCM-CA, Nu", "vao": 60.0, "angulo": 0.0, "flecha": 1.2},
                            {"condutor": "397MCM-CA, Nu", "vao": 60.0, "angulo": 90.0, "flecha": 1.2},
                        ],
                    },
                ]
            }
        }
    }


class PoleLoadBatchResponse(BaseModel):
    """Resposta do cálculo de esforços em lote."""

    count: int = Field(..., description="Número de postes processados")
    success_count: int = Field(..., description="Número de postes calculados com sucesso")
    error_count: int = Field(..., description="Número de postes com erro de cálculo")
    items: List[PoleLoadBatchResponseItem] = Field(..., description="Resultados individuais por poste")
