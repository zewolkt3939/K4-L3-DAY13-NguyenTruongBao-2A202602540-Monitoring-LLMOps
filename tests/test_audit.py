from __future__ import annotations

import json
from pathlib import Path

from app.audit import log_audit_event


def test_log_audit_event(tmp_path: Path, monkeypatch) -> None:
    test_audit_path = tmp_path / "test_audit.jsonl"
    monkeypatch.setattr("app.audit.AUDIT_LOG_PATH", test_audit_path)

    rec = log_audit_event(
        actor="admin",
        action="incident_enabled",
        resource="incident/rag_slow",
        status="success",
        details={"incident_name": "rag_slow"},
        retention_days=90,
    )

    assert rec["actor"] == "admin"
    assert rec["action"] == "incident_enabled"
    assert rec["status"] == "success"
    assert rec["resource"] == "incident/rag_slow"
    assert rec["retention_days"] == 90
    assert "ts" in rec

    assert test_audit_path.exists()
    lines = test_audit_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1

    stored = json.loads(lines[0])
    assert stored["actor"] == "admin"
    assert stored["details"]["incident_name"] == "rag_slow"
