#!/usr/bin/env python

def user_info_block(user_dict):
    name = user_dict['display_name']
    photo = user_dict['images'][0]['url']
    img_tag = '<img src="{}" alt="{}" height="50" width="50">'
    return '{} {}'.format(img_tag.format(photo, name), name)

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
    
