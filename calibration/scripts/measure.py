"""보정 묶음마다 문장 지표와 표현 빈도를 잰다.

사용:
    uv run --no-project --with kiwipiepy calibration/scripts/measure.py \
        --manifest calibration/corpus-manifest.json --cache calibration/cache \
        --models calibration/data/model-samples.jsonl --out calibration/data

출력:
    calibration/data/measure.json   묶음별 집계 (저장소에 넣는다)
    calibration/cache/review/*.tsv  규칙에 걸린 문장 표본 (원문이라 저장소에 넣지 않는다)
"""

from __future__ import annotations

import argparse
import json
import random
import re
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "skills/ko-ste/scripts"))
import kostelib as K  # noqa: E402

THRESH = [14, 17, 25]

# 줄 단위 서식 신호 (분모: 코드 블록 밖의 비어 있지 않은 줄)
LINE_SIGNALS = {
    "arrow": r"→|⇒|->",
    "bold_label": r"^\s*([-*]\s+)?\*\*[^*]{1,20}\*\*\s*[:：]",
    "summary_word": r"요약|정리하면|한 줄|TL;DR|핵심(은|:)",
    "emoji_marker": r"✅|❌|⚠️|💡|👉|📌",
    "closing_offer": r"(필요하시면|원하시면|궁금한 점|도움이 필요|말씀해 주세요|알려 주시면|알려주시면)",
    "numbered_heading": r"^#+\s*\d+[.)]",
    "hr": r"^\s*---\s*$",
}


def line_signals(md: str, c: Counter) -> None:
    infence = False
    for ln in md.splitlines():
        if re.match(r"^\s*(```|~~~)", ln):
            infence = not infence
            continue
        if infence or not ln.strip():
            continue
        c["_lines"] += 1
        for k, rx in LINE_SIGNALS.items():
            if re.search(rx, ln):
                c[k] += 1


def pct(values: list[int], p: float) -> float:
    if not values:
        return float("nan")
    s = sorted(values)
    k = (len(s) - 1) * p
    f = int(k)
    c = min(f + 1, len(s) - 1)
    return round(s[f] + (s[c] - s[f]) * (k - f), 1)


def docs_for_source(src: dict, cache: Path) -> list[tuple[str, str]]:
    root = cache / src["id"]
    files: list[Path] = []
    for pat in src["paths"]:
        files.extend(sorted(root.glob(pat)))
    out = []
    for f in dict.fromkeys(files):
        rel = f.relative_to(root).as_posix()
        if any(Path(rel).match(g) for g in src.get("exclude_globs", [])):
            continue
        if "README_EN" in rel or rel.endswith(".en.md"):
            continue
        out.append((rel, f.read_text(encoding="utf-8", errors="replace")))
    return out


def analyze_doc(md: str, exclude_blocks=None):
    st = K.parse_markdown(md, exclude_blocks)
    rows = []
    fragments = 0
    for u in st.units:
        for s in K.split_sentences(u.text):
            r = K.analyze_sentence(s)
            if r is None:
                if len(K.eojeols(s)) >= 3 and K.HANGUL.search(s):
                    fragments += 1
                continue
            r["kind"] = u.kind
            rows.append(r)
    return st, rows, fragments


def summarize(rows: list[dict], lines: Counter, fragments: int) -> dict:
    ej = [r["eojeol"] for r in rows]
    n = len(rows)
    words = sum(ej)
    hits = Counter()
    hit_sents = Counter()
    for r in rows:
        for k, v in r["hits"].items():
            hits[k] += v
            hit_sents[k] += 1
    out = {
        "sentences": n,
        "eojeol_total": words,
        "fragments_excluded": fragments,
        "lines": dict(lines),
        "eojeol": {
            "median": pct(ej, 0.5), "p75": pct(ej, 0.75), "p90": pct(ej, 0.9), "p95": pct(ej, 0.95),
            "mean": round(statistics.mean(ej), 1) if ej else None,
            **{f"over_{t}": round(sum(1 for x in ej if x > t) / n * 100, 1) if n else None for t in THRESH},
        },
        "imperative": (lambda imp: {
            "n": len(imp),
            "median": pct(imp, 0.5), "p75": pct(imp, 0.75), "p90": pct(imp, 0.9),
            "over_14": round(sum(1 for x in imp if x > 14) / len(imp) * 100, 1) if imp else None,
            "over_17": round(sum(1 for x in imp if x > 17) / len(imp) * 100, 1) if imp else None,
            "clauses_ge2_pct": round(sum(1 for r in rows if r["mood"] == "imp" and r["clauses"] >= 2) / len(imp) * 100, 1) if imp else None,
        })([r["eojeol"] for r in rows if r["mood"] == "imp"]),
        "declarative": (lambda d: {
            "n": len(d), "median": pct(d, 0.5), "p90": pct(d, 0.9),
            "over_17": round(sum(1 for x in d if x > 17) / len(d) * 100, 1) if d else None,
            "over_25": round(sum(1 for x in d if x > 25) / len(d) * 100, 1) if d else None,
        })([r["eojeol"] for r in rows if r["mood"] == "decl"]),
        "ui_ge2_pct": round(sum(1 for r in rows if r["ui"] >= 2) / n * 100, 2) if n else None,
        "ui_ge3_pct": round(sum(1 for r in rows if r["ui"] >= 3) / n * 100, 2) if n else None,
        "noun_run_ge4_pct": round(sum(1 for r in rows if r["noun_run"] >= 4) / n * 100, 2) if n else None,
        "noun_run_ge5_pct": round(sum(1 for r in rows if r["noun_run"] >= 5) / n * 100, 2) if n else None,
        "clauses": {
            "median": pct([r["clauses"] for r in rows], 0.5),
            "p90": pct([r["clauses"] for r in rows], 0.9),
            "ge3_pct": round(sum(1 for r in rows if r["clauses"] >= 3) / n * 100, 1) if n else None,
            "ge4_pct": round(sum(1 for r in rows if r["clauses"] >= 4) / n * 100, 1) if n else None,
            "aux_share_of_ec_pct": round(sum(r["ec_aux"] for r in rows) / max(1, sum(r["ec"] for r in rows)) * 100, 1),
        },
        "per_100_sent": {k: round(hit_sents[k] / n * 100, 2) for k in sorted(hit_sents)} if n else {},
        "per_1000_eojeol": {k: round(hits[k] / words * 1000, 2) for k in sorted(hits)} if words else {},
        "per_100_lines": {
            "bold_lines": round(lines["bold"] / max(1, lines["total"]) * 100, 2),
            "bold_spans": round(lines["bold_spans"] / max(1, lines["total"]) * 100, 2),
            "heading": round(lines["heading"] / max(1, lines["total"]) * 100, 2),
            "list": round(lines["list"] / max(1, lines["total"]) * 100, 2),
            "table": round(lines["table"] / max(1, lines["total"]) * 100, 2),
            "emoji": round(lines["emoji"] / max(1, lines["total"]) * 100, 2),
        },
    }
    return out


def add_lines(c: Counter, st: K.DocStats) -> None:
    c["total"] += st.lines_total
    c["bold"] += st.lines_bold
    c["bold_spans"] += st.bold_spans
    c["heading"] += st.lines_heading
    c["list"] += st.lines_list
    c["table"] += st.lines_table
    c["emoji"] += st.emoji


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", default="calibration/corpus-manifest.json")
    ap.add_argument("--cache", default="calibration/cache")
    ap.add_argument("--models", default="calibration/data/model-samples.jsonl")
    ap.add_argument("--out", default="calibration/data")
    ap.add_argument("--seed", type=int, default=7)
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    cache = Path(args.cache)
    rng = random.Random(args.seed)

    sig: dict[str, Counter] = defaultdict(Counter)
    groups: dict[str, list[dict]] = defaultdict(list)
    glines: dict[str, Counter] = defaultdict(Counter)
    gfrag: Counter = Counter()
    per_source = {}

    for src in manifest["sources"]:
        rows_all, lines, frag = [], Counter(), 0
        for rel, md in docs_for_source(src, cache):
            st, rows, fr = analyze_doc(md, src.get("exclude_blocks"))
            line_signals(md, sig[src["bundle"]])
            for r in rows:
                r["src"] = f"{src['id']}:{rel}"
            rows_all.extend(rows)
            add_lines(lines, st)
            frag += fr
        cap = src.get("cap_sentences")
        if cap and len(rows_all) > cap:
            rows_all = rng.sample(rows_all, cap)
        per_source[src["id"]] = summarize(rows_all, lines, frag)
        groups[src["bundle"]].extend(rows_all)
        glines[src["bundle"]].update(lines)
        gfrag[src["bundle"]] += frag

    model_rows = [json.loads(x) for x in Path(args.models).read_text(encoding="utf-8").splitlines() if x.strip()]
    for m in model_rows:
        if "text" not in m:
            continue
        st, rows, fr = analyze_doc(m["text"])
        g = "model:" + m["model"]
        line_signals(m["text"], sig[g])
        line_signals(m["text"], sig["model:all"])
        for r in rows:
            r["src"] = f"{m['model']}:{m['id']}"
        groups[g].extend(rows)
        groups["model:all"].extend(rows)
        glines[g].update({"total": 0})
        add_lines(glines[g], st)
        add_lines(glines["model:all"], st)
        gfrag[g] += fr
        gfrag["model:all"] += fr

    result = {
        "seed": args.seed,
        "groups": {g: summarize(rows, glines[g], gfrag[g]) for g, rows in sorted(groups.items())},
        "per_source": per_source,
        "line_signals_per_100_lines": {
            g: {"lines": c["_lines"], **{k: round(c[k] / max(1, c["_lines"]) * 100, 2) for k in LINE_SIGNALS}} for g, c in sorted(sig.items())
        },
    }
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "measure.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    # 규칙에 걸린 사람 글 문장 표본: 오탐 검토용 (원문이므로 cache에만)
    review = cache / "review"
    review.mkdir(parents=True, exist_ok=True)
    human = groups["toss"] + groups["pre2022"]
    checks = {
        "len_gt17": lambda r: r["eojeol"] > 17,
        "imp_gt14": lambda r: r["mood"] == "imp" and r["eojeol"] > 14,
        "imp_clauses_ge2": lambda r: r["mood"] == "imp" and r["clauses"] >= 2,
        "decl_17_25": lambda r: r["mood"] == "decl" and 17 < r["eojeol"] <= 25,
        "len_gt25": lambda r: r["eojeol"] > 25,
        "ui_ge2": lambda r: r["ui"] >= 2,
        "noun_run_ge4": lambda r: r["noun_run"] >= 4,
        "clauses_ge3": lambda r: r["clauses"] >= 3,
    }
    for key in K.PATTERNS:
        checks[key] = (lambda k: (lambda r: k in r["hits"]))(key)
    checks["B.kyungwoo"] = lambda r: "B.kyungwoo" in r["hits"]
    checks["S.comma_after_ec"] = lambda r: "S.comma_after_ec" in r["hits"]
    for name, fn in checks.items():
        sel = [r for r in human if fn(r)]
        sample = rng.sample(sel, min(25, len(sel)))
        with (review / f"{name}.tsv").open("w", encoding="utf-8") as f:
            f.write(f"# {len(sel)} hits\n")
            for r in sample:
                f.write(f"{r['src']}\t{r['eojeol']}\tui={r['ui']}\tnr={r['noun_run']}:{r['noun_span']}\tcl={r['clauses']}\t{r['sent']}\n")
    print(json.dumps({g: {k: v for k, v in s.items() if k in ("sentences", "eojeol", "fragments_excluded")} for g, s in result["groups"].items()}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
