import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
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
from dash.dependencies import Input, Output

# ===== Visualization 1: User's Top Tracks ===== (works)
def plot_top_songs(user_top_songs): 
    """
    This plot shows the top 50 songs for the user
    """

    # putting the list of songs into another variable  
    songs = user_top_songs

    # creating a dataframe 
    top_songs_data = pd.DataFrame()

    # processing and concatenating to clean up the dataframe 
    top_songs_data['Songs'] = songs

    # Adding position values to prepare for the grapg 
    top_songs_data['Position'] = top_songs_data.index + 1

    # creating the plot 
    top_songs_data = top_songs_data[::-1]
    fig = px.bar(top_songs_data, x = 'Position', y = 'Songs', orientation='h', width=1500, height=1000)
    fig.update_layout(
        margin=dict(l=50, r=50, t=50, b=50),  # Adjust margins as needed
    )

    return fig

# ===== Visualization 2: User's Top Artists ====== (works)
def plot_top_artists(user_top_artists):
    """
    This plot shows the top 15 artists for the user
    """

    # putting the list of songs into another variable  
    artists = user_top_artists

    # creating a dataframe 
    top_artists_data = pd.DataFrame()

    # processing and concatenating to clean up the dataframe 
    top_artists_data['Artists'] = artists

    # Adding position values to prepare for the grapg 
    top_artists_data['Position'] = top_artists_data.index + 1

    # creating the plot 
    # top_artists_data = top_artists_data[::-1]
    fig = px.bar(top_artists_data, x = 'Position', y = 'Artists', orientation='h', width=1500, height=700, color='Artists')
    fig.update_layout(
        margin=dict(l=15, r=15, t=15, b=15),

    )
    
    return fig

# ===== Visualization 3: Recommended Countries Plot ====== (works)
def plot_recommended_countries(country_scores): 
    # first processing into a dataframe for the plot 
    # creating new columns, preparing for df 
    column_names = ['Country', 'Common_Songs']
    
    # creating a new dataframe 
    recommend_data = pd.DataFrame(list(country_scores.items()), columns=column_names)


    #feeding into new dataframe
    # assuming that country_scores is a list of country names 
    # countries = country_scores 
    fig = px.scatter(recommend_data, x="Country", y="Common_Songs")
    fig.show()

    return fig 