import numpy as np
import pandas as pd
import spotipy
import datetime
from spotipy.oauth2 import SpotifyOAuth

# Replace with your own credentials from the Spotify Developer Dashboard
client_id = "c5029ed3aca649949ef00903e6aabf91"
client_secret = "836208c86df64c4d98db67b6bc426ace"

# Initialize the SpotifyOAauth object with the required scopes and redirect URI
sp = spotipy.Spotify(
    auth_manager=SpotifyOAuth(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri="http://localhost:8000/callback",
        scope="user-read-recently-played,playlist-read-private,user-modify-playback-state,user-top-read",  # Add additional scopes as needed
    )
)

# parking lot for finished functions :)
def get_user_playlists():
    output = []
    for playlist in sp.current_user_playlists()['items']:
        output.append([playlist['name'], playlist['uri']])
    return output

def get_songlist_from_playlist(playlist:str) -> list:
    playlist = sp.playlist(playlist)
    songlist = []
    for i in range(len(playlist['tracks']['items'])):
        songlist.append(playlist['tracks']['items'][i]['track']['uri'])
    return songlist

def get_trackdata_from_search(search_query:str) -> list:
    results = sp.search(q = search_query, limit = 10, type = 'track')
    tracklist = []
    for song in results['tracks']['items']:
        songdict = {'name':song['name'],
                    'uri':song['uri'],
                    'first_artist':song['artists'][0]['uri'],
                    'artist_name':song['artists'][0]['name'],
                    'image_url':song['album']['images'][0]['url'],
                    'duration':song['duration_ms']/1000,
                    'popularity':song['popularity']}
        tracklist.append(songdict)
    return tracklist

def get_trackdata_from_playlist(playlist:str) -> list:
    playlist = sp.playlist(playlist)
    tracklist = []
    for song in playlist['tracks']['items']:
        songdict = {'name':song['track']['name'],
                    'uri':song['track']['uri'],
                    'first_artist':song['track']['artists'][0]['uri'],
                    'artist_name':song['track']['artists'][0]['name'],
                    'image_url':song['track']['album']['images'][0]['url'],
                    'duration':song['track']['duration_ms']/1000,
                    'popularity':song['track']['popularity']}
        tracklist.append(songdict)
    return tracklist

def get_songlist_from_history(limit:int) -> list:
    history = sp.current_user_recently_played(limit=limit)
    songlist = []
    for i in range(len(history['items'])):
        songlist.append(history['items'][i]['track']['uri'])
    return songlist

def get_songlist_from_toptracks(limit:int, time:str) -> list:
    #time can be one of three strings, 'long_term' gives all recorded data, 'medium_term' gives 6 months, 'short_term' gives 4 weeks
    history = sp.current_user_top_tracks(limit=limit, offset=0, time_range=time)
    songlist = []
    for i in range(len(history['items'])):
        songlist.append(history['items'][i]['uri'])
    return songlist

def get_features_from_song(ID:str) -> dict:
    info = sp.track(ID)
    features = sp.audio_features(ID)[0]
    songdata = {'name':info['name'],
                   'uri':info['uri'],
                   'first_artist':info['artists'][0]['uri'], #will i ever need to process features or collab type songs? revisit this perhaps
                   'album':info['album']['uri'],
                   'duration_s':(info['duration_ms']/1000),
                   'release_date':info['album']['release_date'],  
                   'age':(datetime.date.today().year - int(info['album']['release_date'][:4])),
                   'popularity':info['popularity'],
                   'danceability':features['danceability'],
                   'energy':features['energy'],
                   'loudness':features['loudness'],
                   'speechiness':features['speechiness'],
                   'valence':features['valence'],
                   'instrumentalness':features['instrumentalness'],
                   'acousticness':features['acousticness'],
                   'liveness':features['liveness'],
                   'tempo':features['tempo'],
                   'mode':features['mode'],
                   'key':features['key'],
                   'time_signature':features['time_signature'],
                  }
    return songdata

def make_df_from_songlist(songlist:list):
    df = []
    for ID in songlist:
        df.append(get_features_from_song(ID))
    return pd.DataFrame(df)