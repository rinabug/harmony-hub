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
    # This is a simple recommendation system. In a real-world scenario, 
    # you'd use a more sophisticated algorithm based on user preferences.
    movies = ia.get_top250_movies()
    return [{'title': movie['title'], 'year': movie['year'], 'director': movie['directors'][0]['name'] if movie.get('directors') else 'Unknown'} for movie in movies[:5]]

def get_show_recommendations(username):
    # Similarly, this is a simple recommendation system for TV shows.
    shows = ia.get_top250_tv()
    return [{'title': show['title'], 'year': show['year'], 'creator': show['creators'][0]['name'] if show.get('creators') else 'Unknown'} for show in shows[:5]]