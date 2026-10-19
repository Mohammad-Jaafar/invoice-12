import argparse
import shutil
from pathlib import Path

import cv2
import numpy as np

BORDER_GRAY = (235, 235, 235)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=Path("data/clean"))
    parser.add_argument("--target", type=Path, default=Path("data/scanned"))
    parser.add_argument("--seed", type=int, default=7)
    return parser.parse_args()


def degrade(image: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    height, width = image.shape[:2]
    angle = rng.uniform(-3, 3)
    matrix = cv2.getRotationMatrix2D((width / 2, height / 2), angle, 1.0)
    image = cv2.warpAffine(
        image,
        matrix,
        (width, height),
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=BORDER_GRAY,
    )
    kernel = int(rng.choice([3, 5]))
    image = cv2.GaussianBlur(image, (kernel, kernel), 0)
    noise = rng.normal(0, rng.uniform(3, 12), image.shape)
    brightness = rng.uniform(-25, 25)
    image = image.astype(np.float32) + noise + brightness
    return np.clip(image, 0, 255).astype(np.uint8)


def main() -> None:
    args = parse_args()
    args.target.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(args.seed)
    count = 0
    for path in sorted(args.source.glob("*.png")):
        image = degrade(cv2.imread(str(path)), rng)
        quality = int(rng.integers(40, 71))
        cv2.imwrite(
            str(args.target / f"{path.stem}.jpg"),
            image,
            [cv2.IMWRITE_JPEG_QUALITY, quality],
        )
        shutil.copyfile(path.with_suffix(".json"), args.target / f"{path.stem}.json")
        count += 1
    print(f"degraded {count} invoices into {args.target.as_posix()}")


if __name__ == "__main__":
    main()
