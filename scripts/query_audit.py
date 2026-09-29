import argparse
import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
AUDIT_LOG_PATH = Path(os.getenv("AUDIT_LOG_PATH", "data/audit.jsonl"))


def query_audit_logs(action: str | None = None, status: str | None = None, limit: int = 20):
    if not AUDIT_LOG_PATH.exists():
        print(f"Audit log file {AUDIT_LOG_PATH} does not exist yet.")
        return

    records = []
    for line in AUDIT_LOG_PATH.read_text(encoding="utf-8").splitlines():
        if line.strip():
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                pass

    if action:
        records = [r for r in records if r.get("action") == action]
    if status:
        records = [r for r in records if r.get("status") == status]

    print(f"=== AUDIT LOG QUERY RESULTS ({len(records)} found, showing up to {limit}) ===")
    for rec in records[-limit:]:
        print(f"[{rec.get('ts')}] actor={rec.get('actor')} | action={rec.get('action')} | resource={rec.get('resource')} | status={rec.get('status')} | retention={rec.get('retention_days')}d")
        if rec.get("details"):
            print(f"    details: {json.dumps(rec.get('details'), ensure_ascii=False)}")


def main():
    parser = argparse.ArgumentParser(description="Query compliance audit logs")
    parser.add_argument("--action", type=str, help="Filter by action name (e.g. incident_enabled, incident_disabled)")
    parser.add_argument("--status", type=str, choices=["success", "failed", "denied"], help="Filter by status")
    parser.add_argument("--limit", type=int, default=10, help="Maximum records to show")
    args = parser.parse_args()

    query_audit_logs(action=args.action, status=args.status, limit=args.limit)


if __name__ == "__main__":
    main()
