import json
from flask import Flask, request, redirect, g, render_template, jsonify
import requests
from urllib.parse import quote

#from visualization import collect_user_listening_data, collect_user_top_tracks, recommend_countries
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import base64
from io import BytesIO
import os

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

# ================ SQL DB ================

import pandas as pd
import sqlite3

# allows computers of users of the website to access the top-songs csv file
# loading in csv file
global_data = None
def download_csv():
    global global_df
    # Load the CSV file into the DataFrame
    global_df = pd.read_csv('/Users/andrewhan/Desktop/2023-2024/Winter_24/PIC_Class/Project/TEST/country_charts.csv')

download_csv()

def get_global_data():
    global global_df
    # Check if global_df is not None
    if global_df is not None:
        # Convert the DataFrame to a dictionary
        df_dict = global_df.to_dict(orient='records')
        # Return the DataFrame as JSON
        return jsonify(df_dict)

def initialize_database():
    #read csv, CHANGE FILE PATH!!!
    if global_df is not None:
        df = global_df
        df = df [['country', 'song_title', 'artist_name', 'Pos']]
        df = df.rename(columns={'Pos': 'rank'})
        df['song_title'] = df['song_title'].str.strip()

    else:
        return 'global_df is not initialized'

    #Create SQLite DB & Table
    conn = sqlite3.connect('country_data.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS rank_data (
        country TEXT,
        song_name TEXT,
        artist_name TEXT,
        rank INTEGER
        )
    ''')
    conn.commit()

    #adding data from df into the sqlite table
    df.to_sql('rank_data', conn, if_exists='replace', index=False)
    conn.commit()
    conn.close()

# ================ Functions for gathering info from user ================

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

def collect_user_top_artists():
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=CLIENT_ID,
                                                    client_secret=CLIENT_SECRET,
                                                    redirect_uri=REDIRECT_URI,
                                                    scope='user-library-read,user-top-read'))

    # Fetch the user's top tracks
    top_artists = sp.current_user_top_artists(time_range = 'short_term', limit=15)

    # Return just the top artists
    return top_artists

# ================ Data Visualizations ================

IMAGE_DIR = 'static/images/'

user_listening_data = collect_user_listening_data()
user_top_songs = collect_user_top_tracks()

def top_songs_plot():
    plt.figure(figsize=(10, 12))
    sns.barplot(x=list(range(1, len(user_listening_data['top_tracks']) + 1)), y= user_top_songs)
    plt.title('Top Tracks')
    plt.xlabel('Rank')
    plt.ylabel('Track Name')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(os.path.join(IMAGE_DIR, 'top_songs_plot.png'))

def top_artists_plot():
    plt.figure(figsize=(10, 6))
    sns.barplot(x=list(range(1, len(user_listening_data['top_artists']) + 1)), y=user_listening_data['top_artists'])
    plt.title('Top Artists')
    plt.xlabel('Rank')
    plt.ylabel('Artist Name')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(os.path.join(IMAGE_DIR, 'top_artists_plot.png'))

def top_countries_plot():
    countries = country_scores  # Assuming this is a list of strings
    plt.figure(figsize=(8, 4))
    sns.barplot(x= list(country_scores.keys()), y=list(country_scores.values()))
    plt.title('Recommended Countries Based on Listening History')
    plt.xlabel('Country')
    plt.ylabel('Recommendation Strength')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(os.path.join(IMAGE_DIR, 'top_countries_plot.png'))

def generate_all_plots():
    if not os.path.exists(IMAGE_DIR):
        os.makedirs(IMAGE_DIR)

    top_songs_plot()
    top_artists_plot()
    top_countries_plot()
# ================ Country Recommendations ================

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

    max_score = max(country_counts.values())
    top_countries = sorted(country_counts.keys(), key=country_counts.get, reverse=True)[:3]
    
    country_scores = {}
    for country in top_countries:
        score = (country_counts[country] / 200) * (1 / max_score) * 100
        country_scores[country] = score
    
    return country_scores

country_scores = recommend_countries(user_top_songs)

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

    user_listening_data = collect_user_listening_data()
    user_top_songs = collect_user_top_tracks()
    country_scores = recommend_countries(user_top_songs)

    generate_all_plots()

    return render_template("index2.html")

@dash_app.callback(
    dash.dependencies.Output('top-artists-plot', 'figure'),
    dash.dependencies.Output('top-tracks-plot', 'figure'),
    dash.dependencies.Output('recommended-countries-plot', 'figure'),
    [dash.dependencies.Input('update-button', 'n_clicks')]
)

# @app.route('/top-artists-plot')
# def top_artists():
#     return render_template('index2.html', image_path='images/top_artists_plot.png')

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
    initialize_database()
    app.run(debug=True, port=PORT)
