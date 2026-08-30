from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from app.config import resolve_repo_path


class CaseRepository:
    def __init__(self, database_path: str) -> None:
        self.path = Path(resolve_repo_path(database_path))
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute("""
                CREATE TABLE IF NOT EXISTS cases (
                    case_id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    document_family TEXT NOT NULL,
                    claimed_identity TEXT,
                    document_number TEXT,
                    outcome TEXT NOT NULL,
                    major_findings_json TEXT NOT NULL,
                    coverage_json TEXT NOT NULL,
                    autopsy_json TEXT NOT NULL
                )
            """)

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    def save(self, autopsy: dict[str, Any]) -> None:
        visible = autopsy.get("visible_document_data", {}).get("visible_fields", {})
        with self._connect() as connection:
            connection.execute(
                "INSERT OR REPLACE INTO cases VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    autopsy["case_id"], autopsy["created_at"], autopsy.get("document_family") or "UNCLASSIFIED",
                    visible.get("holder_name"), visible.get("document_number"), autopsy["outcome"],
                    json.dumps(autopsy.get("critical_findings", [])), json.dumps(autopsy.get("evidence_coverage", {})), json.dumps(autopsy),
                ),
            )

    def get(self, case_id: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute("SELECT autopsy_json FROM cases WHERE case_id = ?", (case_id,)).fetchone()
        return json.loads(row[0]) if row else None

    def list(self, limit: int = 50) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute("SELECT case_id, created_at, document_family, claimed_identity, document_number, outcome, major_findings_json, coverage_json FROM cases ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
        return [{**dict(row), "major_findings": json.loads(row["major_findings_json"]), "coverage": json.loads(row["coverage_json"])} for row in rows]

    def summary(self) -> dict[str, int]:
        with self._connect() as connection:
            rows = connection.execute("SELECT outcome, COUNT(*) AS count FROM cases GROUP BY outcome").fetchall()
        counts = {row["outcome"]: row["count"] for row in rows}
        return {"cases_screened": sum(counts.values()), "refer": counts.get("REFER", 0), "high_risk": counts.get("HIGH_RISK", 0), "indeterminate": counts.get("INDETERMINATE", 0), "low_risk": counts.get("LOW_RISK", 0)}
