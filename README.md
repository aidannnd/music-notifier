Spotify New Music Notifier
==================

This Python script will alert the user about new music from artists they follow by calling the Spotify API using Spotipy. It collects the information, compares it against previously indexed artists, and notifies the user about new music.

## How To Use

1. Install Spotipy
2. Create a new app on the Spotify Developers Dashboard and give it a Redirect URI (I use "http://localhost/")
3. Create a new Gmail account for sending emails (enable third-party app access)
4. Replace the lines of app_info.txt with your information
	1. Your Spotify username will be a string of numbers if you signed up with Facebook, otherwise, it will be the username you use to log in
	2. The receiver address is likely to be your personal email address depending on where you want the emails about new music to be sent
5. The first time running the application you will need to log in through a browser and the program will perform an initial index of all your followed artists
	1. The program will open a link in-browser, wait several seconds then copy the url in the address bar and paste it into the program as input. This will generate a cache file for you.
6. The script will then need to be put in a service that runs it on an interval (every day, once a week, etc), such as a scheduler
	1. I use pythonanywhere.com because it's easy to set up, just be sure to pip install --user Spotipy through the Bash console

## How It Works

The script will call out to the API for each artist indexed in a file called data.txt as json. If it is the first time being run it will generate this file for use the next time the script is run. If there are any differences between what is indexed and what is received from the API, that indicates that there is new music. The script will collect this music and email the provided address a list of all the new music found.