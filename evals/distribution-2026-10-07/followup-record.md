# npm-installed skill follow-up execution

All paths below are relative to the ko-ste repository. Installed skill: `.local/npx-install-smoke/.agents/skills/ko-ste`.
Exact served model identifier: unknown; it was not exposed to this evaluating agent.

## Actual request source

The fresh request supplied in the task message was:

```text
ko-ste로 읽기 쉽게 고치고 바꾼 이유도 표로 보여줘.
인증 토큰의 갱신 수행이 필요합니다. 갱신 중에는 기존 토큰을 삭제하면 안 됩니다.
```

Source SHA-256: `398E010871A255225198EC6A6B1541611A9F2C0AC0DEBCA632ACBFA5BB1F7271`.
Hash encoding: UTF-8 without BOM, one LF between the two lines, no final newline.

## Resources actually read

The installed entrypoint and both references were read completely. A truncated batched rendering of the native-pair reference was followed by a separate full read. Linked resources were not opened.

| Resource | Exact SHA-256 |
|---|---|
| `.local/npx-install-smoke/.agents/skills/ko-ste/SKILL.md` | `3E0B02D254B79BF174A47B2DB9BD73409C40634C4FBCEB1DA84BE97461452E78` |
| `.local/npx-install-smoke/.agents/skills/ko-ste/references/01-rules.md` | `9BABD9D8107D969BEA00D767AD67962A063B4FB375B22F7276A32CF3CB7F607F` |
| `.local/npx-install-smoke/.agents/skills/ko-ste/references/04-native-pairs.md` | `21D12F3864E07D77CA720668EF1A3879CDABFF31CE1280D871E0701F38D46B9A` |

A direct `Test-Path` check found no optional `references/nikl-native-pairs.md` in the installed package. No actual native quote pairs were read or claimed as checked. No audits, tests, other evaluation artifacts, or external history were read for this request.

## Execution and checks

The answer was generated once from the fresh request and the current installed package. It was saved verbatim as UTF-8 without BOM or a final newline to `evals/distribution-2026-10-07/followup-output.md`. A case-sensitive PowerShell comparison confirmed that the saved string equaled the frozen generated string.

The source and answer body were manually compared for necessity, prohibition, the renewal condition, the token references, and formal sentence endings. The unchanged second sentence was also compared directly.

The current installed helper was run on temporary files containing only the source body and edited answer body; the requested explanation table was excluded from that comparison:

```text
uv run --offline --no-project --with kiwipiepy==0.24.0 .local/npx-install-smoke/.agents/skills/ko-ste/scripts/check.py --compare <temporary-original.txt> <temporary-answer-body.txt>
```

`PYTHONDONTWRITEBYTECODE=1` was set. The helper exited 0 and emitted:

```text
WARN `--no-project` was provided, but no project was found
보존 요소 차이 없음 (의미 보존을 증명하지는 않는다. 문맥으로 다시 확인한다.)
```

The two temporary files and their empty system temporary directory were removed. The answer hash remained unchanged after the check. The answer was not rewritten after checks. The prior six-output artifact was not opened or overwritten.

Execution resources were used by the current installed helper and hashed without loading their source as writing guidance:

| Resource | Exact SHA-256 |
|---|---|
| `.local/npx-install-smoke/.agents/skills/ko-ste/scripts/check.py` | `948A7ACE1EA8F20F73CAF8E88CA847B3346D9D637F778B05E1656973C3B05B39` |
| `.local/npx-install-smoke/.agents/skills/ko-ste/scripts/kostelib.py` | `3777A54C73E5E8CF48B4BAA26E3C62BB9C83D5A825A91C82B0704FF1CE92D17A` |

Actual tools: `functions.exec` with `exec_command`/PowerShell for explicit installed-file reads, SHA-256 hashing, exact string comparison, artifact saves, and invoking `uv`. Escalated execution saved the authorized artifacts and ran the temporary-file comparison workflow. No skill files were edited.

## Saved response

| Artifact | Exact SHA-256 |
|---|---|
| `evals/distribution-2026-10-07/followup-output.md` | `ED1808DE29424D7F6C28BBD8EAF20219CE55A842E66C86A3DE7A903E55D067E7` |
