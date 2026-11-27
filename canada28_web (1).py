#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
加拿大28 杀组合提示 - 网页版（自动刷新）
运行后访问 http://127.0.0.1:5000
"""

from flask import Flask, render_template_string
import requests
from collections import Counter
import threading
import time
import json
import os

app = Flask(__name__)

API_BASE = "https://pc28.world/api/v1"
HEADERS = {"User-Agent": "Canada28-Web/1.0"}
BET_AMOUNT = 100
HISTORY_FILE = "history.json"

def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return []

def save_history(history):
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except:
        pass

cache = {
    "latest": None,
    "kill": None,
    "bets": [],
    "counts": {},
    "sums": {},
    "update_time": "",
    "last_period": None,
    "pending_kill": None,
    "history": load_history()
}

HTML = """
<!DOCTYPE html>
<html lang="zh">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>加拿大28 杀组合提示</title>
    <meta http-equiv="refresh" content="15">
    <style>
        * { box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: #f5f5f5; margin: 0; padding: 12px; 
        }
        .container { max-width: 420px; margin: 0 auto; }
        .card {
            background: white; border-radius: 12px; padding: 16px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08); margin-bottom: 12px;
        }
        .period { font-size: 18px; font-weight: bold; text-align: center; margin-bottom: 12px; }
        .countdown { text-align: center; margin: 10px 0; font-size: 15px; }
        .cd-box { 
            display: inline-block; background: #e74c3c; color: white; 
            font-size: 28px; font-weight: bold; padding: 8px 16px; 
            border-radius: 8px; margin: 0 4px;
        }
        .numbers { display: flex; justify-content: center; align-items: center; gap: 8px; margin: 16px 0; }
        .num-box { 
            width: 48px; height: 48px; border-radius: 8px; 
            display: flex; align-items: center; justify-content: center;
            font-size: 22px; font-weight: bold; color: white;
        }
        .n1 { background: #1abc9c; }
        .n2 { background: #1abc9c; }
        .n3 { background: #1abc9c; }
        .sum { background: #27ae60; }
        .tag { 
            display: inline-block; padding: 6px 12px; border-radius: 6px; 
            color: white; font-weight: bold; margin: 0 4px; font-size: 16px;
        }
        .big { background: #e74c3c; }
        .small { background: #3498db; }
        .odd { background: #e74c3c; }
        .even { background: #3498db; }
        .kill-box {
            text-align: center; background: #fff0f0; border: 2px solid #e74c3c;
            border-radius: 10px; padding: 12px; margin: 12px 0;
        }
        .kill-title { color: #e74c3c; font-size: 13px; }
        .kill-name { font-size: 24px; font-weight: bold; color: #e74c3c; }
        .stats { margin: 10px 0; }
        .stat-title { text-align: center; color: #666; font-size: 13px; margin-bottom: 6px; }
        .stat-row { display: flex; justify-content: space-between; padding: 5px 0; border-bottom: 1px solid #eee; font-size: 14px; }
        .stat-num { font-weight: bold; color: #e74c3c; }
        .sum-grid { display: grid; grid-template-columns: repeat(7, 1fr); gap: 4px; margin: 8px 0; font-size: 12px; }
        .sum-item { text-align: center; background: #f8f8f8; border-radius: 4px; padding: 4px 2px; }
        .sum-val { font-weight: bold; }
        .sum-cnt { color: #e74c3c; font-size: 11px; }
        .bets { text-align: center; margin-top: 12px; }
        .bet {
            display: inline-block; background: #27ae60; color: white;
            padding: 10px 22px; margin: 4px; border-radius: 6px;
            font-size: 16px; font-weight: bold;
        }
        .footer { text-align: center; color: #999; font-size: 11px; margin-top: 12px; }
        .history { margin-top: 10px; font-size: 13px; }
        .hist-row { display: flex; justify-content: space-between; padding: 4px 0; border-bottom: 1px solid #eee; }
        .win { color: #27ae60; font-weight: bold; }
        .lose { color: #e74c3c; font-weight: bold; }
    </style>
</head>
<body>
    <div class="container">
        {% if latest %}
        <div class="card">
            <div class="period">最新：{{ latest.draw.nbr }} 期</div>
            <div class="countdown">
                下一期：
                <span class="cd-box" id="min">{{ '%02d' % (latest.countdown.seconds // 60) }}</span>分
                <span class="cd-box" id="sec">{{ '%02d' % (latest.countdown.seconds % 60) }}</span>秒
            </div>
            <script>
            (function(){
                let total = {{ latest.countdown.seconds }};
                function tick(){
                    if(total <= 0){ location.reload(); return; }
                    total--;
                    let m = Math.floor(total / 60);
                    let s = total % 60;
                    document.getElementById('min').textContent = m.toString().padStart(2,'0');
                    document.getElementById('sec').textContent = s.toString().padStart(2,'0');
                }
                setInterval(tick, 1000);
            })();
            </script>
            <div class="numbers">
                <div class="num-box n1">{{ latest.draw.n1 }}</div>
                <span>+</span>
                <div class="num-box n2">{{ latest.draw.n2 }}</div>
                <span>+</span>
                <div class="num-box n3">{{ latest.draw.n3 }}</div>
                <span>=</span>
                <div class="num-box sum">{{ latest.draw.sum }}</div>
                <span class="tag {% if latest.draw.big %}big{% else %}small{% endif %}">{{ '大' if latest.draw.big else '小' }}</span>
                <span class="tag {% if latest.draw.odd %}odd{% else %}even{% endif %}">{{ '单' if latest.draw.odd else '双' }}</span>
            </div>
        </div>
        {% else %}
        <div class="card" style="text-align:center;color:#999;">正在获取数据...</div>
        {% endif %}

        <div class="card">
            {% if kill %}
            <div class="kill-box">
                <div class="kill-title">当前杀组合</div>
                <div class="kill-name">{{ kill }}</div>
            </div>
            <div class="stats">
                <div class="stat-title">最近100期组合次数</div>
                {% for name, num in counts.items() %}
                <div class="stat-row">
                    <span>{{ name }}</span>
                    <span class="stat-num">{{ num }}</span>
                </div>
                {% endfor %}
            </div>
            <div class="stats">
                <div class="stat-title">最近100期和值次数</div>
                <div class="sum-grid">
                {% for s in range(28) %}
                <div class="sum-item">
                    <div class="sum-val">{{ s }}</div>
                    <div class="sum-cnt">{{ sums.get(s, 0) }}</div>
                </div>
                {% endfor %}
                </div>
            </div>
            <div class="bets">
                <div style="color:#666;font-size:13px;margin-bottom:6px;">建议发给机器人</div>
                {% for b in bets %}
                <div class="bet">{{ b }}</div>
                {% endfor %}
            </div>
            {% if history %}
            <div class="history">
                <div class="stat-title">
                    最近杀组合记录（共{{ history|length }}期　胜率 {{ '%.1f'|format(win_rate) }}%）
                    {% if streak_type %}　{{ streak_type }}{{ streak_count }}期{% endif %}
                </div>
                {% for h in history[:15] %}
                <div class="hist-row">
                    <span>{{ h.period }} 杀{{ h.kill }}</span>
                    <span>实际{{ h.actual }}</span>
                    <span class="{{ 'win' if h.win else 'lose' }}">{{ '中' if h.win else '挂' }}</span>
                </div>
                {% endfor %}
            </div>
            {% endif %}
            {% else %}
            <div style="text-align:center;color:#999;">暂无建议</div>
            {% endif %}
        </div>
    </div>
    <div class="footer">数据来源 pc28.world · 最近100期 · 金额固定 {{ amount }} · 仅供参考</div>
</body>
</html>
"""

def get_latest():
    try:
        r = requests.get(f"{API_BASE}/draws/latest", headers=HEADERS, timeout=10)
        data = r.json()
        if data.get("ok"):
            return data["data"]
    except:
        pass
    return None

def get_history(limit=100):
    try:
        r = requests.get(f"{API_BASE}/draws?limit={limit}", headers=HEADERS, timeout=10)
        data = r.json()
        if data.get("ok"):
            return data["data"]["items"]
    except:
        pass
    return []

def decide_kill(history):
    combos = [item.get("combo", "") for item in history if item.get("combo")]
    sums = [item.get("sum", 0) for item in history]
    if not combos:
        return None, {}, {}
    counter = Counter(combos)
    for c in ["大单", "大双", "小单", "小双"]:
        counter[c] = counter.get(c, 0)
    sum_counter = Counter(sums)
    for i in range(28):
        sum_counter[i] = sum_counter.get(i, 0)
    kill = counter.most_common(1)[0][0]
    return kill, dict(counter), dict(sum_counter)

def get_bets(kill):
    mapping = {
        "大单": ["小" + str(BET_AMOUNT), "双" + str(BET_AMOUNT)],
        "大双": ["小" + str(BET_AMOUNT), "单" + str(BET_AMOUNT)],
        "小单": ["大" + str(BET_AMOUNT), "双" + str(BET_AMOUNT)],
        "小双": ["大" + str(BET_AMOUNT), "单" + str(BET_AMOUNT)],
    }
    return mapping.get(kill, [])

def update_loop():
    while True:
        latest = get_latest()
        if not latest:
            time.sleep(5)
            continue

        current_period = latest["draw"]["nbr"]
        actual_combo = latest["draw"].get("combo", "")

        # 如果有新期开奖，结算上一期的杀组合
        if cache["last_period"] and current_period != cache["last_period"] and cache["pending_kill"]:
            win = actual_combo != cache["pending_kill"]
            record = {
                "period": cache["last_period"],
                "kill": cache["pending_kill"],
                "actual": actual_combo,
                "win": win
            }
            cache["history"].insert(0, record)
            if len(cache["history"]) > 50:
                cache["history"] = cache["history"][:50]
            save_history(cache["history"])

        # 计算当前建议
        history_data = get_history(100)
        kill, counts, sums = decide_kill(history_data)
        bets = get_bets(kill) if kill else []

        # 计算胜率
        total = len(cache["history"])
        wins = sum(1 for h in cache["history"] if h["win"])
        win_rate = (wins / total * 100) if total > 0 else 0

        # 计算当前连中/连挂
        streak_count = 0
        streak_type = ""
        if cache["history"]:
            last_win = cache["history"][0]["win"]
            for h in cache["history"]:
                if h["win"] == last_win:
                    streak_count += 1
                else:
                    break
            streak_type = "连中" if last_win else "连挂"

        cache["latest"] = latest
        cache["kill"] = kill
        cache["bets"] = bets
        cache["counts"] = counts
        cache["sums"] = sums
        cache["pending_kill"] = kill
        cache["last_period"] = current_period
        cache["update_time"] = time.strftime("%H:%M:%S")
        cache["win_rate"] = win_rate
        cache["streak_count"] = streak_count
        cache["streak_type"] = streak_type
        time.sleep(12)

@app.route("/")
def index():
    return render_template_string(
        HTML,
        latest=cache["latest"],
        kill=cache["kill"],
        bets=cache["bets"],
        counts=cache["counts"],
        sums=cache["sums"],
        history=cache["history"],
        win_rate=cache.get("win_rate", 0),
        streak_count=cache.get("streak_count", 0),
        streak_type=cache.get("streak_type", ""),
        update_time=cache["update_time"],
        amount=BET_AMOUNT
    )

if __name__ == "__main__":
    t = threading.Thread(target=update_loop, daemon=True)
    t.start()
    print("网页版已启动 → http://127.0.0.1:5000")
    app.run(host="0.0.0.0", port=5000, debug=False)
