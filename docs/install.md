# 설치와 갱신

ko-ste는 GitHub에서 배포한다. 실행 지침은 `skills/ko-ste/`에 있고, 연구 도구와 원문 인용 자료는 별도로 보존한다.

## skills CLI

Node.js 22.20 이상과 npm/npx가 있는 환경에서 실행한다.

```sh
npx skills add fivestar1103/ko-ste --skill ko-ste
```

사용자 전체 범위를 직접 지정할 수도 있다.

```sh
# Claude Code
npx skills add fivestar1103/ko-ste --skill ko-ste --agent claude-code --global

# Codex
npx skills add fivestar1103/ko-ste --skill ko-ste --agent codex --global
```

`--global`을 빼면 현재 프로젝트에 설치한다. 설치 도구는 [공식 skills CLI](https://github.com/vercel-labs/skills)를 사용한다. npm의 `skills`가 GitHub 스킬을 설치하며, 별도 `ko-ste` npm 패키지를 발행하는 방식은 아니다.

기존 파일을 직접 수정했다면 갱신 전에 보관한다. 최신 스킬은 같은 설치 명령을 다시 실행해 설치한다. 설치 후 새 에이전트 세션에서 사용한다.

## Claude Code marketplace

Claude Code 안에서 실행한다.

```text
/plugin marketplace add fivestar1103/ko-ste
/plugin install ko-ste@ko-ste
```

호출 이름은 `/ko-ste:ko-ste`다. [Claude Code 공식 안내](https://code.claude.com/docs/en/plugin-marketplaces)의 GitHub marketplace 방식을 따른다. 직접 스킬 설치와 marketplace 설치 중 하나를 선택한다.

CLI에서 관리할 때는 다음 명령을 쓴다.

```sh
claude plugin marketplace update ko-ste
claude plugin update ko-ste@ko-ste
```

저장소는 portable `plugin.json`과 `.claude-plugin/`, `.codex-plugin/` 호환 manifest를 제공한다. 이 GitHub marketplace 제공과 각 서비스의 중앙 디렉터리 심사·등록은 별도다.

## 선택 대조기

지침을 쓰는 데 Python은 필요 없다. `check.py`를 실행할 때는 Python 3.11 이상과 Kiwi 0.24.0이 필요하다. `uv`가 준비된 저장소에서 실행하는 예시는 다음과 같다.

```sh
uv run --no-project --with kiwipiepy==0.24.0 skills/ko-ste/scripts/check.py draft.md --mode 80
uv run --no-project --with kiwipiepy==0.24.0 skills/ko-ste/scripts/check.py --compare original.md edited.md
```

설치된 스킬에서도 경로를 그 스킬의 `scripts/check.py`로 바꾸면 실행할 수 있다. 대조기는 표지의 차이를 찾을 뿐 사실과 조건의 의미를 완전히 판정하지 못한다.

## 원문 예문

국립국어원의 전후 쌍은 [별도 연구 자료](../research/nikl-native-pairs.md)에서 확인한다. 인용문은 변경 금지 조건이 있어 MIT 실행 스킬에 복제하지 않는다. 스킬의 `references/04-native-pairs.md`는 쪽수·관련 규칙·채택과 제외 이유·원자료 위치를 제공한다.

[README로 돌아가기](../README.md)
