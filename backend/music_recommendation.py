from spotipy import Spotify

def get_music_recommendations(sp: Spotify, limit=10):
    top_tracks = sp.current_user_top_tracks(limit=5, time_range='short_term')
    track_ids = [track['id'] for track in top_tracks['items']]
    recommendations = sp.recommendations(seed_tracks=track_ids, limit=limit)
    formatted_recommendations = []
    for track in recommendations['tracks']:
        formatted_recommendations.append({
            'name': track['name'],
            'artist': track['artists'][0]['name'],
            'album': track['album']['name'],
            'preview_url': track['preview_url'],
            'external_url': track['external_urls']['spotify']
        })
    return formatted_recommendations