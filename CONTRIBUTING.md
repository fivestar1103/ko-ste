# 기여하기

문장이 더 짧아졌다는 이유만으로 개선이라고 판단하지 않는다. 원문의 사실·조건·예외·수치·확신·의무와 문체가 유지되어야 한다. 이미 잘 읽히는 문장은 그대로 둔다.

규칙 수정에는 문제가 되는 입력, 현재 출력, 원하는 동작과 관련 규칙 ID를 함께 적는다. 본인이 직접 고친 전후 쌍은 LLM 예문과 구분한다. 회사 자료와 개인 정보는 올리지 않는다. 예문을 제공할 때는 본인이 작성했거나 MIT로 제공할 권한이 있는 문장을 쓴다.

```bash
uv sync --locked
uv run python -m pytest -q
uv run python scripts/validate_artifacts.py
uv run python calibration/scripts/report.py --check
```

의미 보존이나 모호성 처리의 동작을 바꾸면 해당 실패를 재현하는 사례로 확인한다. 자동 검사 통과와 사람의 의미 판단은 별도로 기록한다. 모델 호출에는 인증과 사용량이 필요하며 CI의 필수 검사는 모델을 호출하지 않는다.

말뭉치 측정은 `calibration/scripts/fetch_corpus.py`와 `calibration/scripts/measure.py`로 재현한다. 새 스킬 버전의 성과를 주장하려면 스킬 해시, 모델 식별자, 입력, 원출력과 미판정 수를 기록한다. 수정에 사용한 사례의 성적을 독립적인 최종 성능으로 쓰지 않는다.

기여한 코드와 직접 작성한 문서는 저장소의 MIT 조건으로 제공한다. `skills/ko-ste/references/04-native-pairs.md`의 국립국어원 원문 인용은 공공누리 제3유형을 따른다. 인용문은 원자료와 대조할 때만 정정하고, 프로젝트의 해설과 구분한다.

배포 원본은 GitHub다. `skills/ko-ste`는 `npx skills add`가 읽는 독립적인 스킬이며, `.claude-plugin/marketplace.json`은 Claude Code의 설치 진입점이며 같은 `skills/ko-ste` 폴더만 플러그인으로 설치한다. 버전을 올릴 때 `pyproject.toml`, 세 plugin manifest, marketplace 항목의 버전을 함께 바꾼다. 중앙 marketplace 등록이나 npm 레지스트리 발행은 이 저장소의 GitHub 배포와 별도다.
