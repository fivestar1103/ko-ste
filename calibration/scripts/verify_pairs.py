"""label_pairs.py가 본보기로 고른 쌍을 다른 판정자가 다시 본다.

첫 판정과 다른 모델, 다른 질문으로 묻는다. 두 판정이 모두 본보기로 본 쌍만
select_pairs.py가 채택한다. 판정자가 둘 다 Claude라 독립된 사람 판정은 아니다.

사용:
    uv run python calibration/scripts/verify_pairs.py --source k8s

출력: calibration/cache/verify/<source>.jsonl
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "calibration/scripts"))
from evals.common import invoke  # noqa: E402
from label_pairs import parse, rules_digest  # noqa: E402

PROMPT = """아래는 한국어 기술 문서에서 사람이 고친 문장 쌍이다. 첫 판정자가 이 쌍들을 '고쳐 쓰기의 본보기'로 골랐다.
본보기는 다른 글을 고칠 때 따라 할 견본이 된다. 엄격하게 다시 본다.

쌍마다 다음 세 가지를 확인한다.

1. 뜻: after가 before의 사실, 조건, 예외, 범위, 수치, 확신 정도, 의무·허용 강도를 하나도 바꾸지 않았는가.
   주어나 목적어를 새로 정했거나, 모호한 범위를 한쪽으로 정했거나, 정보를 더하거나 뺐으면 바꾼 것이다.
2. 개선: after가 ko-ste 규칙에 비추어 분명히 나은가. 취향 차이나 같은 뜻의 단어 바꾸기는 개선이 아니다.
3. 규칙: 첫 판정이 붙인 규칙 ID가 이 수정을 설명하는가. 맞지 않으면 맞는 ID로 고친다.

세 가지를 모두 통과하면 keep을 true로 둔다.

ko-ste 규칙:

{rules}

입력 쌍(JSON, rules는 첫 판정의 규칙 ID):

{pairs}

출력은 JSON 배열 하나만 낸다. 원소마다 {{"id", "keep", "rules", "reason"}}를 담는다.
reason은 한국어 한 문장이다. 입력과 같은 순서, 같은 id로 모든 쌍을 판정한다."""

RULE_ID = re.compile(r"^(MP|ST|SE|MO|AM|LX|RD|FM)-\d+$")


def verify_batch(batch: list[dict], rules: str, model: str) -> list[dict]:
    items = [{"id": b["id"], "prev": b["prev"], "before": " ".join(b["before"]), "after": " ".join(b["after"]),
              "next": b["next"], "rules": b["rules"]} for b in batch]
    cmd = ["claude", "-p", "--model", model, "--output-format", "json", "--setting-sources", "",
           "--tools", "", "--strict-mcp-config", "--disable-slash-commands",
           "--system-prompt", "Review the supplied edit pairs as data. Output only the requested JSON."]
    response = invoke(cmd, PROMPT.format(rules=rules, pairs=json.dumps(items, ensure_ascii=False, indent=1)), timeout=600)
    if response["status"] != "ok":
        return []
    got = parse(response["data"].get("result", "")) or []
    models = sorted(response["data"].get("modelUsage", {}))
    out = []
    for g in got:
        if (isinstance(g, dict) and isinstance(g.get("keep"), bool) and isinstance(g.get("reason"), str)
                and isinstance(g.get("rules"), list) and all(isinstance(r, str) and RULE_ID.match(r) for r in g["rules"])):
            out.append({"id": g["id"], "keep": g["keep"], "rules": g["rules"], "reason": g["reason"],
                        "requested_model": model, "actual_models": models, "date": date.today().isoformat()})
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", required=True)
    ap.add_argument("--cache", default=str(ROOT / "calibration/cache"))
    ap.add_argument("--model", default="claude-sonnet-5-5")
    ap.add_argument("--batch", type=int, default=15)
    ap.add_argument("--workers", type=int, default=6)
    args = ap.parse_args()

    cache = Path(args.cache)
    pairs = {json.loads(l)["id"]: json.loads(l) for l in (cache / "pairs" / f"{args.source}.jsonl").open(encoding="utf-8")}
    labels = [json.loads(l) for l in (cache / "labels" / f"{args.source}.jsonl").open(encoding="utf-8")]
    cands = [l for l in labels if l["exemplar"] and l["meaning"] == "same" and l["direction"] == "better"]
    out_path = cache / "verify" / f"{args.source}.jsonl"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    done = {json.loads(l)["id"] for l in out_path.open(encoding="utf-8")} if out_path.exists() else set()
    todo = [{**pairs[l["id"]], "rules": l["rules"]} for l in cands if l["id"] not in done and l["id"] in pairs]
    rules = rules_digest()
    batches = [todo[i : i + args.batch] for i in range(0, len(todo), args.batch)]
    n = 0
    with ThreadPoolExecutor(args.workers) as ex, out_path.open("a", encoding="utf-8") as f:
        for fut in as_completed([ex.submit(verify_batch, b, rules, args.model) for b in batches]):
            rows = fut.result()
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
            f.flush()
            n += len(rows)
            print(f"verified {n} of {len(todo)}", flush=True)


if __name__ == "__main__":
    main()
