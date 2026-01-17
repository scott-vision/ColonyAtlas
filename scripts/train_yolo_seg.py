import argparse

from ultralytics import YOLO


def main() -> None:
    parser = argparse.ArgumentParser(description="Train a YOLO-seg model.")
    parser.add_argument("--model", default="yolo11n-seg.pt", help="Pretrained model.")
    parser.add_argument("--data", required=True, help="Path to data.yaml.")
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--batch", type=int, default=32)
    parser.add_argument("--device", default="0", help="GPU index or 'cpu'.")
    args = parser.parse_args()

    model = YOLO(args.model)
    model.train(
        data=args.data,
        imgsz=args.imgsz,
        epochs=args.epochs,
        batch=args.batch,
        device=args.device,
    )


if __name__ == "__main__":
    main()
