from flask import Flask, render_template, jsonify, request
from data_fetcher import fetch_all_data, get_data
from ml_engine import generate_ensemble, generate_by_strategy, get_statistics

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/generate")
def api_generate():
    strategy = request.args.get("strategy", "ensemble")
    n_sets = int(request.args.get("sets", 5))
    n_sets = max(1, min(10, n_sets))

    draws = get_data()
    if not draws:
        return jsonify({"error": "데이터가 없습니다. 먼저 데이터를 갱신해주세요."}), 400

    if strategy == "ensemble":
        results, strategy_details = generate_ensemble(draws, n_sets=n_sets)
        return jsonify({
            "numbers": results,
            "strategy": "앙상블 (5가지 전략 종합)",
            "details": {k: v for k, v in strategy_details.items()},
        })
    else:
        results = []
        for _ in range(n_sets):
            results.append(generate_by_strategy(draws, strategy))
        strategy_names = {
            "frequency": "빈도 분석",
            "random_forest": "랜덤 포레스트",
            "pattern": "패턴 분석",
            "zone": "구간 분석",
            "sum_optimize": "합계 최적화",
        }
        return jsonify({
            "numbers": results,
            "strategy": strategy_names.get(strategy, strategy),
        })


@app.route("/api/stats")
def api_stats():
    draws = get_data()
    if not draws:
        return jsonify({"error": "데이터가 없습니다."}), 400
    stats = get_statistics(draws)
    return jsonify(stats)


@app.route("/api/draws")
def api_draws():
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 10))
    search = request.args.get("search", "").strip()

    draws = get_data()
    if not draws:
        return jsonify({"error": "데이터가 없습니다."}), 400

    # 최신순 정렬
    draws = sorted(draws, key=lambda x: x["draw_no"], reverse=True)

    # 회차 검색
    if search:
        try:
            draw_no = int(search)
            draws = [d for d in draws if d["draw_no"] == draw_no]
        except ValueError:
            draws = []

    total = len(draws)
    start = (page - 1) * per_page
    end = start + per_page
    page_draws = draws[start:end]

    return jsonify({
        "draws": page_draws,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page,
    })


@app.route("/api/fetch-data")
def api_fetch_data():
    try:
        data = fetch_all_data()
        return jsonify({
            "success": True,
            "total_draws": len(data),
            "latest": data[-1] if data else None,
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)
