Spotify New Music Notifier
==================

Note: this project is still a work in progress

This Python script will alert the user about new music from artists they follow by calling the Spotify API using Spotipy. It collects the information, compares it against previously indexed artists, and notifies the user about new music with an email if they would like. The new music is also added to a playlist on the user's account.

## How To Use

1. Follow all the artists on Spotify you want to be notified about.
2. Create a new app on the Spotify Developers Dashboard and give it a Redirect URI (I use "http://localhost:8080/")
	1. On the app's dashboard, you will find the Client ID and Secret to put in app_info.txt
3. Replace the lines of app_info.txt with your information
	1. Your Spotify username will be a string of numbers if you signed up with Facebook, otherwise, it will be the username you use to log in
	2. The lines regarding email are optional (refer to step 8), if you would not like email notifications do not touch these
4. Install Spotipy
5. Run the script with Python once, it will have you log in through a browser and the program will perform an initial index of all your followed artists to data.txt
	1. The program will open a link in-browser, wait several seconds then copy the URL in the address bar and paste it into the program as input (this will generate a cache file for you)
7. The script and all associated files will then need to be put in a service that runs it on an interval (every day, once a week, etc), such as a scheduler
	1. I use pythonanywhere because it's easy to set up, just be sure to "pip install --user Spotipy" through the Bash console
8. If you would like email notifications, create a new throwaway Gmail account for sending emails (enable third-party app access), fill in app_info.txt
	1. The receiver address is likely to be your personal email address depending on where you want the emails about new music to be sent

## How It Works

The script will call out to the API for each artist indexed in a file called data.txt as JSON. If it is the first time being run it will generate this file for use the next time the script is run. If there are any differences between what is indexed and what is received from the API, that indicates that there is new music. The script will collect this music and add every song to a playlist called "New Music" on the user's account, if the playlist does not exist yet, it will be created and its id will be stored in app_info.txt. An email notification will also be sent to the user if it is set up.