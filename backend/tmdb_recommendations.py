import os
import requests
from dotenv import load_dotenv

load_dotenv()

TMDB_API_KEY = os.getenv('TMDB_API_KEY')

def get_movie_recommendations_from_tmdb(genre, age_rating, year_range):
    genre_map = {
        "Action": 28,
        "Adventure": 12,
        "Comedy": 35,
        "Drama": 18,
        "Fantasy": 14,
        "Horror": 27,
        "Mystery": 9648,
        "Romance": 10749,
        "Sci-Fi": 878,
        "Thriller": 53
    }

    year_map = {
        "2000-2010": (2000, 2010),
        "2011-2015": (2011, 2015),
        "2016-2020": (2016, 2020),
        "2021-present": (2021, 2024)  # Adjust this range as needed
    }

    start_year, end_year = year_map[year_range]

    url = f"https://api.themoviedb.org/3/discover/movie"
    params = {
        'api_key': TMDB_API_KEY,
        'with_genres': genre_map[genre],
        'certification_country': 'US',
        'certification': age_rating,
        'primary_release_date.gte': f'{start_year}-01-01',
        'primary_release_date.lte': f'{end_year}-12-31',
        'sort_by': 'popularity.desc'
    }

    response = requests.get(url, params=params)
    data = response.json()
    
    recommendations = []
    if 'results' in data:
        for movie in data['results'][:10]:  # Get the top 10 recommendations
            movie_id = movie['id']
            watch_providers = get_watch_providers(movie_id)
            trailer_url = get_movie_trailer(movie_id)
            recommendations.append({
                'title': movie['title'],
                'overview': movie.get('overview', 'No overview available'),
                'release_date': movie.get('release_date', 'Unknown release date'),
                'poster_path': f"https://image.tmdb.org/t/p/w500{movie['poster_path']}" if movie.get('poster_path') else None,
                'watch_providers': watch_providers,
                'trailer_url': trailer_url
            })
    return recommendations


def get_watch_providers(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}/watch/providers"
    params = {'api_key': TMDB_API_KEY}
    response = requests.get(url, params=params)
    data = response.json()

    if 'results' in data and 'US' in data['results']:
        providers = data['results']['US']
        streaming_providers = providers.get('flatrate', [])
        streaming_names = [provider['provider_name'] for provider in streaming_providers]
        return streaming_names
    return []


def get_movie_trailer(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}/videos?api_key={TMDB_API_KEY}"
    response = requests.get(url)
    data = response.json()
    
    if 'results' in data:
        for video in data['results']:
            if video['site'] == 'YouTube' and video['type'] == 'Trailer':
                return f"https://www.youtube.com/embed/{video['key']}"
    return None