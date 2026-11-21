"""C01 UAT: 필드를 빼거나 값이 틀리면 검증이 실패하고, 정상 행은 통과한다."""
import copy
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import validate  # noqa: E402

GOOD = json.loads((ROOT / "data" / "ledger" / "WL-0001.json").read_text(encoding="utf-8"))
SCHEMA = json.loads((ROOT / "schema" / "ledger.schema.json").read_text(encoding="utf-8"))
REQUIRED = SCHEMA["required"]
TAG_REQUIRED = SCHEMA["properties"]["tags"]["required"]


def run(row):
    with tempfile.TemporaryDirectory() as d:
        Path(d, "WL-9999.json").write_text(json.dumps(row, ensure_ascii=False), encoding="utf-8")
        return validate.main(d)


def check(name, got, want):
    ok = got == want
    print(f"{'PASS' if ok else 'FAIL'}  {name} (exit={got}, 기대={want})")
    return ok


def main():
    results = [check("정상 행은 통과", run(GOOD), 0)]
    for field in REQUIRED:
        bad = copy.deepcopy(GOOD)
        del bad[field]
        results.append(check(f"필수 필드 '{field}' 제거 시 실패", run(bad), 1))
    for tag in TAG_REQUIRED:
        bad = copy.deepcopy(GOOD)
        del bad["tags"][tag]
        results.append(check(f"태그 '{tag}' 제거 시 실패", run(bad), 1))
    bad = copy.deepcopy(GOOD)
    bad["tags"]["sensitivity"] = "매우높음"
    results.append(check("허용 외 enum 값은 실패", run(bad), 1))
    bad = copy.deepcopy(GOOD)
    bad["declared_reduction_rate"] = 1.5
    results.append(check("감축률 1 초과는 실패", run(bad), 1))
    bad = copy.deepcopy(GOOD)
    bad["writer_name"] = "x"
    results.append(check("작성자 식별 필드는 스키마가 거부", run(bad), 1))
    bad = copy.deepcopy(GOOD)
    bad["hours_per_month"] = -1
    results.append(check("음수 시간은 실패", run(bad), 1))
    bad = copy.deepcopy(GOOD)
    bad["extra"] = "x"
    results.append(check("정의되지 않은 필드는 실패", run(bad), 1))
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
