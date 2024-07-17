import sqlite3

def send_message(conn, sender_username, receiver_username, message_content):
    cursor = conn.cursor()
    cursor.execute("INSERT INTO messages (sender_username, receiver_username, message_content, timestamp) VALUES (?, ?, ?, datetime('now'))", 
                    (sender_username, receiver_username, message_content))
    conn.commit()

def get_messages(conn, receiver_username):
    cursor = conn.cursor()
    cursor.execute("SELECT sender_username, message_content, timestamp FROM messages WHERE receiver_username = ? ORDER BY timestamp DESC", 
                    (receiver_username,))
    messages = [{'sender_username': row[0], 'message_content': row[1], 'timestamp': row[2]} for row in cursor.fetchall()]
    return messages