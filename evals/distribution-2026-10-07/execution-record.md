# Independent installed-package forward execution

Recorded at: 2026-10-07 14:17:45 UTC.
Repository root for relative paths: `<repository>`.
Installed package: `.local/package-forward/ko-ste`.
Model identifier: **unknown**. The exact served model identifier was not exposed to this evaluating agent; no model identifier was inferred from the available tool catalog.

## Resources read into the agent context

| Resource | Exact SHA-256 |
|---|---|
| `.local/package-forward/ko-ste/SKILL.md` | `122A9A1AB8116841B071FB6923BA173DDCE84D291845499A08B9DBC1D6B023BE` |
| `.local/package-forward/ko-ste/references/01-rules.md` | `9BABD9D8107D969BEA00D767AD67962A063B4FB375B22F7276A32CF3CB7F607F` |
| `.local/package-forward/ko-ste/references/04-native-pairs.md` | `D828F1DC28198747ACABCFF49D36F981026DDF3BA039E7350ACA3ABDC0270BEC` |
| `evals/distribution-2026-10-07/inputs.json` | `CA92CE60F304D18AA22D1689CB0894DABFEDA26178AFEB70CE6542F9223EF7EE` |

External procedure resource, outside the repository:

| Resource | Exact SHA-256 |
|---|---|
| `<system-skills>/skill-creator/SKILL.md` | `CCCD291077EC57C6F50CA6529F0F3FB93212DA09473EFFB2FCEC808E81B21288` |

The skill-creator entrypoint was read completely, including Independent Forward-Testing. The installed entrypoint and both references were read completely. The initial batched tool output truncated the rules reference; its two line ranges were then read to obtain the whole file.

The optional `.local/package-forward/ko-ste/references/nikl-native-pairs.md` file was not installed: a direct `Test-Path` check returned false. No actual native quote pairs were read or claimed as checked. The excluded resources named in the task were not opened. No web sources or other evaluations were read.

## Execution

The six prompts were handled as separate user requests. Each answer used only its corresponding prompt facts and the installed guidance. The full answer strings were generated once and saved in `outputs.json` before the comparison helper was run. They were not changed after the helper output.

Tools actually used:

- `functions.exec` orchestrating `exec_command` with PowerShell for explicit-path text reads, SHA-256 hashing, saving the two requested artifacts, temporary comparison-file creation and cleanup, and JSON structure checks.
- `exec_command` invoking `uv`; the installed version reported `uv 0.10.0 (0ba432459 2026-02-05)`.
- `write_stdin` to collect the completed comparison command.
- `clock__curr_time` to record UTC time.

The first default-sandbox `Set-Content` attempt to save `outputs.json` returned Access denied. The same authorized save succeeded with `require_escalated`. Escalated shell execution was also used for the comparison helper, temporary-file cleanup, and this record. There was no automatic approval rejection.

## Actual checks

Manual source/result comparison covered conditions, scope, uncertainty, obligation, identifiers, code, and numbers. For the English translation, the supplied English facts and modality were compared manually. The direct-writing prompt had no comparison source.

For edited Korean inputs 1, 2, 4, and 5, the installed helper was invoked with:

```text
uv run --offline --no-project --with kiwipiepy==0.24.0 <installed-package>/scripts/check.py --compare <temporary-original.txt> <temporary-answer-body.txt>
```

`PYTHONDONTWRITEBYTECODE=1` was set for these runs. Comparison files held the original text and the answer body; clarification notes and the requested explanation table were excluded from the body comparison. Temporary files were stored under a newly created system temporary directory and removed afterward. No skill files were edited.

Execution resources were used by the installed comparison helper and hashed without loading their source as writing guidance:

| Resource | Exact SHA-256 |
|---|---|
| `.local/package-forward/ko-ste/scripts/check.py` | `948A7ACE1EA8F20F73CAF8E88CA847B3346D9D637F778B05E1656973C3B05B39` |
| `.local/package-forward/ko-ste/scripts/kostelib.py` | `545757567A798EB35C754FFD4E4912586D43297598CCABB0F477F8DD3B712559` |

All four comparison runs exited 0. Each also emitted:

```text
WARN `--no-project` was provided, but no project was found
```

Input 1 emitted this candidate:

```text
MP-2 scope 표지 4→3: 원문 {'경우': 1, '만': 1, '일부': 1, '면': 1} / 결과 {'만': 1, '일부': 1, '면': 1}
```

Inputs 2, 4, and 5 each emitted:

```text
보존 요소 차이 없음 (의미 보존을 증명하지는 않는다. 문맥으로 다시 확인한다.)
```

The saved artifact was parsed with PowerShell `ConvertFrom-Json`: it contained six records, unique IDs 1 through 6, and a string `output` for every record. The temporary comparison directory was confirmed removed.

## Saved answer artifact

| Artifact | Exact SHA-256 |
|---|---|
| `evals/distribution-2026-10-07/outputs.json` | `79225C04E8F03080AA842858354B14141E462B93AACC4C24A3054B86627220A6` |


Final serialization check: each saved answer string was compared case-sensitively with the frozen generated string in PowerShell. No mismatches were found. The saved outputs SHA-256 remained `79225C04E8F03080AA842858354B14141E462B93AACC4C24A3054B86627220A6`, and the execution-record path existed.

Public copy: private absolute paths were replaced with placeholders; resource hashes and outputs are unchanged. Read resources are preserved in read-snapshot/.
