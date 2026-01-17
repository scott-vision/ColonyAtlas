from __future__ import annotations

import argparse
import glob
import os
import random
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

try:
    from pycocotools.coco import COCO
except Exception as exc:
    raise ImportError("pycocotools is required. Install via: pip install pycocotools") from exc

try:
    from ultralytics import SAM
except Exception as exc:
    raise ImportError("ultralytics is required. Install via: pip install ultralytics") from exc

COMMON_IMAGE_SUBDIRS = ("images", "img", "train", "val", "valid", "test", "dataset", "data")


def find_coco_json(dataset_dir: str) -> str:
    jsons = sorted(glob.glob(os.path.join(dataset_dir, "*.json")))
    if not jsons:
        jsons = sorted(glob.glob(os.path.join(dataset_dir, "**", "*.json"), recursive=True))
    if not jsons:
        raise FileNotFoundError(f"No .json COCO annotation file found under: {dataset_dir}")
    for cand in jsons:
        name = os.path.basename(cand).lower()
        if "instances" in name or "coco" in name or "annotations" in name:
            return cand
    return jsons[0]


def resolve_image_path(dataset_dir: str, file_name: str) -> str:
    if os.path.isabs(file_name) and os.path.exists(file_name):
        return file_name
    p = os.path.join(dataset_dir, file_name)
    if os.path.exists(p):
        return p
    for sub in COMMON_IMAGE_SUBDIRS:
        p2 = os.path.join(dataset_dir, sub, file_name)
        if os.path.exists(p2):
            return p2
    base = os.path.basename(file_name)
    matches = glob.glob(os.path.join(dataset_dir, "**", base), recursive=True)
    matches = [m for m in matches if os.path.isfile(m)]
    if matches:
        return matches[0]
    raise FileNotFoundError(
        f"Could not resolve image path for COCO file_name='{file_name}' under '{dataset_dir}'"
    )


def load_rgb(image_path: str) -> np.ndarray:
    im = Image.open(image_path).convert("RGB")
    return np.array(im)


def coco_xywh_to_xyxy(b: Sequence[float]) -> Tuple[float, float, float, float]:
    x, y, w, h = b
    return (x, y, x + w, y + h)


def draw_bboxes(ax, bboxes_xyxy: np.ndarray, labels: Optional[List[str]] = None, linewidth: float = 2.0):
    import matplotlib.patches as patches

    for i, (x1, y1, x2, y2) in enumerate(bboxes_xyxy):
        rect = patches.Rectangle((x1, y1), (x2 - x1), (y2 - y1), fill=False, linewidth=linewidth)
        ax.add_patch(rect)
        if labels:
            ax.text(
                x1,
                y1,
                labels[i],
                fontsize=10,
                verticalalignment="top",
                bbox=dict(facecolor="white", alpha=0.6),
            )


def overlay_masks(ax, masks: np.ndarray, alpha: float = 0.45):
    if masks is None or len(masks) == 0:
        return
    masks = masks.astype(bool)
    h, w = masks.shape[-2], masks.shape[-1]
    color_cycle = plt.rcParams["axes.prop_cycle"].by_key().get("color", ["C0", "C1", "C2"])
    for i, m in enumerate(masks):
        if m.shape != (h, w):
            continue
        color = color_cycle[i % len(color_cycle)]
        overlay = np.zeros((h, w, 4), dtype=np.float32)
        rgb = np.array(plt.matplotlib.colors.to_rgb(color), dtype=np.float32)
        overlay[..., :3] = rgb
        overlay[..., 3] = m.astype(np.float32) * alpha
        ax.imshow(overlay)


@dataclass
class COCOImageSample:
    image_id: int
    file_name: str
    image_path: str
    bboxes_xyxy: np.ndarray
    cat_ids: List[int]


def get_samples_from_coco(
    coco: COCO,
    dataset_dir: str,
    image_ids: Sequence[int],
    max_boxes: Optional[int] = None,
    min_box_area: float = 1.0,
) -> List[COCOImageSample]:
    samples: List[COCOImageSample] = []
    for img_id in image_ids:
        img_info = coco.loadImgs([img_id])[0]
        file_name = img_info["file_name"]
        image_path = resolve_image_path(dataset_dir, file_name)
        ann_ids = coco.getAnnIds(imgIds=[img_id], iscrowd=None)
        anns = coco.loadAnns(ann_ids)
        bboxes = []
        cat_ids = []
        for ann in anns:
            if "bbox" not in ann:
                continue
            x, y, w, h = ann["bbox"]
            if w * h < min_box_area:
                continue
            bboxes.append(coco_xywh_to_xyxy((x, y, w, h)))
            cat_ids.append(int(ann.get("category_id", -1)))
        if len(bboxes) == 0:
            bboxes_xyxy = np.zeros((0, 4), dtype=np.float32)
        else:
            bboxes_xyxy = np.array(bboxes, dtype=np.float32)
            if max_boxes is not None and len(bboxes_xyxy) > max_boxes:
                bboxes_xyxy = bboxes_xyxy[:max_boxes]
                cat_ids = cat_ids[:max_boxes]
        samples.append(
            COCOImageSample(
                image_id=int(img_id),
                file_name=file_name,
                image_path=image_path,
                bboxes_xyxy=bboxes_xyxy,
                cat_ids=cat_ids,
            )
        )
    return samples


def predict_sam2_from_bboxes(
    sam_model: SAM,
    image_rgb: np.ndarray,
    bboxes_xyxy: np.ndarray,
    device: Optional[str] = None,
):
    if bboxes_xyxy is None or len(bboxes_xyxy) == 0:
        return np.zeros((0, image_rgb.shape[0], image_rgb.shape[1]), dtype=bool), None
    bboxes_list = bboxes_xyxy.tolist()
    try:
        results = sam_model.predict(image_rgb, bboxes=bboxes_list, device=device, verbose=False)
    except TypeError:
        try:
            results = sam_model(image_rgb, bboxes=bboxes_list, device=device, verbose=False)
        except Exception:
            results = sam_model.predict(image_rgb)
    r0 = results[0] if isinstance(results, (list, tuple)) else results
    masks = None
    if hasattr(r0, "masks") and r0.masks is not None:
        data = r0.masks.data
        try:
            import torch

            if isinstance(data, torch.Tensor):
                masks = data.detach().cpu().numpy().astype(bool)
            else:
                masks = np.array(data).astype(bool)
        except Exception:
            masks = np.array(data).astype(bool)
    if masks is None:
        masks = np.zeros((0, image_rgb.shape[0], image_rgb.shape[1]), dtype=bool)
    return masks, r0


def show_coco_sam2_grid(
    dataset_dir: str,
    n: int = 6,
    filenames: Optional[Sequence[str]] = None,
    seed: int = 0,
    sam2_weights: str = "sam2_b.pt",
    device: Optional[str] = None,
    max_boxes_per_image: Optional[int] = None,
    min_box_area: float = 1.0,
    figsize_per_row: Tuple[float, float] = (14.0, 5.0),
):
    if not os.path.isabs(dataset_dir):
        raise ValueError("Please provide an absolute path for dataset_dir.")
    ann_path = find_coco_json(dataset_dir)
    coco = COCO(ann_path)
    sam_model = SAM(sam2_weights)
    all_img_ids = coco.getImgIds()
    if not all_img_ids:
        raise ValueError("No images found in COCO annotations.")
    if filenames and len(filenames) > 0:
        imgs = coco.loadImgs(all_img_ids)
        fname_to_id: Dict[str, int] = {im["file_name"]: int(im["id"]) for im in imgs}
        missing = [f for f in filenames if f not in fname_to_id]
        if missing:
            raise ValueError("Filenames not found in COCO annotations:\n" + "\n".join(missing))
        chosen_ids = [fname_to_id[f] for f in filenames]
    else:
        rng = random.Random(seed)
        chosen_ids = rng.sample(all_img_ids, k=min(n, len(all_img_ids)))

    samples = get_samples_from_coco(
        coco=coco,
        dataset_dir=dataset_dir,
        image_ids=chosen_ids,
        max_boxes=max_boxes_per_image,
        min_box_area=min_box_area,
    )

    num_rows = len(samples)
    fig_w, fig_h = figsize_per_row
    fig, axes = plt.subplots(num_rows, 2, figsize=(fig_w, fig_h * num_rows), squeeze=False)

    for row, sample in enumerate(samples):
        image_rgb = load_rgb(sample.image_path)
        title = os.path.basename(sample.file_name)
        ax_left = axes[row, 0]
        ax_left.imshow(image_rgb)
        if len(sample.bboxes_xyxy) > 0:
            draw_bboxes(ax_left, sample.bboxes_xyxy)
        ax_left.set_title(f"{title}  |  COCO bboxes")
        ax_left.axis("off")

        ax_right = axes[row, 1]
        ax_right.imshow(image_rgb)
        masks, _raw = predict_sam2_from_bboxes(
            sam_model=sam_model, image_rgb=image_rgb, bboxes_xyxy=sample.bboxes_xyxy, device=device
        )
        if masks is not None and len(masks) > 0:
            overlay_masks(ax_right, masks, alpha=0.45)
        if len(sample.bboxes_xyxy) > 0:
            draw_bboxes(ax_right, sample.bboxes_xyxy, linewidth=1.5)
        ax_right.set_title(f"{title}  |  SAM2 from bboxes")
        ax_right.axis("off")

    plt.tight_layout()
    plt.show()


def main() -> None:
    parser = argparse.ArgumentParser(description="COCO viewer + SAM2 segmentation from COCO bboxes.")
    parser.add_argument("--dataset-dir", required=True, help="Absolute dataset directory.")
    parser.add_argument("--n", type=int, default=6)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--sam2-weights", default="sam2_b.pt")
    parser.add_argument("--device", default=None)
    parser.add_argument("--max-boxes", type=int, default=None)
    parser.add_argument("--min-box-area", type=float, default=1.0)
    parser.add_argument("--filenames", nargs="*", default=None)
    args = parser.parse_args()

    show_coco_sam2_grid(
        dataset_dir=args.dataset_dir,
        n=args.n,
        filenames=args.filenames,
        seed=args.seed,
        sam2_weights=args.sam2_weights,
        device=args.device,
        max_boxes_per_image=args.max_boxes,
        min_box_area=args.min_box_area,
    )


if __name__ == "__main__":
    main()
