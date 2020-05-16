import spotipy
import spotipy.util as util
import smtplib, ssl # for email sending and encryption
from email.mime.text import MIMEText # for sending email with a hyperlink
from email.mime.multipart import MIMEMultipart
import json
import os

def read_app_info():
    """
        Reads from the app_info.txt file and creates a list of variables to be used by other functions.
        :return: list of variables from app_info.txt
    """
    # get info from app_info.txt
    file_name = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app_info.txt") # adds the path up to the file for running different working directory settings
    app_info_fp = open(file_name)
    
    username = app_info_fp.readline().strip()
    client_id = app_info_fp.readline().strip()
    client_secret = app_info_fp.readline().strip()
    redirect_uri = app_info_fp.readline().strip()
    sender_email = app_info_fp.readline().strip()
    sender_password = app_info_fp.readline().strip()
    receiver_email = app_info_fp.readline().strip()
    placeholder = app_info_fp.readline().strip()

    try:
        playlist_id = app_info_fp.readline().strip()
    except: # there is not an existing playlist_id in app_info
        playlist_id = ""

    app_info_fp.close()

    return [username, client_id, client_secret, redirect_uri, sender_email, sender_password, receiver_email, placeholder, playlist_id]

def set_credentials(username, client_id, client_secret, redirect_uri):
    """
        Sets the developer credentials for accessing the Spotify API and creates a Spotipy object for calling the API.
        :param username: username from app_info.txt
        :param client_id: Spotify app client_id from app_info.txt
        :param client_secret: Spotify app client_secret from app_info.txt
        :param redirect_uri: Spotify app redirect_uri from app_info.txt
        :return: sp (a Spotipy object)
    """
    scope = "playlist-modify-private playlist-modify-public user-follow-read"
    token = util.prompt_for_user_token(username, scope, client_id, client_secret, redirect_uri)
    sp = spotipy.Spotify(token)
    return sp

def get_new_music(saved_data, api_data):
    """
        Compares saved_data and api_data, compiles a dict of artists with new music.
        :param saved_data: a dict of indexed data from data.txt
        :param api_data: a dict of up-to-date data from the API
        :return: new_music (a dict of new music)
    """
    new_music = {} # a dict to represent artists with new music with titles of the new singles/albums, structured differently than other dicts like api_data

    for artist in api_data.keys(): # artist is an artist_id in this case
        if artist in saved_data.keys(): # artist has been previously indexed
            # see if there is a discrepancy between the two regarding the saved albums/singles
            if sorted(api_data[artist]["singles"]) != sorted(saved_data[artist]["singles"]) or \
                sorted(api_data[artist]["albums"]) != sorted(saved_data[artist]["albums"]): # we use sorted here because sometimes the order of album ids from the api changes
                new_music[artist] = {}
                new_music[artist]["name"] = api_data[artist]["name"]
                # get a list of items that appear in api_data but not in saved_data, add it to new_music
                new_music[artist]["albums"] = list(set(api_data[artist]["albums"]) - set(saved_data[artist]["albums"])) # set difference
                new_music[artist]["singles"] = list(set(api_data[artist]["singles"]) - set(saved_data[artist]["singles"])) # set difference

    file_name = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data.txt") # adds the path up to the file for running different working directory settings
    with open(file_name, 'w') as out_file:
        json.dump(api_data, out_file) # update indexed data with up-to-date data

    return new_music

def get_latest(artist, album_type, sp):
    """
        Calls the API for information about the given artist's album_type. Creates a list
        of the latest items of album_type up to a max of 5, skipping duplicates.
        * Performs one API call per artist
        :param artist: the artist id to look up (string)
        :param album_type: either "single" or "album"
        :param sp: the Spotipy object
        :return: items (a list of up to 5 items of album_type requested for the artist)
    """
    items = []
    results = sp.artist_albums(artist, album_type, country="US") # calls API and gets a dict
    for item in results["items"]:
        if len(items) == 5: # get up to last 5 items of album_type for artist
            break
        if item["id"] not in items:
            items.append(item["id"])
    return items

def update_followed_artists(sp):
    """
        Calls the API for the current authorized user to get their followed artists and updates the saved_data json for any new artists.
        The API can only be called with 50 artists at a time, so the function will loop until complete.
        * Performs round_up(number_of_followed_users/50) calls for the first call
        * Performs 2*number_of_followed_users for second calls (through get_latest)
        :param sp: the Spotipy object
        :return: the results from a call to get_new_music (a dict) or None (no previously indexed data)
    """
    # fill out the api_data dictionary with information from the API
    num_recieved_artists = 50
    after_id = None # after_id is the last artist ID retrieved from the previous request, starts as None

    api_data = {} # will represent up-to-date information regarding followed artists and their latest single/albums
    while num_recieved_artists == 50:
        artists_dict = sp.current_user_followed_artists(50, after_id) # call API to get a dictionary of 50 followed artists
        after_id = artists_dict["artists"]["cursors"]["after"] # update after_id for use in next call if necessary
        num_recieved_artists = len(artists_dict["artists"]["items"])

        for artist in artists_dict["artists"]["items"]:
            api_data[artist["id"]] = {}
            api_data[artist["id"]]["name"] = artist["name"]
            # calls API through get_latest to get the artists singles and albums
            api_data[artist["id"]]["singles"] = get_latest(artist["id"], "single", sp)
            api_data[artist["id"]]["albums"] = get_latest(artist["id"], "album", sp)

    # try to read the data from data.txt
    file_name = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data.txt") # adds the path up to the file for running different working directory settings
    try:
        with open(file_name) as json_file:
            saved_data = json.load(json_file)
    except: # file is empty, not formatted correctly, or does not exist
        saved_data = {}

    if saved_data == {}: # likely a first time user so no indexed info yet
        # write data (this path will not trigger a notification)
        with open(file_name, 'w') as out_file:
            json.dump(api_data, out_file)
    else:
        return get_new_music(saved_data, api_data) # compare data indexed to new data from api and collect new music

def send_email(sender_email, sender_password, receiver_email, playlist_id):
    """
        Sends an email to the provided address with a link to the user's playlist.
        This email simply serves as a notification.
        :param sender_email: the address the email will be sent from
        :param sender_password: the password for the sender_email
        :param receiver_email: the address that will receive the email sent from sender_email
        :param playlist_id: id of playlist to link in email
    """
    message = MIMEMultipart("alternative")
    message["Subject"] = "New music on Spotify"
    message["From"] = sender_email
    message["To"] = receiver_email

    playlist_link = "https://open.spotify.com/playlist/" + playlist_id

    # create the plain-text and HTML versions of the message
    text = "We've detected new music!\nCheck it out in your New Music playlist on Spotify"
    html = """\
    <html>
        <body>
            <p>We've detected new music!<br>
            Check it out in your <a href="{:s}">New Music playlist</a></p>
        </body>
    </html>
    """.format(playlist_link)

    # turn the messages into plain/html MIMEText objects
    part1 = MIMEText(text, "plain")
    part2 = MIMEText(html, "html")

    message.attach(part1)
    message.attach(part2)

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, receiver_email, message.as_string())

def add_to_playlist(username, playlist_id, new_music, app_info, sp):
    """
        Adds all the songs from each album in new_music to the supplied playlist_id for the given username.
        If the playlist does not exist it will be created and have its id written to app_info.txt
        :param username: the username to find/create the playlist under
        :param playlist_id: the id of the playlist to find (will be "" if it does not exist)
        :param new_music: a dictionary of new music from update_followed_artists()
        :param app_info: the lines from app_info.txt, obtained in read_app_info()
        :param sp: the Spotipy object
    """
    album_ids = []
    # turn dictionary of new music into list of album ids
    for artist_id in new_music.keys():
        album_ids.extend(new_music[artist_id]['albums'])
        album_ids.extend(new_music[artist_id]['singles'])
    
    # turn the list of album ids into a list of all the song ids from each album
    song_ids = []
    for album_id in album_ids:
        for song in sp.album(album_id)["tracks"]["items"]: # call API to get all the song ids within the given album_id
            song_ids.append(song["id"])

    # try to add song ids to the playlist
    try:
        sp.user_playlist_add_tracks(username, playlist_id, song_ids) # add track
    except: # playlist has not been made before or does not exist anymore
        # overwrite line for playlist_id in app_info.txt
        file_name = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app_info.txt") # adds the path up to the file for running different working directory settings
        app_info_fp = open(file_name, 'w')
        for i in range(0, 8):
            app_info_fp.write(app_info[i] + '\n')

        # call the API and create a playlist then return a dict of related info
        playlist = sp.user_playlist_create(username, "New Music", False, "New music from music notifier, checked daily and updated here.")
        
        app_info_fp.write(playlist["id"])
        app_info_fp.close()

        sp.user_playlist_add_tracks(username, playlist["id"], song_ids) # add tracks to the newly-created playlist
        
        return playlist["id"]

if __name__ == '__main__':
    app_info = read_app_info()
    # app_info is formatted: [username, client_id, client_secret, redirect_uri, sender_email, sender_password, receiver_email, placeholder, *playlist_id]
    
    sp = set_credentials(app_info[0], app_info[1], app_info[2], app_info[3]) # create spotipy object and set credentials

    new_music = update_followed_artists(sp)

    if new_music is not None and new_music != {}: # there was new music found
        new_playlist_id = add_to_playlist(app_info[0], app_info[8], new_music, app_info, sp) # add new music to playlist
        
        if (app_info[4] != "(Sender Email Address *Optional)"): # user has filled in information for sending email
            if new_playlist_id is not None: # update playlist_id if necessary
                app_info[8] = new_playlist_id 
            
            send_email(app_info[4], app_info[5], app_info[6], app_info[8]) # send an email