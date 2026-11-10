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


def test_export_writes_parseable_data_js(df, tmp_path, monkeypatch):
    import run

    monkeypatch.setattr(run, "OUT", tmp_path)  # não suja os arquivos versionados
    monkeypatch.setattr(run, "APP", tmp_path)
    run.cmd_export(df, [])
    text = (tmp_path / "data.js").read_text()
    prefix = "window.SCORES = "
    assert text.startswith(prefix)
    data = json.loads(text[len(prefix):].rstrip().rstrip(";"))
    assert {"as_of", "wall_days", "curve", "audit", "backtest", "agents", "managers", "deals"} <= set(data)
    assert all(a["brief"].startswith("Bom dia") for a in data["agents"])
    assert data["totals"]["alive"] == sum(a["alive"] for a in data["agents"])


def test_brief_has_no_placeholder_and_uses_real_code(sc):
    for agent in sc["sales_agent"].unique():
        me = sc[sc["sales_agent"] == agent]
        text = BR.build_brief(agent, sc)
        assert "{" not in text and "}" not in text, agent
        first = next(q for q in ("Agir", "Decidir", "Qualificar") if (me["queue"] == q).any())
        code = me[me["queue"] == first].sort_values("rank_in_agent").iloc[0]["opportunity_id"]
        assert f"*1 {code}* = avancei · *2 {code}* = perdi · *3 {code}* = adiar" in text


def test_brief_example_uses_decidir_when_agir_is_empty(sc):
    only_decidir = [a for a in sc["sales_agent"].unique()
                    if not ((sc["sales_agent"] == a) & (sc["queue"] == "Agir")).any()]
    if not only_decidir:  # na base atual todo vendedor tem Agir: testa com a fila Agir removida
        a = "Zane Levy"
        sub = sc[(sc["sales_agent"] == a) & (sc["queue"] != "Agir")]
        sub.attrs.update(sc.attrs)
        code = sub[sub["queue"] == "Decidir"].sort_values("rank_in_agent").iloc[0]["opportunity_id"]
        assert f"*1 {code}*" in BR.build_brief(a, sub)
    else:
        assert "*1 " in BR.build_brief(only_decidir[0], sc)


def test_team_headline_numbers_come_from_the_scope(sc):
    scopes = (BR.agent_summary(sc).to_dict("records") + BR.manager_summary(sc).to_dict("records")
              + BR.region_summary(sc).to_dict("records") + [BR.total_summary(sc)])
    for scope in scopes:
        text = BR.team_headline(scope)
        allowed = {BR._num(scope[k]) for k in ("decide_count", "decide_value", "missing_account_count")}
        assert BR.validate_numbers(text, allowed) == [], text
    # número inventado é acusado também aqui
    assert BR.validate_numbers(BR.team_headline(BR.total_summary(sc)) + " US$ 1.234", allowed) == ["1.234"]


def test_export_has_headline_per_scope(df):
    import run

    p = run.build_payload(df)
    for scope in p["agents"] + p["managers"] + p["regions"] + [p["totals"]]:
        assert scope["headline"].startswith(("Antes de cobrar", "Base em ordem"))
        assert scope["open_count"] == scope["alive"] + scope["decide_count"] + scope["qualify_count"]


def test_briefs_json_numbers_validate_and_file_is_small(df, tmp_path, monkeypatch):
    import run

    monkeypatch.setattr(run, "OUT", tmp_path)
    monkeypatch.setattr(run, "APP", tmp_path)
    run.cmd_export(df, [])
    raw = (tmp_path / "briefs.json").read_bytes()
    assert len(raw) < 200 * 1024
    b = json.loads(raw)
    assert {"as_of", "generated_at", "engine_commit", "agents", "managers"} <= set(b)
    assert len(b["agents"]) == 27 and len(b["managers"]) == 6
    for a in b["agents"]:
        assert BR.validate_numbers(a["brief"], set(a["allowed_numbers"])) == [], a["agent"]
    for m in b["managers"]:
        assert BR.validate_numbers(m["digest"], set(m["allowed_numbers"])) == [], m["manager"]
        assert m["digest"].startswith("Bom dia, ") and "Detalhes no app: https://" in m["digest"]


def test_manager_digest_numbers_are_checked(sc):
    m = sorted(sc["manager"].unique())[0]
    text = BR.build_manager_digest(m, sc) + "\nMeta: US$ 8.888"
    assert BR.validate_numbers(text, BR.manager_numbers(m, sc)) == ["8.888"]
