"""Evaluation I/O. An unavailable or malformed result is never a pass."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

NOTE = re.compile(r"^(?:#{1,6}\s*)?(?:\*\*)?(?:그대로 둠|확인 필요|확인할 점|확인이 필요한 점|바꾼 점|고친 (?:부분|점|내용)|수정한|변경한|변경 사항|고칠 곳이 없(?:습니다|어요|다)?|참고|추가 권장|표로 정리|다른 표현)\b")
INTRO = re.compile(r"^(?:#{1,6}\s*)?(?:\*\*)?(?:다듬은|고친|수정한|수정안|권장안|추천안)[^\n]{0,30}?(?:\*\*)?\s*[:：]?\s*$")


def extract_output(full: str) -> dict:
    """Only remove recognizable editorial wrappers, outside fenced code.

    Never take just the first quote: that would discard later prose or code.
    Unrecognized commentary stays in the body for the judge to inspect.
    """
    lines = full.strip().splitlines()
    body, notes = [], []
    fence = None
    in_notes = False
    for line in lines:
        stripped = line.strip()
        marker = re.match(r"^(`{3,}|~{3,})", stripped)
        if not fence and not in_notes and not body and INTRO.match(stripped):
            continue
        if not fence and not in_notes and body and NOTE.match(stripped):
            in_notes = True
        if not fence and not in_notes and stripped == "---" and body:
            # A separator alone could be part of the document. Keep it unless
            # the following section is recognized as an editorial note.
            body.append(line)
            continue
        (notes if in_notes else body).append(line)
        if marker:
            char = marker[1][0]
            if fence is None:
                fence = (char, len(marker[1]))
            elif char == fence[0] and len(marker[1]) >= fence[1]:
                fence = None
    while notes and body and body[-1].strip() in {"", "---"}:
        body.pop()
    # Unwrap a quoted answer only if ALL nonempty lines are quoted.
    if body and all(not line.strip() or line.lstrip().startswith(">") for line in body):
        body = [re.sub(r"^\s*>\s?", "", line) for line in body]
    return {"body": "\n".join(body).strip(), "notes": "\n".join(notes).strip(),
            "status": "ok" if any(line.strip() for line in body) else "error"}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def skill_digest(skill: Path) -> str:
    items = [(p.relative_to(skill).as_posix(), digest(p)) for p in sorted(skill.rglob("*"))
             if p.is_file() and "__pycache__" not in p.parts and p.suffix in {".md", ".py"}]
    return hashlib.sha256(json.dumps(items, ensure_ascii=False).encode()).hexdigest()


def invoke(cmd: list[str], prompt: str, cwd: Path | None = None, timeout: int = 120) -> dict:
    try:
        process = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   text=True, encoding="utf-8", cwd=cwd, shell=(sys.platform == "win32"))
        try:
            stdout, _stderr = process.communicate(prompt, timeout=timeout)
        except subprocess.TimeoutExpired:
            if sys.platform == "win32":
                # Only kill the process tree created by this invocation.
                subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"], capture_output=True)
            process.kill()
            process.communicate()
            return {"error": "timeout", "status": "error"}
        data = json.loads(stdout)
    except subprocess.TimeoutExpired:
        return {"error": "timeout", "status": "error"}
    except (OSError, ValueError):
        return {"error": "CLI failed or returned invalid JSON", "status": "error"}
    if not isinstance(data, dict):
        return {"error": "CLI returned non-object JSON", "status": "error"}
    if process.returncode or data.get("is_error") or data.get("permission_denials") or not isinstance(data.get("result"), str) or not data["result"].strip():
        # Do not dump stderr or environment values into committed artifacts.
        return {"error": "CLI returned an error or empty result", "error_code": data.get("api_error", "cli_error"), "status": "error"}
    return {"status": "ok", "data": data}
