import sqlite3
from contextlib import contextmanager

DATABASE = './blog.db'

@contextmanager
def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    with get_db() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()

def get_all_posts():
    with get_db() as conn:
        cursor = conn.execute('''
            SELECT id, title, substr(content, 1, 200) as excerpt, created_at 
            FROM posts ORDER BY created_at DESC
        ''')
        return cursor.fetchall()

def get_post_by_id(post_id):
    with get_db() as conn:
        cursor = conn.execute('SELECT * FROM posts WHERE id = ?', (post_id,))
        return cursor.fetchone()

def create_post(title, content):
    with get_db() as conn:
        cursor = conn.execute(
            'INSERT INTO posts (title, content) VALUES (?, ?)',
            (title, content)
        )
        conn.commit()
        return cursor.lastrowid