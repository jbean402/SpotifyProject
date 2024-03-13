from flask import Flask, redirect, request
import os
import uuid
import urllib.parse
import requests
import base64

app = Flask(__name__)

CLIENT_ID = 'bd21c17ff2cc461e81564cc64daa133a'
CLIENT_SECRET = '64539af59cc04fd28da590a2a30f43bf'
REDIRECT_URI = 'http://127.0.0.1:5000'

@app.route('/login')
def login():
    authentication_request_params = {
        'response_type': 'code',
        'client_id': CLIENT_ID,
        'redirect_uri': REDIRECT_URI,
        'scope': 'user-read-email user-read-private user-top-read',
        'state': str(uuid.uuid4()),
        'show_dialog': 'true'
    }
    auth_url = 'https://accounts.spotify.com/authorize/?' + urllib.parse.urlencode(authentication_request_params)
    return redirect(auth_url)

def get_access_token(authorization_code: str):
    spotify_request_access_token_url = 'https://accounts.spotify.com/api/token'
    client_id = CLIENT_ID
    client_secret = CLIENT_SECRET
    redirect_uri = REDIRECT_URI

    # Encode Client ID and Client Secret
    client_creds = f"{client_id}:{client_secret}"
    client_creds_b64 = base64.b64encode(client_creds.encode())

    headers = {
        'Authorization': f'Basic {client_creds_b64.decode()}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    body = {
        'grant_type': 'authorization_code',
        'code': authorization_code,
        'redirect_uri': redirect_uri
    }

    response = requests.post(spotify_request_access_token_url, data=body, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception('Failed to obtain access token')

@app.route('/callback')
def callback():
    code = request.args.get('code')
    credentials = get_access_token(authorization_code=code)
    # It's not secure or recommended to store sensitive information like tokens in environment variables for production apps.
    # Consider using Flask sessions or another secure method for managing user sessions and tokens.
    os.environ['token'] = credentials['access_token']
    return redirect('/your-music')

@app.route('/your-music')
def your_music():
    user_profile_url = 'https://api.spotify.com/v1/me'
    user_top_items_url = 'https://api.spotify.com/v1/me/top/'
    limit = 18
    
    # Add the access token to the request header
    headers = {
        'Authorization': f'Bearer {os.getenv("token")}'
    }
    
    # Retrieving User details via GET request to user profile endpoint
    user_profile = requests.get(user_profile_url, headers=headers)
    if user_profile.status_code == 200:
        user_profile = user_profile.json()
        display_name = user_profile.get('display_name', 'Unknown')

    # Retrieving top Artists details via GET request to top artists endpoint
    top_artists_url = f"{user_top_items_url}artists?limit={limit}"
    artists = requests.get(top_artists_url, headers=headers)
    if artists.status_code == 200:
        artists = artists.json().get('items', [])

    # Retrieving top Tracks details via GET request to top tracks endpoint
    top_tracks_url = f"{user_top_items_url}tracks?limit={limit}"
    tracks = requests.get(top_tracks_url, headers=headers)
    if tracks.status_code == 200:
        tracks = tracks.json().get('items', [])

    return f"Hello {display_name}, here are your top artists: {artists} and top tracks: {tracks}"

if __name__ == "__main__":
    app.run(debug=True)
