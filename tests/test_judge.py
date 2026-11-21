"""C02 UAT: 값 하나를 바꾸면 판정 구간이 바뀐다."""
import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import judge  # noqa: E402

RULES = judge.load_rules()


def load(name):
    return json.loads((ROOT / "data" / "ledger" / name).read_text(encoding="utf-8"))


W1 = load("WL-0001.json")
W2 = load("WL-0002.json")


def check(name, got, want):
    ok = got == want
    print(f"{'PASS' if ok else 'FAIL'}  {name} (결과={got}, 기대={want})")
    return ok


def verdict(row, rules=RULES):
    v = judge.judge(row, rules)
    return (v["verdict"], v["rule_id"])


def main():
    r = []
    # 실제 샘플 두 행은 서로 다른 구간으로 갈린다
    r.append(check("WL-0001 (정형·일부·승인 조건부)", verdict(W1), ("승인 조건부", "R4")))
    r.append(check("WL-0002 (반정형·핵심·민감도 높음)", verdict(W2), ("사람 주도 · AI 보조", "R2")))

    # 값 하나를 바꾸면 구간이 바뀐다
    x = copy.deepcopy(W1); x["tags"]["approval"] = "없음"
    r.append(check("WL-0001 승인 조건부→없음", verdict(x), ("바로 위임", "R5")))

    x = copy.deepcopy(W1); x["hours_per_month"] = 3
    r.append(check("WL-0001 월 8h→3h", verdict(x), ("개별 설계", "R3")))

    x = copy.deepcopy(W1); x["declared_reduction_rate"] = 0
    r.append(check("WL-0001 감축률 0.7→0", verdict(x), ("개별 설계", "R3")))

    x = copy.deepcopy(W1); x["tags"]["structure"] = "비정형"
    r.append(check("WL-0001 정형→비정형", verdict(x), ("사람 고유", "R1")))

    x = copy.deepcopy(W1); x["tags"]["judgment"] = "핵심"
    r.append(check("WL-0001 판단 일부→핵심", verdict(x), ("사람 주도 · AI 보조", "R2")))

    x = copy.deepcopy(W1); x["tags"]["approval"] = "필수"; x["tags"]["sensitivity"] = "높음"
    r.append(check("승인 필수 + 민감도 높음은 May=아니오", verdict(x), ("사람 고유", "R1")))

    # 규칙 파일의 숫자만 바꿔도 판정이 바뀐다 (코드는 그대로)
    strict = copy.deepcopy(RULES); strict["should"]["min_hours_per_month"] = 9
    r.append(check("기준 5h→9h (규칙 파일만 변경)", verdict(W1, strict), ("개별 설계", "R3")))

    # 출력 계약: 근거가 함께 남는다
    v = judge.judge(W1, RULES)
    r.append(check("판정에 규칙 ID와 세 질문의 근거가 있다",
                   all(v[k]["reason"] for k in ("can", "should", "may")) and bool(v["rule_id"]), True))
    r.append(check("판정기는 순수 함수(시각 없음)", "judged_at" in v, False))
    return 0 if all(r) else 1


if __name__ == "__main__":
    sys.exit(main())
