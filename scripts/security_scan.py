import json
import os
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

SECRET_PATTERNS = {
    "Langfuse Secret Key": re.compile(r"sk-lf-[a-zA-Z0-9_-]{20,}"),
    "OpenAI API Key": re.compile(r"sk-[a-zA-Z0-9]{32,}"),
    "AWS Access Key": re.compile(r"AKIA[0-9A-Z]{16}"),
    "Generic Private Key": re.compile(r"-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----"),
}

PII_PATTERNS = {
    "raw_email": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b"),
    "raw_phone_vn": re.compile(r"(?<!\d)(?:\+84|0)(?:[ .-]?\d){9}(?!\d)"),
    "raw_cccd": re.compile(r"\b\d{12}\b"),
    "raw_credit_card": re.compile(r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b"),
}


def check_git_tracked_secrets():
    print("[1/4] Scanning git tracked files for secrets and credentials...")
    res = subprocess.run(["git", "ls-files"], cwd=REPO_ROOT, capture_output=True, text=True)
    tracked_files = [f for f in res.stdout.splitlines() if f.strip()]
    
    leaks = []
    for rel_path in tracked_files:
        full_path = REPO_ROOT / rel_path
        if rel_path in {".gitignore", "requirements.txt"} or rel_path.endswith((".png", ".jpg", ".webp", ".ico")):
            continue
        try:
            content = full_path.read_text(encoding="utf-8", errors="ignore")
            for secret_type, pattern in SECRET_PATTERNS.items():
                if pattern.search(content):
                    leaks.append((rel_path, secret_type))
        except Exception:
            pass

    if leaks:
        print("  [FAILED] Found potential secrets in tracked files:")
        for path, stype in leaks:
            print(f"    - {path}: {stype}")
        return False
    print("  [PASSED] No credentials or secrets found in git tracked files.")
    return True


def check_env_and_challenge_ignored():
    print("[2/4] Verifying .env and challenge.json exclusion from Git...")
    res = subprocess.run(["git", "ls-files", ".env", "config/challenge.json"], cwd=REPO_ROOT, capture_output=True, text=True)
    leaked = [f for f in res.stdout.splitlines() if f.strip()]
    if leaked:
        print(f"  [FAILED] Restricted files are tracked in git: {leaked}")
        return False
    print("  [PASSED] .env and config/challenge.json are correctly excluded by .gitignore.")
    return True


def check_logs_pii():
    print("[3/4] Verifying data/logs.jsonl for raw PII leaks...")
    log_path = REPO_ROOT / "data" / "logs.jsonl"
    if not log_path.exists():
        print("  [WARNING] data/logs.jsonl does not exist.")
        return True

    lines = log_path.read_text(encoding="utf-8").splitlines()
    leaks = 0
    for idx, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            rec = json.loads(line)
            # dump back to raw string without ensure_ascii
            raw = json.dumps(rec, ensure_ascii=False)
            for pii_name, pattern in PII_PATTERNS.items():
                # Allow REDACTED placeholders
                cleaned = re.sub(r"\[REDACTED_[A-Z_]+\]", "", raw)
                if pattern.search(cleaned):
                    leaks += 1
                    print(f"  [LEAK] Line {idx}: detected {pii_name}")
        except json.JSONDecodeError:
            pass

    if leaks > 0:
        print(f"  [FAILED] Detected {leaks} raw PII occurrences in data/logs.jsonl.")
        return False
    print("  [PASSED] 0 PII leaks found in data/logs.jsonl. All sensitive tokens are scrubbed.")
    return True


def check_evidence_integrity():
    print("[4/4] Verifying all evidence files referenced in submission/REPORT.md...")
    report_path = REPO_ROOT / "submission" / "REPORT.md"
    if not report_path.exists():
        print("  [FAILED] submission/REPORT.md not found.")
        return False

    report = report_path.read_text(encoding="utf-8")
    links = re.findall(r"evidence/[a-zA-Z0-9_\-\. ]+", report)
    missing = []
    for link in links:
        target = REPO_ROOT / "submission" / link.strip()
        if not target.exists():
            missing.append(link)

    if missing:
        print(f"  [FAILED] Missing evidence files: {missing}")
        return False
    print(f"  [PASSED] All {len(links)} evidence links resolve to valid existing files.")
    return True


def main():
    print("=" * 60)
    print(" K4-L3A PRE-SUBMISSION SECURITY & INTEGRITY SCANNER")
    print("=" * 60)
    
    ok1 = check_git_tracked_secrets()
    ok2 = check_env_and_challenge_ignored()
    ok3 = check_logs_pii()
    ok4 = check_evidence_integrity()
    
    print("-" * 60)
    if ok1 and ok2 and ok3 and ok4:
        print("[SUCCESS] ALL SECURITY & INTEGRITY CHECKS PASSED (100% READY FOR SUBMISSION)!")
        sys.exit(0)
    else:
        print("[ERROR] PRE-SUBMISSION CHECK FAILED. REVIEW ISSUES ABOVE.")
        sys.exit(1)


if __name__ == "__main__":
    main()
