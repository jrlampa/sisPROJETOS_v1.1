"""
Padrões regulatórios de queda de tensão — ABNT, ANEEL/PRODIST e concessionárias.

Este módulo codifica os limites normativos de queda de tensão utilizados no
cálculo de projetos de redes de distribuição elétrica.

Hierarquia de normas:
    1. ABNT NBR 5410 — instalações de BT (5% max). Padrão-base.
    2. ANEEL/PRODIST Módulo 8 — redes de distribuição BT/MT (8%/7% max).
    3. Normas de concessionárias (Light, Enel) — derivadas do PRODIST;
       sobrepõem a ABNT com toast explícito ao usuário.

Regra:
    Quando normas de concessionárias são aplicadas, a ABNT NBR 5410 é ignorada
    e o campo ``override_toast_pt_br`` deve ser exibido como toast na interface.

Referências:
    - ABNT NBR 5410:2004 — Instalações Elétricas de Baixa Tensão
    - ANEEL PRODIST Módulo 8 (Res. Norm. 956/2021) — Qualidade da Energia Elétrica
    - ANEEL PRODIST Módulo 6 — Acesso ao Sistema de Distribuição
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import ClassVar, FrozenSet, Optional


@dataclass(frozen=True)
class VoltageStandard:
    """Padrão regulatório de queda de tensão (value object imutável).

    Encapsula os limites e metadados de um padrão normativo de queda de
    tensão. Quando o padrão de uma concessionária é aplicado, ABNT NBR 5410
    deve ser ignorada e o campo ``override_toast_pt_br`` exibido como toast.

    Attributes:
        name: Identificador do padrão (ex: 'NBR 5410', 'PRODIST Módulo 8 BT').
        source: Origem normativa. Deve ser um de VALID_SOURCES.
        max_drop_percent: Limite máximo de queda de tensão em % (> 0).
        overrides_abnt: True quando este padrão substitui a ABNT NBR 5410.
        override_toast_pt_br: Mensagem de toast em pt-BR a exibir ao usuário
            quando ABNT é ignorada. Obrigatória se overrides_abnt=True.

    Raises:
        ValueError: Se name ou source forem inválidos, max_drop_percent ≤ 0,
                    ou overrides_abnt=True sem override_toast_pt_br definido.

    Example:
        >>> s = VoltageStandard(
        ...     name="NBR 5410",
        ...     source="ABNT",
        ...     max_drop_percent=5.0,
        ...     overrides_abnt=False,
        ... )
        >>> s.check(4.9)
        True
        >>> s.check(5.1)
        False
    """

    VALID_SOURCES: ClassVar[FrozenSet[str]] = frozenset({"ABNT", "ANEEL/PRODIST", "CONCESSIONAIRE"})

    name: str
    source: str
    max_drop_percent: float
    overrides_abnt: bool
    override_toast_pt_br: str = field(default="")

    def __post_init__(self) -> None:
        if not self.name or not isinstance(self.name, str):
            raise ValueError("Nome do padrão é obrigatório")
        if self.source not in self.VALID_SOURCES:
            raise ValueError(f"Fonte inválida: '{self.source}'. " f"Valores aceitos: {sorted(self.VALID_SOURCES)}")
        if self.max_drop_percent <= 0:
            raise ValueError(f"Limite de queda deve ser positivo; recebido: {self.max_drop_percent}")
        if self.overrides_abnt and not self.override_toast_pt_br:
            raise ValueError("Padrão que sobrepõe ABNT deve definir 'override_toast_pt_br'")

    def check(self, drop_percent: float) -> bool:
        """Verifica se uma queda de tensão está dentro deste padrão.

        Args:
            drop_percent: Queda de tensão calculada em % (valor ≥ 0).

        Returns:
            True se drop_percent ≤ max_drop_percent.
        """
        return drop_percent <= self.max_drop_percent


# ─── Padrões pré-definidos ────────────────────────────────────────────────────

NBR_5410: VoltageStandard = VoltageStandard(
    name="NBR 5410",
    source="ABNT",
    max_drop_percent=5.0,
    overrides_abnt=False,
    override_toast_pt_br="",
)
"""ABNT NBR 5410:2004 — Instalações Elétricas de Baixa Tensão. Limite: 5%."""

PRODIST_MODULE8_BT: VoltageStandard = VoltageStandard(
    name="PRODIST Módulo 8 — BT",
    source="ANEEL/PRODIST",
    max_drop_percent=8.0,
    overrides_abnt=True,
    override_toast_pt_br=(
        "⚠️ ANEEL/PRODIST Módulo 8 aplicado (Baixa Tensão). "
        "Limite regulatório: 8% de queda de tensão. "
        "ABNT NBR 5410 (5%) ignorada conforme hierarquia ANEEL."
    ),
)
"""ANEEL PRODIST Módulo 8 BT — V_pu adequado ≥ 0.92 → max queda = 8%."""

PRODIST_MODULE8_MT: VoltageStandard = VoltageStandard(
    name="PRODIST Módulo 8 — MT",
    source="ANEEL/PRODIST",
    max_drop_percent=7.0,
    overrides_abnt=True,
    override_toast_pt_br=(
        "⚠️ ANEEL/PRODIST Módulo 8 aplicado (Média Tensão). "
        "Limite regulatório: 7% de queda de tensão. "
        "ABNT NBR 5410 (5%) ignorada conforme hierarquia ANEEL."
    ),
)
"""ANEEL PRODIST Módulo 8 MT — V_pu adequado ≥ 0.93 → max queda = 7%."""

LIGHT_BT: VoltageStandard = VoltageStandard(
    name="Light — BT (PRODIST Módulo 8)",
    source="CONCESSIONAIRE",
    max_drop_percent=8.0,
    overrides_abnt=True,
    override_toast_pt_br=(
        "⚠️ Norma da concessionária Light (BT) aplicada conforme "
        "ANEEL/PRODIST Módulo 8. Limite: 8% de queda de tensão. "
        "ABNT NBR 5410 (5%) ignorada."
    ),
)
"""Norma Light para BT — derivada do PRODIST Módulo 8. Limite: 8%."""

ENEL_BT: VoltageStandard = VoltageStandard(
    name="Enel — BT (PRODIST Módulo 8)",
    source="CONCESSIONAIRE",
    max_drop_percent=8.0,
    overrides_abnt=True,
    override_toast_pt_br=(
        "⚠️ Norma da concessionária Enel (BT) aplicada conforme "
        "ANEEL/PRODIST Módulo 8. Limite: 8% de queda de tensão. "
        "ABNT NBR 5410 (5%) ignorada."
    ),
)
"""Norma Enel para BT — derivada do PRODIST Módulo 8. Limite: 8%."""

# Registro de todos os padrões pré-definidos (imutável)
ALL_STANDARDS: FrozenSet[VoltageStandard] = frozenset(
    {NBR_5410, PRODIST_MODULE8_BT, PRODIST_MODULE8_MT, LIGHT_BT, ENEL_BT}
)
"""Conjunto imutável de todos os padrões regulatórios pré-definidos."""


def get_standard_by_name(name: str) -> Optional[VoltageStandard]:
    """Busca um padrão pré-definido pelo nome.

    Args:
        name: Nome exato do padrão (case-sensitive).

    Returns:
        O ``VoltageStandard`` correspondente, ou ``None`` se não encontrado.

    Example:
        >>> std = get_standard_by_name("NBR 5410")
        >>> std.max_drop_percent
        5.0
    """
    return next((s for s in ALL_STANDARDS if s.name == name), None)
