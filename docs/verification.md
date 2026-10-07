# 검증과 재현

자동 검사와 실제 모델의 의미 판단을 구분한다. 오류·빈 출력·잘못된 판정 JSON·미판정은 통과나 실패율의 분모에 넣지 않는다. 원출력은 판정 후 바꾸지 않는다.

## 수행한 검증

| 검사 | 확인 범위 |
|---|---|
| pytest | 오류·미판정 집계, 출력 추출, 코드·경로·표지 대조, 측정 함수의 회귀 사례 |
| 형식·출처 검사 | Python 구문, 스킬 참조, plugin 버전 일치, 말뭉치 lock |
| 설치 | skills CLI 1.7.1로 Claude Code·Codex에 실제 복사 설치 |
| marketplace | Claude Code 2.1.292의 공식 `plugin validate`로 manifest 검사 |
| 측정 재현 | 고정 말뭉치와 Kiwi 0.24.0으로 기존 집계 JSON과 일치 |
| 동작 | 개발 사례, 별도 Codex 입력과 독립 판정. 실패와 불확실한 판정을 모두 보존 |

CI는 모델을 호출하지 않는다. 공개 소스의 고정 커밋을 받아 설치·자동 검사·말뭉치 집계를 다시 확인한다.

## 로컬 검사

```sh
uv sync --locked
uv run python -m pytest -q
uv run python scripts/validate_artifacts.py
uv run python calibration/scripts/report.py --check
claude plugin validate .
```

## 말뭉치 측정

```sh
uv run python calibration/scripts/fetch_corpus.py
uv run python calibration/scripts/measure.py
```

기본 fetch는 `calibration/data/corpus-lock.json`의 커밋을 따른다. 새 커밋을 선택하는 `--refresh-lock`은 별도 판단이다. 원문 말뭉치는 `calibration/cache/`에만 두며 Git으로 배포하지 않는다.

## 모델 동작 시험

Claude Code 인증과 충분한 사용량이 필요하다.

```sh
uv run python evals/run_evals.py --iteration 3 --tag opus --model claude-opus-5-5 --runs 2
uv run python evals/judge.py --iteration 3 --tag opus
uv run python calibration/scripts/report.py --write
```

기존 Claude 실행은 스킬 해시를 기록하지 않았고 그 사례를 개발에 사용했다. 현재 버전의 성과나 독립 최종 측정으로 인용하지 않는다. 2회차 의미 판정은 사용 한도로 미완료다.

Codex 후속 시험은 작은 별도 표본이며 사람이 만든 정답과 대조한 시험이 아니다. 모델 이름이 노출되지 않은 실행은 미상으로 기록했다. 사람 독자의 이해도·과업 수행 실험은 하지 않았다.

[보정 방법과 수치](../skills/ko-ste/references/03-calibration.md) · [첫 후속 시험](../evals/forward-2026-10-07/README.md) · [배포 구조 시험](../evals/distribution-2026-10-07/README.md)

[README로 돌아가기](../README.md)
