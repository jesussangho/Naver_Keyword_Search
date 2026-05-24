"""
네이버 검색 API - 블로그 검색 결과의 문서수(total) 조회
"""
import json
import os
import sys
import urllib.parse
import urllib.request

CLIENT_ID = os.environ.get("NAVER_CLIENT_ID", "OmIWV_6SWBTRPhDsMhmo")
CLIENT_SECRET = os.environ.get("NAVER_CLIENT_SECRET", "qWj8puJFp_")


def get_blog_document_count(query: str) -> int:
    enc_text = urllib.parse.quote(query)
    url = "https://openapi.naver.com/v1/search/blog?query=" + enc_text + "&display=1"
    request = urllib.request.Request(url)
    request.add_header("X-Naver-Client-Id", CLIENT_ID)
    request.add_header("X-Naver-Client-Secret", CLIENT_SECRET)

    response = urllib.request.urlopen(request)
    rescode = response.getcode()
    if rescode != 200:
        raise RuntimeError("Error Code: " + str(rescode))

    body = json.loads(response.read().decode("utf-8"))
    return int(body.get("total", 0))


def main() -> None:
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:]).strip()
    else:
        query = input("검색할 키워드를 입력하세요: ").strip()

    if not query:
        print("키워드를 입력해 주세요.")
        sys.exit(1)

    try:
        total = get_blog_document_count(query)
    except Exception as e:
        print("조회 실패:", e)
        sys.exit(1)

    print("키워드:", query)
    print("문서수:", f"{total:,}")


if __name__ == "__main__":
    main()
