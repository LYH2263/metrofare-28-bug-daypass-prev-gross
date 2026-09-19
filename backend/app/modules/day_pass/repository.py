"""day_pass_config 单行配置表的读写;封顶必须为正数。"""
import sqlite3

DDL = """
CREATE TABLE IF NOT EXISTS day_pass_config(
    id INTEGER PRIMARY KEY CHECK (id = 1),
    day TEXT NOT NULL,
    cap REAL NOT NULL CHECK (cap > 0),
    enabled INTEGER NOT NULL DEFAULT 0
);
"""


def get_config(conn: sqlite3.Connection) -> dict | None:
    row = conn.execute("SELECT day, cap, enabled FROM day_pass_config WHERE id = 1").fetchone()
    if row is None:
        return None
    return {"day": row["day"], "cap": float(row["cap"]), "enabled": bool(row["enabled"])}


def save_config(conn: sqlite3.Connection, day: str, cap: float, enabled: bool) -> dict:
    cap = float(cap)
    if cap <= 0:
        raise ValueError("cap must be positive")
    conn.execute(
        "INSERT INTO day_pass_config(id, day, cap, enabled) VALUES (1, ?, ?, ?) "
        "ON CONFLICT(id) DO UPDATE SET day = excluded.day, cap = excluded.cap, enabled = excluded.enabled",
        (day, cap, 1 if enabled else 0),
    )
    conn.commit()
    return get_config(conn)
