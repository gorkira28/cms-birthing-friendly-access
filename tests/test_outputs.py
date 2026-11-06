import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def test_state_table_complete_and_unique():
    table = pd.read_csv(ROOT / "outputs" / "tables" / "state_designation_density.csv")
    assert len(table) == 51
    assert table["state"].is_unique
    assert table["female_15_44"].gt(0).all()
    assert table["designated_hospitals"].ge(0).all()


def test_key_results_reconcile():
    results = json.loads((ROOT / "outputs" / "tables" / "key_results.json").read_text())
    table = pd.read_csv(ROOT / "outputs" / "tables" / "state_designation_density.csv")
    assert results["designated_hospitals_50_states_dc"] == int(table.designated_hospitals.sum())
    assert results["designated_hospitals_all_cms_rows"] == (
        results["designated_hospitals_50_states_dc"] + results["excluded_puerto_rico_designated"]
    )


def test_map_and_figures_exist():
    expected = [
        ROOT / "qgis" / "birthing_friendly_state_rates.geojson",
        ROOT / "outputs" / "figures" / "state_designation_density_map.png",
        ROOT / "outputs" / "figures" / "state_density_ranked.png",
        ROOT / "outputs" / "figures" / "ownership_mix.png",
    ]
    assert all(path.exists() and path.stat().st_size > 1_000 for path in expected)

