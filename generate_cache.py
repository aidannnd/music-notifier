import spotipy
import spotipy.util as util

if __name__ == '__main__':
    with open("app_info.txt") as app_info:
        username = input("Enter username: ")
        client_id = app_info.readline().strip()
        client_secret = app_info.readline().strip()
        redirect_uri = app_info.readline().strip()
        scope = "playlist-modify-private playlist-modify-public user-follow-read ugc-image-upload"

        token = util.prompt_for_user_token(username, scope, client_id, client_secret, redirect_uri)
        sp = spotipy.Spotify(token)