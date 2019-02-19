#!/usr/bin/env python
from spotipy.oauth2 import SpotifyClientCredentials
import spotipy

def connect(cid = '',
            secret = ''):
    client_credentials_manager = SpotifyClientCredentials(client_id=cid, client_secret=secret)
    global sp
    sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

def get_playlist_tracks(user, playlist):
    track_dispenser = sp.user_playlist_tracks(user, playlist)
    tracks = []
    while track_dispenser['next']:
        tracks.extend(track_dispenser['items'])
    return tracks
    
def get_features(tid):
    ##Binary features (value represents confidence. these tend to be bimodal.)
    # acousticness
    # instrumentalness (> 0.5 probably no vocals)
    # liveness (>0.8 very likely live)
    #
    ##Continuous features (0 low to 1 high scale)
    # danceability
    # energy
    # speechiness (spoken word, not vocals)
    # valence (0 is sad/negative, 1 is happy/positive)
    #
    ##Discrete features
    # key
    # mode (1 = major, 0 = minor)
    #
    ##Other
    # loudness (dB) from -60 to 0
    # tempo (BPM)
    # time_signature
    # duration
    
    features = sp.audio_features(tid)
    features = features[0] # when are there multiple?
    return features

def print_track(tid, title=True, album=False, artists=True):
    track = sp.track(tid)
    fields = []
    if title:
        fields.append(track['name'])
    if album:
        fields.append(track['album'])
    if artists:
        fields.append( ', '.join([artist['name'] for artist in track['artists']]) )
    print(' - '.join(fields))
    