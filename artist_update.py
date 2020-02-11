from spotipy.oauth2 import SpotifyClientCredentials
import spotipy
import smtplib, ssl # for email sending and encryption

import index_artist

def set_credentials():
    """
        Sets my developer credentials for accessing the Spotify API and creates a Spotipy 
        object for calling the API.
        RETURNS
        - sp: a spotipy.client.Spotify object for calling the API
    """
    # sets my developer credentials for accessing the Spotify API
    client_credentials_manager = SpotifyClientCredentials(client_id='4f851eec64194e3e87195933f6360226', client_secret='9a521ac9a1fd4ade87aa5743efe55620')
    sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
    sp.trace = False
    return sp

def get_artist(name, sp):
    """
        Calls the Spotify API for information about the given artist's albums. Creates a list
        of the latest albums up to a max of 5, skipping duplicates. 
        PARAMS
        - name(str): the name of the artist to access the API with
        - sp: a spotipy.client.Spotify object for calling the API
        RETURNS
        a dictionary of artist info from the API, or None
    """
    results = sp.search(q='artist:' + name, type='artist')
    items = results['artists']['items']
    if len(items) > 0:
        return items[0]
    else:
        return None

def get_latest_albums(artist, sp):
    """
        Calls the Spotify API for information about the given artist's albums. Creates a list
        of the latest albums up to a max of 5, skipping duplicates. 
        PARAMS
        - artist(dict): information received from the Spotify API about an artist
        - sp: a spotipy.client.Spotify object for calling the API
        RETURNS
        - return_list(list): a formatted list output of the artist's latest albums
    """
    return_list = []
    albums = []
    results = sp.artist_albums(artist['id'], album_type='album')
    albums.extend(results['items'])
    while results['next']:
        results = sp.next(results)
        albums.extend(results['items'])
    return_list.append('---Latest albums:')
    unique = set()  # skip duplicate albums
    count = 0
    for album in albums:
        if count == 5: # max 5 latest albums
            break
        name = album['name'].lower()
        if name not in unique:
            return_list.append(album['name'])
            unique.add(name)
            count+=1
    return return_list

def get_latest_singles(artist, sp):
    """
        Calls the Spotify API for information about the given artist's singles. Creates a list
        of the latest singles up to a max of 5, skipping duplicates. 
        PARAMS
        - artist(dict): information received from the Spotify API about an artist
        - sp: a spotipy.client.Spotify object for calling the API
        RETURNS
        - return_list(list): a formatted list output of the artist's latest albums
    """
    return_list = []
    singles = []
    results = sp.artist_albums(artist['id'], album_type='single', limit=5)
    singles.extend(results['items'])
    while results['next']:
        results = sp.next(results)
        singles.extend(results['items'])
    return_list.append('---Latest singles/EPs:')
    unique = set()  # skip duplicate albums
    count = 0
    for single in singles:
        if count == 5: # max 5 latest singles
            break
        name = single['name'].lower()
        if name not in unique:
            return_list.append(single['name'])
            unique.add(name)
            count+=1
    return return_list

# def get_latest_features(artist, sp):
#     """
#         Calls the Spotify API for information about the given artist's features. Creates a list
#         of the latest features up to a max of 5, skipping duplicates.
#         PARAMS
#         - artist(dict): information received from the Spotify API about an artist
#         - sp: a spotipy.client.Spotify object for calling the API
#         RETURNS
#         - return_list(list): a formatted list output of the artist's latest albums
#     """
#     return_list = []
#     features = []
#     results = sp.artist_albums(artist['id'], album_type='appears_on', limit=5)
#     features.extend(results['items'])
#     while results['next']:
#         results = sp.next(results)
#         features.extend(results['items'])
#     return_list.append('---Latest features:')
#     unique = set()  # skip duplicate albums
#     count = 0
#     for feature in features:
#         if count i == 5: # max 5 latest singles
#             break
#         name = feature['name'].lower()
#         if name not in unique:
#             return_list.append(feature['name'])
#             unique.add(name)
#             count+=1
#     return return_list

def compare_updates(compare_list, artists_list):
    """
        Parse through the compare_list and compare it to Index_Info.txt. Build a list of artists
        who have new music.
        PARAMS
        - compare_list(list): comprised of an artist followed by their latest albums and singles,
        formatted similarily to the Indexed_Info.txt file
        - artists_list(list): artists to check for new music
        RETURNS
        = new_music_artists(list): a list of artists who have new music
    """

    # get the list of artists with new music
    index_list = []
    for line in f_index:
        index_list.append(line.strip())
    
    new_music_artists = []
    artists_list_index = 0
    current_artist = artists_list[artists_list_index]
    skip_to_next = False
    index_list_offset = 0

    for index, elem in enumerate(compare_list):
        if elem == '':
            skip_to_next = False
            artists_list_index += 1
            current_artist = artists_list[artists_list_index]

        if not skip_to_next and elem != index_list[index - index_list_offset]:
            new_music_artists.append(current_artist)
            skip_to_next = True
            index_list_offset += 1

    # update the Indexed_Info.txt
    open('Indexed_Info.txt', 'w').close() # wipe the file
    index_artist.main()

    return new_music_artists

def send_email(new_music_artists):
    """
        Send an email address containing a list of artists with new music
        PARAMS
        - new_music_artists(list): artists with new music
        NO RETURN
    """
    
    artist_str = ""
    for artist in new_music_artists:
        if new_music_artists.index(artist) == len(new_music_artists) - 1:
            artist_str += artist
        else:
            artist_str += artist + ", "

    # Create a secure SSL context
    context = ssl.create_default_context()

    with smtplib.SMTP_SSL("smtp.gmail.com", port, context=context) as server:
        port = 465  # For SSL (the default is 465)
        smtp_server = "smtp.gmail.com"
        sender_email = "email.notif.artistupdate@gmail.com"  # the sender address
        receiver_email = "email.notif.artistupdate@gmail.com"  # the receiver address
        password = "_gUq2^d.~!fe+" # sender address password
        message = "From: email.notif.artistupdate@gmail.com\n" \
        "To: email.notif.artistupdate@gmail.com\n" \
        "Subject: New music on Spotify\n\n" \
        "We've detected new music from the following artists:\n\n{:s}".format(artist_str)

        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, message)

if __name__ == '__main__':
    sp = set_credentials() # set up my app credentials

    f_artists = open("Artists.txt", "r")
    f_index = open("Indexed_Info.txt", "r+")
    compare_list = [] # to fill with the lines from Indexed_Info.txt
    artists_list = [] # to fill with the artists who we want to check for new music
    for artists_line in f_artists:
        artists_list.append(artists_line.strip())
        compare_list.append(artists_line.strip())
        artist_id = get_artist(artists_line, sp) # get a dictionary of artist info from API
        compare_list.extend(get_latest_albums(artist_id, sp)) # add the formatted album output to compare_list
        compare_list.extend(get_latest_singles(artist_id, sp)) # add the formatted singles output to compare_list
        compare_list.append('')
    compare_list.pop() # remove the last ' ' appended to prevent overflow in compare_updates
    
    new_music_artists = compare_updates(compare_list, artists_list)
    if new_music_artists != []: # there was at least one artist with new music to send an email
        send_email(new_music_artists)

    f_index.close()
    f_artists.close()