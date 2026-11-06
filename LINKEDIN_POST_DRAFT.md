# LinkedIn draft

**Formula:** F19 Anecdote-Meets-Evidence Bridge  
**Goal:** saves and thoughtful comments  
**Suggested posting window:** Tuesday–Thursday, 7:30–9:00 a.m. local time  
**Link placement:** first comment, not the post body

## Post

2,256 hospitals across the 50 states and Washington, D.C. carry the CMS Birthing-Friendly designation.

I wanted to know whether that count looked different after accounting for the size of the population most likely to use maternity services.

I joined CMS Hospital General Information with the Census Bureau's 2025 age and sex estimates, cleaned the facility records in DuckDB SQL, and built a GIS-ready state analysis in Python.

Three numbers stood out:

→ 3.33 designated hospitals per 100,000 women ages 15–44 nationally  
→ 2.01 in Nevada, the lowest state density  
→ 9.08 in Wyoming, the highest

Critical Access Hospitals represented 215 designated facilities. States with a larger Critical Access Hospital share also tended to have higher designation density (Spearman rho 0.70).

That pattern is useful for screening, but it is not a hospital safety ranking. The designation reflects a structural quality measure, and state density does not capture delivery volume, travel time, or local maternity-unit closures.

My next step would be a county-level travel-time analysis with birth volume and rurality.

Which additional measure would make this most useful for maternal-health planning?

#HealthcareAnalytics #MaternalHealth

## First comment

Project, code, methods, and QGIS-ready data: [GitHub repository link after publication]

