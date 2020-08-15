Spotify New Music Notifier
==================

This Python script adds new releases from artists users follow to a playlist on their account by calling the Spotify API using Spotipy. It collects followed artist's releases, determines which are new, and adds them to the correct playlists. If a user would like, emails can be sent to notify them of new music as well.

<img src='https://i.imgur.com/4FfLIL4.jpg' title='Playlist Screenshot' width='' alt='Playlist Screenshot' />

## How It Works

The script stores information about users from the cache_files folder in user_info.txt as json. It will add new users and update existing ones before calling the API for every artist followed by the userbase as a whole. It collects each artist's music and determines which is new by comparing the release date with today's date. If new music is found, it is added to the respective user's playlist. If no playlist exists for a user, the script creates one on their account. Any new music is logged as a new dated file in the logs folder. Finally, email notifications are sent out to users who got new music and have an email paired with their username.

## How To Use

This script is built to be run for multiple users whose API access tokens are stored as cache files.
To run it for multiple users, or yourself:

1. Follow all the artists on Spotify you want to be notified about
2. Create a new app on the Spotify Developers Dashboard and give it a Redirect URI (I use "http://localhost:8080/")
	1. On the app's dashboard, you will find the Client ID and Secret to put in app_info.txt
3. Replace the lines of app_info.txt with your information
	1. For email functionality, create a new throwaway sender email address and put its log-in details, as well as your personal email, into app_info.txt
	2. Enable third-party app access on your throwaway sender email
4. Run pip install Spotipy on the computer running the python script
5. Create cache files for all the users you are running it for with generate_cache.py and put them in the cache_files folder
	1. This file creates a Spotipy cache file for the user currently signed into your computer's default browser and pairs it with the username input through console
	2. After entering a username, the file will open a link in-browser, wait several seconds then copy the URL in the address bar and paste it into the program as input
6. The notifier.py script assumes it will be run once a day after midnight, that's typically when most new music is released
	1. The script and all associated files can be put in a service that runs it every day, such as a scheduler
	2. I use pythonanywhere because it's easy to set up, just be sure to "pip install --user Spotipy" through the Bash console
