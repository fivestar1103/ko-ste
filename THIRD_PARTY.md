# 자료 출처와 이용 조건

직접 작성한 규칙·설명·예문·Python·CI 코드는 MIT로 제공한다. 외부 인용문과 의존성에는 각 자료의 조건이 적용된다. 저장소 전체가 같은 조건의 MIT 자료는 아니다. 설치되는 스킬(`skills/ko-ste/`)에는 국립국어원 전후 쌍 인용이 들어 있으며, 그 인용은 MIT가 아니라 공공누리 제3유형을 따른다. 보정 말뭉치 원문은 어디에도 동봉하지 않는다.

| 자료 | 이용 조건과 사용 범위 |
|---|---|
| 국립국어원 「쉬운 공문서 쓰기 길잡이」(2022, 발간등록번호 11-1371028-000915-01) | [배포 페이지](https://www.korean.go.kr/front/etcData/etcDataView.do?mn_id=&etc_seq=700&pageIndex=1), [공공누리 제3유형](https://www.kogl.or.kr/info/licenseType3.do): 출처표시·변경금지, 상업적 이용 가능. `skills/ko-ste/references/04-native-pairs.md`의 보기·권장 표현은 원문 인용이며 쪽수를 붙였다. 인용문은 변경하지 않고 프로젝트 해설과 구분한다. 고지는 [`skills/ko-ste/NIKL-NOTICE.md`](skills/ko-ste/NIKL-NOTICE.md)에 있으며 설치 파일에 함께 들어간다. |
| Viva Republica, toss/technical-writing | [원 저장소](https://github.com/toss/technical-writing), 커밋 `68ba335cbe35c877775f092e98177b60da5f3d95`, CC BY-NC-SA 4.0. 일반적인 편집 원칙과 대조하고 말뭉치를 집계했다. 원문 설명·예문·번역은 배포 스킬에 포함하지 않는다. 원문은 제외된 `calibration/cache/`에만 받으며 원래 조건을 따른다. |
| danyuchn/asd-ste100-skill | [원 저장소](https://github.com/danyuchn/asd-ste100-skill), 커밋 `32511c6`, MIT. 두 모드, 의미 보존, 출력 설계를 참고했다. 영어 규칙을 번역하거나 공식 사전을 복제하지 않았다. Copyright (c) 2026 Dustin Yuchen Teng. 전문은 `skills/ko-ste/UPSTREAM-LICENSES.md`에 보존했다. |
| beamonic/no-ai-slop-ko | [원 저장소](https://github.com/beamonic/no-ai-slop-ko), 커밋 `e9e3371`, MIT. 주장·문체 보존과 표현 검토에 참고했다. Copyright (c) 2026 Peter Yang; Copyright (c) 2026 Beamonic. 전문은 `skills/ko-ste/UPSTREAM-LICENSES.md`에 보존했다. |
| ASD-STE100 / ASD STEMG | [공식 사이트](https://www.asd-ste100.org/). 공개 설명의 목적과 범주를 참고했다. Issue 9 규격 원문을 확보·검증하지 않았고 공식 규칙·승인 사전 전체를 포함하지 않는다. 제휴나 공인을 뜻하지 않는다. |
| 국립국어원 사전 3종 | 표준국어대사전, 우리말샘, 한국어기초사전의 검색 건수만 기록했다. 용례 본문은 복제하지 않았다. 사전별 집계 단위가 다르고 활용형 검색이 중복될 수 있다. |
| 공개 개발 문서 14개 자료(13개 저장소와 위키) | `calibration/corpus-manifest.json`에 URL, `calibration/data/corpus-lock.json`에 커밋을 기록했다. 원문과 검토 표본은 Git에서 제외했다. 고정 커밋의 고지는 [검토 기록](docs/license-review.md)에 있다. FE 뉴스·khaiii 위키의 재이용 조건은 확인이 더 필요하다. 집계 공개가 원문 재배포·변형·상업적 이용 허락을 뜻하지 않는다. |
| 선택 Python 의존성 | `kiwipiepy`·`kiwipiepy_model` 0.24.0은 Apache-2.0이다. 패키지·모델·바이너리를 동봉하지 않고 사용자 환경에 별도로 설치한다. Kiwi의 [LICENSE.txt](https://github.com/bab2min/kiwipiepy/blob/v0.24.0/LICENSE.txt)·[NOTICE](https://github.com/bab2min/kiwipiepy/blob/v0.24.0/NOTICE), 다른 의존성의 조건도 각각 적용된다. 보정에 사용한 Kiwi의 2022년 커밋은 별도 LGPL 고지다. |
| 과거 평가 자료 | `evals/`에는 국립국어원 문구를 사용한 과거 입력·스냅샷·모델 출력이 있다. 원출력은 보존하며 모두 MIT로 재허락하지 않는다. [평가 자료 고지](evals/NOTICE.md)와 [확인하지 못한 이용 범위](docs/license-review.md)를 함께 따른다. |

초안의 조회일과 읽은 범위는 [보정 문서](skills/ko-ste/references/03-calibration.md)에 기록했다. 2026-10-08에는 국립국어원·공공누리 고지, 고정 GitHub 커밋의 이용 조건, 설치하는 Kiwi 0.24.0을 다시 확인했다. ASD의 FAQ와 소프트웨어 안내도 확인했으나 Issue 9 규격 원문은 확보하지 않았다. [증거 URL·해시](docs/license-sources.json)와 [검토 결과](docs/license-review.md)를 보존한다.

커버는 imagegen으로 생성했다. 프로젝트가 제공할 권한이 있는 범위에 MIT를 적용하며 이미지 전체의 독점권·저작권 성립·비침해를 보장하지 않는다. 폰트 소프트웨어는 포함하지 않는다. 참고한 디자인과 생성 프롬프트는 [assets/README.md](assets/README.md)에 있다.
