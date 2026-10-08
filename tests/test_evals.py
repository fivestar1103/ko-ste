"""Guard against missing judgments being reported as success."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "evals"))
sys.path.insert(0, str(ROOT / "skills" / "ko-ste" / "scripts"))
sys.path.insert(0, str(ROOT / "calibration/scripts"))
from common import extract_output
from judge import failed, normalize, summarize, valid_result
from run_evals import grade
import report
import dict_check
import check
import common


def result(**changes):
    return {"added": [], "dropped": [], "certainty_changed": [], "obligation_changed": [],
            "ambiguous_rewrite": False, "notes_quality": "none", **changes}


@pytest.mark.parametrize("value", [{}, {"error": "quota"}, result(added="missing"), result(ambiguous_rewrite="false")])
def test_invalid_judgment_is_not_a_pass(value):
    assert not valid_result(value)
    assert failed(value) is None


def test_error_does_not_enter_failure_rate_denominator():
    rows = [{"group": "a", "status": "ok", "result": result()},
            {"group": "a", "status": "error", "error": "quota"},
            {"group": "a", "status": "ok", "result": result(dropped=["일부"])},
            {"group": "a", "status": "ok", "result": {}}]
    a = summarize(rows)["a"]
    assert (a["expected"], a["completed"], a["pending"], a["fail"]) == (4, 2, 2, 1)


def test_disclosed_interpretation_choice_still_fails():
    assert failed(result(ambiguous_rewrite=True, notes_quality="useful"))


def test_absence_of_output_cannot_pass_negative_regex():
    ev = {"assertions": [{"id": "x", "text": "no obligation", "type": "regex_none", "pattern": "해야"}]}
    assert grade(ev, "")[0]["passed"] is None


def test_body_preserves_multiple_quoted_paragraphs_and_following_code():
    full = "> 첫 문장.\n\n> 둘째 문장.\n\n```sh\n확인 필요: literal\n```\n\n확인 필요: 범위를 물음"
    parsed = extract_output(full)
    assert "둘째 문장" in parsed["body"] and "literal" in parsed["body"]
    assert parsed["notes"] == "확인 필요: 범위를 물음"


def test_unquoted_document_separators_are_not_truncated():
    assert "둘째 문단" in extract_output("첫 문단.\n\n---\n\n둘째 문단.")["body"]


def test_no_changes_note_is_not_part_of_edited_body():
    parsed = extract_output("이 설정은 바꾸지 마.\n\n고칠 곳이 없습니다.")
    assert parsed["body"] == "이 설정은 바꾸지 마."
    assert parsed["notes"] == "고칠 곳이 없습니다."


def test_empty_report_markers_are_filled_and_idempotent():
    doc = "<!-- BEGIN:x -->\n<!-- END:x -->"
    updated = report.apply(doc, {"x": "table"})
    assert "table" in updated and report.apply(updated, {"x": "table"}) == updated
    with pytest.raises(ValueError):
        report.apply("no marker", {"x": "table"})


def test_dictionary_request_failure_is_not_zero_occurrences():
    rec = {"literal": {"a": {"stdict": -1}}, "natural": {}}
    assert dict_check.verdict(rec).startswith("미판정")


def test_changed_scope_marker_with_same_count_is_reported():
    assert any("MP-2" in s for s in check.compare("일부 요청이 실패했습니다.", "모든 요청이 실패했습니다."))


def test_code_blocks_and_windows_paths_are_protected():
    assert any("fenced_code" in s for s in check.compare("```sh\necho hello\n```", "```sh\necho bye\n```"))
    assert any("path" in s for s in check.compare(r"파일은 D:\app\settings.toml에 둡니다.", r"파일은 D:\app\config.toml에 둡니다."))


@pytest.mark.parametrize("response", [
    '{"is_error":true,"api_error":"usage_limit_reached","result":"quota"}',
    '{"result":"answer","permission_denials":[{"tool":"Read"}]}',
    '[]',
    '{"result":""}',
])
def test_failed_cli_cannot_supply_a_graded_answer(monkeypatch, response):
    class Process:
        returncode = 0
        def communicate(self, *_args, **_kwargs):
            return response, ""
    monkeypatch.setattr(common.subprocess, "Popen", lambda *_args, **_kwargs: Process())
    actual = common.invoke(["cli"], "prompt")
    assert actual["status"] == "error" and "data" not in actual


def test_object_items_from_judge_are_kept_as_failures():
    # 실패 항목을 객체로 돌려준 판정이 미판정으로 빠지면 실패율이 낮게 집계된다.
    raw = result(obligation_changed=[{"원문": "보내지 않아야", "결과": "보내야", "설명": "금지가 의무로 바뀜"}])
    assert not valid_result(raw)
    fixed = normalize(raw)
    assert valid_result(fixed)
    assert failed(fixed) is True
    assert "보내지 않아야" in fixed["obligation_changed"][0]
