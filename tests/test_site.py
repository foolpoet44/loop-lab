"""C03 UAT: 판정 JSON이 한 장의 카드로 보인다."""
import copy
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import build_site  # noqa: E402
import judge  # noqa: E402

RULES = judge.load_rules()


def load(name):
    return json.loads((ROOT / "data" / "ledger" / name).read_text(encoding="utf-8"))


def check(name, ok):
    print(f"{'PASS' if ok else 'FAIL'}  {name}")
    return ok


def build(verdicts):
    with tempfile.TemporaryDirectory() as d:
        vdir = Path(d, "v")
        vdir.mkdir()
        for v in verdicts:
            (vdir / f"{v['id']}.json").write_text(json.dumps(v, ensure_ascii=False), encoding="utf-8")
        out = Path(d, "site", "index.html")
        code = build_site.main(str(vdir), str(out))
        return code, (out.read_text(encoding="utf-8") if out.exists() else "")


def main():
    r = []
    rows = [load("WL-0001.json"), load("WL-0002.json")]
    verdicts = []
    for row in rows:
        v = judge.judge(row, RULES)
        v["judged_at"] = "2026-11-22T08:00:00+09:00"
        verdicts.append(v)

    code, html = build(verdicts)
    r.append(check("종료 코드 0", code == 0))
    r.append(check("카드 수 = 판정 수", html.count('<article class="card">') == 2))
    for v in verdicts:
        r.append(check(f"{v['id']}: 활동명·판정·규칙 ID가 보인다",
                       v["activity"] in html and v["verdict"] in html and f"적용 규칙 {v['rule_id']}" in html))
        r.append(check(f"{v['id']}: Can/Should/May 값과 근거가 보인다",
                       all(v[k]["reason"] in html for k in ("can", "should", "may"))))
    r.append(check("서로 다른 판정이 서로 다른 색 클래스로 표시된다",
                   "v-gate" in html and "v-assist" in html))

    # 값은 이스케이프된다
    evil = copy.deepcopy(verdicts[0])
    evil["activity"] = "<script>alert(1)</script>"
    _, html2 = build([evil])
    r.append(check("HTML 주입은 이스케이프된다", "<script>alert(1)" not in html2 and "&lt;script&gt;" in html2))

    # 초안 태그는 경고로 표시
    draft = copy.deepcopy(verdicts[0]); draft["tags_status"] = "초안"
    _, html3 = build([draft])
    r.append(check("태그 초안은 '확정 전'으로 경고된다", "확정 전" in html3))

    # 판정이 없으면 실패
    with tempfile.TemporaryDirectory() as d:
        r.append(check("판정 파일이 없으면 실패(종료 코드 1)", build_site.main(d, str(Path(d, "x.html"))) == 1))
    return 0 if all(r) else 1


if __name__ == "__main__":
    sys.exit(main())
