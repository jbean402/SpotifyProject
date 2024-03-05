import dash
from dash.dependencies import Input, Output, State
from dash import dcc
from dash import html
from dash.exceptions import PreventUpdate
import spotipy
from spotipy.oauth2 import SpotifyOAuth

# Spotify credentials
CLIENT_ID = 'your_client_id'
CLIENT_SECRET = 'your_client_secret'
REDIRECT_URI = 'http://localhost:8050/callback'  # Redirect URI of Dash app

# Scopes for Spotify API access
SCOPE = 'user-read-email'

# Dash app initialization
app = dash.Dash(__name__)

# CSS styles
external_stylesheets = ['https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

# Spotify authentication
sp_oauth = SpotifyOAuth(client_id=CLIENT_ID, client_secret=CLIENT_SECRET, redirect_uri=REDIRECT_URI, scope=SCOPE)

# Login page layout
login_layout = html.Div([
    html.Div([
        html.H2("Spotify Login", className="mb-4"),
        html.Button('Login with Spotify', id='login-button', n_clicks=0, className="btn btn-primary mt-3"),
        html.Div(id='login-status', className="mt-3")
    ], style={'width': '30%', 'margin': 'auto', 'marginTop': '50px'})
], className="container")

# Home page layout
home_layout = html.Div([
    html.H1("Welcome to the Home Page"),
    html.Button("Logout", id="logout-button", n_clicks=0, className="btn btn-danger mt-3")
], className="container mt-5")

# App layout
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])

# Spotify login callback
@app.callback(
    [Output('login-status', 'children'),
     Output('url', 'pathname')],
    [Input('login-button', 'n_clicks')]
)
def spotify_login(n_clicks):
    if n_clicks > 0:
        auth_url = sp_oauth.get_authorize_url()
        return dcc.Location(href=auth_url, id='redirect'), '/'
    else:
        raise PreventUpdate

# Callback to handle Spotify authentication redirect
@app.callback(
    Output('page-content', 'children'),
    [Input('url', 'href')]
)
def handle_redirect(url):
    code = sp_oauth.parse_response_code(url)
    if code:
        token_info = sp_oauth.get_cached_token()
        if token_info is not None:
            access_token = token_info['access_token']
            # Authentication successful, redirect to home page
            return home_layout
        else:
            return "Failed to authenticate with Spotify."
    else:
        raise PreventUpdate

if __name__ == '__main__':
    app.run_server(debug=True)
