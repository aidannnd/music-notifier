from spotipy.oauth2 import SpotifyClientCredentials
import spotipy
import sys

import artist_update

'''
This file wil check Index_Info for all artists in Artists.txt.
If any are not there it calls artist_update and adds the information
'''

def add_artist(f_index, artist, sp):
    """
        Populates the Indexed_Info.txt file with formatted info for the latest albums and singles
        for each artist
        PARAMS
        - f_index(file object): the file object for Indexed_Info.txt
        - artist(string): the name of the artist to look up info on
        - sp: a spotipy.client.Spotify object for calling the API
        NO RETURN
    """
    f_index.write(artist + '\n')
    artist_id = artist_update.get_artist(artist, sp) # get artist id
    albums = artist_update.get_latest_albums(artist_id, sp)
    singles = artist_update.get_latest_singles(artist_id, sp)

    for album in albums:
        f_index.write(album + '\n')
    
    for single in singles:
        f_index.write(single + '\n')
    
    f_index.write('\n')

def main():
    sp = artist_update.set_credentials()

    f_artists = open("Artists.txt", "r")
    f_index = open("Indexed_Info.txt", "r+")
    for artists_line in f_artists:
        found_artist = False
        for index_line in f_index:
            if index_line.strip() == artists_line.strip():
                found_artist = True
                break
        if not found_artist:
            add_artist(f_index, artists_line.strip(), sp)
            
    f_index.close()
    f_artists.close()

if __name__ == "__main__":
    main()