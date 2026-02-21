"""
Schemas Pydantic para a API REST do sisPROJETOS.

Define modelos de entrada e saída para cada endpoint,
garantindo validação automática e documentação OpenAPI.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

# ── Elétrico ─────────────────────────────────────────────────────────────────


class VoltageDropRequest(BaseModel):
    """Dados de entrada para cálculo de queda de tensão (NBR 5410)."""

    power_kw: float = Field(..., gt=0, description="Potência ativa em kW")
    distance_m: float = Field(..., gt=0, description="Comprimento do trecho em metros")
    voltage_v: float = Field(..., gt=0, description="Tensão de fornecimento em V")
    material: str = Field(default="Alumínio", description="Material do condutor (Alumínio, Cobre)")
    section_mm2: float = Field(..., gt=0, description="Seção transversal do condutor em mm²")
    cos_phi: float = Field(default=0.92, gt=0, le=1, description="Fator de potência cos φ")
    phases: int = Field(default=3, description="Número de fases (1 ou 3)")

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
            }
        }
    }


class VoltageDropResponse(BaseModel):
    """Resultado do cálculo de queda de tensão."""

    current: float = Field(..., description="Corrente calculada em Ampères")
    delta_v_volts: float = Field(..., description="Queda de tensão em Volts")
    percentage_drop: float = Field(..., description="Queda de tensão percentual (%)")
    allowed: bool = Field(..., description="True se ≤ 5% (limite NBR 5410)")


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


# ── Catenária ─────────────────────────────────────────────────────────────────


class CatenaryRequest(BaseModel):
    """Dados de entrada para cálculo de catenária."""

    span: float = Field(..., gt=0, description="Vão horizontal em metros")
    ha: float = Field(default=0.0, description="Altura do suporte A em metros")
    hb: float = Field(default=0.0, description="Altura do suporte B em metros")
    tension_daN: float = Field(..., gt=0, description="Tensão horizontal em daN")
    weight_kg_m: float = Field(..., gt=0, description="Peso linear do condutor em kg/m")

    model_config = {
        "json_schema_extra": {
            "example": {
                "span": 80.0,
                "ha": 9.0,
                "hb": 9.0,
                "tension_daN": 500.0,
                "weight_kg_m": 0.779,
            }
        }
    }


class CatenaryResponse(BaseModel):
    """Resultado do cálculo de catenária."""

    sag: float = Field(..., description="Flecha máxima em metros")
    tension: float = Field(..., description="Tensão horizontal em daN")
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
