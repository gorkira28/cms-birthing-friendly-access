CREATE OR REPLACE TABLE hospital_clean AS
SELECT
    LPAD(TRIM("Facility ID"), 6, '0') AS facility_id,
    TRIM("Facility Name") AS facility_name,
    TRIM("Address") AS address,
    TRIM("City/Town") AS city,
    UPPER(TRIM("State")) AS state,
    LPAD(TRIM("ZIP Code"), 5, '0') AS zip_code,
    TRIM("County/Parish") AS county,
    TRIM("Hospital Type") AS hospital_type,
    TRIM("Hospital Ownership") AS hospital_ownership,
    CASE WHEN UPPER(TRIM("Meets criteria for birthing friendly designation")) = 'Y'
         THEN 1 ELSE 0 END AS birthing_friendly,
    CASE
      WHEN "Hospital overall rating" IN ('1','2','3','4','5')
      THEN CAST("Hospital overall rating" AS INTEGER)
      ELSE NULL
    END AS hospital_overall_rating
FROM read_csv_auto(getvariable('cms_csv'), all_varchar = true, header = true);

CREATE OR REPLACE TABLE designated_hospitals AS
SELECT *
FROM hospital_clean
WHERE birthing_friendly = 1;

CREATE OR REPLACE TABLE state_designation_counts AS
SELECT
    state,
    COUNT(*) AS designated_hospitals,
    SUM(CASE WHEN hospital_type = 'Critical Access Hospitals' THEN 1 ELSE 0 END) AS designated_cah,
    SUM(CASE WHEN hospital_type = 'Acute Care Hospitals' THEN 1 ELSE 0 END) AS designated_acute,
    COUNT(DISTINCT facility_id) AS distinct_facilities
FROM designated_hospitals
GROUP BY state;

