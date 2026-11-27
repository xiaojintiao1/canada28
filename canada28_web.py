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
    <title>Canada28 Tip Tool</title>
    <meta http-equiv="refresh" content="15">
    <style>
        * { box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: #f8f9fa; margin: 0; padding: 0; color: #333;
        }
        .header {
            background: white; padding: 12px 16px; display: flex; align-items: center;
            border-bottom: 1px solid #eee; position: sticky; top: 0; z-index: 10;
        }
        .logo { font-size: 22px; font-weight: bold; color: #e74c3c; margin-right: 8px; }
        .logo span { color: #333; }
        .badge { background: #3498db; color: white; font-size: 12px; padding: 2px 8px; border-radius: 12px; margin-left: 6px; }
        .container { max-width: 480px; margin: 0 auto; padding: 12px; }
        .card {
            background: white; border-radius: 12px; padding: 16px;
            box-shadow: 0 1px 4px rgba(0,0,0,0.06); margin-bottom: 12px;
        }
        .period-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; font-size: 14px; }
        .period-label { color: #3498db; font-weight: 500; }
        .countdown { text-align: center; margin: 16px 0; }
        .cd-label { font-size: 14px; color: #666; margin-bottom: 8px; }
        .cd-boxes { display: flex; justify-content: center; gap: 8px; align-items: center; }
        .cd-box { 
            background: #e74c3c; color: white; font-size: 28px; font-weight: bold;
            width: 56px; height: 56px; border-radius: 10px; display: flex; align-items: center; justify-content: center;
        }
        .cd-sep { font-size: 24px; color: #e74c3c; font-weight: bold; }
        .numbers { display: flex; justify-content: center; align-items: center; gap: 6px; margin: 16px 0; flex-wrap: wrap; }
        .num-box { 
            width: 44px; height: 44px; border-radius: 8px; 
            display: flex; align-items: center; justify-content: center;
            font-size: 20px; font-weight: bold; color: white;
        }
        .n1, .n2, .n3 { background: #3498db; }
        .sum { background: #e74c3c; }
        .tag { 
            display: inline-block; padding: 4px 10px; border-radius: 6px; 
            color: white; font-weight: bold; font-size: 15px; margin-left: 4px;
        }
        .big, .odd { background: #e74c3c; }
        .small, .even { background: #3498db; }
        .kill-section { text-align: center; margin: 16px 0; }
        .kill-title { color: #e74c3c; font-size: 14px; margin-bottom: 8px; }
        .kill-btn {
            display: inline-block; background: #e74c3c; color: white;
            font-size: 22px; font-weight: bold; padding: 10px 40px; border-radius: 8px;
        }
        .history-card { }
        .hist-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; font-size: 14px; }
        .hist-title { font-weight: 500; }
        .win-rate { color: #27ae60; font-weight: bold; }
        .streak { color: #27ae60; font-size: 13px; }
        table { width: 100%; border-collapse: collapse; font-size: 13px; }
        th { text-align: left; padding: 8px 4px; color: #666; font-weight: normal; border-bottom: 1px solid #eee; }
        td { padding: 8px 4px; border-bottom: 1px solid #f0f0f0; }
        .kill-text { color: #e74c3c; }
        .actual-text { color: #27ae60; }
        .result-win { color: #27ae60; font-weight: bold; }
        .result-lose { color: #e74c3c; font-weight: bold; }
        .footer { text-align: center; color: #999; font-size: 12px; padding: 16px; }
        .stats { margin: 12px 0; }
        .stat-title { text-align: center; color: #666; font-size: 13px; margin-bottom: 6px; }
        .stat-row { display: flex; justify-content: space-between; padding: 5px 0; border-bottom: 1px solid #eee; font-size: 14px; }
        .sum-grid { display: grid; grid-template-columns: repeat(7, 1fr); gap: 4px; margin: 8px 0; font-size: 12px; }
        .sum-item { text-align: center; background: #f8f8f8; border-radius: 4px; padding: 4px 2px; }
        .bets { text-align: center; margin-top: 12px; }
        .bet {
            display: inline-block; background: #27ae60; color: white;
            padding: 8px 18px; margin: 4px; border-radius: 6px; font-size: 15px; font-weight: bold;
        }
    </style>
</head>
<body>
    <div class="header">
        <div class="logo">🍁 Canada28 <span>TIP TOOL</span></div>
    </div>
    <div class="container">
        {% if latest %}
        <div class="card">
            <div class="period-row">
                <span class="period-label">● 最新期数</span>
                <span>{{ latest.draw.nbr }} 期</span>
            </div>
            <div class="countdown">
                <div class="cd-label">倒计时</div>
                <div class="cd-boxes">
                    <div class="cd-box" id="min">{{ '%02d' % (latest.countdown.seconds // 60) }}</div>
                    <div class="cd-sep">:</div>
                    <div class="cd-box" id="sec">{{ '%02d' % (latest.countdown.seconds % 60) }}</div>
                </div>
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
            {% if kill %}
            <div class="kill-section">
                <div class="kill-title">🎯 当前杀组合</div>
                <div class="kill-btn">{{ kill }}</div>
            </div>
            {% endif %}
        </div>
        {% else %}
        <div class="card" style="text-align:center;color:#999;">正在获取数据...</div>
        {% endif %}

        {% if kill %}
        <div class="card" style="padding:8px 12px;">
            <div style="display:flex;gap:8px;">
                <div style="flex:1;font-size:12px;">
                    <div style="text-align:center;color:#666;font-size:12px;margin-bottom:4px;">最近400期组合次数</div>
                    {% for name, num in counts.items() %}
                    <div style="display:flex;justify-content:space-between;padding:2px 0;border-bottom:1px solid #f0f0f0;">
                        <span>{{ name }}</span>
                        <span style="color:#e74c3c;font-weight:bold;">{{ num }}</span>
                    </div>
                    {% endfor %}
                </div>
                <div style="flex:1;font-size:11px;">
                    <div style="text-align:center;color:#666;font-size:12px;margin-bottom:4px;">最近400期和值次数</div>
                    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:2px;">
                    {% for s in range(28) %}
                    <div style="text-align:center;background:#f8f8f8;border-radius:3px;padding:2px 0;">
                        <div>{{ s }}</div>
                        <div style="color:#e74c3c;font-size:10px;">{{ sums.get(s, 0) }}</div>
                    </div>
                    {% endfor %}
                    </div>
                </div>
            </div>
            <div class="bets" style="margin-top:8px;">
                <div style="color:#666;font-size:12px;margin-bottom:4px;">建议发给机器人</div>
                {% for b in bets %}
                <div class="bet" style="padding:6px 14px;font-size:14px;">{{ b }}</div>
                {% endfor %}
            </div>
        </div>
        {% endif %}

        {% if history %}
        <div class="card history-card">
            <div class="hist-header">
                <div class="hist-title">🕐 杀组合记录（共{{ history|length }}期　胜率 <span class="win-rate">{{ '%.1f'|format(win_rate) }}%</span>）</div>
                {% if streak_type %}<div class="streak">{{ streak_type }}{{ streak_count }}期</div>{% endif %}
            </div>
            <div style="text-align:center;margin:8px 0;font-size:16px;font-weight:bold;">
                盈亏总额：<span style="color:{{ '#27ae60' if total_profit >= 0 else '#e74c3c' }};">{{ '%+d'|format(total_profit) }}</span>
            </div>
            <table>
                <thead>
                    <tr>
                        <th>期数</th>
                        <th>杀组合</th>
                        <th>实际（和值）</th>
                        <th>结果</th>
                        <th>盈亏</th>
                    </tr>
                </thead>
                <tbody>
                {% for h in history[:20] %}
                    <tr>
                        <td>{{ h.period }}</td>
                        <td class="kill-text">杀{{ h.kill }}</td>
                        <td class="actual-text">{{ h.actual }}（{{ h.sum }}）</td>
                        <td class="{{ 'result-win' if h.win else 'result-lose' }}">{{ '中' if h.win else '错' }}</td>
                        <td style="color:{{ '#27ae60' if h.profit > 0 else '#e74c3c' }};font-weight:bold;">{{ '%+d'|format(h.profit) }}</td>
                    </tr>
                {% endfor %}
                </tbody>
            </table>
        </div>
        {% endif %}
    </div>
    <div class="footer">预测仅供参考，理性娱乐，量力而行</div>
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

def get_history(limit=400):
    items = []
    before = None
    while len(items) < limit:
        try:
            url = f"{API_BASE}/draws?limit=200"
            if before:
                url += f"&before={before}"
            r = requests.get(url, headers=HEADERS, timeout=10)
            data = r.json()
            if data.get("ok") and data["data"].get("items"):
                batch = data["data"]["items"]
                items.extend(batch)
                if len(batch) < 200:
                    break
                before = batch[-1].get("nbr")
            else:
                break
        except:
            break
    return items[:limit]

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

def calc_profit(actual, sum_val):
    # 按开奖实际结果计算盈亏
    if sum_val in (13, 14):
        return -200
    # 实际开出大单 / 小双 → +120
    if actual in ("大单", "小双"):
        return 120
    # 实际开出大双 / 小单 → +160
    if actual in ("大双", "小单"):
        return 160
    return -300

def update_loop():
    while True:
        latest = get_latest()
        if not latest:
            time.sleep(5)
            continue

        current_period = latest["draw"]["nbr"]
        actual_combo = latest["draw"].get("combo", "")
        sum_val = latest["draw"].get("sum", 0)

        # 19:00-19:30 重置记录
        now = time.localtime()
        if now.tm_hour == 19 and 0 <= now.tm_min <= 30:
            if cache.get("reset_done") != time.strftime("%Y-%m-%d"):
                cache["history"] = []
                save_history([])
                cache["reset_done"] = time.strftime("%Y-%m-%d")

        # 如果有新期开奖，结算上一期的杀组合
        if cache["last_period"] and current_period != cache["last_period"] and cache["pending_kill"]:
            win = actual_combo != cache["pending_kill"]
            # 杀什么开什么（没中）固定 -300
            if not win:
                profit = -300
            else:
                profit = calc_profit(actual_combo, sum_val)
            record = {
                "period": cache["last_period"],
                "kill": cache["pending_kill"],
                "actual": actual_combo,
                "win": win,
                "profit": profit,
                "sum": sum_val
            }
            cache["history"].insert(0, record)
            # 一天大约 400 期，保留 500 期足够
            if len(cache["history"]) > 500:
                cache["history"] = cache["history"][:500]
            save_history(cache["history"])

        # 计算当前建议（最近400期）
        history_data = get_history(400)
        kill, counts, sums = decide_kill(history_data)
        bets = get_bets(kill) if kill else []

        # 计算胜率和盈亏
        total = len(cache["history"])
        wins = sum(1 for h in cache["history"] if h["win"])
        win_rate = (wins / total * 100) if total > 0 else 0
        total_profit = sum(h.get("profit", 0) for h in cache["history"])

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
        cache["total_profit"] = total_profit
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
        total_profit=cache.get("total_profit", 0),
        update_time=cache["update_time"],
        amount=BET_AMOUNT
    )

if __name__ == "__main__":
    t = threading.Thread(target=update_loop, daemon=True)
    t.start()
    print("网页版已启动 → http://127.0.0.1:5000")
    app.run(host="0.0.0.0", port=5000, debug=False)
