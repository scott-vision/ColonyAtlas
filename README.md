# ColonyAtlas

**Interactive Morphology Analysis for Bacterial Colonies - AIEBaB 2026 Hackathon**

## Overview

**ColonyAtlas** is an end-to-end platform for automated, quantitative analysis of bacterial colony morphology from plate images. It combines modern computer vision models with an interactive web interface to enable both single-colony inspection and population-level phenotyping.

Users can upload single images or batches of plate images, automatically segment individual colonies, and explore results through an interactive dashboard where every colony is clickable, measurable, and auditable.

---

## Key Capabilities

- Automated colony detection and instance segmentation  
- High-quality mask generation (SAM-assisted or trained segmentation models)  
- Per-colony morphology quantification  
- Plate-level and dataset-level variability analysis  
- Interactive web-based exploration and plotting  
- Export-ready quantitative outputs (CSV / Parquet)

---


## High-Level Architecture

```text
+---------------------------+        REST / JSON         +---------------------------+
| Frontend (ColonyAtlas UI) |  <-----------------------> | Backend (FastAPI)         |
| - React / Next.js         |                            | - Upload & job control    |
| - Tailwind CSS            |                            | - Inference orchestration |
| - Image + mask overlay    |                            | - Feature extraction      |
| - Interactive plots       |                            | - Results API             |
+-------------+-------------+                            +-------------+-------------+
              |                                                        |
              |                                                        |
              |                                                        |
              v                                                        v
     +---------------------------+                          +---------------------------+
     | Browser state / UI events |                          | ML & Analysis Pipeline    |
     | - selected colony_id      |                          | - Detection               |
     | - active filters          |                          | - SAM box-prompt masks    |
     | - plot selections         |                          | - Instance segmentation   |
     +---------------------------+                          | - QC + post-processing    |
                                                            | - Morphology metrics     |
                                                            +-------------+-------------+
                                                                          |
                                                                          v
                                                            +---------------------------+
                                                            | Storage & Outputs         |
                                                            | - Images & overlays       |
                                                            | - Masks (per colony)      |
                                                            | - Tables (CSV/Parquet)    |
                                                            | - Embeddings (PCA/UMAP)   |
                                                            +---------------------------+



```
---

## Core Workflow

1. **Upload**
   - Single image or batch of images (folder or ZIP)
   - Optional metadata (experiment, condition, strain, replicate)

2. **Detection**
   - Object detection localises individual colonies

3. **Segmentation**
   - SAM box-prompted instance masks
   - Optional trained instance segmentation model for fast inference

4. **Post-processing & QC**
   - Artifact removal
   - Partial/border colony detection
   - Touching/merged colony flags

5. **Morphology Quantification**
   - Per-colony feature vectors computed

6. **Exploration & Export**
   - Interactive visualisation
   - CSV/Parquet export for downstream analysis

---

## Morphological Metrics

### Size Metrics

| Metric | Description |
|------|------------|
| Area | Colony area (px² or mm²) |
| Perimeter | Boundary length |
| Equivalent Diameter | Diameter of equal-area circle |
| Major Axis Length | Ellipse fit |
| Minor Axis Length | Ellipse fit |
| Bounding Box Area | Axis-aligned bounding box |

---

### Shape Metrics

| Metric | Description |
|------|------------|
| Circularity | 4πA / P² |
| Aspect Ratio | Major / Minor axis |
| Solidity | Area / convex hull area |
| Convexity | Convex hull perimeter / perimeter |
| Eccentricity | Ellipse eccentricity |
| Roughness | Perimeter / √Area |

---

### Spatial & Context Metrics

| Metric | Description |
|------|------------|
| Nearest Neighbour Distance | Local spacing |
| Local Density | Colonies per unit area |
| Edge Distance | Distance to plate edge |
| Touching Flag | Overlapping or merged colonies |

---

## Variability Quantification

ColonyAtlas quantifies within-plate and between-condition variability using:

- Mean and median
- Standard deviation
- Coefficient of variation (CV)
- IQR / MAD (robust spread)
- Quantile summaries (10/50/90%)

### Multivariate Morphology Space

- PCA for interpretable morphology axes
- UMAP for non-linear phenotypic clustering
- Distance-to-centroid as a variability score

---

## Web Application (ColonyAtlas UI)

### Main Views

1. Upload
2. Plate Overview
3. Analysis Dashboard

---

## Analysis Dashboard Layout

### Image Viewer (Left Panel)

- Plate image with colony overlays
- Hover to preview colony metrics
- Click to select a colony
- Toggle masks, IDs, and colouring modes
- Previous / Next colony navigation

---

### Colony Inspector (Right Panel)

- Mask preview of selected colony
- Detailed morphology metrics table
- QC flags and spatial context indicators

---

### Plot Panels

- Area distribution (histogram / KDE)
- Metric vs metric scatter plot (fully selectable axes)
- PCA / UMAP embedding view
- Plate spatial heatmap

---

### Interaction Rules

- Selection is global (viewer ↔ plots ↔ metrics)
- Every plotted point maps to a single colony
- QC flags are first-class filters and colour keys

---

## Data Outputs

results/
  plates/
    <plate_id>/
      images/
        original.png
        overlay.png
      masks/
        colony_<colony_id>.png
      tables/
        colonies.csv
        qc_flags.csv
        plate_summary.csv
      embeddings/
        pca.csv
        umap.csv
  index.csv



---

## Backend API (FastAPI)

| Endpoint | Description |
|-------|------------|
| POST /upload | Upload images |
| POST /analyze | Run analysis pipeline |
| GET /plates | List plates |
| GET /plate/{id} | Plate-level results |
| GET /colony/{id} | Colony-level metrics |
| GET /plots | Dynamic plot data |

- Async job handling
- GPU / CPU compatible
- Stateless, UI-driven API design

---

## Frontend Stack

- React / Next.js
- Tailwind CSS
- Plotly / D3 for analytics
- Canvas / SVG overlays for masks

---

## Model Strategy

### Phase 1

- Object detection
- SAM box-prompted masks

### Phase 2

- Trained instance segmentation (YOLO-seg / Mask R-CNN)
- SAM retained for fallback and label generation

---

## Use Cases

- Colony phenotype screening
- Growth and morphology variability analysis
- Mutant vs wild-type comparisons
- Antibiotic or stress-response assays
- Automated plating QC

---

## Future Extensions

- Time-series colony growth tracking
- Active learning for segmentation improvement
- Automated phenotype clustering
- LIMS integration
- Multi-plate comparative dashboards

---

## Summary

**ColonyAtlas** transforms raw colony images into quantitative, explorable morphology data, enabling rigorous biological insight through a single coherent platform.

## Development

See `docs/DEV.md` for local and Docker run instructions.
