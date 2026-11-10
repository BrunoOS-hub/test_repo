"""CLI do motor.

  python run.py audit                 # fatos de qualidade dos dados
  python run.py curve                 # curva de chance por idade
  python run.py agent "Zane Levy"     # pauta de segunda de um vendedor
  python run.py backtest              # score vs. 4 alternativas em segundas passadas
  python run.py export                # gera outputs/scores.json e app/data.js (app e WhatsApp)
"""
import json
import sys
from pathlib import Path

import pandas as pd

from engine import backtest as B
from engine import brief as BR
from engine.config import AS_OF
from engine.load import data_audit, load
from engine.score import score_open

OUT = Path(__file__).resolve().parent / "outputs"
APP = Path(__file__).resolve().parent / "app"


def cmd_audit(df, _):
    print(json.dumps(data_audit(df, AS_OF), indent=2, ensure_ascii=False))


def cmd_curve(df, _):
    sc = score_open(df)
    print(f"Parede: {sc.attrs['wall_days']} dias | data de referência {sc.attrs['as_of']}")
    print(sc.attrs["curve"].to_string())


def cmd_agent(df, args):
    name = " ".join(args) or "Zane Levy"
    sc = score_open(df)
    me = sc[sc["sales_agent"] == name]
    if me.empty:
        sys.exit(f"Vendedor não encontrado ou sem deals: {name}")
    for q in ["Agir", "Qualificar", "Decidir"]:
        part = me[me["queue"] == q]
        print(f"\n== {q} ({len(part)}) ==")
        for _, r in part.head(5).iterrows():
            acc = r["account"] if isinstance(r["account"], str) else "conta não cadastrada"
            print(f"#{r['rank_in_agent']} {r['product']} · {acc} [{r['opportunity_id']}]")
            print(f"   {r['reason']}\n   → {r['action']}")


def cmd_backtest(df, _):
    detail, summary = B.run(df)
    pd.set_option("display.float_format", lambda x: f"{x:,.3f}")
    print(summary.to_string())
    lo, mid, hi = B.bootstrap_lift(detail)
    point = summary.loc["score", "vs_valor"]
    print(f"\nGanho do score sobre 'valor': {point:+.1%} (estimativa pontual; IC 90%: {lo:+.1%} a {hi:+.1%}; mediana do bootstrap {mid:+.1%})")
    OUT.mkdir(exist_ok=True)
    detail.to_csv(OUT / "backtest_detail.csv", index=False)
    summary.to_csv(OUT / "backtest_summary.csv")


def build_payload(df):
    """Tudo que o app e o WhatsApp consomem. Nenhum número nasce fora do motor."""
    sc = score_open(df)
    cols = ["opportunity_id", "sales_agent", "manager", "regional_office", "product", "account", "sector",
            "deal_stage", "queue", "rank_in_agent", "age", "days_to_wall", "sales_price", "chance_90d",
            "expected_value", "missing_account", "reason", "action"]
    out = sc[cols].copy()
    for c in ["age", "days_to_wall"]:
        out[c] = out[c].astype("Int64")

    detail, summary = B.run(df)
    lo, mid, hi = B.bootstrap_lift(detail)
    backtest = {
        "weeks": int(summary["weeks"].iloc[0]),
        "k": 5,
        "summary": summary.reset_index().to_dict(orient="records"),
        "lift_point": float(summary.loc["score", "vs_valor"]),
        "ci90": [float(lo), float(hi)],
    }

    agents = json.loads(BR.agent_summary(sc).to_json(orient="records"))
    for a in agents:
        a["brief"] = BR.build_brief(a["sales_agent"], sc)
    managers = json.loads(BR.manager_summary(sc).to_json(orient="records"))
    regions = json.loads(BR.region_summary(sc).to_json(orient="records"))
    totals = BR.total_summary(sc)
    for scope in agents + managers + regions + [totals]:  # recomendação do gestor, por escopo
        scope["headline"] = BR.team_headline(scope)
    return {
        "as_of": sc.attrs["as_of"],
        "wall_days": sc.attrs["wall_days"],
        "curve": sc.attrs["curve"].reset_index().rename(columns={"bin": "age_bin"}).to_dict(orient="records"),
        "audit": data_audit(df, AS_OF),
        "backtest": backtest,
        "agents": agents,
        "managers": managers,
        "regions": regions,
        "totals": totals,
        "deals": json.loads(out.to_json(orient="records")),
    }


def cmd_export(df, _):
    payload = build_payload(df)
    OUT.mkdir(exist_ok=True)
    (OUT / "scores.json").write_text(json.dumps(payload, ensure_ascii=False, indent=1, default=str))
    APP.mkdir(exist_ok=True)
    # data.js em vez de fetch: fetch não funciona em file:// (o app abre com duplo clique).
    compact = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), default=str)
    (APP / "data.js").write_text(f"window.SCORES = {compact};\n")
    print(f"{len(payload['deals'])} deals → {OUT / 'scores.json'} e {APP / 'data.js'}")


COMMANDS = {"audit": cmd_audit, "curve": cmd_curve, "agent": cmd_agent, "backtest": cmd_backtest, "export": cmd_export}

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "audit"
    if cmd not in COMMANDS:
        sys.exit(__doc__)
    COMMANDS[cmd](load(), sys.argv[2:])
