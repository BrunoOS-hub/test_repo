"""Resumos por vendedor/manager e a pauta de segunda (texto de WhatsApp).

Tudo é determinístico: os números vêm do dataframe do score e nada é recalculado fora daqui.
`validate_numbers` serve para checar qualquer texto (inclusive o de um LLM, na F3): todo número
citado precisa ter sido produzido pelo motor.
"""
import re

import pandas as pd

from .config import HORIZON_DAYS

NO_ACCOUNT = "conta não cadastrada"
REPLY_LINE = "Responda: 1 {cód} = avancei · 2 {cód} = perdi · 3 {cód} = adiar"


def money(x) -> str:
    return f"US$ {x:,.0f}".replace(",", ".")


def _num(x) -> str:
    return f"{x:,.0f}".replace(",", ".")


def _account(r) -> str:
    return r["account"] if isinstance(r["account"], str) else NO_ACCOUNT


def _aggregate(g: pd.DataFrame) -> dict:
    agir = g[g["queue"] == "Agir"]
    decidir = g[g["queue"] == "Decidir"]
    return {
        "alive": int(len(agir)),
        "expected_value_sum": float(agir["expected_value"].sum()),
        "decide_count": int(len(decidir)),
        "decide_value": float(decidir["sales_price"].sum()),
        "qualify_count": int((g["queue"] == "Qualificar").sum()),
        "missing_account_count": int(g["missing_account"].sum()),
    }


def _summary(sc: pd.DataFrame, by: list[str]) -> pd.DataFrame:
    rows = [{**dict(zip(by, key if isinstance(key, tuple) else (key,))), **_aggregate(g)}
            for key, g in sc.groupby(by, sort=True)]
    return pd.DataFrame(rows)


def agent_summary(sc: pd.DataFrame) -> pd.DataFrame:
    """Uma linha por vendedor: manager, escritório regional e totais por fila."""
    return _summary(sc, ["sales_agent", "manager", "regional_office"])


def manager_summary(sc: pd.DataFrame) -> pd.DataFrame:
    """O mesmo agregado por manager."""
    return _summary(sc, ["manager", "regional_office"])


def region_summary(sc: pd.DataFrame) -> pd.DataFrame:
    """O mesmo agregado por escritório regional."""
    return _summary(sc, ["regional_office"])


def total_summary(sc: pd.DataFrame) -> dict:
    """Agregado da base inteira."""
    return _aggregate(sc)


def build_brief(agent: str, sc: pd.DataFrame, top: int = 5) -> str:
    """Pauta de segunda do vendedor em PT-BR. Seções vazias são omitidas."""
    me = sc[sc["sales_agent"] == agent]
    as_of = pd.Timestamp(sc.attrs["as_of"]).strftime("%d/%m/%Y")
    wall = sc.attrs["wall_days"]
    agir = me[me["queue"] == "Agir"].sort_values("rank_in_agent")
    decidir = me[me["queue"] == "Decidir"].sort_values("rank_in_agent")
    n_qualify = int((me["queue"] == "Qualificar").sum())

    first = agent.split()[0]
    lines = [f"Bom dia, {first}! Sua pauta da semana (base {as_of}):"]
    if len(agir):
        shown = agir.head(top)
        lines.append(f"🎯 *Agir*: {len(shown)} de {len(agir)} deals vivos")
        for i, (_, r) in enumerate(shown.iterrows(), 1):
            lines.append(f"{i}. {r['product']} · {_account(r)}")
            lines.append(f"   {money(r['expected_value'])} esperados ({r['chance_90d']:.0%} em 90 dias) → {r['action']}")
            lines.append(f"   cód {r['opportunity_id']}")
    if len(decidir):
        r = decidir.iloc[0]
        lines.append(f"🧹 *Decidir*: {len(decidir)} deals passaram de {wall} dias ({money(decidir['sales_price'].sum())} parados). "
                     f"Comece por: {r['product']} · {_account(r)} (cód {r['opportunity_id']}).")
    if n_qualify:
        lines.append(f"🔎 *Qualificar*: {n_qualify} deals sem primeiro contato.")
    lines.append(REPLY_LINE)
    text = "\n".join(lines)

    extra = validate_numbers(text, engine_numbers(me, sc, top))
    if extra:  # só acontece se o formato mudar sem atualizar a lista de números do motor
        raise ValueError(f"Brief de {agent} cita números que o motor não produziu: {extra}")
    return text


# ---- validação de números -------------------------------------------------

_CODE = re.compile(r"cód (?:\{cód\}|[A-Z0-9]+)")  # códigos de deal misturam letras e dígitos
_NUMBER = re.compile(r"(?<![\w.,/])\d+(?:[.,/]\d+)*%?(?![\w])")


def extract_numbers(text: str) -> list[str]:
    """Números citados no texto (dinheiro, %, datas, contagens). Códigos de deal são ignorados."""
    return _NUMBER.findall(_CODE.sub("cód", text))


def validate_numbers(text: str, allowed: set[str]) -> list[str]:
    """Números do texto que não estão em `allowed` (lista vazia = tudo veio do motor)."""
    return [n for n in extract_numbers(text) if n not in allowed]


def engine_numbers(me: pd.DataFrame, sc: pd.DataFrame, top: int = 5) -> set[str]:
    """Todo número que o motor produziu para este vendedor, já formatado como aparece no texto."""
    allowed = {str(i) for i in range(1, max(top, 3) + 1)}  # numeração da lista e opções 1/2/3
    allowed.add(pd.Timestamp(sc.attrs["as_of"]).strftime("%d/%m/%Y"))
    allowed.update([str(sc.attrs["wall_days"]), str(HORIZON_DAYS)])
    for q in ("Agir", "Qualificar", "Decidir"):
        part = me[me["queue"] == q]
        allowed.add(str(len(part)))
    allowed.add(_num(me.loc[me["queue"] == "Decidir", "sales_price"].sum()))
    for _, r in me.iterrows():
        allowed.update([_num(r["sales_price"]), _num(r["expected_value"]), f"{r['chance_90d']:.0%}"])
        for k in ("age", "days_to_wall"):
            if pd.notna(r[k]):
                allowed.add(str(int(r[k])))
        for k in ("product", "account"):  # "GTK 500" etc.
            if isinstance(r[k], str):
                allowed.update(re.findall(r"\d+", r[k]))
    return allowed
