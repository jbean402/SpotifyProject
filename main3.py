import json
from flask import Flask, request, redirect, g, render_template, jsonify
import requests
from urllib.parse import quote

from visualization import collect_user_listening_data, collect_user_top_tracks, recommend_countries

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import base64
from io import BytesIO

import sqlite3
import spotipy
from spotipy.oauth2 import SpotifyOAuth

# Authentication Steps, paramaters, and responses are defined at https://developer.spotify.com/web-api/authorization-guide/
# Visit this url to see all the steps, parameters, and expected response.

app = Flask(__name__)

#  Client Keys
CLIENT_ID = "bd21c17ff2cc461e81564cc64daa133a"
CLIENT_SECRET = "363723b2c2724b17b9d5f78b25ea0634"

# Spotify URLS
SPOTIFY_AUTH_URL = "https://accounts.spotify.com/authorize"
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_API_BASE_URL = "https://api.spotify.com"
API_VERSION = "v1"
SPOTIFY_API_URL = "{}/{}".format(SPOTIFY_API_BASE_URL, API_VERSION)

# Server-side Parameters
CLIENT_SIDE_URL = "http://127.0.0.1"
PORT = 8080
REDIRECT_URI = "{}:{}/callback/q".format(CLIENT_SIDE_URL, PORT)
SCOPE = "playlist-modify-public playlist-modify-private"
STATE = ""
SHOW_DIALOG_bool = True
SHOW_DIALOG_str = str(SHOW_DIALOG_bool).lower()

auth_query_parameters = {
    "response_type": "code",
    "redirect_uri": REDIRECT_URI,
    "scope": SCOPE,
    # "state": STATE,
    # "show_dialog": SHOW_DIALOG_str,
    "client_id": CLIENT_ID
}

'''
@app.route("/")
def login():
    return render_template("login.html")

@app.route("/login", methods=["GET", "POST"])
def authorize_spotify():
    if request.method == "POST":
        url_args = "&".join(["{}={}".format(key, quote(val)) for key, val in auth_query_parameters.items()])
        auth_url = "{}?{}".format(SPOTIFY_AUTH_URL, url_args)
        return redirect(auth_url)
    else:
        # Handle GET request (if needed)
        return render_template("login.html")

'''

@app.route("/")
def index():
    # Auth Step 1: Authorization
    url_args = "&".join(["{}={}".format(key, quote(val)) for key, val in auth_query_parameters.items()])
    auth_url = "{}/?{}".format(SPOTIFY_AUTH_URL, url_args)
    return redirect(auth_url)

    
@app.route("/callback/q")
def callback():
    # Auth Step 4: Requests refresh and access tokens
    auth_token = request.args['code']
    code_payload = {
        "grant_type": "authorization_code",
        "code": str(auth_token),
        "redirect_uri": REDIRECT_URI,
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
    }
    post_request = requests.post(SPOTIFY_TOKEN_URL, data=code_payload)

    # Auth Step 5: Tokens are Returned to Application
    response_data = json.loads(post_request.text)
    access_token = response_data["access_token"]
    refresh_token = response_data["refresh_token"]
    token_type = response_data["token_type"]
    expires_in = response_data["expires_in"]

    # Auth Step 6: Use the access token to access Spotify API
    authorization_header = {"Authorization": "Bearer {}".format(access_token)}
    return render_template("index2.html")

@app.route('/get_user_data')
def get_user_data():
    user_data = collect_user_listening_data()
    return jsonify(user_data)

@app.route('/recommend_countries')
def recommend():
    user_top_songs = collect_user_top_tracks()
    country_scores = recommend_countries(user_top_songs)
    return jsonify(country_scores)

if __name__ == "__main__":
    app.run(debug=True, port=PORT)