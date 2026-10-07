"""ko-ste 동작 시험: 같은 요청을 스킬 있음/없음으로 독립 실행하고 채점한다.

각 실행은 새 `claude -p` 세션이다. 설정 파일(CLAUDE.md 등)은 읽지 않는다.
- with_skill: 프롬프트 앞에 스킬 경로를 주고 SKILL.md를 따르라고 한다.
- without_skill: 같은 요청만 준다. 스킬은 꺼 둔다(--disable-slash-commands).

사용:
    uv run --no-project --with kiwipiepy evals/run_evals.py --iteration 1 --model claude-opus-5-5
    uv run --no-project --with kiwipiepy evals/run_evals.py --iteration 1 --grade-only

결과: evals/results/iteration-N/<eval>/<config>/run-K/output.md, grading.json
      evals/results/iteration-N/benchmark.json, benchmark.md
"""

from __future__ import annotations

import argparse
import difflib
import json
import re
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Event

from common import extract_output, invoke, digest, skill_digest

ROOT = Path(__file__).resolve().parent.parent
SKILL = ROOT / "skills" / "ko-ste"


def run_claude(prompt: str, model: str, with_skill: bool, cwd: Path) -> dict:
    """프롬프트는 stdin으로 넘긴다. Windows 셸은 여러 줄 인자를 자른다."""
    if with_skill:
        prompt = (
            f"Skill path: {SKILL.as_posix()}\n"
            f"먼저 {SKILL.as_posix()}/SKILL.md를 읽고, 그 스킬의 지침에 따라 아래 요청을 처리해.\n\n{prompt}"
        )
    cmd = [
        "claude", "-p", "--model", model, "--output-format", "json",
        "--setting-sources", "", "--permission-mode", "default",
        "--tools", "Read,Glob,Grep" if with_skill else "",
        "--allowed-tools", "Read,Glob,Grep",
        "--add-dir", str(SKILL),
        "--strict-mcp-config",  # 연결된 MCP 커넥터 안내가 출력에 섞이지 않게 MCP를 끈다
    ]
    cmd.append("--disable-slash-commands")
    t0 = time.time()
    result = invoke(cmd, prompt, cwd=cwd)
    if result["status"] != "ok":
        return {"text": "", **result, "seconds": round(time.time() - t0, 1), "tokens": 0}
    d = result["data"]
    u = d.get("usage", {})
    return {"text": d["result"], "status": "ok", "seconds": round(time.time() - t0, 1),
            "tokens": sum(u.get(k, 0) for k in ("input_tokens", "output_tokens", "cache_read_input_tokens", "cache_creation_input_tokens")),
            "turns": d.get("num_turns"), "actual_models": sorted(d.get("modelUsage", {}))}


def count_sentences(text: str) -> int:
    body = re.sub(r"```.*?```", "", text, flags=re.S)
    items = len(re.findall(r"^\s*([-*]|\d+[.)])\s+\S", body, flags=re.M))
    sents = len(re.findall(r"[다요음임함][.!?]?(\s|$)", body))
    return max(items, sents)


STOP = re.compile(r"^\s*(\*\*)?\s*(그대로 둠|확인 필요|확인할 점|바꾼|고친 (부분|점|내용)|수정한|변경한|변경 사항|참고|추가 권장|표로 정리|다른 표현|원문|고칠 곳이 없)")
INTRO = re.compile(r"^\s*(#+\s*)?(\*\*)?\s*(다듬은|고친|수정한|수정안|권장안|추천안)[^\n]{0,20}(\*\*)?\s*:?\s*(\*\*)?\s*$")


def main_text(text: str) -> str:
    """다듬은 본문만 뽑는다. 설명, '그대로 둠', '확인 필요', 바꾼 점 목록은 뺀다.

    - 인용 블록(>)이 있으면 첫 인용 블록을 본문으로 본다(스킬 없는 출력에 흔한 형식).
    - 없으면 처음부터 설명 머리말이나 가로줄(---) 전까지를 본문으로 본다.
    - '다듬은 문장:'처럼 본문을 소개하는 줄은 뺀다.
    """
    return extract_output(text)["body"]


def grade(ev: dict, full: str) -> list[dict]:
    res = []
    body = main_text(full)
    for a in ev["assertions"]:
        t = a["type"]
        # 기본은 본문만 본다. '확인 필요' 같은 알림을 찾는 검사만 출력 전체를 본다.
        text = full if a.get("scope") == "all" else body
        ok, ev_txt = None, ""
        if not body.strip():
            res.append({"text": a["text"], "id": a["id"], "passed": None, "evidence": "실행 결과 없음", "status": "error"})
            continue
        if t == "regex_any":
            m = re.search(a["pattern"], text)
            ok, ev_txt = bool(m), (m.group(0) if m else "일치 없음")
        elif t == "regex_none":
            m = re.search(a["pattern"], text)
            ok, ev_txt = not m, (f"발견: {m.group(0)}" if m else "없음")
        elif t == "regex_all":
            miss = [p for p in a["patterns"] if not re.search(p, text)]
            ok, ev_txt = not miss, (f"누락: {miss}" if miss else "모두 있음")
        elif t == "min_sentences":
            n = count_sentences(text)
            ok, ev_txt = n >= a["min"], f"{n}개"
        elif t == "max_count":
            n = len(re.findall(a["pattern"], text))
            ok, ev_txt = n <= a["max"], f"{n}개"
        elif t == "similarity":
            r = difflib.SequenceMatcher(None, a["original"], text).ratio()
            ok, ev_txt = r >= a["min"], f"{r:.2f}"
        elif t == "order":
            a1 = re.search(a["first"], text)
            a2 = re.search(a["second"], text)
            ok = bool(a1 and a2 and a1.start() < a2.start())
            ev_txt = f"{a1.start() if a1 else None} < {a2.start() if a2 else None}"
        elif t == "judge":
            ok, ev_txt = None, "사람/모델 판정 필요"
        res.append({"text": a["text"], "id": a["id"], "passed": ok, "evidence": ev_txt})
    return res


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--iteration", type=int, required=True)
    ap.add_argument("--model", default="claude-opus-5-5")
    ap.add_argument("--tag", default="", help="결과 하위 폴더 이름(모델별 실행을 나눌 때)")
    ap.add_argument("--runs", type=int, default=1)
    ap.add_argument("--only", nargs="*", type=int)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--grade-only", action="store_true")
    args = ap.parse_args()

    evals = json.loads((ROOT / "evals" / "evals.json").read_text(encoding="utf-8"))["evals"]
    if args.only:
        evals = [e for e in evals if e["id"] in args.only]
    base = ROOT / "evals" / "results" / f"iteration-{args.iteration}" / args.tag
    if not args.grade_only:
        base.mkdir(parents=True, exist_ok=True)
        manifest = {"model": args.model, "skill_sha256": skill_digest(SKILL),
                    "evals_sha256": digest(ROOT / "evals" / "evals.json"), "protocol": 2}
        meta = base / "manifest.json"
        if meta.exists() and json.loads(meta.read_text(encoding="utf-8")) != manifest:
            raise SystemExit("모델·스킬·시험이 바뀌었습니다. 새 iteration/tag를 쓰세요.")
        if not meta.exists() and any(base.glob("eval-*/*/run-*/output.md")):
            raise SystemExit("기존 실행은 버전 기록이 없습니다. 새 iteration/tag를 쓰세요.")
        meta.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    jobs = []
    for ev in evals:
        for cfg in ("with_skill", "without_skill"):
            for k in range(1, args.runs + 1):
                d = base / f"eval-{ev['id']:02d}-{ev['name']}" / cfg / f"run-{k}"
                jobs.append((ev, cfg, d))

    unavailable = Event()

    def do(job):
        ev, cfg, d = job
        d.mkdir(parents=True, exist_ok=True)
        out = d / "output.md"
        timing = d / "timing.json"
        prior_error = timing.exists() and bool(json.loads(timing.read_text(encoding="utf-8")).get("error"))
        if not args.grade_only and (not out.exists() or not out.read_text(encoding="utf-8").strip() or prior_error):
            # with_skill은 스킬 폴더에서 실행해 읽기 권한을 준다. without_skill은 빈 폴더에서 실행한다.
            r = ({"text": "", "error": "generation paused after CLI error", "status": "error", "seconds": 0, "tokens": 0}
                 if unavailable.is_set() else run_claude(ev["prompt"], args.model, cfg == "with_skill", cwd=SKILL if cfg == "with_skill" else d))
            if r.get("error"):
                unavailable.set()
            out.write_text(r["text"], encoding="utf-8")
            (d / "timing.json").write_text(json.dumps({k: v for k, v in r.items() if k != "text"} | {"model": args.model}, ensure_ascii=False), encoding="utf-8")
            print(ev["id"], cfg, "done", r.get("seconds"), r.get("error", "")[:80], flush=True)
        text = out.read_text(encoding="utf-8") if out.exists() else ""
        g = grade(ev, "" if prior_error and args.grade_only else text)
        (d / "body.md").write_text(main_text(text), encoding="utf-8")
        (d / "grading.json").write_text(json.dumps({"expectations": g}, ensure_ascii=False, indent=2), encoding="utf-8")
        return ev, cfg, g

    with ThreadPoolExecutor(args.workers) as ex:
        results = list(ex.map(do, jobs))

    summary = {}
    for ev, cfg, g in results:
        s = summary.setdefault(ev["name"], {}).setdefault(cfg, {"pass": 0, "total": 0, "judge": 0, "error": 0})
        for x in g:
            if x.get("status") == "error":
                s["error"] += 1
            elif x["passed"] is None:
                s["judge"] += 1
            else:
                s["total"] += 1
                s["pass"] += int(x["passed"])
    (base / "benchmark.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = ["| eval | with_skill | without_skill |", "|---|---|---|"]
    tot = {"with_skill": [0, 0], "without_skill": [0, 0]}
    for name, s in summary.items():
        row = [name]
        for cfg in ("with_skill", "without_skill"):
            c = s.get(cfg, {"pass": 0, "total": 0})
            row.append(f"{c['pass']}/{c['total']}")
            tot[cfg][0] += c["pass"]
            tot[cfg][1] += c["total"]
        lines.append("| " + " | ".join(row) + " |")
    lines.append(f"| 합계 | {tot['with_skill'][0]}/{tot['with_skill'][1]} | {tot['without_skill'][0]}/{tot['without_skill'][1]} |")
    lines += ["", "자동 검사는 표면 신호만 잽니다. 의미 보존이나 독자 이해도를 증명하지 않습니다.",
              f"오류 검사: {sum(c['error'] for v in summary.values() for c in v.values())}. 오류는 통과나 평가 분모에 넣지 않습니다.",
              "실행 당시 스킬 버전: " + ("manifest.json 참고" if (base / "manifest.json").exists() else "미기록(기존 실행). 현재 스킬의 성과로 해석하지 않습니다.")]
    (base / "benchmark.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    if any(c["error"] for v in summary.values() for c in v.values()):
        raise SystemExit(2)


if __name__ == "__main__":
    main()
