"""SQLite log of bird visits."""

from __future__ import annotations

import sqlite3
import threading
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS visits (
    id         INTEGER PRIMARY KEY,
    sci        TEXT NOT NULL,
    started    REAL NOT NULL,
    ended      REAL NOT NULL,
    best_score REAL NOT NULL,
    photo      TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS visits_started ON visits(started);
"""


class Store:
    def __init__(self, path: str | Path):
        self._db = sqlite3.connect(str(path), check_same_thread=False)
        self._db.row_factory = sqlite3.Row
        self._lock = threading.Lock()
        with self._lock:
            self._db.executescript(SCHEMA)

    def open_visit(self, sci: str, t: float, score: float, photo: str) -> int:
        with self._lock, self._db:
            cur = self._db.execute(
                "INSERT INTO visits (sci, started, ended, best_score, photo) VALUES (?, ?, ?, ?, ?)",
                (sci, t, t, score, photo),
            )
            return cur.lastrowid

    def extend_visit(self, visit_id: int, t: float, score: float) -> None:
        with self._lock, self._db:
            self._db.execute(
                "UPDATE visits SET ended = MAX(ended, ?), best_score = MAX(best_score, ?) WHERE id = ?",
                (t, score, visit_id),
            )

    def species_since(self, since: float) -> list[dict]:
        """One row per species seen since `since`, most visits first, with its best photo."""
        with self._lock:
            rows = self._db.execute(
                """
                WITH v AS (SELECT * FROM visits WHERE started >= ?),
                best AS (
                    SELECT sci, photo FROM (
                        SELECT sci, photo,
                               ROW_NUMBER() OVER (PARTITION BY sci ORDER BY best_score DESC) AS rn
                        FROM v)
                    WHERE rn = 1)
                SELECT v.sci, COUNT(*) AS visits, MIN(v.started) AS first_seen,
                       MAX(v.ended) AS last_seen, MAX(v.best_score) AS best_score, best.photo
                FROM v JOIN best USING (sci)
                GROUP BY v.sci
                ORDER BY visits DESC, last_seen DESC
                """,
                (since,),
            ).fetchall()
        return [dict(r) for r in rows]

    def recent(self, limit: int = 50) -> list[dict]:
        with self._lock:
            rows = self._db.execute(
                "SELECT * FROM visits ORDER BY started DESC LIMIT ?", (limit,)
            ).fetchall()
        return [dict(r) for r in rows]
