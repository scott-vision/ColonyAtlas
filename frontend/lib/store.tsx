import { createContext, useContext, useMemo, useReducer } from "react";
import type { MetricKey } from "./types";
import { METRIC_KEYS } from "./metrics";

interface FiltersState {
  qcFlags: string[];
  metricRanges: Record<string, [number, number]>;
}

interface DashboardState {
  activePlateId: string | null;
  selectedColonyId: string | null;
  hoveredColonyId: string | null;
  filters: FiltersState;
  colourBy: "id" | "qc" | "cluster" | "condition";
  showMasks: boolean;
  showOutlines: boolean;
  showIds: boolean;
  xMetric: MetricKey;
  yMetric: MetricKey;
}

type Action =
  | { type: "setPlate"; plateId: string }
  | { type: "selectColony"; colonyId: string | null }
  | { type: "hoverColony"; colonyId: string | null }
  | { type: "setColourBy"; colourBy: DashboardState["colourBy"] }
  | { type: "toggleMasks" }
  | { type: "toggleOutlines" }
  | { type: "toggleIds" }
  | { type: "setXMetric"; metric: MetricKey }
  | { type: "setYMetric"; metric: MetricKey }
  | { type: "setFilters"; filters: FiltersState };

const initialState: DashboardState = {
  activePlateId: null,
  selectedColonyId: null,
  hoveredColonyId: null,
  filters: { qcFlags: [], metricRanges: {} },
  colourBy: "id",
  showMasks: true,
  showOutlines: false,
  showIds: false,
  xMetric: METRIC_KEYS[0],
  yMetric: METRIC_KEYS[3]
};

function reducer(state: DashboardState, action: Action): DashboardState {
  switch (action.type) {
    case "setPlate":
      return { ...state, activePlateId: action.plateId };
    case "selectColony":
      return { ...state, selectedColonyId: action.colonyId };
    case "hoverColony":
      return { ...state, hoveredColonyId: action.colonyId };
    case "setColourBy":
      return { ...state, colourBy: action.colourBy };
    case "toggleMasks": {
      const next = !state.showMasks;
      return {
        ...state,
        showMasks: next,
        showOutlines: next ? false : state.showOutlines
      };
    }
    case "toggleOutlines": {
      const next = !state.showOutlines;
      return {
        ...state,
        showOutlines: next,
        showMasks: next ? false : state.showMasks
      };
    }
    case "toggleIds":
      return { ...state, showIds: !state.showIds };
    case "setXMetric":
      return { ...state, xMetric: action.metric };
    case "setYMetric":
      return { ...state, yMetric: action.metric };
    case "setFilters":
      return { ...state, filters: action.filters };
    default:
      return state;
  }
}

const DashboardContext = createContext<
  { state: DashboardState; dispatch: React.Dispatch<Action> } | undefined
>(undefined);

export function DashboardProvider({
  plateId,
  children
}: {
  plateId: string;
  children: React.ReactNode;
}) {
  const [state, dispatch] = useReducer(reducer, {
    ...initialState,
    activePlateId: plateId
  });
  const value = useMemo(() => ({ state, dispatch }), [state]);
  return <DashboardContext.Provider value={value}>{children}</DashboardContext.Provider>;
}

export function useDashboardStore() {
  const context = useContext(DashboardContext);
  if (!context) {
    throw new Error("useDashboardStore must be used within DashboardProvider");
  }
  return context;
}
