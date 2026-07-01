"""
database.py
SQLite persistence layer for CareerTwin AI.
Handles: users, skills, career matches, roadmap progress, interview history.
"""

import sqlite3
import os
from contextlib import contextmanager
from datetime import datetime

# Allow override via env var so Cloud Run / Docker can mount a volume
DB_PATH = os.environ.get("DB_PATH", "database.db")



@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    """Create all tables if they don't exist. Call once at app startup."""
    with get_conn() as conn:
        c = conn.cursor()

        c.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS skills (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                skill_name TEXT NOT NULL,
                proficiency TEXT DEFAULT 'Beginner',
                added_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS career_matches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                role_name TEXT NOT NULL,
                match_score INTEGER,
                rationale TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS skill_gaps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                target_role TEXT NOT NULL,
                missing_skill TEXT NOT NULL,
                priority TEXT DEFAULT 'Medium',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS roadmap_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                target_role TEXT NOT NULL,
                day_number INTEGER NOT NULL,
                task_description TEXT NOT NULL,
                is_completed INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS interview_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                target_role TEXT NOT NULL,
                question TEXT NOT NULL,
                answer TEXT,
                score INTEGER,
                feedback TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS resume_reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                filename TEXT,
                suggestions TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                tech_stack TEXT,
                link TEXT,
                added_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)


# ---------- Users ----------

def create_or_get_user(name: str, email: str) -> int:
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("SELECT id FROM users WHERE email = ?", (email,))
        row = c.fetchone()
        if row:
            return row["id"]
        c.execute("INSERT INTO users (name, email) VALUES (?, ?)", (name, email))
        return c.lastrowid


# ---------- Skills ----------

def add_skill(user_id: int, skill_name: str, proficiency: str = "Beginner"):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO skills (user_id, skill_name, proficiency) VALUES (?, ?, ?)",
            (user_id, skill_name, proficiency),
        )


def get_skills(user_id: int):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM skills WHERE user_id = ? ORDER BY added_at DESC", (user_id,)
        ).fetchall()
        return [dict(r) for r in rows]


def clear_skills(user_id: int):
    with get_conn() as conn:
        conn.execute("DELETE FROM skills WHERE user_id = ?", (user_id,))


# ---------- Career Matches ----------

def save_career_matches(user_id: int, matches: list):
    """matches: list of dicts {role_name, match_score, rationale}"""
    with get_conn() as conn:
        for m in matches:
            conn.execute(
                "INSERT INTO career_matches (user_id, role_name, match_score, rationale) VALUES (?, ?, ?, ?)",
                (user_id, m["role_name"], m.get("match_score", 0), m.get("rationale", "")),
            )


def get_career_matches(user_id: int):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM career_matches WHERE user_id = ? ORDER BY created_at DESC", (user_id,)
        ).fetchall()
        return [dict(r) for r in rows]


# ---------- Skill Gaps ----------

def save_skill_gaps(user_id: int, target_role: str, gaps: list):
    with get_conn() as conn:
        for g in gaps:
            conn.execute(
                "INSERT INTO skill_gaps (user_id, target_role, missing_skill, priority) VALUES (?, ?, ?, ?)",
                (user_id, target_role, g["skill"], g.get("priority", "Medium")),
            )


def get_skill_gaps(user_id: int, target_role: str = None):
    with get_conn() as conn:
        if target_role:
            rows = conn.execute(
                "SELECT * FROM skill_gaps WHERE user_id = ? AND target_role = ? ORDER BY created_at DESC",
                (user_id, target_role),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM skill_gaps WHERE user_id = ? ORDER BY created_at DESC", (user_id,)
            ).fetchall()
        return [dict(r) for r in rows]


# ---------- Roadmap ----------

def save_roadmap_tasks(user_id: int, target_role: str, tasks: list):
    """tasks: list of dicts {day_number, task_description}"""
    with get_conn() as conn:
        for t in tasks:
            conn.execute(
                "INSERT INTO roadmap_tasks (user_id, target_role, day_number, task_description) VALUES (?, ?, ?, ?)",
                (user_id, target_role, t["day_number"], t["task_description"]),
            )


def get_roadmap_tasks(user_id: int, target_role: str):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM roadmap_tasks WHERE user_id = ? AND target_role = ? ORDER BY day_number ASC",
            (user_id, target_role),
        ).fetchall()
        return [dict(r) for r in rows]


def mark_task_complete(task_id: int, completed: bool = True):
    with get_conn() as conn:
        conn.execute(
            "UPDATE roadmap_tasks SET is_completed = ? WHERE id = ?",
            (1 if completed else 0, task_id),
        )


def get_roadmap_completion_pct(user_id: int, target_role: str) -> float:
    with get_conn() as conn:
        total = conn.execute(
            "SELECT COUNT(*) as cnt FROM roadmap_tasks WHERE user_id = ? AND target_role = ?",
            (user_id, target_role),
        ).fetchone()["cnt"]
        if total == 0:
            return 0.0
        done = conn.execute(
            "SELECT COUNT(*) as cnt FROM roadmap_tasks WHERE user_id = ? AND target_role = ? AND is_completed = 1",
            (user_id, target_role),
        ).fetchone()["cnt"]
        return round((done / total) * 100, 1)


# ---------- Interview History ----------

def save_interview_result(user_id: int, target_role: str, question: str, answer: str, score: int, feedback: str):
    with get_conn() as conn:
        conn.execute(
            """INSERT INTO interview_history
               (user_id, target_role, question, answer, score, feedback)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (user_id, target_role, question, answer, score, feedback),
        )


def get_interview_history(user_id: int):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM interview_history WHERE user_id = ? ORDER BY created_at ASC", (user_id,)
        ).fetchall()
        return [dict(r) for r in rows]


# ---------- Resume Reviews ----------

def save_resume_review(user_id: int, filename: str, suggestions: str):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO resume_reviews (user_id, filename, suggestions) VALUES (?, ?, ?)",
            (user_id, filename, suggestions),
        )


def get_resume_reviews(user_id: int):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM resume_reviews WHERE user_id = ? ORDER BY created_at DESC", (user_id,)
        ).fetchall()
        return [dict(r) for r in rows]


# ---------- Projects ----------

def add_project(user_id: int, title: str, description: str, tech_stack: str, link: str = ""):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO projects (user_id, title, description, tech_stack, link) VALUES (?, ?, ?, ?, ?)",
            (user_id, title, description, tech_stack, link),
        )


def get_projects(user_id: int):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM projects WHERE user_id = ? ORDER BY added_at DESC", (user_id,)
        ).fetchall()
        return [dict(r) for r in rows]


def delete_project(project_id: int, user_id: int):
    with get_conn() as conn:
        conn.execute(
            "DELETE FROM projects WHERE id = ? AND user_id = ?",
            (project_id, user_id),
        )
