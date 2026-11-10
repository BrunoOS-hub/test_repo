import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine import brief as BR  # noqa: E402
from engine.load import load  # noqa: E402
from engine.score import score_open  # noqa: E402


@pytest.fixture(scope="module")
def df():
    return load()


@pytest.fixture(scope="module")
def sc(df):
    return score_open(df)


def test_every_brief_number_comes_from_the_engine(sc):
    for agent in sc["sales_agent"].unique():
        me = sc[sc["sales_agent"] == agent]
        text = BR.build_brief(agent, sc)
        assert BR.validate_numbers(text, BR.engine_numbers(me, sc)) == [], agent


def test_validate_numbers_flags_invented_number(sc):
    agent = "Zane Levy"
    me = sc[sc["sales_agent"] == agent]
    text = BR.build_brief(agent, sc).replace("Bom dia", "Você vai fechar US$ 9.999. Bom dia", 1)
    assert "9.999" in BR.validate_numbers(text, BR.engine_numbers(me, sc))


def test_deal_codes_are_not_read_as_numbers():
    assert BR.extract_numbers("cód 4D0K5T7T e cód 01XZ9CRY") == []


def test_brief_omits_empty_sections(sc):
    qualify_only = sc[sc["queue"] == "Qualificar"]["sales_agent"].unique()
    no_qualify = [a for a in sc["sales_agent"].unique() if not (sc[(sc["sales_agent"] == a) & (sc["queue"] == "Qualificar")]).shape[0]]
    assert len(qualify_only) and len(no_qualify)
    assert "Qualificar" not in BR.build_brief(no_qualify[0], sc)
    assert "Qualificar" in BR.build_brief(qualify_only[0], sc)


def test_agent_summary_alive_matches_agir_queue(sc):
    s = BR.agent_summary(sc)
    assert s["alive"].sum() == (sc["queue"] == "Agir").sum()
    assert s["decide_count"].sum() == (sc["queue"] == "Decidir").sum()
    assert s["qualify_count"].sum() == (sc["queue"] == "Qualificar").sum()
    assert BR.manager_summary(sc)["alive"].sum() == s["alive"].sum()


def test_export_writes_parseable_data_js(df):
    import run

    run.cmd_export(df, [])
    text = (Path(run.APP) / "data.js").read_text()
    prefix = "window.SCORES = "
    assert text.startswith(prefix)
    data = json.loads(text[len(prefix):].rstrip().rstrip(";"))
    assert {"as_of", "wall_days", "curve", "audit", "backtest", "agents", "managers", "deals"} <= set(data)
    assert all(a["brief"].startswith("Bom dia") for a in data["agents"])
    assert data["totals"]["alive"] == sum(a["alive"] for a in data["agents"])
