// ── DOM 요소 ──
const $ = (sel) => document.querySelector(sel);
const btnGenerate = $("#btn-generate");
const btnStats = $("#btn-stats");
const btnFetch = $("#btn-fetch");
const loading = $("#loading");
const resultsSection = $("#results");
const numberSets = $("#number-sets");
const resultStrategy = $("#result-strategy");
const strategyDetails = $("#strategy-details");
const strategyList = $("#strategy-list");
const statsPanel = $("#stats-panel");
const historyList = $("#history-list");

// ── 이력 저장 ──
let history = JSON.parse(localStorage.getItem("lotto_history") || "[]");

// ── 유틸 ──
function getBallClass(num) {
    if (num <= 10) return "range-1";
    if (num <= 20) return "range-2";
    if (num <= 30) return "range-3";
    if (num <= 40) return "range-4";
    return "range-5";
}

function createBall(num, delay = 0, small = false) {
    const ball = document.createElement("div");
    ball.className = `ball ${getBallClass(num)}${small ? " small" : ""}`;
    ball.textContent = num;
    ball.style.animationDelay = `${delay}s`;
    return ball;
}

function createBallContainer(numbers, small = false) {
    const container = document.createElement("div");
    container.className = "ball-container";
    numbers.forEach((n, i) => {
        container.appendChild(createBall(n, i * 0.08, small));
    });
    return container;
}

function showLoading() {
    loading.classList.remove("hidden");
    btnGenerate.disabled = true;
}

function hideLoading() {
    loading.classList.add("hidden");
    btnGenerate.disabled = false;
}

function formatTime(date) {
    const h = date.getHours().toString().padStart(2, "0");
    const m = date.getMinutes().toString().padStart(2, "0");
    const s = date.getSeconds().toString().padStart(2, "0");
    return `${h}:${m}:${s}`;
}

// ── 번호 생성 ──
btnGenerate.addEventListener("click", async () => {
    const strategy = $("#strategy").value;
    const sets = $("#sets").value;

    showLoading();
    resultsSection.classList.add("hidden");
    strategyDetails.classList.add("hidden");

    try {
        const resp = await fetch(`/api/generate?strategy=${strategy}&sets=${sets}`);
        const data = await resp.json();

        if (data.error) {
            alert(data.error);
            hideLoading();
            return;
        }

        // 결과 표시
        numberSets.innerHTML = "";
        resultStrategy.textContent = data.strategy;

        data.numbers.forEach((nums, idx) => {
            const setDiv = document.createElement("div");
            setDiv.className = "number-set";
            setDiv.style.animationDelay = `${idx * 0.1}s`;

            const label = document.createElement("span");
            label.className = "set-label";
            label.textContent = String.fromCharCode(65 + idx);

            setDiv.appendChild(label);
            setDiv.appendChild(createBallContainer(nums));
            numberSets.appendChild(setDiv);
        });

        resultsSection.classList.remove("hidden");

        // 앙상블 전략 상세
        if (data.details) {
            strategyList.innerHTML = "";
            for (const [name, nums] of Object.entries(data.details)) {
                if (!nums || nums.length === 0) continue;
                const item = document.createElement("div");
                item.className = "strategy-item";

                const nameSpan = document.createElement("span");
                nameSpan.className = "name";
                nameSpan.textContent = name;

                item.appendChild(nameSpan);
                item.appendChild(createBallContainer(nums, true));
                strategyList.appendChild(item);
            }
            strategyDetails.classList.remove("hidden");
        }

        // 이력 저장
        const entry = {
            time: new Date().toISOString(),
            strategy: data.strategy,
            numbers: data.numbers,
        };
        history.unshift(entry);
        if (history.length > 50) history = history.slice(0, 50);
        localStorage.setItem("lotto_history", JSON.stringify(history));
        renderHistory();

    } catch (err) {
        alert("번호 생성 실패: " + err.message);
    }

    hideLoading();
});

// ── 통계 ──
btnStats.addEventListener("click", async () => {
    if (!statsPanel.classList.contains("hidden")) {
        statsPanel.classList.add("hidden");
        return;
    }

    showLoading();

    try {
        const resp = await fetch("/api/stats");
        const data = await resp.json();

        if (data.error) {
            alert(data.error);
            hideLoading();
            return;
        }

        // 최신 당첨번호
        const latestDiv = $("#latest-draw");
        if (data.latest_draw) {
            latestDiv.innerHTML = `
                <div style="margin-bottom:0.5rem; font-size:0.85rem; color:var(--text-dim)">
                    ${data.latest_draw.draw_no}회 (${data.latest_draw.date})
                </div>
            `;
            latestDiv.appendChild(createBallContainer(data.latest_draw.numbers, true));
            const bonusBall = createBall(data.latest_draw.bonus, 0.5, true);
            bonusBall.style.marginLeft = "8px";
            bonusBall.style.opacity = "0.7";
            bonusBall.title = "보너스";
            latestDiv.querySelector(".ball-container").appendChild(bonusBall);
        }

        // 기본 통계
        $("#basic-stats").innerHTML = `
            <div class="stat-row"><span class="label">총 회차</span><span>${data.total_draws}회</span></div>
            <div class="stat-row"><span class="label">합계 평균</span><span>${data.sum_stats.mean}</span></div>
            <div class="stat-row"><span class="label">합계 표준편차</span><span>${data.sum_stats.std}</span></div>
            <div class="stat-row"><span class="label">최근 합계 평균</span><span>${data.sum_stats.recent_mean}</span></div>
            <div class="stat-row"><span class="label">평균 홀수 개수</span><span>${data.avg_odd_count}개</span></div>
        `;

        // 핫 번호
        const hotDiv = $("#hot-numbers");
        hotDiv.innerHTML = "";
        hotDiv.appendChild(createBallContainer(data.hot_numbers, true));

        // 콜드 번호
        const coldDiv = $("#cold-numbers");
        coldDiv.innerHTML = "";
        coldDiv.appendChild(createBallContainer(data.cold_numbers, true));

        // 빈도 차트
        const freqChart = $("#freq-chart");
        const freqValues = Object.values(data.number_freq);
        const maxFreq = Math.max(...freqValues);

        let chartHTML = '<div class="freq-bar-chart">';
        for (let n = 1; n <= 45; n++) {
            const freq = data.number_freq[n] || 0;
            const height = (freq / maxFreq) * 100;
            chartHTML += `<div class="freq-bar" style="height:${height}%">
                <span class="tooltip">${n}번: ${freq}회</span>
            </div>`;
        }
        chartHTML += "</div>";

        chartHTML += '<div class="freq-labels">';
        for (let n = 1; n <= 45; n++) {
            chartHTML += `<span>${n % 5 === 0 || n === 1 ? n : ""}</span>`;
        }
        chartHTML += "</div>";

        freqChart.innerHTML = chartHTML;

        statsPanel.classList.remove("hidden");

    } catch (err) {
        alert("통계 로드 실패: " + err.message);
    }

    hideLoading();
});

// ── 데이터 갱신 ──
btnFetch.addEventListener("click", async () => {
    btnFetch.disabled = true;
    btnFetch.textContent = "갱신 중...";

    try {
        const resp = await fetch("/api/fetch-data");
        const data = await resp.json();

        if (data.error) {
            alert("데이터 갱신 실패: " + data.error);
        } else {
            const latest = data.latest;
            alert(`데이터 갱신 완료!\n총 ${data.total_draws}회차\n최신: ${latest.draw_no}회 (${latest.date})`);
        }
    } catch (err) {
        alert("데이터 갱신 실패: " + err.message);
    }

    btnFetch.disabled = false;
    btnFetch.textContent = "데이터 갱신";
});

// ── 역대 당첨번호 ──
const btnDraws = $("#btn-draws");
const drawsPanel = $("#draws-panel");
let currentDrawPage = 1;

btnDraws.addEventListener("click", () => {
    if (!drawsPanel.classList.contains("hidden")) {
        drawsPanel.classList.add("hidden");
        return;
    }
    currentDrawPage = 1;
    $("#draw-search").value = "";
    loadDraws(1, "");
    drawsPanel.classList.remove("hidden");
});

$("#btn-draw-search").addEventListener("click", () => {
    const search = $("#draw-search").value.trim();
    currentDrawPage = 1;
    loadDraws(1, search);
});

$("#draw-search").addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
        const search = $("#draw-search").value.trim();
        currentDrawPage = 1;
        loadDraws(1, search);
    }
});

$("#btn-draw-reset").addEventListener("click", () => {
    $("#draw-search").value = "";
    currentDrawPage = 1;
    loadDraws(1, "");
});

async function loadDraws(page, search) {
    const list = $("#draws-list");
    const pager = $("#draws-pager");
    list.innerHTML = '<div class="loading"><div class="spinner"></div></div>';
    pager.innerHTML = "";

    try {
        const params = new URLSearchParams({ page, per_page: 10 });
        if (search) params.set("search", search);

        const resp = await fetch(`/api/draws?${params}`);
        const data = await resp.json();

        if (data.error) {
            list.innerHTML = `<p class="empty-msg">${data.error}</p>`;
            return;
        }

        if (data.draws.length === 0) {
            list.innerHTML = '<p class="empty-msg">검색 결과가 없습니다.</p>';
            return;
        }

        list.innerHTML = "";
        data.draws.forEach((draw) => {
            const row = document.createElement("div");
            row.className = "draw-row";

            const info = document.createElement("div");
            info.className = "draw-info";
            info.innerHTML = `<div class="draw-no">${draw.draw_no}회</div><div class="draw-date">${draw.date}</div>`;

            const ballWrap = createBallContainer(draw.numbers, true);

            // 보너스 구분자 + 공
            const sep = document.createElement("span");
            sep.className = "bonus-sep";
            sep.textContent = "+";
            ballWrap.appendChild(sep);

            const bonusBall = createBall(draw.bonus, 0, true);
            bonusBall.style.opacity = "0.7";
            bonusBall.title = "보너스";
            ballWrap.appendChild(bonusBall);

            row.appendChild(info);
            row.appendChild(ballWrap);
            list.appendChild(row);
        });

        // 페이저
        if (data.total_pages > 1 && !search) {
            renderDrawsPager(data.page, data.total_pages, search);
        }

    } catch (err) {
        list.innerHTML = `<p class="empty-msg">로드 실패: ${err.message}</p>`;
    }
}

function renderDrawsPager(current, totalPages, search) {
    const pager = $("#draws-pager");
    pager.innerHTML = "";

    const prevBtn = document.createElement("button");
    prevBtn.textContent = "이전";
    prevBtn.disabled = current <= 1;
    prevBtn.addEventListener("click", () => { currentDrawPage--; loadDraws(currentDrawPage, search); });
    pager.appendChild(prevBtn);

    // 페이지 번호들
    let startPage = Math.max(1, current - 2);
    let endPage = Math.min(totalPages, startPage + 4);
    if (endPage - startPage < 4) startPage = Math.max(1, endPage - 4);

    for (let p = startPage; p <= endPage; p++) {
        const btn = document.createElement("button");
        btn.textContent = p;
        if (p === current) btn.className = "active";
        btn.addEventListener("click", () => { currentDrawPage = p; loadDraws(p, search); });
        pager.appendChild(btn);
    }

    const info = document.createElement("span");
    info.className = "page-info";
    info.textContent = `/ ${totalPages}`;
    pager.appendChild(info);

    const nextBtn = document.createElement("button");
    nextBtn.textContent = "다음";
    nextBtn.disabled = current >= totalPages;
    nextBtn.addEventListener("click", () => { currentDrawPage++; loadDraws(currentDrawPage, search); });
    pager.appendChild(nextBtn);
}

// ── 이력 렌더링 ──
function renderHistory() {
    if (history.length === 0) {
        historyList.innerHTML = '<p class="empty-msg">아직 생성된 번호가 없습니다.</p>';
        return;
    }

    historyList.innerHTML = "";
    history.slice(0, 10).forEach((entry) => {
        const item = document.createElement("div");
        item.className = "history-item";

        const time = new Date(entry.time);
        const meta = document.createElement("div");
        meta.className = "history-meta";
        meta.innerHTML = `<span>${time.toLocaleDateString("ko-KR")} ${formatTime(time)}</span><span>${entry.strategy}</span>`;
        item.appendChild(meta);

        entry.numbers.forEach((nums) => {
            item.appendChild(createBallContainer(nums, true));
        });

        historyList.appendChild(item);
    });
}

// 초기 렌더링
renderHistory();
