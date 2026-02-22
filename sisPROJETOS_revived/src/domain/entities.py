"""
Entidades de domínio do sisPROJETOS (DDD).

Entidades são objetos com identidade própria que encapsulam regras de negócio
do domínio de engenharia elétrica. Diferente dos value objects, entidades podem
ser mutáveis e são identificadas por um atributo de identidade.

No contexto do sisPROJETOS, as entidades representam o catálogo de ativos
de rede de distribuição elétrica, conforme normas ABNT vigentes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import ClassVar, FrozenSet, Optional


@dataclass
class Conductor:
    """Entidade de domínio: condutor elétrico de rede de distribuição.

    Representa um condutor cadastrado no catálogo técnico do sistema,
    com suas características físico-mecânicas utilizadas nos cálculos
    de catenária e pole load.

    Attributes:
        name: Nome técnico do condutor (ex: '556MCM-CA', '1/0AWG-CAA').
        weight_kg_m: Peso linear em kg/m (≥ 0).
        breaking_load_daN: Carga de ruptura em daN (> 0).
        section_mm2: Seção transversal em mm² (opcional, > 0 se informado).

    Raises:
        ValueError: Se name for vazio, weight_kg_m < 0, breaking_load_daN ≤ 0
                    ou section_mm2 ≤ 0 (quando informado).

    Example:
        >>> c = Conductor(name="556MCM-CA", weight_kg_m=1.594, breaking_load_daN=13750.0)
        >>> c.name
        '556MCM-CA'
    """

    name: str
    weight_kg_m: float
    breaking_load_daN: float
    section_mm2: Optional[float] = field(default=None)

    def __post_init__(self) -> None:
        if not self.name or not isinstance(self.name, str):
            raise ValueError("Nome do condutor é obrigatório")
        if self.weight_kg_m < 0:
            raise ValueError(f"Peso linear não pode ser negativo; recebido: {self.weight_kg_m}")
        if self.breaking_load_daN <= 0:
            raise ValueError(f"Carga de ruptura deve ser positiva; recebida: {self.breaking_load_daN}")
        if self.section_mm2 is not None and self.section_mm2 <= 0:
            raise ValueError(f"Seção transversal deve ser positiva; recebida: {self.section_mm2}")


@dataclass
class Pole:
    """Entidade de domínio: poste de distribuição elétrica.

    Representa um poste do catálogo técnico, com suas características
    estruturais usadas nos cálculos de esforços mecânicos (NBR 8451).

    Attributes:
        material: Material construtivo (ex: 'Concreto', 'Madeira', 'Aço').
        height_m: Altura total em metros (> 0).
        format: Formato estrutural (ex: 'Circular', 'Duplo T').
        nominal_load_daN: Carga nominal em daN (> 0).

    Raises:
        ValueError: Se material ou format forem vazios, ou se height_m ≤ 0
                    ou nominal_load_daN ≤ 0.

    Example:
        >>> p = Pole(material="Concreto", height_m=11.0, format="Circular", nominal_load_daN=300.0)
        >>> p.nominal_load_daN
        300.0
    """

    material: str
    height_m: float
    format: str
    nominal_load_daN: float

    def __post_init__(self) -> None:
        if not self.material or not isinstance(self.material, str):
            raise ValueError("Material do poste é obrigatório")
        if self.height_m <= 0:
            raise ValueError(f"Altura do poste deve ser positiva; recebida: {self.height_m}")
        if not self.format or not isinstance(self.format, str):
            raise ValueError("Formato do poste é obrigatório")
        if self.nominal_load_daN <= 0:
            raise ValueError(f"Carga nominal deve ser positiva; recebida: {self.nominal_load_daN}")


@dataclass
class Concessionaire:
    """Entidade de domínio: concessionária de energia elétrica.

    Representa uma concessionária cadastrada, com o método de cálculo
    que ela utiliza para projetos de distribuição.

    Attributes:
        name: Nome da concessionária (ex: 'Light', 'Enel').
        method: Método de cálculo ('flecha' ou 'tabela').

    Raises:
        ValueError: Se name for vazio ou method não for 'flecha' ou 'tabela'.

    Example:
        >>> c = Concessionaire(name="Light", method="flecha")
        >>> c.method
        'flecha'
    """

    VALID_METHODS: ClassVar[FrozenSet[str]] = frozenset({"flecha", "tabela"})

    name: str
    method: str

    def __post_init__(self) -> None:
        if not self.name or not isinstance(self.name, str):
            raise ValueError("Nome da concessionária é obrigatório")
        if self.method not in self.VALID_METHODS:
            raise ValueError(f"Método inválido: '{self.method}'. Valores aceitos: 'flecha', 'tabela'")
