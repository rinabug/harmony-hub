import sqlite3
from imdb import Cinemagoer
import requests

ia = Cinemagoer()

def get_movie_info(movie_title):
    movies = ia.search_movie(movie_title)
    if movies:
        movie_id = movies[0].getID()
        movie = ia.get_movie(movie_id)
        return {
            'title': movie.get('title'),
            'year': movie.get('year'),
            'director': movie.get('directors')[0]['name'] if movie.get('directors') else 'Unknown',
            'rating': movie.get('rating'),
            'plot': movie.get('plot outline', 'No plot available')
        }
    return None

def add_to_wishlist(conn, username, movie_title):
    movie_info = get_movie_info(movie_title)
    if not movie_info:
        return False
    
    cursor = conn.cursor()
    cursor.execute("""
    INSERT OR IGNORE INTO movies (title, release_year, director) 
    VALUES (?, ?, ?)
    """, (movie_info['title'], movie_info['year'], movie_info['director']))
    
    movie_id = cursor.lastrowid if cursor.lastrowid != 0 else cursor.execute("SELECT id FROM movies WHERE title = ?", (movie_info['title'],)).fetchone()[0]
    cursor.execute("INSERT OR IGNORE INTO wishlists (username, movie_id) VALUES (?, ?)", (username, movie_id))
    conn.commit()
    return True

def get_wishlist(conn, username):
    cursor = conn.cursor()
    cursor.execute("""
    SELECT movies.title, movies.release_year, movies.director 
    FROM wishlists 
    JOIN movies ON wishlists.movie_id = movies.id 
    WHERE wishlists.username = ?
    """, (username,))
    return cursor.fetchall()

def add_review(conn, username, movie_title, rating, review_text):
    movie_info = get_movie_info(movie_title)
    if not movie_info:
        return False
    
    cursor = conn.cursor()
    cursor.execute("""
    INSERT OR IGNORE INTO movies (title, release_year, director) 
    VALUES (?, ?, ?)
    """, (movie_info['title'], movie_info['year'], movie_info['director']))
    
    movie_id = cursor.lastrowid if cursor.lastrowid != 0 else cursor.execute("SELECT id FROM movies WHERE title = ?", (movie_info['title'],)).fetchone()[0]
    cursor.execute("INSERT INTO reviews (username, movie_id, rating, review_text) VALUES (?, ?, ?, ?)", 
                   (username, movie_id, rating, review_text))
    conn.commit()
    return True

def get_reviews(conn, username):
    cursor = conn.cursor()
    cursor.execute("""
    SELECT movies.title, movies.release_year, movies.director, reviews.rating, reviews.review_text 
    FROM reviews 
    JOIN movies ON reviews.movie_id = movies.id 
    WHERE reviews.username = ?
    """, (username,))
    return cursor.fetchall()

def get_movie_recommendations(username):
    #CHAT GPT PLACEHOLDER
    url = "https://imdb-api.com/en/API/Top250Movies/YOUR_IMDB_API_KEY"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return [movie['title'] for movie in data['items'][:5]]
    return []