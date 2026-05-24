"""
네이버 검색광고 API - 키워드 도구 연관 키워드 조회

네이버 광고주센터 키워드 도구에서 제공하던 연관 키워드 목록을
/keywordstool API로 조회해 출력·엑셀 저장합니다.
"""
import base64
import hashlib
import hmac
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from typing import Dict, List, Optional, Tuple

try:
    from openpyxl import Workbook
except ImportError:
    print("openpyxl 패키지가 필요합니다. 아래 명령으로 설치해 주세요:")
    print("  python3 -m venv .venv && .venv/bin/pip install -r requirements.txt")
    print("  .venv/bin/python 연관키워드검색.py")
    sys.exit(1)

BASE_URL = "https://api.searchad.naver.com"
API_KEY = os.environ.get(
    "NAVER_SEARCH_ACCESS_LICENSE_KEY",
    "0100000000dd8f61526f89d0750886d5d0fe0ef71a018ae95cdd17b407f0d54b106bab7036",
)
SECRET_KEY = os.environ.get(
    "NAVER_SEARCH_SECRET_KEY",
    "AQAAAADdj2FSb4nQdQiG1dD+Dvca8aEIzoYUNkvbq4Hjie4znQ==",
)
CUSTOMER_ID = os.environ.get("NAVER_SEARCH_CUSTOMER_ID", "4394922")

EXCEL_HEADERS = (
    "키워드",
    "PC검색량",
    "모바일검색량",
    "월간총검색량",
    "월평균클릭수(PC)",
    "월평균클릭수(모바일)",
    "월평균클릭률(PC)",
    "월평균클릭률(모바일)",
    "월평균노출광고수",
    "경쟁정도",
)


def generate_signature(timestamp: str, method: str, uri: str, secret_key: str) -> str:
    message = f"{timestamp}.{method}.{uri}"
    digest = hmac.new(
        secret_key.encode("utf-8"),
        message.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    return base64.b64encode(digest).decode("utf-8")


def build_headers(method: str, uri: str) -> Dict[str, str]:
    timestamp = str(round(time.time() * 1000))
    return {
        "Content-Type": "application/json; charset=UTF-8",
        "X-Timestamp": timestamp,
        "X-API-KEY": API_KEY,
        "X-Customer": str(CUSTOMER_ID),
        "X-Signature": generate_signature(timestamp, method, uri, SECRET_KEY),
    }


def normalize_keyword(keyword: str) -> str:
    return keyword.strip().replace(" ", "")


def parse_count(value) -> Optional[int]:
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return int(value)
    text = str(value).strip()
    if not text:
        return None
    if text == "<10":
        return None
    cleaned = text.replace(",", "")
    try:
        return int(float(cleaned))
    except ValueError:
        return None


def format_count(value) -> str:
    text = str(value).strip() if value is not None else ""
    if text == "<10":
        return "<10"
    parsed = parse_count(value)
    if parsed is None:
        return text or "-"
    return f"{parsed:,}"


def calc_total(pc_count, mobile_count) -> str:
    pc_text = str(pc_count).strip() if pc_count is not None else ""
    mobile_text = str(mobile_count).strip() if mobile_count is not None else ""
    if pc_text == "<10" or mobile_text == "<10":
        return "10 미만 포함 구간"
    pc_num = parse_count(pc_count)
    mobile_num = parse_count(mobile_count)
    if pc_num is not None and mobile_num is not None:
        return f"{pc_num + mobile_num:,}"
    return "-"


def parse_display_number(value) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip()
    if not text or text == "-":
        return None
    try:
        return float(text.replace(",", ""))
    except ValueError:
        return None


def extract_row(item: Dict) -> Tuple[str, str, str, str, str, str, str, str, str, str]:
    pc_count = item.get("monthlyPcQcCnt", "0")
    mobile_count = item.get("monthlyMobileQcCnt", "0")
    return (
        item.get("relKeyword", ""),
        format_count(pc_count),
        format_count(mobile_count),
        calc_total(pc_count, mobile_count),
        str(item.get("monthlyAvePcClkCnt", "-")),
        str(item.get("monthlyAveMobileClkCnt", "-")),
        str(item.get("monthlyAvePcCtr", "-")),
        str(item.get("monthlyAveMobileCtr", "-")),
        str(item.get("plAvgDepth", "-")),
        str(item.get("compIdx", "-")),
    )


def get_related_keywords(keyword: str, show_detail: int = 1) -> List[Dict]:
    uri = "/keywordstool"
    method = "GET"
    params = {
        "hintKeywords": keyword,
        "showDetail": str(show_detail),
    }
    query = urllib.parse.urlencode(params)
    url = f"{BASE_URL}{uri}?{query}"

    request = urllib.request.Request(url, headers=build_headers(method, uri))
    with urllib.request.urlopen(request) as response:
        if response.getcode() != 200:
            raise RuntimeError(f"Error Code: {response.getcode()}")

        body = json.loads(response.read().decode("utf-8"))
        return body.get("keywordList", [])


def print_row(row: Tuple[str, str, str, str, str, str, str, str, str, str]) -> None:
    (
        keyword,
        pc,
        mobile,
        total,
        pc_clk,
        mobile_clk,
        pc_ctr,
        mobile_ctr,
        depth,
        comp,
    ) = row
    print(
        f"키워드: {keyword} | PC검색량: {pc} | 모바일검색량: {mobile} | "
        f"월간총검색량: {total} | 경쟁정도: {comp}"
    )


def sanitize_filename(keyword: str) -> str:
    sanitized = re.sub(r'[\\/:*?"<>|]', "_", keyword.strip())
    return sanitized or "키워드"


def save_to_excel(
    filepath: str,
    rows: List[Tuple[str, str, str, str, str, str, str, str, str, str]],
) -> None:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "연관키워드"
    sheet.append(list(EXCEL_HEADERS))
    for row in rows:
        keyword, pc, mobile, total, pc_clk, mobile_clk, pc_ctr, mobile_ctr, depth, comp = row
        sheet.append(
            [
                keyword,
                parse_display_number(pc),
                parse_display_number(mobile),
                parse_display_number(total),
                parse_display_number(pc_clk),
                parse_display_number(mobile_clk),
                parse_display_number(pc_ctr),
                parse_display_number(mobile_ctr),
                parse_display_number(depth),
                comp,
            ]
        )
    workbook.save(filepath)


def ask_max_count() -> int:
    while True:
        text = input("저장할 연관 키워드 개수를 입력하세요 (0 = 전체): ").strip()
        if not text.isdigit():
            print("0 이상의 숫자를 입력해 주세요.")
            continue
        return int(text)


def main() -> None:
    if len(sys.argv) > 1:
        seed_keyword = " ".join(sys.argv[1:]).strip()
    else:
        seed_keyword = input("검색할 키워드를 입력하세요: ").strip()

    if not seed_keyword:
        print("키워드를 입력해 주세요.")
        sys.exit(1)

    max_count = ask_max_count()
    count_label = "전체" if max_count == 0 else f"{max_count}개"

    print(f"\n'{seed_keyword}' 연관 키워드 조회를 시작합니다. (저장: {count_label})\n")

    try:
        keyword_list = get_related_keywords(seed_keyword)
    except Exception as e:
        print("조회 실패:", e)
        sys.exit(1)

    if not keyword_list:
        print("키워드:", seed_keyword)
        print("연관 키워드 검색 결과가 없습니다.")
        sys.exit(0)

    rows = [extract_row(item) for item in keyword_list]
    if max_count > 0:
        rows = rows[:max_count]

    for row in rows:
        print_row(row)

    excel_path = f"{sanitize_filename(seed_keyword)}_연관키워드.xlsx"
    save_to_excel(excel_path, rows)
    print(f"\n총 {len(rows)}개 연관 키워드를 '{excel_path}' 파일에 저장했습니다.")


if __name__ == "__main__":
    main()
