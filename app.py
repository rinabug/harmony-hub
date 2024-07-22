from dotenv import load_dotenv
import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
from spotipy.cache_handler import FlaskSessionCacheHandler
from backend.user_auth import create_users_table, is_valid_email, is_valid_password, register_user, login_user, get_user_id_by_username, get_pending_friend_requests, get_friends, send_friend_request, accept_friend_request, reject_friend_request
from backend.concert_recommendations import get_concert_recommendations
from backend.music_recommendation import get_music_recommendations
from backend.recent_listens import get_recently_played_tracks

#messaging

from flask_socketio import SocketIO, emit, join_room, leave_room
from backend.user_auth import send_message, get_messages, mark_messages_as_read
import datetime



app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(64)
socketio = SocketIO(app, cors_allowed_origins="*") #messaging

DATABASE = 'users.db'

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

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    return conn

@app.before_request
def initialize_database():
    conn = get_db_connection()
    create_users_table(conn)
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


@app.route('/search_friends', methods=['GET'])
def search_friends():
    if 'username' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    query = request.args.get('q')
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT username FROM users WHERE username LIKE ? AND username != ?", (f'%{query}%', session['username']))
    results = [{'username': row[0]} for row in cursor.fetchall()]
    conn.close()
    return jsonify(results)

def ensure_token_validity(token_info):
    """
    Ensure the Spotify token is valid, refreshing it if necessary.
    """
    if sp_oauth.is_token_expired(token_info):
        token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
        session['token_info'] = token_info
    return token_info

@app.route('/send_friend_request', methods=['POST'])
def send_friend_request_route():
    if 'username' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    data = request.json
    receiver_username = data.get('username')
    
    conn = get_db_connection()
    sender_id = get_user_id_by_username(conn, session['username'])
    receiver_id = get_user_id_by_username(conn, receiver_username)
    
    if not receiver_id:
        conn.close()
        return jsonify({'error': 'User not found'}), 404
    
    try:
        success = send_friend_request(conn, sender_id, receiver_id)
        conn.close()
        
        if success:
            return jsonify({'message': 'Friend request sent'}), 200
        else:
            return jsonify({'error': 'Failed to send friend request'}), 400
    except Exception as e:
        conn.close()
        print(f"Error sending friend request: {str(e)}")
        return jsonify({'error': 'An unexpected error occurred'}), 500

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

@app.route('/get_friend_requests', methods=['GET'])
def get_friend_requests_route():
    if 'username' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    conn = get_db_connection()
    user_id = get_user_id_by_username(conn, session['username'])
    friend_requests = get_pending_friend_requests(conn, user_id)
    conn.close()
    
    return jsonify({'requests': [{'id': r[0], 'username': r[1], 'sender_id': r[2]} for r in friend_requests]}), 200

@app.route('/get_friends', methods=['GET'])
def get_friends_route():
    if 'username' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    conn = get_db_connection()
    user_id = get_user_id_by_username(conn, session['username'])
    friends = get_friends(conn, user_id)
    conn.close()
    
    return jsonify({'friends': [{'id': f[0], 'username': f[1]} for f in friends]}), 200

#messaging
@app.route('/get_messages/<int:friend_id>')
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
    conn = get_db_connection()
    sender_id = get_user_id_by_username(conn, data['sender'])
    receiver_id = get_user_id_by_username(conn, data['receiver'])
    content = data['message']
    
    message_id = send_message(conn, sender_id, receiver_id, content)
    conn.close()
    
    if message_id:
        room = f"{min(sender_id, receiver_id)}_{max(sender_id, receiver_id)}"
        emit('new_message', {
            'id': message_id,
            'sender': data['sender'],
            'content': content,
            'timestamp': datetime.now().isoformat()
        }, room=room)
    else:
        emit('error', {'msg': 'Failed to send message'})

@socketio.on('join')
def on_join(data):
    username = data['username']
    room = data['room']
    join_room(room)
    print(f"User {username} joined room {room}")
    emit('user_joined', {'username': username}, room=room)


@socketio.on('leave')
def on_leave(data):
    username = data['username']
    room = data['room']
    leave_room(room)
    print(f"User {username} left room {room}")
    emit('user_left', {'username': username}, room=room)

@socketio.on('send_message')
def handle_message(data):
    print("Received message:", data)
    sender = data['sender']
    receiver = data['receiver']
    content = data['message']
    room = data['room']
    
    # Save message to database
    conn = get_db_connection()
    sender_id = get_user_id_by_username(conn, sender)
    receiver_id = get_user_id_by_username(conn, receiver)
    message_id = send_message(conn, sender_id, receiver_id, content)
    conn.close()
    
    if message_id:
        emit('new_message', {
            'id': message_id,
            'sender': sender,
            'content': content,
            'timestamp': datetime.datetime.now().isoformat()
        }, room=room)
        print(f"Message sent to room {room}")
    else:
        emit('error', {'msg': 'Failed to send message'}, room=request.sid)


if __name__ == '__main__':
    app.run(debug=True, port=8080)


