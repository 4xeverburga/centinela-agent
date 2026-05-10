import aiosqlite


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS projects (
    project_id TEXT PRIMARY KEY,
    chat_id TEXT NOT NULL,
    local_name TEXT NOT NULL,
    admin_user_id TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'ACTIVE',
    started_at TEXT NOT NULL,
    floor_plan_file_id TEXT NOT NULL DEFAULT '',
    finished_at TEXT NOT NULL DEFAULT '',
    closure_reason TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS users (
    telegram_user_id TEXT PRIMARY KEY,
    display_name TEXT NOT NULL,
    role TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS inspections_queue (
    file_id TEXT NOT NULL,
    system_version TEXT NOT NULL,
    project_id TEXT NOT NULL,
    chat_id TEXT NOT NULL,
    message_id INTEGER NOT NULL,
    cluster_id TEXT NOT NULL DEFAULT '',
    is_representative INTEGER NOT NULL DEFAULT 1,
    status TEXT NOT NULL DEFAULT 'PENDING',
    attempts INTEGER NOT NULL DEFAULT 0,
    received_at TEXT NOT NULL,
    last_error TEXT NOT NULL DEFAULT '',
    worker_id TEXT NOT NULL DEFAULT '',
    processed_at TEXT NOT NULL DEFAULT '',
    PRIMARY KEY (file_id, system_version),
    FOREIGN KEY (project_id) REFERENCES projects(project_id)
);

CREATE TABLE IF NOT EXISTS chat_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT NOT NULL,
    chat_id TEXT NOT NULL,
    message_id INTEGER NOT NULL,
    telegram_user_id TEXT NOT NULL,
    display_name TEXT NOT NULL,
    role TEXT NOT NULL,
    text TEXT NOT NULL,
    file_id TEXT NOT NULL DEFAULT '',
    cluster_id TEXT NOT NULL DEFAULT '',
    timestamp TEXT NOT NULL,
    is_included_in_history INTEGER NOT NULL DEFAULT 1,
    rejected_reason TEXT NOT NULL DEFAULT '',
    FOREIGN KEY (project_id) REFERENCES projects(project_id),
    UNIQUE (chat_id, message_id)
);

CREATE TABLE IF NOT EXISTS inspections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT NOT NULL,
    image_file_id TEXT NOT NULL,
    system_version TEXT NOT NULL DEFAULT '',
    item_id TEXT NOT NULL,
    category TEXT NOT NULL,
    inspection_status TEXT NOT NULL,
    location_on_map TEXT NOT NULL DEFAULT '',
    ocr_data TEXT NOT NULL DEFAULT '',
    tech_observation TEXT NOT NULL DEFAULT '',
    ai_system_observation TEXT NOT NULL DEFAULT '',
    is_suspicious INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    FOREIGN KEY (project_id) REFERENCES projects(project_id)
);

CREATE TABLE IF NOT EXISTS human_reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT NOT NULL,
    trigger TEXT NOT NULL,
    question TEXT NOT NULL,
    asked_at TEXT NOT NULL,
    image_file_id TEXT NOT NULL DEFAULT '',
    answer TEXT NOT NULL DEFAULT '',
    reviewer_user_id TEXT NOT NULL DEFAULT '',
    answered_at TEXT NOT NULL DEFAULT '',
    FOREIGN KEY (project_id) REFERENCES projects(project_id)
);

CREATE TABLE IF NOT EXISTS admin_whitelist (
    telegram_user_id TEXT PRIMARY KEY,
    added_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS assistants (
    telegram_user_id TEXT PRIMARY KEY,
    admin_user_id TEXT NOT NULL,
    added_at TEXT NOT NULL
);
"""


async def get_connection(db_path: str) -> aiosqlite.Connection:
    conn = await aiosqlite.connect(db_path)
    conn.row_factory = aiosqlite.Row
    await conn.execute("PRAGMA journal_mode=WAL")
    await conn.execute("PRAGMA foreign_keys=ON")
    return conn


async def initialize_db(db_path: str) -> aiosqlite.Connection:
    conn = await get_connection(db_path)
    await conn.executescript(SCHEMA_SQL)
    await conn.commit()
    return conn
