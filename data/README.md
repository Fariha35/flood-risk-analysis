# Data Guide — Sylhet Flood Susceptibility Analysis

## Study Area

This project uses **Sylhet Division, Bangladesh** as the case-study region. Sylhet Division contains four districts: **Sylhet, Sunamganj, Habiganj, and Moulvibazar**.

The analysis is designed as a reproducible, research-oriented flood-susceptibility workflow. The repository will not use fabricated flood observations or invented performance results. All model targets and predictors must come from documented public datasets or from transformations of those datasets.

## Research Objective

The first implementation will estimate **historical flood susceptibility in Sylhet Division** by relating observed historical inundation patterns to terrain, rainfall, river proximity, and land-cover variables.

The main questions are:

1. Which areas of Sylhet Division have experienced the highest historical inundation frequency?
2. Which terrain, rainfall, river-proximity, and land-cover variables are most strongly associated with historical flooding?
3. How well can supervised machine-learning models distinguish locations with higher and lower historical flood susceptibility?
4. How sensitive are model results to spatial validation and predictor resolution?

## Target Analysis Grid

The main modelling grid will use **500 m cells** because the primary historical inundation dataset is supplied at 500 m resolution. Higher-resolution predictors will be aggregated to this grid rather than treated as if they provide 500 m-independent observations.

Native source resolution will always be recorded in metadata. Resampling a coarse dataset to 500 m does **not** create new spatial information.

## Dataset Manifest

### 1. Sylhet Division Boundary

**Purpose:** Clip all source datasets to the study area.

- Source authority: Bangladesh administrative boundary data published through a Bangladesh government GIS service and attributed to Bangladesh Bureau of Statistics (BBS)
- Administrative level: ADM1 / Division
- CRS: EPSG:4326 in the published service
- Target feature: Sylhet Division
- Expected local output: `data/raw/boundaries/sylhet_division.geojson`

Government GIS service:
https://gis.dghs.gov.bd/server/rest/services/Hosted/bgd_admbnda_adm1_bbs_20201113/FeatureServer

BBS geospatial portal:
https://ecds.bbs.gov.bd/

### 2. Historical Flood / Inundation Target

**Primary target dataset:** Bangladesh weekly flood maps developed by the Tellman research group.

- Spatial coverage: Bangladesh
- Temporal coverage: 2001–2022
- Temporal frequency: weekly
- Spatial resolution: 500 m
- Pixel value: fractional inundated area
- Method basis: fusion of MODIS and Sentinel-1 observations
- Use in this project: derive historical inundation frequency/intensity for Sylhet Division and construct the modelling target
- Expected local directory: `data/raw/flood/`

Dataset description and access:
https://beth-tellman.github.io/datasets.html

Associated research paper:
Giezendanner, J. et al. *Inferring the past: a combined CNN–LSTM deep learning framework to fuse satellites for historical inundation mapping.*
https://arxiv.org/abs/2305.00640

**Secondary validation/reference source:** Global Flood Database (GFD) v1.

- 913 mapped flood events
- Period: 2000–2018
- Event-level flood extent and duration information
- Access: Google Earth Engine and downloadable GeoTIFF resources
- Use in this project: independent historical reference and sensitivity checks where coverage overlaps Sylhet

Earth Engine catalog:
https://developers.google.com/earth-engine/datasets/catalog/GLOBAL_FLOOD_DB_MODIS_EVENTS_V1

Source code/data repository:
https://github.com/cloudtostreet/MODIS_GlobalFloodDatabase

### 3. Rainfall

**Dataset:** CHIRPS v3

- Provider: Climate Hazards Center, University of California, Santa Barbara
- Coverage: 60°N–60°S, all longitudes
- Temporal coverage: 1981 to near-present
- Native spatial resolution: 0.05°
- Variable: precipitation
- Use in this project: rainfall climatology, seasonal rainfall, extreme-rainfall indicators, and/or time-window rainfall summaries aligned with the flood observations
- Expected local directory: `data/raw/rainfall/`

Official source:
https://www.chc.ucsb.edu/data/chirps3

**Important:** CHIRPS is much coarser than the 500 m modelling grid. It will be resampled only for raster alignment, while its native resolution will remain documented and considered during interpretation.

### 4. Digital Elevation Model

**Dataset:** Copernicus DEM GLO-30

- Provider: Copernicus Data Space Ecosystem
- Approximate native grid spacing: 30 m
- Use in this project: elevation and terrain derivatives such as slope
- Processing: clip to Sylhet, calculate terrain derivatives at native resolution, then aggregate relevant statistics to the 500 m modelling grid
- Expected local directory: `data/raw/dem/`

Official documentation:
https://documentation.dataspace.copernicus.eu/APIs/SentinelHub/Data/DEM.html

### 5. River Network

**Dataset:** HydroRIVERS v1

- Provider: HydroSHEDS
- Data type: vector river network
- Extraction basis: HydroSHEDS hydrography
- Inclusion rule: river reaches with catchment area of at least 10 km² and/or average discharge of at least 0.1 m³/s
- Use in this project: distance to river, river density, and hydrologic proximity variables
- Expected local directory: `data/raw/hydrology/`

Official source:
https://www.hydrosheds.org/products/hydrorivers

### 6. Land Cover

**Primary historical land-cover dataset:** MODIS MCD12Q1 Version 6.1

- Provider: NASA
- Temporal frequency: yearly
- Native spatial resolution: 500 m
- Product: MODIS/Terra+Aqua Land Cover Type Yearly L3 Global 500 m
- Use in this project: temporally compatible land-cover information for the historical analysis
- Expected local directory: `data/raw/landcover/`

NASA product page:
https://ladsweb.modaps.eosdis.nasa.gov/missions-and-measurements/products/MCD12Q1

NASA data catalog:
https://data.nasa.gov/dataset/modis-terraaqua-land-cover-type-yearly-l3-global-500m-sin-grid-v061-fac3a

**Optional high-resolution contextual layer:** ESA WorldCover 2021 (10 m). This layer may be used for map visualization or a sensitivity analysis, but it will not silently replace historical land cover because doing so would introduce temporal mismatch across the 2001–2022 flood record.

Official source:
https://esa-worldcover.org/en/data-access

## Planned Derived Variables

The first model-ready table is expected to contain variables such as:

| Group | Candidate variable | Derivation |
|---|---|---|
| Target | historical inundation frequency | fraction/count of historical weeks with inundation above a documented threshold |
| Target | mean/maximum fractional inundation | aggregation of weekly flood-map values |
| Terrain | elevation | Copernicus DEM aggregated to 500 m |
| Terrain | slope | derived from DEM, then aggregated |
| Hydrology | distance to nearest river | distance from grid-cell centroid to HydroRIVERS network |
| Hydrology | river density | river length within a defined neighbourhood |
| Rainfall | mean monsoon rainfall | CHIRPS aggregation |
| Rainfall | extreme-rainfall statistic | CHIRPS percentile/max-based metric |
| Land cover | land-cover class | MODIS MCD12Q1 yearly or period-representative encoding |

The exact final feature set will be fixed only after the source files have been acquired and validated.

## Data Folder Policy

```text
data/
├── README.md
├── raw/
│   ├── boundaries/
│   ├── flood/
│   ├── rainfall/
│   ├── dem/
│   ├── hydrology/
│   └── landcover/
├── interim/
└── processed/
```

### `raw/`
Original downloaded data or study-area extracts. Raw files must not be manually edited after acquisition.

### `interim/`
Intermediate outputs such as clipped rasters, reprojected layers, aligned grids, and temporary feature layers.

### `processed/`
Final model-ready tables/rasters generated reproducibly from code.

## Git and Redistribution Rules

Large geospatial rasters will generally **not** be committed directly to GitHub. Instead, this repository will contain:

- source documentation
- acquisition scripts where practical
- checksums/metadata where useful
- preprocessing code
- small derived samples when redistribution permits
- final lightweight metrics, figures, and maps

Every source must be reviewed for its own license and redistribution conditions before raw files are committed.

## Reproducibility Requirements

For every dataset used in an executed experiment, record:

1. dataset name and version
2. source/provider
3. download or access date
4. native CRS
5. native spatial resolution
6. temporal coverage
7. study-area clipping method
8. resampling/aggregation method
9. NoData handling
10. output filename
11. license/attribution requirement

## Current Status

- Study area selected: **Sylhet Division, Bangladesh**
- Repository foundation: initialized
- Data directories: initialized
- Dataset sources: identified
- Raw data acquisition: **not yet executed**
- Model training: **not yet executed**
- Quantitative results: **not yet generated**

No performance metric or scientific conclusion should be added to the repository until it is produced by an executed and reproducible analysis.
