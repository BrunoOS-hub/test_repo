"""Backtest: voltar a segundas-feiras passadas, montar a lista de cada vendedor só com o que
se sabia naquele dia, e medir quanto da receita ganha nos 90 dias seguintes estava no topo.

Compara o score contra 4 jeitos de ordenar que um vendedor usaria sem a ferramenta.
"""
import numpy as np
import pandas as pd

from . import curve as C
from .config import HORIZON_DAYS
from .load import max_cycle
from .score import score_open

STRATEGIES = ["score", "valor", "mais_novo", "obvia", "sorteio"]


def _past_rates(df, s, col):
    """Win rate por categoria usando só deals fechados até s (com suavização)."""
    closed = df[df["is_closed"] & (df["close_date"] <= s)]
    base = closed["won"].mean()
    g = closed.groupby(col)["won"].agg(["sum", "count"])
    return ((g["sum"] + 20 * base) / (g["count"] + 20)).to_dict(), base


def rank_lists(df, s, k, rng):
    """Top-k por vendedor para cada estratégia, na data s. Só deals com engage_date."""
    sc = score_open(df, str(s.date()))
    sc = sc[sc["engage_date"].notna()].copy()
    # Estratégias concorrentes
    sc["k_score"] = np.where(sc["queue"] == "Agir", sc["expected_value"], -1)  # zumbis no fim
    sc["k_valor"] = sc["sales_price"]
    sc["k_mais_novo"] = -sc["age"]
    agent_wr, base = _past_rates(df, s, "sales_agent")
    prod_wr, _ = _past_rates(df, s, "product")
    sc["k_obvia"] = sc["sales_price"] * sc["sales_agent"].map(agent_wr).fillna(base) * sc["product"].map(prod_wr).fillna(base)
    sc["k_sorteio"] = rng.random(len(sc))
    picks = {}
    for st in STRATEGIES:
        top = sc.sort_values(f"k_{st}", ascending=False).groupby("sales_agent").head(k)
        picks[st] = set(top["opportunity_id"])
    return sc, picks


def run(df, start="2017-06-05", end=None, k=5, horizon=HORIZON_DAYS, seed=7):
    """Retorna (detalhe por data, resumo). end padrão: última segunda com resultado conhecido."""
    last_close = df["close_date"].max()
    end = pd.Timestamp(end) if end else last_close - pd.Timedelta(days=horizon)
    rng = np.random.default_rng(seed)
    rows = []
    for s in pd.date_range(start, end, freq="W-MON"):
        sc, picks = rank_lists(df, s, k, rng)
        h_end = s + pd.Timedelta(days=horizon)
        won = sc[(sc["deal_stage"] == "Won") & (sc["close_date"] <= h_end)]
        won_val = won.set_index("opportunity_id")["close_value"]
        total = won_val.sum()
        for st, ids in picks.items():
            cap = won_val[won_val.index.isin(ids)].sum()
            rows.append({"date": s.date(), "strategy": st, "captured": cap, "total_won": total, "share": cap / total if total else np.nan})
    detail = pd.DataFrame(rows)
    summary = (detail.groupby("strategy")
               .agg(captured=("captured", "sum"), total_won=("total_won", "sum"), weeks=("date", "nunique"))
               .assign(share=lambda d: d["captured"] / d["total_won"])
               .reindex(STRATEGIES))
    summary["vs_valor"] = summary["captured"] / summary.loc["valor", "captured"] - 1
    return detail, summary


def bootstrap_lift(detail, a="score", b="valor", n=2000, seed=11):
    """Intervalo de 90% para o ganho de a sobre b, reamostrando semanas."""
    piv = detail.pivot(index="date", columns="strategy", values="captured")
    rng = np.random.default_rng(seed)
    idx = np.arange(len(piv))
    lifts = []
    for _ in range(n):
        smp = piv.iloc[rng.choice(idx, len(idx))]
        lifts.append(smp[a].sum() / smp[b].sum() - 1)
    return np.percentile(lifts, [5, 50, 95])
