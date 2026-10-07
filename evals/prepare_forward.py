"""Prepare an unlabeled review packet from independently produced answers."""
import json
import random
from pathlib import Path

BASE = Path(__file__).resolve().parent / "forward-2026-10-07"
ORIGINALS = [
    "이 모듈은 Windows와 Linux에서 동작합니다. 설정 파일은 실행 폴더에 둡니다.",
    "모든 연결이 끊기지 않았습니다. 작업을 다시 시작하기 전에 확인하세요.",
    "검사가 실패한 경우에만 요청을 취소하고 임시 파일의 일부를 12시간 이내에 지워야 합니다. 검사가 통과하면 파일을 지워도 됩니다.",
    "이 변경이 오류를 줄였을 가능성은 있지만 아직 확인되지 않았습니다. 금요일까지 결과를 공유할 예정입니다.",
    "`settings.toml`을 열어 `port`를 9090으로 바꾸고 저장한 다음 앱을 다시 시작하세요. 앱을 다시 시작하기 전에 실행 중인 작업이 끝났는지 확인하세요.",
]


def main():
    rows = []
    for cfg in ("with_skill", "without_skill"):
        for n, original in enumerate(ORIGINALS, 1):
            path = BASE / cfg / f"case-{n}" / "output.md"
            rows.append({"case": n, "config": cfg, "original": original, "output": path.read_text(encoding="utf-8").strip()})
    random.Random(717).shuffle(rows)
    mapping, packet = {}, []
    for n, row in enumerate(rows, 1):
        identity = f"item-{n:02}"
        mapping[identity] = {"case": row["case"], "config": row["config"]}
        packet.append({"id": identity, "original": row["original"], "output": row["output"]})
    (BASE / "blind-inputs.json").write_text(json.dumps(packet, ensure_ascii=False, indent=2), encoding="utf-8")
    (BASE / "review-mapping.json").write_text(json.dumps(mapping, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Prepared 10 unlabeled outputs")


if __name__ == "__main__":
    main()
