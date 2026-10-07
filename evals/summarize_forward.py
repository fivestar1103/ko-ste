"""Recreate the summary of the independent, blinded follow-up review."""
import hashlib
import json
import sys
from pathlib import Path

from common import extract_output
from judge import valid_result, failed
from prepare_forward import BASE, ORIGINALS


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    reviews = json.loads((BASE / "blind-review.json").read_text(encoding="utf-8"))
    mapping = json.loads((BASE / "review-mapping.json").read_text(encoding="utf-8"))
    assert {r["id"] for r in reviews} == set(mapping), "Review coverage mismatch"
    summary = {}
    for r in reviews:
        assert valid_result(r), r["id"]
        cfg = mapping[r["id"]]["config"]
        s = summary.setdefault(cfg, {"reviewed": 0, "flagged": 0, "useful_notes": 0, "noise_notes": 0})
        s["reviewed"] += 1
        s["flagged"] += int(bool(failed(r)))
        s["useful_notes"] += int(r["notes_quality"] == "useful")
        s["noise_notes"] += int(r["notes_quality"] == "noise")
    lines = ["| 설정 | 검토 출력 | 의미 변경 지적 | 유용한 알림 | 잡음 알림 |", "|---|---|---|---|---|"]
    for cfg in ("with_skill", "without_skill"):
        s = summary[cfg]
        lines.append(f"| {cfg} | {s['reviewed']} | {s['flagged']} | {s['useful_notes']} | {s['noise_notes']} |")
    lines += ["", "미사용 출력의 지적 2건 중 1건(item-02)은 서술형이 원래 절차 지시인지 판단할 문맥이 없어 불확실합니다.",
              "item-07은 실패 조건을 두 동작 모두에 걸도록 구조를 확정한 변경이 지적됐습니다. 이 해석 판정도 사람의 정답 자료로 확인한 것은 아닙니다.", "",
              "이미 명확한 두 입력(1·4번)의 본문을 그대로 유지한 수:"]
    for cfg in ("with_skill", "without_skill"):
        exact = sum(extract_output((BASE / cfg / f"case-{n}" / "output.md").read_text(encoding="utf-8"))["body"] == ORIGINALS[n - 1] for n in (1, 4))
        summary[cfg]["unchanged_clear_inputs"] = exact
        lines.append(f"- {cfg}: {exact}/2")
    lines += ["", "표본 5개에 대한 모델 판정입니다. 실패율이나 독자 이해도의 개선을 일반화하지 않습니다."]
    (BASE / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    (BASE / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
