import re
import hashlib
import sqlite3
from flask import session

def get_db_connection():
    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row
    return conn

def create_tables():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.executescript('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        reset_token TEXT
    );
                         

    CREATE TABLE IF NOT EXISTS profiles (
        user_id INTEGER PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        email TEXT NOT NULL,
        bio TEXT,
        profile_picture TEXT,
        favorite_music TEXT,
        recently_played_tracks TEXT,
        favorite_movies TEXT,
        recently_watched TEXT,
        ratings TEXT,
        FOREIGN KEY (user_id) REFERENCES users(id)
    );

    CREATE TABLE IF NOT EXISTS friend_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender_id INTEGER,
        receiver_id INTEGER,
        status TEXT CHECK(status IN ('pending', 'accepted', 'rejected')),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (sender_id) REFERENCES users (id),
        FOREIGN KEY (receiver_id) REFERENCES users (id)
    );

    CREATE TABLE IF NOT EXISTS friends (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        friend_id INTEGER,
        status TEXT CHECK(status IN ('pending', 'accepted', 'rejected')),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id),
        FOREIGN KEY (friend_id) REFERENCES users (id)
    );
                         
    CREATE TABLE IF NOT EXISTS movie_ratings (
        user_id INTEGER NOT NULL,
        movie_id INTEGER NOT NULL,
        rating INTEGER NOT NULL,
        PRIMARY KEY (user_id, movie_id),
        FOREIGN KEY (user_id) REFERENCES users(id)
    );
                         
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender_id INTEGER,
        receiver_id INTEGER,
        content TEXT NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        is_read BOOLEAN DEFAULT 0,
        FOREIGN KEY (sender_id) REFERENCES users (id),
        FOREIGN KEY (receiver_id) REFERENCES users (id)
    );
    ''')
    conn.commit()
    conn.close()

def alter_profiles_table():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(profiles)")
    columns = [column['name'] for column in cursor.fetchall()]

    if 'favorite_music' not in columns:
        cursor.execute("ALTER TABLE profiles ADD COLUMN favorite_music TEXT")
    if 'recently_played_tracks' not in columns:
        cursor.execute("ALTER TABLE profiles ADD COLUMN recently_played_tracks TEXT")
    if 'favorite_movies' not in columns:
        cursor.execute("ALTER TABLE profiles ADD COLUMN favorite_movies TEXT")
    if 'recently_watched' not in columns:
        cursor.execute("ALTER TABLE profiles ADD COLUMN recently_watched TEXT")
    if 'ratings' not in columns:
        cursor.execute("ALTER TABLE profiles ADD COLUMN ratings TEXT")
    
    conn.commit()
    conn.close()


def is_valid_email(email):
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(email_regex, email) is not None

def is_valid_password(password):
    password_regex = r'^(?=.*[!@#$%^&*(),.?":{}|<>])(?=.*[a-zA-Z0-9]).{8,}$'
    return re.match(password_regex, password) is not None

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(conn, username, email, password):
    cursor = conn.cursor()
    try:
        hashed_password = hash_password(password)
        cursor.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)", (username, email, hashed_password))
        conn.commit()
        user_id = cursor.lastrowid
        cursor.execute("INSERT INTO profiles (user_id, username, email) VALUES (?, ?, ?)", (user_id, username, email))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False

def login_user(conn, identifier, password):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ? OR email = ?", (identifier, identifier))
    user = cursor.fetchone()
    if user and user['password'] == hash_password(password):
        return user
    return None

def update_profile(conn, user_id, email, bio, profile_picture):
    cursor = conn.cursor()
    cursor.execute('''
    UPDATE profiles
    SET email = ?, bio = ?, profile_picture = ?
    WHERE user_id = ?
    ''', (email, bio, profile_picture, user_id))
    conn.commit()

def get_profile(conn, username):
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM profiles WHERE username = ?', (username,))
    row = cursor.fetchone()
    
    return dict(row) if row else None


def set_reset_token(conn, email, token):
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET reset_token = ? WHERE email = ?", (token, email))
    conn.commit()

def get_user_by_reset_token(conn, token):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE reset_token = ?", (token,))
    return cursor.fetchone()

def reset_password(conn, token, new_password):
    cursor = conn.cursor()
    hashed_password = hash_password(new_password)
    cursor.execute("UPDATE users SET password = ?, reset_token = NULL WHERE reset_token = ?", (hashed_password, token))
    conn.commit()

#friend stuff

def send_friend_request(conn, sender_id, receiver_id):
    cursor = conn.cursor()
    try:
        cursor.execute('''
        INSERT INTO friend_requests (sender_id, receiver_id, status)
        VALUES (?, ?, 'pending')
        ''', (sender_id, receiver_id))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    
def accept_friend_request(conn, request_id, user_id, friend_id):
    cursor = conn.cursor()
    try:
        # Update the friend request status
        cursor.execute('''
        UPDATE friend_requests
        SET status = 'accepted'
        WHERE id = ? AND receiver_id = ?
        ''', (request_id, user_id))
        
        # Add entries to the friends table
        cursor.execute('''
        INSERT INTO friends (user_id, friend_id, status)
        VALUES (?, ?, 'accepted'), (?, ?, 'accepted')
        ''', (user_id, friend_id, friend_id, user_id))
        
        conn.commit()
        return True
    except sqlite3.Error:
        conn.rollback()
        return False

def reject_friend_request(conn, request_id, user_id):
    cursor = conn.cursor()
    try:
        cursor.execute('''
        UPDATE friend_requests
        SET status = 'rejected'
        WHERE id = ? AND receiver_id = ?
        ''', (request_id, user_id))
        conn.commit()
        return True
    except sqlite3.Error:
        return False

def get_pending_friend_requests(conn, user_id):
    cursor = conn.cursor()
    cursor.execute('''
    SELECT fr.id, u.username, u.id as sender_id
    FROM friend_requests fr
    JOIN users u ON fr.sender_id = u.id
    WHERE fr.receiver_id = ? AND fr.status = 'pending'
    ''', (user_id,))
    return cursor.fetchall()

def get_friends(conn, user_id):
    cursor = conn.cursor()
    cursor.execute('''
    SELECT u.id, u.username
    FROM friends f
    JOIN users u ON f.friend_id = u.id
    WHERE f.user_id = ? AND f.status = 'accepted'
    ''', (user_id,))
    return cursor.fetchall()

def get_user_id_by_username(conn, username):
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
    result = cursor.fetchone()
    return result[0] if result else None

def reject_friend_request(conn, username, request_id):
    cursor = conn.cursor()
    cursor.execute('''
        DELETE FROM friend_requests 
        WHERE id = (SELECT id FROM friend_requests WHERE id = ? AND receiver_id = (SELECT id FROM users WHERE username = ?))
    ''', (request_id, username))
    conn.commit()

#MESSAGING:
def send_message(conn, sender_id, receiver_id, content):
    cursor = conn.cursor()
    try:
        cursor.execute('''
        INSERT INTO messages (sender_id, receiver_id, content)
        VALUES (?, ?, ?)
        ''', (sender_id, receiver_id, content))
        conn.commit()
        return cursor.lastrowid
    except sqlite3.Error:
        return None

def get_messages(conn, user_id, friend_id):
    cursor = conn.cursor()
    cursor.execute('''
    SELECT m.id, m.sender_id, m.receiver_id, m.content, m.timestamp, m.is_read
    FROM messages m
    WHERE (m.sender_id = ? AND m.receiver_id = ?) OR (m.sender_id = ? AND m.receiver_id = ?)
    ORDER BY m.timestamp ASC
    ''', (user_id, friend_id, friend_id, user_id))
    return cursor.fetchall()

def mark_messages_as_read(conn, user_id, friend_id):
    cursor = conn.cursor()
    try:
        cursor.execute('''
        UPDATE messages
        SET is_read = 1
        WHERE receiver_id = ? AND sender_id = ? AND is_read = 0
        ''', (user_id, friend_id))
        conn.commit()
        return True
    except sqlite3.Error:
        return False