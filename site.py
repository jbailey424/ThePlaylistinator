import streamlit as st
from api_tools import *
#DISCLAIMERS:
# the site only has access to my private spotify data, so features that SHOULD be acting on the end-users account will instead just happen to my account. you can only browse public playlists or my playlists, you can only upload playlists to my account, you can only query from my listening history. This is just a sad result of how streamlit interacts with the spotify API authentication :(
# many API call functions limit their output to 100 songs. the playlist you build can be as long as you want, but when pulling songs from other playlists only their first 100 songs will be accessible
# only the first listed artist for a song is retrieved, features or second artists are just discarded (sorry!)

#TO-DOS:
# display album cover with song lists
# i would like to be able to click on displayed songs in a playlist and get a popup with some stats about the song
# song/artist names with special characters mess up the st.write, look into fixing
# page selection inputs and song removal inputs are one step behind and refresh off. whats going on?
# for search or for short playlists, get rid of page navigation. make it only appear if you have a long enough selection

st.set_page_config(page_title = 'THE PLAYLISTINATOR', page_icon = 'exploding_head', layout = 'wide')

#
#FUNCTIONS AND SESSION VARIABLES HERE, SITE LAYOUT BELOW
#
if 'new_playlist_list' not in st.session_state:
    st.session_state['new_playlist_list'] = []
if 'page_number' not in st.session_state:
    st.session_state['page_number'] = 1
if 'previous_playlist' not in st.session_state:
    st.session_state['previous_playlist'] = None
    
def url_input():
    url_input = st.text_input(label='Enter a Spotify playlist URL', help='Tooltip :)')
    return url_input

def user_playlist_selectbox():
    playlist_dict = {key: value for key, value in get_user_playlists()}
    selected_name = st.selectbox(label = 'Pick from user playlists',
                                     options = [i[0] for i in get_user_playlists()],
                                     index = 0,
                                     help = 'tooltip :)',)
    return playlist_dict[selected_name]

def song_search_results():
    search_query = st.text_input(label = 'Search for tracks', help = 'Tooltip :)')
    return search_query

#
#SITE LAYOUT HERE
#

#TITLE HEADER
st.subheader('For DATA 440, made by Jeff Bailey')
st.title("Let's make a playlist. First, select a list of input songs to start.")

#BROWSING/ADDING SONG SECTION
col1, col2 = st.columns([0.3, 0.7])   

with col1: #select how to retrieve songs, currently by selecting playlist from library or by url. add song suggestions and search
    st.header('Add songs by:')
    method = st.radio(label = 'choose', options = ('Select User Playlist', 'Enter Playlist URL', 'Search Tracks', 'Search LastFM Tags (WIP)', 'Spotify Suggestions (WIP)'), index = 1)
    if method == 'Select User Playlist':
        selected_playlist = user_playlist_selectbox()
    elif method == 'Search Tracks':
        selected_playlist = song_search_results() #maybe change selected_playlist to songlist now that there are other options?
    else:
        selected_playlist = url_input()

with col2:
     #for these methods, display the selected playlist and its tracks 
    try:
        if (method == 'Select User Playlist') or (method == 'Enter Playlist URL'):
            selected_playlist_data = sp.playlist(selected_playlist)
            imagecol, titlecol = st.columns([0.2, 0.8])
            with imagecol:
                st.image(selected_playlist_data['images'][0]['url'])
            with titlecol:
                st.subheader(selected_playlist_data['name'])
                st.write(selected_playlist_data['description'])
                st.write(str('By ' + selected_playlist_data['owner']['display_name']))
            selected_playlist_df = pd.DataFrame(get_trackdata_from_playlist(selected_playlist))
            analyze_selected_playlist = False
            analyticscol, addallcol, _ = st.columns([0.12, 0.12, 0.76])
            with analyticscol:
                if st.button(label = 'Analytics'):
                    analyze_selected_playlist = True
                    st.write('analyzing!')
            with addallcol:
                if analyze_selected_playlist == False:
                    if st.button(label = 'ADD ALL'):
                        st.session_state['new_playlist_list'].extend(selected_playlist_df.to_dict(orient='records'))
                else:
                    if st.button(label = 'Back to songs'):
                        analyze_selected_playlist = False
            if selected_playlist != st.session_state['previous_playlist']: #reset to page 1 if you pick a new playlist
                st.session_state['page_number'] = 1
                st.session_state['previous_playlist'] = selected_playlist
        elif (method == 'Search Tracks'):
            if (selected_playlist != None) and (selected_playlist != ''):
                st.write('Top ten results for "' + selected_playlist + '"')
            #needs to define selected_playlist_df with song data from the given "selected_playlist" search query
            selected_playlist_df = pd.DataFrame(get_trackdata_from_search(selected_playlist))
            if selected_playlist != st.session_state['previous_playlist']: #reset to page 1 if you pick a new playlist
                st.session_state['page_number'] = 1
                st.session_state['previous_playlist'] = selected_playlist
        
        if analyze_selected_playlist == True:
            display_analytics(selected_playlist_df)
            st.write('put graphs here')
        else:
            with st.container():
                songs_per_page = 10
                col1, col2, col3 = st.columns([0.2, 0.6, 0.2]) #navigation buttons
                with col1:
                    if st.button("Previous") and (st.session_state.page_number > 1):
                        st.session_state.page_number -= 1
                with col2:
                    placeholder_pagetext = st.empty()
                with col3:
                    if st.button("Next") and (st.session_state.page_number * songs_per_page < len(selected_playlist_df)):
                        st.session_state.page_number += 1

                start_index = (st.session_state.page_number - 1) * songs_per_page
                end_index = min(start_index + songs_per_page, len(selected_playlist_df))
                col_addsong, col_songname = st.columns([0.1, 0.9])
                for i in range(start_index, end_index): #display songs within selected index                
                    songforadding = dict(selected_playlist_df.loc[i])
                    tooltipstring = str(songforadding['artist_name'] + '\n' + str(songforadding['duration']))
                    col_addsong, col_songinfo, col_songname = st.columns([0.1, 0.06, 0.84])
                    with col_addsong:
                        if st.button(label = 'add', help = 'Add this song to your new playlist!', key = i):
                            st.session_state['new_playlist_list'].append(songforadding)
                    with col_songinfo:
                        st.image(songforadding['image_url'])
                        #st.button(label="ℹ️", help = tooltipstring, key = (str(i) + 'infobutton'))
                    with col_songname:
                        st.write(songforadding['name'] + ' by ' + songforadding['artist_name'])            

    except Exception as e: #handle issues and report to user
        if selected_playlist == '':
            st.write('Awaiting input 😇')
        elif 'http status: 40' in str(e):
            st.write('Invalid URL 😧')
        else:
            st.write(e)        

#ANALYZING/EDITING NEW PLAYLIST SECTION
st.title("BEHOLD YOUR NEW PLAYLIST:")
removecol, infocol = st.columns([0.1, 0.9])
with removecol:
    for i in range(len(st.session_state.new_playlist_list)):
        if st.button('X', key = (str(i) + 'removebuttonnewplaylist')):
            st.session_state['new_playlist_list'].pop(i)
            
new_playlist_df = pd.DataFrame(st.session_state.new_playlist_list)
with infocol:
    for i in range(len(st.session_state.new_playlist_list)):
        imagecol, namecol = st.columns([0.03, 0.97])
        with imagecol:
            st.image(new_playlist_df.loc[i]['image_url'])
        with namecol:
            st.write(new_playlist_df.loc[i]['name'])
        
#SETTING EMPTYS FOR FORCING THINGS TO LOAD LAST
try:
    with placeholder_pagetext.container():
        st.write(f"Page {st.session_state['page_number']}, showing songs {start_index + 1} to {end_index} out of {len(selected_playlist_df)}.")
except:
    pass

st.write(new_playlist_df)