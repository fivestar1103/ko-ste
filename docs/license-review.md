# 배포 라이선스 검토

검토일: 2026-10-08. 기준 커밋은 `35f1bad31d1e613575bb7c3965bc4874e66532d3`이며, 그 뒤의 README·커버 변경도 확인했다.

직접 작성한 기본 스킬과 도구는 MIT로 배포한다. 국립국어원 인용문, 외부 의존성, 과거 평가 자료까지 모두 MIT라고 볼 수는 없다. 아래는 배포 파일과 실제 고지를 대조한 기록이며, 개별 표현의 저작물성이나 모든 제3자 권리의 법적 판단을 대신하지 않는다.

## 확인 결과와 조치

| 대상 | 확인 결과 | 조치 |
|---|---|---|
| 기본 스킬의 MIT 참조 두 건 | 원 저장소의 고지와 `UPSTREAM-LICENSES.md`의 전문이 일치한다. | 저작권자와 MIT 전문을 설치 파일에 유지한다. |
| 기본 스킬의 국립국어원 예문 | `02-examples.md`가 모든 예문을 LLM 작성으로 설명하면서 외부 원문 한 문장을 포함했다. `01-rules.md`에도 해당 원문의 일부가 있었다. | 현재 기본 스킬의 해당 예문을 새로 작성했다. 원자료 설명은 쪽수와 사례 ID로 연결한다. |
| 국립국어원 연구 자료 | 원문의 보기·권장 표현을 별도 표에 옮겼으며 공공누리 제3유형을 표시했다. | 인용문을 MIT 허락에서 제외한다. 고지·원자료 링크를 파일 앞에 붙이고 인용문은 편집하지 않는다. |
| 과거 평가 자료 | 일부 입력·읽기 스냅샷·출력에 국립국어원 문구가 남아 있다. | 원출력은 바꾸지 않는다. 별도 고지로 출처와 재이용 제한을 표시한다. 기본 스킬의 최신 동작 예문으로 재배포하지 않는다. |
| 토스 가이드 | 고정 커밋의 README가 CC BY-NC-SA 4.0을 명시한다. | 원문·번역·수정 예문을 MIT 배포본에 넣지 않는다. 말뭉치 원문과 검토 표본은 Git에서 제외한다. |
| Kiwi 의존성 | 현재 설치하는 `kiwipiepy`·`kiwipiepy_model` 0.24.0은 Apache-2.0이다. 보정용 2022년 커밋의 고지는 LGPL-2.1-or-later로 다르다. | 버전과 용도를 나눠 고지한다. 패키지·모델·바이너리를 이 저장소에 동봉하지 않는다. |
| 커버 | imagegen으로 생성한 이미지다. 표지의 문구를 “한국어 기술 문서를 다듬는 스킬”로 수정했다. | 생성 사실과 프롬프트를 보존한다. 제공할 권한이 있는 범위에 MIT를 적용한다. 독점권·저작권 성립·비침해를 보장하지 않는다. |
| ASD-STE100 명칭 | 공식 FAQ는 일반 글에서 원칙을 활용할 수 있다고 설명하지만 도구의 인증·공인을 제공하지 않는다. | 공식 규격·사전·로고를 포함하지 않으며 공인·호환 인증을 주장하지 않는다. |

토스의 `docs/sentence/` 6개 파일과 현재 스킬 문서에서 공백을 제외한 35자 이상의 연속 일치 부분을 검색했으며 발견하지 못했다. 이 검사는 긴 복제를 찾는 보조 수단이다. 의역·번역·선택과 배열의 유사성까지 법적으로 판정하지 않는다.

## 국립국어원 인용과 과거 평가

[원자료 배포 페이지](https://www.korean.go.kr/front/etcData/etcDataView.do?mn_id=&etc_seq=700&pageIndex=1)와 [공공누리 제3유형 조건](https://www.kogl.or.kr/info/licenseType3.do)을 다시 확인했다. 출처를 표시해야 하며 상업적 이용은 가능하지만 원문 변경과 2차적 저작물 작성은 허용하지 않는다. 출처를 표시하는 것만으로 변경 허락이 생기지는 않는다.

`research/nikl-native-pairs.md`의 외부 인용은 그 조건을 따른다. 프로젝트 해설은 인용과 구분하며 국립국어원의 후원·공인을 뜻하지 않는다. 이번 검토는 PDF의 모든 전사 문구·문장부호·강조를 새로 대조한 검수가 아니다. 이 표를 독립적인 예문 상품이나 수정 가능한 데이터셋으로 배포하려면 원문 대조와 허락 범위를 먼저 확인해야 한다.

`evals/NOTICE.md`는 과거의 국립국어원 기반 입력과 스냅샷을 식별한다. 모델이 이를 고친 결과가 원문의 보호되는 표현을 변형한 2차적 저작물인지까지 판단하지 못했다. 따라서 과거 평가 전체를 상업적으로 재배포하거나 수정 가능한 MIT 예문 모음으로 이용해도 된다고 주장하지 않는다. 그 이용이 필요하면 권리자의 추가 허락이나 해당 자료의 개별 법률 검토가 필요하다. 이번 작업에서 과거 기록과 Git 이력을 소급 수정하지 않았다.

## 보정 말뭉치

원문은 `calibration/cache/`에 받으며 Git으로 배포하지 않는다. 공개하는 `measure.json`에는 집계만 있고 원문 문장은 없다. 숫자 집계를 공개한다는 사실이 원문·데이터베이스 전체를 재배포하거나 상업적으로 이용할 권리를 뜻하지는 않는다. CC의 [이용 조건](https://creativecommons.org/licenses/by-nc-sa/4.0/legalcode.en)에는 데이터베이스 권리도 포함된다.

고정 커밋별 증거 URL과 파일 해시는 [조회 기록](license-sources.json)에 있다. 아래는 해당 버전의 루트 고지 기준이다. 별도 출처가 있는 인용·모델·데이터까지 같은 허락이라고 단정하지 않는다.

| 자료 ID | 확인한 조건 | 확인 범위 |
|---|---|---|
| toss-tw | CC BY-NC-SA 4.0 | README의 License 절 |
| kiwipiepy | LGPL-2.1-or-later | 보정에 사용한 2022년 커밋의 LICENSE.txt |
| soynlp | LGPL-3.0 | LICENSE |
| khaiii | Apache-2.0 | LICENSE와 제3자 NOTICE.md |
| khaiii-wiki | 재이용 허락 미확인 | 서버의 고정 wiki 커밋에 LICENSE·NOTICE 파일이 없고 문서 검색에서도 위키 자체의 허락을 찾지 못함 |
| kcbert | MIT | LICENSE |
| koelectra | Apache-2.0 | LICENSE |
| kochat | Apache-2.0 | LICENSE |
| pykospacing | GPL-3.0 | LICENSE |
| kogpt2 | CC BY-NC-SA 4.0 | LICENSE |
| fe-news | 루트의 재이용 허락 미확인 | 루트 LICENSE가 없고 README에도 허락을 찾지 못함 |
| interview-beginner | MIT | LICENSE |
| tech-interview | MIT | LICENSE |
| frontend-fundamentals | MIT | LICENSE.md |

GitHub에 공개되어 있다는 이유만으로 일반적인 재이용 허락이 생기지는 않는다. GitHub가 설명하는 열람·fork 권한과 저작물의 재배포·변형 허락은 범위가 다르다. [GitHub 안내](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/licensing-a-repository)

위키의 고지가 확인되지 않은 점, FE 뉴스와 학습 노트에 외부 글이 섞일 수 있다는 점, 비상업 조건의 자료를 상업적 목적에 쓰는 경우는 추가 확인 대상이다. 기존 집계를 재현한 사실을 그 용도의 권리 확인으로 표시하지 않는다.

## 선택 Python 도구의 의존성

스킬 지침을 읽는 데 Python이나 Kiwi는 필요하지 않다. 대조기·개발 도구는 사용자의 환경에 패키지를 별도로 설치한다. `uv.lock`은 버전·다운로드 위치·해시를 기록하며 외부 소스나 모델을 포함하지 않는다.

| 패키지 | 확인한 버전 | 배포 메타데이터의 조건 |
|---|---|---|
| kiwipiepy, kiwipiepy_model | 0.24.0 | Apache-2.0 |
| NumPy | 2.5.3 | BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0 |
| tqdm | 4.70.1 | MPL-2.0 AND MIT |
| packaging | 26.3 | Apache-2.0 OR BSD-2-Clause |
| pytest | 8.3.5 | MIT |
| PyYAML | 6.0.2 | MIT |
| pluggy | 1.6.0 | MIT |
| iniconfig | 2.3.1 | MIT |

이는 macOS·Python 3.12에서 설치한 배포본의 메타데이터 확인이다. 다른 운영체제의 wheel, 패키지에 포함된 제3자 라이브러리, 새 버전은 각각의 LICENSE·NOTICE를 확인해야 한다. 향후 실행 파일이나 모델을 동봉하면 Apache·MPL 등 해당 배포본의 고지·소스 제공 조건도 다시 검토해야 한다. 현재 MIT 코드만 제공한다는 고지가 그 조건을 대체하지 않는다.

Kiwi 0.24.0의 [LICENSE.txt](https://github.com/bab2min/kiwipiepy/blob/v0.24.0/LICENSE.txt), [NOTICE](https://github.com/bab2min/kiwipiepy/blob/v0.24.0/NOTICE), [PyPI 메타데이터](https://pypi.org/project/kiwipiepy/0.24.0/)를 대조했다. NOTICE는 내부의 Eigen·simdjson 등에도 별도 조건이 있음을 설명한다.

## 디자인과 생성 이미지

jevgrep의 짧은 소개·설치·사용 구성과 큰 제목의 인상을 참고했다. 프로젝트의 코드·이미지·로고·문구·폰트 파일을 이 저장소로 복제하지 않았다. dashboard는 소유자가 요청한 색조·서체의 참고다. 사용한 imagegen 편집 입력은 이 프로젝트의 기존 생성 커버다.

[OpenAI 이용약관](https://openai.com/policies/terms-of-use/)의 Content 절은 법이 허용하는 범위에서 사용자에게 산출물에 대한 OpenAI의 권리를 이전하며, 결과가 고유하지 않을 수 있다고 명시한다. 이는 제3자의 권리를 이전하거나 비침해를 보장하는 조항이 아니다. MIT 표시는 프로젝트가 제공할 권한이 있는 부분의 허락이며, AI 결과 전체에 독점 저작권이 성립한다는 주장이 아니다.

## ASD-STE100

[공식 FAQ](https://www.asd-ste100.org/STE_faq.html)와 [소프트웨어 안내](https://asd-ste100.org/software.html)를 확인했다. 일반적인 글쓰기 원칙의 참고와 공식 규격·사전의 복제는 구분한다. 도구의 ASD 인증·승인, 로고·상표 사용 허락을 주장하지 않는다. MIT로 공개된 다른 스킬의 고지가 ASD가 소유한 원문의 재배포까지 허락하는 것은 아니다.

Issue 9 규격 원문은 이번에도 확보하지 않았으므로 규격 전문에 대한 적합성 검증을 했다고 말하지 않는다. ko-ste는 자체 한국어 편집 지침이며 공인된 한국어 STE 표준이 아니다.

[출처별 고지](../THIRD_PARTY.md) · [기여 조건](../CONTRIBUTING.md)

## 2026-10-08 후속 변경 (0.1.1)

위 검토는 국립국어원 인용을 설치 스킬 밖(`research/`)에 두는 구성을 기준으로 했다. 검수에서 두 가지가 확인되어 구성을 바꿨다.

- 설치 스킬이 사람이 고친 전후 쌍을 읽을 수 없었다. 선택 자료를 받는 경로(릴리스 첨부나 설치 안내)가 없었다.
- marketplace 항목의 `source`가 저장소 루트(`./`)여서, 플러그인 설치가 `research/`와 평가 원출력까지 복사했다. 실제로는 이미 인용이 함께 배포되고 있었다.

공공누리 제3유형은 출처표시와 변경금지를 지키면 상업적 이용을 포함한 재배포를 허용한다. 그래서 전후 쌍을 `skills/ko-ste/references/04-native-pairs.md`로 옮기고, 인용 고지를 `skills/ko-ste/NIKL-NOTICE.md`로 옮겨 설치 파일에 함께 넣었다. 인용 표 75행은 옮기기 전과 글자 단위로 같다. 파일 머리와 `NOTICE.md`에 인용이 MIT가 아님을 적었다.

marketplace 항목의 `source`를 `./skills/ko-ste`로 좁혔다. 플러그인 설치는 이제 스킬 폴더만 복사한다. 과거 평가 자료(`evals/`)는 저장소에만 남는다.
