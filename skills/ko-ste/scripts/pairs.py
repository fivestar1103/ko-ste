"""사람이 고친 기술 문서 전후 쌍을 규칙 ID나 낱말로 찾는다.

자료는 ../data/의 jsonl이다. 2022-10-31 이전에 공개 기술 문서 번역 저장소에서
사람이 고친 문장만 모았다. 출처와 이용 조건은 ../PAIRS-NOTICE.md에 있다.

사용:
    python scripts/pairs.py --rule SE-2
    python scripts/pairs.py --rule LX-3 --grep 수행 -n 10
    python scripts/pairs.py --stats
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from collections import Counter
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / "data"


def load() -> list[dict]:
    rows = []
    for f in sorted(DATA.glob("pairs*.jsonl")):
        rows.extend(json.loads(l) for l in f.open(encoding="utf-8") if l.strip())
    return rows


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--rule", help="규칙 ID (예: SE-2)")
    ap.add_argument("--grep", help="고치기 전이나 고친 글에 든 낱말")
    ap.add_argument("-n", type=int, default=5, help="보여 줄 쌍 수")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--stats", action="store_true", help="규칙별 쌍 수만 보여 준다")
    args = ap.parse_args()

    rows = load()
    if args.stats:
        c = Counter(r for row in rows for r in row["rules"])
        for rule, n in sorted(c.items()):
            print(f"{rule}\t{n}")
        print(f"전체\t{len(rows)}")
        return
    if args.rule:
        rows = [r for r in rows if args.rule in r["rules"]]
    if args.grep:
        rows = [r for r in rows if args.grep in r["before"] or args.grep in r["after"]]
    random.Random(args.seed).shuffle(rows)
    for r in rows[: args.n]:
        print(f"[{r['id']}] {', '.join(r['rules'])} · {r['source']} ({r['license']})")
        print(f"  전: {r['before']}")
        print(f"  후: {r['after']}")
    print(f"({min(args.n, len(rows))}/{len(rows)}쌍)")


if __name__ == "__main__":
    main()
