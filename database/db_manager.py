"""
database/db_manager.py — SQLite Database Manager
Full ORM-style layer for AI Interview Coach
Tables: users, resumes, interviews, interview_questions, analytics, roadmap_items
"""

import sqlite3
import json
import logging
from datetime import datetime, date
from pathlib import Path
from typing import Optional, List, Dict, Any

from config import DB_PATH

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Central SQLite manager using context-manager connections.
    All public methods return plain dicts / lists for easy UI consumption.
    """

    def __init__(self):
        self.db_path = str(DB_PATH)
        self._init_schema()

    # ─────────────────────────────────────────
    #  CONNECTION HELPER
    # ─────────────────────────────────────────
    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=10)
        conn.row_factory = sqlite3.Row          # dict-like access
        conn.execute("PRAGMA journal_mode=WAL")  # better concurrent writes
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    # ─────────────────────────────────────────
    #  SCHEMA INITIALISATION
    # ─────────────────────────────────────────
    def _init_schema(self):
        ddl = """
        -- Users / profile
        CREATE TABLE IF NOT EXISTS users (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            name            TEXT    NOT NULL DEFAULT 'User',
            email           TEXT    UNIQUE,
            target_role     TEXT,
            experience_yrs  REAL    DEFAULT 0,
            gemini_api_key  TEXT    DEFAULT '',
            created_at      TEXT    DEFAULT (datetime('now')),
            updated_at      TEXT    DEFAULT (datetime('now'))
        );

        -- Uploaded resumes
        CREATE TABLE IF NOT EXISTS resumes (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id         INTEGER NOT NULL DEFAULT 1,
            filename        TEXT    NOT NULL,
            file_path       TEXT,
            raw_text        TEXT,
            ats_score       REAL    DEFAULT 0,
            skills_found    TEXT    DEFAULT '[]',   -- JSON list
            missing_skills  TEXT    DEFAULT '[]',
            suggestions     TEXT    DEFAULT '[]',
            gemini_review   TEXT    DEFAULT '',
            created_at      TEXT    DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        -- Interview sessions
        CREATE TABLE IF NOT EXISTS interviews (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id         INTEGER NOT NULL DEFAULT 1,
            mode            TEXT    NOT NULL,       -- Technical / HR / Mixed
            domain          TEXT    DEFAULT '',
            difficulty      TEXT    DEFAULT 'Mid-level',
            total_questions INTEGER DEFAULT 0,
            answered        INTEGER DEFAULT 0,
            avg_score       REAL    DEFAULT 0,
            confidence_score REAL   DEFAULT 0,
            duration_secs   INTEGER DEFAULT 0,
            status          TEXT    DEFAULT 'in_progress',  -- in_progress / completed
            created_at      TEXT    DEFAULT (datetime('now')),
            completed_at    TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        -- Individual Q&A pairs per interview
        CREATE TABLE IF NOT EXISTS interview_questions (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            interview_id    INTEGER NOT NULL,
            question_num    INTEGER NOT NULL,
            question_text   TEXT    NOT NULL,
            user_answer     TEXT    DEFAULT '',
            ai_feedback     TEXT    DEFAULT '',
            score           REAL    DEFAULT 0,
            follow_up       TEXT    DEFAULT '',
            time_taken_secs INTEGER DEFAULT 0,
            created_at      TEXT    DEFAULT (datetime('now')),
            FOREIGN KEY (interview_id) REFERENCES interviews(id)
        );

        -- Daily analytics snapshots
        CREATE TABLE IF NOT EXISTS analytics (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id         INTEGER NOT NULL DEFAULT 1,
            snapshot_date   TEXT    NOT NULL DEFAULT (date('now')),
            ats_score       REAL    DEFAULT 0,
            readiness_score REAL    DEFAULT 0,
            interview_count INTEGER DEFAULT 0,
            avg_interview_score REAL DEFAULT 0,
            skills_json     TEXT    DEFAULT '{}',   -- {skill: proficiency_pct}
            weak_skills     TEXT    DEFAULT '[]',
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        -- Learning roadmap items
        CREATE TABLE IF NOT EXISTS roadmap_items (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id         INTEGER NOT NULL DEFAULT 1,
            skill           TEXT    NOT NULL,
            resource_title  TEXT    DEFAULT '',
            resource_url    TEXT    DEFAULT '',
            resource_type   TEXT    DEFAULT 'Article', -- Article/Video/Course/Practice
            priority        TEXT    DEFAULT 'Medium',
            status          TEXT    DEFAULT 'pending', -- pending/in_progress/done
            ai_notes        TEXT    DEFAULT '',
            created_at      TEXT    DEFAULT (datetime('now')),
            updated_at      TEXT    DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        -- Ensure default user exists
        INSERT OR IGNORE INTO users (id, name, email, target_role)
        VALUES (1, 'User', 'user@aic.app', 'Software Engineer');
        """
        with self._get_conn() as conn:
            conn.executescript(ddl)
        logger.info("Database schema initialised at %s", self.db_path)

    # ─────────────────────────────────────────
    #  USER
    # ─────────────────────────────────────────
    def get_user(self, user_id: int = 1) -> Dict:
        with self._get_conn() as conn:
            row = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
            return dict(row) if row else {}

    def update_user(self, user_id: int = 1, **kwargs) -> bool:
        allowed = {"name", "email", "target_role", "experience_yrs", "gemini_api_key"}
        fields = {k: v for k, v in kwargs.items() if k in allowed}
        if not fields:
            return False
        fields["updated_at"] = datetime.now().isoformat()
        cols = ", ".join(f"{k}=?" for k in fields)
        vals = list(fields.values()) + [user_id]
        with self._get_conn() as conn:
            conn.execute(f"UPDATE users SET {cols} WHERE id=?", vals)
        return True

    # ─────────────────────────────────────────
    #  RESUMES
    # ─────────────────────────────────────────
    def save_resume(self, data: Dict) -> int:
        cols = ["user_id", "filename", "file_path", "raw_text", "ats_score",
                "skills_found", "missing_skills", "suggestions", "gemini_review"]
        vals = [
            data.get("user_id", 1),
            data.get("filename", ""),
            data.get("file_path", ""),
            data.get("raw_text", ""),
            data.get("ats_score", 0),
            json.dumps(data.get("skills_found", [])),
            json.dumps(data.get("missing_skills", [])),
            json.dumps(data.get("suggestions", [])),
            data.get("gemini_review", ""),
        ]
        with self._get_conn() as conn:
            cur = conn.execute(
                f"INSERT INTO resumes ({','.join(cols)}) VALUES ({','.join('?'*len(cols))})",
                vals
            )
            return cur.lastrowid

    def get_latest_resume(self, user_id: int = 1) -> Optional[Dict]:
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM resumes WHERE user_id=? ORDER BY created_at DESC LIMIT 1",
                (user_id,)
            ).fetchone()
            if not row:
                return None
            r = dict(row)
            for field in ["skills_found", "missing_skills", "suggestions"]:
                try:
                    r[field] = json.loads(r[field])
                except Exception:
                    r[field] = []
            return r

    def get_all_resumes(self, user_id: int = 1) -> List[Dict]:
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT id, filename, ats_score, created_at FROM resumes "
                "WHERE user_id=? ORDER BY created_at DESC", (user_id,)
            ).fetchall()
            return [dict(r) for r in rows]

    # ─────────────────────────────────────────
    #  INTERVIEWS
    # ─────────────────────────────────────────
    def create_interview(self, mode: str, domain: str = "",
                         difficulty: str = "Mid-level",
                         total_questions: int = 5) -> int:
        with self._get_conn() as conn:
            cur = conn.execute(
                "INSERT INTO interviews (mode, domain, difficulty, total_questions) "
                "VALUES (?,?,?,?)",
                (mode, domain, difficulty, total_questions)
            )
            return cur.lastrowid

    def save_question(self, interview_id: int, question_num: int,
                      question_text: str, user_answer: str = "",
                      ai_feedback: str = "", score: float = 0,
                      follow_up: str = "", time_taken: int = 0) -> int:
        with self._get_conn() as conn:
            cur = conn.execute(
                "INSERT INTO interview_questions "
                "(interview_id, question_num, question_text, user_answer, "
                " ai_feedback, score, follow_up, time_taken_secs) "
                "VALUES (?,?,?,?,?,?,?,?)",
                (interview_id, question_num, question_text, user_answer,
                 ai_feedback, score, follow_up, time_taken)
            )
            return cur.lastrowid

    def complete_interview(self, interview_id: int,
                           avg_score: float, confidence: float,
                           duration_secs: int, answered: int):
        with self._get_conn() as conn:
            conn.execute(
                "UPDATE interviews SET status='completed', avg_score=?, "
                "confidence_score=?, duration_secs=?, answered=?, "
                "completed_at=datetime('now') WHERE id=?",
                (avg_score, confidence, duration_secs, answered, interview_id)
            )

    def get_interview(self, interview_id: int) -> Optional[Dict]:
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM interviews WHERE id=?", (interview_id,)
            ).fetchone()
            return dict(row) if row else None

    def get_interview_questions(self, interview_id: int) -> List[Dict]:
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM interview_questions WHERE interview_id=? "
                "ORDER BY question_num", (interview_id,)
            ).fetchall()
            return [dict(r) for r in rows]

    def get_recent_interviews(self, user_id: int = 1, limit: int = 10) -> List[Dict]:
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT id, mode, domain, difficulty, avg_score, confidence_score, "
                "answered, total_questions, status, created_at, completed_at "
                "FROM interviews WHERE user_id=? ORDER BY created_at DESC LIMIT ?",
                (user_id, limit)
            ).fetchall()
            return [dict(r) for r in rows]

    # ─────────────────────────────────────────
    #  ANALYTICS
    # ─────────────────────────────────────────
    def upsert_analytics(self, data: Dict):
        today = date.today().isoformat()
        with self._get_conn() as conn:
            existing = conn.execute(
                "SELECT id FROM analytics WHERE user_id=1 AND snapshot_date=?",
                (today,)
            ).fetchone()
            if existing:
                conn.execute(
                    "UPDATE analytics SET ats_score=?, readiness_score=?, "
                    "interview_count=?, avg_interview_score=?, skills_json=?, "
                    "weak_skills=? WHERE id=?",
                    (
                        data.get("ats_score", 0),
                        data.get("readiness_score", 0),
                        data.get("interview_count", 0),
                        data.get("avg_interview_score", 0),
                        json.dumps(data.get("skills_json", {})),
                        json.dumps(data.get("weak_skills", [])),
                        existing["id"]
                    )
                )
            else:
                conn.execute(
                    "INSERT INTO analytics "
                    "(ats_score, readiness_score, interview_count, "
                    " avg_interview_score, skills_json, weak_skills) "
                    "VALUES (?,?,?,?,?,?)",
                    (
                        data.get("ats_score", 0),
                        data.get("readiness_score", 0),
                        data.get("interview_count", 0),
                        data.get("avg_interview_score", 0),
                        json.dumps(data.get("skills_json", {})),
                        json.dumps(data.get("weak_skills", []))
                    )
                )

    def get_analytics_history(self, days: int = 30) -> List[Dict]:
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM analytics WHERE user_id=1 "
                "ORDER BY snapshot_date DESC LIMIT ?", (days,)
            ).fetchall()
            result = []
            for r in rows:
                d = dict(r)
                try:
                    d["skills_json"] = json.loads(d["skills_json"])
                except Exception:
                    d["skills_json"] = {}
                try:
                    d["weak_skills"] = json.loads(d["weak_skills"])
                except Exception:
                    d["weak_skills"] = []
                result.append(d)
            return result

    def get_dashboard_stats(self, user_id: int = 1) -> Dict:
        """Return all KPIs needed for the Home Dashboard."""
        with self._get_conn() as conn:
            # Latest ATS score
            resume = conn.execute(
                "SELECT ats_score, skills_found FROM resumes "
                "WHERE user_id=? ORDER BY created_at DESC LIMIT 1", (user_id,)
            ).fetchone()

            # Interview stats
            ivw = conn.execute(
                "SELECT COUNT(*) as cnt, AVG(avg_score) as avg_s, "
                "AVG(confidence_score) as avg_c "
                "FROM interviews WHERE user_id=? AND status='completed'", (user_id,)
            ).fetchone()

            # Recent 7 interviews for trend
            recent = conn.execute(
                "SELECT avg_score, created_at FROM interviews "
                "WHERE user_id=? AND status='completed' "
                "ORDER BY created_at DESC LIMIT 7", (user_id,)
            ).fetchall()

        ats = resume["ats_score"] if resume else 0
        skills_raw = resume["skills_found"] if resume else "[]"
        try:
            skills_list = json.loads(skills_raw)
        except Exception:
            skills_list = []

        readiness = min(100, (ats * 0.4 + (ivw["avg_s"] or 0) * 0.6)) if ivw["cnt"] else ats * 0.5
        return {
            "ats_score":        round(ats, 1),
            "readiness_score":  round(readiness, 1),
            "interview_count":  ivw["cnt"] or 0,
            "avg_score":        round(ivw["avg_s"] or 0, 1),
            "avg_confidence":   round(ivw["avg_c"] or 0, 1),
            "skills_found":     skills_list,
            "score_trend":      [dict(r) for r in recent],
        }

    # ─────────────────────────────────────────
    #  ROADMAP
    # ─────────────────────────────────────────
    def save_roadmap_items(self, items: List[Dict], user_id: int = 1):
        with self._get_conn() as conn:
            for item in items:
                conn.execute(
                    "INSERT INTO roadmap_items "
                    "(user_id, skill, resource_title, resource_url, "
                    " resource_type, priority, ai_notes) "
                    "VALUES (?,?,?,?,?,?,?)",
                    (
                        user_id,
                        item.get("skill", ""),
                        item.get("resource_title", ""),
                        item.get("resource_url", ""),
                        item.get("resource_type", "Article"),
                        item.get("priority", "Medium"),
                        item.get("ai_notes", ""),
                    )
                )

    def get_roadmap(self, user_id: int = 1) -> List[Dict]:
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM roadmap_items WHERE user_id=? "
                "ORDER BY CASE priority WHEN 'High' THEN 1 WHEN 'Medium' THEN 2 ELSE 3 END, "
                "created_at DESC", (user_id,)
            ).fetchall()
            return [dict(r) for r in rows]

    def update_roadmap_status(self, item_id: int, status: str):
        with self._get_conn() as conn:
            conn.execute(
                "UPDATE roadmap_items SET status=?, updated_at=datetime('now') WHERE id=?",
                (status, item_id)
            )

    def clear_roadmap(self, user_id: int = 1):
        with self._get_conn() as conn:
            conn.execute("DELETE FROM roadmap_items WHERE user_id=?", (user_id,))


# Singleton
_db_instance: Optional[DatabaseManager] = None

def get_db() -> DatabaseManager:
    global _db_instance
    if _db_instance is None:
        _db_instance = DatabaseManager()
    return _db_instance