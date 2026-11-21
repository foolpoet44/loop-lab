"""원장 JSON을 스키마로 검증한다. 하나라도 실패하면 종료 코드 1."""
import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parent.parent


def validate_file(path, validator):
    """파일 하나를 검증하고 오류 메시지 목록을 돌려준다."""
    try:
        row = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return [f"JSON 파싱 실패: {e}"]
    errors = sorted(validator.iter_errors(row), key=lambda e: list(e.path))
    return [
        f"{'/'.join(str(p) for p in e.path) or '(root)'}: {e.message}"
        for e in errors
    ]


def main(ledger_dir=None):
    schema = json.loads((ROOT / "schema" / "ledger.schema.json").read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    target = Path(ledger_dir) if ledger_dir else ROOT / "data" / "ledger"
    files = sorted(target.glob("*.json"))
    if not files:
        print(f"검증할 원장 파일이 없습니다: {target}")
        return 1
    failed = 0
    for f in files:
        errs = validate_file(f, validator)
        if errs:
            failed += 1
            print(f"FAIL {f.name}")
            for m in errs:
                print(f"  - {m}")
        else:
            print(f"OK   {f.name}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else None))
