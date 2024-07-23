def create_friend_tables(conn):
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS friend_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sender_username TEXT,
    receiver_username TEXT,
    status TEXT,
    FOREIGN KEY (sender_username) REFERENCES users (username),
    FOREIGN KEY (receiver_username) REFERENCES users (username)
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS friends (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user1_username TEXT,
        user2_username TEXT,
        status TEXT,
        FOREIGN KEY (user1_username) REFERENCES users (username),
        FOREIGN KEY (user2_username) REFERENCES users (username)
    )
    ''')
    conn.commit()

def alter_friends_table(conn):
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(friends)")
    columns = [column['name'] for column in cursor.fetchall()]

    if 'status' not in columns:
        cursor.execute("ALTER TABLE friends ADD COLUMN status TEXT")
    
    conn.commit()

def initialize_friend_system(conn):
    create_friend_tables(conn)
    alter_friends_table(conn)

def send_friend_request(conn, sender_username, receiver_username):
    cursor = conn.cursor()
    cursor.execute("SELECT username FROM users WHERE username = ?", (receiver_username,))
    if not cursor.fetchone():
        return False

    cursor.execute("""
    INSERT INTO friend_requests (sender_username, receiver_username, status)
    VALUES (?, ?, ?)
    """, (sender_username, receiver_username, "pending"))
    
    conn.commit()
    return True

def view_friend_requests(conn, username):
    cursor = conn.cursor()
    cursor.execute('''
    SELECT sender_username, id
    FROM friend_requests
    WHERE receiver_username = ? AND status = 'pending'
    ''', (username,))
    requests = cursor.fetchall()
    return [{'sender_username': request[0], 'id': request[1]} for request in requests]

def view_friends(conn, username):
    cursor = conn.cursor()
    cursor.execute('''
    SELECT
        CASE
            WHEN user1_username = ? THEN user2_username
            ELSE user1_username
        END as friend_username
    FROM friends
    WHERE (user1_username = ? OR user2_username = ?) AND status = 'accepted'
    ''', (username, username, username))
    friends = cursor.fetchall()
    return [friend[0] for friend in friends]

def accept_friend_request(conn, username, request_id):
    cursor = conn.cursor()
    cursor.execute('''
    UPDATE friend_requests
    SET status = 'accepted'
    WHERE id = ? AND receiver_username = ?
    ''', (request_id, username))

    if cursor.rowcount == 0:
        return False

    cursor.execute('''
    INSERT INTO friends (user1_username, user2_username, status)
    SELECT sender_username, receiver_username, 'accepted'
    FROM friend_requests
    WHERE id = ?
    ''', (request_id,))
    
    conn.commit()
    return True
