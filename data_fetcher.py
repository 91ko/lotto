import json
import os
import subprocess
import sys
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
CACHE_FILE = os.path.join(DATA_DIR, "lotto_data.json")

# 로또 1회차 추첨일: 2002-12-07
FIRST_DRAW_DATE = datetime(2002, 12, 7)


def estimate_latest_draw():
    """현재 날짜 기준으로 최신 회차 번호를 추정한다."""
    today = datetime.now()
    days_since_first = (today - FIRST_DRAW_DATE).days
    return days_since_first // 7 + 1


def load_cached_data():
    """캐시된 데이터를 로드한다."""
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_cached_data(data):
    """데이터를 JSON 파일에 캐싱한다."""
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def fetch_all_data(progress_callback=None):
    """최신 데이터를 가져온다. 로컬에서는 scrape_data.py 실행, Vercel에서는 캐시만 반환."""
    # Vercel 환경에서는 스크래핑 불가 (읽기 전용 파일시스템)
    if os.environ.get("VERCEL"):
        return load_cached_data()

    scraper_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scrape_data.py")
    try:
        result = subprocess.run(
            [sys.executable, scraper_path],
            capture_output=True, text=True, timeout=300, encoding="utf-8", errors="replace"
        )
        print(result.stdout)
        if result.returncode != 0:
            print(f"스크래퍼 오류: {result.stderr}")
    except Exception as e:
        print(f"데이터 갱신 실패: {e}")

    return load_cached_data()


def get_data():
    """캐시된 데이터를 반환하거나, 없으면 전체 데이터를 가져온다."""
    cached = load_cached_data()
    if cached:
        return cached
    return fetch_all_data()
