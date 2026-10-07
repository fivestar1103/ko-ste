"""원자료에서 03-calibration.md의 수치표를 다시 만든다.

문서 안의 <!-- BEGIN:이름 --> … <!-- END:이름 --> 구간을 덮어쓴다.
    uv run --no-project calibration/scripts/report.py --write
    uv run --no-project calibration/scripts/report.py --check   # 문서와 원자료가 다르면 종료 코드 1
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "skills" / "ko-ste" / "references" / "03-calibration.md"
DATA = ROOT / "calibration" / "data"

GROUPS = [
    ("toss", "토스 가이드"),
    ("pre2022", "2022 이전 문서"),
    ("post2023", "2023 이후 문서"),
    ("model:claude-opus-5-5", "Opus 5.5"),
    ("model:claude-sonnet-5-5", "Sonnet 5.5"),
    ("model:claude-haiku-4-5-20251001", "Haiku 4.5"),
]


def table(header: list[str], rows: list[list]) -> str:
    out = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    out += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return "\n".join(out)


def sec_corpus(m: dict) -> str:
    rows = []
    for g, name in GROUPS:
        s = m["groups"][g]
        rows.append([name, s["sentences"], s["eojeol_total"], s["fragments_excluded"], s["lines"].get("total", 0)])
    return table(["묶음", "분석한 문장", "어절", "제외한 조각", "줄"], rows)


def sec_length(m: dict) -> str:
    rows = []
    for g, name in GROUPS:
        e = m["groups"][g]["eojeol"]
        rows.append([name, e["median"], e["p75"], e["p90"], e["p95"], f"{e['over_14']}%", f"{e['over_17']}%", f"{e['over_25']}%"])
    return table(["묶음", "중앙값", "75%", "90%", "95%", ">14", ">17", ">25"], rows)


def sec_mood(m: dict) -> str:
    rows = []
    for g, name in GROUPS:
        s = m["groups"][g]
        i, d = s["imperative"], s["declarative"]
        rows.append([name, i["n"], i["median"], i["p90"], f"{i['over_14']}%", d["n"], d["median"], d["p90"], f"{d['over_17']}%", f"{d['over_25']}%"])
    return table(["묶음", "지시문 수", "지시 중앙값", "지시 90%", "지시 >14", "설명문 수", "설명 중앙값", "설명 90%", "설명 >17", "설명 >25"], rows)


def sec_struct(m: dict) -> str:
    rows = []
    for g, name in GROUPS:
        s = m["groups"][g]
        c = s["clauses"]
        rows.append([name, f"{s['ui_ge2_pct']}%", f"{s['ui_ge3_pct']}%", f"{s['noun_run_ge4_pct']}%", f"{s['noun_run_ge5_pct']}%", c["median"], f"{c['ge3_pct']}%", f"{c['ge4_pct']}%", f"{c['aux_share_of_ec_pct']}%"])
    return table(["묶음", "'의'≥2", "'의'≥3", "명사≥4", "명사≥5", "절 중앙값", "절≥3", "절≥4", "보조 구성 비율"], rows)


EXPR = [
    ("B.e_daehan", "~에 대한/대해"), ("B.tonghae", "~를 통해"), ("B.inhae", "~로 인해"), ("B.kyungwoo", "~할 경우"),
    ("B.wihae", "~를 위해"), ("B.e_uihae", "~에 의해"), ("B.nominal_verb", "진행/수행/실시하다"), ("B.provide", "제공하다"),
    ("B.hanja", "어려운 한자어 후보"), ("B.mit", "및"), ("A.double_passive", "이중 피동"),
    ("S.eval", "평가어"), ("S.intensifier", "강조 부사"), ("S.meta", "메타 담화"), ("S.demonstrative", "지시어"),
    ("S.contrast", "상투적 대비"), ("S.closing", "맺음 제안"), ("S.important", "~것이 중요/좋다"),
    ("S.comma_after_ec", "연결어미 뒤 쉼표"), ("S.dash", "줄표"), ("S.exclaim", "느낌표 종결"),
]


def sec_expr(m: dict) -> str:
    rows = []
    for key, name in EXPR:
        rows.append([name, f"`{key}`"] + [m["groups"][g]["per_100_sent"].get(key, 0) for g, _ in GROUPS])
    return table(["표현(문장 100개당)", "패턴"] + [n for _, n in GROUPS], rows)


def sec_lines(m: dict) -> str:
    keys = [("bold_lines", "굵게 쓴 줄"), ("table", "표 줄"), ("list", "목록 줄"), ("heading", "제목 줄"), ("emoji", "이모지")]
    rows = [[n] + [m["groups"][g]["per_100_lines"][k] for g, _ in GROUPS] for k, n in keys]
    ls = m["line_signals_per_100_lines"]
    for k, n in [("arrow", "화살표"), ("bold_label", "굵은 소제목+쌍점"), ("closing_offer", "맺음 제안"), ("summary_word", "요약 표지"), ("emoji_marker", "✅·💡 표지"), ("hr", "가로줄")]:
        rows.append([n] + [ls.get(g, {}).get(k, 0) for g, _ in GROUPS])
    return table(["신호(줄 100개당)"] + [n for _, n in GROUPS], rows)


def sec_dict(d: dict) -> str:
    rows = []
    for r in d["pairs"]:
        lit = ", ".join(f"{k}" for k in r["literal"]) or "-"
        nat = ", ".join(f"{k}" for k in list(r["natural"])[:2]) + (" …" if len(r["natural"]) > 2 else "")
        L, N = r["literal_sum"], r["natural_sum"]
        rows.append([r["english"], lit.split(",")[0] if r["literal"] else "-", nat,
                     f"{L['opendict']}/{L['krdict']}/{L['stdict']}", f"{N['opendict']}/{N['krdict']}/{N['stdict']}", r.get("verdict", "")])
    return f"조회일: {d['date']}\n\n" + table(["영어", "직역 조합(대표)", "자연스러운 짝(대표)", "직역 용례 우리말샘/기초/표준", "짝 용례 우리말샘/기초/표준", "판정"], rows)


def _iters() -> list[Path]:
    return sorted((ROOT / "evals" / "results").glob("iteration-*"), key=lambda p: int(p.name.split("-")[1]))


def _collect(fname: str) -> str:
    parts = []
    for it in _iters():
        for f in [it / fname] + sorted(it.glob(f"*/{fname}")):
            if f.exists():
                label = f.parent.relative_to(ROOT / "evals" / "results").as_posix()
                parts.append(f"{label}\n\n" + f.read_text(encoding="utf-8").strip())
    return "\n\n".join(parts) or "(아직 없음)"


def sec_evals() -> str:
    return _collect("benchmark.md")


def sec_judge() -> str:
    return _collect("judge.md")


def build() -> dict[str, str]:
    m = json.loads((DATA / "measure.json").read_text(encoding="utf-8"))
    d = json.loads((DATA / "dict-collocations.json").read_text(encoding="utf-8"))
    return {
        "corpus": sec_corpus(m), "length": sec_length(m), "mood": sec_mood(m), "struct": sec_struct(m),
        "expr": sec_expr(m), "lines": sec_lines(m), "dict": sec_dict(d), "evals": sec_evals(), "judge": sec_judge(),
    }


def apply(doc: str, secs: dict[str, str]) -> str:
    for k, v in secs.items():
        pattern = rf"(<!-- BEGIN:{k} -->\n).*?(<!-- END:{k} -->)"
        if len(re.findall(pattern, doc, flags=re.S)) != 1:
            raise ValueError(f"Missing or duplicate report marker: {k}")
        doc = re.sub(pattern, lambda mm: mm.group(1) + v + "\n" + mm.group(2), doc, flags=re.S)
    return doc


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    doc = DOC.read_text(encoding="utf-8")
    new = apply(doc, build())
    if args.check:
        if new != doc:
            print("03-calibration.md의 표가 원자료와 다르다. --write로 다시 만든다.")
            sys.exit(1)
        print("일치")
    elif args.write:
        DOC.write_text(new, encoding="utf-8")
        print("갱신함")
    else:
        print(new)


if __name__ == "__main__":
    main()
