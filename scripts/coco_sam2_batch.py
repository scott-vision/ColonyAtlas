from __future__ import annotations

import argparse
import glob
import json
import os
from typing import Dict, List, Optional, Sequence

import cv2
import numpy as np
from PIL import Image

from pycocotools.coco import COCO
from ultralytics import SAM

COMMON_IMAGE_SUBDIRS = ("images", "img", "train", "val", "valid", "test", "dataset", "data")


def find_coco_json(dataset_dir: str) -> str:
    jsons = sorted(glob.glob(os.path.join(dataset_dir, "*.json")))
    if not jsons:
        jsons = sorted(glob.glob(os.path.join(dataset_dir, "**", "*.json"), recursive=True))
    if not jsons:
        raise FileNotFoundError(f"No COCO .json found under: {dataset_dir}")
    for cand in jsons:
        name = os.path.basename(cand).lower()
        if "instances" in name or "annotations" in name or "coco" in name:
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
    raise FileNotFoundError(f"Cannot resolve image file_name='{file_name}' under '{dataset_dir}'")


def load_rgb(image_path: str) -> np.ndarray:
    return np.array(Image.open(image_path).convert("RGB"))


def coco_xywh_to_xyxy(b: Sequence[float]) -> List[float]:
    x, y, w, h = b
    return [x, y, x + w, y + h]


def predict_sam2_from_bboxes(
    sam_model: SAM,
    image_rgb: np.ndarray,
    bboxes_xyxy: np.ndarray,
    device: Optional[str] = None,
) -> np.ndarray:
    h, w = image_rgb.shape[:2]
    if bboxes_xyxy is None or len(bboxes_xyxy) == 0:
        return np.zeros((0, h, w), dtype=bool)
    bboxes_list = bboxes_xyxy.tolist()
    try:
        results = sam_model.predict(image_rgb, bboxes=bboxes_list, device=device, verbose=False)
    except TypeError:
        results = sam_model(image_rgb, bboxes=bboxes_list, device=device, verbose=False)
    r0 = results[0] if isinstance(results, (list, tuple)) else results
    if getattr(r0, "masks", None) is None or r0.masks is None:
        return np.zeros((0, h, w), dtype=bool)
    data = r0.masks.data
    try:
        import torch

        if isinstance(data, torch.Tensor):
            masks = data.detach().cpu().numpy().astype(bool)
        else:
            masks = np.array(data).astype(bool)
    except Exception:
        masks = np.array(data).astype(bool)
    if masks.ndim == 2:
        masks = masks[None, ...]
    return masks


def save_instance_id_mask(
    masks: np.ndarray, out_path: str, overlap_policy: str = "small_overwrites"
) -> np.ndarray:
    if masks.ndim != 3:
        raise ValueError("masks must be (N,H,W)")
    n, h, w = masks.shape
    inst = np.zeros((h, w), dtype=np.uint16)
    if n == 0:
        Image.fromarray(inst, mode="I;16").save(out_path)
        return inst
    areas = masks.reshape(n, -1).sum(axis=1)
    if overlap_policy == "small_overwrites":
        order = np.argsort(areas)
    elif overlap_policy == "large_overwrites":
        order = np.argsort(-areas)
    elif overlap_policy == "first_wins":
        order = np.arange(n)
    elif overlap_policy == "last_wins":
        order = np.arange(n)
    else:
        raise ValueError(f"Unknown overlap_policy: {overlap_policy}")
    if overlap_policy == "first_wins":
        for idx in order:
            m = masks[idx]
            writeable = (inst == 0) & m
            inst[writeable] = idx + 1
    else:
        for idx in order:
            inst[masks[idx]] = idx + 1
    Image.fromarray(inst, mode="I;16").save(out_path)
    return inst


def instance_mask_to_yolo_polygon_line(
    instance_binary_mask: np.ndarray,
    class_id: int,
    eps_frac: float = 0.002,
    min_area: float = 4.0,
    keep_largest_contour: bool = True,
) -> Optional[str]:
    m = instance_binary_mask.astype(np.uint8) * 255
    h, w = m.shape[:2]
    contours, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None
    if keep_largest_contour:
        contours = [max(contours, key=cv2.contourArea)]
    cnt = contours[0]
    area = float(cv2.contourArea(cnt))
    if area < min_area:
        return None
    eps = eps_frac * cv2.arcLength(cnt, True)
    approx = cv2.approxPolyDP(cnt, eps, True).reshape(-1, 2)
    if approx.shape[0] < 3:
        return None
    pts = []
    for (x, y) in approx:
        pts.append(f"{x / w:.6f}")
        pts.append(f"{y / h:.6f}")
    return f"{class_id} " + " ".join(pts)


def sam2_coco_to_instmask_and_yoloseg_resume(
    dataset_dir: str,
    out_dir: str,
    sam2_weights: str = "sam2_b.pt",
    device: Optional[str] = None,
    eps_frac: float = 0.002,
    min_box_area: float = 1.0,
    max_boxes_per_image: Optional[int] = None,
    overlap_policy: str = "small_overwrites",
    write_empty_label_files: bool = True,
    skip_existing: bool = True,
    strict_skip: bool = False,
    force_redo: bool = False,
):
    if not os.path.isabs(dataset_dir):
        raise ValueError("dataset_dir must be an absolute path.")
    os.makedirs(out_dir, exist_ok=True)
    masks_dir = os.path.join(out_dir, "masks_16bit")
    labels_dir = os.path.join(out_dir, "labels_yoloseg")
    meta_dir = os.path.join(out_dir, "meta")
    os.makedirs(masks_dir, exist_ok=True)
    os.makedirs(labels_dir, exist_ok=True)
    os.makedirs(meta_dir, exist_ok=True)
    ann_path = find_coco_json(dataset_dir)
    coco = COCO(ann_path)
    cats = coco.loadCats(coco.getCatIds())
    cats = sorted(cats, key=lambda c: int(c["id"]))
    category_id_to_class_id = {int(c["id"]): i for i, c in enumerate(cats)}
    classes = [c.get("name", str(c["id"])) for c in cats]
    with open(os.path.join(out_dir, "category_id_to_class_id.json"), "w") as f:
        json.dump(category_id_to_class_id, f, indent=2)
    with open(os.path.join(out_dir, "classes.json"), "w") as f:
        json.dump(classes, f, indent=2)

    sam_model = SAM(sam2_weights)
    img_ids = coco.getImgIds()
    total = len(img_ids)
    if total == 0:
        raise ValueError("No images found in COCO annotation.")
    skipped = 0
    processed = 0
    errors = 0

    for idx, img_id in enumerate(img_ids, start=1):
        img_info = coco.loadImgs([img_id])[0]
        file_name = img_info["file_name"]
        stem = os.path.splitext(os.path.basename(file_name))[0]
        inst_path = os.path.join(masks_dir, f"{stem}_inst.png")
        label_path = os.path.join(labels_dir, f"{stem}.txt")
        meta_path = os.path.join(meta_dir, f"{stem}.json")

        if not force_redo and skip_existing:
            mask_ok = os.path.exists(inst_path)
            meta_ok = os.path.exists(meta_path)
            label_ok = os.path.exists(label_path)
            done = (mask_ok and meta_ok and label_ok) if strict_skip else (mask_ok and meta_ok)
            if done:
                skipped += 1
                if idx % 200 == 0 or idx == total:
                    print(f"[{idx}/{total}] skipped={skipped} processed={processed} errors={errors}")
                continue

        try:
            image_path = resolve_image_path(dataset_dir, file_name)
            image_rgb = load_rgb(image_path)
            h, w = image_rgb.shape[:2]
            ann_ids = coco.getAnnIds(imgIds=[img_id], iscrowd=None)
            anns = coco.loadAnns(ann_ids)
            bboxes = []
            cat_ids = []
            ann_ids_kept = []
            for ann in anns:
                if "bbox" not in ann:
                    continue
                x, y, bw, bh = ann["bbox"]
                if (bw * bh) < min_box_area:
                    continue
                bboxes.append(coco_xywh_to_xyxy(ann["bbox"]))
                cat_ids.append(int(ann.get("category_id", -1)))
                ann_ids_kept.append(int(ann.get("id", -1)))
            bboxes_xyxy = np.array(bboxes, dtype=np.float32) if bboxes else np.zeros((0, 4), dtype=np.float32)
            if max_boxes_per_image is not None and len(bboxes_xyxy) > max_boxes_per_image:
                bboxes_xyxy = bboxes_xyxy[:max_boxes_per_image]
                cat_ids = cat_ids[:max_boxes_per_image]
                ann_ids_kept = ann_ids_kept[:max_boxes_per_image]

            masks = predict_sam2_from_bboxes(sam_model, image_rgb, bboxes_xyxy, device=device)
            inst_u16 = save_instance_id_mask(masks, inst_path, overlap_policy=overlap_policy)
            label_lines: List[str] = []
            instances_meta: List[Dict] = []

            num_instances = int(inst_u16.max())
            for inst_id in range(1, num_instances + 1):
                idx0 = inst_id - 1
                if idx0 >= len(cat_ids):
                    continue
                coco_cat = cat_ids[idx0]
                if coco_cat not in category_id_to_class_id:
                    continue
                class_id = category_id_to_class_id[coco_cat]
                bin_mask = inst_u16 == inst_id
                yolo_line = instance_mask_to_yolo_polygon_line(
                    instance_binary_mask=bin_mask,
                    class_id=class_id,
                    eps_frac=eps_frac,
                    min_area=4.0,
                    keep_largest_contour=True,
                )
                if yolo_line is not None:
                    label_lines.append(yolo_line)
                instances_meta.append(
                    {
                        "instance_id": int(inst_id),
                        "coco_category_id": int(coco_cat),
                        "yolo_class_id": int(class_id),
                        "source_bbox_xyxy": [float(x) for x in bboxes_xyxy[idx0].tolist()]
                        if idx0 < len(bboxes_xyxy)
                        else None,
                        "source_ann_id": int(ann_ids_kept[idx0])
                        if idx0 < len(ann_ids_kept)
                        else None,
                    }
                )

            if label_lines or write_empty_label_files:
                with open(label_path, "w") as f:
                    f.write("\n".join(label_lines) + ("\n" if label_lines else ""))

            meta = {
                "image_id": int(img_id),
                "file_name": file_name,
                "image_path": image_path,
                "width": int(w),
                "height": int(h),
                "instance_mask_16bit": os.path.basename(inst_path),
                "num_instances": int(num_instances),
                "instances": instances_meta,
            }
            with open(meta_path, "w") as f:
                json.dump(meta, f, indent=2)

            processed += 1
        except Exception as exc:
            errors += 1
            err_path = os.path.join(meta_dir, f"{stem}.error.txt")
            with open(err_path, "w") as f:
                f.write(repr(exc))
            print(f"[ERROR] {file_name} -> {exc}")

        if idx % 50 == 0 or idx == total:
            print(f"[{idx}/{total}] skipped={skipped} processed={processed} errors={errors}")

    print("Done.")
    print(f"Skipped:   {skipped}")
    print(f"Processed: {processed}")
    print(f"Errors:    {errors}")
    print(f"Instance masks: {masks_dir}")
    print(f"YOLO-SEG labels: {labels_dir}")
    print(f"Metadata: {meta_dir}")
    print(f"Class mapping: {os.path.join(out_dir, 'classes.json')}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Batch SAM2 COCO -> instance masks + YOLO-seg labels.")
    parser.add_argument("--dataset-dir", required=True, help="Absolute dataset directory.")
    parser.add_argument("--out-dir", required=True, help="Output directory.")
    parser.add_argument("--sam2-weights", default="sam2_b.pt")
    parser.add_argument("--device", default=None)
    parser.add_argument("--eps-frac", type=float, default=0.002)
    parser.add_argument("--min-box-area", type=float, default=1.0)
    parser.add_argument("--max-boxes", type=int, default=None)
    parser.add_argument("--overlap-policy", default="small_overwrites")
    parser.add_argument("--skip-existing", action="store_true", default=True)
    parser.add_argument("--strict-skip", action="store_true", default=False)
    parser.add_argument("--force-redo", action="store_true", default=False)
    args = parser.parse_args()

    sam2_coco_to_instmask_and_yoloseg_resume(
        dataset_dir=args.dataset_dir,
        out_dir=args.out_dir,
        sam2_weights=args.sam2_weights,
        device=args.device,
        eps_frac=args.eps_frac,
        min_box_area=args.min_box_area,
        max_boxes_per_image=args.max_boxes,
        overlap_policy=args.overlap_policy,
        skip_existing=args.skip_existing,
        strict_skip=args.strict_skip,
        force_redo=args.force_redo,
    )


if __name__ == "__main__":
    main()
