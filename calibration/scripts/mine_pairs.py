"""Git 이력에서 사람이 고친 한국어 문장 전후 쌍을 캔다.

pairs-manifest.json의 출처마다 다음을 한다.

1. 저장소를 blob 없이 받는다(calibration/cache/mining/<id>.git).
2. 작성일과 커밋일이 모두 cutoff 이전인 비병합 커밋에서 수정된 한국어 파일을 찾는다.
3. 수정 전후 파일을 문장으로 나누고 바뀐 문장끼리 정렬한다.
4. 바뀐 방식을 분류해 calibration/cache/pairs/<id>.jsonl에 쓴다.

여기서 나온 쌍은 후보다. 다듬기인지, 뜻이 바뀌었는지는 라벨링 단계에서 판정한다.

사용:
    uv run python calibration/scripts/mine_pairs.py --only k8s
"""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import re
import subprocess
import sys
from collections import Counter
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "skills/ko-ste/scripts"))
import kostelib as K  # noqa: E402


def git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=True, encoding="utf-8").stdout


# ---------------------------------------------------------------------------
# 1. 저장소와 blob


def ensure_repo(src: dict, cache: Path) -> Path:
    d = cache / "mining" / f"{src['id']}.git"
    if not d.exists():
        d.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "clone", "-q", "--bare", "--filter=blob:none", src["repo"], str(d)], check=True)
    return d


def prefetch(repo: Path, oids: list[str], chunk: int = 800) -> None:
    """빠진 blob을 한꺼번에 받는다. 하나씩 받으면 요청이 수천 번 나간다."""
    have = set()
    if oids:
        out = subprocess.run(
            ["git", "-C", str(repo), "cat-file", "--batch-check=%(objectname)", "--batch-all-objects"],
            check=True, capture_output=True, text=True,
        ).stdout
        have = set(out.split())
    missing = [o for o in oids if o not in have]
    for i in range(0, len(missing), chunk):
        subprocess.run(
            ["git", "-C", str(repo), "-c", "fetch.negotiationAlgorithm=noop", "fetch", "-q", "--no-tags",
             "--no-write-fetch-head", "--filter=blob:none", "origin", *missing[i : i + chunk]],
            check=True,
        )


class BlobReader:
    def __init__(self, repo: Path):
        self.p = subprocess.Popen(["git", "-C", str(repo), "cat-file", "--batch"], stdin=subprocess.PIPE, stdout=subprocess.PIPE)

    def read(self, oid: str) -> str:
        assert self.p.stdin and self.p.stdout
        self.p.stdin.write(oid.encode() + b"\n")
        self.p.stdin.flush()
        header = self.p.stdout.readline().split()
        if header[1] == b"missing":
            raise KeyError(oid)
        size = int(header[2])
        data = self.p.stdout.read(size)
        self.p.stdout.read(1)
        return data.decode("utf-8", errors="replace")


# ---------------------------------------------------------------------------
# 2. 커밋 목록


def changes(repo: Path, head: str, paths: list[str], cutoff: str, exclude_authors: str | None = None):
    """(커밋, 작성일, 제목, 경로, 수정 전 blob, 수정 후 blob)을 오래된 순으로 돌려준다.

    exclude_authors는 기계 번역 봇처럼 사람이 아닌 작성자를 거르는 정규식이다.
    작성자 이름은 거를 때만 쓰고 결과에 남기지 않는다.
    """
    cut = datetime.fromisoformat(cutoff)
    out = git(repo, "log", head, "--no-merges", "--no-renames", "--raw", "--no-abbrev", "--reverse",
              f"--before={cutoff}", "--format=\x01%H\t%aI\t%cI\t%an\t%s", "--", *paths)
    for block in out.split("\x01")[1:]:
        lines = block.strip("\n").split("\n")
        sha, adate, cdate, author, subject = lines[0].split("\t", 4)
        # 커밋일만 보면 오래된 날짜로 다시 쓴 커밋을 놓친다. 작성일도 함께 본다.
        if datetime.fromisoformat(adate) >= cut or datetime.fromisoformat(cdate) >= cut:
            continue
        if exclude_authors and re.search(exclude_authors, author, re.I):
            continue
        for ln in lines[1:]:
            if not ln.startswith(":"):
                continue
            meta, path = ln.split("\t", 1)
            _, _, old, new, status = meta[1:].split()
            if status == "M":
                yield sha, adate, subject, path, old, new


# ---------------------------------------------------------------------------
# 3. 문장 추출

SHORTCODE_TEXT = re.compile(r"\{\{[<%]\s*glossary_tooltip\b[^}]*?\btext=\"([^\"]*)\"[^}]*[>%]\}\}")
SHORTCODE = re.compile(r"\{\{[<%]\s*(/?)\s*([\w-]+)[^}]*[>%]\}\}")
# 글 안의 값이 아니라 문단을 감싸는 숏코드. 문장에서 지운다.
BLOCK_SHORTCODES = {
    "note", "caution", "warning", "feature-state", "tabs", "tab", "table", "codenew", "include", "capture",
    "comment", "figure", "mermaid", "glossary_definition", "toc", "details", "thirdparty-content", "alert",
    "callout", "version-check", "prerequisites", "whatsnext", "content", "blocks", "cncf-landscape",
}
HTML_COMMENT = re.compile(r"<!--.*?-->", re.S)
TOML_FRONT = re.compile(r"\A\+\+\+\n.*?\n\+\+\+\n", re.S)
INVISIBLE = re.compile("[​‌‍⁠﻿]")
LIST_ITEM = re.compile(r"^\s*([-*+]|\d+[.)])\s+")


def join_list_continuations(md: str) -> str:
    """목록 항목이 여러 줄에 걸치면 한 줄로 잇는다.

    parse_markdown은 들여 쓴 다음 줄을 새 문단으로 본다. 그대로 두면 줄을 바꾼
    수정이 문장을 나눈 수정으로 잡힌다.
    """
    out: list[str] = []
    in_fence = in_item = False
    for line in md.splitlines():
        if K.FENCE.match(line):
            in_fence = not in_fence
            in_item = False
            out.append(line)
            continue
        if in_fence:
            out.append(line)
            continue
        if not line.strip():
            in_item = False
            out.append(line)
            continue
        if LIST_ITEM.match(line):
            in_item = True
            out.append(line)
            continue
        s = line.strip()
        if in_item and line[:1] in " \t" and not s.startswith(("#", "|", ">", "<", "![", "{{")):
            out[-1] = out[-1].rstrip() + " " + s
            continue
        in_item = False
        out.append(line)
    return "\n".join(out)


def display_clean(raw: str) -> str:
    """사람이 읽을 형태로 남긴다. 인라인 코드는 백틱째 둔다."""
    s = K.LINK.sub(r"\1", raw)
    s = K.HTML_TAG.sub("", s)
    s = K.BOLD.sub(lambda m: m.group(1) or m.group(2), s)
    s = re.sub(r"(?<![*\w])\*(?=\S)([^*\n]+?)(?<=\S)\*(?![*\w])", r"\1", s)
    return re.sub(r"\s+", " ", s).strip()


def md_sentences(md: str) -> list[str]:
    md = INVISIBLE.sub("", md).replace(" ", " ")
    md = TOML_FRONT.sub("", md)
    md = HTML_COMMENT.sub("", md)
    md = SHORTCODE_TEXT.sub(r"\1", md)
    # 줄 전체가 숏코드면 지운다. 문장 안의 숏코드는 감싸는 것이면 지우고, 값이면 이름만 남긴다.
    md = re.sub(r"^\s*(\{\{[<%][^}]*[>%]\}\}\s*)+$", "", md, flags=re.M)
    md = SHORTCODE.sub(lambda m: "" if m.group(1) or m.group(2) in BLOCK_SHORTCODES else "{{" + m.group(2) + "}}", md)
    st = K.parse_markdown(join_list_continuations(md))
    sents: list[str] = []
    for u in st.units:
        text = display_clean(u.raw)
        if not K.HANGUL.search(text):
            continue
        sents.extend(K.split_sentences(text))
    return sents


def units_to_sentences(units: list[str]) -> list[str]:
    sents: list[str] = []
    for u in units:
        text = re.sub(r"\s+", " ", INVISIBLE.sub("", u).replace(" ", " ")).strip()
        if K.HANGUL.search(text):
            sents.extend(K.split_sentences(text))
    return sents


class _HtmlUnits(HTMLParser):
    """MDN 위키 HTML에서 문단 단위 글을 모은다. 코드 블록과 제목은 뺀다."""

    BLOCK = {"p", "li", "dd", "dt", "td", "th", "blockquote", "div", "section", "figcaption", "caption", "br"}
    SKIP = {"pre", "script", "style", "h1", "h2", "h3", "h4", "h5", "h6", "table"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.units: list[str] = []
        self.buf: list[str] = []
        self.skip = 0

    def flush(self):
        if self.buf:
            self.units.append("".join(self.buf))
            self.buf = []

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP:
            self.flush()
            self.skip += 1
        elif tag in self.BLOCK:
            self.flush()
        elif tag == "code" and not self.skip:
            self.buf.append("`")

    def handle_endtag(self, tag):
        if tag in self.SKIP:
            self.skip = max(0, self.skip - 1)
        elif tag in self.BLOCK:
            self.flush()
        elif tag == "code" and not self.skip:
            self.buf.append("`")

    def handle_data(self, data):
        if not self.skip:
            self.buf.append(data)


KUMA_MACRO = re.compile(r"\{\{\s*([\w-]+)[^}]*\}\}")


def html_sentences(html: str) -> list[str]:
    # MDN 위키 시절 문서. 표는 데이터라 빼고, KumaScript 매크로는 이름만 남긴다.
    if html.lstrip().startswith("---"):
        html = re.sub(r"\A\s*---\n.*?\n---\n", "", html, flags=re.S)
    html = KUMA_MACRO.sub(lambda m: "{{" + m.group(1) + "}}", html)
    p = _HtmlUnits()
    p.feed(html)
    p.flush()
    return units_to_sentences(p.units)


def mdn_sentences(text: str) -> list[str]:
    # 2021년 말부터 MDN 번역 문서가 HTML에서 마크다운으로 바뀌었다. 내용으로 고른다.
    body = re.sub(r"\A\s*---\n.*?\n---\n", "", text, flags=re.S)
    if re.search(r"<(p|li|dd|h2)[\s>]", body):
        return html_sentences(text)
    return md_sentences(KUMA_MACRO.sub(lambda m: "{{" + m.group(1) + "}}", text))


def ipynb_sentences(text: str) -> list[str]:
    try:
        nb = json.loads(text)
    except ValueError:
        return []
    cells = [c for c in nb.get("cells", []) if c.get("cell_type") == "markdown"]
    md = "\n\n".join("".join(c["source"]) if isinstance(c.get("source"), list) else c.get("source", "") for c in cells)
    return md_sentences(md)


RST_ROLE = re.compile(r":[\w:-]+:`([^`<]*?)(?:\s*<[^>]*>)?`")
RST_LINK = re.compile(r"`([^`<]+?)\s*<[^>]+>`_+")


def rst_sentences(text: str) -> list[str]:
    """reStructuredText. 지시어 블록, 리터럴 블록, 제목 밑줄을 빼고 문단만 남긴다."""
    units: list[str] = []
    buf: list[str] = []
    lines = text.splitlines()
    skip_indent: int | None = None

    def flush():
        if buf:
            units.append(" ".join(buf))
            buf.clear()

    for i, line in enumerate(lines):
        s = line.strip()
        indent = len(line) - len(line.lstrip())
        if skip_indent is not None:
            if not s or indent > skip_indent:
                continue
            skip_indent = None
        if not s:
            flush()
            continue
        if re.match(r"^([=\-~^\"'`#*+])\1{2,}$", s):
            buf.clear()  # 앞줄은 제목이었다
            continue
        if s.startswith(".. ") or s == "::":
            flush()
            skip_indent = indent
            continue
        if s.startswith(("|", "+-", "+=", ">>>")):
            flush()
            continue
        para = re.sub(r"^([-*+]|\d+\.|#\.)\s+", "", s)
        if para != s:
            flush()
        if s.endswith("::"):
            # 'foo::'는 'foo:'로, 'foo ::'는 'foo'로 보인다. 뒤의 들여 쓴 블록은 코드다.
            para = para[:-3] if para.endswith(" ::") else para[:-1]
            buf.append(para)
            flush()
            skip_indent = indent
            continue
        buf.append(para)
    flush()
    cleaned = []
    for u in units:
        u = RST_LINK.sub(r"\1", u)
        u = RST_ROLE.sub(r"`\1`", u)
        u = re.sub(r"``([^`]+)``", r"`\1`", u)
        u = re.sub(r"\*\*([^*]+)\*\*|\*([^*]+)\*", lambda m: m.group(1) or m.group(2), u)
        cleaned.append(u)
    return units_to_sentences(cleaned)


def sphinx_py_sentences(text: str) -> list[str]:
    """sphinx-gallery 튜토리얼(.py). 맨 앞 docstring과 '####' 다음 주석 블록이 본문이다."""
    parts: list[str] = []
    m = re.match(r'\s*(?:#[^\n]*\n\s*)*[rRuU]?("""|\'\'\')(.*?)\1', text, re.S)
    if m:
        parts.append(m.group(2))
    block: list[str] | None = None
    for line in text.splitlines():
        if re.match(r"^#{20,}\s*$", line) or re.match(r"^# %%", line):
            if block:
                parts.append("\n".join(block))
            block = []
            continue
        if block is not None:
            if line.startswith("#"):
                block.append(line[2:] if line.startswith("# ") else line[1:])
                continue
            if block:
                parts.append("\n".join(block))
            block = None
    if block:
        parts.append("\n".join(block))
    return rst_sentences("\n\n".join(parts))


def json_strings_sentences(text: str) -> list[str]:
    """번역 문자열 JSON(vscode-loc). 키 순서대로 한국어 문자열을 문단으로 본다."""
    try:
        data = json.loads(text)
    except ValueError:
        return []
    units: list[str] = []

    def walk(v):
        if isinstance(v, dict):
            for k in sorted(v):
                walk(v[k])
        elif isinstance(v, list):
            for x in v:
                walk(x)
        elif isinstance(v, str) and K.HANGUL.search(v):
            units.append(re.sub(r"&&", "", v))

    walk(data)
    return units_to_sentences(units)


def by_extension(handlers: dict[str, Callable[[str], list[str]]]) -> Callable[[str, str], list[str]]:
    def run(text: str, path: str) -> list[str]:
        for ext, fn in handlers.items():
            if path.endswith(ext):
                return fn(text)
        return []

    return run


EXTRACTORS: dict[str, Callable[[str, str], list[str]]] = {
    "md": lambda text, path: md_sentences(text),
    "mdn": lambda text, path: mdn_sentences(text),
    "tf": by_extension({".md": md_sentences, ".ipynb": ipynb_sentences}),
    "sphinx": by_extension({".rst": rst_sentences, ".py": sphinx_py_sentences}),
    "json": lambda text, path: json_strings_sentences(text),
}


def is_candidate(s: str) -> bool:
    letters = len(K.HANGUL.findall(s)) + len(re.findall(r"[A-Za-z]", re.sub(r"`[^`]*`", "", s)))
    return letters > 0 and len(K.HANGUL.findall(s)) / letters >= 0.5 and len(K.eojeols(s)) >= 3


# ---------------------------------------------------------------------------
# 4. 정렬과 분류

MIN_SIM = 0.5


def sim(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, a, b, autojunk=False).ratio()


def align_block(old: list[str], new: list[str]) -> list[tuple[list[int], list[int], float]]:
    """바뀐 구간 안에서 1:1, 1:2(나눔), 2:1(합침) 짝을 고른다. 순서는 지킨다."""
    n, m = len(old), len(new)
    if n * m > 400:  # 통째로 다시 쓴 구간은 쌍으로 보지 않는다
        return []
    best = [[(0.0, None)] * (m + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        for j in range(m + 1):
            if i == 0 and j == 0:
                continue
            cands = []
            if i:
                cands.append((best[i - 1][j][0], ("skip_old", i - 1, j)))
            if j:
                cands.append((best[i][j - 1][0], ("skip_new", i, j - 1)))
            for di, dj in ((1, 1), (1, 2), (2, 1)):
                if i >= di and j >= dj:
                    s = sim(" ".join(old[i - di : i]), " ".join(new[j - dj : j]))
                    if s >= MIN_SIM:
                        # 나눔·합침은 1:1보다 확실할 때만 고르도록 조금 깎는다
                        gain = s - MIN_SIM - (0.05 if di + dj > 2 else 0)
                        cands.append((best[i - di][j - dj][0] + gain, ("pair", i - di, j - dj, s)))
            best[i][j] = max(cands, key=lambda c: c[0])
    out = []
    i, j = n, m
    while i or j:
        step = best[i][j][1]
        if step[0] == "pair":
            _, pi, pj, s = step
            out.append((list(range(pi, i)), list(range(pj, j)), s))
            i, j = pi, pj
        else:
            i, j = step[1], step[2]
    return out[::-1]


PROTECTED = re.compile(r"`[^`]+`|https?://\S+|[A-Za-z][A-Za-z0-9_.\-/]*|\d+(?:[.,]\d+)*")
PUNCT = re.compile(r"[\s.,!?·:;\"'()\[\]「」『』<>~\-–—…/]")


def jamo(s: str) -> str:
    out = []
    for ch in s:
        c = ord(ch) - 0xAC00
        if 0 <= c < 11172:
            out.append(chr(0x1100 + c // 588) + chr(0x1161 + (c % 588) // 28) + (chr(0x11A7 + c % 28) if c % 28 else ""))
        else:
            out.append(ch)
    return "".join(out)


def edit_distance(a: str, b: str) -> int:
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def classify(before: list[str], after: list[str]) -> str:
    b, a = " ".join(before), " ".join(after)
    if len(before) != len(after) and re.sub(r"\s+", "", b) == re.sub(r"\s+", "", a):
        return "reflow"  # 문장 분리만 달라졌다
    if len(before) < len(after):
        return "split"
    if len(before) > len(after):
        return "merge"
    if re.sub(r"\s+", "", b) == re.sub(r"\s+", "", a):
        return "spacing"
    if PUNCT.sub("", b) == PUNCT.sub("", a):
        return "punct"
    if Counter(PROTECTED.findall(b)) != Counter(PROTECTED.findall(a)):
        return "token"
    bw, aw = b.split(), a.split()
    changed = sum(1 for x, y in zip(bw, aw) if x != y) + abs(len(bw) - len(aw))
    if changed <= 1 and edit_distance(jamo(b), jamo(a)) <= 2:
        return "minor"
    return "rewrite"


SUBJECT_TAGS = {
    "typo": r"오타|오탈자|typo|맞춤법|띄어쓰기|spacing|spelling",
    "style": r"다듬|자연스|어색|가독|문장|표현|번역 ?(개선|수정|보완)|improve|polish|wording|refine|readab|proofread|교정|윤문|review",
    "term": r"용어|번역어|glossary|terminolog|consisten|통일",
    "sync": r"outdated|sync|업데이트|update|최신화|upstream",
    "translate": r"translat|번역 ?추가|localiz|l10n",
}


def subject_tags(subject: str) -> list[str]:
    return [k for k, rx in SUBJECT_TAGS.items() if re.search(rx, subject, re.I)]


# ---------------------------------------------------------------------------
# 5. 실행


def mine(src: dict, cache: Path, cutoff: str, head: str | None) -> tuple[list[dict], dict]:
    repo = ensure_repo(src, cache)
    head = head or git(repo, "rev-parse", "HEAD").strip()
    # 출처마다 더 이른 cutoff를 둘 수 있다(기계 번역을 들이기 전까지만 읽을 때).
    cutoff = min(cutoff, src.get("cutoff", cutoff), key=datetime.fromisoformat)
    rows = list(changes(repo, head, src["paths"], cutoff, src.get("exclude_authors")))
    prefetch(repo, sorted({o for r in rows for o in r[4:6]}))
    reader = BlobReader(repo)
    extract = EXTRACTORS[src["format"]]
    sent_cache: dict[str, list[str]] = {}

    def sents(oid: str, path: str) -> list[str]:
        if oid not in sent_cache:
            sent_cache[oid] = extract(reader.read(oid), path)
        return sent_cache[oid]

    pairs: list[dict] = []
    seen: set[tuple[str, str]] = set()
    stats = Counter()
    for sha, adate, subject, path, old_oid, new_oid in rows:
        stats["file_changes"] += 1
        old, new = sents(old_oid, path), sents(new_oid, path)
        sm = difflib.SequenceMatcher(None, old, new, autojunk=False)
        for op, i1, i2, j1, j2 in sm.get_opcodes():
            if op == "equal":
                stats["unchanged_sentences"] += i2 - i1
                continue
            if op != "replace":
                continue
            for oi, nj, s in align_block(old[i1:i2], new[j1:j2]):
                before = [old[i1 + k] for k in oi]
                after = [new[j1 + k] for k in nj]
                if not all(is_candidate(x) for x in before + after):
                    continue
                key = (" ".join(before), " ".join(after))
                if key in seen:
                    stats["duplicate"] += 1
                    continue
                seen.add(key)
                kind = classify(before, after)
                if kind == "reflow":
                    stats["reflow"] += 1
                    continue
                first = i1 + oi[0]
                pairs.append({
                    "id": hashlib.sha1("\x00".join([src["id"], sha, path, *key]).encode()).hexdigest()[:12],
                    "source": src["id"],
                    "commit": sha,
                    "date": adate[:10],
                    "path": path,
                    "subject": subject,
                    "tags": subject_tags(subject),
                    "kind": kind,
                    "sim": round(s, 3),
                    "before": before,
                    "after": after,
                    "prev": old[first - 1] if first > 0 else "",
                    "next": old[i1 + oi[-1] + 1] if i1 + oi[-1] + 1 < len(old) else "",
                })
    # 나중에 되돌린 수정은 표시한다. 다듬기로 확정된 수정이 아니다.
    keys = {(" ".join(p["before"]), " ".join(p["after"])) for p in pairs}
    for p in pairs:
        p["reverted"] = (" ".join(p["after"]), " ".join(p["before"])) in keys
    stats["pairs"] = len(pairs)
    stats.update(f"kind.{p['kind']}" for p in pairs)
    stats["commits"] = len({r[0] for r in rows})
    return pairs, {"head": head, "stats": dict(sorted(stats.items()))}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", default=str(ROOT / "calibration/pairs-manifest.json"))
    ap.add_argument("--cache", default=str(ROOT / "calibration/cache"))
    ap.add_argument("--lock", default=str(ROOT / "calibration/data/pairs-lock.json"))
    ap.add_argument("--only", nargs="*", help="이 출처만 캔다")
    ap.add_argument("--refresh-lock", action="store_true", help="고정한 HEAD 대신 현재 HEAD를 쓴다")
    args = ap.parse_args()

    manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    cache = Path(args.cache)
    lock_path = Path(args.lock)
    lock = json.loads(lock_path.read_text(encoding="utf-8")) if lock_path.exists() else {}
    out_dir = cache / "pairs"
    out_dir.mkdir(parents=True, exist_ok=True)
    for src in manifest["sources"]:
        if args.only and src["id"] not in args.only:
            continue
        locked = None if args.refresh_lock else lock.get(src["id"], {}).get("head")
        pairs, info = mine(src, cache, manifest["cutoff"], locked)
        with (out_dir / f"{src['id']}.jsonl").open("w", encoding="utf-8") as f:
            for p in pairs:
                f.write(json.dumps(p, ensure_ascii=False) + "\n")
        cutoff = min(manifest["cutoff"], src.get("cutoff", manifest["cutoff"]), key=datetime.fromisoformat)
        lock[src["id"]] = {"repo": src["repo"], "head": info["head"], "cutoff": cutoff, "stats": info["stats"]}
        print(src["id"], json.dumps(info["stats"], ensure_ascii=False))
    # 다른 출처를 동시에 캐는 실행이 있을 수 있다. 쓰기 직전에 다시 읽어 이번에 캔 출처만 고친다.
    current = json.loads(lock_path.read_text(encoding="utf-8")) if lock_path.exists() else {}
    current.update({k: v for k, v in lock.items() if not args.only or k in args.only})
    lock_path.write_text(json.dumps(current, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
