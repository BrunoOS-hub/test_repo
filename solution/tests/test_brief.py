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


def test_extract_numbers_reads_positions_money_and_percent():
    assert BR.extract_numbers("*1) GTX Pro · X*\nUS$ 2.239 esperados · 41% em 90 dias\n*avancei 1*") == ["1", "2.239", "41%", "90", "1"]


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


def test_brief_has_no_placeholder_and_no_deal_code_in_text(sc):
    for agent in sc["sales_agent"].unique():
        text = BR.build_brief(agent, sc)
        assert "{" not in text and "}" not in text, agent
        for oid in sc[sc["sales_agent"] == agent]["opportunity_id"]:
            assert oid not in text, (agent, oid)  # I/1 e O/0 confundem na digitação


def test_whatsapp_format_has_no_leading_space_or_auto_list(sc):
    import re

    texts = [BR.build_brief(a, sc) for a in sc["sales_agent"].unique()]
    texts += [BR.build_manager_digest(m, sc) for m in sc["manager"].unique()]
    for text in texts:
        for line in text.split("\n"):
            assert not line.startswith(" "), repr(line)
            assert not re.match(r"\d+\. ", line), repr(line)  # "1. " vira lista automática no WhatsApp
        assert "\n\n\n" not in text and not text.endswith("\n")


def test_brief_blocks_are_separated_by_blank_lines(sc):
    text = BR.build_brief("Zane Levy", sc)
    blocks = text.split("\n\n")
    assert blocks[0].startswith("Bom dia, Zane!") and "(base 31/12/2017)" in blocks[0]
    assert blocks[1].startswith("🎯 *Agir*: 5 de ")
    assert [b.split(")")[0] for b in blocks[2:7]] == [f"*{i}" for i in range(1, 6)]
    assert all(len(b.split("\n")) == 3 and b.split("\n")[2].startswith("→ ") for b in blocks[2:7])
    assert blocks[7].startswith("🧹 *Decidir*")
    assert blocks[-1] == "Responda com a ação + o número do deal:\n*avancei 1* · *perdi 1* · *adiar 1*"


def test_brief_last_line_quotes_avancei_1(sc):
    for agent in sc["sales_agent"].unique():
        assert BR.build_brief(agent, sc).split("\n")[-1] == "*avancei 1* · *perdi 1* · *adiar 1*", agent


def test_agent_without_agir_numbers_the_decidir_deal(sc):
    sem_agir = [a for a in sc["sales_agent"].unique() if not ((sc["sales_agent"] == a) & (sc["queue"] == "Agir")).any()]
    assert sem_agir  # na base atual há 6
    for agent in sem_agir:
        deals = BR.brief_deals(agent, sc)
        r = sc[sc["opportunity_id"] == deals[0]["opportunity_id"]].iloc[0]
        assert len(deals) == 1 and r["queue"] == "Decidir"
        assert f"Comece por: *1) {r['product']} · {BR._account(r)}*." in BR.build_brief(agent, sc)


def test_brief_deals_map_positions_to_real_ids(sc):
    ids = set(sc["opportunity_id"])
    for agent in sc["sales_agent"].unique():
        deals = BR.brief_deals(agent, sc)
        n = min(5, int(((sc["sales_agent"] == agent) & (sc["queue"] == "Agir")).sum())) or 1
        assert [d["pos"] for d in deals] == list(range(1, n + 1)), agent
        assert all(d["opportunity_id"] in ids for d in deals)
        # a posição N do texto é o deal N de "deals": produto e conta batem
        text = BR.build_brief(agent, sc)
        for d in deals:
            r = sc[sc["opportunity_id"] == d["opportunity_id"]].iloc[0]
            assert f"*{d['pos']}) {r['product']} · {BR._account(r)}*" in text


def test_brief_qualify_section_follows_block_pattern(sc):
    agent = sc[sc["queue"] == "Qualificar"]["sales_agent"].iloc[0]
    blocks = BR.build_brief(agent, sc).split("\n\n")
    assert any(b.startswith("🔎 *Qualificar*: ") and "\n" not in b for b in blocks)


def test_manager_digest_format(sc):
    m = sorted(sc["manager"].unique())[0]
    blocks = BR.build_manager_digest(m, sc).split("\n\n")
    assert blocks[0].startswith("Bom dia, ") and "(base 31/12/2017)" in blocks[0]
    assert blocks[1].startswith(("Antes de cobrar", "Base em ordem"))
    assert blocks[2] == "Top 3 por valor esperado:"
    for i, b in enumerate(blocks[3:6], 1):
        name, detail = b.split("\n")
        assert name.startswith(f"*{i}) ") and name.endswith("*")
        assert detail.startswith("US$ ") and detail.endswith(" parados") and " esperados · " in detail
    assert blocks[-1].startswith("Detalhes no app: https://")


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
    ids = {d["opportunity_id"] for d in json.loads((tmp_path / "scores.json").read_text())["deals"]}
    for a in b["agents"]:
        assert [d["pos"] for d in a["deals"]] == list(range(1, len(a["deals"]) + 1)) and a["deals"], a["agent"]
        assert all(d["opportunity_id"] in ids for d in a["deals"]), a["agent"]
        assert not any(d["opportunity_id"] in a["brief"] for d in a["deals"])
    for m in b["managers"]:
        assert BR.validate_numbers(m["digest"], set(m["allowed_numbers"])) == [], m["manager"]
        assert m["digest"].startswith("Bom dia, ") and "Detalhes no app: https://" in m["digest"]


def test_manager_digest_numbers_are_checked(sc):
    m = sorted(sc["manager"].unique())[0]
    text = BR.build_manager_digest(m, sc) + "\nMeta: US$ 8.888"
    assert BR.validate_numbers(text, BR.manager_numbers(m, sc)) == ["8.888"]
