"""
Serviços de domínio (DDD Domain Services) do sisPROJETOS.

Serviços de domínio encapsulam operações de negócio que envolvem múltiplos
conceitos de domínio e não pertencem naturalmente a uma única entidade.
São stateless e trabalham exclusivamente com entidades e value objects do domínio.

Referências normativas:
    - NBR 5422: Cálculo de catenária e flecha de condutores (§3.2 — conversão kgf→daN)
    - NBR 5410: Queda de tensão em instalações elétricas de baixa tensão (limite 5%)
    - ANEEL PRODIST Módulo 8: Qualidade da Energia Elétrica (BT: 8%, MT: 7%)
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Optional

from domain.entities import Conductor
from domain.value_objects import CatenaryResult, VoltageDropResult

if TYPE_CHECKING:
    from domain.standards import VoltageStandard

# Fator de conversão: 1 kgf = 9.80665 N = 0.980665 daN  (NBR 5422 §3.2)
_KG_TO_DAN: float = 0.980665


class CatenaryDomainService:
    """Serviço de domínio para cálculo de catenária (NBR 5422).

    Encapsula a fórmula da catenária hiperbólica e produz um ``CatenaryResult``
    imutável a partir de uma entidade ``Conductor`` e parâmetros de vão.

    A constante catenária 'a' é calculada como::

        a = T / w  (m)

    onde T é a tensão horizontal (daN) e w é o peso linear do condutor (daN/m).

    A flecha máxima em vão nivelado segue::

        f = a · (cosh(L / (2a)) − 1)  (NBR 5422)

    Esta fórmula é a mesma utilizada em ``CatenaryLogic.calculate_catenary()``
    (``src/modules/catenaria/logic.py``), garantindo consistência nos resultados.

    Example:
        >>> from domain.entities import Conductor
        >>> svc = CatenaryDomainService()
        >>> c = Conductor(name="556MCM-CA", weight_kg_m=1.594, breaking_load_daN=13750.0)
        >>> result = svc.calculate(c, span=100.0, tension_daN=2000.0)
        >>> result.sag > 0
        True
    """

    def calculate(
        self,
        conductor: Conductor,
        span: float,
        tension_daN: float,
        ha: float = 0.0,
        hb: float = 0.0,
    ) -> CatenaryResult:
        """Calcula flecha e constante catenária para um condutor num vão.

        Args:
            conductor: Entidade Conductor com peso linear (weight_kg_m > 0).
            span: Distância horizontal entre apoios em metros (deve ser > 0).
            tension_daN: Tensão horizontal no condutor em daN (deve ser > 0).
            ha: Altura do apoio A em metros (padrão 0.0, não utilizado no cálculo
                de flecha de vão nivelado, reservado para extensões futuras).
            hb: Altura do apoio B em metros (padrão 0.0, idem).

        Returns:
            ``CatenaryResult`` com ``sag`` (m), ``tension`` (daN) e
            ``catenary_constant`` (m).

        Raises:
            ValueError: Se ``span`` ≤ 0, ``tension_daN`` ≤ 0 ou
                        ``conductor.weight_kg_m`` ≤ 0.
        """
        if span <= 0:
            raise ValueError(f"Vão deve ser positivo; recebido: {span}")
        if tension_daN <= 0:
            raise ValueError(f"Tensão deve ser positiva; recebida: {tension_daN}")
        if conductor.weight_kg_m <= 0:
            raise ValueError(f"Peso linear do condutor deve ser > 0; recebido: {conductor.weight_kg_m}")

        # Peso linear em daN/m conforme conversão NBR 5422 §3.2
        w_dan_m: float = conductor.weight_kg_m * _KG_TO_DAN

        # Constante catenária: a = T / w  (m)
        catenary_constant: float = tension_daN / w_dan_m

        # Flecha máxima em vão nivelado: f = a·(cosh(L/2a) − 1)  (NBR 5422)
        sag: float = catenary_constant * (math.cosh(span / (2 * catenary_constant)) - 1)

        return CatenaryResult(
            sag=round(sag, 6),
            tension=tension_daN,
            catenary_constant=round(catenary_constant, 6),
        )

    def is_within_clearance(self, result: CatenaryResult, min_clearance_m: float) -> bool:
        """Verifica se a flecha respeita a distância mínima ao solo (NBR 5422).

        Args:
            result: Resultado do cálculo de catenária.
            min_clearance_m: Distância mínima ao solo em metros (ex: 6.0 m para BT).

        Returns:
            True se ``result.sag`` ≤ ``min_clearance_m``.
        """
        return result.sag <= min_clearance_m


class VoltageDropDomainService:
    """Serviço de domínio para cálculo de queda de tensão (NBR 5410 / PRODIST).

    Encapsula a fórmula de queda de tensão e produz um ``VoltageDropResult``
    imutável. Segue a mesma fórmula de ``ElectricalLogic.calculate_voltage_drop()``
    (``src/modules/electrical/logic.py``) para consistência de resultados.

    Para circuito monofásico (fator 2 = ida + volta)::

        I = P / (V · cos φ)
        ΔV = 2 · I · R · cos φ

    Para circuito trifásico::

        I = P / (√3 · V · cos φ)
        ΔV = √3 · I · R · cos φ

    onde ``R = ρ · L / A`` (Ω).

    O parâmetro ``standard`` determina o padrão normativo de referência:
    - Padrão: ``NBR_5410`` (5%). Para verificar conformidade, use
      ``result.is_within_limit``.
    - ANEEL/PRODIST BT (8%) ou MT (7%): use ``PRODIST_MODULE8_BT`` /
      ``PRODIST_MODULE8_MT``. Verificar com ``result.is_within_standard(std)``.
    - Norma de concessionária (Light/Enel): use ``LIGHT_BT`` ou ``ENEL_BT``.
      Quando ``standard.overrides_abnt=True``, exibir ``standard.override_toast_pt_br``
      como toast na interface.

    Example:
        >>> svc = VoltageDropDomainService()
        >>> result = svc.calculate("Alumínio", 0.0282, 100.0, 10.0, 35.0, 380.0, 3)
        >>> result.is_within_limit
        True
    """

    def calculate(
        self,
        material: str,
        resistivity: float,
        length_m: float,
        power_kw: float,
        section_mm2: float,
        voltage_v: float,
        phases: int = 3,
        cos_phi: float = 0.92,
        standard: Optional[VoltageStandard] = None,
    ) -> VoltageDropResult:
        """Calcula a queda de tensão para um trecho de circuito.

        Args:
            material: Nome do material condutor (ex: 'Alumínio', 'Cobre').
            resistivity: Resistividade em Ω·mm²/m (deve ser > 0).
            length_m: Comprimento do trecho em metros (deve ser ≥ 0).
            power_kw: Potência em quilowatts (deve ser > 0).
            section_mm2: Seção transversal em mm² (deve ser > 0).
            voltage_v: Tensão do sistema em Volts (deve ser > 0).
            phases: Número de fases — 1 (monofásico) ou 3 (trifásico).
            cos_phi: Fator de potência (padrão 0.92; deve estar em (0, 1]).
            standard: Padrão normativo de referência (opcional). Se fornecido
                e ``standard.overrides_abnt=True``, o chamador deve exibir
                ``standard.override_toast_pt_br`` como toast ao usuário. O
                argumento não altera o cálculo — apenas facilita a verificação
                de conformidade via ``result.is_within_standard(standard)``.

        Returns:
            ``VoltageDropResult`` com ``drop_v`` (V), ``drop_percent`` (%)
            e ``material``. Use ``result.is_within_standard(standard)`` para
            verificar conformidade com o padrão fornecido, ou
            ``result.is_within_limit`` para NBR 5410 (5%).

        Raises:
            ValueError: Se qualquer parâmetro estiver fora dos limites definidos.
        """
        if not material or not isinstance(material, str):
            raise ValueError("Material do condutor é obrigatório")
        if resistivity <= 0:
            raise ValueError(f"Resistividade deve ser positiva; recebida: {resistivity}")
        if length_m < 0:
            raise ValueError(f"Comprimento não pode ser negativo; recebido: {length_m}")
        if power_kw <= 0:
            raise ValueError(f"Potência deve ser positiva; recebida: {power_kw}")
        if section_mm2 <= 0:
            raise ValueError(f"Seção transversal deve ser positiva; recebida: {section_mm2}")
        if voltage_v <= 0:
            raise ValueError(f"Tensão deve ser positiva; recebida: {voltage_v}")
        if phases not in (1, 3):
            raise ValueError(f"Fases deve ser 1 ou 3; recebido: {phases}")
        if not (0 < cos_phi <= 1.0):
            raise ValueError(f"Fator de potência deve estar em (0, 1]; recebido: {cos_phi}")

        power_w: float = power_kw * 1000.0
        resistance: float = resistivity * length_m / section_mm2  # Ω

        if phases == 3:
            current: float = power_w / (math.sqrt(3) * voltage_v * cos_phi)
            drop_v: float = math.sqrt(3) * current * resistance * cos_phi
        else:
            current = power_w / (voltage_v * cos_phi)
            drop_v = 2 * current * resistance * cos_phi

        drop_percent: float = (drop_v / voltage_v) * 100.0

        return VoltageDropResult(
            drop_v=round(drop_v, 4),
            drop_percent=round(drop_percent, 4),
            material=material,
        )
