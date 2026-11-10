import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine import curve as C  # noqa: E402
from engine.config import AS_OF, HORIZON_DAYS  # noqa: E402
from engine.load import data_audit, load  # noqa: E402
from engine.score import score_open  # noqa: E402


@pytest.fixture(scope="module")
def df():
    return load()


@pytest.fixture(scope="module")
def sc(df):
    return score_open(df)


def test_every_deal_has_price(df):
    assert df["sales_price"].notna().all()
    assert "GTXPro" not in set(df["product"])


def test_audit_matches_known_facts(df):
    a = data_audit(df, AS_OF)
    assert a["open_deals"] == 2089
    assert a["max_closed_cycle_days"] == 138
    assert a["engaging_beyond_wall"] == 1291
    assert a["open_without_account"] == 1425


def test_curve_never_sees_the_future(df):
    as_of = pd.Timestamp("2017-07-03")
    panel = C.snapshot_panel(df, str(as_of.date()))
    assert panel["snapshot"].max() + pd.Timedelta(days=HORIZON_DAYS) <= as_of


def test_beyond_wall_is_zero_and_goes_to_decidir(sc):
    beyond = sc[sc["age"] > sc.attrs["wall_days"]]
    assert len(beyond) > 0
    assert (beyond["chance_90d"] == 0).all()
    assert (beyond["queue"] == "Decidir").all()


def test_prospecting_goes_to_qualificar(sc):
    assert (sc.loc[sc["engage_date"].isna(), "queue"] == "Qualificar").all()


def test_expected_value_is_price_times_chance(sc):
    agir = sc[sc["queue"] == "Agir"]
    assert ((agir["sales_price"] * agir["chance_90d"]).round(0) == agir["expected_value"]).all()


def test_reason_quotes_the_engine_numbers(sc):
    r = sc[sc["queue"] == "Agir"].iloc[0]
    assert f"{r['chance_90d']:.0%}" in r["reason"]
    assert f"{r['expected_value']:,.0f}".replace(",", ".") in r["reason"]


def test_rank_is_sorted_within_agent(sc):
    agir = sc[sc["queue"] == "Agir"]
    for _, g in agir.groupby("sales_agent"):
        assert g.sort_values("rank_in_agent")["expected_value"].is_monotonic_decreasing
