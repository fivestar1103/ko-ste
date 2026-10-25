"""라벨을 붙인 전후 쌍에서 본보기를 골라 스킬 자료로 쓴다.

고르는 조건:
- label_pairs.py 판정: meaning이 "same", direction이 "better", exemplar가 true,
  purpose가 style, grammar 중 하나
- verify_pairs.py 재판정: keep이 true. 규칙 ID는 재판정 쪽을 쓴다.
- 나중에 되돌린 수정이 아님

커밋 해시로 쌍을 나눠 일부는 평가용으로 떼어 둔다. 같은 커밋의 쌍은 같은 쪽에 들어가므로
본보기와 평가 사례가 같은 수정에서 나오지 않는다.

출력:
- skills/ko-ste/references/05-tech-pairs.md 규칙별 대표 쌍(CC BY-SA 출처는 넣지 않는다)
- skills/ko-ste/data/pairs.jsonl            MIT·BSD·Apache·CC BY 출처의 본보기
- skills/ko-ste/data/pairs-cc-by-sa.jsonl   CC BY-SA 출처(MDN)의 본보기
- evals/human-pairs/heldout.jsonl           평가용으로 떼어 둔 쌍(스킬에 넣지 않는다)
- skills/ko-ste/PAIRS-NOTICE.md             출처별 이용 조건과 고지
- skills/ko-ste/data/licenses/              출처 저장소의 라이선스 파일 사본
- calibration/data/pairs-summary.json       출처·규칙별 집계
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
# 용어만 바꾼 쌍(purpose "term")은 뺀다. 번역 프로젝트의 용어집을 따른 교체라서 일반적인 다듬기의
# 본보기가 아니다. 본보기로 두면 독자가 쓰는 기술 용어까지 바꾸게 만들 수 있다(LX-5).
KEEP_PURPOSE = {"style", "grammar"}
HELDOUT_SHARE = 5  # 커밋 해시 기준 5분의 1을 평가용으로 뗀다


def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(l) for l in path.open(encoding="utf-8") if l.strip()]


def heldout(commit: str) -> bool:
    return int(hashlib.sha256(commit.encode()).hexdigest(), 16) % HELDOUT_SHARE == 0


def license_file(repo: Path, head: str, preferred: str | None) -> tuple[str, str]:
    names = subprocess.run(["git", "-C", str(repo), "ls-tree", "--name-only", head], check=True,
                           capture_output=True, text=True).stdout.split()
    name = preferred or next(n for n in names if "licen" in n.lower())
    text = subprocess.run(["git", "-C", str(repo), "show", f"{head}:{name}"], check=True,
                          capture_output=True, text=True, encoding="utf-8").stdout
    return name, text


LICENSE_URLS = {
    "CC-BY-4.0": "https://creativecommons.org/licenses/by/4.0/",
    "CC-BY-SA-2.5": "https://creativecommons.org/licenses/by-sa/2.5/",
    "CC-BY-SA-3.0": "https://creativecommons.org/licenses/by-sa/3.0/",
}

NOTICE_HEAD = """# 전후 쌍 자료의 출처와 이용 조건

`data/pairs.jsonl`과 `data/pairs-cc-by-sa.jsonl`의 `before`·`after`는 아래 공개 저장소의 Git 이력에서
발췌한 문장이다. 이 문장들은 ko-ste의 MIT 조건이 아니라 각 출처의 조건을 따른다.

- 발췌 방식: 사람이 고친 커밋에서 고치기 전 문장과 고친 뒤 문장을 문장 단위로 뽑았다. 마크다운·HTML 표시와
  숏코드를 지웠고 문장 자체는 고치지 않았다. 각 행의 `commit`과 `path`가 원래 위치다.
- 기간: 작성일과 커밋일이 모두 {cutoff} 이전인 커밋만 썼다. ChatGPT 공개(2022-11-30) 전에 쓴 글만 모으려는 것이다.
- `rules`, `purpose`, `label_note`는 ko-ste가 붙인 분류다(Claude 판정, 사람 검수 전). 출처 저장소의 견해가 아니다.
- CC BY-SA 출처의 문장은 `data/pairs-cc-by-sa.jsonl`에만 있다. 이 파일을 고쳐 배포하면 같은 조건(CC BY-SA)을 따라야 한다.
- 출처 저장소의 라이선스 파일 사본은 `data/licenses/`에 있다.

| 출처 | 저장소 | 고정 커밋 | 이용 조건 | 저작자 표시 | 쌍 |
|---|---|---|---|---|---|
"""


PER_RULE = 4
MAX_EOJEOL = 35

REFERENCE_HEAD = """# 사람이 고친 기술 문서 전후 쌍

이 파일은 공개 기술 문서 번역 저장소의 Git 이력에서 사람이 고친 문장을 규칙별로 몇 개씩 골라 보인다.
작성일과 커밋일이 모두 {cutoff} 이전인 수정만 썼다. 고치기 전과 고친 뒤 문장은 원문 그대로다.
출처와 이용 조건은 [PAIRS-NOTICE.md](../PAIRS-NOTICE.md)에 있다. 이 파일의 문장은 MIT 자료가 아니다.

- 고른 방법: Claude 판정 두 번(뜻이 같고, 규칙에 비추어 나아졌는가)을 모두 통과한 쌍이다. 사람이 검수하기 전이다.
- 쓰는 법: 같은 규칙의 문장을 고칠 때 고치는 폭과 방식을 참고한다. 문장을 출력에 옮겨 쓰지 않는다.
- 더 찾기: `python scripts/pairs.py --rule <규칙 ID>`는 전체 {total}쌍에서 찾는다.

"""


def eojeol_count(s: str) -> int:
    return len(s.split())


def write_reference(rows: list[dict], manifest: dict) -> None:
    """규칙마다 짧은 쌍을 출처가 겹치지 않게 몇 개씩 고른다."""
    by_rule: dict[str, list[dict]] = defaultdict(list)
    for r in sorted(rows, key=lambda r: hashlib.sha256(r["id"].encode()).hexdigest()):
        if eojeol_count(r["before"]) <= MAX_EOJEOL and len(r["rules"]) == 1:
            by_rule[r["rules"][0]].append(r)
    order = lambda rid: (rid.split("-")[0], int(rid.split("-")[1]))  # noqa: E731
    parts = [REFERENCE_HEAD.format(cutoff=manifest["cutoff"][:10], total=len(rows))]
    for rule in sorted(by_rule, key=order):
        # 출처와 커밋이 겹치지 않게 고른다. 한 커밋이 같은 낱말을 일괄로 바꾼 경우가 많다.
        # 1차: 새 출처이면서 새 커밋, 2차: 새 커밋, 3차: 남은 쌍.
        picked: list[dict] = []
        for fresh in (lambda r: r["source"] not in {x["source"] for x in picked}
                      and r["commit"] not in {x["commit"] for x in picked},
                      lambda r: r["commit"] not in {x["commit"] for x in picked},
                      lambda r: True):
            for r in by_rule[rule]:
                if len(picked) < PER_RULE and r not in picked and fresh(r):
                    picked.append(r)
        parts.append(f"## {rule}\n\n| 출처 | 고치기 전 | 사람이 고친 글 |\n|---|---|---|\n")
        for r in picked:
            cell = lambda t: t.replace("|", "\\|")  # noqa: E731
            parts.append(f"| {r['source']} `{r['commit'][:7]}` | {cell(r['before'])} | {cell(r['after'])} |\n")
        parts.append("\n")
    (ROOT / "skills/ko-ste/references/05-tech-pairs.md").write_text("".join(parts).rstrip() + "\n", encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", default=str(ROOT / "calibration/pairs-manifest.json"))
    ap.add_argument("--cache", default=str(ROOT / "calibration/cache"))
    args = ap.parse_args()

    manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    cache = Path(args.cache)
    summary: dict = {"sources": {}, "rules": Counter()}
    shipped: dict[str, list[dict]] = defaultdict(list)
    held: list[dict] = []
    for src in manifest["sources"]:
        pairs = {p["id"]: p for p in load_jsonl(cache / "pairs" / f"{src['id']}.jsonl")}
        labels = load_jsonl(cache / "labels" / f"{src['id']}.jsonl")
        verdicts = {v["id"]: v for v in load_jsonl(cache / "verify" / f"{src['id']}.jsonl")}
        if not labels:
            continue
        stat = Counter(mined=len(pairs), labeled=len(labels), verified=len(verdicts))
        stat.update(f"meaning.{l['meaning']}" for l in labels)
        stat.update(f"purpose.{l['purpose']}" for l in labels)
        stat.update(f"direction.{l['direction']}" for l in labels)
        for lab in labels:
            p = pairs.get(lab["id"])
            if p is None:
                continue
            ok = (lab["meaning"] == "same" and lab["direction"] == "better" and lab["exemplar"]
                  and lab["purpose"] in KEEP_PURPOSE and not p["reverted"])
            if not ok:
                continue
            stat["exemplar_candidates"] += 1
            v = verdicts.get(lab["id"])
            if v is None or not v["keep"] or not v["rules"]:
                continue
            stat["verified_kept"] += 1
            # 문체 규칙(FM-)만 걸린 쌍은 문서 전체의 어미를 맞춘 수정이다. 한 문장만 떼어 보이면
            # 높임 수준을 바꾸라는 본보기로 읽힐 수 있다(MP-6).
            if all(r.startswith("FM-") for r in v["rules"]):
                stat["style_only_dropped"] += 1
                continue
            row = {
                "id": f"{src['id']}-{p['id']}",
                "rules": v["rules"],
                "purpose": lab["purpose"],
                "before": " ".join(p["before"]),
                "after": " ".join(p["after"]),
                "source": src["id"],
                "commit": p["commit"],
                "path": p["path"],
                "date": p["date"],
                "license": src["license"],
                "label_note": lab["note"],
            }
            if heldout(p["commit"]):
                held.append({**row, "prev": p["prev"], "next": p["next"]})
                stat["heldout"] += 1
            else:
                bucket = "pairs-cc-by-sa" if "SA" in src["license"] else "pairs"
                shipped[bucket].append(row)
                stat["shipped"] += 1
                summary["rules"].update(v["rules"])
        summary["sources"][src["id"]] = dict(sorted(stat.items()))

    data_dir = ROOT / "skills/ko-ste/data"
    data_dir.mkdir(parents=True, exist_ok=True)
    for name in ("pairs", "pairs-cc-by-sa"):
        rows = sorted(shipped.get(name, []), key=lambda r: r["id"])
        with (data_dir / f"{name}.jsonl").open("w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
    write_reference(shipped.get("pairs", []), manifest)
    eval_dir = ROOT / "evals/human-pairs"
    eval_dir.mkdir(parents=True, exist_ok=True)
    with (eval_dir / "heldout.jsonl").open("w", encoding="utf-8") as f:
        for r in sorted(held, key=lambda r: r["id"]):
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    lock = json.loads((ROOT / "calibration/data/pairs-lock.json").read_text(encoding="utf-8"))
    lic_dir = data_dir / "licenses"
    lic_dir.mkdir(parents=True, exist_ok=True)
    lines = [NOTICE_HEAD.format(cutoff=manifest["cutoff"][:10])]
    for src in manifest["sources"]:
        n = summary["sources"].get(src["id"], {}).get("shipped", 0)
        if not n:
            continue
        head = lock[src["id"]]["head"]
        name, text = license_file(cache / "mining" / f"{src['id']}.git", head, src.get("license_file"))
        (lic_dir / f"{src['id']}-{Path(name).stem}.txt").write_text(text, encoding="utf-8")
        repo_url = src["repo"].removesuffix(".git")
        lic_file = f"data/licenses/{src['id']}-{Path(name).stem}.txt"
        lic = f"[{src['license']}]({LICENSE_URLS[src['license']]})" if src["license"] in LICENSE_URLS else src["license"]
        lines.append(f"| {src['id']} | [{repo_url.split('github.com/')[1]}]({repo_url}) | `{head[:10]}` | "
                     f"{lic}, [사본]({lic_file}) | {src['attribution']} | {n} |\n")
    (ROOT / "skills/ko-ste/PAIRS-NOTICE.md").write_text("".join(lines), encoding="utf-8")
    summary["rules"] = dict(summary["rules"].most_common())
    (ROOT / "calibration/data/pairs-summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
