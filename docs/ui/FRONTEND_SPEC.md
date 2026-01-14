# docs/ui/FRONTEND_SPEC.md

# ColonyAtlas Frontend UI Specification (Tailwind + React/Next.js)

## Purpose

This document defines the ColonyAtlas web UI at an implementation-ready level. It is designed to be used as a guide by engineers or LLMs implementing a Tailwind-based frontend.

## Design Goals

- Support the primary workflow: **Upload → Analyze → Explore plate → Inspect colonies → Plot metrics → Export**
- Make results **auditable**: any metric must trace back to a colony mask and original image location.
- Ensure the UI is **fast to navigate** for plates with many colonies (100–2000+).
- Ensure selection and filtering behaviour is **consistent across viewer + plots**.

---

## Visual Design System

### Theme

- Default: **dark theme** (preferred for image analysis).
- Palette (conceptual; implement with Tailwind slate/gray scale):
  - Page background: `slate-950`
  - Panels: `slate-900` / `slate-800`
  - Borders: `slate-700` (subtle)
  - Primary accent: `cyan`/`blue` family
  - Warning: `amber` family
  - Error: `red` family
  - Success: `emerald` family

### Typography

- Use a clean sans font (system or Inter).
- Headings: semibold.
- Numeric values: optionally monospace for alignment.

### Common Panel (Card) Style

All major UI sections should use a common panel layout:

- Container: `rounded-2xl border border-slate-700 bg-slate-900`
- Header: title + right-aligned actions
- Content: consistent padding (`p-4` or `p-6`)
- For dense tables: enable internal scrolling rather than page jumping

---

## Global App Layout

### App Shell

Persistent elements:

- **Top nav bar** (~56px height)
  - Left: ColonyAtlas logo/title
  - Center: primary nav tabs
  - Right: settings/help (optional)

Primary nav tabs:

1. **Upload**
2. **Plate Overview**
3. **Analysis Dashboard**

Global status indicators:

- Job status: `Idle | Uploading | Analyzing | Complete | Failed`
- Breadcrumb: `Dataset / Plate / Image` (where applicable)

---

## Pages

## 1) Upload Page

### Purpose

Upload single images or batches, attach metadata, and start analysis.

### Layout (Two-column)

**Left: Upload Panel**

- Drag-and-drop zone
- Buttons:
  - `Select Files`
  - `Select Folder` (if supported)
- Metadata inputs (optional but recommended):
  - Experiment name
  - Condition / Strain
  - Replicate
  - Pixel size (µm/px) or plate diameter (for scaling)
- Pipeline options (optional, can be collapsed under “Advanced”):
  - Segmentation mode: `SAM prompted by detection | Trained instance segmentation | Hybrid`
  - QC strictness: `Lenient | Standard | Strict`

**Right: Queue Panel**

- List of files with:
  - name, size, progress bar
  - remove action
- CTA: `Start Analysis`

### Required States

- Empty state (no files): show supported formats and instructions
- Uploading state: per-file progress
- Ready state: `Start Analysis` enabled
- Running state: disable inputs; show logs/progress

---

## 2) Plate Overview Page

### Purpose

Browse processed plates/images and open a specific plate in the dashboard.

### Layout

- Top controls row:
  - Search input (plate name / metadata)
  - Filters: condition, date range, QC status
  - Sort: newest, colony count, variability score
- Plate grid:
  - Plate cards with thumbnail + summary

### Plate Card (minimum contents)

- Thumbnail (raw or overlay)
- Plate name + metadata line (condition/replicate)
- Summary chips:
  - colony count
  - QC flagged count
  - optional variability score
- Actions:
  - `Open Dashboard`
  - `Export CSV` (optional in-card)

---

## 3) Analysis Dashboard Page (Core UI)

### Purpose

Interactive exploration: viewer + colony inspector + plots.

### Desktop Layout (recommended)

Use a responsive grid with three regions:

1. **Left column (60–65%)**: Image Viewer
2. **Right column (35–40%)**: Colony Inspector + Plot panels
3. **Bottom row (full width)**: Embedding + Heatmap panels

### Responsive Behaviour

- Tablet: right column stacks below viewer
- Mobile: single-column with collapsible panels and a colony list

---

# Core Components and Behaviours

## A) Image Viewer Panel

### Header Controls

- Toggle: `Show Masks`
- Toggle: `Show IDs`
- Dropdown: `Colour by` = `ID | QC Flag | Cluster | Condition`
- Button: `Download Overlay` (optional)

### Rendering Requirements

- Render original plate image in a fixed container.
- Overlay layer (SVG or Canvas):
  - outlines always available
  - filled masks optional (opacity)
  - hovered colony highlight (brighter outline)
  - selected colony highlight (thicker outline)

### Interaction

- Hover colony:
  - show tooltip: `Colony ID, Area, Circularity, QC flags`
- Click colony:
  - sets selected colony globally
  - updates colony inspector
  - highlights corresponding points on plots

### Footer Navigation

- `Previous colony` / `Next colony` buttons
- indicator: `Colony X of N`
- optional: zoom controls (`Fit`, `+`, `-`)
- optional: `Prev image` / `Next image` for multi-image datasets

---

## B) Colony Inspector Panel

### Purpose

Display selected colony details and metrics.

### Header

- Title: `Colony Details`
- Actions:
  - `Copy metrics`
  - `Flag` (manual QC override; optional)
  - Toggle: `Mask only` (preview)

### Content

Two sub-panels:

**1) Mask Preview**

- colony crop (bbox region) with mask overlay
- show centroid marker (optional)

**2) Metrics Table**
Minimum fields:

- `Colony ID`
- `Area`
- `Perimeter`
- `Equivalent diameter`
- `Circularity`
- `Solidity`
- `Eccentricity`
- `Aspect ratio`
- `Roughness (P/√A)`
- `Nearest neighbour distance`
- `QC flags`

### Interaction Coupling

- Clicking a metric name may “pin” it for plotting defaults (optional).
- `Send to scatter` action sets X/Y dropdowns (optional).

---

## C) Plot Panels

### 1) Distribution Panel (Histogram / Violin)

- Metric selector (default: Area)
- Visual: histogram (required), violin optional
- Interactions:
  - hover shows bin statistics
  - optional brushing selects subset (filters viewer and plots)

### 2) Scatter Panel (Metric vs Metric)

- Dropdowns: X metric, Y metric
- Each point = one colony (must contain `colony_id`)
- Interactions:
  - hover tooltip includes colony ID and values
  - click selects colony (global)
  - lasso selection optional (filters)

---

## D) Bottom Analytics Panels

### 1) Embedding Panel (PCA / UMAP)

- Tabs: `PCA`, `UMAP`
- Each point = colony with `colony_id`
- Colour by: QC/cluster/condition

### 2) Plate Heatmap Panel

- Dropdown: metric to visualise (Area, Circularity, Roughness, Density)
- Render as plate-position heatmap or overlay grid
- Clicking a region selects nearest colony or shows list

---

## Selection and Filtering Rules (Must)

1. **Global selected colony:** one source of truth (e.g., `selectedColonyId` in state).
2. **Hover does not change selection.**
3. **Plot points link to colony IDs**; click selects globally.
4. **Filters apply everywhere**: viewer highlights filtered set; plots update to filtered subset.
5. **QC flags are first-class**: filter and colour-by support required.

---

## Loading / Empty / Error States (Must)

Each major panel must handle:

- Loading: show skeleton or spinner, preserve layout
- Empty: show message and what user should do
- Error: show error summary and retry action

---

## Tailwind Implementation Guidance

- Use a 12-column grid on desktop.
- Prefer fixed heights for plot panels to avoid layout shifting.
- Use `overflow-auto` within panels rather than growing the page vertically.
- Avoid bespoke CSS; implement design with Tailwind utilities and small reusable className constants.

---

## Acceptance Criteria (UI)

- A user can upload images, run analysis, open a plate, click a colony, and see:
  - a highlight in the viewer
  - a populated colony inspector
  - the corresponding point highlighted on scatter and embedding plots
- User can choose any two metrics and generate scatter for that plate with colonies as datapoints.
- User can export per-colony table for the plate.
