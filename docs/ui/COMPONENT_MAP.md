# ColonyAtlas UI Component Map

React / Next.js + Tailwind

## Purpose

This document defines the frontend implementation blueprint for ColonyAtlas.
It specifies component boundaries, responsibilities, props, events, and backend interactions.

This file is intended to be read by:

- Frontend engineers
- LLMs implementing the UI from specification

---

## Suggested Frontend Folder Structure

frontend/
app/ (or pages/)
upload/
plates/
dashboard/[plateId]/
components/
layout/
AppShell.tsx
TopNav.tsx
Panel.tsx
upload/
UploadDropzone.tsx
UploadQueue.tsx
UploadMetadataForm.tsx
plates/
PlateGrid.tsx
PlateCard.tsx
PlateFilters.tsx
dashboard/
DashboardLayout.tsx
ImageViewer.tsx
ViewerToolbar.tsx
ViewerOverlayCanvas.tsx
ColonyInspector.tsx
MetricsTable.tsx
MaskPreview.tsx
MetricHistogram.tsx
MetricScatter.tsx
EmbeddingPlot.tsx
PlateHeatmap.tsx
ExportMenu.tsx
lib/
api.ts
types.ts
metrics.ts
qc.ts

---

## Global State (Single Source of Truth)

A global store (React Context, Zustand, Redux) MUST manage:

- activePlateId: string
- selectedColonyId: string | null
- filters:
  - qcFlags?: string[]
  - metricRanges?: Record<string, [number, number]>
- colourBy: 'id' | 'qc' | 'cluster' | 'condition'
- showMasks: boolean
- showIds: boolean
- xMetric: string
- yMetric: string

Rules:

- Selection changes propagate to viewer, inspector, and plots
- Hover does NOT modify global selection

---

## Core Type Definitions

Plate:

- id: string
- name: string
- created_at: string
- metadata?: key/value map
- image_url: string
- overlay_url?: string
- colony_count: number
- qc_summary: map of flag → count
- summary_stats: map of metric → value

Colony:

- id: string
- plate_id: string
- bbox: { x, y, w, h }
- centroid: { x, y }
- mask_url?: string
- metrics: map of metric → value
- qc_flags: string[]
- cluster_id?: string

---

## Page-Level Components

### Upload Page

UploadPage
Responsibilities:

- Own upload state and metadata
- Trigger backend analysis job

Renders:

- UploadDropzone
- UploadMetadataForm
- UploadQueue

Events:

- onFilesSelected(files)
- onStartAnalysis()

API:

- POST /upload
- POST /analyze

---

### Plate Overview Page

PlatesPage
Responsibilities:

- Fetch and display plate list
- Apply filters and sorting

Renders:

- PlateFilters
- PlateGrid
  - PlateCard

API:

- GET /plates

---

### Dashboard Page

DashboardPage (plateId)
Responsibilities:

- Fetch plate and colony data
- Coordinate global dashboard state

Renders:

- ImageViewer
- ColonyInspector
- MetricHistogram
- MetricScatter
- EmbeddingPlot
- PlateHeatmap
- ExportMenu

API:

- GET /plate/{plateId}
- GET /plate/{plateId}/colonies
- Optional: GET /plots

---

## Core UI Components

### ImageViewer

Props:

- imageUrl
- colonies
- selectedColonyId
- showMasks
- showIds
- colourBy

Events:

- onHoverColony(colonyId | null)
- onSelectColony(colonyId)

Requirements:

- Hover shows tooltip
- Click selects colony globally
- Selected colony visually distinct

---

### ColonyInspector

Props:

- colony (or null)
- imageUrl
- maskUrl (optional)

Renders:

- MaskPreview
- MetricsTable

Actions:

- Copy metrics
- Apply QC flag (optional)

---

### MetricsTable

Props:

- metrics
- qcFlags

Requirements:

- Stable metric ordering
- Numeric alignment
- Optional clickable metric names

---

### MetricHistogram

Props:

- colonies (filtered)
- metric
- selectedColonyId

Events:

- onMetricChange(metric)
- onBrushRange(range) optional

Requirements:

- Histogram or violin plot
- Highlight selected colony

---

### MetricScatter

Props:

- colonies
- xMetric
- yMetric
- selectedColonyId
- colourBy

Events:

- onChangeXMetric(metric)
- onChangeYMetric(metric)
- onSelectColony(colonyId)

Requirements:

- Each point maps to a colony_id
- Click selects globally

---

### EmbeddingPlot

Props:

- points: { colony_id, x, y, group? }
- selectedColonyId
- colourBy

Events:

- onSelectColony(colonyId)

---

### PlateHeatmap

Props:

- colonies
- metric
- plateImageDims

Events:

- onSelectColony(colonyId) using nearest match

---

### ExportMenu

Actions:

- Export per-colony CSV
- Export plate summary CSV
- Download overlay image
- Download masks ZIP (optional)

---

## UI Acceptance Tests

1. Clicking a colony outline selects it everywhere.
2. Clicking a scatter point selects the same colony in the viewer.
3. Changing X/Y metrics updates plots without losing selection.
4. Applying QC filters updates viewer and plots consistently.
5. Exported CSV reflects the current filtered state.
