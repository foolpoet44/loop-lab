"""판정 JSON -> 카드가 뜨는 정적 페이지 한 장(site/index.html).

서버도 외부 의존도 없다. 판정 JSON을 읽어 HTML 문자열로 바꿀 뿐이다.
값은 모두 html.escape 를 거친다.
"""
import json
import sys
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# 판정 구간별 색상 클래스. 판정 문구는 rules/judge.v0.json 의 verdict 와 같아야 한다.
VERDICT_CLASS = {
    "바로 위임": "v-go",
    "승인 조건부": "v-gate",
    "개별 설계": "v-design",
    "사람 주도 · AI 보조": "v-assist",
    "사람 고유": "v-human",
}
VALUE_CLASS = {"예": "ok", "조건부": "mid", "부분": "mid", "아니오": "no"}

CSS = """
:root{--bg:#f6f5f2;--card:#fff;--ink:#1f1f1d;--sub:#6b6a66;--line:#e2e0da;
--go:#1d7a46;--gate:#1f5fae;--design:#9a6a00;--assist:#6a3fb0;--human:#55534e;--bad:#b3261e}
@media(prefers-color-scheme:dark){:root{--bg:#161615;--card:#222221;--ink:#f0efec;--sub:#a3a29d;--line:#37362f;
--go:#5fd08b;--gate:#7fb0f0;--design:#e6b24a;--assist:#b79af0;--human:#bdbbb4;--bad:#ff8a80}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.6 -apple-system,"Apple SD Gothic Neo","Noto Sans KR",sans-serif}
main{max-width:720px;margin:0 auto;padding:24px 16px 48px}
h1{font-size:20px;margin:0 0 4px}
.lead{color:var(--sub);margin:0 0 20px;font-size:13px}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:18px;margin:0 0 16px}
.top{display:flex;gap:12px;justify-content:space-between;align-items:flex-start}
.top h2{font-size:17px;margin:0}
.meta{color:var(--sub);font-size:12.5px;margin-top:2px}
.badge{flex:none;font-weight:600;font-size:13px;border:1.5px solid currentColor;border-radius:999px;padding:3px 12px;white-space:nowrap}
.v-go{color:var(--go)}.v-gate{color:var(--gate)}.v-design{color:var(--design)}
.v-assist{color:var(--assist)}.v-human{color:var(--human)}.v-none{color:var(--bad)}
.qs{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:10px;margin:14px 0 12px}
.q{border:1px solid var(--line);border-radius:8px;padding:10px 12px}
.q b{font-size:12px;color:var(--sub);font-weight:600}
.val{font-size:17px;font-weight:700;margin:2px 0}
.ok{color:var(--go)}.mid{color:var(--design)}.no{color:var(--human)}
.why{font-size:12.5px;color:var(--sub)}
.foot{font-size:12px;color:var(--sub);display:flex;flex-wrap:wrap;gap:4px 14px}
.warn{color:var(--bad);font-weight:600}
"""


def card(v):
    cls = VERDICT_CLASS.get(v["verdict"], "v-none")

    def q(label, key):
        x = v[key]
        return (
            f'<div class="q"><b>{label}</b>'
            f'<div class="val {VALUE_CLASS.get(x["value"], "")}">{escape(x["value"])}</div>'
            f'<div class="why">{escape(x["reason"])}</div></div>'
        )

    tag_state = (
        f'<span>태그 {escape(v["tags_status"])}</span>'
        if v["tags_status"] == "확인"
        else f'<span class="warn">태그 {escape(v["tags_status"])} (확정 전)</span>'
    )
    return (
        '<article class="card">'
        '<div class="top"><div>'
        f'<h2>{escape(v["activity"])}</h2>'
        f'<div class="meta">{escape(v["id"])} · {escape(v["source_code"])} · 월 {v["hours_per_month"]:g}h</div>'
        f'</div><div class="badge {cls}">{escape(v["verdict"])}</div></div>'
        f'<div class="qs">{q("Can · AI가 할 수 있나", "can")}'
        f'{q("Should · 할 가치가 있나", "should")}{q("May · 맡겨도 되나", "may")}</div>'
        '<div class="foot">'
        f'<span>적용 규칙 {escape(str(v["rule_id"]))}</span>'
        f'<span>규칙 v{escape(v["rules_version"])}</span>'
        f'{tag_state}'
        f'<span>판정 {escape(v.get("judged_at", "-"))}</span>'
        "</div></article>"
    )


def render(verdicts):
    cards = "\n".join(card(v) for v in verdicts)
    return (
        '<!doctype html><html lang="ko"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        "<title>업무 원장 판정 카드</title>"
        f"<style>{CSS}</style></head><body><main>"
        "<h1>업무 원장 판정 카드</h1>"
        f'<p class="lead">원장 {len(verdicts)}행 · 규칙 기반 판정(v0) · 근거를 함께 표시합니다</p>'
        f"{cards}</main></body></html>\n"
    )


def main(verdict_dir=None, out_file=None):
    src = Path(verdict_dir) if verdict_dir else ROOT / "out" / "verdicts"
    dst = Path(out_file) if out_file else ROOT / "site" / "index.html"
    files = sorted(src.glob("*.json"))
    if not files:
        print(f"판정 파일이 없습니다: {src}")
        return 1
    verdicts = [json.loads(f.read_text(encoding="utf-8")) for f in files]
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(render(verdicts), encoding="utf-8")
    print(f"카드 {len(verdicts)}장 -> {dst}")
    return 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:3]))
