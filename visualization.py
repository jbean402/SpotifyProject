import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import sqlite3
import csv
# Import your functions or ensure they are defined in this script
# from your_module import collect_user_listening_data, recommend_countries
import spotipy
from spotipy.oauth2 import SpotifyOAuth

# repositioning df columns for sqlite table
df = pd.read_csv('/Users/andrewhan/Desktop/2023-2024/Winter_24/PIC_Class/Project/TEST/country_charts.csv')
df = df [['country', 'song_title', 'artist_name', 'Pos']]
df = df.rename(columns={'Pos': 'rank'})
df['song_title'] = df['song_title'].str.strip()
df.head()


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


def print_top_songs():
    conn = sqlite3.connect('country_data.db')
    c = conn.cursor()

    # Query the database to retrieve all distinct country names
    c.execute("SELECT DISTINCT song_title FROM rank_data")
    songs = c.fetchall()

    # Print the list of countries
    for song in songs:
        print(song)

    # Close connection
    conn.close()


def print_countries():
    conn = sqlite3.connect('country_data.db')
    c = conn.cursor()

    # Query the database to retrieve all distinct country names
    c.execute("SELECT DISTINCT country FROM rank_data")
    countries = c.fetchall()

    # Print the list of countries
    for country in countries:
        print(country)

    # Close connection
    conn.close()

# print_top_songs()


your_client_id = '5073d5f2f848429a97f7e5fff17bd1aa'
your_client_secret = 'f0e698a562f447f8ba6baf0eabac0abf'
your_redirect_uri = 'http://127.0.0.1:5000'

def collect_user_listening_data():
    # Initialize Spotipy with your client ID, client secret, and redirect URI
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=your_client_id,
                                                    client_secret=your_client_secret,
                                                    redirect_uri=your_redirect_uri,
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
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=your_client_id,
                                                    client_secret=your_client_secret,
                                                    redirect_uri=your_redirect_uri,
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


    # total_country_occurrences = sum(country_counts.values())

    top_countries = sorted(country_counts.keys(), key=country_counts.get, reverse=True)[:3]
    
    country_scores = {country: (country_counts[country] / 200) * (1 / max(country_scores.values()))* 100 for country in country_counts.keys()}
    
    # top_country_scores = {country: country_scores[country] for country in top_countries}

    return country_scores

# Ensure you have your Spotify API credentials set
user_listening_data = collect_user_listening_data()
user_top_songs = collect_user_top_tracks()

country_scores = recommend_countries(user_top_songs)

# print_top_songs()

# print (f'User listening data: {user_listening_data}')
# print (f'User top songs: {user_top_songs}')

print (f'User country scores: {country_scores}')


# Visualization 1: User's Top Artists
plt.figure(figsize=(10, 6))
sns.barplot(x=list(range(1, len(user_listening_data['top_artists']) + 1)), y=user_listening_data['top_artists'])
plt.title('Top Artists')
plt.xlabel('Rank')
plt.ylabel('Artist Name')
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()

# Visualization 2: User's Top Tracks
plt.figure(figsize=(10, 6))
sns.barplot(x=list(range(1, len(user_listening_data['top_tracks']) + 1)), y= user_top_songs)
plt.title('Top Tracks')
plt.xlabel('Rank')
plt.ylabel('Track Name')
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()

# Visualization 3: Recommended Countries
# Assuming recommended_countries is a list of country names
countries = country_scores  # Assuming this is a list of strings
plt.figure(figsize=(8, 4))
sns.barplot(x= list(country_scores.keys()), y=list(country_scores.values()))
plt.title('Recommended Countries Based on Listening History')
plt.xlabel('Country')
plt.ylabel('Recommendation Strength')
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()
