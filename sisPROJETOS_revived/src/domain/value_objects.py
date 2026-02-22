"""
Value Objects de domínio do sisPROJETOS (DDD).

Value Objects são objetos imutáveis definidos pelos seus valores, sem identidade
própria. São usados para representar conceitos de domínio ricos em semântica
de forma type-safe e auto-validada.

Referências normativas:
    - NBR 5422: Cálculo de catenária e flecha de condutores
    - NBR 5410: Queda de tensão em instalações elétricas
    - NBR 13133: Coordenadas UTM e convenção 2.5D (Z = elevação)
    - ABNT NBR ISO 6709: Representação de posição geográfica
    - ANEEL PRODIST Módulo 8: Qualidade da Energia Elétrica (BT: 8%, MT: 7%)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, ClassVar

if TYPE_CHECKING:
    from domain.standards import VoltageStandard


@dataclass(frozen=True)
class UTMCoordinate:
    """Coordenada UTM 2.5D imutável conforme ABNT NBR 13133.

    Representa um ponto geográfico no sistema de coordenadas UTM (Universal
    Transversa de Mercator), no formato 2.5D: posição XY + elevação Z.

    Attributes:
        easting: Coordenada E (Este) em metros. Deve ser positivo.
        northing: Coordenada N (Norte) em metros. Deve ser positivo.
        zone: Fuso UTM (ex: '23K', '23S'). Não pode ser vazio.
        elevation: Elevação em metros acima do nível do mar (padrão 0.0).

    Raises:
        ValueError: Se easting ≤ 0, northing ≤ 0 ou zone for vazio.

    Example:
        >>> p = UTMCoordinate(easting=788547.0, northing=7634925.0, zone="23K", elevation=720.0)
        >>> p.easting
        788547.0
    """

    easting: float
    northing: float
    zone: str
    elevation: float = 0.0

    def __post_init__(self) -> None:
        if self.easting <= 0:
            raise ValueError(f"Easting deve ser positivo; recebido: {self.easting}")
        if self.northing <= 0:
            raise ValueError(f"Northing deve ser positivo; recebido: {self.northing}")
        if not self.zone or not isinstance(self.zone, str):
            raise ValueError("Zone UTM é obrigatória e deve ser uma string não-vazia")


@dataclass(frozen=True)
class CatenaryResult:
    """Resultado imutável do cálculo de catenária (NBR 5422).

    Encapsula os parâmetros calculados de uma catenária, garantindo que os
    valores de negócio sejam válidos após a criação.

    Attributes:
        sag: Flecha máxima em metros (≥ 0).
        tension: Tensão horizontal em daN (> 0).
        catenary_constant: Constante catenária 'a' em metros (> 0).

    Raises:
        ValueError: Se sag < 0, tension ≤ 0 ou catenary_constant ≤ 0.

    Example:
        >>> r = CatenaryResult(sag=1.23, tension=2000.0, catenary_constant=130.5)
        >>> r.sag
        1.23
    """

    sag: float
    tension: float
    catenary_constant: float

    def __post_init__(self) -> None:
        if self.sag < 0:
            raise ValueError(f"Flecha (sag) não pode ser negativa; recebida: {self.sag}")
        if self.tension <= 0:
            raise ValueError(f"Tensão horizontal deve ser positiva; recebida: {self.tension}")
        if self.catenary_constant <= 0:
            raise ValueError(f"Constante catenária deve ser positiva; recebida: {self.catenary_constant}")


@dataclass(frozen=True)
class VoltageDropResult:
    """Resultado imutável do cálculo de queda de tensão (NBR 5410).

    Attributes:
        drop_v: Queda de tensão em Volts (≥ 0).
        drop_percent: Queda de tensão em porcentagem (≥ 0).
        material: Material do condutor (ex: 'Alumínio', 'Cobre').

    Properties:
        is_within_limit: True se drop_percent ≤ 5.0 (limite NBR 5410).

    Raises:
        ValueError: Se drop_v < 0, drop_percent < 0 ou material for vazio.

    Example:
        >>> r = VoltageDropResult(drop_v=5.5, drop_percent=2.5, material="Alumínio")
        >>> r.is_within_limit
        True
    """

    drop_v: float
    drop_percent: float
    material: str

    LIMIT_PERCENT: ClassVar[float] = 5.0  # NBR 5410

    def __post_init__(self) -> None:
        if self.drop_v < 0:
            raise ValueError(f"Queda de tensão não pode ser negativa; recebida: {self.drop_v}")
        if self.drop_percent < 0:
            raise ValueError(f"Porcentagem de queda não pode ser negativa; recebida: {self.drop_percent}")
        if not self.material or not isinstance(self.material, str):
            raise ValueError("Material do condutor é obrigatório")

    @property
    def is_within_limit(self) -> bool:
        """Verifica conformidade com o limite de queda de tensão NBR 5410 (5%).

        Returns:
            True se a queda de tensão for ≤ 5% (conforme NBR 5410).
        """
        return self.drop_percent <= self.LIMIT_PERCENT

    def is_within_standard(self, standard: "VoltageStandard") -> bool:
        """Verifica conformidade com o limite de um padrão regulatório.

        Permite verificar conformidade com ABNT NBR 5410, ANEEL/PRODIST
        Módulo 8 (BT/MT) ou normas de concessionárias (Light, Enel).

        Args:
            standard: Padrão regulatório a aplicar (``VoltageStandard``).

        Returns:
            True se drop_percent ≤ standard.max_drop_percent.

        Example:
            >>> from domain.standards import PRODIST_MODULE8_BT
            >>> r = VoltageDropResult(drop_v=14.0, drop_percent=6.4, material="Al")
            >>> r.is_within_limit         # NBR 5410 — 5%: False
            False
            >>> r.is_within_standard(PRODIST_MODULE8_BT)  # PRODIST — 8%: True
            True
        """
        return standard.check(self.drop_percent)


@dataclass(frozen=True)
class SpanResult:
    """Resultado imutável do cálculo de esforço por vão de condutor.

    Representa os dados calculados para um único vão em um cálculo de esforços
    em postes (pole load), conforme metodologia Light/Enel.

    Attributes:
        vao: Comprimento do vão em metros (≥ 0).
        angulo: Ângulo de desvio em graus (0–360).
        flecha: Flecha do vão em metros (≥ 0).

    Raises:
        ValueError: Se vao < 0, angulo fora de [0, 360] ou flecha < 0.

    Example:
        >>> s = SpanResult(vao=100.0, angulo=15.0, flecha=1.5)
        >>> s.vao
        100.0
    """

    vao: float
    angulo: float
    flecha: float

    def __post_init__(self) -> None:
        if self.vao < 0:
            raise ValueError(f"Comprimento do vão não pode ser negativo; recebido: {self.vao}")
        if not (0.0 <= self.angulo <= 360.0):
            raise ValueError(f"Ângulo deve estar entre 0 e 360 graus; recebido: {self.angulo}")
        if self.flecha < 0:
            raise ValueError(f"Flecha não pode ser negativa; recebida: {self.flecha}")
