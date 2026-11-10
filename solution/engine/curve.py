"""Curva de chance: P(ganhar nos próximos H dias | idade do deal).

Estimada com "fotos" do pipeline em datas passadas. Em cada foto s, olhamos os deals
abertos naquele dia, a idade de cada um, e se ele foi ganho em (s, s+H].
Só usamos fotos cujo resultado já era conhecido na data de uso (s + H <= as_of),
então a curva nunca enxerga o futuro.
"""
import numpy as np
import pandas as pd

from .config import AGE_BINS, AGE_LABELS, HORIZON_DAYS, PRIOR_STRENGTH, SNAPSHOT_FREQ


def open_at(df: pd.DataFrame, s: pd.Timestamp) -> pd.DataFrame:
    """Deals com engage_date que estavam abertos no dia s."""
    m = df["engage_date"].notna() & (df["engage_date"] <= s) & (df["close_date"].isna() | (df["close_date"] > s))
    out = df.loc[m].copy()
    out["age"] = (s - out["engage_date"]).dt.days
    return out


def snapshot_panel(df: pd.DataFrame, as_of: str, horizon: int = HORIZON_DAYS) -> pd.DataFrame:
    """Painel (foto, deal, idade, ganhou_no_horizonte) só com fotos de resultado conhecido."""
    as_of = pd.Timestamp(as_of)
    last = as_of - pd.Timedelta(days=horizon)
    first = df["engage_date"].min()
    rows = []
    for s in pd.date_range(first, last, freq=SNAPSHOT_FREQ):
        o = open_at(df, s)
        if o.empty:
            continue
        end = s + pd.Timedelta(days=horizon)
        o["won_h"] = ((o["deal_stage"] == "Won") & (o["close_date"] <= end)).astype(int)
        o["snapshot"] = s
        rows.append(o[["opportunity_id", "snapshot", "age", "won_h"]])
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame(columns=["opportunity_id", "snapshot", "age", "won_h"])


def age_bin(age) -> pd.Series:
    return pd.cut(pd.Series(age), AGE_BINS, labels=AGE_LABELS)


def fit_curve(panel: pd.DataFrame, wall_days: int) -> pd.DataFrame:
    """Chance por faixa de idade, suavizada para a média global. Acima da parede = 0."""
    base = panel["won_h"].mean() if len(panel) else 0.0
    g = panel.assign(bin=age_bin(panel["age"]).values).groupby("bin", observed=False)["won_h"].agg(["sum", "count"])
    g["p"] = (g["sum"] + PRIOR_STRENGTH * base) / (g["count"] + PRIOR_STRENGTH)
    # Nenhum deal da base fechou depois da parede: a chance ali é zero por definição observada.
    g.loc["139+", "p"] = 0.0
    g["p"] = g["p"].round(4)
    return g.rename(columns={"sum": "wins", "count": "obs"})


def chance(curve: pd.DataFrame, age, wall_days: int) -> np.ndarray:
    a = pd.Series(age)
    p = age_bin(a).map(curve["p"]).astype(float)
    p[a > wall_days] = 0.0
    return p.to_numpy()
