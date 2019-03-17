#!/usr/bin/env python
import pandas as pd
from flask import g

def user_info_block(user_dict):
    name = user_dict['display_name']
    photo = user_dict['images'][0]['url']
    img_tag = '<img src="{}" alt="{}" height="50" width="50">'
    return '{} {}'.format(img_tag.format(photo, name), name)

def sort_tracks(track_dispenser, sort_key=None):
    # this is slow for large collections
    tracks = track_dispenser['items']
    while track_dispenser['next']:
        track_dispenser = g.sp.next(track_dispenser)
        tracks.extend(track_dispenser['items'])
    if sort_key:
        tracks.sort(key=sort_key)
    return tracks

def get_track_info(tracks):
    ids = [t['track']['id'] for t in tracks]
    features = []
    for i in range(0, len(ids), 100):
        rqst = g.sp.audio_features(ids[i:i+100])
        features.extend(rqst)

    df = []
    for track, feats in zip(tracks, features):
        t = {}
        t['ID'] = track['track']['id']
        t['Added'] = track['added_at']
        t['Track'] = track['track']['name']
        t['Artist'] = ', '.join([artist['name'] for artist in track['track']['artists']])
        t['Album'] = track['track']['album']['name']
        t['Release'] = track['track']['album']['release_date']
        t['Popularity'] = track['track']['popularity']

        t['Acousticness'] = feats['acousticness']
        t['Danceability'] = feats['danceability']
        t['Duration'] = feats['duration_ms']
        t['Energy'] = feats['energy']
        t['Instrumentalness'] = feats['instrumentalness']
        t['Key'] = feats['key']
        t['Liveness'] = feats['liveness']
        t['Loudness'] = feats['loudness']
        t['Mode'] = feats['mode']
        t['Speechiness'] = feats['speechiness']
        t['Tempo'] = feats['tempo']
        t['Time Signature'] = feats['time_signature']
        t['Valence'] = feats['valence']

        df.append(t)
        
    return pd.DataFrame(df)

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
