from dotenv import load_dotenv
import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import pandas as pd

# get credentials from .env file

load_dotenv()

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT = os.getenv("REDIRECT")

# init spotipy

scope = "playlist-modify-private playlist-read-private"

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    redirect_uri=REDIRECT,
    scope=scope
))

# get user_id
def get_user_id():
    user_profile = sp.current_user()
    return user_profile['id']

# get playlist_id given playlist name
def get_playlist_id(playlist_name: str) -> str:
    playlists = sp.current_user_playlists()
    for playlist in playlists['items']:
        if playlist['name'] == playlist_name:
            return playlist['id']
    
    return None

# ask user for playlist to search
def ask_playlist():
    playlist_name = input("Please enter the name of the playlist you would like to search: ")
    playlist_id = get_playlist_id(playlist_name)

    while playlist_id is None:
        playlist_name = input("Playlist does not exist. Please try again: ")
        playlist_id = get_playlist_id(playlist_name)
    
    return playlist_id

# get all songs in a playlist
def get_all_songs(playlist_id: str) -> list:
    results = []
    offset = 0

    # add all songs in batches of 100
    while True:
        curr_batch = sp.playlist_items(playlist_id, fields="items(track(id, artists(name)))",offset=offset)
        
        # exit if no more songs exist in the playlist
        if not curr_batch or 'items' not in curr_batch or not curr_batch['items']:
            break

        results.extend([
            {
                "artists": [artist['name'] for artist in item['track']['artists'] if 'name' in artist],
                "id": item['track']['id']
            }
            for item in curr_batch['items'] if item.get('track')
        ])

        offset += 100

    return results

# check if artist exists in artist list
def is_artist_present(artist_list, artist_name):
    return any(artist.lower() == artist_name.lower() for artist in artist_list)

# main function
def main() -> None:

    # ask user for playlist to search
    playlist_id = ask_playlist()
    
    # get all songs in that playlist
    all_songs = get_all_songs(playlist_id)

    # store playlist in a pandas df
    df = pd.DataFrame(all_songs)

    # ask user which artist they want a playlist of
    artist_name = input("Please enter the name of the artist you would like to search for: ")
    
    # filter playlist by artist name
    mask = df['artists'].apply(lambda artists: is_artist_present(artists, artist_name))
    artist_songs = df[mask]

    # if no songs are found, exit program
    if artist_songs.empty:
        print(f"No songs by {artist_name} exist in this playlist.")
        return

    # create new playlist
    user_id = get_user_id()
    new_playlist = sp.user_playlist_create(user=user_id, name=f"{artist_name} playlist", public=False)
    new_playlist_id = new_playlist['id']

    # add songs into new playlist in batches of 100
    for i in range(0, artist_songs.shape[0], 100):
        batch_ids = artist_songs['id'].iloc[i:i+100].tolist()
        sp.playlist_add_items(new_playlist_id, batch_ids)

    print(f"New playlist created with {artist_songs.shape[0]} songs by {artist_name}")
    return


if __name__ == "__main__":
    main()