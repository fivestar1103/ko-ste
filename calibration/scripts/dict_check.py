"""국립국어원 사전 3종에서 동사 조합의 용례 수를 센다.

영어 have/make/pay를 직역한 조합('결정을 만들다')과 자연스러운 짝('결정을 내리다')을
비교한다. 사전 웹 검색 화면을 그대로 조회하므로 응답 형식이 바뀌면 고쳐야 한다.

- 우리말샘(opendict): 용례 탭의 '용례 N' = 구절을 포함한 용례 문장 수
- 한국어기초사전(krdict): '용례 N' = 구절을 포함한 용례 문장 수
- 표준국어대사전(stdict): 자세히 찾기, 검색 대상 '용례' = 그 구절이 용례에 든 표제어 수
  (문장 수가 아니라 표제어 수다. 다른 두 사전과 직접 더하지 않는다.)

검색은 부분 문자열 일치다. '내렸다'는 '내리'를 포함하지 않으므로 활용형 줄기를 여럿 준다.

사용:
    uv run --no-project calibration/scripts/dict_check.py --out calibration/data/dict-collocations.json
"""

from __future__ import annotations

import argparse
import html
import http.cookiejar
import json
import re
import time
import sys
import urllib.parse
import urllib.request

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/130 Safari/537.36"

# (영어, 직역 조합 줄기들, 자연스러운 조합 줄기들)
PAIRS = [
    ("make a decision", ["결정을 만들", "결정을 만든", "결정을 만드"], ["결정을 내리", "결정을 내린", "결정을 내렸", "결정을 내려"]),
    ("pay attention", ["주의를 지불"], ["주의를 기울", "주의를 기울"]),
    ("pay attention (관심)", ["관심을 지불"], ["관심을 기울"]),
    ("make a mistake", ["실수를 만들", "실수를 만든", "실수를 만드"], ["실수를 저지르", "실수를 저질", "실수를 하", "실수를 한", "실수를 했", "실수를 해"]),
    ("make an effort", ["노력을 만들", "노력을 만든", "노력을 만드"], ["노력을 기울"]),
    ("reach/make a conclusion", ["결론을 만들", "결론을 만든", "결론을 만드"], ["결론을 내리", "결론을 내린", "결론을 내렸", "결론을 내려"]),
    ("have an effect", ["영향을 가지", "영향을 가진", "영향을 가졌", "영향을 갖"], ["영향을 미치", "영향을 미친", "영향을 미쳤", "영향을 주", "영향을 준", "영향을 줬", "영향을 끼치", "영향을 끼친", "영향을 끼쳤"]),
    ("have a meaning", ["의미를 가지", "의미를 가진", "의미를 가졌", "의미를 갖"], ["의미가 있", "의미가 없"]),
    ("have a good time", ["시간을 가지", "시간을 가진", "시간을 가졌", "시간을 갖"], ["시간을 보내", "시간을 보낸", "시간을 보냈"]),
    ("make a change", ["변화를 만들", "변화를 만든", "변화를 만드"], ["변화를 일으키", "변화를 일으킨", "변화를 일으켰", "변화를 가져오", "변화를 가져온", "변화를 가져왔"]),
    ("make a difference", ["차이를 만들", "차이를 만든", "차이를 만드"], ["차이가 나는", "차이가 나다", "차이가 나서", "차이가 난", "차이가 났", "차이를 낳"]),
    # 정상 기술 표현: 사전 용례가 없을 수 있다는 점을 보이는 대조군
    ("(대조) slow response", [], ["응답이 느리", "응답이 느린", "응답이 느려"]),
    ("(대조) read a value", [], ["값을 읽", "값을 읽은"]),
]


def _get(opener, url: str, data: bytes | None = None, referer: str | None = None) -> str:
    req = urllib.request.Request(url, data=data, headers={"User-Agent": UA, **({"Referer": referer} if referer else {})})
    for attempt in range(5):
        try:
            with opener.open(req, timeout=30) as r:
                return r.read().decode("utf-8", "replace")
        except OSError:
            if attempt == 4:
                raise
            time.sleep(10 * (attempt + 1))
    return ""


def _text(page: str) -> str:
    page = re.sub(r"(?s)<(script|style).*?</\1>", "", page)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", page)))


class Dicts:
    def __init__(self) -> None:
        self.cj = http.cookiejar.CookieJar()
        self.op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.cj))
        _get(self.op, "https://stdict.korean.go.kr/search/searchDetailWords.do")

    def opendict(self, q: str) -> int:
        url = "https://opendict.korean.go.kr/search/searchResult?" + urllib.parse.urlencode({"query": q, "dicType": "4", "currentPage": "1"})
        m = re.search(r"용례 (\d[\d,]*)", _text(_get(self.op, url)))
        return int(m.group(1).replace(",", "")) if m else -1

    def krdict(self, q: str) -> int:
        url = "https://krdict.korean.go.kr/kor/dicMarinerSearch/search?" + urllib.parse.urlencode(
            {"nation": "kor", "mainSearchWord": q, "sort": "W", "currentPage": "1", "blockCount": "10"}
        )
        m = re.search(r"용례 (\d[\d,]*)", _text(_get(self.op, url)))
        return int(m.group(1).replace(",", "")) if m else -1

    def stdict(self, q: str) -> int:
        form = {
            "word_no": "0", "searchKeywordTo": "3", "spCodeAll": "-1", "dialectRegionCodeAll": "-1", "techTermAll": "-1",
            "searchFlag": "Y", "searchBoxFlag": "Y", "pageSize": "10", "pageIndex": "1", "searchSpType": "or",
            "searchWordKindCode_all": "-1", "searchWordKind_all": "-1", "searchSpCode_all": "-1", "searchTechtermCode_all": "-1",
            "searchMultimediaCode_all": "-1", "searchType": "1", "searchOp": "AND", "searchTargets": "EXAMPLE",
            "searchTargetsOrgLanguage": "-1", "searchConditions": "all", "searchKeywords": q,
        }
        page = _get(self.op, "https://stdict.korean.go.kr/search/searchDetailWords.do", urllib.parse.urlencode(form).encode(),
                    referer="https://stdict.korean.go.kr/search/searchDetailWords.do")
        m = re.search(r"결과\s*\(총\s*([\d,]+)\s*개\)", _text(page))
        return int(m.group(1).replace(",", "")) if m else -1


MIN_NATURAL = 20  # 작업 기준. 공인 기준이 아니다.
RATIO = 10


def verdict(rec: dict) -> str:
    """우리말샘+한국어기초사전(둘 다 용례 문장 수)의 합으로 판정한다.

    표준국어대사전은 표제어 수라서 합치지 않는다. 직역 조합이 거기 나오면 반대 증거로만 본다.
    """
    if any(v < 0 for side in ("literal", "natural") for counts in rec[side].values() for v in counts.values()):
        return "미판정(조회 실패)"
    if not rec["literal"]:
        return "대조군"
    lit = rec["literal_sum"]["opendict"] + rec["literal_sum"]["krdict"]
    nat = rec["natural_sum"]["opendict"] + rec["natural_sum"]["krdict"]
    if nat < MIN_NATURAL and lit < MIN_NATURAL:
        return "보류(둘 다 드묾)"
    if nat >= MIN_NATURAL and nat >= RATIO * max(lit, 1) and rec["literal_sum"]["stdict"] == 0:
        return "검토 후보(빈도 차이; 번역투 판정 아님)"
    return "자동 판정 안 함"


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="calibration/data/dict-collocations.json")
    ap.add_argument("--sleep", type=float, default=2.5)
    ap.add_argument("--rejudge", action="store_true", help="저장된 결과에 판정만 다시 붙인다")
    args = ap.parse_args()
    if args.rejudge:
        with open(args.out, encoding="utf-8") as f:
            out = json.load(f)
        for rec in out["pairs"]:
            rec["verdict"] = verdict(rec)
            print(rec["english"], rec["verdict"])
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=2)
        return
    d = Dicts()
    rows = []
    for eng, literal, natural in PAIRS:
        rec = {"english": eng, "literal": {}, "natural": {}}
        for side, stems in (("literal", literal), ("natural", natural)):
            for stem in dict.fromkeys(stems):
                rec[side][stem] = {}
                for name in ("opendict", "krdict", "stdict"):
                    rec[side][stem][name] = getattr(d, name)(stem)
                    time.sleep(args.sleep)
        for side in ("literal", "natural"):
            rec[side + "_sum"] = {n: (-1 if any(v[n] < 0 for v in rec[side].values()) else sum(v[n] for v in rec[side].values())) for n in ("opendict", "krdict", "stdict")}
        rec["verdict"] = verdict(rec)
        rows.append(rec)
        print(eng, rec["literal_sum"], rec["natural_sum"], flush=True)
    out = {"date": time.strftime("%Y-%m-%d"), "note": "stdict는 표제어 수, 나머지는 용례 문장 수. 부분 문자열 일치. 줄기 사이 중복 일치 가능.", "pairs": rows}
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
