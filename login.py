import dash
from dash.dependencies import Input, Output, State
from dash import dcc
from dash import html
from dash.exceptions import PreventUpdate

app = dash.Dash(__name__)

# CSS styles
external_stylesheets = ['https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

# Login page layout
login_layout = html.Div([
    html.Div([
        html.H2("Login", className="mb-4"),
        html.Div([
            html.Label("Username", className="font-weight-bold"),
            dcc.Input(id='username', type='text', placeholder='Enter your username', className="form-control"),
            html.Label("Password", className="font-weight-bold mt-3"),
            dcc.Input(id='password', type='password', placeholder='Enter your password', className="form-control"),
            html.Button('Login', id='login-button', n_clicks=0, className="btn btn-primary mt-3"),
            html.Div(id='login-status', className="mt-3")
        ])
    ], style={'width': '30%', 'margin': 'auto', 'marginTop': '50px'})
], className="container")

# Home page layout
home_layout = html.Div([
    html.H1("Welcome to the Home Page"),
    html.Button("Logout", id="logout-button", n_clicks=0, className="btn btn-danger mt-3")
], className="container mt-5")

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])

@app.callback(
    [Output('login-status', 'children'),
     Output('url', 'pathname')],
    [Input('login-button', 'n_clicks')],
    [State('username', 'value'), State('password', 'value')]
)
def authenticate(n_clicks, username, password):
    if n_clicks > 0:
        if username == 'admin' and password == 'password':
            return 'Login successful!', '/home'
        else:
            return 'Invalid username or password. Please try again.', '/'
    else:
        raise PreventUpdate

@app.callback(
    Output('page-content', 'children'),
    [Input('url', 'pathname')]
)
def display_page(pathname):
    if pathname == '/home':
        return home_layout
    else:
        return login_layout

if __name__ == '__main__':
    app.run_server(debug=True)