import sqlite3

def init_db():
    conn = sqlite3.connect("up.db")
    cur = conn.cursor()

    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT,
            full_name TEXT,
            is_admin BOOLEAN
        )
    ''')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            date TEXT,
            action TEXT,
            value REAL
        )
    ''')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS clients_count (
            user_id INTEGER,
            date TEXT,
            clients INTEGER DEFAULT 0,
            PRIMARY KEY (user_id, date)
        )
    ''')

    conn.commit()
    conn.close()


def add_user(user_id: int, username: str, full_name: str, is_admin: bool = False):
    conn = sqlite3.connect("up.db")
    cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE id = ?", (user_id,))
    if not cur.fetchone():
        cur.execute("INSERT INTO users (id, username, full_name, is_admin) VALUES (?, ?, ?, ?)",
                    (user_id, username, full_name, is_admin))
        conn.commit()
    conn.close()

def add_entry(user_id: int, action: str, value: float, date: str):
    conn = sqlite3.connect("up.db")
    cur = conn.cursor()
    cur.execute("INSERT INTO entries (user_id, date, action, value) VALUES (?, ?, ?, ?)",
                (user_id, date, action, value))
    conn.commit()
    conn.close()

def get_all_users():
    conn = sqlite3.connect("up.db")
    cur = conn.cursor()
    cur.execute("SELECT id, username, full_name FROM users")
    users = cur.fetchall()
    conn.close()
    return users

def get_user_name(user_id: int):
    conn = sqlite3.connect("up.db")
    cur = conn.cursor()
    cur.execute("SELECT full_name FROM users WHERE id = ?", (user_id,))
    result = cur.fetchone()
    conn.close()
    return result[0] if result else str(user_id)