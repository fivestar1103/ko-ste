"""문체 지시 없이 현재 모델이 쓴 한국어 글을 모은다.

Claude Code CLI(`claude -p`)를 최소 시스템 프롬프트로 부른다.
설정 파일(CLAUDE.md 등)과 도구를 끄므로 사용자 문체 지시가 섞이지 않는다.
CLI 자체가 붙이는 요소가 있을 수 있으므로 결과는 "이 실행 환경의 출력"으로만 해석한다.

사용:
    uv run calibration/scripts/gen_model_samples.py \
        --prompts calibration/prompts/model-prompts.tsv \
        --models claude-opus-5-5 claude-sonnet-5-5 claude-haiku-4-5-20251001 \
        --out calibration/data/model-samples.jsonl
"""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Event

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "evals"))
from common import invoke

SYSTEM_PROMPT = "You are a helpful assistant."


def run_one(model: str, row: dict) -> dict:
    cmd = [
        "claude", "-p",
        "--system-prompt", SYSTEM_PROMPT,
        "--setting-sources", "",
        "--tools", "",
        "--model", model,
        "--output-format", "json",
        "--strict-mcp-config", "--disable-slash-commands",
    ]
    t0 = time.time()
    response = invoke(cmd, row["prompt"])
    metadata = {"id": row["id"], "genre": row["genre"], "model": model,
                "prompt": row["prompt"], "system_prompt": SYSTEM_PROMPT,
                "seconds": round(time.time() - t0, 1), "date": time.strftime("%Y-%m-%d")}
    if response["status"] != "ok":
        return metadata | response
    data = response["data"]
    return metadata | {"text": data["result"], "status": "ok", "actual_models": sorted(data.get("modelUsage", {}))}


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--prompts", required=True)
    ap.add_argument("--models", nargs="+", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--workers", type=int, default=4)
    args = ap.parse_args()

    with open(args.prompts, encoding="utf-8") as f:
        rows = list(csv.DictReader(f, delimiter="\t"))
    out = Path(args.out)
    done = set()
    if out.exists():
        for line in out.read_text(encoding="utf-8").splitlines():
            r = json.loads(line)
            if "text" in r:
                done.add((r["model"], r["id"]))
    jobs = [(m, r) for m in args.models for r in rows if (m, r["id"]) not in done]
    print(f"{len(jobs)} jobs", flush=True)
    unavailable = Event()
    def execute(job):
        if unavailable.is_set():
            return {"model": job[0], "id": job[1]["id"], "status": "error", "error": "paused after CLI error"}
        response = run_one(*job)
        if response.get("error"):
            unavailable.set()
        return response
    with ThreadPoolExecutor(args.workers) as ex, out.open("a", encoding="utf-8") as f:
        for res in ex.map(execute, jobs):
            f.write(json.dumps(res, ensure_ascii=False) + "\n")
            f.flush()
            print(res["model"], res["id"], "ok" if "text" in res else "ERR", flush=True)
    if unavailable.is_set():
        raise SystemExit(2)


if __name__ == "__main__":
    main()
