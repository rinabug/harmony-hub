import requests
from dotenv import load_dotenv
import os
import sqlite3
import uuid
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, json
from flask_mail import Mail, Message
from werkzeug.utils import secure_filename
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
from spotipy.cache_handler import FlaskSessionCacheHandler
from backend.user_auth import (
    create_tables, get_db_connection, register_user, login_user, update_profile, get_profile, 
    is_valid_email, is_valid_password, set_reset_token, get_user_by_reset_token, reset_password, 
    alter_profiles_table, get_user_id_by_username, get_pending_friend_requests, get_friends, 
    send_friend_request, accept_friend_request, reject_friend_request, send_message, 
    get_messages, mark_messages_as_read
)
from backend.concert_recommendations import get_concert_recommendations
from backend.music_recommendation import get_music_recommendations
from backend.recent_listens import get_recently_played_tracks
from backend.tmdb_recommendations import get_movie_recommendations_from_tmdb
from backend.spotify_utils import extract_top_genres, genre_mapping

from flask_socketio import SocketIO, emit, join_room, leave_room
from datetime import datetime

from backend.trivia import create_leaderboard_table, update_score, get_leaderboard, get_friends_leaderboard, generate_trivia_question


app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(64)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max upload size
socketio = SocketIO(app, cors_allowed_origins="*") #messaging

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

load_dotenv()
TMDB_API_KEY='9543dc934149c1e3c3e522690966c634'

client_id = '908db28b7d8e4d03888632068918bff1'
client_secret = '92919a8126964ba5b4da358d97c729ef'
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

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# Flask-Mail configuration using environment variables
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT'))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS') == 'True'
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_USERNAME')

mail = Mail(app)
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
    create_tables()
    alter_profiles_table()
    create_leaderboard_table(conn)
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

    sp = Spotify(auth=token_info['access_token'])
    favorite_music, recently_played_tracks = fetch_spotify_data(sp)

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE profiles
        SET favorite_music = ?, recently_played_tracks = ?
        WHERE username = ?
    ''', (json.dumps(favorite_music), json.dumps(recently_played_tracks), session['username']))
    conn.commit()
    conn.close()

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
        top_charts = sp.featured_playlists(limit=10)
        top_charts_info = [(pl['name'], pl['images'][0]['url'], pl['external_urls']['spotify']) for pl in top_charts['playlists']['items']]

        #music recommendations
        music_recommendations = get_music_recommendations(sp)

        # Fetch recently played tracks
        recently_played_tracks = get_recently_played_tracks(sp)

        #movie rec based on listening history
        top_genres = extract_top_genres(sp)
        movie_genres = [genre_mapping.get(genre, 'Drama') for genre in top_genres]
        if movie_genres:
            movie_recommendations = get_movie_recommendations_from_tmdb(movie_genres[0], "PG-13", "2021-present")
        else:
            movie_recommendations = []

    except Exception as e:
        print(f"Error fetching Spotify playlists: {e}")
        flash("There was an error connecting to Spotify. Please try logging in again.")
        return redirect(url_for('loginSpotify'))

    return render_template('index.html', 
                           username=username, 
                           playlists_info=playlists_info, 
                           top_charts_info=top_charts_info, 
                           music_recommendations=music_recommendations, 
                           recently_played_tracks=recently_played_tracks,
                           movie_recommendations=movie_recommendations)
    
def generate_movie_recommendations(favorite_movies, recently_watched):
    # For simplicity, we use genres from favorite and recently watched movies
    genres = set()
    for movie in favorite_movies + recently_watched:
        if 'genre_ids' in movie:
            genres.update(movie['genre_ids'])

    # Use the first genre as an example, you might want to handle this better in a real application
    if genres:
        genre = list(genres)[0]
        return get_movie_recommendations_from_tmdb(genre, "PG-13", "2021-present")
    return []

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
            session['username'] = user['username']
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

# New routes for password reset functionality
@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()
        if user:
            reset_token = str(uuid.uuid4())
            set_reset_token(conn, email, reset_token)
            send_reset_email(email, reset_token)
            flash('A password reset link has been sent to your email.', 'success')
        else:
            flash('Email not found.', 'danger')
    return render_template('forgot_password.html')

def send_reset_email(email, token):
    reset_url = url_for('reset_password_route', token=token, _external=True)
    # Replace with your email sending code
    print(f"Send this link to {email}: {reset_url}")

@app.route('/reset_password/<token>', methods=['GET', 'POST'], endpoint='reset_password_route')
def reset_password_route(token):
    conn = get_db_connection()
    user = get_user_by_reset_token(conn, token)
    if not user:
        flash('Invalid or expired token.', 'danger')
        return redirect(url_for('forgot_password'))

    if request.method == 'POST':
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        if new_password != confirm_password:
            flash('Passwords do not match.', 'danger')
        elif not is_valid_password(new_password):
            flash('Password must be at least 8 characters long and contain at least one special character.', 'danger')
        else:
            reset_password(conn, token, new_password)
            flash('Your password has been reset successfully.', 'success')
            return redirect(url_for('login'))
    return render_template('reset_password.html', token=token)


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

@app.route('/get_movie_recommendations', methods=['POST'])
def get_movie_recommendations():
    if 'username' not in session:
        flash("Please log in to access this page.")
        return redirect(url_for('login'))

    genre = request.form.get('genre')
    age_rating = request.form.get('age_rating')
    year_range = request.form.get('year_range')

    try:
        recommendations = get_movie_recommendations_from_tmdb(genre, age_rating, year_range)
        return render_template('discover.html', recommendations=recommendations)
    except Exception as e:
        print(f"Error with recommendations: {e}")
        flash("There was an error fetching recommendations.")
        return redirect(url_for('discover'))

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'username' not in session:
        flash("Please log in to access this page.")
        return redirect(url_for('login'))

    profile_conn = get_db_connection()
    username = session['username']
    user_profile = get_profile(profile_conn, username)

    favorite_music = json.loads(user_profile['favorite_music']) if user_profile['favorite_music'] else []
    recently_played_tracks = json.loads(user_profile['recently_played_tracks']) if user_profile['recently_played_tracks'] else []
    favorite_movies = json.loads(user_profile['favorite_movies']) if user_profile['favorite_movies'] else []
    recently_watched = json.loads(user_profile['recently_watched']) if user_profile['recently_watched'] else []
    ratings = json.loads(user_profile['ratings']) if user_profile['ratings'] else []
    
    if request.method == 'POST':
        new_username = request.form['username']
        email_address = request.form['email_address']
        bio = request.form['bio']
        current_password = request.form['current_password']
        profile_picture = user_profile['profile_picture']

        user_conn = get_db_connection()
        user = login_user(user_conn, username, current_password)
        
        errors = {}

        if user:
            cursor = user_conn.cursor()

            if new_username != username:
                cursor.execute("SELECT * FROM users WHERE username = ?", (new_username,))
                if cursor.fetchone():
                    errors['username'] = 'Username already exists.'
            
            if email_address != user_profile['email']:
                cursor.execute("SELECT * FROM users WHERE email = ?", (email_address,))
                if cursor.fetchone():
                    errors['email'] = 'Email already exists.'

            if errors:
                return jsonify({'errors': errors}), 400

            if 'profile_picture' in request.files:
                file = request.files['profile_picture']
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    unique_filename = str(uuid.uuid4()) + "_" + filename
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                    file.save(file_path)
                    profile_picture = unique_filename

            cursor.execute('''
            UPDATE users
            SET username = ?, email = ?
            WHERE id = ?
            ''', (new_username, email_address, user['id']))

            cursor.execute('''
            UPDATE profiles
            SET username = ?, email = ?, bio = ?, profile_picture = ?
            WHERE user_id = ?
            ''', (new_username, email_address, bio, profile_picture, user['id']))

            user_conn.commit()
            user_conn.close()

            session['username'] = new_username
            flash('Profile updated successfully', 'success')
        else:
            user_conn.close()
            flash('Incorrect password. Please try again.', 'danger')

        return redirect(url_for('profile'))
    
    token_info = session.get('token_info', None)
    if not token_info:
        flash("Please connect your Spotify account.")
        return redirect(url_for('loginSpotify'))

    try:
        token_info = ensure_token_validity(token_info)
        sp = Spotify(auth=token_info['access_token'])
        
        top_tracks = sp.current_user_top_tracks(limit=10)
        favorite_music = [
            {
                'name': track['name'],
                'artist': track['artists'][0]['name'],
                'album_image': track['album']['images'][0]['url'],
                'spotify_url': track['external_urls']['spotify']
            }
            for track in top_tracks['items']
        ]

        # Fetch recently played tracks
        recently_played_tracks = get_recently_played_tracks(sp)

    except Exception as e:
        print(f"Error fetching Spotify data: {e}")
        flash("There was an error connecting to Spotify. Please try logging in again.")
        return redirect(url_for('loginSpotify'))

    cursor = profile_conn.cursor()
    cursor.execute('''
        UPDATE profiles
        SET favorite_music = ?, recently_played_tracks = ?
        WHERE username = ?
    ''', (json.dumps(favorite_music), json.dumps(recently_played_tracks), session['username']))
    profile_conn.commit()
    profile_conn.close()

    return render_template('profile.html', username=username, favorite_music=favorite_music, user_profile=user_profile, recently_played_tracks=recently_played_tracks, favorite_movies=favorite_movies, recently_watched=recently_watched, ratings=ratings)


@app.route('/user/<username>')
def view_user_profile(username):
    if 'username' not in session:
        flash("Please log in to access this page.")
        return redirect(url_for('login'))

    conn = get_db_connection()
    user_profile = get_profile(conn, username)
    conn.close()

    if user_profile:
        favorite_music = json.loads(user_profile['favorite_music']) if user_profile['favorite_music'] else []
        recently_played_tracks = json.loads(user_profile['recently_played_tracks']) if user_profile['recently_played_tracks'] else []
        favorite_movies = json.loads(user_profile['favorite_movies']) if user_profile['favorite_movies'] else []
        recently_watched = json.loads(user_profile['recently_watched']) if user_profile['recently_watched'] else []
        ratings = json.loads(user_profile['ratings']) if user_profile['ratings'] else []

        badges = []  # Placeholder for badges

        return render_template('user_profile.html',
                               user_profile=user_profile,
                               favorite_music=favorite_music,
                               recently_played_tracks=recently_played_tracks,
                               favorite_movies=favorite_movies,
                               recently_watched=recently_watched,
                               ratings=ratings,
                               badges=badges)
    else:
        flash('User not found.', 'danger')
        return redirect(url_for('find_friend'))

@app.route('/find_friend')
def find_friend():
    if 'username' not in session:
        flash("Please log in to access this page.")
        return redirect(url_for('login'))

    username = session['username']
    conn = get_db_connection()
    user_id = get_user_id_by_username(conn, username)
    friends = get_friends(conn, user_id)
    friend_requests = get_pending_friend_requests(conn, user_id)
    conn.close()

    friends_list = [{'username': friend['username']} for friend in friends]
    friend_requests_list = [{'id': request['id'], 'username': request['username'], 'sender_id': request['sender_id']} for request in friend_requests]

    return render_template('find_friend.html', username=username, friends=friends_list, friend_requests=friend_requests_list)


@app.route('/view_friend_requests')
def view_friend_requests_route():
    if 'username' not in session:
        return jsonify({'status': 'error', 'message': 'Please log in.'}), 401
    
    conn = get_db_connection()
    user_id = get_user_id_by_username(conn, session['username'])
    friend_requests = get_pending_friend_requests(conn, user_id)
    conn.close()
    
    friend_requests_dicts = [{'id': r['id'], 'username': r['username'], 'sender_id': r['sender_id']} for r in friend_requests]
    
    return jsonify({'status': 'success', 'requests': friend_requests_dicts})

@app.route('/search_friends', methods=['GET'])
def search_friends():
    query = request.args.get('q')
    if not query:
        return jsonify([])

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT username FROM users WHERE username LIKE ?", ('%' + query + '%',))
    users = cursor.fetchall()
    conn.close()

    results = [{'username': user[0]} for user in users if user[0] != session.get('username')]
    return jsonify(results)

@app.route('/accept_friend_request', methods=['POST'])
def accept_friend_request_route():
    if 'username' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    data = request.json
    request_id = data.get('request_id')
    
    conn = get_db_connection()
    user_id = get_user_id_by_username(conn, session['username'])
    
    # Fetch the sender_id from the friend_requests table
    cursor = conn.cursor()
    cursor.execute('SELECT sender_id FROM friend_requests WHERE id = ? AND receiver_id = ?', (request_id, user_id))
    result = cursor.fetchone()
    
    if not result:
        conn.close()
        return jsonify({'error': 'Friend request not found'}), 404
    
    sender_id = result[0]
    
    if accept_friend_request(conn, request_id, user_id, sender_id):
        conn.close()
        return jsonify({'message': 'Friend request accepted'}), 200
    else:
        conn.close()
        return jsonify({'error': 'Failed to accept friend request'}), 400
    
@app.route('/reject_friend_request', methods=['POST'])
def reject_friend_request_route():
    if 'username' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    data = request.json
    request_id = data.get('request_id')
    
    conn = get_db_connection()
    user_id = get_user_id_by_username(conn, session['username'])
    
    if reject_friend_request(conn, request_id, user_id):
        conn.close()
        return jsonify({'message': 'Friend request rejected'}), 200
    else:
        conn.close()
        return jsonify({'error': 'Failed to reject friend request'}), 400

@app.route('/send_request', methods=['POST'])
def send_request():
    if 'username' not in session:
        return jsonify({'error': 'Not authenticated'}), 401

    data = request.get_json()
    sender_username = session['username']
    receiver_username = data.get('username')

    conn = get_db_connection()
    sender_id = get_user_id_by_username(conn, sender_username)
    receiver_id = get_user_id_by_username(conn, receiver_username)
    success = send_friend_request(conn, sender_id, receiver_id)
    conn.close()

    if success:
        return jsonify({'success': True})
    else:
        return jsonify({'error': 'Failed to send friend request'}), 400
    
#messaging
@app.route('/get_messages/<int:friend_id>', methods=['GET'])
def get_messages_route(friend_id):
    if 'username' not in session:
        return jsonify({'error': 'Not logged in'}), 401

    conn = get_db_connection()
    user_id = get_user_id_by_username(conn, session['username'])
    messages = get_messages(conn, user_id, friend_id)
    conn.close()

    return jsonify({'messages': messages}), 200


@socketio.on('send_message')
def handle_message(data):
    sender = data['sender']
    receiver = data['receiver']
    content = data['message']
    room = data['room']

    conn = get_db_connection()
    sender_id = get_user_id_by_username(conn, sender)
    receiver_id = get_user_id_by_username(conn, receiver)
    message_id = send_message(conn, sender_id, receiver_id, content)
    conn.close()

    if message_id:
        emit('new_message', {
            'id': message_id,
            'sender_id': sender_id,
            'receiver_id': receiver_id,
            'sender_username': sender,
            'content': content,
            'timestamp': datetime.datetime.now().isoformat()
        }, room=room)
    else:
        emit('error', {'msg': 'Failed to send message'}, room=request.sid)


@socketio.on('join')
def on_join(data):
    username = data['username']
    room = data['room']
    join_room(room)
    emit('user_joined', {'username': username}, room=room)

@socketio.on('leave')
def on_leave(data):
    username = data['username']
    room = data['room']
    leave_room(room)
    emit('user_left', {'username': username}, room=room)


@app.route('/user/<username>')
def user_profile(username):
    if 'username' not in session:
        flash("Please log in to access this page.")
        return redirect(url_for('login'))
    
    current_user = session['username']
    conn = get_db_connection()
    user_profile = get_profile(conn, username)
    
    if not user_profile:
        flash("User not found.")
        return redirect(url_for('find_friend'))
    
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE username = ?", (user_profile['username'],))
    user_id = cursor.fetchone()['id']
    ratings = get_movie_ratings(user_id)

    favorite_music = json.loads(user_profile['favorite_music']) if user_profile['favorite_music'] else []
    recently_played_tracks = json.loads(user_profile['recently_played_tracks']) if user_profile['recently_played_tracks'] else []
    favorite_movies = json.loads(user_profile['favorite_movies']) if user_profile['favorite_movies'] else []
    recently_watched = json.loads(user_profile['recently_watched']) if user_profile['recently_watched'] else []

    # Placeholder for badges 
    badges = [] 

    return render_template('user_profile.html', 
                           user_profile=user_profile, 
                           favorite_music=favorite_music,
                           recently_played_tracks=recently_played_tracks, 
                           favorite_movies=favorite_movies,
                           recently_watched=recently_watched,
                           current_user=current_user,
                           ratings=ratings,
                           badges=badges)

def search_movie(query):
    url = f"https://api.themoviedb.org/3/search/movie"
    params = {
        'api_key': TMDB_API_KEY,
        'query': query
    }
    response = requests.get(url, params=params)
    return response.json()

@app.route('/search_movie', methods=['POST'])
def search_movie_route():
    query = request.json.get('query')
    url = f"https://api.themoviedb.org/3/search/movie"
    params = {
        'api_key': TMDB_API_KEY,
        'query': query
    }
    response = requests.get(url, params=params)
    search_results = response.json()
    return jsonify(search_results)

@app.route('/add_favorite', methods=['POST'])
def add_favorite():
    if 'username' not in session:
        flash("Please log in to access this page.")
        return redirect(url_for('login'))

    username = session['username']
    movie_data = request.json
    movie_id = movie_data['id']
    movie_title = movie_data['title']
    movie_poster = f"https://image.tmdb.org/t/p/w500{movie_data['poster_path']}"
    movie_overview = movie_data['overview']
    movie_trailer = movie_data.get('trailer')

    profile_conn = get_db_connection()
    user_profile = get_profile(profile_conn, username)

    favorite_movies = json.loads(user_profile['favorite_movies']) if user_profile['favorite_movies'] else []
    new_favorite = {
        'id': movie_id,
        'title': movie_title,
        'poster': movie_poster,
        'overview': movie_overview,
        'trailer': movie_trailer
    }

    if new_favorite not in favorite_movies:
        favorite_movies.append(new_favorite)
        cursor = profile_conn.cursor()
        cursor.execute('''
            UPDATE profiles
            SET favorite_movies = ?
            WHERE username = ?
        ''', (json.dumps(favorite_movies), username))
        profile_conn.commit()

    profile_conn.close()
    return jsonify({"status": "success"})

@app.route('/add_recently_watched', methods=['POST'])
def add_recently_watched():
    if 'username' not in session:
        flash("Please log in to access this page.")
        return redirect(url_for('login'))

    username = session['username']
    movie_data = request.json
    movie_id = movie_data['id']
    movie_title = movie_data['title']
    movie_poster = f"https://image.tmdb.org/t/p/w500{movie_data['poster_path']}"
    movie_overview = movie_data['overview']
    movie_trailer = movie_data.get('trailer')

    profile_conn = get_db_connection()
    user_profile = get_profile(profile_conn, username)

    recently_watched = json.loads(user_profile['recently_watched']) if user_profile['recently_watched'] else []
    new_watched = {
        'id': movie_id,
        'title': movie_title,
        'poster': movie_poster,
        'overview': movie_overview,
        'trailer': movie_trailer
    }

    if new_watched not in recently_watched:
        recently_watched.append(new_watched)
        cursor = profile_conn.cursor()
        cursor.execute('''
            UPDATE profiles
            SET recently_watched = ?
            WHERE username = ?
        ''', (json.dumps(recently_watched), username))
        profile_conn.commit()

    profile_conn.close()
    return jsonify({"status": "success"})

@app.route('/update_rating', methods=['POST'])
def update_rating():
    if 'username' not in session:
        return jsonify({'status': 'error', 'message': 'Please log in.'}), 401

    data = request.json
    movie_id = data['movie_id']
    rating = data['rating']
    username = session['username']

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
    user_id = cursor.fetchone()['id']

    cursor.execute('''
    INSERT INTO movie_ratings (user_id, movie_id, rating)
    VALUES (?, ?, ?)
    ON CONFLICT(user_id, movie_id) DO UPDATE SET rating = excluded.rating
    ''', (user_id, movie_id, rating))

    conn.commit()
    conn.close()

    return jsonify({'status': 'success'})

def get_movie_ratings(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT movie_id, rating FROM movie_ratings WHERE user_id = ?", (user_id,))
    ratings = cursor.fetchall()
    conn.close()
    return {rating['movie_id']: rating['rating'] for rating in ratings}



@app.route('/collab')
def collab():
    return render_template('collab.html')

@app.route('/game')
def game():
    return render_template('game.html')

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

def fetch_spotify_data(sp):
    favorite_music = []
    recently_played_tracks = []

    try:
        top_tracks = sp.current_user_top_tracks(limit=10)
        favorite_music = [
            {
                'name': track['name'],
                'artist': track['artists'][0]['name'],
                'album_image': track['album']['images'][0]['url'],
                'spotify_url': track['external_urls']['spotify']
            }
            for track in top_tracks['items']
        ]

        recent_tracks = sp.current_user_recently_played(limit=10)
        recently_played_tracks = [
            {
                'name': track['track']['name'],
                'artist': track['track']['artists'][0]['name'],
                'album': track['track']['album']['name'],
                'album_image_url': track['track']['album']['images'][0]['url'],
                'preview_url': track['track']['preview_url'],
                'external_url': track['track']['external_urls']['spotify']
            }
            for track in recent_tracks['items']
        ]
    except Exception as e:
        print(f"Error fetching Spotify data: {e}")

    return favorite_music, recently_played_tracks

#trivia
@app.route('/get_global_leaderboard')
def get_global_leaderboard_route():
    conn = get_db_connection()
    leaderboard = get_leaderboard(conn)
    conn.close()
    return jsonify(leaderboard)

@app.route('/get_friends_leaderboard')
def get_friends_leaderboard_route():
    if 'username' not in session:
        return jsonify([])
    
    conn = get_db_connection()
    leaderboard = get_friends_leaderboard(conn, session['username'])
    conn.close()
    return jsonify(leaderboard)

@app.route('/get_trivia_question')
def get_trivia_question():
    if 'username' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    if 'token_info' not in session:
        return jsonify({'error': 'Spotify authentication required'}), 400
    
    token_info = session.get('token_info')
    sp = Spotify(auth=token_info['access_token'])
    
    try:
        top_artists = sp.current_user_top_artists(limit=5, time_range='short_term')['items']
        artist_names = [artist['name'] for artist in top_artists]
        asked_questions = session.get('asked_questions', [])
        question_data = generate_trivia_question(artist_names, asked_questions)
        if question_data:
            session['asked_questions'] = asked_questions + [question_data['question']]
            session['current_question'] = question_data
            return jsonify(question_data)
        else:
            return jsonify({'error': 'Failed to generate question'}), 500
    except Exception as e:
        print(f"Error generating trivia question: {e}")
        return jsonify({'error': 'Error generating trivia question'}), 500

@app.route('/answer_trivia', methods=['POST'])
def answer_trivia():
    if 'username' not in session or 'current_question' not in session:
        return jsonify({'error': 'Invalid session'}), 400

    data = request.get_json()
    user_answer = data.get('answer')
    current_question = session['current_question']

    if user_answer == current_question['correct_answer']:
        conn = get_db_connection()
        update_score(conn, session['username'], 1)
        conn.close()
        result = {'status': 'correct', 'message': 'Correct answer!', 'correct_answer': current_question['correct_answer']}
    else:
        result = {'status': 'incorrect', 'message': f"Wrong answer. The correct answer was {current_question['correct_answer']}.", 'correct_answer': current_question['correct_answer']}

    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True, port=8080)
