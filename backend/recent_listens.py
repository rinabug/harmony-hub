from spotipy import Spotify

def get_recently_played_tracks(sp: Spotify, limit=10):
    recently_played = sp.current_user_recently_played(limit=limit)
    formatted_tracks = []
    for item in recently_played['items']:
        track = item['track']
        formatted_tracks.append({
            'name': track['name'],
            'artist': track['artists'][0]['name'],
            'album': track['album']['name'],
            'album_image_url': track['album']['images'][0]['url'] if track['album']['images'] else None,
            'preview_url': track['preview_url'],
            'external_url': track['external_urls']['spotify']
        })
    return formatted_tracks
