"""동행복권 사이트에서 전체 로또 당첨번호를 수집하는 스크립트."""
import undetected_chromedriver as uc
import time
import json
import re
import os

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
CACHE_FILE = os.path.join(DATA_DIR, "lotto_data.json")
BATCH_SIZE = 100  # 한 번에 조회할 회차 수


def scrape_all():
    print("Chrome 브라우저 시작...")
    driver = uc.Chrome(version_main=147)

    try:
        driver.get("https://www.dhlottery.co.kr/lt645/result")
        time.sleep(5)
        print(f"페이지 로드 완료: {driver.current_url}")

        # 최신 회차 번호 확인
        latest = driver.execute_script(r'''
            var s = document.getElementById("srchStrLtEpsd");
            if(s && s.options.length > 1) return parseInt(s.options[1].value);
            return 0;
        ''')
        print(f"최신 회차: {latest}")

        if latest == 0:
            print("회차 정보를 가져올 수 없습니다.")
            return

        # 기존 캐시 로드
        existing = {}
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                for item in json.load(f):
                    existing[item["draw_no"]] = item

        start = 1
        while start <= latest:
            end = min(start + BATCH_SIZE - 1, latest)

            # 이미 전부 캐시된 범위 스킵
            if all(i in existing for i in range(start, end + 1)):
                print(f"  {start}~{end}회 (캐시됨)")
                start = end + 1
                continue

            print(f"  {start}~{end}회 조회 중...", end=" ", flush=True)

            # select 설정 + 조회 버튼 클릭
            driver.execute_script(r'''
                document.getElementById('srchStrLtEpsd').value = arguments[0];
                document.getElementById('srchEndLtEpsd').value = arguments[1];
                var btns = document.querySelectorAll('.btn-sm-rec');
                for(var i=0; i<btns.length; i++) { btns[i].click(); break; }
            ''', str(start), str(end))
            time.sleep(2)

            # 테이블에서 데이터 추출
            rows_json = driver.execute_script(r'''
                var rows = document.querySelectorAll('.tbl-tr.tbody');
                var result = [];
                for(var i=0; i<rows.length; i++) {
                    var row = rows[i];

                    // 회차
                    var roundTd = row.querySelector('.td-round');
                    if(!roundTd) continue;
                    var m = roundTd.textContent.match(/(\d+)/);
                    if(!m) continue;
                    var drawNo = parseInt(m[1]);

                    // 당첨번호
                    var numTd = row.querySelector('.td-num');
                    var balls = numTd ? numTd.querySelectorAll('.result-ball') : [];
                    var nums = [];
                    for(var j=0; j<balls.length; j++) {
                        var t = balls[j].textContent.trim();
                        if(/^\d+$/.test(t)) nums.push(parseInt(t));
                    }

                    // 보너스
                    var bonusTd = row.querySelector('.td-bonus');
                    var bonusBalls = bonusTd ? bonusTd.querySelectorAll('.result-ball') : [];
                    var bonus = 0;
                    for(var j=0; j<bonusBalls.length; j++) {
                        var t = bonusBalls[j].textContent.trim();
                        if(/^\d+$/.test(t)) bonus = parseInt(t);
                    }

                    if(nums.length === 6) {
                        nums.sort(function(a,b){return a-b});
                        result.push({draw_no: drawNo, numbers: nums, bonus: bonus});
                    }
                }
                return JSON.stringify(result);
            ''')

            batch = json.loads(rows_json)
            count = 0
            for item in batch:
                if item["draw_no"] not in existing:
                    # 날짜 계산 (1회차: 2002-12-07, 매주 토요일)
                    from datetime import datetime, timedelta
                    draw_date = datetime(2002, 12, 7) + timedelta(weeks=item["draw_no"] - 1)
                    item["date"] = draw_date.strftime("%Y-%m-%d")
                    existing[item["draw_no"]] = item
                    count += 1
            print(f"{count}건 수집")

            time.sleep(0.5)
            start = end + 1

        # 전체 데이터 정렬 및 저장
        all_data = sorted(existing.values(), key=lambda x: x["draw_no"])
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(all_data, f, ensure_ascii=False, indent=2)

        print(f"\n완료! 총 {len(all_data)}회차 저장됨")
        if all_data:
            print(f"최신: {all_data[-1]['draw_no']}회 - {all_data[-1]['numbers']} + {all_data[-1]['bonus']}")

    finally:
        try:
            driver.quit()
        except Exception:
            pass


if __name__ == "__main__":
    scrape_all()
