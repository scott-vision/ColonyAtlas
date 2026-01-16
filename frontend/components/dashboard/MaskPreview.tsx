"use client";

import { useEffect, useRef } from "react";
import type { Colony } from "../../lib/types";

export default function MaskPreview({
  colony,
  imageUrl
}: {
  colony: Colony | null;
  imageUrl: string;
}) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    if (!colony || !canvasRef.current) return;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    const img = new Image();
    img.crossOrigin = "anonymous";
    img.onload = () => {
      const { x, y, w, h } = colony.bbox;
      const padding = 10;
      const cropX = Math.max(0, x - padding);
      const cropY = Math.max(0, y - padding);
      const cropW = Math.min(img.width - cropX, w + padding * 2);
      const cropH = Math.min(img.height - cropY, h + padding * 2);
      const targetWidth = 240;
      const aspect = cropH / cropW;
      canvas.width = targetWidth;
      canvas.height = Math.max(120, Math.round(targetWidth * aspect));
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.drawImage(img, cropX, cropY, cropW, cropH, 0, 0, canvas.width, canvas.height);
    };
    img.src = imageUrl;
  }, [colony, imageUrl]);

  if (!colony) {
    return (
      <div className="rounded-lg border border-dashed border-slate-800 p-4 text-sm text-slate-500">
        Select a colony to preview its mask.
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-slate-800 bg-slate-950 p-3">
      <canvas ref={canvasRef} className="w-full" />
      <p className="mt-2 text-xs text-slate-400">Colony crop preview</p>
    </div>
  );
}
