"""판정기 v0: 원장 한 행 -> 판정 JSON.

판정 로직은 rules/judge.v0.json 에서만 온다. 이 파일은 규칙을 해석할 뿐이다.
나중에 규칙 대신 LLM이 judge()를 채워도 입출력 계약(row -> verdict)은 그대로다.
"""
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import validate  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
KST = timezone(timedelta(hours=9))


def load_rules(path=None):
    p = Path(path) if path else ROOT / "rules" / "judge.v0.json"
    return json.loads(p.read_text(encoding="utf-8"))


def match(cond, facts):
    """조건 dict가 facts와 맞는지. {"any": [...]} 는 하나라도 맞으면 참."""
    if "any" in cond:
        return any(match(c, facts) for c in cond["any"])
    return all(facts.get(k) == v for k, v in cond.items())


def judge(row, rules):
    """원장 한 행과 규칙을 받아 판정 dict를 돌려준다. 시각은 넣지 않는다(순수 함수)."""
    t = row["tags"]

    can = rules["can"][t["structure"]][t["judgment"]]
    can_reason = f"정형도 {t['structure']} · 판단 개입 {t['judgment']} → {can}"

    s = rules["should"]
    hours = row["hours_per_month"]
    rate = row.get("declared_reduction_rate")
    enough_hours = hours >= s["min_hours_per_month"]
    expects_cut = rate is not None and rate > s["require_declared_reduction_rate_above"]
    should = "예" if (enough_hours and expects_cut) else "아니오"
    rate_txt = "작성자 감축률 없음" if rate is None else f"작성자 감축률 {rate}"
    should_reason = (
        f"월 {hours:g}h (기준 {s['min_hours_per_month']:g}h "
        f"{'이상' if enough_hours else '미만'}) · {rate_txt} → {should}"
    )

    may, may_rule = "예", None
    may_facts = {"approval": t["approval"], "sensitivity": t["sensitivity"]}
    for r in rules["may"]:
        if "when" not in r or match(r["when"], may_facts):
            may, may_rule = r["value"], r["id"]
            break
    may_reason = f"민감도 {t['sensitivity']} · 승인 {t['approval']} → {may}"

    facts = {"can": can, "should": should, "may": may}
    verdict, rule_id = "판정 불가", None
    for r in rules["verdicts"]:
        if match(r["when"], facts):
            verdict, rule_id = r["verdict"], r["id"]
            break

    return {
        "schema_version": "0.2",
        "id": row["id"],
        "source_code": row["source_code"],
        "activity": row["activity"],
        "hours_per_month": hours,
        "verdict": verdict,
        "rule_id": rule_id,
        "rules_version": rules["rules_version"],
        "tags_status": t["status"],
        "can": {"value": can, "reason": can_reason},
        "should": {"value": should, "reason": should_reason},
        "may": {"value": may, "reason": may_reason, "rule_id": may_rule},
    }


def main(ledger_dir=None, out_dir=None):
    ledger = Path(ledger_dir) if ledger_dir else ROOT / "data" / "ledger"
    out = Path(out_dir) if out_dir else ROOT / "out" / "verdicts"
    if validate.main(str(ledger)) != 0:
        print("원장 검증 실패: 판정을 중단합니다.")
        return 1
    rules = load_rules()
    out.mkdir(parents=True, exist_ok=True)
    now = datetime.now(KST).isoformat(timespec="seconds")
    for f in sorted(ledger.glob("*.json")):
        row = json.loads(f.read_text(encoding="utf-8"))
        v = judge(row, rules)
        v["judged_at"] = now
        (out / f"{row['id']}.json").write_text(
            json.dumps(v, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print(f"{row['id']}  {v['verdict']}  ({v['rule_id']})")
    return 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:3]))
