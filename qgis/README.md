# QGIS workflow

Open `birthing_friendly_state_rates.geojson` in QGIS 3.x.

1. Set the layer CRS to EPSG:4269 if QGIS does not read it automatically.
2. Use **Graduated** symbology on `designated_per_100k_female_15_44`.
3. Choose four quantile classes and a sequential `YlGnBu` palette.
4. Label states with `state` only at a national scale.
5. Add the title “CMS Birthing-Friendly designation density” and a note that the measure is structural, not a clinical ranking.

The GeoJSON includes the state count, denominator, rate, Poisson interval, Critical Access Hospital share, and descriptive quartile. The Python figure uses the same joined layer, so QGIS edits can be checked against `outputs/tables/state_designation_density.csv`.

