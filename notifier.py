import spotipy
import spotipy.util as util
import smtplib, ssl # for email sending and encryption
import json

def set_credentials():
    """
        Sets the developer credentials for accessing the Spotify API and creates a Spotipy object for calling the API.
        :return: sp (Spotipy object)
    """
    # get info from app_Info.txt
    appfile = open("app_info.txt")

    username = appfile.readline().strip()
    client_id = appfile.readline().strip()
    client_secret = appfile.readline().strip()
    redirect_uri = appfile.readline().strip()
    scope = "playlist-modify-private user-follow-read"

    appfile.close()

    # sets my developer credentials for accessing the Spotify API
    token = util.prompt_for_user_token(username, scope, client_id, client_secret, redirect_uri)
    sp = spotipy.Spotify(token)
    return sp

def get_new_music(saved_data, api_data):
    """
        Compares saved_data and api_data, compiles a dict of artists with new music.
        :param saved_data: a dict of indexed data from data.txt stored on the computer
        :param api_data: a dict of up-to-date data from the API
        :return: new_music (a dict of new music for use by send_email)
    """
    new_music = {} # a dict to represent artists with new music with titles of the new singles/albums, structured differently than other dicts like api_data

    for artist in api_data.keys(): # artist is an artist_id in this case
        if artist in saved_data.keys(): # artist has been previously indexed
            if api_data[artist] != saved_data[artist]: # there is a discrepancy between the two regarding the saved albums/singles for the artist
                new_music[artist] = {}
                new_music[artist]["name"] = api_data[artist]["name"]
                # get a list of items that appear in api_data but not in saved_data, add it to new_music
                new_music[artist]["albums"] = list(set(api_data[artist]["albums"]) - set(saved_data[artist]["albums"])) # set difference
                new_music[artist]["singles"] = list(set(api_data[artist]["singles"]) - set(saved_data[artist]["singles"])) # set difference

    if new_music != {}: # there was some new music found
        with open("data.txt", 'w') as out_file:
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
        if len(items) < 5: # get up to last 5 items of album_type for artist
            if item["name"] not in items:
                items.append(item["name"])
        else:
            break
    return items

def update_followed_artists(sp):
    """
        Calls the API for the current authorized user to get their followed artists and updates the saved_data json for any new artists.
        The API can only be called with 50 artists at a time, so the function will loop until complete.
        * Performs round_up(number_of_followed_users/50) calls for the first call
        * Performs 2*number_of_followed_users for second calls (through get_latest)
        :param sp:  the Spotipy object
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
    with open("data.txt") as json_file:
        try:
            saved_data = json.load(json_file)
        except: # file is empty or not formatted correctly
            saved_data = {}

    if saved_data == {}: # likely a first time user so no index info yet
        # write data (this path will not trigger a notification)
        with open("data.txt", 'w') as out_file:
            json.dump(api_data, out_file)
    else:
        return get_new_music(saved_data, api_data) # compare data indexed to new data from api and collect new music

def send_email(new_music):
    """
        Sends an email to the provided address with formatted text dexcribing artists with new albums or singles.
        :param new_music: a dict of artists and their new music
    """
    # create formatted output for the email
    music_formatted = ""
    for artist in new_music.keys():
        music_formatted += new_music[artist]["name"] + ": "
        for album in new_music[artist]["albums"]:
            music_formatted += album + ", "
        for single in new_music[artist]["singles"]:
            music_formatted += single + ", "
        music_formatted = music_formatted[:-2] # remove last ", "
        music_formatted += '\n'

    # create a secure SSL context
    context = ssl.create_default_context()

    appfile = open("app_info.txt")
    lines = appfile.readlines() # get contents of app_info as a list
    appfile.close()

    # for SSL the default port is 465
    with smtplib.SMTP_SSL("smtp.gmail.com", port=465, context=context) as server:
        smtp_server = "smtp.gmail.com"
        sender_email = lines[4].strip()  # the sender address
        receiver_email = lines[5].strip()  # the receiver address
        password = lines[6].strip() # sender address password
        message = "From: {:s}\n" \
        "To: {:s}\n" \
        "Subject: New music on Spotify\n\n" \
        "We've detected new music!\n\n{:s}".format(sender_email, receiver_email, music_formatted)

        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(smtp_server, port=465, context=context) as server:
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, message)

if __name__ == '__main__':
    sp = set_credentials() # create spotipy object and set credentials
    
    new_music = update_followed_artists(sp)

    if new_music is not None: # there was new music found
        send_email(new_music)