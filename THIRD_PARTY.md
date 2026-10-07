# 자료 출처와 이용 조건

직접 작성한 규칙·설명·예문·Python·CI 코드는 MIT로 제공한다. 설치되는 기본 스킬에는 변경·상업적 이용을 제한하는 외부 원문을 넣지 않는다. 외부 자료의 허락을 MIT로 바꾸지는 않는다.

| 자료 | 이용 조건과 사용 범위 |
|---|---|
| 국립국어원 「쉬운 공문서 쓰기 길잡이」(2022, 발간등록번호 11-1371028-000915-01) | [배포 페이지](https://www.korean.go.kr/front/etcData/etcDataView.do?mn_id=&etc_seq=700&pageIndex=1), [공공누리 제3유형](https://www.kogl.or.kr/info/licenseType3.do): 출처표시·변경금지, 상업적 이용 가능. `research/nikl-native-pairs.md`의 보기·권장 표현은 원문 인용이며 쪽수를 붙였다. 프로젝트 해설과 구분한다. 실행 스킬에는 인용문 대신 원자료 위치와 검토 메모를 제공한다. |
| Viva Republica, toss/technical-writing | [원 저장소](https://github.com/toss/technical-writing), 커밋 `68ba335cbe35c877775f092e98177b60da5f3d95`, CC BY-NC-SA 4.0. 일반적인 편집 원칙과 대조하고 말뭉치를 집계했다. 원문 설명·예문·번역은 배포 스킬에 포함하지 않는다. 원문은 제외된 `calibration/cache/`에만 받으며 원래 조건을 따른다. |
| danyuchn/asd-ste100-skill | [원 저장소](https://github.com/danyuchn/asd-ste100-skill), 커밋 `32511c6`, MIT. 두 모드, 의미 보존, 출력 설계를 참고했다. 영어 규칙을 번역하거나 공식 사전을 복제하지 않았다. Copyright (c) 2026 Dustin Yuchen Teng. 전문은 `skills/ko-ste/UPSTREAM-LICENSES.md`에 보존했다. |
| beamonic/no-ai-slop-ko | [원 저장소](https://github.com/beamonic/no-ai-slop-ko), 커밋 `e9e3371`, MIT. 주장·문체 보존과 표현 검토에 참고했다. Copyright (c) 2026 Peter Yang; Copyright (c) 2026 Beamonic. 전문은 `skills/ko-ste/UPSTREAM-LICENSES.md`에 보존했다. |
| ASD-STE100 / ASD STEMG | [공식 사이트](https://www.asd-ste100.org/). 공개 설명의 목적과 범주를 참고했다. Issue 9 규격 원문을 확보·검증하지 않았고 공식 규칙·승인 사전 전체를 포함하지 않는다. 제휴나 공인을 뜻하지 않는다. |
| 국립국어원 사전 3종 | 표준국어대사전, 우리말샘, 한국어기초사전의 검색 건수만 기록했다. 용례 본문은 복제하지 않았다. 사전별 집계 단위가 다르고 활용형 검색이 중복될 수 있다. |
| 공개 개발 문서 13개 저장소 | `calibration/corpus-manifest.json`에 URL, `calibration/data/corpus-lock.json`에 커밋을 기록했다. 원문은 Git에서 제외했다. 각 저장소의 라이선스는 원 저장소에서 확인한다. 집계가 원문 재배포 허락을 뜻하지 않는다. |

조회일: 2026-10-07. 읽은 범위와 확보하지 못한 자료는 [보정 문서](skills/ko-ste/references/03-calibration.md)에 기록했다. 초안 조사는 Claude가 수행했고 후속 작업에서 국립국어원 고지와 토스·MIT 참조 저장소의 라이선스를 확인했다. STE 사이트는 후속 접속에서 403을 반환했다. 이전 확인 기록을 새 검증으로 주장하지 않는다.

공개 그래픽은 직접 작성한 SVG와 그 렌더링이며 MIT로 제공한다. IBM Plex Sans KR·IBM Plex Mono를 렌더링에 사용했다. 폰트 소프트웨어는 저장소에 포함하지 않았고, IBM Plex의 [SIL Open Font License 1.1](https://github.com/IBM/plex/blob/master/LICENSE.txt)을 따른다. 디자인·생성 기록은 [assets/README.md](assets/README.md)에 있다.
