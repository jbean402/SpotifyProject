import pandas as pd
import numpy as np

import seaborn as sns
import sqlite3
import csv

# data visualization 
import plotly.express as px 

# Import your functions or ensure they are defined in this script
# from your_module import collect_user_listening_data, recommend_countries
import spotipy
from spotipy.oauth2 import SpotifyOAuth

import dash
from dash import dcc, html
import dash_ag_grid as dag
from dash.dependencies import Input, Output

# from visualization 
from visualization import plot_top_songs, plot_top_artists, plot_recommended_countries

# ==== SQL DATABASE HANDLER ====

# importing df
df_initial = pd.read_csv('country_charts.csv')

# repositioning df columns for sqlite table
def prepare_df(df):
    df = df [['country', 'song_title', 'artist_name', 'Pos']]
    df = df.rename(columns={'Pos': 'rank'})
    df['song_title'] = df['song_title'].str.strip()
    return df

df = prepare_df(df_initial)

# ==== SQL DATABASE ====
class DatabaseHandler:
    @staticmethod
    def create_database():
        conn = sqlite3.connect('country_data.db') #creates and connects to country_data.db database
        conn.close()
    
    @staticmethod
    def create_table():
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
        conn.close()

# MULTI INDEX SQL
    @staticmethod
    def insert_data():
        conn = sqlite3.connect('country_data.db')
        c = conn.cursor()
        df.to_sql('rank_data', conn, if_exists='replace', index=False)


        conn.commit()
        conn.close()
        
DatabaseHandler.create_table()
DatabaseHandler.insert_data()

# ==== DATA ====

# ==== FUNCTIONS THAT QUERY SQL DATABASE ==== 
def get_top_songs():
    conn = sqlite3.connect('country_data.db')
    c = conn.cursor()

    # Query the database to retrieve all distinct country names
    c.execute("""
        WITH ranked_songs AS (
            SELECT 
                "Pos",
                "artist_name",
                "song_title",
                "country",
                ROW_NUMBER() OVER (PARTITION BY "country" ORDER BY "Pos") as row_num
            FROM 
                country_data
        )
        SELECT 
            "Pos",
            "artist_name",
            "song_title",
            "country"
        FROM 
            ranked_songs
        WHERE 
            row_num <= 50
    """)
    
    top_songs = c.fetchall()

    # close connection
    conn.close()

    # Converting to dataframe
    top_songs_df = pd.DataFrame(top_songs, columns=['Pos', 'artist_name', 'song_title', 'country'])
    return top_songs_df

    pass 

def get_countries():
    conn = sqlite3.connect('country_data.db')
    c = conn.cursor()

    # Query the database to retrieve all distinct country names
    c.execute("SELECT DISTINCT country FROM rank_data")
    countries = c.fetchall()

    # close connection
    conn.close()

    # converting to dataframe 
    country_name_df = pd.DataFrame(countries, columns=['country'])
    
    return country_name_df


# ==== FUNCTIONS THAT RETRIEVE DATA FROM SPOTIFY VIA SPOTIPY ====
def collect_user_top_artists():
    # Initialize Spotipy with your client ID, client secret, and redirect URI
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id='4db82491748043009a9d79b9a2d6739d',
                                                    client_secret='6a07b26c450d44b286d46261f2322a17',
                                                    redirect_uri='http://127.0.0.1:5000/redirect',
                                                    scope='user-library-read,user-top-read'))

    # Fetch the user's top artists (short_term = collecting within the past 4 weeks)
    top_artists = sp.current_user_top_artists(limit=15)

    # Process the fetched data as needed
    user_top_artists = [artist['name'] for artist in top_artists['items']]

    return user_top_artists

def collect_user_top_tracks():
    # Initialize Spotipy with your client ID, client secret, and redirect URI
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id='4db82491748043009a9d79b9a2d6739d',
                                                    client_secret='6a07b26c450d44b286d46261f2322a17',
                                                    redirect_uri='http://127.0.0.1:5000/redirect',
                                                    scope='user-library-read,user-top-read'))

    # Fetch the user's top tracks (short_term = collecting within the past 4 weeks)
    top_tracks = sp.current_user_top_tracks(limit=50, time_range="short_term") 

    # Extract just the top track names
    user_top_tracks = [track['name'] for track in top_tracks['items']]

    return user_top_tracks

# ==== RECOMMENDING COUNTRIES ====
def recommend_countries(user_top_tracks):
    conn = sqlite3.connect('country_data.db')
    c = conn.cursor()

    common_songs_per_country = {}

    # counting total no of songs listened to by user 
    total_user_songs = len(user_top_tracks)

    for song in user_top_tracks:
        # Query the database to retrieve associated countries
        c.execute("SELECT DISTINCT country FROM rank_data WHERE song_title = ?", (song,))
        countries = c.fetchall()
        
        # Increment counts for each country
        for country in countries:
            country_name = country[0]
            common_songs_per_country[country_name] = common_songs_per_country.get(country_name, 0) + 1

    # calculating the score for each country 
    country_scores = {}
    for country, common_songs_count in common_songs_per_country.items():
        score = (common_songs_count / total_user_songs) * 100
        country_scores[country] = score

    # Sorting the dictionary by values in descending order
    sorted_country_scores = {k: v for k, v in sorted(country_scores.items(), key=lambda item: item[1], reverse=True)}

    return sorted_country_scores

# ==== PLOTLY APP ====

# Define the Plotly Dash app
app = dash.Dash(__name__)


# Define the layout of the app
app.layout = html.Div(
    style={'display': 'flex', 'justifyContent': 'center', 'alignItems': 'center', 'flexDirection': 'column', 'backgroundColor': '#1db954'},
    children=[
    html.H1(children='User Vs. The World', style={'textAlign':'center', 'fontSize':50, 'fontFamily': 'Gill Sans', 'color': 'White', 'marginBottom': '10px', 'fontWeight': 'medium'}),
    html.P("What country do your music tastes align with?", style={'fontFamily': 'Gill Sans', 'fontSize': 20, 'color':'191414', 'marginTop':'10px'}),
    dcc.Dropdown(
        id='data-type-dropdown',
        options=[
            {'label': 'Top Songs', 'value': 'top_songs'},
            {'label': 'Top Artists', 'value': 'top_artists'},
            {'label': 'Similar Countries', 'value': 'recommended_countries'},
        ],
        value='top_songs',  # Default value
        clearable=False,
        style={'width': '300px','margin': 'auto', 'fontSize': '20px', 'fontFamily': 'Gill Sans'},
    ),
    dcc.Graph(id='data-plot', style={'margin': 'center', 'marginTop': '20px'})
    ]
)

# Define a callback to update the plot based on the dropdown selection
@app.callback(
    Output('data-plot', 'figure'),
    [Input('data-type-dropdown', 'value')]
)

def update_data_plot(data_type):
    if data_type == 'top_songs':
        # Call function to collect user's top songs
        user_top_songs = collect_user_top_tracks()  # Assuming you have a function like this
        
        # Call function to plot top songs
        return plot_top_songs(user_top_songs)
    
    elif data_type == 'top_artists':
        # Call function to collect user's top artists
        user_top_artists = collect_user_top_artists()  # Assuming you have a function like this
        
        # Call function to plot top artists
        return plot_top_artists(user_top_artists)
    
    elif data_type == 'recommended_countries':
        user_top_songs = collect_user_top_tracks()
        recommended = recommend_countries(user_top_songs)

        return plot_recommended_countries(recommended)

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)
