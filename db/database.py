"""SQLite database connection and schema management."""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "gold_lms.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Create all tables if they don't exist. Called on app startup."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            full_name TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('rep','manager','admin')),
            manager_id INTEGER REFERENCES users(id),
            is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS cohorts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            status TEXT DEFAULT 'active' CHECK(status IN ('upcoming','active','completed','archived')),
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS cohort_enrollments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cohort_id INTEGER NOT NULL REFERENCES cohorts(id),
            user_id INTEGER NOT NULL REFERENCES users(id),
            hire_date TEXT NOT NULL,
            enrollment_date TEXT DEFAULT (datetime('now')),
            status TEXT DEFAULT 'active' CHECK(status IN ('active','completed','dropped','on_hold')),
            UNIQUE(cohort_id, user_id)
        );

        CREATE TABLE IF NOT EXISTS certifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            description TEXT,
            category TEXT,
            display_order INTEGER DEFAULT 0,
            target_week INTEGER,
            max_attempts INTEGER DEFAULT 3,
            is_active INTEGER DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS certification_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id),
            certification_id INTEGER NOT NULL REFERENCES certifications(id),
            cohort_id INTEGER NOT NULL REFERENCES cohorts(id),
            attempt_number INTEGER NOT NULL DEFAULT 1,
            result TEXT NOT NULL CHECK(result IN ('pass','fail')),
            score REAL,
            evaluated_by INTEGER REFERENCES users(id),
            notes TEXT,
            attempt_date TEXT DEFAULT (date('now')),
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS modules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            slug TEXT NOT NULL UNIQUE,
            title TEXT NOT NULL,
            description TEXT,
            display_order INTEGER DEFAULT 0,
            week_target INTEGER,
            vertical TEXT,
            is_required INTEGER DEFAULT 1,
            is_active INTEGER DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS app_config (
            key TEXT PRIMARY KEY,
            value TEXT
        );

        CREATE TABLE IF NOT EXISTS user_preferences (
            user_id INTEGER PRIMARY KEY REFERENCES users(id),
            vertical TEXT
        );

        CREATE TABLE IF NOT EXISTS lessons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            module_id INTEGER NOT NULL REFERENCES modules(id),
            slug TEXT NOT NULL,
            title TEXT NOT NULL,
            display_order INTEGER DEFAULT 0,
            content_type TEXT NOT NULL CHECK(content_type IN ('html','video','link','doc')),
            content_body TEXT,
            url TEXT,
            est_minutes INTEGER,
            UNIQUE(module_id, slug)
        );

        CREATE TABLE IF NOT EXISTS lesson_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id),
            lesson_id INTEGER NOT NULL REFERENCES lessons(id),
            status TEXT DEFAULT 'not_started' CHECK(status IN ('not_started','in_progress','completed')),
            completed_at TEXT,
            UNIQUE(user_id, lesson_id)
        );

        CREATE TABLE IF NOT EXISTS activity_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER REFERENCES users(id),
            action TEXT NOT NULL,
            entity_type TEXT,
            entity_id INTEGER,
            details TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );
    """)

    conn.commit()

    # Check if seed data is needed
    row = cursor.execute("SELECT COUNT(*) FROM users").fetchone()
    if row[0] == 0:
        from db.seed import seed_all
        seed_all(conn)

    conn.close()


def query(sql, params=(), one=False):
    """Execute a read query and return results as list of dicts."""
    conn = get_connection()
    cursor = conn.execute(sql, params)
    rows = cursor.fetchall()
    conn.close()
    if one:
        return dict(rows[0]) if rows else None
    return [dict(r) for r in rows]


def execute(sql, params=()):
    """Execute a write query and return lastrowid."""
    conn = get_connection()
    cursor = conn.execute(sql, params)
    conn.commit()
    lastrowid = cursor.lastrowid
    conn.close()
    return lastrowid


def execute_many(sql, param_list):
    """Execute a write query with many params."""
    conn = get_connection()
    conn.executemany(sql, param_list)
    conn.commit()
    conn.close()
