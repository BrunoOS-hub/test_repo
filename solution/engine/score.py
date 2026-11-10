"""Score dos deals abertos numa data. Saída determinística: os números que o vendedor vê
(e que o texto da IA cita) saem daqui e de nenhum outro lugar."""
import pandas as pd

from . import curve as C
from .config import AS_OF
from .load import max_cycle

QUEUE_ORDER = {"Agir": 0, "Qualificar": 1, "Decidir": 2}


def score_open(df: pd.DataFrame, as_of: str = AS_OF, curve_df: pd.DataFrame | None = None) -> pd.DataFrame:
    ref = pd.Timestamp(as_of)
    wall = max_cycle(df[df["close_date"] <= ref]) if (df["close_date"] <= ref).any() else 138
    if curve_df is None:
        curve_df = C.fit_curve(C.snapshot_panel(df, as_of), wall)

    open_ = df[(df["engage_date"].isna() | (df["engage_date"] <= ref)) & (df["close_date"].isna() | (df["close_date"] > ref))].copy()
    open_["age"] = (ref - open_["engage_date"]).dt.days  # NaN para Prospecting sem data
    open_["chance_90d"] = 0.0
    has_age = open_["age"].notna()
    open_.loc[has_age, "chance_90d"] = C.chance(curve_df, open_.loc[has_age, "age"].to_numpy(), wall)
    open_["expected_value"] = (open_["sales_price"] * open_["chance_90d"]).round(0)
    open_["days_to_wall"] = (wall - open_["age"]).where(has_age)

    open_["queue"] = "Agir"
    open_.loc[~has_age, "queue"] = "Qualificar"
    open_.loc[has_age & (open_["age"] > wall), "queue"] = "Decidir"
    open_["missing_account"] = open_["account"].isna()

    open_["reason"] = open_.apply(lambda r: _reason(r, wall), axis=1)
    open_["action"] = open_.apply(lambda r: _action(r), axis=1)

    # Ordem: fila → valor esperado (Agir) ou preço (Qualificar/Decidir) → em Decidir, o que
    # passou da parede há menos tempo primeiro (é o mais recuperável).
    open_["_q"] = open_["queue"].map(QUEUE_ORDER)
    open_["_k"] = -open_["expected_value"].where(open_["queue"] == "Agir", open_["sales_price"])
    open_["_a"] = open_["age"].fillna(0)
    open_ = open_.sort_values(["_q", "_k", "_a", "opportunity_id"])
    open_["rank_in_agent"] = open_.groupby(["sales_agent", "queue"]).cumcount() + 1
    open_.attrs.update(wall_days=wall, as_of=str(ref.date()), curve=curve_df)
    return open_.drop(columns=["_q", "_k", "_a"])


def _money(x):
    return f"US$ {x:,.0f}".replace(",", ".")


def _reason(r, wall):
    if r["queue"] == "Qualificar":
        return f"Ainda em prospecção (sem data de início). Vale {_money(r['sales_price'])} a preço de lista."
    if r["queue"] == "Decidir":
        return f"Aberto há {int(r['age'])} dias; nenhum deal da base fechou depois de {wall} dias."
    return (f"{_money(r['sales_price'])} × {r['chance_90d']:.0%} de chance em 90 dias "
            f"(deals com {int(r['age'])} dias) = {_money(r['expected_value'])} esperados.")


def _action(r):
    if r["queue"] == "Qualificar":
        return "Fazer o primeiro contato e confirmar se há oportunidade."
    if r["queue"] == "Decidir":
        return "Confirmar com o cliente: reativar com data de decisão ou marcar como perdido."
    if r["days_to_wall"] <= 0:
        return "Pedir a decisão hoje: o deal chegou ao limite histórico de fechamento."
    if r["days_to_wall"] <= 30:
        return f"Pedir a decisão: faltam {int(r['days_to_wall'])} dias para o limite histórico."
    if r["age"] <= 14:
        return "Fase em que mais se perde: qualificar a necessidade e agendar a próxima reunião."
    return "Avançar para proposta e marcar data de decisão."
