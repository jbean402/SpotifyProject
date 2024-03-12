import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
# Import your functions or ensure they are defined in this script
# from your_module import collect_user_listening_data, recommend_countries
import spotipy
from spotipy.oauth2 import SpotifyOAuth

your_client_id = 'bd21c17ff2cc461e81564cc64daa133a'
your_client_secret = '64539af59cc04fd28da590a2a30f43bf'
your_redirect_uri = 'http://127.0.0.1:5000'

def collect_user_listening_data():
    # Initialize Spotipy with your client ID, client secret, and redirect URI
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=your_client_id,
                                                   client_secret=your_client_secret,
                                                   redirect_uri=your_redirect_uri,
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

def recommend_countries(user_listening_data, top_n=3):
    # Load the dataset of top songs in different countries
    top_songs_data = pd.read_csv('top_songs_by_country.csv')  # Example: Replace with your dataset
    
    # Calculate similarity score for each country
    similarity_scores = {}
    for country in top_songs_data['Country']:
        country_top_songs = top_songs_data[top_songs_data['Country'] == country]['SongTitle']
        common_songs = set(user_listening_data['top_tracks']).intersection(country_top_songs)
        similarity_scores[country] = len(common_songs)
    
    # Sort countries based on similarity scores
    sorted_countries = sorted(similarity_scores.items(), key=lambda x: x[1], reverse=True)
    
    # Extract top N countries
    top_countries = [country for country, score in sorted_countries[:top_n]]
    
    return top_countries


# Ensure you have your Spotify API credentials set
user_listening_data = collect_user_listening_data()
recommended_countries = recommend_countries(user_listening_data)

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
sns.barplot(x=list(range(1, len(user_listening_data['top_tracks']) + 1)), y=user_listening_data['top_tracks'])
plt.title('Top Tracks')
plt.xlabel('Rank')
plt.ylabel('Track Name')
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()

# Visualization 3: Recommended Countries
# Assuming recommended_countries is a list of country names
countries = recommended_countries  # Assuming this is a list of strings
values = [1 for _ in countries]  # Just a dummy list to create a bar chart

plt.figure(figsize=(8, 4))
sns.barplot(x=countries, y=values)
plt.title('Recommended Countries Based on Listening History')
plt.xlabel('Country')
plt.ylabel('Recommendation Strength')
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()