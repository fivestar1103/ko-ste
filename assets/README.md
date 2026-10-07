# 공개 그래픽

`cover`는 프로젝트 소개, `workflow`는 의미 보존 → 필요한 수정 → 원문 대조의 작업 순서를 보여 준다. 기본 파일은 밝은 테마이며 `-dark`, `-mobile` 변형을 함께 제공한다. README는 화면 크기와 테마에 맞게 이미지를 고른다.

SVG가 편집 원본이고 PNG가 GitHub에서 쓰는 렌더링이다. 도형·문구·배치는 이 프로젝트에서 직접 작성했으며 MIT로 제공한다. 실제 성능을 측정하지 않은 수치나 보장은 그래픽에 넣지 않았다.

디자인은 소유자의 dashboard 공통 토큰을 참고했다. IBM Plex Sans KR·IBM Plex Mono, 회색 paper, ink, slate, 얇은 규칙선과 고정폭 구역 제목을 쓴다. `dzhng/jevgrep`는 커버 → 짧은 설명 → 설치 → 사용 → 검증의 정보 배치만 참고했다. 그 프로젝트의 이미지나 문구를 복제하지 않았다.

이미지는 `scripts/render_artwork.cjs`로 렌더링한다. Playwright 1.62.1과 Chromium, IBM Plex 웹 폰트 CSS·파일이 필요하다. 폰트 파일은 저장소에 재배포하지 않는다.

```bash
npm install --no-save --package-lock=false playwright@1.62.1
npx playwright install chromium
node scripts/render_artwork.cjs /path/to/plex-fonts.css /path/to/fonts
```

IBM Plex의 폰트 라이선스는 [원 프로젝트](https://github.com/IBM/plex/blob/master/LICENSE.txt)의 SIL Open Font License 1.1을 따른다. 문서용 렌더링에 사용했으며 폰트 소프트웨어를 MIT로 재허락하지 않는다.
