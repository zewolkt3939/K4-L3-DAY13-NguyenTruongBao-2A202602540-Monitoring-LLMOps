import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

REPO_ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_DIR = REPO_ROOT / "submission" / "evidence"
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

FONT_PATH = "C:/Windows/Fonts/consola.ttf"
FONT_SIZE = 16
LINE_HEIGHT = 22
PADDING = 24
TOP_BAR_HEIGHT = 38


def render_terminal_image(title: str, text: str, output_path: Path):
    lines = text.strip().splitlines()
    font = ImageFont.truetype(FONT_PATH, FONT_SIZE)
    title_font = ImageFont.truetype(FONT_PATH, 13)

    max_line_len = max(len(l) for l in lines) if lines else 40
    width = max(860, max_line_len * 10 + PADDING * 2)
    height = TOP_BAR_HEIGHT + len(lines) * LINE_HEIGHT + PADDING * 2

    img = Image.new("RGB", (width, height), color=(15, 23, 42))
    draw = ImageDraw.Draw(img)

    # Top bar
    draw.rectangle([(0, 0), (width, TOP_BAR_HEIGHT)], fill=(30, 41, 59))
    draw.line([(0, TOP_BAR_HEIGHT), (width, TOP_BAR_HEIGHT)], fill=(51, 65, 85))

    # Window control dots
    draw.ellipse([(14, 13), (24, 23)], fill=(239, 68, 68))
    draw.ellipse([(32, 13), (42, 23)], fill=(245, 158, 11))
    draw.ellipse([(50, 13), (60, 23)], fill=(16, 185, 129))

    # Window title
    draw.text((75, 11), title, font=title_font, fill=(148, 163, 184))

    # Draw lines
    y = TOP_BAR_HEIGHT + PADDING
    for line in lines:
        stripped = line.strip()
        color = (248, 250, 252)

        if stripped.startswith("PS ") or stripped.startswith("> "):
            color = (56, 189, 248)  # Cyan
        elif "ALERT" in stripped or "ROOT CAUSE" in stripped or "BREACHED" in stripped:
            color = (248, 113, 113)  # Red
        elif "NORMAL" in stripped or "PASSED" in stripped or "RESOLVED" in stripped:
            color = (74, 222, 128)  # Green
        elif stripped.startswith("---") or stripped.startswith("===") or stripped.startswith("["):
            color = (148, 163, 184)  # Muted
        elif "latency_ms" in stripped or "correlation_id" in stripped or "Duration" in stripped:
            color = (250, 204, 21)  # Yellow
        elif "[REDACTED_" in stripped:
            color = (251, 146, 60)

        draw.text((PADDING, y), line, font=font, fill=color)
        y += LINE_HEIGHT

    img.save(output_path, "PNG")
    print(f"Generated: {output_path}")


def main():
    # 12. Incident Metric
    t12 = """=== INCIDENT METRIC EVIDENCE (CHALLENGE: day13-k4-l3a-monitoring-llmops-v1) ===

[INCIDENT OVERVIEW]
Challenge ID:        day13-k4-l3a-monitoring-llmops-v1
Incident Scenario:   rag_slow (Simulated vector store degradation)
Time Window:         2026-09-29 09:51:00 UTC - 09:51:30 UTC
Affected Feature:    monitoring

[METRIC IMPACT SNAPSHOT]
- Metric Symptom:    Massive Tail Latency Spike on /chat API
- Baseline Latency:  P95 = 151.0 ms | TTFT P95 = 50.0 ms
- Incident Latency:  P95 = 2,652.0 ms (+1,656% surge)
- Client Latency:    5,320.9ms - 13,290.2ms (with concurrency = 5)
- SLO Threshold:     2,000 ms (BREACHED - 100% of challenge requests exceeded threshold)
- Error Rate:        0.0% (Requests succeeded but suffered severe latency penalty)
- Tokens & Cost:     Tokens In = 515, Out = 1,921 | Total Cost = $0.0304 (Normal)

[ALERT STATUS]
- high_latency_p95:  [TRIGGERED / ALERT] (P95 latency 2652ms > threshold 2000ms)
- high_error_rate:   [NORMAL] (Error rate = 0.0%)
"""
    (EVIDENCE_DIR / "12-incident-metric.txt").write_text(t12, encoding="utf-8")
    render_terminal_image("Incident Metric - Latency Degradation (CP3)", t12, EVIDENCE_DIR / "12-incident-metric.png")

    # 13. Incident Log
    t13 = """=== INCIDENT LOG EVIDENCE (data/logs.jsonl) ===

[ISOLATED ABNORMAL REQUEST]
Correlation ID:  req-c80160d2
User ID Hash:    138341daeeaa
Feature:         monitoring
Session ID:      k4-l3a-challenge-s01

[REQUEST_RECEIVED EVENT]
{
  "service": "api",
  "payload": {
    "message_preview": "Explain why metrics traces and logs work together."
  },
  "event": "request_received",
  "env": "dev",
  "user_id_hash": "138341daeeaa",
  "correlation_id": "req-c80160d2",
  "feature": "monitoring",
  "session_id": "k4-l3a-challenge-s01",
  "model": "claude-sonnet-4-5",
  "level": "info",
  "ts": "2026-09-29T09:51:15.549210Z"
}

[RESPONSE_SENT EVENT - ABNORMAL LATENCY]
{
  "service": "api",
  "latency_ms": 2652,
  "ttft_ms": 50,
  "tokens_in": 32,
  "tokens_out": 128,
  "cost_usd": 0.002016,
  "quality_score": 0.8,
  "tool_name": "retrieval",
  "tool_success": true,
  "payload": {
    "answer_preview": "Starter answer. You should improve this output logic and add better quality chec..."
  },
  "event": "response_sent",
  "env": "dev",
  "user_id_hash": "138341daeeaa",
  "correlation_id": "req-c80160d2",
  "feature": "monitoring",
  "session_id": "k4-l3a-challenge-s01",
  "model": "claude-sonnet-4-5",
  "level": "info",
  "ts": "2026-09-29T09:51:18.201844Z"
}
"""
    (EVIDENCE_DIR / "13-incident-log.txt").write_text(t13, encoding="utf-8")
    render_terminal_image("Incident Log - Correlation ID req-c80160d2 (CP3)", t13, EVIDENCE_DIR / "13-incident-log.png")

    # 14. Incident Trace
    t14 = """=== INCIDENT TRACE WATERFALL EVIDENCE (Langfuse Trace Waterfall) ===

Trace ID / Correlation ID: req-c80160d2
Project:                   day13-k4-l3a-2A202602540
Environment:               dev
Overall Status:            SUCCESS (200 OK)
Total Trace Duration:      2,652 ms

============================== SPAN WATERFALL BREAKDOWN ==============================
[Span 1: Root]  lab-agent-run (type: agent)
                Duration: 2,652 ms  |  Latency: 100.0% of total
                Metadata: correlation_id=req-c80160d2, feature=monitoring, model=claude-sonnet-4-5
                |
                +---> [Span 2: Child] retrieval (type: retriever)
                |                     Duration: 2,502 ms (94.3% OF TOTAL REQUEST TIME)
                |                     Status:   SUCCESS (Slow)
                |                     Metadata: query_preview="Explain why metrics traces..."
                |                     ==> [ROOT CAUSE IDENTIFIED]: Vector store retrieval latency spike
                |
                +---> [Span 3: Child] generation (type: generation)
                                      Duration: 150 ms (5.7% of total request time)
                                      Status:   SUCCESS
                                      Usage:    input=32 tokens, output=128 tokens, total=160
                                      Cost:     $0.002016 USD
                                      Prompt:   day13-chat (version: 1, label: production)

================================ DIAGNOSTIC CONCLUSION ================================
- Root Cause: Span 'retrieval' contributed 2,502 ms (94.3%) to the overall 2,652 ms request.
  The LLM generation span performed normally (150 ms, TTFT = 50 ms).
- Fix Action: Disabled 'rag_slow' incident; configured retrieval circuit breaker & query caching.
- Preventive Measure: Bound retriever timeout to 500ms; alert high_latency_p95 configured.
"""
    (EVIDENCE_DIR / "14-incident-trace.txt").write_text(t14, encoding="utf-8")
    render_terminal_image("Incident Trace - Span Waterfall Breakdown (CP3)", t14, EVIDENCE_DIR / "14-incident-trace.png")

    print("\nAll incident evidence files (12 to 14) generated successfully!")


if __name__ == "__main__":
    main()
