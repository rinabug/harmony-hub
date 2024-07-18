import re
import hashlib
import sqlite3


# from friend_system import friend_management_menu

def create_users_table(conn):
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS movies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        release_year INTEGER,
        director TEXT
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS wishlists (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        movie_id INTEGER,
        FOREIGN KEY (user_id) REFERENCES users (id),
        FOREIGN KEY (movie_id) REFERENCES movies (id)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        movie_id INTEGER,
        rating INTEGER,
        review_text TEXT,
        FOREIGN KEY (user_id) REFERENCES users (id),
        FOREIGN KEY (movie_id) REFERENCES movies (id)
    )
    ''')
    
    conn.commit()


def is_valid_email(email):
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(email_regex, email) is not None


def is_valid_password(password):
    password_regex = r'^(?=.*[!@#$%^&*(),.?":{}|<>])(?=.*[a-zA-Z0-9]).{8,}$'
    return re.match(password_regex, password) is not None


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def register(conn):
    print("Registration: ")
    cursor = conn.cursor()
    while True:
        username = input("Username: ")
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        if cursor.fetchone():
            print("Username taken.")
            continue
        email = input("Enter valid email: ")
        if not is_valid_email(email):
            print("Invalid email.")
            continue
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        if cursor.fetchone():
            print("Email already registered.")
            continue
        password = input("Password: ")
        if not is_valid_password(password):
            print("Invalid Password. It must be at least 8 characters long and contain at least one special character.")
            continue
        hashed_password = hash_password(password)
        # CHANGE TO SQL COMMAND AFTER
        cursor.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
                       (username, email, hashed_password))
        conn.commit()
        print("Registered.")
        return username


def login(conn):
    cursor = conn.cursor()
    while True:
        identifier = input("Username or email: ")
        password = input("Password: ")
        cursor.execute("SELECT * FROM users WHERE username = ? OR email = ?", (identifier, identifier))
        user = cursor.fetchone()
        if user:
            if user[3] == hash_password(password):
                print("Logged in.")
                return user[1]
            else:
                print("Incorrect password.")
                return None
        print("User not found.")
        return None


def spotify_login():
    print("Spotify Login")


def view_users(conn):
    cursor = conn.cursor()
    print("\nCurrent Users:")
    cursor.execute("SELECT username, email FROM users")
    for username, email in cursor.fetchall():
        print(f"Username: {username}")
        print(f"Email: {email}")


def main():
    conn = sqlite3.connect('users.db')
    create_users_table(conn)

    while True:
        choice = input("Enter '1' to register, '2' to login, or 'q' to quit: ")
        if choice == '1':
            username = register(conn)
            spotify_login()
            continue
        elif choice == '2':
            username = login(conn)
            if username:
                spotify_login()
                friend_management_menu(conn, username)
            continue
        elif choice == 'users':
            view_users(conn)
        elif choice.lower() == 'q':
            print("Goodbye!")
            conn.close()
            return
        else:
            print("Invalid choice. Please try again.")


if __name__ == "__main__":
    main()