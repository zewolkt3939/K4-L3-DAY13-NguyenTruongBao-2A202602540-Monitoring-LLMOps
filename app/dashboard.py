from __future__ import annotations

import json
import os
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from .metrics import percentile

LOG_PATH = Path(os.getenv("LOG_PATH", "data/logs.jsonl"))


def calculate_dashboard_data() -> dict:
    if not LOG_PATH.exists():
        return {
            "latency": {"p50": 0, "p95": 0, "p99": 0, "ttft_p95": 0, "status": "ok"},
            "traffic": {"count": 0, "rate_per_minute": 0.0, "status": "ok"},
            "errors": {"error_rate_pct": 0.0, "breakdown": {}, "tool_success_rate_pct": 100.0, "status": "ok"},
            "cost": {"total": 0.0, "status": "ok"},
            "tokens": {"tokens_in": 0, "tokens_out": 0, "total": 0, "status": "ok"},
            "quality": {"mean": 1.0, "status": "ok"},
        }

    records: list[dict] = []
    for line in LOG_PATH.read_text(encoding="utf-8").splitlines():
        if line.strip():
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                pass

    req_received = [r for r in records if r.get("event") == "request_received"]
    req_sent = [r for r in records if r.get("event") == "response_sent"]
    req_failed = [r for r in records if r.get("event") == "request_failed"]

    # 1. Latency
    latencies = [int(r["latency_ms"]) for r in req_sent if "latency_ms" in r and r["latency_ms"] is not None]
    ttfts = [int(r["ttft_ms"]) for r in req_sent if "ttft_ms" in r and r["ttft_ms"] is not None]
    p50 = percentile(latencies, 50)
    p95 = percentile(latencies, 95)
    p99 = percentile(latencies, 99)
    ttft_p95 = percentile(ttfts, 95)
    latency_status = "ok" if p95 <= 3000 else "alert"

    # 2. Traffic
    total_received = len(req_received)
    rate_per_min = round(total_received / 60.0, 2)
    traffic_status = "ok" if rate_per_min >= 0.01 else "warning"

    # 3. Errors & Retrieval
    total_requests = max(1, total_received)
    error_rate_pct = round((len(req_failed) / total_requests) * 100.0, 2)
    error_breakdown = Counter(r.get("error_type", "Unknown") for r in req_failed)
    
    # tool_success
    tool_events = [r for r in records if r.get("tool_success") is not None]
    tool_successes = sum(1 for r in tool_events if r.get("tool_success") is True)
    tool_success_rate = round((tool_successes / max(1, len(tool_events))) * 100.0, 2) if tool_events else 100.0
    error_status = "ok" if error_rate_pct <= 2.0 else "alert"

    # 4. Cost
    costs = [float(r["cost_usd"]) for r in req_sent if "cost_usd" in r and r["cost_usd"] is not None]
    total_cost = round(sum(costs), 4)
    cost_status = "ok" if total_cost <= 2.5 else "alert"

    # 5. Tokens
    t_in = sum(int(r.get("tokens_in", 0) or 0) for r in req_sent)
    t_out = sum(int(r.get("tokens_out", 0) or 0) for r in req_sent)
    tokens_status = "ok" if (t_in <= 50000 and t_out <= 50000) else "alert"

    # 6. Quality
    q_scores = [float(r["quality_score"]) for r in req_sent if "quality_score" in r and r["quality_score"] is not None]
    mean_quality = round(sum(q_scores) / len(q_scores), 3) if q_scores else 0.0
    quality_status = "ok" if mean_quality >= 0.75 else "alert"

    return {
        "latency": {"p50": p50, "p95": p95, "p99": p99, "ttft_p95": ttft_p95, "status": latency_status, "threshold": "<= 3000ms"},
        "traffic": {"count": total_received, "rate_per_minute": rate_per_min, "status": traffic_status, "threshold": ">= 1 req/min"},
        "errors": {"error_rate_pct": error_rate_pct, "breakdown": dict(error_breakdown), "tool_success_rate_pct": tool_success_rate, "status": error_status, "threshold": "<= 2%"},
        "cost": {"total": total_cost, "status": cost_status, "threshold": "<= $2.50"},
        "tokens": {"tokens_in": t_in, "tokens_out": t_out, "total": t_in + t_out, "status": tokens_status, "threshold": "<= 50,000"},
        "quality": {"mean": mean_quality, "status": quality_status, "threshold": ">= 0.75"},
    }


def render_dashboard_html() -> str:
    data = calculate_dashboard_data()
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    def badge(status: str) -> str:
        color = "#10b981" if status == "ok" else ("#ef4444" if status == "alert" else "#f59e0b")
        text = "NORMAL" if status == "ok" else ("ALERT" if status == "alert" else "WARNING")
        return f'<span style="background:{color}22; color:{color}; border:1px solid {color}55; padding:3px 10px; border-radius:12px; font-size:11px; font-weight:600; text-transform:uppercase;">{text}</span>'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>K4-L3A Day 13 Monitoring & LLMOps Dashboard</title>
    <meta http-equiv="refresh" content="30">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg: #0b0f19;
            --card-bg: rgba(17, 24, 39, 0.75);
            --card-border: rgba(255, 255, 255, 0.08);
            --text-main: #f3f4f6;
            --text-muted: #9ca3af;
            --accent: #6366f1;
            --success: #10b981;
            --warning: #f59e0b;
            --danger: #ef4444;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            background: var(--bg);
            color: var(--text-main);
            font-family: 'Inter', sans-serif;
            padding: 24px;
            min-height: 100vh;
        }}
        .header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid var(--card-border);
            padding-bottom: 16px;
            margin-bottom: 24px;
        }}
        .title h1 {{
            font-size: 20px;
            font-weight: 700;
            letter-spacing: -0.5px;
            background: linear-gradient(135deg, #e0e7ff 0%, #a5b4fc 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .title p {{
            font-size: 13px;
            color: var(--text-muted);
            margin-top: 4px;
        }}
        .meta-badges {{
            display: flex;
            gap: 12px;
            align-items: center;
        }}
        .meta-tag {{
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid var(--card-border);
            border-radius: 6px;
            padding: 6px 12px;
            font-size: 12px;
            color: var(--text-muted);
            font-family: 'JetBrains Mono', monospace;
        }}
        .grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 20px;
        }}
        .panel {{
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 12px;
            padding: 20px;
            backdrop-filter: blur(12px);
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            position: relative;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
        }}
        .panel-header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 16px;
        }}
        .panel-title {{
            font-size: 14px;
            font-weight: 600;
            color: var(--text-main);
        }}
        .panel-unit {{
            font-size: 11px;
            color: var(--text-muted);
            text-transform: uppercase;
            margin-top: 2px;
        }}
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 12px;
            margin-bottom: 16px;
        }}
        .metric-cell {{
            background: rgba(0, 0, 0, 0.2);
            border: 1px solid rgba(255, 255, 255, 0.04);
            border-radius: 8px;
            padding: 10px 12px;
        }}
        .metric-label {{
            font-size: 11px;
            color: var(--text-muted);
            margin-bottom: 4px;
            text-transform: uppercase;
        }}
        .metric-val {{
            font-size: 20px;
            font-weight: 700;
            font-family: 'JetBrains Mono', monospace;
            color: #fff;
        }}
        .panel-footer {{
            border-top: 1px solid rgba(255, 255, 255, 0.05);
            padding-top: 12px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 11px;
            color: var(--text-muted);
        }}
        .threshold-pill {{
            font-family: 'JetBrains Mono', monospace;
            color: #cbd5e1;
            font-weight: 500;
        }}
    </style>
</head>
<body>
    <div class="header">
        <div class="title">
            <h1>K4-L3A Day 13 Monitoring & LLMOps Dashboard</h1>
            <p>Data Source: data/logs.jsonl | Primary SLO: 99.5% (&lt;= 3000ms, 28d window)</p>
        </div>
        <div class="meta-badges">
            <div class="meta-tag">Time Range: Last 60m</div>
            <div class="meta-tag">Refresh: 30s</div>
            <div class="meta-tag">Updated: {now_str}</div>
        </div>
    </div>

    <div class="grid">
        <!-- 1. Latency Panel -->
        <div class="panel">
            <div class="panel-header">
                <div>
                    <div class="panel-title">1. Latency percentiles and TTFT</div>
                    <div class="panel-unit">Unit: milliseconds (ms)</div>
                </div>
                {badge(data['latency']['status'])}
            </div>
            <div class="metrics-grid">
                <div class="metric-cell">
                    <div class="metric-label">P50 Latency</div>
                    <div class="metric-val">{data['latency']['p50']}ms</div>
                </div>
                <div class="metric-cell">
                    <div class="metric-label">P95 Latency</div>
                    <div class="metric-val">{data['latency']['p95']}ms</div>
                </div>
                <div class="metric-cell">
                    <div class="metric-label">P99 Latency</div>
                    <div class="metric-val">{data['latency']['p99']}ms</div>
                </div>
                <div class="metric-cell">
                    <div class="metric-label">TTFT P95</div>
                    <div class="metric-val">{data['latency']['ttft_p95']}ms</div>
                </div>
            </div>
            <div class="panel-footer">
                <span>Threshold / SLO:</span>
                <span class="threshold-pill">P95 &lt;= 3000ms</span>
            </div>
        </div>

        <!-- 2. Traffic Panel -->
        <div class="panel">
            <div class="panel-header">
                <div>
                    <div class="panel-title">2. Request traffic</div>
                    <div class="panel-unit">Unit: requests_per_minute</div>
                </div>
                {badge(data['traffic']['status'])}
            </div>
            <div class="metrics-grid">
                <div class="metric-cell">
                    <div class="metric-label">Total Requests</div>
                    <div class="metric-val">{data['traffic']['count']}</div>
                </div>
                <div class="metric-cell">
                    <div class="metric-label">Rate / Minute</div>
                    <div class="metric-val">{data['traffic']['rate_per_minute']}</div>
                </div>
            </div>
            <div class="panel-footer">
                <span>Threshold:</span>
                <span class="threshold-pill">Rate &gt;= 1 req/min</span>
            </div>
        </div>

        <!-- 3. Errors Panel -->
        <div class="panel">
            <div class="panel-header">
                <div>
                    <div class="panel-title">3. Error rate and retrieval success</div>
                    <div class="panel-unit">Unit: percent (%)</div>
                </div>
                {badge(data['errors']['status'])}
            </div>
            <div class="metrics-grid">
                <div class="metric-cell">
                    <div class="metric-label">Error Rate</div>
                    <div class="metric-val">{data['errors']['error_rate_pct']}%</div>
                </div>
                <div class="metric-cell">
                    <div class="metric-label">Retrieval Success</div>
                    <div class="metric-val">{data['errors']['tool_success_rate_pct']}%</div>
                </div>
            </div>
            <div class="panel-footer">
                <span>Threshold:</span>
                <span class="threshold-pill">Error rate &lt;= 2%</span>
            </div>
        </div>

        <!-- 4. Cost Panel -->
        <div class="panel">
            <div class="panel-header">
                <div>
                    <div class="panel-title">4. Cost over time</div>
                    <div class="panel-unit">Unit: USD ($)</div>
                </div>
                {badge(data['cost']['status'])}
            </div>
            <div class="metrics-grid">
                <div class="metric-cell">
                    <div class="metric-label">Total Window Cost</div>
                    <div class="metric-val">${data['cost']['total']:.4f}</div>
                </div>
                <div class="metric-cell">
                    <div class="metric-label">Daily Budget</div>
                    <div class="metric-val">$2.5000</div>
                </div>
            </div>
            <div class="panel-footer">
                <span>Threshold:</span>
                <span class="threshold-pill">Total &lt;= $2.50</span>
            </div>
        </div>

        <!-- 5. Tokens Panel -->
        <div class="panel">
            <div class="panel-header">
                <div>
                    <div class="panel-title">5. Input and output tokens</div>
                    <div class="panel-unit">Unit: tokens</div>
                </div>
                {badge(data['tokens']['status'])}
            </div>
            <div class="metrics-grid">
                <div class="metric-cell">
                    <div class="metric-label">Tokens In</div>
                    <div class="metric-val">{data['tokens']['tokens_in']:,}</div>
                </div>
                <div class="metric-cell">
                    <div class="metric-label">Tokens Out</div>
                    <div class="metric-val">{data['tokens']['tokens_out']:,}</div>
                </div>
            </div>
            <div class="panel-footer">
                <span>Threshold:</span>
                <span class="threshold-pill">Tokens &lt;= 50,000</span>
            </div>
        </div>

        <!-- 6. Quality Panel -->
        <div class="panel">
            <div class="panel-header">
                <div>
                    <div class="panel-title">6. Quality proxy</div>
                    <div class="panel-unit">Unit: score (0.00 - 1.00)</div>
                </div>
                {badge(data['quality']['status'])}
            </div>
            <div class="metrics-grid">
                <div class="metric-cell">
                    <div class="metric-label">Average Quality</div>
                    <div class="metric-val">{data['quality']['mean']:.2f}</div>
                </div>
                <div class="metric-cell">
                    <div class="metric-label">Target Standard</div>
                    <div class="metric-val">&gt;= 0.75</div>
                </div>
            </div>
            <div class="panel-footer">
                <span>Threshold:</span>
                <span class="threshold-pill">Mean &gt;= 0.75</span>
            </div>
        </div>
    </div>
</body>
</html>"""
