# Flood Risk Analysis

A reproducible geospatial and machine-learning workflow for flood susceptibility analysis and flood-risk-oriented mapping using terrain, hydrological, environmental, and rainfall-related variables.

> **Project status:** Under active development. Quantitative results will be reported only after the corresponding experiments have been executed and validated.

## Project Overview

Flooding is a major environmental hazard that can affect communities, infrastructure, agriculture, and ecosystems. This project develops a transparent and reproducible workflow for identifying flood-prone areas from spatial data and data-driven models.

The technical workflow is designed to combine:

- Digital Elevation Model (DEM) processing
- Terrain and hydrological feature extraction
- Rainfall-related variables
- Land-cover information
- Proximity-to-drainage features
- Machine-learning classification
- Model evaluation and interpretation
- Spatial prediction and mapping

### Terminology note

Strictly speaking, **flood risk** includes not only the probability or intensity of flooding, but also **exposure** and **vulnerability**. The initial modeling stage of this repository therefore focuses primarily on **flood susceptibility / flood occurrence probability**. Exposure and vulnerability layers can be integrated later if a complete risk assessment is required.

## Research Questions

1. Which geospatial, terrain, hydrological, and rainfall-related variables contribute most strongly to flood susceptibility prediction?
2. How accurately can supervised machine-learning models distinguish flood-prone from non-flood-prone locations, or estimate flood-susceptibility classes when an appropriate labeled dataset is available?
3. How does predictive performance change when different combinations of terrain, rainfall, land-cover, and proximity variables are used?
4. How strongly do validation results depend on the train-test strategy, particularly when spatial separation is used to reduce spatial leakage?
5. Can the final workflow generate interpretable and reproducible susceptibility maps suitable for further hydrological and environmental analysis?

## Core Workflow

```text
Raw Spatial Data
      |
      v
Data Validation and Cleaning
      |
      v
DEM and Terrain Processing
      |
      v
Hydrological Feature Extraction
      |
      v
Rainfall / Land-Cover / Proximity Features
      |
      v
Raster Alignment and Feature Engineering
      |
      v
Spatially Aware Train / Validation Split
      |
      v
Machine-Learning Models
      |
      v
Performance Evaluation
      |
      v
Model Interpretation and Error Analysis
      |
      v
Flood-Susceptibility Mapping
```

## Candidate Predictor Variables

The final feature set will depend on data availability and scientific relevance.

| Category | Candidate Variables |
|---|---|
| Terrain | elevation, slope, aspect |
| Hydrology | flow direction, flow accumulation, drainage density |
| Rainfall | rainfall intensity, accumulated precipitation |
| Surface characteristics | land cover, vegetation-related variables |
| Proximity | distance to rivers, streams, or drainage channels |
| Derived spatial features | topographic wetness-related indicators, normalized terrain metrics |

Every variable used in an experiment will be documented with its source, spatial resolution, coordinate reference system, preprocessing procedure, and role in the model.

## Modeling Strategy

The project is structured to compare multiple supervised-learning methods under a consistent preprocessing and validation framework.

Candidate models include:

- Logistic Regression as an interpretable baseline
- Random Forest
- Gradient-Boosted Trees
- Support Vector Machine

Model selection will be based on validated empirical performance, stability, interpretability, and suitability for the available dataset rather than on model complexity alone.

## Evaluation Strategy

Evaluation will be selected according to the final target definition and class distribution. Candidate metrics include:

- Precision
- Recall
- F1-score
- ROC-AUC
- PR-AUC when class imbalance is substantial
- Confusion matrix
- Balanced accuracy
- Cross-validation statistics
- Feature-importance or model-interpretation outputs

A major methodological concern is **spatial autocorrelation**. Randomly splitting nearby pixels or points can produce overly optimistic results because neighboring samples may be highly similar. For that reason, the project will prioritize **spatially separated holdout sets or spatial/block cross-validation** when the dataset supports them.

## Repository Structure

```text
flood-risk-analysis/
├── README.md
├── LICENSE
├── .gitignore
├── requirements.txt
├── data/
│   ├── raw/
│   ├── interim/
│   └── processed/
├── notebooks/
├── src/
│   ├── data/
│   ├── features/
│   ├── models/
│   └── visualization/
├── tests/
├── results/
│   ├── figures/
│   ├── metrics/
│   └── maps/
└── docs/
```

## Reproducibility Principles

The project is developed under the following reproducibility rules:

1. Raw source data remain separate from derived and processed data.
2. Data cleaning and feature engineering are performed through documented code.
3. Coordinate reference systems, raster resolution, spatial extent, and resampling choices are explicitly recorded.
4. Model parameters and random seeds are saved where applicable.
5. Evaluation metrics are generated programmatically.
6. Figures and maps are generated from saved analysis outputs.
7. No quantitative performance result is reported unless it comes from an executed experiment.
8. Large or redistribution-restricted datasets are not committed directly; instead, their sources and preparation instructions are documented.
9. Final evaluation data are kept separate from model-development decisions to reduce information leakage.

## Development Plan

### Stage 1: Project foundation

- Repository structure
- Environment configuration
- Data-validation utilities
- Reproducible preprocessing pipeline

### Stage 2: Geospatial preprocessing

- DEM loading and validation
- Coordinate-reference-system checks
- Terrain-variable generation
- Raster alignment and resampling
- Missing-data handling

### Stage 3: Hydrological feature engineering

- Flow-related variables
- Stream or drainage proximity
- Watershed-related spatial features
- Derived terrain-hydrology indicators

### Stage 4: Machine-learning experiments

- Interpretable baseline model
- Tree-based models
- Hyperparameter tuning
- Spatial validation
- Model comparison

### Stage 5: Interpretation and mapping

- Feature importance or model interpretation
- Error analysis
- Flood-susceptibility probability mapping
- Uncertainty and limitation assessment
- Reproducible final outputs

## Scientific Considerations

Flood-susceptibility modeling is sensitive to data quality, spatial resolution, class imbalance, temporal mismatch among datasets, label uncertainty, and validation design.

Special attention is therefore given to:

- avoiding target and spatial leakage
- using consistent coordinate reference systems
- checking raster resolution, extent, and alignment
- handling missing values explicitly
- documenting flood-label definitions
- evaluating class imbalance
- separating exploratory analysis from final evaluation
- distinguishing predictive association from physical causation
- reporting uncertainty and methodological limitations

## Installation

Clone or download the repository, open a terminal in the project directory, and create a virtual environment:

```bash
python -m venv .venv
```

Activate the environment, then install the project dependencies:

```bash
pip install -r requirements.txt
```

The exact dependency versions will be pinned in `requirements.txt` as the implementation is finalized.

## Usage

Executable scripts and notebooks will be documented as they are added. The goal is for each major processing step to be reproducible from code rather than relying on undocumented manual GIS operations.

## Results

Results will be added only after the experiments have been executed and checked. Planned outputs include:

- model-comparison tables
- confusion matrices
- ROC and precision-recall curves
- feature-importance or interpretation plots
- flood-susceptibility maps
- error-analysis summaries
- computational performance information

**No placeholder or fabricated accuracy values are reported in this repository.**

## Limitations

Expected limitations may include:

- uncertainty in flood-event labels
- incomplete temporal coverage
- differences in spatial resolution among source datasets
- spatial autocorrelation
- class imbalance
- temporal mismatch between predictor and target data
- limited transferability across geographic regions
- uncertainty introduced by preprocessing choices

The limitations section will be revised after the final dataset and experiments are established.

## Future Work

Possible extensions include:

- event-based flood forecasting
- temporal deep-learning models
- physically informed machine learning
- uncertainty quantification
- explainable AI for spatial predictions
- integration of exposure and vulnerability layers for full flood-risk assessment
- comparison across multiple watersheds or geographic regions

## Author

**Jeba Fariha Islam**

Research project in geospatial analysis, hydrology, environmental modeling, and machine learning.

## License

A license will be added before the repository is finalized for public reuse.
