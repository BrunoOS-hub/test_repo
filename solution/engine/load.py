"""Carrega e limpa as 4 tabelas do CRM. Sem lógica de score aqui."""
import pandas as pd

from .config import DATA_DIR

PRODUCT_FIXES = {"GTXPro": "GTX Pro"}  # pipeline usa "GTXPro", catálogo usa "GTX Pro"


def load(data_dir=DATA_DIR) -> pd.DataFrame:
    """Retorna o pipeline enriquecido (1 linha por oportunidade)."""
    p = pd.read_csv(data_dir / "sales_pipeline.csv", parse_dates=["engage_date", "close_date"])
    accounts = pd.read_csv(data_dir / "accounts.csv")
    products = pd.read_csv(data_dir / "products.csv")
    teams = pd.read_csv(data_dir / "sales_teams.csv")

    p["product"] = p["product"].replace(PRODUCT_FIXES)
    df = (
        p.merge(products, on="product", how="left", validate="many_to_one")
        .merge(teams, on="sales_agent", how="left", validate="many_to_one")
        .merge(accounts[["account", "sector", "revenue", "employees"]], on="account", how="left")
    )
    if df["sales_price"].isna().any():
        missing = sorted(df.loc[df["sales_price"].isna(), "product"].unique())
        raise ValueError(f"Produtos sem preço no catálogo: {missing}")
    df["is_closed"] = df["deal_stage"].isin(["Won", "Lost"])
    df["won"] = (df["deal_stage"] == "Won").astype(int)
    return df


def max_cycle(df: pd.DataFrame) -> int:
    """Maior duração (engage → close) entre deals concluídos."""
    closed = df[df["is_closed"]]
    return int((closed["close_date"] - closed["engage_date"]).dt.days.max())


def data_audit(df: pd.DataFrame, as_of: str) -> dict:
    """Fatos de qualidade de dados que o gestor precisa saber."""
    ref = pd.Timestamp(as_of)
    open_ = df[~df["is_closed"]]
    eng = open_[open_["deal_stage"] == "Engaging"]
    wall = max_cycle(df)
    return {
        "deals_total": len(df),
        "open_deals": len(open_),
        "engaging": len(eng),
        "prospecting": int((open_["deal_stage"] == "Prospecting").sum()),
        "open_without_account": int(open_["account"].isna().sum()),
        "prospecting_without_engage_date": int(open_["engage_date"].isna().sum()),
        "max_closed_cycle_days": wall,
        "engaging_beyond_wall": int(((ref - eng["engage_date"]).dt.days > wall).sum()),
        "win_rate_closed": round(df.loc[df["is_closed"], "won"].mean(), 4),
        "product_name_fixes": PRODUCT_FIXES,
    }
