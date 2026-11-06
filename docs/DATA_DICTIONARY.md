# Analytic data dictionary

## `outputs/tables/state_designation_density.csv`

| Field | Definition |
|---|---|
| `state_fips` | Two-character Census state FIPS code |
| `state_name` | Census state or district name |
| `female_15_44` | 2025 civilian female population ages 15–44 |
| `state` | Postal abbreviation |
| `designated_hospitals` | CMS rows with designation value `Y` |
| `designated_cah` | Designated facilities classified as Critical Access Hospitals |
| `designated_acute` | Designated facilities classified as Acute Care Hospitals |
| `distinct_facilities` | Distinct six-character CCNs; used for reconciliation |
| `designated_per_100k_female_15_44` | Designated count divided by population, scaled to 100,000 |
| `rate_ci_low`, `rate_ci_high` | Exact 95% Poisson interval for the standardized rate |
| `cah_share_pct` | Critical Access Hospitals as a percentage of designated hospitals |
| `density_quartile` | Descriptive quartile of state designation density |

## `data/processed/designated_hospitals.csv`

Contains public CMS facility identifiers, names, address fields, hospital type and ownership, designation flag, and overall rating. It contains no patient records, PHI, or proprietary Texas DSHS data.

## Important semantics

- `Y` means CMS reported that the hospital met criteria for the designation.
- A blank field is retained conceptually as “not recorded as Y,” not asserted to mean that the hospital failed the measure or does not provide obstetric care.
- The denominator is women ages 15–44 for transparent standardization. It is not the number of pregnancies, births, or people seeking maternity care.

