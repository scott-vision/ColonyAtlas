import type { MetricKey } from "./types";

export const METRIC_LABELS: Record<MetricKey, string> = {
  area: "Area",
  perimeter: "Perimeter",
  equivalent_diameter: "Equivalent Diameter",
  circularity: "Circularity",
  solidity: "Solidity",
  eccentricity: "Eccentricity",
  aspect_ratio: "Aspect Ratio",
  roughness: "Roughness",
  nearest_neighbor_distance: "Nearest Neighbour Distance"
};

export const METRIC_KEYS: MetricKey[] = Object.keys(METRIC_LABELS) as MetricKey[];
