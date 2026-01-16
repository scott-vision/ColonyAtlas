export type MetricKey =
  | "area"
  | "perimeter"
  | "equivalent_diameter"
  | "circularity"
  | "solidity"
  | "eccentricity"
  | "aspect_ratio"
  | "roughness"
  | "nearest_neighbor_distance";

export type QCFlag = "border" | "merged" | "low_contrast" | "artifact";

export interface Plate {
  id: string;
  name: string;
  created_at: string;
  metadata?: Record<string, string>;
  attributes?: PlateAttributes | null;
  image_url: string;
  overlay_url?: string | null;
  colony_count: number;
  qc_summary: Record<string, number>;
  summary_stats: Record<string, number>;
  derived_stats?: Record<string, string | number>;
}

export interface Colony {
  id: string;
  plate_id: string;
  bbox: { x: number; y: number; w: number; h: number };
  centroid: { x: number; y: number };
  mask_url?: string | null;
  metrics: Record<string, number>;
  qc_flags: string[];
  cluster_id?: string | null;
  outline?: { x: number; y: number }[][];
}

export interface AnalyzeRequest {
  plate_ids: string[];
}

export interface UploadResponse {
  plates: Plate[];
}

export interface PlateAttributes {
  plate_diameter_mm: number;
  species: string;
  hours_post_inoculation: number;
  volume: number;
  treatment_description: string;
  notes: string;
}
