# top_errors_runner.py
import json
from __future__ import annotations
import argparse
from collections import defaultdict
from pathlib import Path

def parse_tokens_from_file(path: Path) -> list[str]:
    """
    로그 파일 포맷을 유연하게 처리:
    - 한 줄에 PASS 하나씩 있어도 되고
    - "PASS,FAIL_err1,FAIL_err9" 처럼 콤마로 구분돼도 되고
    - 공백/탭/개행 섞여도 됨
    """
    text = path.read_text(encoding="utf-8", errors="replace")
    # 콤마를 개행으로 바꾸고, 공백 기준 split
    text = text.replace(",", "\n")
    tokens = [t.strip() for t in text.split() if t.strip()]
    return tokens

def top_errors(logs: list[str]) -> dict:
    result = {"top_errors": {}, "etc": {}}

    if not logs:
        result["message"] = "로그가 포함되어있지 않습니다."
        return result

    top = defaultdict(int)
    etc = defaultdict(int)

    seen_pass_or_fail = False
    seen_fail = False
    seen_pass = False

    def classify(token: str):
        t = (token or "").strip()
        if not t:
            return ("ETC", t)

        u = t.upper()

        if u == "PASS":
            return ("PASS", None)

        if u.startswith("FAIL"):
            if "_" in t:
                _, code = t.split("_", 1)
                code = code.strip()
                if code:
                    return ("TOP", code.lower())
            return ("UNKNOWN", None)

        return ("ETC", t)  # 원본 그대로

    for token in logs:
        kind, value = classify(token)

        if kind == "PASS":
            seen_pass_or_fail = True
            seen_pass = True
            continue

        if kind == "TOP":
            seen_pass_or_fail = True
            seen_fail = True
            top[value] += 1
            continue

        if kind == "UNKNOWN":
            seen_pass_or_fail = True
            seen_fail = True
            etc["UNKNOWN"] += 1
            continue

        etc[value] += 1

    result["top_errors"] = dict(top)
    result["etc"] = dict(etc)

    if seen_pass_or_fail and (not seen_fail) and seen_pass:
        result["message"] = "All PASS 되었습니다."
    elif not seen_pass_or_fail:
        result["message"] = "로그 정보에 pass,fail 모두 없습니다."

    return result

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--logfile", required=True, help="로그 파일 경로 (예: logs/sample.log)")
    args = ap.parse_args()

    path = Path(args.logfile)
    if not path.exists():
        raise SystemExit(f"❌ 파일이 없습니다: {path}")

    logs = parse_tokens_from_file(path)
    result = top_errors(logs)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))

if __name__ == "__main__":
    main()
