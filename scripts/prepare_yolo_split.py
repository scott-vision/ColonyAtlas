import argparse
import os
import random
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"}


def is_image(path: Path) -> bool:
    return path.suffix.lower() in IMAGE_EXTS


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def is_yoloseg_label_empty(label_path: Path) -> bool:
    if not label_path.exists():
        return True
    txt = read_text(label_path).strip()
    if not txt:
        return True
    lines = [ln.strip() for ln in txt.splitlines() if ln.strip()]
    return len(lines) == 0


def rewrite_to_single_class(label_in: Path, label_out: Path) -> None:
    label_out.parent.mkdir(parents=True, exist_ok=True)
    if not label_in.exists():
        label_out.write_text("", encoding="utf-8")
        return

    lines = [ln.strip() for ln in read_text(label_in).splitlines() if ln.strip()]
    if not lines:
        label_out.write_text("", encoding="utf-8")
        return

    new_lines = []
    for line in lines:
        parts = line.split()
        if len(parts) < 3:
            continue
        new_lines.append("0 " + " ".join(parts[1:]))

    label_out.write_text("\n".join(new_lines) + ("\n" if new_lines else ""), encoding="utf-8")


def pair_images_labels(
    input_dir: Path,
    images_subdir: Optional[str] = None,
    labels_subdir: Optional[str] = None,
) -> List[Tuple[Path, Path]]:
    if images_subdir:
        img_root = input_dir / images_subdir
        images = [p for p in img_root.rglob("*") if p.is_file() and is_image(p)]
    else:
        images = [p for p in input_dir.rglob("*") if p.is_file() and is_image(p)]

    pairs = []
    for img in images:
        stem = img.stem
        if labels_subdir:
            label = input_dir / labels_subdir / f"{stem}.txt"
        else:
            label1 = img.parent.parent / "labels" / f"{stem}.txt"
            label2 = img.parent / f"{stem}.txt"
            label = label1 if label1.exists() else label2
            if not label.exists():
                matches = list(input_dir.rglob(f"{stem}.txt"))
                label = matches[0] if matches else label2
        pairs.append((img, label))
    return pairs


def split_balance_and_convert_to_one_class_3way(
    input_dir: str,
    output_dir: str,
    train_frac: float = 0.7,
    val_frac: float = 0.15,
    test_frac: float = 0.15,
    seed: int = 0,
    images_subdir: Optional[str] = None,
    labels_subdir: Optional[str] = None,
    copy_images: bool = True,
    balance_empty_ratio: float = 0.5,
) -> Dict[str, int]:
    total = train_frac + val_frac + test_frac
    if abs(total - 1.0) > 1e-6:
        raise ValueError("train_frac + val_frac + test_frac must equal 1.0")
    if not (0.0 < train_frac < 1.0 and 0.0 < val_frac < 1.0 and 0.0 < test_frac < 1.0):
        raise ValueError("train/val/test fractions must be between 0 and 1")
    if balance_empty_ratio <= 0 or balance_empty_ratio >= 1:
        raise ValueError("balance_empty_ratio must be between 0 and 1")

    in_dir = Path(input_dir)
    out_dir = Path(output_dir)

    out_img_train = out_dir / "images" / "train"
    out_img_val = out_dir / "images" / "val"
    out_img_test = out_dir / "images" / "test"

    out_lbl_train = out_dir / "labels" / "train"
    out_lbl_val = out_dir / "labels" / "val"
    out_lbl_test = out_dir / "labels" / "test"

    for p in [out_img_train, out_img_val, out_img_test, out_lbl_train, out_lbl_val, out_lbl_test]:
        p.mkdir(parents=True, exist_ok=True)

    rng = random.Random(seed)
    pairs = pair_images_labels(in_dir, images_subdir=images_subdir, labels_subdir=labels_subdir)
    if not pairs:
        raise ValueError(f"No images found under: {input_dir}")

    empty_pairs: List[Tuple[Path, Path]] = []
    nonempty_pairs: List[Tuple[Path, Path]] = []
    missing_label = 0

    for img, lbl in pairs:
        if not lbl.exists():
            missing_label += 1
        if is_yoloseg_label_empty(lbl):
            empty_pairs.append((img, lbl))
        else:
            nonempty_pairs.append((img, lbl))

    max_empty_to_keep = int(
        round((balance_empty_ratio / (1.0 - balance_empty_ratio)) * len(nonempty_pairs))
    )
    empty_target = min(len(empty_pairs), max_empty_to_keep)

    rng.shuffle(empty_pairs)
    empty_pairs_bal = empty_pairs[:empty_target]

    def split_3way(
        items: List[Tuple[Path, Path]],
    ) -> Tuple[List[Tuple[Path, Path]], List[Tuple[Path, Path]], List[Tuple[Path, Path]]]:
        rng.shuffle(items)
        n = len(items)
        n_train = int(round(train_frac * n))
        n_val = int(round(val_frac * n))
        n_train = min(n_train, n)
        n_val = min(n_val, n - n_train)
        train = items[:n_train]
        val = items[n_train : n_train + n_val]
        test = items[n_train + n_val :]
        return train, val, test

    train_non, val_non, test_non = split_3way(nonempty_pairs)
    train_emp, val_emp, test_emp = split_3way(empty_pairs_bal)

    train_set = train_non + train_emp
    val_set = val_non + val_emp
    test_set = test_non + test_emp

    rng.shuffle(train_set)
    rng.shuffle(val_set)
    rng.shuffle(test_set)

    def emit(split: List[Tuple[Path, Path]], img_out_root: Path, lbl_out_root: Path):
        for img, lbl in split:
            dst_img = img_out_root / img.name
            dst_lbl = lbl_out_root / f"{img.stem}.txt"
            if copy_images:
                shutil.copy2(img, dst_img)
            else:
                if dst_img.exists():
                    dst_img.unlink()
                os.symlink(str(img), str(dst_img))
            rewrite_to_single_class(lbl, dst_lbl)

    emit(train_set, out_img_train, out_lbl_train)
    emit(val_set, out_img_val, out_lbl_val)
    emit(test_set, out_img_test, out_lbl_test)

    def count_empty(label_dir: Path) -> int:
        return sum(1 for p in label_dir.glob("*.txt") if is_yoloseg_label_empty(p))

    stats = {
        "found_images": len(pairs),
        "missing_label_files_treated_as_empty": missing_label,
        "original_empty": len(empty_pairs),
        "original_nonempty": len(nonempty_pairs),
        "kept_empty": len(empty_pairs_bal),
        "kept_nonempty": len(nonempty_pairs),
        "kept_total": len(train_set) + len(val_set) + len(test_set),
        "train_images": len(train_set),
        "val_images": len(val_set),
        "test_images": len(test_set),
        "train_empty_labels": count_empty(out_lbl_train),
        "val_empty_labels": count_empty(out_lbl_val),
        "test_empty_labels": count_empty(out_lbl_test),
    }
    stats["train_nonempty_labels"] = stats["train_images"] - stats["train_empty_labels"]
    stats["val_nonempty_labels"] = stats["val_images"] - stats["val_empty_labels"]
    stats["test_nonempty_labels"] = stats["test_images"] - stats["test_empty_labels"]
    return stats


def main() -> None:
    parser = argparse.ArgumentParser(description="Split YOLO-seg dataset into train/val/test.")
    parser.add_argument("--input-dir", required=True, help="Source dataset directory.")
    parser.add_argument("--output-dir", required=True, help="Output directory for split.")
    parser.add_argument("--train-frac", type=float, default=0.8)
    parser.add_argument("--val-frac", type=float, default=0.1)
    parser.add_argument("--test-frac", type=float, default=0.1)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--images-subdir", default=None)
    parser.add_argument("--labels-subdir", default=None)
    parser.add_argument("--copy-images", action="store_true", default=True)
    parser.add_argument("--symlink-images", action="store_true", default=False)
    parser.add_argument("--balance-empty-ratio", type=float, default=0.5)
    args = parser.parse_args()

    copy_images = args.copy_images and not args.symlink_images
    stats = split_balance_and_convert_to_one_class_3way(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        train_frac=args.train_frac,
        val_frac=args.val_frac,
        test_frac=args.test_frac,
        seed=args.seed,
        images_subdir=args.images_subdir,
        labels_subdir=args.labels_subdir,
        copy_images=copy_images,
        balance_empty_ratio=args.balance_empty_ratio,
    )
    print(stats)


if __name__ == "__main__":
    main()
