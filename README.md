# The Playlistinator, for DATA440

## Overview

The **Playlistinator** is a streamlit-based web application that walks users through exploring and curating Spotify playlists. This was inspired by my own personal dissatisfaction with Spotify's playlist discovery and song suggestions methods, and my goal was to make a more interesting and informative interface for making personalized playlists. 

## Features

- **Search by Last.fm Tag:** Explore songs based on Last.fm tags, a powerful user-made library of song features.
- **Spotify Playlist Analytics:** See interesting analytics and summary statistics, either for an existing playlist or for the new one the user creates.
- **Build Your Playlist:** Create and manage a new playlist, informed by analytics and search functions that Spotify itself does not provide

## Setup Instructions

1. **Install Dependencies:**
   ```bash
   pipenv shell
   pipenv install
   ```

2. **Run the Application:**
   ```bash
   streamlit run site.py
   ```

3. **Access the Web Application:**
   Open your web browser and navigate to [http://localhost:8501](http://localhost:8501).

## Limitations and To-Do

- **No individual user authentication:** Because of streamlit limitations, the Spotify API can only be used by a spotify developer account with their own API key. My personal key is hard-coded currently, and theoretically another user could register a dev account for free and replace my key with theirs, but this is untested.
- **100 Song Limit:** The Spotify API only retrieves song lists of up to 100 items, so opening a playlist with too many songs will only return the first 100.
- **Limited Recommendation Systems:** Currently I only implemented the Spotify API suggestion function. My plan was to make unique suggestion functions myself, but time escaped me. Look for them in the final submission!
