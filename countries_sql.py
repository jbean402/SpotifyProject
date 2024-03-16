import sqlite3
import pandas as pd
import numpy as np

df = pd.read_csv('/Users/andrewhan/Desktop/2023-2024/Winter_24/PIC_Class/Project/country_charts.csv')
df.head()

conn = sqlite3.connect('country_data.db')

df.to_sql('country_data', conn, if_exists='replace', index=False)

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
            CREATE TABLE IF NOT EXISTS countries (
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
        DatabaseHandler.create_database()
        DatabaseHandler.create_table()
        conn = sqlite3.connect('country_data.db')
        c = conn.cursor()
        c.execute('''
            INSERT INTO countries (country, song_name, artist_name, rank)
            SELECT country, song_name, artist_name, rank
            FROM countries
            WHERE (country, rank) IN (
            SELECT country, MAX(rank)
            FROM countries
            GROUP BY country
            )
        ''')
        conn.commit()
        
        #fetch data from the countries table
        c.execute('''
            SELECT c.country, c.song_name, c.artist_name, c.rank
            FROM countries c
            JOIN countries yt ON c.country = yt.country AND c.song_name = yt.song_name AND c.artist_name = yt.artist_name
            ORDER BY c.country
        ''')

        conn.commit()
        conn.close()

DatabaseHandler.insert_data()

import spotipy
from spotipy.oauth2 import SpotifyOAuth

def collect_user_listening_data():
    # Initialize Spotipy with your client ID, client secret, and redirect URI
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id='your_client_id',
                                                   client_secret='your_client_secret',
                                                   redirect_uri='your_redirect_uri',
                                                   scope='user-library-read,user-top-read'))

    # Fetch the user's top artists and tracks
    top_artists = sp.current_user_top_artists(limit=15)
    top_tracks = sp.current_user_top_tracks(limit=200)

    # Process the fetched data as needed
    user_listening_data = {
        'top_artists': [artist['name'] for artist in top_artists['items']],
        'top_tracks': [track['name'] for track in top_tracks['items']]
    }
    return user_listening_data

def recommend_countries(user_top_songs):
    conn = sqlite3.connect('country_data.db')
    c = conn.cursor()

    country_counts = {}

    for song in user_top_songs:
        # Query the database to retrieve associated countries
        c.execute("SELECT DISTINCT country FROM countries WHERE song_name = ?", (song,))
        countries = c.fetchall()
        
        # Increment counts for each country
        for country in countries:
            country_name = country[0]
            country_counts[country_name] = country_counts.get(country_name, 0) + 1
    
    # Close connection
    conn.close()
    
    # Recommend the country with the highest count
    top_countries = sorted(country_counts, key=country_counts.get, reverse=True)[:3]

    total_top_country_occurrences = sum(country_counts[country] for country in top_countries)
    
    # Calculate the country score as a percentage of how much the user's top songs match the top countries
    country_scores = {country: (country_counts[country] / total_top_country_occurrences) * 100 for country in top_countries}
    
    return top_countries, country_scores
