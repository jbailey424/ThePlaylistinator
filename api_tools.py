import numpy as np
import requests
import pandas as pd
import spotipy
import datetime
from spotipy.oauth2 import SpotifyOAuth
import streamlit as st
import plotly.express as px
from sklearn.preprocessing import MinMaxScaler

'''
spotipy stuff
'''
client_id = "c5029ed3aca649949ef00903e6aabf91"
client_secret = "836208c86df64c4d98db67b6bc426ace"

sp = spotipy.Spotify(
    auth_manager=SpotifyOAuth(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri="http://localhost:8000/callback",
        scope="user-read-recently-played,playlist-read-private,user-modify-playback-state,user-top-read",  # add additional scopes as needed
    )
)

# parking lot for finished functions :)
def get_user_playlists() -> list: #list of playlists for the signed-in user, of form [{'name':str, 'uri':str}, ]
    output = []
    for playlist in sp.current_user_playlists()['items']:
        output.append([playlist['name'], playlist['uri']])
    return output

def get_songlist_from_playlist(playlist:str) -> list: #list of track uris from inputed playlist id/uri/url
    playlist = sp.playlist(playlist)
    songlist = []
    for i in range(len(playlist['tracks']['items'])):
        songlist.append(playlist['tracks']['items'][i]['track']['uri'])
    return songlist

def get_trackdata_from_search(search_query:str) -> list: #returns a list of song metadata dictionaries from a search query
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

def get_trackdata_from_playlist(playlist:str) -> list: #returns a list of song metadata dictionaries from a playlist id/uri/url
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

def get_songlist_from_history(limit:int) -> list: #returns list of song uris from user history, not currently used
    history = sp.current_user_recently_played(limit=limit)
    songlist = []
    for i in range(len(history['items'])):
        songlist.append(history['items'][i]['track']['uri'])
    return songlist

def get_songlist_from_toptracks(limit:int, time:str) -> list: #returns list of song uris from user's top tracks, not currently used
    #time can be one of three strings, 'long_term' gives all recorded data, 'medium_term' gives 6 months, 'short_term' gives 4 weeks
    history = sp.current_user_top_tracks(limit=limit, offset=0, time_range=time)
    songlist = []
    for i in range(len(history['items'])):
        songlist.append(history['items'][i]['uri'])
    return songlist

def get_fulldata_from_songlist(songlist:list)->list: #from an inputted list of song uris, return a list of dictionaries of song audio attributes
    dictlist = []
    songfeatures = sp.audio_features(songlist) #query audio features in one batch because the API limits this call
    for i, n in enumerate(songlist):
        info = sp.track(n) #query song info one at a time because API doesn't care about this call
        features = songfeatures[i]
        songdata = {'name':info['name'],
                    'uri':info['uri'],
                    'first_artist':info['artists'][0]['uri'], #will i ever need to process features or collab type songs? revisit this perhaps
                    'artist_name':info['artists'][0]['name'],
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
                    'time_signature':features['time_signature'],}
        dictlist.append(songdata)
    return dictlist

def make_df_from_songlist(songlist:list): #i dont remember making this function and it references another function that doesnt exist. who knows!
    df = []
    for ID in songlist:
        df.append(get_features_from_song(ID))
    return pd.DataFrame(df)

'''
lastfm stuff
'''

key = 'a73abdec33ee8367126a980e3f067eaa'
secret = '3e380c0f4443ba6f282d2e345717bed5'
agent = 'jeff424'

def lastfm_call(payload):
    headers = {'user-agent': 'jeff424'}
    url = 'https://ws.audioscrobbler.com/2.0/'
    payload['api_key'] = 'a73abdec33ee8367126a980e3f067eaa'
    payload['format'] = 'json'
    response = requests.get(url, headers=headers, params=payload)
    return response

def gettoptags_fromsong(songname, artistname):
    tags = []
    try:
        r = lastfm_call({'method': 'track.getTopTags', 'track':songname, 'artist':artistname, 'autocorrect':1})
        for tag in r.json().get('toptags', {}).get('tag', [])[:15]:
            tags.append(tag['name'])
    except:
        pass
    return tags

'''
visualizations
'''
def display_analytics(playlistdf):
    #so final goal for this, is to display a nice spread of playlist summary stats and graphs :)
    fulldata = get_fulldata_from_songlist(playlistdf['uri'])
    fulldf = pd.DataFrame(fulldata)
    st.write(round(playlistdf['duration'].mean()/60, 2))
    attribute_radar(fulldf)
    #st.write(fulldf)
    
def attribute_radar(songlist_data): #make a plotly radar plot of the mean of the following song attributes for an inputted df
    scaler = MinMaxScaler()
    attributes = ['popularity', 'danceability', 'energy', 'loudness', 'speechiness', 'valence', 'instrumentalness', 'acousticness', 'liveness', 'tempo']
    playlistdf_norm = pd.DataFrame(scaler.fit_transform(songlist_data[attributes]), columns = [s.capitalize() for s in attributes])
    means = playlistdf_norm.mean()
    fig = px.line_polar(r = list(means.values), 
                        theta = list(means.to_dict().keys()), 
                        range_r = [0, 1],
                        line_close=True, line_shape = 'spline')
    fig.update_traces(fill='toself')
    fig.update_polars(
        radialaxis=dict(
            tickvals=[],
            tickmode='array',
            showticklabels=False,
            showline = False))
    fig.update_layout(font=dict(size=14, family="Arial Black", color="SteelBlue"))
    st.plotly_chart(fig, use_container_width=True)