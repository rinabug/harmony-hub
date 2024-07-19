import sqlite3

def create_profiles_table(conn):
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS profiles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        bio TEXT,
        profile_picture TEXT
    )
    ''')
    conn.commit()

def get_profile_db_connection():
    conn = sqlite3.connect('profiles.db')
    conn.row_factory = sqlite3.Row
    return conn

def update_profile(conn, username, email, bio, profile_picture):
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO profiles (username, email, bio, profile_picture)
    VALUES (?, ?, ?, ?)
    ON CONFLICT(username) DO UPDATE SET
    email=excluded.email,
    bio=excluded.bio,
    profile_picture=excluded.profile_picture
    ''', (username, email, bio, profile_picture))
    conn.commit()

def get_profile(conn, username):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM profiles WHERE username = ?", (username,))
    return cursor.fetchone()
