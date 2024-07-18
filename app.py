import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, flash
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
from backend.user_auth import create_users_table, is_valid_email, is_valid_password, register_user, login_user

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(64)
DATABASE = 'users.db'

client_id = '6754e8f664b34afea88fa0a353647e33'
client_secret = 'c12ca62b11b24896872bbeab7cd4d814'
redirect_uri = 'http://localhost:8080/callback'
scope = 'playlist-read-private,user-follow-read,user-top-read,user-read-recently-played'

sp_oauth = SpotifyOAuth(
    client_id=client_id,
    client_secret=client_secret,
    redirect_uri=redirect_uri,
    scope=scope,
    cache_path='.spotifycache',
    show_dialog=True
)

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    return conn

@app.route('/')
def start_page():
    return render_template('start-page.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        identifier = request.form.get('identifier')
        password = request.form.get('password')
        conn = get_db_connection()
        user = login_user(conn, identifier, password)
        if user:
            session['username'] = user[1]
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
                return redirect(url_for('connect'))
            else:
                flash('An error occurred during registration. Please try again.', 'danger')
    return render_template('signup.html')

#connecting platforms
@app.route('/connect', methods=['GET', 'POST'])
def connect():
    if request.method == 'POST':
        platform = request.form.get('platform')
        if platform == 'spotify':
            return redirect(url_for('spotify_login'))
        elif platform == 'apple_music':
            ...
            #flash('Apple Music connection is not implemented yet.', 'info')
        elif platform == 'soundcloud':
            ...
            #flash('SoundCloud connection is not implemented yet.', 'info')
        elif platform == 'other':
            ...
            #flash('Other music platform connection is not implemented yet.', 'info')
    return render_template('connect.html')

@app.route('/spotify_login')
def spotify_login():
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)

@app.route('/callback')
def callback():
    code = request.args.get('code')
    token_info = sp_oauth.get_access_token(code)
    session['spotify_token'] = token_info
    flash('Spotify account connected successfully.', 'success')
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('start_page'))

@app.route('/index')
def index():
    return render_template('index.html')

@app.route('/profile')
def profile():
    return render_template('profile.html')

@app.route('/discover')
def discover():
    return render_template('discover.html')

@app.route('/collab')
def collab():
    return render_template('collab.html')

@app.route('/game')
def game():
    return render_template('game.html')

if __name__ == '__main__':
    conn = get_db_connection()
    create_users_table(conn)
    conn.close()
    app.run(debug=True, port=8080)


