import pandas as pd
import pytest
from backend.app.data import sec_client


@pytest.fixture
def fake_nav_cache(tmp_path, monkeypatch):
    nav_panel = tmp_path / "nav_panel.parquet"
    pd.DataFrame({
        "proj_id": ["A", "A", "B"],
        "nav_date": ["2024-01-02", "2024-01-01", "2024-01-01"],
        "nav_per_unit": [10.5, 10.0, 5.0],
    }).to_parquet(nav_panel, index=False)
    monkeypatch.setattr(sec_client, "NAV_PANEL_PATH", nav_panel)
    return nav_panel


def test_get_daily_nav_reads_local_cache_sorted_and_filtered_by_proj_id(fake_nav_cache):
    df = sec_client.get_daily_nav("A", "2024-01-01", "2024-01-02")
    assert list(df["nav_date"]) == list(pd.to_datetime(["2024-01-01", "2024-01-02"]))
    assert list(df["last_val"]) == [10.0, 10.5]
    assert set(df["proj_id"]) == {"A"}


def test_get_daily_nav_filters_by_date_range(fake_nav_cache):
    df = sec_client.get_daily_nav("A", "2024-01-02", "2024-01-02")
    assert len(df) == 1
    assert df.iloc[0]["last_val"] == 10.5


def test_get_daily_nav_returns_empty_frame_for_unknown_proj_id(fake_nav_cache):
    df = sec_client.get_daily_nav("does-not-exist", "2024-01-01", "2024-01-02")
    assert df.empty
    assert list(df.columns) == ["nav_date", "proj_id", "last_val"]


def test_get_daily_nav_returns_empty_frame_when_cache_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(sec_client, "NAV_PANEL_PATH", tmp_path / "does-not-exist.parquet")
    df = sec_client.get_daily_nav("A", "2024-01-01", "2024-01-02")
    assert df.empty


@pytest.fixture
def fake_fund_universe(tmp_path, monkeypatch):
    universe = tmp_path / "fund_universe.csv"
    pd.DataFrame([
        {"proj_id": "A", "fund_class_name": "main", "display_name": "Fund A",
         "amc_name_th": "AMC A", "policy_desc": "ตราสารทุน"},
        {"proj_id": "B", "fund_class_name": "main", "display_name": "Fund B",
         "amc_name_th": "AMC B", "policy_desc": "ตราสารหนี้"},  # wrong policy -- excluded
        {"proj_id": "C", "fund_class_name": "SCBCIO(A)", "display_name": "Fund C",
         "amc_name_th": "AMC C", "policy_desc": "ตราสารทุน"},  # not main class -- excluded
    ]).to_csv(universe, index=False)
    monkeypatch.setattr(sec_client, "FUND_UNIVERSE_PATH", universe)
    sec_client._load_fund_universe.cache_clear()
    yield universe
    sec_client._load_fund_universe.cache_clear()


def test_find_equity_funds_filters_policy_and_main_class(fake_fund_universe):
    funds = sec_client.find_equity_funds()
    assert [f["proj_id"] for f in funds] == ["A"]
    assert funds[0]["proj_name_th"] == "Fund A"
    assert funds[0]["comp_name_th"] == "AMC A"
    assert funds[0]["policy_desc"] == "ตราสารทุน"
