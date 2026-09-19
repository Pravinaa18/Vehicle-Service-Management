import sqlite3
import os
from config import Config

def get_db():
    """Connect to SQLite database and set row_factory for name-based access."""
    db = sqlite3.connect(Config.DATABASE)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON;")
    return db

def query_db(query, args=(), one=False):
    """Execute a SELECT query and return rows as dictionaries."""
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute(query, args)
        rv = cur.fetchall()
        cur.close()
        return (dict(rv[0]) if rv else None) if one else [dict(r) for r in rv]
    finally:
        conn.close()

def execute_db(query, args=(), commit=True):
    """Execute an INSERT/UPDATE/DELETE query and return lastrowid or affected rows."""
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute(query, args)
        if commit:
            conn.commit()
        last_id = cur.lastrowid
        row_count = cur.rowcount
        cur.close()
        return last_id if last_id else row_count
    finally:
        conn.close()

def init_db():
    """Initialize database tables using schema.sql."""
    schema_path = os.path.join(os.path.dirname(__file__), 'database', 'schema.sql')
    if not os.path.exists(schema_path):
        raise FileNotFoundError(f"Schema file not found at {schema_path}")
    
    conn = get_db()
    try:
        with open(schema_path, 'r', encoding='utf-8') as f:
            conn.executescript(f.read())
        conn.commit()
    finally:
        conn.close()

def check_and_seed():
    """Check if database has users, if empty run seed script."""
    init_db()
    user_count = query_db("SELECT COUNT(*) as count FROM users", one=True)
    if not user_count or user_count['count'] == 0:
        from database.seed import seed_data
        seed_data()
