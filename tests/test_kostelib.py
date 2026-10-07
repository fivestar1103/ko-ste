"""kostelib 측정 함수 시험. 보정에서 발견한 오판 사례를 고정한다.

    uv run --no-project --with kiwipiepy --with pytest pytest tests -q
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills" / "ko-ste" / "scripts"))

import check  # noqa: E402
import kostelib as K  # noqa: E402


def a(s):
    r = K.analyze_sentence(s)
    assert r is not None, s
    return r


def test_aux_constructions_are_not_clauses():
    # '-고 있다', '-지 않다', '-게 되다'는 절 경계가 아니다
    assert a("설정 파일을 변경하고 있지 않다면 서버를 다시 시작할 수 있습니다.")["clauses"] == 2
    assert a("프롬프트를 활용한 결과가 완벽하지는 않아요.")["clauses"] == 1


def test_postpositional_verbs_are_not_clauses():
    assert a("cpplint는 아래와 같이 pip를 통해 설치할 수 있습니다.")["clauses"] == 1
    assert a("데이터는 정해진 데이터 스키마에 따라 테이블에 저장된다.")["clauses"] == 1


def test_real_connectives_are_counted():
    assert a("서버를 재시작하고 로그를 확인한 다음 캐시를 비우고 다시 배포하세요.")["clauses"] == 3


def test_noun_run_breaks_on_comma_and_time_nouns():
    assert a("코드 예제, 명령어, 설정 방법을 포함하세요.")["noun_run"] < 4
    assert a("글의 저자는 4년 동안, 기술적 스킬 향상을 위한 방법을 공유한다.")["noun_run"] < 4


def test_noun_run_counts_real_cluster():
    assert a("인증 토큰 갱신 실패 처리 로직을 수정했습니다.")["noun_run"] >= 5


def test_noun_run_ignores_latin_and_code():
    # 'Pod'가 든 어절은 세지 않고 사슬을 끊는다: 메모리 사용량 변화 추이를 = 4
    assert a("kubectl 명령으로 Pod 메모리 사용량 변화 추이를 먼저 확인합니다.")["noun_run"] == 4


def test_ui_chain_breaks_on_adverbial_noun():
    assert a("10분의 시청 시간 동안 React의 관점에서 역사를 볼 수 있다.")["ui"] == 1
    assert a("모든 프로세스의 메모리 참조의 계획을 미리 파악할 방법이 없다.")["ui"] == 2


def test_imperative_detection():
    assert a("지금 서버를 다시 시작하세요.")["mood"] == "imp"
    assert a("지금 서버가 다시 시작됩니다.")["mood"] == "decl"


def test_double_passive_pattern():
    assert "A.double_passive" in a("문제가 있는 것으로 보여집니다.")["hits"]
    assert "A.double_passive" not in a("문제가 있는 것으로 보입니다.")["hits"]


def test_compare_catches_lost_scope_hedge_code():
    orig = "`config.yaml`의 `timeout` 값을 30초 이상으로 설정한 경우에만 재시도가 동작할 수 있습니다."
    new = "`config.yaml`의 timeout 값을 30초로 설정하면 재시도가 동작합니다."
    out = "\n".join(check.compare(orig, new))
    assert "`timeout`" in out
    assert "MP-2" in out
    assert "MP-3" in out


def test_compare_clean_when_identical():
    s = "이 라이브러리는 브라우저와 Node.js에서 모두 동작합니다."
    assert check.compare(s, s)[0].startswith("보존 요소 차이 없음")
