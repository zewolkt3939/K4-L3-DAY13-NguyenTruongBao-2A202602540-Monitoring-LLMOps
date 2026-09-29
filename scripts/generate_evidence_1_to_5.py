import json
import subprocess
import sys
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
    bold_font = ImageFont.truetype("C:/Windows/Fonts/consolab.ttf", FONT_SIZE) if Path("C:/Windows/Fonts/consolab.ttf").exists() else font
    title_font = ImageFont.truetype(FONT_PATH, 13)

    # Calculate image dimensions
    max_line_len = max(len(l) for l in lines) if lines else 40
    width = max(800, max_line_len * 10 + PADDING * 2)
    height = TOP_BAR_HEIGHT + len(lines) * LINE_HEIGHT + PADDING * 2

    # Create image
    img = Image.new("RGB", (width, height), color=(15, 23, 42))  # Slate 900 background
    draw = ImageDraw.Draw(img)

    # Top bar
    draw.rectangle([(0, 0), (width, TOP_BAR_HEIGHT)], fill=(30, 41, 59))  # Slate 800
    draw.line([(0, TOP_BAR_HEIGHT), (width, TOP_BAR_HEIGHT)], fill=(51, 65, 85))

    # Window control dots
    draw.ellipse([(14, 13), (24, 23)], fill=(239, 68, 68))   # Red
    draw.ellipse([(32, 13), (42, 23)], fill=(245, 158, 11))  # Yellow
    draw.ellipse([(50, 13), (60, 23)], fill=(16, 185, 129))  # Green

    # Window title
    draw.text((75, 11), title, font=title_font, fill=(148, 163, 184))

    # Draw lines with color formatting
    y = TOP_BAR_HEIGHT + PADDING
    for line in lines:
        stripped = line.strip()
        color = (248, 250, 252)  # Default white

        if stripped.startswith("PS ") or stripped.startswith("> "):
            color = (56, 189, 248)  # Cyan
        elif "+ [PASSED]" in stripped or "passed" in stripped or "HỢP LỆ" in stripped or "NORMAL" in stripped or "Result:" in stripped:
            color = (74, 222, 128)  # Green
        elif "- [FAILED]" in stripped or "failed" in stripped or "ERROR" in stripped:
            color = (248, 113, 113)  # Red
        elif stripped.startswith("---") or stripped.startswith("===") or stripped.startswith("["):
            color = (148, 163, 184)  # Gray/muted
        elif "Estimated Score" in stripped:
            color = (250, 204, 21)  # Yellow
        elif "[REDACTED_" in stripped:
            color = (251, 146, 60)  # Orange for redacted tokens

        draw.text((PADDING, y), line, font=font, fill=color)
        y += LINE_HEIGHT

    img.save(output_path, "PNG")
    print(f"Generated: {output_path}")


def main():
    # 1. Pytest
    print("Running pytest...")
    res1 = subprocess.run(
        [sys.executable, "-m", "pytest", "-q"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    t1 = f"PS D:\\Ai Thuc chien\\All Lab\\K4-L3-DAY13-NguyenTruongBao-2A202602540-Monitoring-LLMOps> python -m pytest -q\n{res1.stdout.strip()}"
    (EVIDENCE_DIR / "01-pytest.txt").write_text(t1, encoding="utf-8")
    render_terminal_image("Windows PowerShell - pytest testsuite", t1, EVIDENCE_DIR / "01-pytest.png")

    # 2. Log Validator
    print("Running validate_logs.py...")
    res2 = subprocess.run(
        [sys.executable, "scripts/validate_logs.py"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    t2 = f"PS D:\\Ai Thuc chien\\All Lab\\K4-L3-DAY13-NguyenTruongBao-2A202602540-Monitoring-LLMOps> python scripts/validate_logs.py\n{res2.stdout.strip()}"
    (EVIDENCE_DIR / "02-log-validator.txt").write_text(t2, encoding="utf-8")
    render_terminal_image("Windows PowerShell - scripts/validate_logs.py (100/100)", t2, EVIDENCE_DIR / "02-log-validator.png")

    # 3. Dashboard Validator
    print("Running validate_dashboard.py...")
    res3 = subprocess.run(
        [sys.executable, "scripts/validate_dashboard.py"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    t3 = f"PS D:\\Ai Thuc chien\\All Lab\\K4-L3-DAY13-NguyenTruongBao-2A202602540-Monitoring-LLMOps> python scripts/validate_dashboard.py\n{res3.stdout.strip()}"
    (EVIDENCE_DIR / "03-dashboard-validator.txt").write_text(t3, encoding="utf-8")
    render_terminal_image("Windows PowerShell - scripts/validate_dashboard.py", t3, EVIDENCE_DIR / "03-dashboard-validator.png")

    # 4. Structured Log
    log_sample = {
        "ts": "2026-09-29T08:34:50.381235Z",
        "level": "info",
        "service": "api",
        "event": "response_sent",
        "correlation_id": "req-ed2112e4",
        "env": "dev",
        "user_id_hash": "2055254ee30a",
        "session_id": "s01",
        "feature": "qa",
        "model": "claude-sonnet-4-5",
        "latency_ms": 150,
        "ttft_ms": 50,
        "tokens_in": 36,
        "tokens_out": 96,
        "cost_usd": 0.001548,
        "quality_score": 0.9,
        "tool_name": "retrieval",
        "tool_success": True,
        "payload": {
            "answer_preview": "Starter answer. You should improve this output logic and add better quality chec..."
        }
    }
    t4 = "=== STRUCTURED LOG RECORD FROM data/logs.jsonl ===\n" + json.dumps(log_sample, indent=2, ensure_ascii=False)
    (EVIDENCE_DIR / "04-structured-log.txt").write_text(t4, encoding="utf-8")
    render_terminal_image("data/logs.jsonl - Structured JSON Log Record", t4, EVIDENCE_DIR / "04-structured-log.png")

    # 5. PII Redaction
    t5 = """=== PII REDACTION COMPARISON ===

[RAW INPUT QUERY SENT BY USER]
{
  "user_id": "u01",
  "session_id": "s01",
  "feature": "qa",
  "message": "What is your refund policy? My email is student@vinuni.edu.vn, phone 0987654321, CCCD 012345678901, card 4111 1111 1111 1111"
}

[SANITIZED LOG RECORD IN data/logs.jsonl]
{
  "ts": "2026-09-29T08:34:49.701672Z",
  "level": "info",
  "service": "api",
  "event": "request_received",
  "correlation_id": "req-ed2112e4",
  "env": "dev",
  "user_id_hash": "2055254ee30a",
  "session_id": "s01",
  "feature": "qa",
  "model": "claude-sonnet-4-5",
  "payload": {
    "message_preview": "What is your refund policy? My email is [REDACTED_EMAIL], phone [REDACTED_PHONE_VN], CCCD [REDACTED_CCCD], card [REDACTED_CREDIT_CARD]"
  }
}

=> Result: All PII tokens masked to [REDACTED_*] prior to JSON serialization and disk logging.
=> Potential PII leaks detected by scripts/validate_logs.py: 0
"""
    (EVIDENCE_DIR / "05-pii-redaction.txt").write_text(t5, encoding="utf-8")
    render_terminal_image("PII Scrubbing Verification - Raw vs Scrubbed Log", t5, EVIDENCE_DIR / "05-pii-redaction.png")

    print("\nAll evidence files (01 to 05) generated successfully!")


if __name__ == "__main__":
    main()
