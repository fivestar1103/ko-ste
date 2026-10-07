"""고정 말뭉치의 집계를 엄격하게 대조하고 차이 위치를 출력한다."""

import argparse
import json
from pathlib import Path


def differences(expected, actual, path="$"):
    if isinstance(expected, dict) and isinstance(actual, dict):
        for key in sorted(expected.keys() | actual.keys()):
            child = f"{path}.{key}"
            if key not in expected or key not in actual:
                yield f"{child}: missing key"
            else:
                yield from differences(expected[key], actual[key], child)
    elif expected != actual:
        yield f"{path}: recorded={expected!r}, reproduced={actual!r}"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("actual")
    parser.add_argument("--expected", default="calibration/data/measure.json")
    args = parser.parse_args()
    expected = json.loads(Path(args.expected).read_text(encoding="utf-8"))
    actual = json.loads(Path(args.actual).read_text(encoding="utf-8"))
    changes = list(differences(expected, actual))
    if changes:
        print("\n".join(changes[:40]))
        raise SystemExit(f"Corpus measurements differ at {len(changes)} fields.")
    print("Corpus measurements match exactly.")


if __name__ == "__main__":
    main()
