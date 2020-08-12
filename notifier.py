import spotipy
import spotipy.util as util
import smtplib, ssl # for email sending and encryption
from email.mime.text import MIMEText # for sending email with a hyperlink
from email.mime.multipart import MIMEMultipart
import base64
import json
import os
from datetime import timedelta, date

def read_app_info():
    """
        Reads from the app_info.txt file and creates a list of variables to be used by other functions.
        :return: list of variables from app_info.txt
    """
    # get info from app_info.txt
    file_name = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app_info.txt") # adds the path up to the file for running different working directory settings
    with open(file_name) as app_info_fp:
        client_id = app_info_fp.readline().strip()
        client_secret = app_info_fp.readline().strip()
        redirect_uri = app_info_fp.readline().strip()
        sender_email = app_info_fp.readline().strip()
        sender_password = app_info_fp.readline().strip()

    return [client_id, client_secret, redirect_uri, sender_email, sender_password]

def check_for_dir(name):
    """ Creates the given name as a directory if it does not exist, expects a '/' at the end of the name """
    if not os.path.isdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), name)): # cache_files folder does not exist
        os.mkdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), name))

def set_credentials(username, client_id, client_secret, redirect_uri):
    """
        Sets the developer credentials for accessing the Spotify API and creates a Spotipy object for calling it.
        :param username: a Spotify username
        :param client_id: Spotify app client_id from app_info.txt
        :param client_secret: Spotify app client_secret from app_info.txt
        :param redirect_uri: Spotify app redirect_uri from app_info.txt
        :return: sp (a Spotipy object)
    """
    scope = "playlist-modify-private playlist-modify-public user-follow-read ugc-image-upload"

    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache_files/.cache-" + username) # look in cache_files
    token = util.prompt_for_user_token(username, scope, client_id, client_secret, redirect_uri, path)
    sp = spotipy.Spotify(token)
    return sp

def update_user_info(username, sp):
    """
        Will create user_info.txt if it does not exist then fetches data from the api for each user placed in the cache_files folder.
        If a user does not exist in user_info.txt for a cache file, a playlist will be made for the user and the function will request an email via the console.
        If a user already exists in user_info.txt, their followed artists will be updated.
        :param username: a Spotify username
        :param sp: a Spotipy object
        :return: user_info (the contents of user_info.txt, a dict of information about each user)
    """
    file_name = os.path.join(os.path.dirname(os.path.abspath(__file__)), "user_info.txt")
    try:
        in_file = open(file_name) # will try to open file
        user_info = json.load(in_file)
    except: # file not created yet
        user_info = {}

    if username not in user_info.keys():
        user_info[username] = {}
        user_info[username]["playlist_id"] = create_playlist(username, sp) # creates playlist on the account and returns the id
        user_info[username]["email"] = input("Enter new user email: ") # get user email from console

    # update followed_artists for the user
    user_info[username]["followed_artists"] = get_followed_artists(username, sp) # gets a dict of form artist_id:artist_name

    try: # will close the file if it was opened previously
        in_file.close()
    except:
        pass

    with open(file_name, 'w') as out_file: # write to user_info.txt, create file if it does not exist
        json.dump(user_info, out_file)

    return user_info

def create_playlist(username, sp):
    """
        Creates a playlist on the username's account and gives it the cover photo of "playlist_cover.jpg".
        :param username: a Spotify username
        :param sp: a Spotipy object
        :return: the playlist id of the playlist just created (str)
    """
    playlist = sp.user_playlist_create(username, "New Music", False, "New music from artists you follow, checked daily and updated by music notifier.")

    # add a playlist cover
    file_name = os.path.join(os.path.dirname(os.path.abspath(__file__)), "playlist_cover.jpg")
    with open(file_name, "rb") as img_file:
        image_data = base64.b64encode(img_file.read())
        sp.playlist_upload_cover_image(playlist["id"], image_data)

    return playlist["id"]

def get_followed_artists(username, sp):
    """
        Calls the API for the user and gets a dictionary of information about the artists they follow, then turns it into a dict of artist_id:artist_name.
        :param username: a Spotify username
        :param sp: a Spotipy object
        :return: followed_artists (a dict representing information about the artists the username follows)
    """
    num_recieved_artists = 50
    after_id = None # after_id is the last artist ID retrieved from the previous request, starts as None

    followed_artists = {} # will represent information about the user's followed artists
    while num_recieved_artists == 50: # the last call to the API will get 50 or less artists
        artists_dict = sp.current_user_followed_artists(50, after_id) # call API to get a dictionary of 50 followed artists
        
        after_id = artists_dict["artists"]["cursors"]["after"] # update after_id for use in next call if necessary
        num_recieved_artists = len(artists_dict["artists"]["items"])

        for artist in artists_dict["artists"]["items"]: # populate followed_artists
            followed_artists[artist["id"]] = artist["name"]

        if after_id is None: # edge case for if user is following a number of artists divisible by 50
            break

    return followed_artists

def remove_users(users, user_info):
    """
        Removes users who have been previously saved in user_info.txt, but no longer appear in cache_files to prevent unnecessary API calls when getting new music.
        :param users: usernames that appear in the cache_files folder (list)
        :param user_info: the json curently stored in user_info.txt, guaranteed up-to-date (dict)
    """
    removed_user = False
    for indexed_user in list(user_info.keys())[:]:
        if indexed_user not in users:
            user_info.pop(indexed_user, None)
            removed_user = True

    if removed_user: # a user was removed from user_info, update the user_info.txt text file
        file_name = os.path.join(os.path.dirname(os.path.abspath(__file__)), "user_info.txt")
        with open(file_name, 'w') as out_file:
            json.dump(user_info, out_file)

def get_new_music(user_info):
    """
        Calls the API for every unique artist followed by the whole userbase.
        Gets each artist's last 5 albums and singles, determines if they are new by comparing today's date and the release date.
        If new music is found, the api data gets added to the new_music dict
        Creates the log_information dict with usernames to be filled with data later
        :param user_info: the json curently stored in user_info.txt, guaranteed up-to-date (dict)
        :param return: new_music (a dict of new music from artists the userbase follows, formatted artist_id:album_dict)
        :param return: log_information (a dict of information to later write into the logs folder, this funciton only fills it with usernames from user_info)
    """
    print("Calling API for new music")
    log_information = {}
    new_music = {}

    followed_artists = set()
    for username in user_info.keys(): # fill followed_artists with ids of all followed artists for all users, ignore duplicaates
        followed_artists.update(user_info[username]["followed_artists"].keys())
        log_information[username] = []

    for artist_id in followed_artists:
        # call api for each artist and get their last 5 albums and singles
        albums = sp.artist_albums(artist_id, "album", country="US", limit=5)
        singles = sp.artist_albums(artist_id, "single", country="US", limit=5)

        # fill a list with all the music received for the artist
        music = []
        music.extend(albums["items"])
        music.extend(singles["items"])

        for album in music:
            # get the release date and turn it into a date type
            date_parts = album["release_date"].split('-') # usually formatted: "XXXX-XX-XX"
            try:
                release_date = date(int(date_parts[0]), int(date_parts[1]), int(date_parts[2]))
            except:
                # the format of the release_date is not always year-month-day
                # the release_date_precision for albums can vary, for example, it may only include the year
                # in this case we ignore the release, assuming all newer music has the necessary metadata
                continue

            # this is what determines if an album is new or not
            if release_date + timedelta(days = 1) >= date.today(): # was released today or yesterday
                # if it was released yesterday, we need to make sure it was after the script ran (checks logs to do this)

                check_for_dir("logs/")

                file_name = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs/" + str(date.today() - timedelta(days = 1)) + ".txt")
                try: # see if there was a log generated yesterday
                    in_file = open(file_name) # will try to open file
                    yesterday_log = json.load(in_file)

                    #TODO this is inefficient, could be improved (also running for removed?)
                    for user in yesterday_log.keys(): # loop over each user, see if the album id was added for any of them
                        if album["id"] in yesterday_log[user]: # album has already been added to users who follow the artist
                            raise Exception("Album already added")

                    # the release has not been previously added. Add the artist if necessary, then the album
                    if artist_id in new_music.keys():
                        new_music[artist_id].append(album)
                    else:
                        new_music[artist_id] = [album]
                except:
                    # album was added yesterday, or no log could be found
                    pass

    return new_music, log_information

def update_playlists(user_info, new_music, spotipy_objects, log_information):
    """
        Updates the playlists of users who follow artists who appear in the new_music dict.
        Creates a text file in the logs folder with generate_logs() of users who had new music added to their playlists.
        :param user_info: the json curently stored in user_info.txt, guaranteed up-to-date (dict)
        :param new_music: a dict of new music from artists the userbase follows, formatted artist_id:album_dict
        :param spotipy_objects: a list of Spotipy objects created for each cache file in order to have proper permissions for editing each user's playlist
        :param log_information: a dict of usernames from user_info formatted username:[]
        :return: users_to_email (a set of users who had their playlists updated)
    """
    print("Updating playlists")
    users_to_email = set()
    for artist_id in new_music.keys():
        users_to_update = [] # a list of users whose playlists we will update with the specific new item
        for username in user_info.keys():
            if artist_id in user_info[username]["followed_artists"].keys(): # the user follows one of the artists who has new music
                users_to_email.add(username)
                users_to_update.append(username)

        for album in new_music[artist_id]:
            song_ids = []
            # create a list of new song URIs
            for song in sp.album(album["id"])["tracks"]["items"]: # call API to get all the song ids for the given album id
                song_ids.append(song["id"])
            for username in users_to_update: # add songs to the users playlist
                log_information[username].append(album["id"]) # create logs
                spotipy_objects[username].user_playlist_add_tracks(username, user_info[username]["playlist_id"], song_ids) # add tracks

    generate_logs(log_information)

    return users_to_email

def generate_logs(log_information):
    """ Write log_information as a json to a new dated text file in the logs folder """
    check_for_dir("logs/")

    file_name = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs/" + str(date.today()) + ".txt")
    with open(file_name, 'w') as out_file: # write to user_info
        json.dump(log_information, out_file)

def send_email(sender_email, sender_password, users_to_email, user_info):
    """
        Sends a notification email to every user in users_to_email if they have a paired email in user_info.
        Uses the sender_email and sender_password from the app_info.txt file.
        :param sender_email: the address the email will be sent from
        :param sender_password: the password for the sender_email
        :param users_to_email: a list of users who had their playlists updated with new music
        :param user_info: the json curently stored in user_info.txt, guaranteed up-to-date (dict)
    """
    for username in users_to_email:
        receiver_email = user_info[username]["email"]
        if receiver_email != "": # user has paired an email
            message = MIMEMultipart("alternative")
            message["Subject"] = "New music on Spotify"
            message["From"] = sender_email
            message["To"] = receiver_email

            playlist_link = "https://open.spotify.com/playlist/" + user_info[username]["playlist_id"]

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

            # send email
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
                server.login(sender_email, sender_password)
                server.sendmail(sender_email, receiver_email, message.as_string())

if __name__ == '__main__':
    app_info = read_app_info() # get information from app_info.txt
    # app_info is formatted: [client_id, client_secret, redirect_uri, sender_email, sender_password]

    user_info = {}
    spotipy_objects = {} # to be a dict formatted as username:spotipy_object
    users = [] # will be a list of usernames from the cache_files folder

    check_for_dir("cache_files/")

    for cache_name in os.listdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache_files/")): # for cache file in the cache_files folder
        username = cache_name[7:].strip() # all cache files are formatted ".cache-username"

        sp = set_credentials(username, app_info[0], app_info[1], app_info[2]) # create spotipy object and set credentials
        spotipy_objects[username] = sp
        user_info = update_user_info(username, sp)
        users.append(username)

    remove_users(users, user_info) # remove users who are no longer in cache_files to prevent unnecessary API calls
    new_music, log_information = get_new_music(user_info) # collect new music from artists the userbase as a whole follows
    users_to_email = update_playlists(user_info, new_music, spotipy_objects, log_information) # update playlists of users
    send_email(app_info[3], app_info[4], users_to_email, user_info) # send emails to users who have an email on their account