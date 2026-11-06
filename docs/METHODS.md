# Methods

## Research question

How does the number of CMS Birthing-Friendly designated hospitals vary across states after standardizing by the 2025 civilian female population ages 15–44, and how does Critical Access Hospital participation relate to that density?

## Study design and unit of analysis

This is a cross-sectional, ecological analysis. Hospitals are identified by six-character CMS Certification Number (CCN). The primary analytic unit is the state (50 states and Washington, D.C.). Puerto Rico is shown in the source reconciliation but excluded from the standardized analysis because the selected Census state population file covers the 50 states and D.C.

## Data sources

1. **CMS Hospital General Information**, modified July 22, 2026 and released August 13, 2026. The analytic field is `Meets criteria for birthing friendly designation`; `Y` is treated as designated. Blank values are not recoded as “No” for interpretation.
2. **Census Vintage 2025 civilian population estimates by single year of age and sex.** Female (`SEX=2`) ages 15 through 44 were summed within state.
3. **Census 2025 cartographic boundary file**, 1:20m state layer, for visualization only.

## Processing

1. Import CMS data as character fields to preserve leading zeros in CCNs and ZIP codes.
2. Trim text, normalize state abbreviations, and create a binary designation indicator only for `Y`.
3. Verify one row per designated CCN and aggregate designated hospitals by state and hospital type.
4. Sum 2025 civilian female population ages 15–44 by state.
5. Left-join hospital counts to all 50 states plus D.C. and calculate:

   `designated hospitals / female population ages 15–44 × 100,000`

6. Calculate exact two-sided 95% Poisson confidence intervals for each state count.
7. Use Spearman rank correlation for (a) state population vs. designation count and (b) designation density vs. the Critical Access Hospital share.
8. Join results to Census boundaries and export GeoJSON for QGIS.

## Statistical choices

- Exact Poisson intervals describe count uncertainty but do not capture data-quality or model uncertainty.
- Spearman correlation was chosen because relationships are monotonic and state values are not assumed normally distributed.
- Quartiles are descriptive, with 51 jurisdictions split by `pandas.qcut`; they are not policy thresholds.
- No causal claims or individual-level inferences are made.

## QA/QC

- CMS row count checked against the catalog: 5,419.
- Designated CCNs must be unique.
- State table must contain exactly 51 unique jurisdictions.
- State counts must equal distinct CCN counts.
- All denominators must be positive and all calculated rates finite.
- The 50-state-plus-D.C. total plus Puerto Rico must reconcile to the full designated count.
- Source byte sizes and SHA-256 hashes are saved in `outputs/tables/source_manifest.csv`.
- Automated tests reconcile the state table, JSON summary, map, and figures.

