"""
database/db_manager.py
SQLite persistence layer for AI Interview Coach
"""
import sqlite3
import json
import logging
from datetime import datetime
from config import DB_PATH

log = logging.getLogger(__name__)


class DatabaseManager:
    def __init__(self):
        self.path = str(DB_PATH)
        self._init_db()

    # ── connection ────────────────────────────────────
    def _conn(self):
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    # ── schema ────────────────────────────────────────
    def _init_db(self):
        with self._conn() as c:
            c.executescript("""
            CREATE TABLE IF NOT EXISTS interview_sessions (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at  TEXT NOT NULL,
                mode        TEXT,
                domain      TEXT,
                difficulty  TEXT,
                score       REAL,
                duration    INTEGER,
                questions   TEXT,
                answers     TEXT,
                feedback    TEXT
            );
            CREATE TABLE IF NOT EXISTS resume_analyses (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at     TEXT NOT NULL,
                filename       TEXT,
                ats_score      REAL,
                skills_found   TEXT,
                missing_skills TEXT,
                suggestions    TEXT,
                full_text      TEXT
            );
            CREATE TABLE IF NOT EXISTS roadmap_items (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at  TEXT NOT NULL,
                title       TEXT,
                domain      TEXT,
                items       TEXT,
                status      TEXT DEFAULT 'active'
            );
            CREATE TABLE IF NOT EXISTS app_settings (
                key   TEXT PRIMARY KEY,
                value TEXT
            );
            """)
        log.info("Database initialised at %s", self.path)

    # ── interview sessions ────────────────────────────
    def save_session(self, mode, domain, difficulty, score, duration,
                     questions, answers, feedback):
        with self._conn() as c:
            c.execute(
                """INSERT INTO interview_sessions
                   (created_at,mode,domain,difficulty,score,duration,questions,answers,feedback)
                   VALUES (?,?,?,?,?,?,?,?,?)""",
                (datetime.now().isoformat(), mode, domain, difficulty,
                 score, duration, json.dumps(questions), json.dumps(answers), feedback)
            )

    def get_sessions(self, limit=50):
        with self._conn() as c:
            rows = c.execute(
                "SELECT * FROM interview_sessions ORDER BY created_at DESC LIMIT ?", (limit,)
            ).fetchall()
        return [dict(r) for r in rows]

    def get_session_stats(self):
        with self._conn() as c:
            row = c.execute(
                """SELECT COUNT(*) as total, AVG(score) as avg_score,
                          MAX(score) as best_score, SUM(duration) as total_time
                   FROM interview_sessions"""
            ).fetchone()
        return dict(row) if row else {"total": 0, "avg_score": 0, "best_score": 0, "total_time": 0}

    def get_score_trend(self, limit=10):
        with self._conn() as c:
            rows = c.execute(
                "SELECT created_at, score FROM interview_sessions ORDER BY created_at ASC LIMIT ?",
                (limit,)
            ).fetchall()
        return [dict(r) for r in rows]

    # ── resume analyses ───────────────────────────────
    def save_resume_analysis(self, filename, ats_score, skills_found,
                              missing_skills, suggestions, full_text=""):
        with self._conn() as c:
            c.execute(
                """INSERT INTO resume_analyses
                   (created_at,filename,ats_score,skills_found,missing_skills,suggestions,full_text)
                   VALUES (?,?,?,?,?,?,?)""",
                (datetime.now().isoformat(), filename, ats_score,
                 json.dumps(skills_found), json.dumps(missing_skills),
                 suggestions, full_text)
            )

    def get_resume_analyses(self, limit=20):
        with self._conn() as c:
            rows = c.execute(
                "SELECT * FROM resume_analyses ORDER BY created_at DESC LIMIT ?", (limit,)
            ).fetchall()
        results = []
        for r in rows:
            d = dict(r)
            for k in ("skills_found", "missing_skills"):
                try:
                    d[k] = json.loads(d[k] or "[]")
                except Exception:
                    d[k] = []
            results.append(d)
        return results

    # ── roadmap ───────────────────────────────────────
    def save_roadmap(self, title, domain, items):
        with self._conn() as c:
            c.execute(
                "INSERT INTO roadmap_items (created_at,title,domain,items) VALUES (?,?,?,?)",
                (datetime.now().isoformat(), title, domain, json.dumps(items))
            )

    def get_roadmaps(self, limit=10):
        with self._conn() as c:
            rows = c.execute(
                "SELECT * FROM roadmap_items ORDER BY created_at DESC LIMIT ?", (limit,)
            ).fetchall()
        results = []
        for r in rows:
            d = dict(r)
            try:
                d["items"] = json.loads(d["items"] or "[]")
            except Exception:
                d["items"] = []
            results.append(d)
        return results

    # ── settings ─────────────────────────────────────
    def get_setting(self, key, default=""):
        with self._conn() as c:
            row = c.execute("SELECT value FROM app_settings WHERE key=?", (key,)).fetchone()
        return row["value"] if row else default

    def set_setting(self, key, value):
        with self._conn() as c:
            c.execute("INSERT OR REPLACE INTO app_settings (key,value) VALUES (?,?)", (key, value))