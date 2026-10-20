# 전후 쌍 자료의 출처와 이용 조건

`data/pairs.jsonl`과 `data/pairs-cc-by-sa.jsonl`의 `before`·`after`는 아래 공개 저장소의 Git 이력에서
발췌한 문장이다. 이 문장들은 ko-ste의 MIT 조건이 아니라 각 출처의 조건을 따른다.

- 발췌 방식: 사람이 고친 커밋에서 고치기 전 문장과 고친 뒤 문장을 문장 단위로 뽑았다. 마크다운·HTML 표시와
  숏코드를 지웠고 문장 자체는 고치지 않았다. 각 행의 `commit`과 `path`가 원래 위치다.
- 기간: 작성일과 커밋일이 모두 2022-10-31 이전인 커밋만 썼다. ChatGPT 공개(2022-11-30) 전에 쓴 글만 모으려는 것이다.
- `rules`, `purpose`, `label_note`는 ko-ste가 붙인 분류다(Claude 판정, 사람 검수 전). 출처 저장소의 견해가 아니다.
- CC BY-SA 출처의 문장은 `data/pairs-cc-by-sa.jsonl`에만 있다. 이 파일을 고쳐 배포하면 같은 조건(CC BY-SA)을 따라야 한다.
- 출처 저장소의 라이선스 파일 사본은 `data/licenses/`에 있다.

| 출처 | 저장소 | 고정 커밋 | 이용 조건 | 저작자 표시 | 쌍 |
|---|---|---|---|---|---|
| k8s | [kubernetes/website](https://github.com/kubernetes/website) | `079a4d63f0` | [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/), [사본](data/licenses/k8s-LICENSE.txt) | The Kubernetes Authors | 70 |
| tf-l10n | [tensorflow/docs-l10n](https://github.com/tensorflow/docs-l10n) | `7cb584af65` | Apache-2.0, [사본](data/licenses/tf-l10n-LICENSE.txt) | The TensorFlow Authors | 3 |
| vue2-kr | [vuejs-kr/kr.vuejs.org](https://github.com/vuejs-kr/kr.vuejs.org) | `83f83fff15` | MIT, [사본](data/licenses/vue2-kr-LICENSE.txt) | Yuxi Evan You, Vue.js 한국 사용자 모임 | 13 |
| ts-kr | [typescript-kr/typescript-kr.github.io](https://github.com/typescript-kr/typescript-kr.github.io) | `3fad5f8dab` | MIT, [사본](data/licenses/ts-kr-LICENSE.txt) | typescript-kr 기여자 | 2 |
| nodejs-org | [nodejs/nodejs.org](https://github.com/nodejs/nodejs.org) | `79b82efc20` | MIT, [사본](data/licenses/nodejs-org-LICENSE.txt) | Node.js Website WG contributors | 4 |
