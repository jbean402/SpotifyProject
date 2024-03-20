import json
from flask import Flask, request, redirect, g, render_template
import requests
from urllib.parse import quote

#from visualization import collect_user_listening_data, collect_user_top_tracks, recommend_countries

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import base64
from io import BytesIO

import sqlite3
import spotipy
from spotipy.oauth2 import SpotifyOAuth

import dash
from dash import dcc, html
import plotly.graph_objs as go


# Authentication Steps, paramaters, and responses are defined at https://developer.spotify.com/web-api/authorization-guide/
# Visit this url to see all the steps, parameters, and expected response.

app = Flask(__name__)
dash_app = dash.Dash(__name__, server=app, url_base_pathname='/dash/')

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
def collect_user_listening_data():
    # Initialize Spotipy with your client ID, client secret, and redirect URI
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=CLIENT_ID,
                                                    client_secret=CLIENT_SECRET,
                                                    redirect_uri=REDIRECT_URI,
                                                    scope='user-library-read,user-top-read'))

    # Fetch the user's top artists and tracks
    top_artists = sp.current_user_top_artists(limit=15)
    top_tracks = sp.current_user_top_tracks(limit=50)

    # Process the fetched data as needed
    user_listening_data = {
        'top_artists': [artist['name'] for artist in top_artists['items']],
        'top_tracks': [track['name'] for track in top_tracks['items']]
    }

    return user_listening_data

def collect_user_top_tracks():
    # Initialize Spotipy with your client ID, client secret, and redirect URI
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=CLIENT_ID,
                                                    client_secret=CLIENT_SECRET,
                                                    redirect_uri=REDIRECT_URI,
                                                    scope='user-library-read,user-top-read'))

    # Fetch the user's top tracks
    top_tracks = sp.current_user_top_tracks(time_range = 'short_term', limit=50)

    # Extract just the top track names
    top_track_names = [track['name'] for track in top_tracks['items']]

    return top_track_names

def recommend_countries(user_top_songs):
    conn = sqlite3.connect('country_data.db')
    c = conn.cursor()

    country_counts = {}

    for song in user_top_songs:
        # Query the database to retrieve associated countries
        c.execute("SELECT DISTINCT country FROM rank_data WHERE song_title = ?", (song,))
        countries = c.fetchall()
        
        # Increment counts for each country
        for country in countries:
            country_name = country[0]
            country_counts[country_name] = country_counts.get(country_name, 0) + 1
    
    # Recommend the country with the highest count
    top_countries = sorted(country_counts.keys(), key=country_counts.get, reverse=True)[:3]

    total_top_country_occurrences = sum(country_counts[country] for country in top_countries)
    
    # Calculate the country score as a percentage of how much the user's top songs match the top countries
    country_scores = {country: (country_counts[country] / total_top_country_occurrences) * 100 for country in top_countries}
    
    return country_scores


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
    return render_template("index.html")

@dash_app.callback(
    dash.dependencies.Output('top-artists-plot', 'figure'),
    dash.dependencies.Output('top-tracks-plot', 'figure'),
    dash.dependencies.Output('recommended-countries-plot', 'figure'),
    [dash.dependencies.Input('update-button', 'n_clicks')]
)
def update_plots(n_clicks):
    # Collect updated data
    user_listening_data = collect_user_listening_data()
    user_top_songs = collect_user_top_tracks()
    country_scores = recommend_countries(user_top_songs)
    
    # Update the plots
    top_artists_fig = go.Figure()
    top_artists_fig.add_trace(go.Bar(
        x=list(range(1, len(user_listening_data['top_artists']) + 1)),
        y=user_listening_data['top_artists'],
        marker_color='rgb(55, 83, 109)'
    ))
    top_artists_fig.update_layout(
        title='Top Artists',
        xaxis=dict(title='Rank'),
        yaxis=dict(title='Artist Name'),
        xaxis_tickangle=-45,
        margin=dict(l=40, r=40, t=40, b=40)
    )

    top_tracks_fig = go.Figure()
    top_tracks_fig.add_trace(go.Bar(
        x=list(range(1, len(user_listening_data['top_tracks']) + 1)),
        y=user_top_songs,
        marker_color='rgb(55, 83, 109)'
    ))
    top_tracks_fig.update_layout(
        title='Top Tracks',
        xaxis=dict(title='Rank'),
        yaxis=dict(title='Track Name'),
        xaxis_tickangle=-45,
        margin=dict(l=40, r=40, t=40, b=40)
    )

    recommended_countries_fig = go.Figure()
    recommended_countries_fig.add_trace(go.Bar(
        x=list(country_scores.keys()),
        y=list(country_scores.values()),
        marker_color='rgb(55, 83, 109)'
    ))
    recommended_countries_fig.update_layout(
        title='Recommended Countries Based on Listening History',
        xaxis=dict(title='Country'),
        yaxis=dict(title='Recommendation Strength'),
        xaxis_tickangle=-45,
        margin=dict(l=40, r=40, t=40, b=40)
    )

    return top_artists_fig, top_tracks_fig, recommended_countries_fig

dash_app.layout = html.Div([
    html.H1('Dash Plots'),
    
    html.Div(id='top-artists-plot'),
    html.Div(id='top-tracks-plot'),
    html.Div(id='recommended-countries-plot')
])

if __name__ == "__main__":
    app.run(debug=True, port=PORT)


'''
user_listening_data = collect_user_listening_data()
user_top_songs = collect_user_top_tracks()
# Recommend countries based on user top songs
country_scores = recommend_countries(user_top_songs)

# Visualization 1: User's Top Artists
top_artists_fig = go.Figure()
top_artists_fig.add_trace(go.Bar(
    x=list(range(1, len(user_listening_data['top_artists']) + 1)),
    y=user_listening_data['top_artists'],
    marker_color='rgb(55, 83, 109)'
))
top_artists_fig.update_layout(
    title='Top Artists',
    xaxis=dict(title='Rank'),
    yaxis=dict(title='Artist Name'),
    xaxis_tickangle=-45,
    margin=dict(l=40, r=40, t=40, b=40)
)

# Visualization 2: User's Top Tracks
top_tracks_fig = go.Figure()
top_tracks_fig.add_trace(go.Bar(
    x=list(range(1, len(user_listening_data['top_tracks']) + 1)),
    y=user_top_songs,
    marker_color='rgb(55, 83, 109)'
))
top_tracks_fig.update_layout(
    title='Top Tracks',
    xaxis=dict(title='Rank'),
    yaxis=dict(title='Track Name'),
    xaxis_tickangle=-45,
    margin=dict(l=40, r=40, t=40, b=40)
)

# Visualization 3: Recommended Countries
recommended_countries_fig = go.Figure()
recommended_countries_fig.add_trace(go.Bar(
    x=list(country_scores.keys()),
    y=list(country_scores.values()),
    marker_color='rgb(55, 83, 109)'
))
recommended_countries_fig.update_layout(
    title='Recommended Countries Based on Listening History',
    xaxis=dict(title='Country'),
    yaxis=dict(title='Recommendation Strength'),
    xaxis_tickangle=-45,
    margin=dict(l=40, r=40, t=40, b=40)
)


app.layout = html.Div([
    html.H1('Dash Plots'),
    
    html.Div([
        dcc.Graph(figure=top_artists_fig),
        dcc.Graph(figure=top_tracks_fig),
        dcc.Graph(figure=recommended_countries_fig)
    ])
])


if __name__ == "__main__":
    app.run(debug=True, port=PORT)
    
'''