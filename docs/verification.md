# 검증과 재현

자동 검사와 실제 모델의 의미 판단을 구분한다. 오류·빈 출력·잘못된 판정 JSON·미판정은 통과나 실패율의 분모에 넣지 않는다. 원출력은 판정 후 바꾸지 않는다.

## 수행한 검증

| 검사 | 확인 범위 |
|---|---|
| pytest | 오류·미판정 집계, 출력 추출, 코드·경로·표지 대조, 측정 함수의 회귀 사례 |
| 형식·출처 검사 | Python 구문, 스킬 참조, plugin 버전 일치, 말뭉치 lock |
| 설치 | 공개 GitHub 저장소를 skills CLI 1.7.1로 받아 Claude Code·Codex에 실제 복사 설치 |
| marketplace | Claude Code 2.1.292로 manifest 검사 후 공개 GitHub marketplace 추가·플러그인 설치 |
| 측정 재현 | 고정 말뭉치와 Kiwi 0.24.0으로 기존 집계 JSON과 일치 |
| 동작 | 개발 사례, 별도 Codex 입력과 독립 판정. 실패와 불확실한 판정을 모두 보존 |

CI는 모델을 호출하지 않는다. 공개 소스의 고정 커밋을 받아 설치·자동 검사·말뭉치 집계를 다시 확인한다.

2026-10-07에 공개 커밋 [`62b0023`](https://github.com/fivestar1103/ko-ste/commit/62b0023adea9c02c827e7d1fed8a80ac32d4c11d)의 설치를 별도 테스트 디렉터리에서 확인했다. skills CLI와 marketplace로 설치한 `SKILL.md`의 SHA-256이 원본과 같았다. [Linux CI](https://github.com/fivestar1103/ko-ste/actions/runs/37639856405)에서는 31개 테스트와 고정 집계의 전체 값 대조를 통과했다.

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

표본 추출 전에 파일 경로의 각 부분을 소문자로 정렬한다. 운영체제의 기본 경로 정렬에 맡기면 같은 seed에서도 다른 표본이 뽑힐 수 있다. 빈 표본의 백분위는 JSON `null`로 기록하며, 집계 대조는 허용 오차 없이 모든 값을 비교한다.

## 모델 동작 시험

Claude Code 인증과 충분한 사용량이 필요하다.

```sh
uv run python evals/run_evals.py --iteration 3 --tag opus --model claude-opus-5-5 --runs 2
uv run python evals/judge.py --iteration 3 --tag opus
uv run python calibration/scripts/report.py --write
```

1·2회차 Claude 실행은 스킬 해시를 기록하지 않았고 그 사례를 개발에 사용했다. 현재 버전의 성과로 인용하지 않는다. 2회차 의미 판정은 사용 한도로 미완료다.

3회차(0.1.1)는 스킬 해시를 기록했다. 개발 사례와 새 사례를 나눠 집계했다. 결과는 아래 '0.1.1 검증' 절과 [보정 문서 7절](../skills/ko-ste/references/03-calibration.md)에 있다.

Codex 후속 시험은 작은 별도 표본이며 사람이 만든 정답과 대조한 시험이 아니다. 모델 이름이 노출되지 않은 실행은 미상으로 기록했다. 사람 독자의 이해도·과업 수행 실험은 하지 않았다.

[보정 방법과 수치](../skills/ko-ste/references/03-calibration.md) · [첫 후속 시험](../evals/forward-2026-10-07/README.md) · [배포 구조 시험](../evals/distribution-2026-10-07/README.md)

## 2026-10-08 문서와 배포 검토

README 설명에는 80% 모드, 설치 안내에는 엄격 모드를 적용했다. 설치 명령·버전·재시도 상한은 원문과 대조했다. 표지는 기존 구성을 유지하며 “한국어 기술 문서를 다듬는 스킬”로 수정했다.

기본 스킬의 외부 원문 예문 일부를 직접 작성한 예문으로 교체했으며, 기존 모델의 원출력·판정·읽기 스냅샷은 바꾸지 않았다. 이는 새 모델 성능 시험이 아니다. [라이선스 검토](license-review.md)에는 확인한 조건과 미확인 범위를 따로 적었다.

macOS·Python 3.12.12에서 고정 의존성으로 31개 테스트, 형식·고지·말뭉치와 출처 lock 검사, 집계 기록 대조, 스킬 형식 검사를 통과했다. 공개 문서의 상대 링크도 확인했다. skills CLI 1.7.1로 격리된 프로젝트에 Codex·Claude Code 설치를 실행한 뒤 모든 스킬 파일과 LICENSE·NOTICE가 원본과 일치하는지 대조했다. Python 의존성·모델 파일·국립국어원 전후 쌍은 설치한 스킬에 없었다.

[README로 돌아가기](../README.md)

## 0.1.1 검증 (2026-10-08)

Windows 11, Claude Code 2.1.292, Python 3.12, uv 0.10.0에서 확인했다.

자동 검사:
- pytest 32개 통과. 판정 항목이 객체로 와도 실패로 남는지 확인하는 회귀 시험 1개를 더했다.
- `validate_artifacts.py` 통과. marketplace 원본이 `./skills/ko-ste`인지, 설치 스킬에 전후 쌍 75행과 고지가 있는지도 검사한다.
- `report.py --check` 일치. `claude plugin validate .` 통과.

설치:
- 브랜치를 GitHub에 올리고 격리한 설정 폴더(`CLAUDE_CONFIG_DIR`)에서 marketplace 추가와 설치를 실행했다.
- 플러그인 캐시에는 스킬 폴더의 파일 11개(188KB)만 들어갔다. 0.1.0에서는 저장소 전체(파일 703개, 4MB)가 들어갔다.
- `claude plugin details`에서 스킬 1개로 인식됐다.
- 경로가 긴 설정 폴더에서는 전체 복제가 `Filename too long`으로 실패했다. `--sparse .claude-plugin skills`로는 같은 위치에서 추가와 설치에 성공했다.

모델 동작(블라인드 의미 판정, 판정 모델 `claude-opus-5-5`, 미판정 0):

| 구분 | 스킬 있음 실패 | 스킬 없음 실패 |
|---|---|---|
| 개발 사례 1–17번 (Opus 2회, Sonnet 1회) | 5/48 | 37/48 |
| 새 사례 18–21번 (Opus 2회, Sonnet 1회) | 1/12 | 7/12 |
| 최종 판 확인 (Opus 2회; 2·9·12·19번) | 1/8 | 8/8 |

- 처음 두 줄은 스킬 해시 `e89d06a2…` 판, 마지막 줄은 `ab4aa1f1…` 판이다.
- 스킬 있음 실패 중 3건은 번역에서 'should'의 강도를 고른 것이다. 판정 기준('해석을 고르면 실패')이 번역 과제에 맞지 않는 한계로 본다.
- 실제 실패는 다음과 같다.
  - 사실 삭제 1건: MP-2를 고친 뒤 재발하지 않았다.
  - 조건 범위 1건: 2번 사례, `ab4aa1f1` 판에서 2회 중 1회 발생했다.
- 생성 모델과 판정 모델이 모두 Claude다. 사람이 만든 정답과 대조하지 않았다. 의미 보존만 쟀고 읽기 개선 정도는 재지 않았다.

판정기 결함:
- 판정 모델이 실패 항목을 객체로 돌려주면 스키마 오류로 버려졌다. 그 결과 실패를 찾은 판정만 미판정으로 빠졌다.
- 이 결함은 3회차에서 찾아 고쳤다. 위 수치는 고친 판정기로 계산했다.
