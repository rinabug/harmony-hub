from dotenv import load_dotenv
import os
import sqlite3
import uuid
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, json
from werkzeug.utils import secure_filename
import hashlib
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
from spotipy.cache_handler import FlaskSessionCacheHandler
from backend.user_auth import create_tables, get_db_connection, register_user, login_user, update_profile, get_profile, is_valid_email, is_valid_password, set_reset_token, get_user_by_reset_token, reset_password, alter_profiles_table
from backend.concert_recommendations import get_concert_recommendations
from backend.music_recommendation import get_music_recommendations
from backend.recent_listens import get_recently_played_tracks
from backend.friend_system import view_friends, view_friend_requests, accept_friend_request, send_friend_request, create_friend_tables, alter_friends_table, initialize_friend_system
from backend.tmdb_recommendations import get_movie_recommendations_from_tmdb

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(64)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max upload size

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

load_dotenv()

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

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.before_request
def initialize_database():
    conn = get_db_connection()
    create_tables()
    alter_profiles_table()
    initialize_friend_system(conn)
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

    return render_template('profile.html', username=username, favorite_music=favorite_music, user_profile=user_profile, recently_played_tracks=recently_played_tracks)


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

        # Placeholder for badges and recent activities
        badges = []  # You should replace this with actual badge data from your database
        recent_activity = []  # You should replace this with actual recent activity data from your database

        return render_template('user_profile.html',
                               user_profile=user_profile,
                               favorite_music=favorite_music,
                               recently_played_tracks=recently_played_tracks,
                               favorite_movies=[],  # Add actual favorite movies if available
                               recent_activity=recent_activity,
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
    friends = view_friends(conn, username)
    friend_requests = view_friend_requests(conn, username)
    conn.close()

    return render_template('find_friend.html', username=username, friends=friends, friend_requests=friend_requests)


@app.route('/view_friends')
def view_friends_route():
    if 'username' not in session:
        return jsonify({'status': 'error', 'message': 'Please log in.'}), 401
    
    conn = get_db_connection()
    friends = view_friends(conn, session['username'])
    conn.close()
    
    return jsonify({'status': 'success', 'friends': friends})

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

@app.route('/view_friend_requests')
def view_friend_requests_route():
    if 'username' not in session:
        return jsonify({'status': 'error', 'message': 'Please log in.'}), 401
    
    conn = get_db_connection()
    friend_requests = view_friend_requests(conn, session['username'])
    conn.close()
    
    return jsonify({'status': 'success', 'requests': friend_requests})

@app.route('/accept_friend_request', methods=['POST'])
def accept_friend_request_route():
    if 'username' not in session:
        return jsonify({'status': 'error', 'message': 'Please log in.'}), 401
    
    data = request.get_json()
    request_id = data.get('request_id')
    
    conn = get_db_connection()
    accept_friend_request(conn, session['username'], request_id)
    conn.close()
    
    return jsonify({'status': 'success', 'message': 'Friend request accepted'})

@app.route('/send_request', methods=['POST'])
def send_request():
    if 'username' not in session:
        return jsonify({'error': 'Not authenticated'}), 401

    data = request.get_json()
    sender_username = session['username']
    receiver_username = data.get('username')

    conn = get_db_connection()
    success = send_friend_request(conn, sender_username, receiver_username)
    conn.close()

    if success:
        return jsonify({'success': True})
    else:
        return jsonify({'error': 'Failed to send friend request'}), 400

@app.route('/user/<username>')
def user_profile(username):
    if 'username' not in session:
        flash("Please log in to access this page.")
        return redirect(url_for('login'))

    conn = get_db_connection()
    user_profile = get_profile(conn, username)
    
    if not user_profile:
        flash("User not found.")
        return redirect(url_for('find_friend'))
    
    favorite_music = json.loads(user_profile['favorite_music']) if user_profile['favorite_music'] else []
    recently_played_tracks = json.loads(user_profile['recently_played_tracks']) if user_profile['recently_played_tracks'] else []

    # Placeholder for badges and recent activities
    badges = []  # You should replace this with actual badge data from your database
    recent_activity = []  # You should replace this with actual recent activity data from your database

    return render_template('user_profile.html', 
                           user_profile=user_profile, 
                           favorite_music=favorite_music, 
                           favorite_movies=[],  # Add actual favorite movies if available
                           recent_activity=recent_activity,
                           badges=badges)

@app.route('/add_favorite_movie', methods=['POST'])
def add_favorite_movie():
    if 'username' not in session:
        flash("Please log in to access this page.")
        return redirect(url_for('login'))

    title = request.form['title']
    username = session['username']

    profile_conn = get_db_connection()
    cursor = profile_conn.cursor()

    cursor.execute('''
    SELECT favorite_movies FROM profiles WHERE username = ?
    ''', (username,))
    favorite_movies = cursor.fetchone()[0]
    favorite_movies = json.loads(favorite_movies) if favorite_movies else []

    favorite_movies.append({'title': title})

    cursor.execute('''
    UPDATE profiles
    SET favorite_movies = ?
    WHERE username = ?
    ''', (json.dumps(favorite_movies), username))

    profile_conn.commit()
    profile_conn.close()

    flash('Favorite movie/show added successfully', 'success')
    return redirect(url_for('profile'))


@app.route('/add_recently_watched', methods=['POST'])
def add_recently_watched():
    if 'username' not in session:
        flash("Please log in to access this page.")
        return redirect(url_for('login'))

    title = request.form['title']
    username = session['username']

    profile_conn = get_db_connection()
    cursor = profile_conn.cursor()

    cursor.execute('''
    SELECT recently_watched FROM profiles WHERE username = ?
    ''', (username,))
    recently_watched = cursor.fetchone()[0]
    recently_watched = json.loads(recently_watched) if recently_watched else []

    recently_watched.append({'title': title})

    cursor.execute('''
    UPDATE profiles
    SET recently_watched = ?
    WHERE username = ?
    ''', (json.dumps(recently_watched), username))

    profile_conn.commit()
    profile_conn.close()

    flash('Recently watched movie/show added successfully', 'success')
    return redirect(url_for('profile'))


@app.route('/add_review', methods=['POST'])
def add_review():
    if 'username' not in session:
        flash("Please log in to access this page.")
        return redirect(url_for('login'))

    title = request.form['title']
    review_text = request.form['review_text']
    username = session['username']

    profile_conn = get_db_connection()
    cursor = profile_conn.cursor()

    cursor.execute('''
    SELECT reviews FROM profiles WHERE username = ?
    ''', (username,))
    reviews = cursor.fetchone()[0]
    reviews = json.loads(reviews) if reviews else []

    reviews.append({'title': title, 'review_text': review_text})

    cursor.execute('''
    UPDATE profiles
    SET reviews = ?
    WHERE username = ?
    ''', (json.dumps(reviews), username))

    profile_conn.commit()
    profile_conn.close()

    flash('Review added successfully', 'success')
    return redirect(url_for('profile'))



@app.route('/collab')
def collab():
    return render_template('collab.html')

@app.route('/game')
def game():
    return render_template('game.html')


def ensure_token_validity(token_info):
    """
    Ensure the Spotify token is valid, refreshing it if necessary.
    """
    if sp_oauth.is_token_expired(token_info):
        token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
        session['token_info'] = token_info
    return token_info

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

if __name__ == '__main__':
    app.run(debug=True, port=8080)


