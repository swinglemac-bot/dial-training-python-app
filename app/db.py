from __future__ import annotations

import sqlite3
from pathlib import Path
from threading import RLock

from .config import config

_lock = RLock()


def _connect() -> sqlite3.Connection:
    db_path = Path(config.auth_database_path).resolve()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


CONN = _connect()


def init_db() -> None:
    with _lock:
        CONN.executescript(
            """
            CREATE TABLE IF NOT EXISTS members (
              id TEXT PRIMARY KEY,
              name TEXT NOT NULL,
              email TEXT NOT NULL UNIQUE,
              role TEXT NOT NULL DEFAULT 'member',
              program_type TEXT NOT NULL DEFAULT 'individual',
              team_name TEXT,
              age INTEGER,
              height_inches INTEGER,
              weight_lbs INTEGER,
              activity_level TEXT,
              email_verified_at TEXT,
              password_hash TEXT NOT NULL,
              created_at TEXT NOT NULL,
              last_login_at TEXT NOT NULL,
              subscription_plan TEXT NOT NULL,
              subscription_status TEXT NOT NULL,
              subscription_started_at TEXT NOT NULL,
              subscription_renews_at TEXT
            );

            CREATE TABLE IF NOT EXISTS sessions (
              token TEXT PRIMARY KEY,
              member_id TEXT NOT NULL,
              issued_at TEXT NOT NULL,
              expires_at TEXT NOT NULL,
              FOREIGN KEY(member_id) REFERENCES members(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS reset_tokens (
              token TEXT PRIMARY KEY,
              member_id TEXT NOT NULL,
              issued_at TEXT NOT NULL,
              expires_at TEXT NOT NULL,
              FOREIGN KEY(member_id) REFERENCES members(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS verification_tokens (
              token TEXT PRIMARY KEY,
              member_id TEXT NOT NULL,
              issued_at TEXT NOT NULL,
              expires_at TEXT NOT NULL,
              FOREIGN KEY(member_id) REFERENCES members(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS app_settings (
              id TEXT PRIMARY KEY,
              allow_registration INTEGER NOT NULL DEFAULT 1,
              announcement_enabled INTEGER NOT NULL DEFAULT 0,
              announcement_message TEXT,
              maintenance_mode INTEGER NOT NULL DEFAULT 0,
              maintenance_message TEXT,
              updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS teams (
              id TEXT PRIMARY KEY,
              name TEXT NOT NULL,
              organization TEXT,
              created_by TEXT NOT NULL,
              created_at TEXT NOT NULL,
              FOREIGN KEY(created_by) REFERENCES members(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS team_memberships (
              id TEXT PRIMARY KEY,
              team_id TEXT NOT NULL,
              member_id TEXT NOT NULL,
              role TEXT NOT NULL,
              joined_at TEXT NOT NULL,
              UNIQUE(team_id, member_id),
              FOREIGN KEY(team_id) REFERENCES teams(id) ON DELETE CASCADE,
              FOREIGN KEY(member_id) REFERENCES members(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS team_workout_templates (
              id TEXT PRIMARY KEY,
              team_id TEXT NOT NULL,
              title TEXT NOT NULL,
              tier TEXT NOT NULL,
              category TEXT NOT NULL,
              payload_json TEXT NOT NULL,
              created_by TEXT NOT NULL,
              created_at TEXT NOT NULL,
              FOREIGN KEY(team_id) REFERENCES teams(id) ON DELETE CASCADE,
              FOREIGN KEY(created_by) REFERENCES members(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS team_workout_assignments (
              id TEXT PRIMARY KEY,
              team_id TEXT NOT NULL,
              template_id TEXT NOT NULL,
              member_id TEXT NOT NULL,
              assigned_by TEXT NOT NULL,
              assigned_at TEXT NOT NULL,
              status TEXT NOT NULL DEFAULT 'assigned',
              FOREIGN KEY(team_id) REFERENCES teams(id) ON DELETE CASCADE,
              FOREIGN KEY(template_id) REFERENCES team_workout_templates(id) ON DELETE CASCADE,
              FOREIGN KEY(member_id) REFERENCES members(id) ON DELETE CASCADE,
              FOREIGN KEY(assigned_by) REFERENCES members(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS athlete_memory (
              athlete_id TEXT PRIMARY KEY,
              summary TEXT NOT NULL,
              updated_at TEXT NOT NULL
            );
            """
        )
        CONN.commit()
