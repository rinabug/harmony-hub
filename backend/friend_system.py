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
        FOREIGN KEY (user1_username) REFERENCES users (username),
        FOREIGN KEY (user2_username) REFERENCES users (username)
    )
    ''')
    conn.commit()

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

def accept_friend_request(conn, username, request_id):
    cursor = conn.cursor()
    cursor.execute('''
    UPDATE friend_requests
    SET status = 'accepted'
    WHERE id = ? AND receiver_username = ?
    ''', (request_id, username))
    
    if cursor.rowcount == 0:
        print("Invalid request ID")
        return

    cursor.execute('''
    INSERT INTO friends (user1_username, user2_username)
    SELECT sender_username, receiver_username
    FROM friend_requests
    WHERE id = ?
    ''', (request_id,))
    
    conn.commit()
    print("Friend request accepted.")

def view_friends(conn, username):
    cursor = conn.cursor()
    cursor.execute('''
    SELECT 
        CASE 
            WHEN user1_username = ? THEN user2_username 
            ELSE user1_username 
        END as friend_username
    FROM friends
    WHERE user1_username = ? OR user2_username = ?
    ''', (username, username, username))
    friends = cursor.fetchall()
    
    return [friend[0] for friend in friends]

def friend_management_menu(conn, username):
    create_friend_tables(conn)
    while True:
        print("\nFriend Management Menu:")
        print("1. Send Friend Request")
        print("2. View Friend Requests")
        print("3. Accept Friend Request")
        print("4. View Friends")
        print("5. Back to Main Menu")
        
        choice = input("Enter your choice: ")
        
        if choice == '1':
            receiver = input("Enter the username of the person you want to send a friend request to: ")
            send_friend_request(conn, username, receiver)
        elif choice == '2':
            view_friend_requests(conn, username)
        elif choice == '3':
            request_id = input("Enter the ID of the friend request you want to accept: ")
            accept_friend_request(conn, username, request_id)
        elif choice == '4':
            view_friends(conn, username)
        elif choice == '5':
            break
        else:
            print("Invalid choice. Please try again.")
