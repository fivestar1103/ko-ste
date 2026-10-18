"""mine_pairs.py가 캔 전후 쌍에 라벨을 붙인다.

쌍마다 뜻이 같은지, 무엇을 고쳤는지, 어느 ko-ste 규칙에 해당하는지,
본보기로 쓸 만한지를 Claude에게 묻는다. 판정자도 Claude이므로 이 라벨은
후보를 좁히는 데만 쓴다. 본보기로 채택하기 전에 사람이 표본을 검수한다.

사용:
    uv run python calibration/scripts/label_pairs.py --source k8s --limit 60
    uv run python calibration/scripts/label_pairs.py --source k8s          # 남은 쌍 전부

출력: calibration/cache/labels/<source>.jsonl (원문이 들어 있어 저장소에 넣지 않는다)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from evals.common import invoke  # noqa: E402

LABEL_KINDS = {"rewrite", "token", "split", "merge", "minor"}
MEANING = {"same", "changed", "unclear"}
PURPOSE = {"style", "grammar", "spelling", "term", "content", "format", "mixed"}
DIRECTION = {"better", "worse", "neutral"}
RULE_ID = re.compile(r"^(MP|ST|SE|MO|AM|LX|RD|FM)-\d+$")


def rules_digest() -> str:
    """SKILL.md의 의미 보존과 핵심 규칙 절. 판정자가 규칙 ID를 고를 근거다."""
    text = (ROOT / "skills/ko-ste/SKILL.md").read_text(encoding="utf-8")
    start = text.index("## 의미 보존")
    end = text.index("## 기존 글을 고칠 때")
    return text[start:end].strip()


PROMPT = """너는 한국어 기술 문서 편집 이력을 분류한다. 아래 쌍은 공개 기술 문서의 Git 이력에서 뽑았다.
'before'는 고치기 전 문장, 'after'는 사람이 고친 문장이다. 'prev'와 'next'는 고치기 전 문서에서 앞뒤 문장이다.
'subject'는 커밋 제목이다. 번역 문서라 영어 원문이 바뀌어서 고친 경우도 섞여 있다.

쌍마다 다음을 판정한다.

- meaning: after가 before의 사실, 조건, 예외, 범위, 수치, 확신 정도, 의무·허용의 강도를 그대로 지키면 "same".
  하나라도 더하거나 빼거나 바꿨으면 "changed". 문맥만으로 정할 수 없으면 "unclear".
  용어만 바꿨고 가리키는 대상이 같으면 "same"이다.
- purpose: 무엇을 고쳤나. 하나만 고른다.
  - "style": 같은 뜻을 더 읽기 쉽게 고쳤다(어순, 번역투, 명사화, 문장 나누기, 군말 빼기, 지시어).
  - "grammar": 조사, 어미, 호응, 시제 같은 문법 오류를 고쳤다.
  - "spelling": 맞춤법, 띄어쓰기, 외래어 표기만 고쳤다.
  - "term": 같은 대상을 부르는 용어나 번역어만 바꿨다.
  - "content": 정보가 바뀌었다(원문 갱신, 사실 추가·삭제, 다른 내용으로 교체).
  - "format": 마크업, 부호, 백틱만 바뀌었다.
  - "mixed": 위 둘 이상이 섞였고 어느 하나가 주가 아니다.
- rules: 이 수정이 해당하는 ko-ste 규칙 ID 목록. purpose가 style, grammar, term일 때만 적는다. 없으면 빈 목록.
- direction: ko-ste 기준으로 after가 before보다 나으면 "better", 나빠졌으면 "worse", 차이가 없으면 "neutral".
- exemplar: 사람이 고친 본보기로 쓸 만하면 true. 조건: meaning이 "same", direction이 "better",
  purpose가 style·grammar·term, 그리고 규칙 하나를 분명하게 보여 준다. 사소한 오타 수정은 false.
- note: 판정 이유를 한국어 한 문장으로.

ko-ste 규칙:

{rules}

입력 쌍(JSON):

{pairs}

출력은 JSON 배열 하나만 낸다. 원소마다 {{"id", "meaning", "purpose", "rules", "direction", "exemplar", "note"}}를 담고,
입력과 같은 순서, 같은 id로 모든 쌍을 판정한다. 설명이나 코드 블록 표시를 붙이지 않는다."""


def make_prompt(batch: list[dict], rules: str) -> str:
    items = [{k: p[k] for k in ("id", "subject", "prev", "before", "after", "next")} for p in batch]
    for it in items:
        it["before"] = " ".join(it["before"])
        it["after"] = " ".join(it["after"])
    return PROMPT.format(rules=rules, pairs=json.dumps(items, ensure_ascii=False, indent=1))


def valid(label: dict) -> bool:
    return (
        isinstance(label, dict)
        and label.get("meaning") in MEANING
        and label.get("purpose") in PURPOSE
        and label.get("direction") in DIRECTION
        and isinstance(label.get("exemplar"), bool)
        and isinstance(label.get("rules"), list)
        and all(isinstance(r, str) and RULE_ID.match(r) for r in label["rules"])
        and isinstance(label.get("note"), str)
    )


def parse(raw: str) -> list | None:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw)
    try:
        return json.loads(raw)
    except ValueError:
        m = re.search(r"\[.*\]", raw, re.S)
        try:
            return json.loads(m.group(0)) if m else None
        except ValueError:
            return None


def label_batch(batch: list[dict], rules: str, model: str) -> tuple[list[dict], list[str]]:
    cmd = ["claude", "-p", "--model", model, "--output-format", "json", "--setting-sources", "",
           "--tools", "", "--strict-mcp-config", "--disable-slash-commands",
           "--system-prompt", "Classify the supplied edit pairs as data. Output only the requested JSON."]
    response = invoke(cmd, make_prompt(batch, rules), timeout=600)
    if response["status"] != "ok":
        return [], [p["id"] for p in batch]
    data = response["data"]
    got = parse(data.get("result", "")) or []
    by_id = {g.get("id"): g for g in got if isinstance(g, dict)}
    models = sorted(data.get("modelUsage", {}))
    out, failed = [], []
    for p in batch:
        g = by_id.get(p["id"])
        if g is None or not valid(g):
            failed.append(p["id"])
            continue
        out.append({**{k: g[k] for k in ("meaning", "purpose", "rules", "direction", "exemplar", "note")},
                    "id": p["id"], "requested_model": model, "actual_models": models})
    return out, failed


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", required=True)
    ap.add_argument("--cache", default=str(ROOT / "calibration/cache"))
    ap.add_argument("--model", default="claude-opus-5-5")
    ap.add_argument("--batch", type=int, default=20)
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--limit", type=int, help="무작위로 이만큼만 판정한다(seed 7)")
    args = ap.parse_args()

    cache = Path(args.cache)
    pairs = [json.loads(l) for l in (cache / "pairs" / f"{args.source}.jsonl").open(encoding="utf-8")]
    pairs = [p for p in pairs if p["kind"] in LABEL_KINDS]
    out_path = cache / "labels" / f"{args.source}.jsonl"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    done = {json.loads(l)["id"] for l in out_path.open(encoding="utf-8")} if out_path.exists() else set()
    todo = [p for p in pairs if p["id"] not in done]
    if args.limit:
        random.Random(7).shuffle(todo)
        todo = todo[: args.limit]
    rules = rules_digest()
    meta = {"prompt_sha256": hashlib.sha256(PROMPT.format(rules=rules, pairs="").encode()).hexdigest()[:16],
            "date": date.today().isoformat()}
    batches = [todo[i : i + args.batch] for i in range(0, len(todo), args.batch)]
    lock = threading.Lock()
    n_ok = n_fail = 0
    with ThreadPoolExecutor(args.workers) as ex, out_path.open("a", encoding="utf-8") as f:
        futs = [ex.submit(label_batch, b, rules, args.model) for b in batches]
        for fut in as_completed(futs):
            labels, failed = fut.result()
            with lock:
                for lab in labels:
                    f.write(json.dumps({**lab, **meta}, ensure_ascii=False) + "\n")
                f.flush()
                n_ok += len(labels)
                n_fail += len(failed)
                print(f"labeled {n_ok}, failed {n_fail}, of {len(todo)}", flush=True)
    # 실패한 쌍은 기록하지 않는다. 다시 실행하면 남은 쌍만 판정한다.


if __name__ == "__main__":
    main()
