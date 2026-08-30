from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

from app.config import resolve_repo_path


class LocalIdentityLinkageStore:
    source = "LOCAL_PROTOTYPE_IDENTITY_LINKAGE"

    def __init__(self, database_path: str, threshold: float = 0.50) -> None:
        self.path = Path(resolve_repo_path(database_path))
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.threshold = threshold
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute("""
                CREATE TABLE IF NOT EXISTS biometric_enrolments (
                    case_id TEXT PRIMARY KEY,
                    identity_reference TEXT NOT NULL,
                    claimed_name TEXT,
                    document_number TEXT,
                    embedding_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)

    @staticmethod
    def _different_identity(name_a: str | None, document_a: str | None, name_b: str | None, document_b: str | None) -> bool:
        norm = lambda value: "".join((value or "").upper().split())
        return bool((norm(document_a) and norm(document_b) and norm(document_a) != norm(document_b)) or (norm(name_a) and norm(name_b) and norm(name_a) != norm(name_b)))

    def search_and_enrol(self, case_id: str, name: str | None, document_number: str | None, embedding: list[float] | None) -> dict[str, Any]:
        if not embedding:
            return {"status": "UNAVAILABLE", "source": self.source, "reason": "No usable local biometric embedding was available.", "matches": [], "enrolled": False}
        vector = np.asarray(embedding, dtype=np.float32)
        matches: list[dict[str, Any]] = []
        with self._connect() as connection:
            for row in connection.execute("SELECT * FROM biometric_enrolments WHERE case_id != ?", (case_id,)):
                candidate = np.asarray(json.loads(row["embedding_json"]), dtype=np.float32)
                similarity = float(np.dot(vector, candidate) / max(float(np.linalg.norm(vector) * np.linalg.norm(candidate)), 1e-9))
                if similarity >= self.threshold and self._different_identity(name, document_number, row["claimed_name"], row["document_number"]):
                    matches.append({
                        "case_id": row["case_id"],
                        "identity_reference": row["identity_reference"],
                        "claimed_name": row["claimed_name"],
                        "document_number": row["document_number"],
                        "similarity": round(similarity, 6),
                        "finding": "POSSIBLE_MULTI_IDENTITY_LINKAGE",
                    })
            identity_reference = matches[0]["identity_reference"] if matches else f"Biometric Cluster {self._next_cluster_number(connection):03d}"
            connection.execute(
                "INSERT OR REPLACE INTO biometric_enrolments VALUES (?, ?, ?, ?, ?, ?)",
                (case_id, identity_reference, name, document_number, json.dumps(vector.tolist()), datetime.now(timezone.utc).isoformat()),
            )
        return {
            "status": "SUSPICIOUS" if matches else "PASS",
            "source": self.source,
            "reason": "A similar local biometric embedding is linked to substantially different claimed identity data." if matches else "No conflicting claimed identity was linked above the prototype threshold.",
            "matches": matches,
            "identity_reference": identity_reference,
            "configured_prototype_threshold": self.threshold,
            "enrolled": True,
            "legal_conclusion": None,
        }

    @staticmethod
    def _next_cluster_number(connection: sqlite3.Connection) -> int:
        rows = connection.execute("SELECT identity_reference FROM biometric_enrolments").fetchall()
        numbers = [int(row[0].rsplit(" ", 1)[-1]) for row in rows if row[0].startswith("Biometric Cluster ") and row[0].rsplit(" ", 1)[-1].isdigit()]
        return max(numbers, default=0) + 1

    def clusters(self) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute("SELECT identity_reference, case_id, claimed_name, document_number, created_at FROM biometric_enrolments ORDER BY identity_reference, created_at DESC").fetchall()
        grouped: dict[str, list[dict[str, Any]]] = {}
        for row in rows:
            grouped.setdefault(row["identity_reference"], []).append(dict(row))
        return [{"identity_reference": key, "credentials": values, "source": self.source} for key, values in grouped.items()]
