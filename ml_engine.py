import numpy as np
import pandas as pd
from collections import Counter
from sklearn.ensemble import RandomForestClassifier
import random


def _numbers_to_features(draws, window=10):
    """최근 window 회차를 기반으로 각 번호(1~45)의 출현 빈도 피처를 생성한다."""
    features = []
    labels = []
    for i in range(window, len(draws)):
        recent = draws[i - window:i]
        freq = Counter()
        for d in recent:
            for n in d["numbers"]:
                freq[n] += 1
        row = [freq.get(n, 0) / window for n in range(1, 46)]
        features.append(row)
        label = [1 if n in draws[i]["numbers"] else 0 for n in range(1, 46)]
        labels.append(label)
    return np.array(features), np.array(labels)


# ── 전략 1: 빈도 분석 ──

def strategy_frequency(draws, recent_n=50):
    """최근 N회차 출현 빈도 기반 가중 랜덤 선택."""
    recent = draws[-recent_n:]
    freq = Counter()
    for d in recent:
        for n in d["numbers"]:
            freq[n] += 1
    weights = np.array([freq.get(n, 0) + 1 for n in range(1, 46)], dtype=float)
    weights /= weights.sum()
    chosen = set()
    while len(chosen) < 6:
        pick = np.random.choice(range(1, 46), p=weights)
        chosen.add(int(pick))
    return sorted(chosen)


# ── 전략 2: 랜덤 포레스트 ──

def strategy_random_forest(draws):
    """RandomForest로 각 번호의 출현 확률을 예측하여 상위 확률 기반 선택."""
    if len(draws) < 30:
        return strategy_frequency(draws)

    X, Y = _numbers_to_features(draws, window=10)
    if len(X) < 10:
        return strategy_frequency(draws)

    probs = np.zeros(45)
    for num_idx in range(45):
        clf = RandomForestClassifier(n_estimators=50, max_depth=5, random_state=42)
        clf.fit(X[:-1], Y[:-1, num_idx])
        probs[num_idx] = clf.predict_proba(X[-1:])[:, -1][0] if len(clf.classes_) > 1 else 0.02

    probs += 0.01
    probs /= probs.sum()
    chosen = set()
    while len(chosen) < 6:
        pick = np.random.choice(range(1, 46), p=probs)
        chosen.add(int(pick))
    return sorted(chosen)


# ── 전략 3: 패턴 분석 ──

def strategy_pattern(draws, recent_n=100):
    """연속번호, 홀짝 비율, 끝수 분포 등 패턴을 반영한 선택."""
    recent = draws[-recent_n:]

    # 홀짝 비율 분석 (평균적으로 3:3 또는 4:2)
    odd_counts = [sum(1 for n in d["numbers"] if n % 2 == 1) for d in recent]
    avg_odd = round(np.mean(odd_counts))
    target_odd = max(2, min(4, avg_odd))

    # 끝수 분포 분석
    ending_freq = Counter()
    for d in recent:
        for n in d["numbers"]:
            ending_freq[n % 10] += 1

    # 번호별 가중치: 빈도 + 끝수 다양성 보너스
    freq = Counter()
    for d in recent:
        for n in d["numbers"]:
            freq[n] += 1

    candidates = list(range(1, 46))
    random.shuffle(candidates)

    chosen = []
    used_endings = set()
    for _ in range(100):
        if len(chosen) == 6:
            break
        random.shuffle(candidates)
        for n in candidates:
            if n in chosen:
                continue
            ending = n % 10
            # 끝수 다양성 유지 (같은 끝수 최대 2개)
            if sum(1 for c in chosen if c % 10 == ending) >= 2:
                continue
            chosen.append(n)
            if len(chosen) == 6:
                break

    # 홀짝 비율 조정
    odd_in_chosen = sum(1 for n in chosen if n % 2 == 1)
    attempts = 0
    while odd_in_chosen != target_odd and attempts < 50:
        idx = random.randint(0, 5)
        new_num = random.randint(1, 45)
        if new_num in chosen:
            continue
        old_odd = chosen[idx] % 2 == 1
        new_odd = new_num % 2 == 1
        if odd_in_chosen > target_odd and old_odd and not new_odd:
            chosen[idx] = new_num
            odd_in_chosen -= 1
        elif odd_in_chosen < target_odd and not old_odd and new_odd:
            chosen[idx] = new_num
            odd_in_chosen += 1
        attempts += 1

    return sorted(chosen)


# ── 전략 4: 구간 분석 ──

def strategy_zone(draws, recent_n=50):
    """1~45를 구간별로 균형 배분하여 선택."""
    zones = [(1, 10), (11, 20), (21, 30), (31, 40), (41, 45)]
    zone_weights = [2, 2, 1, 1, 0]  # 기본: 각 구간에서 뽑을 개수 후보

    # 최근 데이터로 구간별 빈도 분석
    recent = draws[-recent_n:]
    zone_freq = [0] * 5
    for d in recent:
        for n in d["numbers"]:
            for zi, (lo, hi) in enumerate(zones):
                if lo <= n <= hi:
                    zone_freq[zi] += 1
                    break

    # 구간별 1~2개씩 배분 (총 6개)
    distribution = []
    remaining = 6
    for zi in range(5):
        count = min(2, remaining, zones[zi][1] - zones[zi][0] + 1)
        if remaining - count < (4 - zi) * 0:
            count = 1
        if zi == 4:
            count = remaining
        distribution.append(min(count, remaining))
        remaining -= distribution[-1]

    # 각 구간별 빈도 가중 선택
    chosen = []
    for zi, (lo, hi) in enumerate(zones):
        n_pick = distribution[zi]
        if n_pick <= 0:
            continue
        zone_nums = list(range(lo, hi + 1))
        freq = Counter()
        for d in recent:
            for n in d["numbers"]:
                if lo <= n <= hi:
                    freq[n] += 1
        weights = np.array([freq.get(n, 0) + 1 for n in zone_nums], dtype=float)
        weights /= weights.sum()
        picks = np.random.choice(zone_nums, size=min(n_pick, len(zone_nums)), replace=False, p=weights)
        chosen.extend(int(p) for p in picks)

    # 부족하면 랜덤 보충
    all_nums = set(range(1, 46)) - set(chosen)
    while len(chosen) < 6:
        chosen.append(random.choice(list(all_nums - set(chosen))))

    return sorted(chosen[:6])


# ── 전략 5: 합계 최적화 ──

def strategy_sum_optimize(draws, recent_n=100):
    """당첨번호 합계 범위(100~175) 내에서 선택."""
    recent = draws[-recent_n:]
    sums = [sum(d["numbers"]) for d in recent]
    mean_sum = np.mean(sums)
    std_sum = np.std(sums)
    target_low = max(21, int(mean_sum - std_sum))
    target_high = min(255, int(mean_sum + std_sum))

    freq = Counter()
    for d in recent:
        for n in d["numbers"]:
            freq[n] += 1

    for _ in range(1000):
        nums = sorted(random.sample(range(1, 46), 6))
        s = sum(nums)
        if target_low <= s <= target_high:
            return nums

    return sorted(random.sample(range(1, 46), 6))


# ── 앙상블 ──

def generate_ensemble(draws, n_sets=5):
    """5가지 전략을 앙상블하여 최종 번호를 생성한다."""
    strategies = [
        ("빈도 분석", strategy_frequency),
        ("랜덤 포레스트", strategy_random_forest),
        ("패턴 분석", strategy_pattern),
        ("구간 분석", strategy_zone),
        ("합계 최적화", strategy_sum_optimize),
    ]

    # 각 전략에서 번호별 점수 집계
    scores = Counter()
    strategy_results = {}

    for name, func in strategies:
        try:
            nums = func(draws)
            strategy_results[name] = nums
            for n in nums:
                scores[n] += 1
        except Exception as e:
            print(f"전략 '{name}' 실패: {e}")
            strategy_results[name] = []

    # 점수 기반 가중 랜덤으로 n_sets 세트 생성
    results = []
    for _ in range(n_sets):
        weights = np.array([scores.get(n, 0) + 0.5 for n in range(1, 46)], dtype=float)
        weights /= weights.sum()
        chosen = set()
        while len(chosen) < 6:
            pick = np.random.choice(range(1, 46), p=weights)
            chosen.add(int(pick))
        results.append(sorted(chosen))

    return results, strategy_results


def generate_by_strategy(draws, strategy_name):
    """특정 전략으로 번호를 생성한다."""
    strategy_map = {
        "frequency": strategy_frequency,
        "random_forest": strategy_random_forest,
        "pattern": strategy_pattern,
        "zone": strategy_zone,
        "sum_optimize": strategy_sum_optimize,
    }
    func = strategy_map.get(strategy_name)
    if func:
        return func(draws)
    return sorted(random.sample(range(1, 46), 6))


def get_statistics(draws):
    """통계 데이터를 계산한다."""
    if not draws:
        return {}

    all_numbers = []
    for d in draws:
        all_numbers.extend(d["numbers"])

    freq = Counter(all_numbers)
    total = len(draws)

    # 번호별 출현 횟수
    number_freq = {n: freq.get(n, 0) for n in range(1, 46)}

    # 최근 20회 기준 핫/콜드 번호
    recent = draws[-20:]
    recent_freq = Counter()
    for d in recent:
        for n in d["numbers"]:
            recent_freq[n] += 1

    hot_numbers = [n for n, _ in recent_freq.most_common(10)]
    cold_numbers = [n for n in range(1, 46) if recent_freq.get(n, 0) == 0]
    if not cold_numbers:
        cold_numbers = [n for n, _ in recent_freq.most_common()[:-11:-1]]

    # 홀짝 비율
    odd_counts = [sum(1 for n in d["numbers"] if n % 2 == 1) for d in recent]
    avg_odd = round(np.mean(odd_counts), 1)

    # 합계 통계
    sums = [sum(d["numbers"]) for d in draws]
    recent_sums = [sum(d["numbers"]) for d in recent]

    # 번호별 미출현 회차 수
    last_seen = {}
    for i, d in enumerate(draws):
        for n in d["numbers"]:
            last_seen[n] = i
    latest_idx = len(draws) - 1
    absence = {n: latest_idx - last_seen.get(n, -1) for n in range(1, 46)}

    return {
        "total_draws": total,
        "number_freq": number_freq,
        "hot_numbers": hot_numbers[:10],
        "cold_numbers": cold_numbers[:10],
        "avg_odd_count": avg_odd,
        "sum_stats": {
            "mean": round(np.mean(sums), 1),
            "std": round(np.std(sums), 1),
            "recent_mean": round(np.mean(recent_sums), 1),
        },
        "absence": absence,
        "latest_draw": draws[-1] if draws else None,
    }
