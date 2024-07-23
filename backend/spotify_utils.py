from spotipy import Spotify

def extract_top_genres(sp: Spotify):
    top_genres = []
    try:
        top_artists = sp.current_user_top_artists(limit=10)
        for artist in top_artists['items']:
            top_genres.extend(artist['genres'])
    except Exception as e:
        print(f"Error extracting top genres: {e}")
    return top_genres

genre_mapping = {
    'pop': 'Drama',
    'rock': 'Action',
    'hip hop': 'Thriller',
    'jazz': 'Musical',
    'classical': 'Romance',
    'electronic': 'Sci-Fi',
    # Add more mappings as necessary
}