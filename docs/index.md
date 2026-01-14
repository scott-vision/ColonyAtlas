# docs/INDEX.md

# ColonyAtlas Documentation Index

This `docs/` folder contains implementation specifications intended to be used by both humans and LLMs.

## If you are an LLM implementing the frontend

Read these files in order:

1. `docs/ui/FRONTEND_SPEC.md`  
   Source of truth for page layouts, UI behaviour, Tailwind styling conventions, and interaction rules.

2. `docs/ui/COMPONENT_MAP.md`  
   Component tree, props/events, and required API interactions.

3. `docs/api/OPENAPI_NOTES.md`  
   Expected backend payload shapes used by the UI (contracts).

## If you are implementing the backend

Read these files in order:

1. `docs/api/OPENAPI_NOTES.md`
2. `docs/pipeline/METRICS.md`
3. `docs/pipeline/QC_RULES.md`

## Implementation rules (non-negotiable)

- **Global selection state:** the selected colony must be reflected in the image viewer, colony inspector, and all plots.
- **Hover does not change selection:** hover is preview-only; click selects.
- **Every plotted point maps to a colony:** each point must contain a `colony_id` and support click-to-select.
- **QC flags are first-class:** filters and colour modes must support QC flags.
- **Tailwind-first:** styling must be implemented using Tailwind utility classes (avoid custom CSS unless unavoidable).
- **Interactive plots:** hover tooltips and click-to-select are required.

## File map

- UI specification: `docs/ui/FRONTEND_SPEC.md`
- UI component blueprint: `docs/ui/COMPONENT_MAP.md`
- API payload contracts: `docs/api/OPENAPI_NOTES.md`
- Metrics definitions: `docs/pipeline/METRICS.md`
- QC rules: `docs/pipeline/QC_RULES.md`
