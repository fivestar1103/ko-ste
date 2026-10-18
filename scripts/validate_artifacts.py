"""Portable syntax, skill format and provenance checks (no model/network calls)."""
import ast
import json
import re
import tomllib
import xml.etree.ElementTree as ET
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "ko-ste"


def check_tech_pairs():
    """기술 문서 전후 쌍: 출처·기간·라이선스 고지와 평가용 쌍의 분리를 확인한다."""
    manifest = json.loads((ROOT / "calibration/pairs-manifest.json").read_text(encoding="utf-8"))
    lock = json.loads((ROOT / "calibration/data/pairs-lock.json").read_text(encoding="utf-8"))
    sources = {s["id"]: s for s in manifest["sources"]}
    cutoff = manifest["cutoff"][:10]
    notice = (SKILL / "PAIRS-NOTICE.md").read_text(encoding="utf-8")
    shipped_ids = set()
    for name in ("pairs", "pairs-cc-by-sa"):
        for line in (SKILL / "data" / f"{name}.jsonl").read_text(encoding="utf-8").splitlines():
            row = json.loads(line)
            src = sources[row["source"]]
            assert row["license"] == src["license"], row["id"]
            # CC BY-SA 문장은 따로 둔 파일에만 둔다
            assert ("SA" in src["license"]) == (name == "pairs-cc-by-sa"), row["id"]
            assert row["date"] < min(cutoff, src.get("cutoff", cutoff)[:10]), row["id"]
            assert row["rules"] and all(re.fullmatch(r"(MP|ST|SE|MO|AM|LX|RD|FM)-\d+", r) for r in row["rules"])
            assert re.fullmatch(r"[0-9a-f]{40}", row["commit"]) and row["before"] != row["after"]
            assert f"| {row['source']} |" in notice, f"Missing notice row: {row['source']}"
            assert any((SKILL / "data/licenses").glob(f"{row['source']}-*.txt")), f"Missing license copy: {row['source']}"
            assert re.fullmatch(r"[0-9a-f]{40}", lock[row["source"]]["head"])
            shipped_ids.add(row["id"])
    heldout = (ROOT / "evals/human-pairs/heldout.jsonl").read_text(encoding="utf-8").splitlines()
    held_commits = {json.loads(l)["commit"] for l in heldout}
    assert not shipped_ids & {json.loads(l)["id"] for l in heldout}, "held-out pair leaked into skill data"
    for name in ("pairs", "pairs-cc-by-sa"):
        for line in (SKILL / "data" / f"{name}.jsonl").read_text(encoding="utf-8").splitlines():
            assert json.loads(line)["commit"] not in held_commits, "held-out commit leaked into skill data"
    reference = (SKILL / "references/05-tech-pairs.md").read_text(encoding="utf-8")
    assert "../PAIRS-NOTICE.md" in reference
    share_alike = {s["id"] for s in manifest["sources"] if "SA" in s["license"]}
    for cell in re.findall(r"^\| (\S+) `[0-9a-f]{7}` \|", reference, re.M):
        assert cell in sources and cell not in share_alike, f"05-tech-pairs.md must not quote {cell}"


def main():
    for folder in (ROOT / "scripts", ROOT / "tests", ROOT / "evals", ROOT / "calibration/scripts", SKILL / "scripts"):
        for path in folder.glob("*.py"):
            ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
    text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    front = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    assert front, "Missing skill frontmatter"
    meta = yaml.safe_load(front[1])
    assert meta["name"] == "ko-ste" and isinstance(meta["description"], str)
    assert 0 < len(meta["description"]) <= 1024
    version = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]["version"]
    for relative in ("plugin.json", ".claude-plugin/plugin.json", ".codex-plugin/plugin.json"):
        plugin = json.loads((ROOT / relative).read_text(encoding="utf-8"))
        assert plugin["name"] == meta["name"] and plugin["version"] == version
        assert plugin["license"] == "MIT"
    marketplace = json.loads((ROOT / ".claude-plugin/marketplace.json").read_text(encoding="utf-8"))
    entry = marketplace["plugins"][0]
    # 스킬 폴더만 플러그인으로 설치한다. 저장소 전체(평가 원출력, 말뭉치 집계)를 복사하지 않는다.
    assert marketplace["name"] == "ko-ste" and entry["source"] == "./skills/ko-ste"
    assert entry["name"] == meta["name"] and entry["version"] == version and entry["license"] == "MIT"
    assert not (SKILL / ".claude-plugin").exists() and not (SKILL / "skills").exists(), "skill folder must load as a single-skill plugin"
    for filename in re.findall(r"references/[\w.-]+\.md|scripts/[\w.-]+\.py", text):
        assert (SKILL / filename).is_file(), filename
    manifest = json.loads((ROOT / "calibration/corpus-manifest.json").read_text(encoding="utf-8"))
    lock = json.loads((ROOT / "calibration/data/corpus-lock.json").read_text(encoding="utf-8"))
    assert set(lock) == {s["id"] for s in manifest["sources"]}
    for source in manifest["sources"]:
        assert lock[source["id"]]["repo"] == source["repo"]
        assert re.fullmatch(r"[0-9a-f]{40}", lock[source["id"]]["commit"])
    provenance = json.loads((ROOT / "docs/license-sources.json").read_text(encoding="utf-8"))
    sources = {s["id"]: s for s in provenance["sources"]}
    for source_id, pinned in lock.items():
        assert sources[source_id]["ref"] == pinned["commit"], f"Stale license record: {source_id}"
    for source in sources.values():
        for evidence in source["evidence"]:
            assert re.fullmatch(r"[0-9a-f]{64}", evidence["sha256"]), source["id"]
    for notice in ("LICENSE", "NOTICE.md", "UPSTREAM-LICENSES.md", "NIKL-NOTICE.md"):
        assert (SKILL / notice).is_file(), f"Missing installed license notice: {notice}"
    assert (SKILL / "LICENSE").read_bytes() == (ROOT / "LICENSE").read_bytes()
    for relative in ("skills/ko-ste/NIKL-NOTICE.md", "evals/NOTICE.md", "docs/license-review.md"):
        assert (ROOT / relative).is_file(), f"Missing provenance notice: {relative}"
    pairs = (SKILL / "references/04-native-pairs.md").read_text(encoding="utf-8")
    assert len(re.findall(r"^\| NP-\d\d \|", pairs, re.M)) == 55, "native pairs missing from installed skill"
    assert len(re.findall(r"^\| X-\d\d \|", pairs, re.M)) == 20
    assert "../NIKL-NOTICE.md" in pairs and "공공누리 제3유형" in pairs
    check_tech_pairs()
    for path in (ROOT / "calibration/data").glob("*.json"):
        json.loads(path.read_text(encoding="utf-8"))
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    images = re.findall(r'(?:src|srcset)="(assets/[^"]+)"', readme)
    images += re.findall(r'!\[[^\]]*\]\((assets/[^)]+)\)', readme)
    for relative in images:
        assert (ROOT / relative).is_file(), relative
    for graphic in (ROOT / "assets").glob("*.svg"):
        ET.fromstring(graphic.read_text(encoding="utf-8"))
    print("Python syntax, skill/plugin manifests, notices, reference files and corpus/license locks: OK")


if __name__ == "__main__":
    main()
