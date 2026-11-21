# loop-lab

업무 원장 한 행이 판정을 거쳐 카드 한 장이 되기까지, 5단계를 끝에서 끝까지 관통하는 워킹 스켈레톤입니다.

```
원장 JSON → 검증 → 판정(규칙) → 카드 페이지 → (Actions로 자동 배포, 준비 중)
```

## 실행

```bash
pip install -r requirements.txt
python scripts/validate.py                # 원장 검증
python scripts/judge.py                   # 판정 → out/verdicts/*.json
python scripts/build_site.py              # 카드 → site/index.html
```

## 테스트

```bash
python tests/test_validate.py && python tests/test_judge.py && python tests/test_site.py
```

## 구조

| 경로 | 역할 |
| --- | --- |
| `data/ledger/` | 원장 한 행 = 파일 하나 (사람이 고치는 파일) |
| `schema/ledger.schema.json` | 원장 필드 계약 |
| `rules/judge.v0.json` | 판정 규칙과 임계값 (판정기는 이 파일을 해석할 뿐) |
| `scripts/` | 검증 · 판정 · 페이지 생성 |
| `out/`, `site/` | 생성물 (저장소에 올리지 않음) |

## 데이터 취급

저장소는 공개입니다. 원장 원본의 작성자·조직 식별 정보는 올리지 않으며, 샘플 몇 행만 비식별로 둡니다.
