Spotify New Music Notifier
==================

This Python application will alert the user about new music from artists they follow by calling the Spotify API using Spotipy. It collects the information, compares it against previously indexed artists, and notifies the user about new music.

## How To Use

1. Install Spotipy
2. Create a new app on the Spotify Developers Dashboard and give it a Redirect URI
3. Create a new gmail account for sending emails (enable third party app access)
4. Replace the lines of app_info.txt with your information
	1. Your Spotify username will be a string of numbers if you signed up with Facebook, otherwise it will be the username you use to log in
	2. The receiver address is likely to be your personal email address depending on where you want the emails about new music to be sent
5. The first time running the application you will need to log in through a browser and the program will perform an initial index of all your followed artists
6. The script will then need to be put in a service that runs it on an interval (every day, once a week, etc), such as a scheduler
	1. I use pythonanywhere