import sqlite3

def create_badges_table(conn):
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS badges (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        badge_name TEXT,
        earned_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (username) REFERENCES users (username)
    )
    ''')
    conn.commit()

def award_badge(conn, username, badge_name):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM badges WHERE username = ? AND badge_name = ?", (username, badge_name))
    if cursor.fetchone() is None:
        cursor.execute("INSERT INTO badges (username, badge_name) VALUES (?, ?)", (username, badge_name))
        conn.commit()
        return True
    return False

def get_user_badges(conn, username):
    cursor = conn.cursor()
    cursor.execute("SELECT badge_name, earned_date FROM badges WHERE username = ?", (username,))
    return cursor.fetchall()

def check_and_award_badges(conn, username):
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM friend_requests WHERE sender_username = ?", (username,))
    if cursor.fetchone()[0] > 0:
        award_badge(conn, username, "Stop Being Shy")
    
    cursor.execute("SELECT score FROM leaderboard WHERE username = ?", (username,))
    result = cursor.fetchone()
    if result and result[0] >= 10:
        award_badge(conn, username, "Trivia?")