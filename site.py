import streamlit as st
from api_tools import *

st.set_page_config(page_title = 'THE PLAYLISTINATOR', page_icon = 'exploding_head', layout = 'wide')

with st.container():
    st.subheader('For DATA 440, made by Jeff Bailey')
    st.title('PAGE TITLE')
    selected_playlist = st.selectbox(label = 'pick a playlist',
                                     options = [i[1] for i in get_user_playlists()],
                                     index = 0,
                                     help = 'tooltip :)',
                                    )
    
with st.container():
    st.write('so the page just displays top to bottom as you write in st features?\nbehold your selected playlists data:')
    
st.write(make_df_from_songlist(get_songlist_from_playlist(selected_playlist)))