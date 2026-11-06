from __future__ import annotations

import hashlib
import json
import shutil
import urllib.request
from pathlib import Path

import duckdb
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import chi2, spearmanr

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
TABLES = ROOT / "outputs" / "tables"
FIGURES = ROOT / "outputs" / "figures"

CMS_URL = (
    "https://data.cms.gov/provider-data/sites/default/files/resources/"
    "893c372430d9d71a1c52737d01239d47_1785189955/"
    "Hospital_General_Information.csv"
)
CENSUS_URL = (
    "https://www2.census.gov/programs-surveys/popest/datasets/2020-2025/"
    "state/asrh/sc-est2025-agesex-civ.csv"
)
SHAPE_URL = (
    "https://www2.census.gov/geo/tiger/GENZ2025/shp/"
    "cb_2025_us_state_20m.zip"
)

STATE_ABBR = {
    "01": "AL", "02": "AK", "04": "AZ", "05": "AR", "06": "CA", "08": "CO",
    "09": "CT", "10": "DE", "11": "DC", "12": "FL", "13": "GA", "15": "HI",
    "16": "ID", "17": "IL", "18": "IN", "19": "IA", "20": "KS", "21": "KY",
    "22": "LA", "23": "ME", "24": "MD", "25": "MA", "26": "MI", "27": "MN",
    "28": "MS", "29": "MO", "30": "MT", "31": "NE", "32": "NV", "33": "NH",
    "34": "NJ", "35": "NM", "36": "NY", "37": "NC", "38": "ND", "39": "OH",
    "40": "OK", "41": "OR", "42": "PA", "44": "RI", "45": "SC", "46": "SD",
    "47": "TN", "48": "TX", "49": "UT", "50": "VT", "51": "VA", "53": "WA",
    "54": "WV", "55": "WI", "56": "WY",
}


def ensure_dirs() -> None:
    for path in (RAW, PROCESSED, TABLES, FIGURES, ROOT / "qgis"):
        path.mkdir(parents=True, exist_ok=True)


def download(url: str, destination: Path) -> None:
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 portfolio-research"})
    with urllib.request.urlopen(request, timeout=120) as response, destination.open("wb") as out:
        shutil.copyfileobj(response, out)


def acquire_if_missing() -> None:
    sources = {
        RAW / "cms_hospital_general_2026-07-22.csv": CMS_URL,
        RAW / "census_state_age_sex_2025.csv": CENSUS_URL,
        RAW / "cb_2025_us_state_20m.zip": SHAPE_URL,
    }
    for path, url in sources.items():
        if not path.exists():
            download(url, path)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def poisson_rate_ci(count: int, denominator: int, scale: float = 100_000) -> tuple[float, float]:
    alpha = 0.05
    lower = 0 if count == 0 else 0.5 * chi2.ppf(alpha / 2, 2 * count)
    upper = 0.5 * chi2.ppf(1 - alpha / 2, 2 * (count + 1))
    return lower / denominator * scale, upper / denominator * scale


def build_hospital_tables() -> tuple[pd.DataFrame, pd.DataFrame]:
    con = duckdb.connect()
    con.execute("SET VARIABLE cms_csv = ?", [str(RAW / "cms_hospital_general_2026-07-22.csv")])
    sql = (ROOT / "sql" / "build_analytic_tables.sql").read_text(encoding="utf-8")
    con.execute(sql)
    designated = con.table("designated_hospitals").df()
    state_counts = con.table("state_designation_counts").df()
    con.close()
    return designated, state_counts


def build_population() -> pd.DataFrame:
    pop = pd.read_csv(RAW / "census_state_age_sex_2025.csv", dtype={"STATE": str})
    pop["STATE"] = pop["STATE"].str.zfill(2)
    # SEX=2 is female; ages 15 through 44 form the transparent denominator.
    pop = pop.loc[(pop["SEX"] == 2) & pop["AGE"].between(15, 44) & pop["STATE"].isin(STATE_ABBR)]
    result = (
        pop.groupby(["STATE", "NAME"], as_index=False)["POPEST2025_CIV"]
        .sum()
        .rename(columns={"STATE": "state_fips", "NAME": "state_name", "POPEST2025_CIV": "female_15_44"})
    )
    result["state"] = result["state_fips"].map(STATE_ABBR)
    return result


def create_state_results(state_counts: pd.DataFrame, population: pd.DataFrame) -> pd.DataFrame:
    result = population.merge(state_counts, on="state", how="left")
    for col in ["designated_hospitals", "designated_cah", "designated_acute", "distinct_facilities"]:
        result[col] = result[col].fillna(0).astype(int)
    result["designated_per_100k_female_15_44"] = (
        result["designated_hospitals"] / result["female_15_44"] * 100_000
    )
    intervals = [poisson_rate_ci(int(c), int(n)) for c, n in zip(result.designated_hospitals, result.female_15_44)]
    result["rate_ci_low"] = [x[0] for x in intervals]
    result["rate_ci_high"] = [x[1] for x in intervals]
    result["cah_share_pct"] = np.where(
        result["designated_hospitals"] > 0,
        result["designated_cah"] / result["designated_hospitals"] * 100,
        np.nan,
    )
    result["density_quartile"] = pd.qcut(
        result["designated_per_100k_female_15_44"], 4,
        labels=["Q1 lowest", "Q2", "Q3", "Q4 highest"],
    ).astype(str)
    return result.sort_values("designated_per_100k_female_15_44")


def create_figures(state: pd.DataFrame, designated: pd.DataFrame) -> None:
    plt.rcParams.update({"font.family": "DejaVu Sans", "axes.titleweight": "bold"})
    states = gpd.read_file(f"zip://{RAW / 'cb_2025_us_state_20m.zip'}")
    states = states.loc[states["STATEFP"].isin(STATE_ABBR)].copy()
    states["state"] = states["STATEFP"].map(STATE_ABBR)
    mapped = states.merge(state, on="state", how="left")
    mapped.to_file(ROOT / "qgis" / "birthing_friendly_state_rates.geojson", driver="GeoJSON")

    contiguous = mapped.loc[~mapped.state.isin(["AK", "HI"])].to_crs("EPSG:5070")
    fig, ax = plt.subplots(figsize=(13, 8), facecolor="#f7fafc")
    contiguous.plot(
        column="designated_per_100k_female_15_44", cmap="YlGnBu", linewidth=0.45,
        edgecolor="white", legend=True, ax=ax,
        legend_kwds={"label": "Designated hospitals per 100,000 women ages 15–44", "shrink": 0.68},
    )
    ax.set_axis_off()
    ax.set_title("CMS Birthing-Friendly designation density varies across states", loc="left", fontsize=19)
    ax.text(0, 0.97, "Structural designation counts standardized to 2025 Census female population; AK and HI shown in the ranked panel",
            transform=ax.transAxes, fontsize=10, color="#425466")
    fig.tight_layout()
    fig.savefig(FIGURES / "state_designation_density_map.png", dpi=180, bbox_inches="tight")
    plt.close(fig)

    ranked = pd.concat([state.head(10), state.tail(10)]).drop_duplicates().sort_values("designated_per_100k_female_15_44")
    colors = ["#ca5a5a" if q == "Q1 lowest" else "#167d92" for q in ranked["density_quartile"]]
    fig, ax = plt.subplots(figsize=(11, 8), facecolor="white")
    ax.barh(ranked["state"], ranked["designated_per_100k_female_15_44"], color=colors)
    ax.set_xlabel("Designated hospitals per 100,000 women ages 15–44")
    ax.set_title("Lowest- and highest-density states", loc="left", fontsize=17)
    ax.grid(axis="x", alpha=0.18)
    ax.spines[["top", "right", "left"]].set_visible(False)
    for i, value in enumerate(ranked["designated_per_100k_female_15_44"]):
        ax.text(value + 0.03, i, f"{value:.2f}", va="center", fontsize=9)
    fig.tight_layout()
    fig.savefig(FIGURES / "state_density_ranked.png", dpi=180, bbox_inches="tight")
    plt.close(fig)

    ownership = designated["hospital_ownership"].value_counts().head(7).sort_values()
    fig, ax = plt.subplots(figsize=(10, 6), facecolor="white")
    ax.barh(ownership.index, ownership.values, color="#2a6f97")
    ax.set_xlabel("Number of designated hospitals")
    ax.set_title("Ownership mix among designated hospitals", loc="left", fontsize=16)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.grid(axis="x", alpha=0.18)
    fig.tight_layout()
    fig.savefig(FIGURES / "ownership_mix.png", dpi=180, bbox_inches="tight")
    plt.close(fig)


def write_outputs(designated: pd.DataFrame, state: pd.DataFrame) -> None:
    designated.to_csv(PROCESSED / "designated_hospitals.csv", index=False)
    state.to_csv(TABLES / "state_designation_density.csv", index=False)
    state.head(10).to_csv(TABLES / "priority_review_states.csv", index=False)
    ownership = designated.groupby(["hospital_type", "hospital_ownership"], as_index=False).size()
    ownership.to_csv(TABLES / "designated_by_type_ownership.csv", index=False)
    quartiles = (
        state.groupby("density_quartile", as_index=False, observed=True)
        .agg(
            states=("state", "size"),
            median_rate=("designated_per_100k_female_15_44", "median"),
            median_cah_share_pct=("cah_share_pct", "median"),
        )
    )
    quartiles.to_csv(TABLES / "density_quartile_summary.csv", index=False)

    corr = spearmanr(state["female_15_44"], state["designated_hospitals"])
    cah_corr = spearmanr(state["designated_per_100k_female_15_44"], state["cah_share_pct"])
    national_count = int(state.designated_hospitals.sum())
    national_population = int(state.female_15_44.sum())
    results = {
        "cms_hospitals_total": int(len(pd.read_csv(RAW / "cms_hospital_general_2026-07-22.csv", dtype=str))),
        "designated_hospitals_50_states_dc": national_count,
        "designated_hospitals_all_cms_rows": int(len(designated)),
        "excluded_puerto_rico_designated": int((designated.state == "PR").sum()),
        "female_population_15_44_2025": national_population,
        "national_designated_per_100k_female_15_44": national_count / national_population * 100_000,
        "state_median_rate": float(state.designated_per_100k_female_15_44.median()),
        "lowest_state": state.iloc[0].state,
        "lowest_state_rate": float(state.iloc[0].designated_per_100k_female_15_44),
        "highest_state": state.iloc[-1].state,
        "highest_state_rate": float(state.iloc[-1].designated_per_100k_female_15_44),
        "designated_critical_access_hospitals": int(designated.hospital_type.eq("Critical Access Hospitals").sum()),
        "designated_critical_access_share_pct": float(
            designated.hospital_type.eq("Critical Access Hospitals").mean() * 100
        ),
        "spearman_population_count_rho": float(corr.statistic),
        "spearman_population_count_p": float(corr.pvalue),
        "spearman_density_cah_share_rho": float(cah_corr.statistic),
        "spearman_density_cah_share_p": float(cah_corr.pvalue),
    }
    (TABLES / "key_results.json").write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")

    source_rows = []
    for path, url in [
        (RAW / "cms_hospital_general_2026-07-22.csv", CMS_URL),
        (RAW / "census_state_age_sex_2025.csv", CENSUS_URL),
        (RAW / "cb_2025_us_state_20m.zip", SHAPE_URL),
    ]:
        source_rows.append({"file": path.name, "bytes": path.stat().st_size, "sha256": sha256(path), "source_url": url})
    pd.DataFrame(source_rows).to_csv(TABLES / "source_manifest.csv", index=False)


def validate(designated: pd.DataFrame, state: pd.DataFrame) -> None:
    assert designated["facility_id"].nunique() == len(designated), "Duplicate designated facility IDs"
    assert len(state) == 51, "Expected 50 states plus DC"
    assert set(state.state) == set(STATE_ABBR.values()), "Unexpected state coverage"
    assert (state.designated_hospitals == state.distinct_facilities).all(), "State duplicate facility IDs"
    assert (state.female_15_44 > 0).all(), "Non-positive denominator"
    assert state.designated_hospitals.sum() + (designated.state == "PR").sum() == len(designated)
    assert not state[["designated_per_100k_female_15_44", "rate_ci_low", "rate_ci_high"]].isna().any().any()


def main() -> None:
    ensure_dirs()
    acquire_if_missing()
    designated, state_counts = build_hospital_tables()
    population = build_population()
    state = create_state_results(state_counts, population)
    validate(designated, state)
    write_outputs(designated, state)
    create_figures(state, designated)
    print(json.dumps(json.loads((TABLES / "key_results.json").read_text()), indent=2))


if __name__ == "__main__":
    main()

