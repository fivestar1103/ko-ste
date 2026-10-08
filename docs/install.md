# 설치와 업데이트

## skills CLI

Node.js 22.20 이상이 필요합니다. 사용할 프로젝트에서 실행하세요.

```sh
npx skills add fivestar1103/ko-ste --skill ko-ste
```

실행 중에 에이전트와 설치 범위를 선택합니다. [skills CLI](https://github.com/vercel-labs/skills)는 스킬을 GitHub에서 가져옵니다.

모든 프로젝트에서 사용하려면 `--global`을 붙이세요.

```sh
# Claude Code
npx skills add fivestar1103/ko-ste --skill ko-ste --agent claude-code --global

# Codex
npx skills add fivestar1103/ko-ste --skill ko-ste --agent codex --global
```

설치한 파일을 직접 수정했다면 먼저 복사해 두세요. 업데이트하려면 설치 명령을 다시 실행하세요. 설치와 업데이트 후에는 새 에이전트 세션에서 사용하세요.

## Claude Code marketplace

Claude Code 안에서 실행하세요. skills CLI와 marketplace 중 하나로 설치하면 됩니다.

```text
/plugin marketplace add fivestar1103/ko-ste
/plugin install ko-ste@ko-ste
```

설치한 뒤 `/ko-ste:ko-ste`로 호출하세요. GitHub marketplace 설치 방식은 [Claude Code 공식 문서](https://code.claude.com/docs/en/plugin-marketplaces)에 있습니다.

플러그인으로 설치되는 것은 `skills/ko-ste` 폴더뿐입니다. 평가 기록, 말뭉치 집계, 커버 이미지는 설치되지 않습니다.

marketplace를 추가할 때는 저장소 전체를 내려받습니다. Windows에서 `Filename too long` 오류로 추가가 실패하면, 필요한 폴더만 내려받도록 터미널에서 추가하세요.

```sh
claude plugin marketplace add fivestar1103/ko-ste --sparse .claude-plugin skills
```

업데이트는 터미널에서 실행하세요.

```sh
claude plugin marketplace update ko-ste
claude plugin update ko-ste@ko-ste
```

## 문장 대조기

스킬과 별도로 사용할 수 있는 Python 도구입니다. 코드·경로·수치와 표현의 차이를 찾아 원문 대조를 돕습니다. 의미가 보존됐는지는 문맥에서 확인해야 합니다.

Python 3.11 이상과 Kiwi 0.24.0이 필요합니다. `uv`가 설치되어 있다면 저장소에서 실행하세요.

```sh
uv run --no-project --with kiwipiepy==0.24.0 skills/ko-ste/scripts/check.py draft.md --mode 80
uv run --no-project --with kiwipiepy==0.24.0 skills/ko-ste/scripts/check.py --compare original.md edited.md
```

[README](../README.md)
