"""보정용 공개 문서를 고정 커밋으로 받는다.

원문은 calibration/cache/ 아래에만 두고 저장소에는 넣지 않는다.
받은 커밋 해시는 calibration/data/corpus-lock.json에 남긴다.

사용:
    uv run --no-project calibration/scripts/fetch_corpus.py \
        --manifest calibration/corpus-manifest.json --cache calibration/cache
"""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


def git(*args: str, cwd: Path | None = None) -> str:
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True, encoding="utf-8").stdout.strip()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", default="calibration/corpus-manifest.json")
    ap.add_argument("--cache", default="calibration/cache")
    ap.add_argument("--lock", default="calibration/data/corpus-lock.json")
    ap.add_argument("--refresh-lock", action="store_true", help="명시적으로 새 커밋을 선택한다. 기본은 기존 lock을 재현한다")
    args = ap.parse_args()

    manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    cache = Path(args.cache)
    cache.mkdir(parents=True, exist_ok=True)
    existing = json.loads(Path(args.lock).read_text(encoding="utf-8")) if Path(args.lock).exists() and not args.refresh_lock else {}
    lock = {}
    for src in manifest["sources"]:
        d = cache / src["id"]
        if not d.exists():
            git("clone", "-q", "--filter=blob:none", src["repo"], str(d))
        if git("status", "--porcelain", cwd=d):
            raise RuntimeError(f"Dirty corpus cache: {d}. Preserve it before fetching.")
        if src["id"] in existing:
            if existing[src["id"]]["repo"] != src["repo"]:
                raise RuntimeError(f"Manifest/lock repository mismatch: {src['id']}")
            commit = existing[src["id"]]["commit"]
        elif "before" in src:
            commit = git("rev-list", "-1", f"--before={src['before']}T00:00:00+09:00", "origin/HEAD", cwd=d)
        else:
            ref = src.get("commit", "HEAD")
            commit = git("rev-parse", "origin/HEAD" if ref == "HEAD" else ref, cwd=d)
        git("checkout", "-q", commit, cwd=d)
        date = git("show", "-s", "--format=%cI", commit, cwd=d)
        lock[src["id"]] = {"repo": src["repo"], "commit": commit, "commit_date": date}
        print(src["id"], commit[:10], date)
    Path(args.lock).parent.mkdir(parents=True, exist_ok=True)
    Path(args.lock).write_text(json.dumps(lock, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
