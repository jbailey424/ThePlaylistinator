import numpy as np
import requests
import pandas as pd
import spotipy
import datetime
from spotipy.oauth2 import SpotifyOAuth
import streamlit as st
import plotly.express as px
from sklearn.preprocessing import MinMaxScaler
import random

'''
spotipy stuff
'''
client_id = "id"
client_secret = "secret"

sp = spotipy.Spotify( #authorize connection with spotify API, which is accessed through spotipy
    auth_manager=SpotifyOAuth(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri="http://localhost:8000/callback",
        scope="user-read-recently-played,playlist-read-private,user-modify-playback-state,user-top-read",  # add additional scopes as needed
    )
)

def get_user_playlists() -> list: #list of playlists for the signed-in user, of form [{'name':str, 'uri':str}, ]
    '''
    Returns a list of playlist URI's as strings. It gets the URI of every playlist saved in the authorized user's library
    '''
    output = []
    for playlist in sp.current_user_playlists()['items']:
        output.append([playlist['name'], playlist['uri']])
    return output

def get_songlist_from_playlist(playlist:str) -> list: #list of track uris from inputed playlist id/uri/url
    '''
    given a public or authorized playlist's URI as a string, this returns a list of every song's URI from the playlist. 
    '''
    playlist = sp.playlist(playlist)
    songlist = []
    for i in range(len(playlist['tracks']['items'])):
        songlist.append(playlist['tracks']['items'][i]['track']['uri'])
    return songlist

def give_recs(playlistdf):
    '''
    given a dataframe generated from a playlist
    '''
    tracklist = playlistdf['uri'].to_list()
    seed = random.sample(tracklist, min(5, len(tracklist))) if len(tracklist) > 5 else tracklist
    recs = sp.recommendations(seed_tracks = seed, limit = 10)
    tracklist = []
    for song in recs['tracks']:
        songdict = {'name':song['name'],
                    'uri':song['uri'],
                    'first_artist':song['artists'][0]['uri'],
                    'artist_name':song['artists'][0]['name'],
                    'image_url':song['album']['images'][0]['url'],
                    'duration':song['duration_ms']/1000,
                    'popularity':song['popularity']}
        tracklist.append(songdict)
    return pd.DataFrame(tracklist)

def get_trackdata_from_search(search_query:str) -> list: #returns a list of song metadata dictionaries from a search query
    '''
    given a string, query a search for tracks from spotify. return a usable set of metadata dictionaries for each song in the search results. 
    '''
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

def get_trackdata_from_lastfmtag(tag):
    '''
    query songs tagged on lastfm with the inputted string. for the returned songs, get their spotify metadata and return a list of dictionaries.
    '''
    tracklist = []
    faillist = []
    r = lastfm_call({'method': 'tag.getTopTracks', 'tag':tag})
    for i, n in enumerate(r.json()['tracks']['track']):
        try:
            search = f"{n['name']} {n['artist']['name']}"
            song = sp.search(q=search, type='track', limit=1)['tracks']['items'][0]
            songdict = {'name':song['name'],
                        'uri':song['uri'],
                        'first_artist':song['artists'][0]['uri'],
                        'artist_name':song['artists'][0]['name'],
                        'image_url':song['album']['images'][0]['url'],
                        'duration':song['duration_ms']/1000,
                        'popularity':song['popularity']}
            tracklist.append(songdict)
        except:
            faillist.append(n)
    return tracklist

def get_trackdata_from_playlist(playlist:str) -> list: #returns a list of song metadata dictionaries from a playlist id/uri/url
    '''
    given a playlist URI or URL as a string, get the metadata for each song on the playlist and return it as a list of dictionaries.
    '''
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
    '''
    returns a list of song URI's from the authenticated user's most recent listening history. Only parameter is 'limit', the number of songs returned.
    '''
    history = sp.current_user_recently_played(limit=limit)
    songlist = []
    for i in range(len(history['items'])):
        songlist.append(history['items'][i]['track']['uri'])
    return songlist

def get_songlist_from_toptracks(limit:int, time:str) -> list: #returns list of song uris from user's top tracks, not currently used
    '''
    returns list of song URI's from the authenticated user's top tracks.
    limit is the number of songs returned, up to 100
    time can be one of three strings, 'long_term' gives all recorded data, 'medium_term' gives 6 months, 'short_term' gives 4 weeks
    '''
    history = sp.current_user_top_tracks(limit=limit, offset=0, time_range=time)
    songlist = []
    for i in range(len(history['items'])):
        songlist.append(history['items'][i]['uri'])
    return songlist

def get_fulldata_from_songlist(songlist:list)->list: #from an inputted list of song uris, return a list of dictionaries of song audio attributes
    '''
    from a list of song URI's, return a list of dictionaries containing full metadata AND audio features
    can easily be used to expand a metadata df into a full audio df with:
    fulldf = pd.DataFrame(get_fulldata_from_songlist(df['uri']))
    '''
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
    '''
    setup for easy lastfm api calls
    '''
    headers = {'user-agent': 'jeff424'}
    url = 'https://ws.audioscrobbler.com/2.0/'
    payload['api_key'] = 'key' #insert the actual key here!
    payload['format'] = 'json'
    response = requests.get(url, headers=headers, params=payload)
    return response

def gettoptags_fromsong(songname, artistname, limit=15):
    '''
    given a song and artist name, retrieve the top 15 lastfm tags on it
    '''
    tags = []
    try:
        r = lastfm_call({'method': 'track.getTopTags', 'track':songname, 'artist':artistname, 'autocorrect':1})
        for tag in r.json().get('toptags', {}).get('tag', [])[:limit]:
            tags.append(tag['name'])
    except:
        pass
    return tags

'''
visualizations or etc
'''
def barchart_tags(playlistdf): #requires taglist already be a column of df
    '''
    creates and displays a barchart of lastfm tag frequency for a playlistdf. Only needs metadata df, not audio features.
    for each row of the playlist, it queries the lastfm tag using the songs name and artist name. tags are then all counted and visualized.
    '''
    df = playlistdf.copy()
    df['name'] = df['name'] + ' by ' + df['artist_name'] + '<br>'
    exploded_df = df.explode('taglist')
    tag_counts = exploded_df['taglist'].value_counts().reset_index()
    tag_counts.columns = ['Tag', 'Frequency']
    tag_counts = tag_counts[:20]
    #tag_counts = tag_counts[tag_counts['Frequency'] >= 2]
    tag_songs = exploded_df.groupby('taglist')['name'].apply(list).reset_index()
    tag_songs.columns = ['Tag', 'Songs']
    tag_data = pd.merge(tag_counts, tag_songs, on='Tag')
    tag_data = tag_data.sort_values(by='Frequency', ascending=False)
    fig = px.bar(
        tag_data,
        x='Tag',
        y='Frequency',
        title='Tags Distribution and Frequency',
        hover_data={'Songs': True},
        labels={'Frequency': 'Frequency'},
        color = tag_data['Tag'], color_discrete_sequence = px.colors.qualitative.T10)
    fig.update_traces(
        hovertemplate='%{x} appears %{y} times, from:<br>%{customdata}',
        hovertext=tag_data.apply(lambda row: '<br>'.join(row['Songs']), axis=1))
    fig.update_traces(hoverlabel_bgcolor='SteelBlue')
    fig.update_layout(
        showlegend=False,
        xaxis_title='', yaxis_title='',
        font=dict(size=10, family="Arial Black", color="SteelBlue"),
        width=800,
        height=400,)
    st.plotly_chart(fig, use_container_width = True, theme = None)
    
def timeline_chart(df):
    '''
    given a metadata dataframe, create and display a timeline visualization showing distribution of release years of songs.
    '''
    playlistdf = df.copy()
    playlistdf['release_date'] = playlistdf['release_date'].str.slice(0,4)
    playlistdf['year'] = pd.to_datetime(playlistdf['release_date'], errors='coerce').dt.year
    playlistdf['song_name_artist'] = playlistdf['name'] + ' by ' + playlistdf['artist_name']
    yearly_song_lists = playlistdf.groupby('year')['song_name_artist'].apply(list).reset_index(name='song_names')
    fig = px.line(yearly_song_lists, x='year', y=yearly_song_lists['song_names'].apply(len),
                  hover_data={'song_names': True}, 
                  title='Songs by Year',
                  line_shape = 'spline',)
    #fig.update_yaxes(range=[0, max(yearly_song_lists['song_names'].apply(len))])
    fig.update_layout(xaxis=dict(title='', showgrid=False), yaxis=dict(title='', showgrid=True),)
    fig.update_layout(font=dict(size=10, family="Arial Black", color="SteelBlue"),
                     width = 800, height = 400)
    fig.update_traces(
        hovertemplate='%{y} songs from %{x}, including: <br>%{hovertext}',
        hovertext=yearly_song_lists['song_names'].apply(lambda x: '<br>'.join(x)))
    fig.update_traces(hoverlabel_bgcolor='SteelBlue')
    st.plotly_chart(fig, use_container_width = True, theme = None)
    
def attribute_radar(songlist_data): #make a plotly radar plot of the mean of the following song attributes for an inputted df
    '''
    given a full audio feature dataframe, make and display a radar chart showing means 
    '''
    attributes = ['popularity', 'danceability', 'energy', 'valence', 'instrumentalness', 'acousticness', 'speechiness', 'liveness']
    playlistdf = songlist_data[attributes]
    playlistdf.loc[:, 'popularity'] = playlistdf['popularity'] / 100
    playlistdf.columns = [s.capitalize() for s in attributes]
    means = playlistdf.mean()
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
    fig.update_layout(font=dict(size=10, family="Arial Black", color="SteelBlue"),
                     width = 400, height = 400)
    st.plotly_chart(fig, use_container_width = True, theme = None)

def duration_histogram(df):
    '''
    given metadata df, make and display a histogram of song lengths
    '''
    fig = px.histogram(df,
        x='duration_s',
        title='Song Durations',
        nbins=int(round((max(df['duration_s']) + 30) / 30)),
        range_x=[0, round(max(df['duration_s']) + 30)])
    fig.update_layout(
        font=dict(size=10, family="Arial Black", color="SteelBlue"),
        width=800,
        height=400,
        xaxis=dict(tickmode='array',
            tickvals=list(range(0, round(max(df['duration_s'])) + 60, 60)),
            ticktext=[f"{divmod(x, 60)[0]}:{divmod(x, 60)[1]:02}" for x in range(0, round(max(df['duration_s'])) + 60, 60)],
            tickangle=45,
            tickformat='%M:%S',
            title='',),
        yaxis=dict(title=''),)
    st.plotly_chart(fig, use_container_width = True, theme = None)

def display_analytics(playlistdf):
    '''
    given a metadata df, make a full audio feature df and then display an organized dashboard of all the above visualizations for the inputted playlist df. 
    '''
    playlistdata = pd.DataFrame(get_fulldata_from_songlist(playlistdf['uri']))
    taglist = taglist_fromplaylistdf(playlistdata)
    playlistdata['taglist'] = taglist
    fulldf = pd.DataFrame(playlistdata)
    x = playlistdf['duration'].mean()
    st.write(f"This playlist has {len(playlistdf)} songs. The average song length is {format_seconds(x)}.")
    col1, col2 = st.columns(2)
    with col1:
        attribute_radar(fulldf)
    with col2:
        duration_histogram(fulldf)
    col1, col2 = st.columns(2)
    with col1:
        timeline_chart(fulldf)
    with col2:
        barchart_tags(fulldf)
    

def songviz(song:dict):
    '''
    make a radar chart of a single song's audio features by quickly converting it to a df
    '''
    tags = gettoptags_fromsong(song['name'], song['artist_name'], 10)
    attributes = get_fulldata_from_songlist([song['uri']])[0]
    write, viz = st.columns(2)
    with write:
        st.write(attributes['name'] + ' was released ' + attributes['release_date'] + f". Its top tags are {', '.join(tags)}")
    with viz:
        attribute_radar(pd.DataFrame([attributes]))
    return tags, attributes

def taglist_fromplaylistdf(playlistdata)->list:
    '''
    retrieve a list of lists of tags for each song in an inputted playlist df    
    '''
    listlist = []
    for i in (range(len(playlistdata))):
        track, artist = playlistdata.loc[i]['name'], playlistdata.loc[i]['artist_name']
        tags = gettoptags_fromsong(track, artist)
        listlist.append(tags)
    return listlist

def count_strings(list_of_lists):
    '''
    given a list of lists, return a dictionary showing the number of times each unique item appeared across all the lists. 
    this is used for making the bar chart of tags from the list of lists of tags as generated with taglist_fromplaylistdf
    '''
    string_count = {}
    for lst in list_of_lists:
        for string in lst:
            string_count[string] = string_count.get(string, 0) + 1
    sorted_dict = dict(sorted(string_count.items(), key=lambda item: item[1], reverse=True))
    return sorted_dict

def format_seconds(seconds):
    '''
    reformat a song length in seconds into a nice string of form MM:SS
    '''
    minutes, seconds = divmod(seconds, 60)
    return f"{int(minutes)}:{int(seconds):02d}"