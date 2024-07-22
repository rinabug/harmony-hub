from dotenv import load_dotenv
import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_mail import Mail, Message
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
from spotipy.cache_handler import FlaskSessionCacheHandler
from backend.user_auth import create_users_table, is_valid_email, is_valid_password, register_user, login_user
from backend.concert_recommendations import get_concert_recommendations
from backend.music_recommendation import get_music_recommendations
from backend.recent_listens import get_recently_played_tracks
load_dotenv()
app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(64)
DATABASE = 'users.db'


client_id = os.getenv('SPOTIFY_CLIENT_ID')
client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
redirect_uri = 'http://localhost:8080/callback'

scope = 'playlist-read-private,user-follow-read,user-top-read,user-read-recently-played'

cache_handler = FlaskSessionCacheHandler(session)

sp_oauth = SpotifyOAuth(
    client_id=client_id,
    client_secret=client_secret,
    redirect_uri=redirect_uri,
    scope=scope,
    cache_handler=cache_handler,
    show_dialog=True
)
# Flask-Mail configuration using environment variables
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT'))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS') == 'True'
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_USERNAME')

mail = Mail(app)
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn
def setup_database():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            message TEXT,
            is_read BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.close()

@app.before_request
def initialize_database():
    setup_database()
    conn = get_db_connection()
    create_users_table(conn)
    conn.close()


# Add this function to insert notifications into the database
def add_notification(user_id, message):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT COUNT(*) FROM notifications WHERE user_id = ? AND message = ? AND is_read = 0",
        (user_id, message)
    )
    count = cursor.fetchone()[0]

    if count == 0:
        cursor.execute(
            "INSERT INTO notifications (user_id, message) VALUES (?, ?)",
            (user_id, message)
        )
        conn.commit()
    conn.close()

@app.route('/')
def start_page():
    if 'username' in session:
        return redirect(url_for('index'))
    return render_template('start-page.html')

@app.route('/loginSpotify')
def loginSpotify():
    if 'username' not in session:
        flash("Please log in to your account first before connecting Spotify.")
        return redirect(url_for('login'))
    return redirect(sp_oauth.get_authorize_url())

@app.route('/callback')
def callback():
    if 'username' not in session:
        flash("Please log in to your account first.")
        return redirect(url_for('login'))

    token_info = sp_oauth.get_access_token(request.args['code'], as_dict=True)
    session['token_info'] = token_info
    flash('Spotify account connected successfully.', 'success')
    return redirect(url_for('index'))


@app.route('/index')
def index():
    if 'username' not in session:
        flash("Please log in to access this page.")
        return redirect(url_for('login'))

    username = session['username']

    token_info = session.get('token_info', None)
    if not token_info:
        flash("Please connect your Spotify account.")
        return redirect(url_for('loginSpotify'))

    try:
        token_info = ensure_token_validity(token_info)
        sp = Spotify(auth=token_info['access_token'])
        playlists = sp.current_user_playlists(limit=5)
        playlists_info = [(pl['name'], pl['images'][0]['url'], pl['external_urls']['spotify']) for pl in playlists['items']]

        # Fetch featured playlists for top charts section
        top_charts = sp.featured_playlists(limit=5)
        top_charts_info = [(pl['name'], pl['images'][0]['url'], pl['external_urls']['spotify']) for pl in top_charts['playlists']['items']]

        #music recommendations
        music_recommendations = get_music_recommendations(sp)

        # Fetch recently played tracks
        recently_played_tracks = get_recently_played_tracks(sp)

    except Exception as e:
        print(f"Error fetching Spotify playlists: {e}")
        flash("There was an error connecting to Spotify. Please try logging in again.")
        return redirect(url_for('loginSpotify'))

    return render_template('index.html', username=username, playlists_info=playlists_info, top_charts_info=top_charts_info, music_recommendations=music_recommendations, recently_played_tracks=recently_played_tracks)

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('start_page'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        if cursor.fetchone():
            flash('Username already exists. Please choose a different username.', 'danger')
        elif cursor.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone():
            flash('Email already registered. Please use a different email.', 'danger')
        elif not is_valid_email(email):
            flash('Invalid email format.', 'danger')
        elif not is_valid_password(password):
            flash('Password must be at least 8 characters long and contain at least one special character.', 'danger')
        else:
            success = register_user(conn, username, email, password)
            if success:
                session['username'] = username
                flash('Registration successful. Please connect a music platform.', 'success')

                # Send welcome email
                msg = Message("Welcome to MusicBuddyApp!",
                              recipients=[email])
                msg.body = f"""
                Hello {username},

                Welcome to MusicBuddyApp!

                Thank you for registering at MusicBuddyApp. We are thrilled to have you on board. Our service offers personalized music recommendations.

                To get started, you can connect your Spotify account and explore the features we offer.

                If you have any questions or need assistance, feel free to reach out to our support team at support@musicbuddyapp.com.

                Enjoy your musical journey with MusicBuddyApp!

                Best regards,
                The MusicBuddyApp Team
                """
                mail.send(msg)

                return redirect(url_for('connect'))
            else:
                flash('An error occurred during registration. Please try again.', 'danger')
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        identifier = request.form.get('identifier')
        password = request.form.get('password')
        conn = get_db_connection()
        user = login_user(conn, identifier, password)
        if user:
            session['username'] = user[1]
            # Add this line to create a login notification
            add_notification(user[0], f"Welcome back, {user[1]}!")
            flash('Login successful. Please connect a music platform.', 'success')
            return redirect(url_for('connect'))
        else:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username = ? OR email = ?", (identifier, identifier))
            if cursor.fetchone():
                flash('Incorrect password. Please try again.', 'danger')
            else:
                flash('Username or email does not exist. Maybe you should sign up instead.', 'danger')
    return render_template('login.html')

@app.route('/connect', methods=['GET', 'POST'])
def connect():
    if request.method == 'POST':
        platform = request.form.get('platform')
        if platform == 'spotify':
            return redirect(url_for('loginSpotify'))
        elif platform == 'apple_music':
            ...
            # flash('Apple Music connection is not implemented yet.', 'info')
        elif platform == 'soundcloud':
            ...
            #flash('SoundCloud connection is not implemented yet.', 'info')
        elif platform == 'other':
            ...
            #flash('Other music platform connection is not implemented yet.', 'info')
    return render_template('connect.html')

@app.route('/discover', methods=['GET', 'POST'])
def discover():
    if 'username' not in session:
        flash("Please log in to access this page.")
        return redirect(url_for('login'))

    if request.method == 'POST':
        user_location = request.form.get('location')
        favorite_genre = request.form.get('genre')
        radius = int(request.form.get('radius'))

        try:
            top_genres = [favorite_genre]
            chatgpt_recommendation, all_events = get_concert_recommendations(user_location, top_genres, radius)

            return render_template('discover.html',
                                   chatgpt_recommendation=chatgpt_recommendation,
                                   all_events=all_events)
        except Exception as e:
            print(f"Error with recommendations: {e}")
            flash("There was an error fetching recommendations.")
            return redirect(url_for('discover'))

    return render_template('discover.html')

@app.route('/profile')
def profile():
    return render_template('profile.html')

@app.route('/collab')
def collab():
    return render_template('collab.html')

@app.route('/game')
def game():
    return render_template('game.html')

@app.route('/find_friend')
def find_friend():
    return render_template('find_friend.html')

#example data
users = [
    {'username': 'john_doe'},
    {'username': 'jane_smith'},
    {'username': 'alice_jones'},
    {'username': 'bob_brown'}
]

@app.route('/search_friends', methods=['GET'])
def search_friends():
    query = request.args.get('q')
    results = [user for user in users if query.lower() in user['username'].lower()]
    return jsonify(results)

# for the notification
@app.route('/api/notifications')
def get_notifications():
    if 'username' not in session:
        return jsonify([])

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT message, created_at FROM notifications WHERE user_id = (SELECT id FROM users WHERE username = ?) AND is_read = 0",
        (session['username'],)
    )
    notifications = cursor.fetchall()
    conn.close()

    return jsonify([{"message": row["message"], "created_at": row["created_at"]} for row in notifications])


def ensure_token_validity(token_info):
    """
    Ensure the Spotify token is valid, refreshing it if necessary.
    """
    if sp_oauth.is_token_expired(token_info):
        token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
        session['token_info'] = token_info
    return token_info
@app.route('/api/notifications/mark_read', methods=['POST'])
@app.route('/mark_notification_read', methods=['POST'])
def mark_notification_read():
    if 'username' not in session:
        return jsonify({"error": "Unauthorized"}), 401

    notification_id = request.json.get('notification_id')
    if not notification_id:
        return jsonify({"error": "Bad Request"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE notifications SET is_read = 1 WHERE id = ? AND user_id = (SELECT id FROM users WHERE username = ?)",
        (notification_id, session['username'])
    )
    conn.commit()
    conn.close()
    return jsonify({"success": True})


if __name__ == '__main__':
    app.run(debug=True, port=8080)


