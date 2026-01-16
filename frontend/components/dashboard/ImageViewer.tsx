"use client";

import { useMemo, useState } from "react";
import type { Colony } from "../../lib/types";

function getColonyColor(colony: Colony, colourBy: string) {
  if (colourBy === "qc") {
    return colony.qc_flags.length > 0 ? "#f59e0b" : "#22d3ee";
  }
  return "#22d3ee";
}

export default function ImageViewer({
  baseImageUrl,
  overlayImageUrl,
  colonies,
  selectedColonyId,
  hoveredColonyId,
  showMasks,
  showOutlines,
  showIds,
  colourBy,
  onHoverColony,
  onSelectColony
}: {
  baseImageUrl: string;
  overlayImageUrl?: string | null;
  colonies: Colony[];
  selectedColonyId: string | null;
  hoveredColonyId: string | null;
  showMasks: boolean;
  showOutlines: boolean;
  showIds: boolean;
  colourBy: "id" | "qc" | "cluster" | "condition";
  onHoverColony: (colonyId: string | null) => void;
  onSelectColony: (colonyId: string) => void;
}) {
  const [imageSize, setImageSize] = useState<{ width: number; height: number } | null>(null);
  const displayUrl = showMasks && overlayImageUrl ? overlayImageUrl : baseImageUrl;

  const hovered = useMemo(
    () => colonies.find((colony) => colony.id === hoveredColonyId),
    [colonies, hoveredColonyId]
  );

  const buildPath = (outline: { x: number; y: number }[]) => {
    if (!outline.length) return "";
    const [first, ...rest] = outline;
    return `M ${first.x} ${first.y} ${rest.map((p) => `L ${p.x} ${p.y}`).join(" ")} Z`;
  };

  return (
    <div className="space-y-3">
      <div className="relative overflow-hidden rounded-2xl border border-slate-800 bg-slate-950">
        <img
          src={displayUrl}
          alt="Plate"
          className="w-full"
          onLoad={(event) => {
            const target = event.currentTarget;
            setImageSize({ width: target.naturalWidth, height: target.naturalHeight });
          }}
        />
        {imageSize ? (
          <svg
            className="absolute inset-0 h-full w-full"
            viewBox={`0 0 ${imageSize.width} ${imageSize.height}`}
            preserveAspectRatio="xMidYMid meet"
          >
            {colonies.map((colony) => {
              const isSelected = colony.id === selectedColonyId;
              const isHovered = colony.id === hoveredColonyId;
              const color = getColonyColor(colony, colourBy);
              const outlineColor = isSelected ? "#ef4444" : "#22c55e";
              return (
                <g key={colony.id}>
                  <rect
                    x={colony.bbox.x}
                    y={colony.bbox.y}
                    width={colony.bbox.w}
                    height={colony.bbox.h}
                    fill="transparent"
                    stroke="transparent"
                    strokeWidth={0}
                    onMouseEnter={() => onHoverColony(colony.id)}
                    onMouseLeave={() => onHoverColony(null)}
                    onClick={() => onSelectColony(colony.id)}
                  />
                  {showOutlines && colony.outline
                    ? colony.outline.map((pathPoints, index) => (
                        <path
                          key={`${colony.id}-outline-${index}`}
                          d={buildPath(pathPoints)}
                          fill="transparent"
                          stroke={outlineColor}
                          strokeWidth={2}
                        />
                      ))
                    : null}
                  {isSelected || isHovered ? (
                    <circle
                      cx={colony.centroid.x}
                      cy={colony.centroid.y}
                      r={6}
                      fill="transparent"
                      stroke={color}
                      strokeWidth={2}
                    />
                  ) : null}
                  {showIds ? (
                    <text
                      x={colony.bbox.x + 4}
                      y={colony.bbox.y + 12}
                      fontSize="10"
                      fill={color}
                    >
                      {colony.id.slice(0, 4)}
                    </text>
                  ) : null}
                </g>
              );
            })}
          </svg>
        ) : null}
        {hovered ? (
          <div className="absolute left-3 top-3 rounded-lg bg-slate-950/90 px-3 py-2 text-xs text-slate-200">
            <div className="font-semibold">Colony {hovered.id.slice(0, 6)}</div>
            <div>Area: {hovered.metrics.area}</div>
            <div>Circularity: {hovered.metrics.circularity}</div>
            <div>QC: {hovered.qc_flags.join(", ") || "None"}</div>
          </div>
        ) : null}
      </div>
      <div className="flex items-center justify-between text-xs text-slate-400">
        <span>Hover for preview, click to select.</span>
        <span>{selectedColonyId ? `Selected: ${selectedColonyId.slice(0, 6)}` : "None"}</span>
      </div>
    </div>
  );
}
