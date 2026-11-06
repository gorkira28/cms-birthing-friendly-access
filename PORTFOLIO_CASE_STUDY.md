# CMS Birthing-Friendly Designation Density

## The question

Where are CMS Birthing-Friendly designations most sparse after accounting for the population of women ages 15–44?

## What I built

I combined CMS Hospital General Information with Census Vintage 2025 age/sex estimates, used DuckDB SQL to clean and aggregate hospital records, calculated exact Poisson intervals in Python, and produced both a publication-ready map and a QGIS-ready GeoJSON.

## The finding

The 50 states and Washington, D.C. had 2,256 designated hospitals, equivalent to 3.33 per 100,000 women ages 15–44. State rates ranged from 2.01 in Nevada to 9.08 in Wyoming. Critical Access Hospitals made up 9.5% of designated facilities, and their state-level share was positively associated with designation density (Spearman rho 0.70).

## Why it matters

The analysis gives maternal-health planners a transparent first-pass screen for where deeper service-area review may be useful. It deliberately avoids calling the designation a safety ranking or treating state density as travel access.

## Skills demonstrated

DuckDB SQL · Python · GeoPandas · QGIS · statistical inference · data QA/QC · healthcare data interpretation

