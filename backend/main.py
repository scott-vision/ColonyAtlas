from __future__ import annotations

import base64
import csv
import io
import json
import os
import uuid
import math
from datetime import datetime, timezone
from typing import Dict, List, Optional, Union

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from cellpose import core, models
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image, ImageDraw
from pydantic import BaseModel, Field
from skimage.measure import regionprops, find_contours
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from ultralytics import YOLO
from ultralytics.nn.tasks import SegmentationModel
import torch

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
UPLOADS_DIR = os.path.join(DATA_DIR, "uploads")
OVERLAYS_DIR = os.path.join(DATA_DIR, "overlays")
REPORTS_DIR = os.path.join(DATA_DIR, "reports")

os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(OVERLAYS_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)

app = FastAPI(title="ColonyAtlas API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"] ,
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=DATA_DIR), name="static")


class BBox(BaseModel):
    x: float
    y: float
    w: float
    h: float


class Point(BaseModel):
    x: float
    y: float


class Colony(BaseModel):
    id: str
    plate_id: str
    bbox: BBox
    centroid: Point
    mask_url: Optional[str] = None
    metrics: Dict[str, float]
    qc_flags: List[str] = Field(default_factory=list)
    cluster_id: Optional[str] = None
    outline: Optional[List[List[Point]]] = None


class PlateAttributes(BaseModel):
    plate_diameter_mm: float = 90.0
    species: str = ""
    hours_post_inoculation: float = 0.0
    volume: float = 1.0
    treatment_description: str = ""
    notes: str = ""


class Plate(BaseModel):
    id: str
    name: str
    created_at: str
    metadata: Optional[Dict[str, str]] = None
    attributes: Optional[PlateAttributes] = None
    image_url: str
    overlay_url: Optional[str] = None
    colony_count: int
    qc_summary: Dict[str, int]
    summary_stats: Dict[str, float]
    derived_stats: Dict[str, "Union[float, str]"] = Field(default_factory=dict)


class UploadResponse(BaseModel):
    plates: List[Plate]


class AnalyzeRequest(BaseModel):
    plate_ids: List[str]


class AnalyzeResponse(BaseModel):
    analyzed: List[str]


PLATES: Dict[str, Plate] = {}
COLONIES_BY_PLATE: Dict[str, List[Colony]] = {}
PLATE_IMAGE_PATHS: Dict[str, str] = {}
MODEL: Optional[models.CellposeModel] = None
MODEL_TYPE = os.getenv("CELLPOSE_MODEL_TYPE", "cellpose_sam")
YOLO_MODEL: Optional[YOLO] = None
YOLO_MODEL_PATH = os.getenv(
    "YOLO_MODEL_PATH",
    os.path.join(
        BASE_DIR,
        "..",
        "notebooks",
        "runs",
        "segment",
        "train12",
        "weights",
        "best.pt",
    ),
)
SEGMENTATION_METHOD = os.getenv("SEGMENTATION_METHOD", "yolo")
PLATE_DETECTOR: Optional[YOLO] = None
PLATE_MODEL_PATH = os.getenv(
    "PLATE_MODEL_PATH",
    os.path.join(BASE_DIR, "plate-weights.pt"),
)

QC_FLAG_OPTIONS = ["border", "merged", "low_contrast", "artifact"]
METRIC_KEYS = [
    "area",
    "perimeter",
    "equivalent_diameter",
    "circularity",
    "solidity",
    "eccentricity",
    "aspect_ratio",
    "roughness",
    "nearest_neighbor_distance",
]

FLOW_THRESHOLD = 0.4
CELLPROB_THRESHOLD = 0.0
TILE_NORM_BLOCKSIZE = 0


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_metadata(metadata_raw: Optional[str]) -> Optional[Dict[str, str]]:
    if not metadata_raw:
        return None
    try:
        data = json.loads(metadata_raw)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid metadata JSON: {exc}")
    if not isinstance(data, dict):
        raise HTTPException(status_code=400, detail="metadata must be a JSON object")
    return {str(k): str(v) for k, v in data.items()}


def get_model() -> models.CellposeModel:
    global MODEL
    if MODEL is None:
        use_gpu = core.use_gpu()
        MODEL = models.CellposeModel(gpu=use_gpu, model_type=MODEL_TYPE)
    return MODEL


def get_yolo_model() -> YOLO:
    global YOLO_MODEL
    if YOLO_MODEL is None:
        torch.serialization.add_safe_globals([SegmentationModel])
        YOLO_MODEL = YOLO(resolve_model_path(YOLO_MODEL_PATH))
    return YOLO_MODEL


def get_plate_detector() -> YOLO:
    global PLATE_DETECTOR
    if PLATE_DETECTOR is None:
        torch.serialization.add_safe_globals([SegmentationModel])
        PLATE_DETECTOR = YOLO(resolve_model_path(PLATE_MODEL_PATH))
    return PLATE_DETECTOR


def resolve_model_path(path_value: str) -> str:
    if os.path.isabs(path_value):
        return path_value
    return os.path.abspath(os.path.join(BASE_DIR, path_value))


def load_image_array(image_path: str) -> np.ndarray:
    image = Image.open(image_path)
    array = np.asarray(image)
    if array.ndim == 2:
        array = array[:, :, None]
    return array


def compute_average_color(image_path: str) -> tuple[float, float, float]:
    image = Image.open(image_path).convert("RGB")
    array = np.asarray(image).astype(np.float32)
    mean_rgb = array.mean(axis=(0, 1))
    return float(mean_rgb[0]), float(mean_rgb[1]), float(mean_rgb[2])


def rgb_to_hex(rgb: tuple[float, float, float]) -> str:
    return "#{:02x}{:02x}{:02x}".format(*(int(round(v)) for v in rgb))


def build_colonies_from_masks(
    masks: np.ndarray, plate_id: str, image_shape: tuple[int, int]
) -> List[Colony]:
    if masks is None or np.max(masks) == 0:
        return []
    height, width = image_shape
    regions = regionprops(masks)
    areas = [region.area for region in regions] or [0.0]
    median_area = float(np.median(areas))
    colonies: List[Colony] = []
    centroids = []
    for region in regions:
        min_row, min_col, max_row, max_col = region.bbox
        w = max_col - min_col
        h = max_row - min_row
        perimeter = float(region.perimeter) if region.perimeter else 0.0
        area = float(region.area)
        circularity = (4 * 3.14159 * area) / (perimeter ** 2) if perimeter else 0.0
        major = float(region.major_axis_length) if region.major_axis_length else 0.0
        minor = float(region.minor_axis_length) if region.minor_axis_length else 0.0
        aspect_ratio = (major / minor) if minor else 0.0
        roughness = perimeter / (area ** 0.5) if area else 0.0
        flags = []
        if min_col <= 1 or min_row <= 1 or max_col >= width - 1 or max_row >= height - 1:
            flags.append("border")
        if median_area and area > median_area * 3:
            flags.append("merged")
        binary = masks == region.label
        outlines = extract_outline_points(binary.astype(np.uint8), 1.0, 1.0)
        colony = Colony(
            id=str(uuid.uuid4()),
            plate_id=plate_id,
            bbox=BBox(x=float(min_col), y=float(min_row), w=float(w), h=float(h)),
            centroid=Point(x=float(region.centroid[1]), y=float(region.centroid[0])),
            metrics={
                "area": round(area, 2),
                "perimeter": round(perimeter, 2),
                "equivalent_diameter": round(float(region.equivalent_diameter), 2),
                "circularity": round(circularity, 4),
                "solidity": round(float(region.solidity), 4) if region.solidity else 0.0,
                "eccentricity": round(float(region.eccentricity), 4)
                if region.eccentricity
                else 0.0,
                "aspect_ratio": round(aspect_ratio, 3),
                "roughness": round(roughness, 4),
                "nearest_neighbor_distance": 0.0,
            },
            qc_flags=flags,
            outline=outlines,
        )
        colonies.append(colony)
        centroids.append((colony.centroid.x, colony.centroid.y))
    if colonies:
        centroid_array = np.array(centroids)
        distances = []
        for idx, point in enumerate(centroid_array):
            diff = centroid_array - point
            dist = np.sqrt((diff ** 2).sum(axis=1))
            dist[idx] = np.inf
            distances.append(float(np.min(dist)))
        for colony, distance in zip(colonies, distances):
            colony.metrics["nearest_neighbor_distance"] = round(distance, 2)
    return colonies


def build_colonies_from_instance_masks(
    instance_masks: np.ndarray,
    plate_id: str,
    image_shape: tuple[int, int],
    scale_x: float = 1.0,
    scale_y: float = 1.0,
) -> List[Colony]:
    if instance_masks is None or len(instance_masks) == 0:
        return []
    height, width = image_shape
    areas = [float(mask.sum()) for mask in instance_masks] or [0.0]
    median_area = float(np.median(areas))
    colonies: List[Colony] = []
    centroids = []
    for mask in instance_masks:
        binary = mask > 0.5
        if not np.any(binary):
            continue
        regions = regionprops(binary.astype(np.uint8))
        if not regions:
            continue
        region = regions[0]
        min_row, min_col, max_row, max_col = region.bbox
        w = max_col - min_col
        h = max_row - min_row
        perimeter = float(region.perimeter) if region.perimeter else 0.0
        area = float(region.area)
        circularity = (4 * 3.14159 * area) / (perimeter ** 2) if perimeter else 0.0
        major = float(region.major_axis_length) if region.major_axis_length else 0.0
        minor = float(region.minor_axis_length) if region.minor_axis_length else 0.0
        aspect_ratio = (major / minor) if minor else 0.0
        roughness = perimeter / (area ** 0.5) if area else 0.0
        flags = []
        if min_col <= 1 or min_row <= 1 or max_col >= width - 1 or max_row >= height - 1:
            flags.append("border")
        if median_area and area > median_area * 3:
            flags.append("merged")
        outlines = extract_outline_points(binary.astype(np.uint8), scale_x, scale_y)
        colony = Colony(
            id=str(uuid.uuid4()),
            plate_id=plate_id,
            bbox=BBox(
                x=float(min_col * scale_x),
                y=float(min_row * scale_y),
                w=float(w * scale_x),
                h=float(h * scale_y),
            ),
            centroid=Point(
                x=float(region.centroid[1] * scale_x),
                y=float(region.centroid[0] * scale_y),
            ),
            metrics={
                "area": round(area, 2),
                "perimeter": round(perimeter, 2),
                "equivalent_diameter": round(float(region.equivalent_diameter), 2),
                "circularity": round(circularity, 4),
                "solidity": round(float(region.solidity), 4) if region.solidity else 0.0,
                "eccentricity": round(float(region.eccentricity), 4)
                if region.eccentricity
                else 0.0,
                "aspect_ratio": round(aspect_ratio, 3),
                "roughness": round(roughness, 4),
                "nearest_neighbor_distance": 0.0,
            },
            qc_flags=flags,
            outline=outlines,
        )
        colonies.append(colony)
        centroids.append((colony.centroid.x, colony.centroid.y))
    if colonies:
        centroid_array = np.array(centroids)
        distances = []
        for idx, point in enumerate(centroid_array):
            diff = centroid_array - point
            dist = np.sqrt((diff ** 2).sum(axis=1))
            dist[idx] = np.inf
            distances.append(float(np.min(dist)))
        for colony, distance in zip(colonies, distances):
            colony.metrics["nearest_neighbor_distance"] = round(distance, 2)
    return colonies


def build_overlay(
    image_path: str,
    colonies: List[Colony],
    plate_id: str,
    plate_circle: Optional[tuple[float, float, float]] = None,
) -> str:
    image = Image.open(image_path).convert("RGBA")
    overlay = image.copy()
    draw = ImageDraw.Draw(overlay)
    if plate_circle:
        cx, cy, radius = plate_circle
        draw.ellipse(
            [cx - radius, cy - radius, cx + radius, cy + radius],
            outline=(255, 0, 0, 255),
            width=6,
        )
    for colony in colonies:
        bbox = colony.bbox
        x0 = bbox.x
        y0 = bbox.y
        x1 = bbox.x + bbox.w
        y1 = bbox.y + bbox.h
        draw.rectangle([x0, y0, x1, y1], outline=(0, 255, 255, 255), width=2)
    overlay_path = os.path.join(OVERLAYS_DIR, plate_id)
    os.makedirs(overlay_path, exist_ok=True)
    output_path = os.path.join(overlay_path, "overlay.png")
    overlay.save(output_path)
    return f"/static/overlays/{plate_id}/overlay.png"


def draw_mask_outlines(
    draw: ImageDraw.ImageDraw, mask: np.ndarray, scale_x: float, scale_y: float
) -> None:
    contours = find_contours(mask, 0.5)
    for contour in contours:
        points = [(float(col * scale_x), float(row * scale_y)) for row, col in contour]
        if len(points) < 2:
            continue
        points.append(points[0])
        draw.line(points, fill=(0, 255, 255, 255), width=2)


def overlay_instance_masks(
    img_rgb: np.ndarray, masks: List[np.ndarray], alpha: float = 0.45, seed: int = 0
) -> np.ndarray:
    out = img_rgb.copy()
    h, w = out.shape[:2]
    rng = np.random.default_rng(seed)
    colors = rng.integers(0, 256, size=(len(masks), 3), dtype=np.uint8)
    for i, mask in enumerate(masks):
        if mask is None or mask.shape != (h, w) or not mask.any():
            continue
        color = colors[i]
        out[mask] = (alpha * color + (1 - alpha) * out[mask]).astype(np.uint8)
    return out


def extract_outline_points(
    binary: np.ndarray, scale_x: float, scale_y: float
) -> List[List[Point]]:
    outlines: List[List[Point]] = []
    contours = find_contours(binary, 0.5)
    for contour in contours:
        if len(contour) < 2:
            continue
        step = max(1, len(contour) // 200)
        points = [
            Point(x=float(col * scale_x), y=float(row * scale_y))
            for row, col in contour[::step]
        ]
        if points:
            outlines.append(points)
    return outlines


def build_overlay_from_masks(
    image_path: str,
    plate_id: str,
    plate_circle: Optional[tuple[float, float, float]],
    labeled_mask: Optional[np.ndarray] = None,
    instance_masks: Optional[np.ndarray] = None,
    scale_x: float = 1.0,
    scale_y: float = 1.0,
) -> str:
    image = Image.open(image_path).convert("RGB")
    rgb = np.asarray(image).astype(np.uint8)
    masks: List[np.ndarray] = []
    if instance_masks is not None:
        for mask in instance_masks:
            if mask is None:
                continue
            binary = mask > 0.5
            if binary.shape != rgb.shape[:2]:
                resized = Image.fromarray(binary.astype(np.uint8) * 255).resize(
                    (rgb.shape[1], rgb.shape[0]), resample=Image.NEAREST
                )
                binary = np.asarray(resized) > 0
            masks.append(binary)
    elif labeled_mask is not None:
        for label in np.unique(labeled_mask):
            if label == 0:
                continue
            binary = labeled_mask == label
            masks.append(binary)
    overlay_rgb = overlay_instance_masks(rgb, masks, alpha=0.45, seed=0)
    overlay = Image.fromarray(overlay_rgb).convert("RGBA")
    draw = ImageDraw.Draw(overlay)
    if plate_circle:
        cx, cy, radius = plate_circle
        draw.ellipse(
            [cx - radius, cy - radius, cx + radius, cy + radius],
            outline=(255, 0, 0, 255),
            width=6,
        )
    overlay_path = os.path.join(OVERLAYS_DIR, plate_id)
    os.makedirs(overlay_path, exist_ok=True)
    output_path = os.path.join(overlay_path, "overlay.png")
    overlay.save(output_path)
    return f"/static/overlays/{plate_id}/overlay.png"


def summarize_colonies(colonies: List[Colony]) -> Dict[str, float]:
    if not colonies:
        return {key: 0.0 for key in METRIC_KEYS}
    summary: Dict[str, float] = {}
    for key in METRIC_KEYS:
        values = [colony.metrics.get(key, 0.0) for colony in colonies]
        summary[key] = round(sum(values) / len(values), 4)
    return summary


def summarize_qc(colonies: List[Colony]) -> Dict[str, int]:
    summary = {flag: 0 for flag in QC_FLAG_OPTIONS}
    for colony in colonies:
        for flag in colony.qc_flags:
            summary[flag] = summary.get(flag, 0) + 1
    return summary


def generate_boxplot_image(
    colonies: List[Colony], metrics: List[str], output_path: str, title: str
) -> None:
    matplotlib.use("Agg")
    data = [
        [colony.metrics.get(metric, 0.0) for colony in colonies] for metric in metrics
    ]
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.boxplot(data, labels=metrics, showfliers=False)
    ax.set_title(title)
    ax.tick_params(axis="x", rotation=30)
    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)


def image_to_data_uri(image_path: str) -> str:
    with open(image_path, "rb") as file:
        encoded = base64.b64encode(file.read()).decode("utf-8")
    return f"data:image/png;base64,{encoded}"


def generate_report_files(
    plate: Plate, colonies: List[Colony], use_mm_units: bool
) -> Dict[str, str]:
    plate_dir = os.path.join(REPORTS_DIR, plate.id)
    os.makedirs(plate_dir, exist_ok=True)
    size_boxplot_path = os.path.join(plate_dir, "metrics_boxplot_size.png")
    shape_boxplot_path = os.path.join(plate_dir, "metrics_boxplot_shape.png")
    size_metrics = ["area", "perimeter"]
    size_title = "Size Metrics (pixels)"
    if use_mm_units:
        size_metrics = ["area_mm2", "perimeter_mm"]
        size_title = "Size Metrics (mm)"
    generate_boxplot_image(
        colonies, size_metrics, size_boxplot_path, size_title
    )
    generate_boxplot_image(
        colonies,
        ["circularity", "solidity", "eccentricity", "aspect_ratio", "roughness"],
        shape_boxplot_path,
        "Shape Metrics",
    )
    original_path = PLATE_IMAGE_PATHS.get(plate.id)
    overlay_path = None
    if plate.overlay_url:
        overlay_path = os.path.join(OVERLAYS_DIR, plate.id, "overlay.png")
    return {
        "boxplot_size": size_boxplot_path,
        "boxplot_shape": shape_boxplot_path,
        "original": original_path or "",
        "overlay": overlay_path or "",
    }


def detect_plate_circle(image_path: str) -> Optional[tuple[float, float, float]]:
    model = get_plate_detector()
    results = model.predict(source=image_path, conf=0.25, verbose=False)
    if not results:
        return None
    boxes = results[0].boxes
    if boxes is None or boxes.xyxy is None or len(boxes.xyxy) == 0:
        return None
    x0, y0, x1, y1 = boxes.xyxy[0].tolist()
    midpoints = [
        ((x0 + x1) / 2, y0),
        (x1, (y0 + y1) / 2),
        ((x0 + x1) / 2, y1),
        (x0, (y0 + y1) / 2),
    ]
    cx = sum(p[0] for p in midpoints) / len(midpoints)
    cy = sum(p[1] for p in midpoints) / len(midpoints)
    radius = sum(math.hypot(p[0] - cx, p[1] - cy) for p in midpoints) / len(midpoints)
    return float(cx), float(cy), float(radius)


@app.post("/upload", response_model=UploadResponse)
async def upload_images(
    files: List[UploadFile] = File(...),
    metadata: Optional[str] = Form(None),
) -> UploadResponse:
    metadata_map = parse_metadata(metadata)
    plates: List[Plate] = []

    for upload in files:
        plate_id = str(uuid.uuid4())
        filename = os.path.basename(upload.filename)
        plate_dir = os.path.join(UPLOADS_DIR, plate_id)
        os.makedirs(plate_dir, exist_ok=True)
        target_path = os.path.join(plate_dir, filename)
        content = await upload.read()
        with open(target_path, "wb") as f:
            f.write(content)
        image_url = f"/static/uploads/{plate_id}/{filename}"
        plate = Plate(
            id=plate_id,
            name=os.path.splitext(filename)[0],
            created_at=now_iso(),
            metadata=metadata_map,
            attributes=PlateAttributes(),
            image_url=image_url,
            overlay_url=None,
            colony_count=0,
            qc_summary={},
            summary_stats={},
            derived_stats={},
        )
        PLATES[plate_id] = plate
        COLONIES_BY_PLATE[plate_id] = []
        PLATE_IMAGE_PATHS[plate_id] = target_path
        plates.append(plate)

    return UploadResponse(plates=plates)


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze(request: AnalyzeRequest) -> AnalyzeResponse:
    analyzed: List[str] = []
    for plate_id in request.plate_ids:
        plate = PLATES.get(plate_id)
        if not plate:
            raise HTTPException(status_code=404, detail=f"Plate {plate_id} not found")
        image_path = PLATE_IMAGE_PATHS.get(plate_id)
        if not image_path or not os.path.exists(image_path):
            raise HTTPException(status_code=404, detail=f"Image for plate {plate_id} not found")
        image = Image.open(image_path)
        if SEGMENTATION_METHOD == "yolo":
            model = get_yolo_model()
            results = model.predict(
                source=image_path, conf=0.25, verbose=False, retina_masks=True
            )
            result = results[0]
            if result.masks is None or result.masks.data is None:
                colonies = []
                instance_masks = None
                scale_x = 1.0
                scale_y = 1.0
            else:
                instance_masks = result.masks.data.cpu().numpy()
                mask_height, mask_width = instance_masks.shape[-2], instance_masks.shape[-1]
                scale_x = image.size[0] / mask_width
                scale_y = image.size[1] / mask_height
                colonies = build_colonies_from_instance_masks(
                    instance_masks,
                    plate_id,
                    image.size[::-1],
                    scale_x=scale_x,
                    scale_y=scale_y,
                )
        else:
            model = get_model()
            image_array = load_image_array(image_path)
            masks, _, _ = model.eval(
                image_array,
                batch_size=32,
                flow_threshold=FLOW_THRESHOLD,
                cellprob_threshold=CELLPROB_THRESHOLD,
                normalize={"tile_norm_blocksize": TILE_NORM_BLOCKSIZE},
            )
            colonies = build_colonies_from_masks(masks, plate_id, image.size[::-1])
            instance_masks = None
            scale_x = 1.0
            scale_y = 1.0
            labeled_mask = masks
        plate_circle = detect_plate_circle(image_path)
        overlay_url = build_overlay_from_masks(
            image_path,
            plate_id,
            plate_circle=plate_circle,
            labeled_mask=None if SEGMENTATION_METHOD == "yolo" else labeled_mask,
            instance_masks=instance_masks if SEGMENTATION_METHOD == "yolo" else None,
            scale_x=scale_x,
            scale_y=scale_y,
        )
        plate.colony_count = len(colonies)
        plate.overlay_url = overlay_url
        plate.qc_summary = summarize_qc(colonies)
        plate.summary_stats = summarize_colonies(colonies)
        avg_rgb = compute_average_color(image_path)
        volume = plate.attributes.volume if plate.attributes else 1.0
        volume_adjusted = (plate.colony_count / volume) if volume else 0.0
        plate_diameter_mm = (
            plate.attributes.plate_diameter_mm if plate.attributes else 90.0
        )
        plate_area_mm2 = math.pi * (plate_diameter_mm / 2) ** 2
        density = (plate.colony_count / plate_area_mm2) if plate_area_mm2 else 0.0
        mm_per_pixel = None
        if plate_circle:
            _, _, radius = plate_circle
            if radius > 0:
                mm_per_pixel = plate_diameter_mm / (2 * radius)
                for colony in colonies:
                    area_px = colony.metrics.get("area", 0.0)
                    perimeter_px = colony.metrics.get("perimeter", 0.0)
                    colony.metrics["area_mm2"] = round(area_px * mm_per_pixel**2, 4)
                    colony.metrics["perimeter_mm"] = round(perimeter_px * mm_per_pixel, 4)
        mean_area_mm2 = (
            round(
                sum(c.metrics.get("area_mm2", 0.0) for c in colonies) / len(colonies), 4
            )
            if colonies and mm_per_pixel
            else "N/A"
        )
        mean_perimeter_mm = (
            round(
                sum(c.metrics.get("perimeter_mm", 0.0) for c in colonies) / len(colonies), 4
            )
            if colonies and mm_per_pixel
            else "N/A"
        )
        plate.derived_stats = {
            "colony_count": plate.colony_count,
            "volume_adjusted_count": round(volume_adjusted, 3),
            "colony_density_per_mm2": round(density, 4),
            "mm_per_pixel": round(mm_per_pixel, 6) if mm_per_pixel else "N/A",
            "mean_area_mm2": mean_area_mm2,
            "mean_perimeter_mm": mean_perimeter_mm,
            "average_color_hex": rgb_to_hex(avg_rgb),
            "average_color_rgb": f"{avg_rgb[0]:.1f}, {avg_rgb[1]:.1f}, {avg_rgb[2]:.1f}",
        }
        PLATES[plate_id] = plate
        COLONIES_BY_PLATE[plate_id] = colonies
        analyzed.append(plate_id)
    return AnalyzeResponse(analyzed=analyzed)


@app.get("/plates", response_model=List[Plate])
async def list_plates() -> List[Plate]:
    return list(PLATES.values())


@app.get("/plate/{plate_id}", response_model=Plate)
async def get_plate(plate_id: str) -> Plate:
    plate = PLATES.get(plate_id)
    if not plate:
        raise HTTPException(status_code=404, detail="Plate not found")
    return plate


@app.put("/plate/{plate_id}/attributes", response_model=Plate)
async def update_plate_attributes(plate_id: str, attributes: PlateAttributes) -> Plate:
    plate = PLATES.get(plate_id)
    if not plate:
        raise HTTPException(status_code=404, detail="Plate not found")
    plate.attributes = attributes
    PLATES[plate_id] = plate
    return plate


@app.get("/plate/{plate_id}/colonies", response_model=List[Colony])
async def get_plate_colonies(plate_id: str) -> List[Colony]:
    colonies = COLONIES_BY_PLATE.get(plate_id)
    if colonies is None:
        raise HTTPException(status_code=404, detail="Plate not found")
    return colonies


@app.get("/export/plate/{plate_id}/colonies.csv")
async def export_colonies_csv(plate_id: str) -> StreamingResponse:
    colonies = COLONIES_BY_PLATE.get(plate_id)
    if colonies is None:
        raise HTTPException(status_code=404, detail="Plate not found")
    output = io.StringIO()
    fieldnames = [
        "colony_id",
        "plate_id",
        "bbox_x",
        "bbox_y",
        "bbox_w",
        "bbox_h",
        "centroid_x",
        "centroid_y",
        "qc_flags",
    ] + METRIC_KEYS
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for colony in colonies:
        row = {
            "colony_id": colony.id,
            "plate_id": colony.plate_id,
            "bbox_x": colony.bbox.x,
            "bbox_y": colony.bbox.y,
            "bbox_w": colony.bbox.w,
            "bbox_h": colony.bbox.h,
            "centroid_x": colony.centroid.x,
            "centroid_y": colony.centroid.y,
            "qc_flags": ";".join(colony.qc_flags),
        }
        row.update({key: colony.metrics.get(key, 0.0) for key in METRIC_KEYS})
        writer.writerow(row)
    output.seek(0)
    headers = {
        "Content-Disposition": f"attachment; filename=plate_{plate_id}_colonies.csv"
    }
    return StreamingResponse(
        iter([output.getvalue()]), media_type="text/csv", headers=headers
    )


@app.get("/report/plate/{plate_id}")
async def export_plate_report(plate_id: str, format: str = "md"):
    plate = PLATES.get(plate_id)
    if not plate:
        raise HTTPException(status_code=404, detail="Plate not found")
    colonies = COLONIES_BY_PLATE.get(plate_id, [])
    attributes = plate.attributes or PlateAttributes()
    derived = plate.derived_stats
    use_mm_units = derived.get("mm_per_pixel", "N/A") != "N/A"
    assets = generate_report_files(plate, colonies, use_mm_units=use_mm_units)

    if format == "md":
        original_uri = image_to_data_uri(assets["original"]) if assets["original"] else ""
        overlay_uri = image_to_data_uri(assets["overlay"]) if assets["overlay"] else ""
        boxplot_size_uri = (
            image_to_data_uri(assets["boxplot_size"]) if assets["boxplot_size"] else ""
        )
        boxplot_shape_uri = (
            image_to_data_uri(assets["boxplot_shape"]) if assets["boxplot_shape"] else ""
        )
        markdown = f"""# Plate Report: {plate.name}

## Input Details
- Plate diameter (mm): {attributes.plate_diameter_mm}
- Species: {attributes.species or "N/A"}
- Hours post inoculation: {attributes.hours_post_inoculation}
- Volume: {attributes.volume}
- Treatment description: {attributes.treatment_description or "N/A"}
- Notes: {attributes.notes or "N/A"}

## Derived Summary
- Colony count: {derived.get("colony_count", 0)}
- Volume adjusted count: {derived.get("volume_adjusted_count", 0)}
- Colony density (per mm^2): {derived.get("colony_density_per_mm2", 0)}
- mm per pixel: {derived.get("mm_per_pixel", "N/A")}
- Mean area (mm^2): {derived.get("mean_area_mm2", "N/A")}
- Mean perimeter (mm): {derived.get("mean_perimeter_mm", "N/A")}
- Average color: {derived.get("average_color_hex", "N/A")} ({derived.get("average_color_rgb", "")})

## Mean Metrics
"""
        for key, value in plate.summary_stats.items():
            markdown += f"- {key}: {value}\n"
        markdown += "\n## Original Image\n"
        if original_uri:
            markdown += f"![Original]({original_uri})\n"
        markdown += "\n## Segmentation Overlay\n"
        if overlay_uri:
            markdown += f"![Overlay]({overlay_uri})\n"
        markdown += "\n## Morphology Box Plots (Size)\n"
        if boxplot_size_uri:
            markdown += f"![Boxplot Size]({boxplot_size_uri})\n"
        markdown += "\n## Morphology Box Plots (Shape)\n"
        if boxplot_shape_uri:
            markdown += f"![Boxplot Shape]({boxplot_shape_uri})\n"
        output = io.StringIO(markdown)
        headers = {"Content-Disposition": f"attachment; filename=plate_{plate_id}_report.md"}
        return StreamingResponse(
            iter([output.getvalue()]), media_type="text/markdown", headers=headers
        )

    if format == "pdf":
        report_path = os.path.join(REPORTS_DIR, plate_id, "report.pdf")
        c = canvas.Canvas(report_path, pagesize=letter)
        width, height = letter
        margin_x = 40
        y = height - 40
        c.setFont("Helvetica-Bold", 16)
        c.drawString(margin_x, y, f"Plate Report: {plate.name}")
        y -= 28
        c.setFont("Helvetica", 10)
        c.drawString(margin_x, y, f"Plate diameter (mm): {attributes.plate_diameter_mm}")
        y -= 14
        c.drawString(margin_x, y, f"Species: {attributes.species or 'N/A'}")
        y -= 14
        c.drawString(margin_x, y, f"Hours post inoculation: {attributes.hours_post_inoculation}")
        y -= 14
        c.drawString(margin_x, y, f"Volume: {attributes.volume}")
        y -= 14
        c.drawString(margin_x, y, f"Treatment: {attributes.treatment_description or 'N/A'}")
        y -= 14
        c.drawString(margin_x, y, f"Notes: {attributes.notes or 'N/A'}")
        y -= 18
        c.drawString(margin_x, y, f"Colony count: {derived.get('colony_count', 0)}")
        y -= 14
        c.drawString(margin_x, y, f"Volume adjusted count: {derived.get('volume_adjusted_count', 0)}")
        y -= 14
        average_color_hex = derived.get("average_color_hex", "N/A")
        avg_rgb = (0.0, 0.0, 0.0)
        if assets["original"] and os.path.exists(assets["original"]):
            avg_rgb = compute_average_color(assets["original"])
        c.setFillColorRGB(avg_rgb[0] / 255.0, avg_rgb[1] / 255.0, avg_rgb[2] / 255.0)
        c.drawString(margin_x, y, f"Average color: {average_color_hex}")
        c.setFillColor(colors.black)
        y -= 16
        c.drawString(
            margin_x,
            y,
            f"Colony density (per mm^2): {derived.get('colony_density_per_mm2', 0)}",
        )
        y -= 14
        c.drawString(margin_x, y, f"mm per pixel: {derived.get('mm_per_pixel', 'N/A')}")
        y -= 14
        c.drawString(margin_x, y, f"Mean area (mm^2): {derived.get('mean_area_mm2', 'N/A')}")
        y -= 14
        c.drawString(margin_x, y, f"Mean perimeter (mm): {derived.get('mean_perimeter_mm', 'N/A')}")
        y -= 18
        c.setFont("Helvetica-Bold", 11)
        c.drawString(margin_x, y, "Mean Metrics")
        y -= 12
        c.setFont("Helvetica", 9)
        for key, value in plate.summary_stats.items():
            c.drawString(margin_x + 10, y, f"{key}: {value}")
            y -= 10

        # Images row (side by side)
        images_top = y - 12
        image_row_height = 200
        image_width = (width - margin_x * 2 - 20) / 2
        image_y = images_top - image_row_height
        if assets["original"] and os.path.exists(assets["original"]):
            c.drawImage(
                assets["original"],
                margin_x,
                image_y,
                width=image_width,
                height=image_row_height,
                preserveAspectRatio=True,
                anchor="c",
            )
        else:
            c.drawString(margin_x, image_y + image_row_height / 2, "Original image missing")
        if assets["overlay"] and os.path.exists(assets["overlay"]):
            c.drawImage(
                assets["overlay"],
                margin_x + image_width + 20,
                image_y,
                width=image_width,
                height=image_row_height,
                preserveAspectRatio=True,
                anchor="c",
            )
        else:
            c.drawString(
                margin_x + image_width + 20,
                image_y + image_row_height / 2,
                "Overlay image missing",
            )

        # Box plot below images
        boxplot_height = 130
        boxplot_y = image_y - boxplot_height - 20
        boxplot_width = (width - margin_x * 2 - 20) / 2
        c.setFont("Helvetica-Bold", 11)
        c.drawString(margin_x, boxplot_y + boxplot_height + 6, "Morphology Box Plots (Size)")
        c.drawString(
            margin_x + boxplot_width + 20,
            boxplot_y + boxplot_height + 6,
            "Morphology Box Plots (Shape)",
        )
        if assets["boxplot_size"] and os.path.exists(assets["boxplot_size"]):
            c.drawImage(
                assets["boxplot_size"],
                margin_x,
                boxplot_y,
                width=boxplot_width,
                height=boxplot_height,
                preserveAspectRatio=True,
                anchor="c",
            )
        else:
            c.drawString(margin_x, boxplot_y + boxplot_height / 2, "Size plot missing")
        if assets["boxplot_shape"] and os.path.exists(assets["boxplot_shape"]):
            c.drawImage(
                assets["boxplot_shape"],
                margin_x + boxplot_width + 20,
                boxplot_y,
                width=boxplot_width,
                height=boxplot_height,
                preserveAspectRatio=True,
                anchor="c",
            )
        else:
            c.drawString(
                margin_x + boxplot_width + 20,
                boxplot_y + boxplot_height / 2,
                "Shape plot missing",
            )

        c.showPage()
        c.save()
        return FileResponse(report_path, filename=f"plate_{plate_id}_report.pdf")

    raise HTTPException(status_code=400, detail="format must be 'md' or 'pdf'")
