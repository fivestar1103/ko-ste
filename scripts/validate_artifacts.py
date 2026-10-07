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
    assert marketplace["name"] == "ko-ste" and marketplace["plugins"][0]["source"] == "./"
    assert marketplace["plugins"][0]["name"] == meta["name"]
    for filename in re.findall(r"references/[\w.-]+\.md|scripts/[\w.-]+\.py", text):
        assert (SKILL / filename).is_file(), filename
    manifest = json.loads((ROOT / "calibration/corpus-manifest.json").read_text(encoding="utf-8"))
    lock = json.loads((ROOT / "calibration/data/corpus-lock.json").read_text(encoding="utf-8"))
    assert set(lock) == {s["id"] for s in manifest["sources"]}
    for source in manifest["sources"]:
        assert lock[source["id"]]["repo"] == source["repo"]
        assert re.fullmatch(r"[0-9a-f]{40}", lock[source["id"]]["commit"])
    for path in (ROOT / "calibration/data").glob("*.json"):
        json.loads(path.read_text(encoding="utf-8"))
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    for relative in re.findall(r'(?:src|srcset)="(assets/[^"]+)"', readme):
        assert (ROOT / relative).is_file(), relative
    for graphic in (ROOT / "assets").glob("*.svg"):
        ET.fromstring(graphic.read_text(encoding="utf-8"))
    print("Python syntax, skill/plugin manifests, reference files and corpus lock: OK")


if __name__ == "__main__":
    main()
