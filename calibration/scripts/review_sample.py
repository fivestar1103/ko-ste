"""사람 검수용 표본을 뽑는다.

스킬에 넣은 쌍(skills/ko-ste/data/)에서 출처별로 고르게 무작위 표본을 뽑는다.
표본의 쌍 id는 calibration/data/pairs-review.json에 남긴다. 검수 결과도 같은 파일에 적는다.

사용:
    uv run python calibration/scripts/review_sample.py -n 100
"""

from __future__ import annotations

import argparse
import json
import random
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("-n", type=int, default=100)
    ap.add_argument("--seed", type=int, default=13)
    ap.add_argument("--out", default=str(ROOT / "calibration/data/pairs-review.json"))
    args = ap.parse_args()

    manifest = json.loads((ROOT / "calibration/pairs-manifest.json").read_text(encoding="utf-8"))
    repos = {s["id"]: s["repo"].removesuffix(".git") for s in manifest["sources"]}
    rows = []
    for name in ("pairs", "pairs-cc-by-sa"):
        path = ROOT / "skills/ko-ste/data" / f"{name}.jsonl"
        rows += [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]
    by_source: dict[str, list[dict]] = defaultdict(list)
    for r in sorted(rows, key=lambda r: r["id"]):
        by_source[r["source"]].append(r)
    rng = random.Random(args.seed)
    for items in by_source.values():
        rng.shuffle(items)
    # 출처마다 쌍 수에 비례해 뽑되, 작은 출처도 최소 2개는 넣는다.
    total = len(rows)
    quota = {s: max(2, round(args.n * len(items) / total)) for s, items in by_source.items()}
    while sum(quota.values()) > args.n:
        biggest = max(quota, key=lambda s: quota[s])
        quota[biggest] -= 1
    picked = []
    for s, items in sorted(by_source.items()):
        picked += items[: quota[s]]
    rng.shuffle(picked)
    sample = [{
        "id": r["id"], "order": i, "source": r["source"], "repo": repos[r["source"]], "commit": r["commit"],
        "date": r["date"], "purpose": r["purpose"], "rules": r["rules"], "before": r["before"], "after": r["after"],
        "label_note": r["label_note"],
    } for i, r in enumerate(picked)]
    out = {"seed": args.seed, "n": len(sample), "of": total, "ids": [s["id"] for s in sample], "reviews": {}}
    Path(args.out).write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    seed = ROOT / "calibration/cache/review/pairs-sample.json"
    seed.parent.mkdir(parents=True, exist_ok=True)
    seed.write_text(json.dumps(sample, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(sample)} of {total}: {dict(sorted(quota.items()))}")


if __name__ == "__main__":
    main()
