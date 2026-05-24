"""
네이버 검색광고 API - 키워드 월간 검색량 무한 반복 조회
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
from collections import deque
from typing import Callable, Dict, List, Optional, Tuple

try:
    from openpyxl import Workbook
except ImportError:
    print("openpyxl 패키지가 필요합니다. 아래 명령으로 설치해 주세요:")
    print("  python3 -m venv .venv && .venv/bin/pip install -r requirements.txt")
    print("  .venv/bin/python 월간검색량.py")
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

BLOG_CLIENT_ID = os.environ.get("NAVER_CLIENT_ID", "OmIWV_6SWBTRPhDsMhmo")
BLOG_CLIENT_SECRET = os.environ.get("NAVER_CLIENT_SECRET", "qWj8puJFp_")

EXCEL_HEADERS = (
    "키워드",
    "PC검색량",
    "모바일검색량",
    "월간총검색량",
    "문서수",
    "경쟁율",
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


def parse_count(value, minimum_if_lt10: bool = False) -> Optional[int]:
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    text = str(value).strip()
    if not text:
        return None
    if text == "<10":
        return 10 if minimum_if_lt10 else 0
    cleaned = text.replace(",", "")
    try:
        return int(float(cleaned))
    except ValueError:
        return None


def parse_display_number(value) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip()
    if not text or text == "-":
        return None
    if "미만" in text:
        return None
    try:
        return float(text.replace(",", ""))
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


def calc_monthly_total_num(pc_count, mobile_count) -> Optional[int]:
    pc_num = parse_count(pc_count, minimum_if_lt10=True)
    mobile_num = parse_count(mobile_count, minimum_if_lt10=True)
    if pc_num is not None and mobile_num is not None:
        return pc_num + mobile_num
    return None


def calc_competition(
    document_count: Optional[int],
    pc_count,
    mobile_count,
    monthly_total_text: str = "",
) -> float:
    if not document_count:
        return 0.0

    monthly_total = calc_monthly_total_num(pc_count, mobile_count)
    if not monthly_total:
        monthly_total = parse_display_number(monthly_total_text)
    if not monthly_total:
        return 0.0

    return round(document_count / monthly_total, 2)


def get_blog_document_count(query: str) -> int:
    enc_text = urllib.parse.quote(query)
    url = "https://openapi.naver.com/v1/search/blog?query=" + enc_text + "&display=1"
    request = urllib.request.Request(url)
    request.add_header("X-Naver-Client-Id", BLOG_CLIENT_ID)
    request.add_header("X-Naver-Client-Secret", BLOG_CLIENT_SECRET)

    with urllib.request.urlopen(request) as response:
        if response.getcode() != 200:
            raise RuntimeError(f"Error Code: {response.getcode()}")

        body = json.loads(response.read().decode("utf-8"))
        return int(body.get("total", 0))


def extract_volume_row(keyword: str, result: Dict) -> Tuple[str, str, str, str, str, float]:
    pc_count = result.get("monthlyPcQcCnt", "0")
    mobile_count = result.get("monthlyMobileQcCnt", "0")
    rel_keyword = result.get("relKeyword", keyword)
    monthly_total_text = calc_total(pc_count, mobile_count)

    document_count: Optional[int] = None
    try:
        document_count = get_blog_document_count(rel_keyword)
        document_text = f"{document_count:,}"
    except Exception as e:
        print(f"문서수 조회 실패 ({rel_keyword}):", e)
        document_text = "-"

    competition = calc_competition(
        document_count,
        pc_count,
        mobile_count,
        monthly_total_text,
    )

    return (
        rel_keyword,
        format_count(pc_count),
        format_count(mobile_count),
        monthly_total_text,
        document_text,
        competition,
    )


def get_keyword_search_volume(keyword: str, show_detail: int = 1) -> List[Dict]:
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


def find_keyword_result(keyword: str, keyword_list: List[Dict]) -> Optional[Dict]:
    normalized = normalize_keyword(keyword)
    for item in keyword_list:
        rel_keyword = item.get("relKeyword", "")
        if normalize_keyword(rel_keyword) == normalized:
            return item
    return keyword_list[0] if keyword_list else None


def print_volume_row(row: Tuple[str, str, str, str, str, float]) -> None:
    keyword, pc, mobile, total, documents, competition = row
    competition_text = f"{competition:.2f}" if competition else "-"
    print(
        f"키워드: {keyword} | PC검색량: {pc} | 모바일검색량: {mobile} | "
        f"월간총검색량: {total} | 문서수: {documents} | 경쟁율: {competition_text}"
    )


def sanitize_filename(keyword: str) -> str:
    sanitized = re.sub(r'[\\/:*?"<>|]', "_", keyword.strip())
    return sanitized or "키워드"


def save_to_excel(filepath: str, rows: List[Tuple[str, str, str, str, str, float]]) -> None:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "월간검색량"
    sheet.append(list(EXCEL_HEADERS))
    for row in rows:
        keyword, pc, mobile, total, documents, competition = row
        sheet.append(
            [
                keyword,
                parse_display_number(pc),
                parse_display_number(mobile),
                parse_display_number(total),
                parse_display_number(documents),
                competition if competition else None,
            ]
        )
    workbook.save(filepath)


def ask_keyword_count() -> int:
    while True:
        text = input("조회할 키워드 개수를 입력하세요 (0 = 무제한): ").strip()
        if not text.isdigit():
            print("0 이상의 숫자를 입력해 주세요.")
            continue
        return int(text)


def crawl_keywords(
    seed_keyword: str,
    max_count: int,
    on_row: Optional[Callable[[Tuple[str, str, str, str, str, float]], None]] = None,
    on_log: Optional[Callable[[str], None]] = None,
    should_stop: Optional[Callable[[], bool]] = None,
) -> List[Tuple[str, str, str, str, str, float]]:
    searched: set[str] = set()
    queue: deque[str] = deque()
    records: List[Tuple[str, str, str, str, str, float]] = []
    unlimited = max_count == 0

    def log(message: str) -> None:
        if on_log:
            on_log(message)
        else:
            print(message)

    def emit_row(row: Tuple[str, str, str, str, str, float]) -> None:
        if on_row:
            on_row(row)
        else:
            print_volume_row(row)

    def is_limit_reached() -> bool:
        return not unlimited and len(records) >= max_count

    def stopped() -> bool:
        return bool(should_stop and should_stop())

    try:
        first_list = get_keyword_search_volume(seed_keyword)
    except Exception as e:
        raise RuntimeError(f"조회 실패: {e}") from e

    if not first_list:
        log(f"키워드: {seed_keyword}")
        log("검색 결과가 없습니다.")
        return records

    seed_result = find_keyword_result(seed_keyword, first_list)
    if seed_result:
        seed_norm = normalize_keyword(seed_result.get("relKeyword", seed_keyword))
        searched.add(seed_norm)
        row = extract_volume_row(seed_keyword, seed_result)
        records.append(row)
        emit_row(row)
        time.sleep(0.1)

    for item in first_list:
        rel_keyword = item.get("relKeyword", "").strip()
        if not rel_keyword:
            continue
        if normalize_keyword(rel_keyword) not in searched:
            queue.append(rel_keyword)

    try:
        while queue and not is_limit_reached() and not stopped():
            keyword = queue.popleft()
            keyword_norm = normalize_keyword(keyword)
            if keyword_norm in searched:
                continue

            searched.add(keyword_norm)

            try:
                keyword_list = get_keyword_search_volume(keyword)
            except Exception as e:
                log(f"조회 실패 ({keyword}): {e}")
                continue

            if not keyword_list:
                continue

            result = find_keyword_result(keyword, keyword_list)
            if result:
                row = extract_volume_row(keyword, result)
                records.append(row)
                emit_row(row)
                time.sleep(0.1)

            if is_limit_reached():
                break

            for item in keyword_list:
                rel_keyword = item.get("relKeyword", "").strip()
                if not rel_keyword:
                    continue
                if normalize_keyword(rel_keyword) not in searched:
                    queue.append(rel_keyword)

            time.sleep(0.1)
    except KeyboardInterrupt:
        log("조회가 중단되었습니다. 지금까지 수집한 결과를 저장합니다.")

    return records


def main() -> None:
    if len(sys.argv) > 1:
        seed_keyword = " ".join(sys.argv[1:]).strip()
    else:
        seed_keyword = input("검색할 키워드를 입력하세요: ").strip()

    if not seed_keyword:
        print("키워드를 입력해 주세요.")
        sys.exit(1)

    max_count = ask_keyword_count()
    count_label = "무제한" if max_count == 0 else f"{max_count}개"

    print(f"\n'{seed_keyword}' 키워드로 조회를 시작합니다. (조회 개수: {count_label})\n")

    records = crawl_keywords(seed_keyword, max_count)

    if not records:
        sys.exit(0)

    excel_path = f"{sanitize_filename(seed_keyword)}.xlsx"
    save_to_excel(excel_path, records)
    print(f"\n총 {len(records)}개 키워드를 '{excel_path}' 파일에 저장했습니다.")


if __name__ == "__main__":
    main()
