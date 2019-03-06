#!/usr/bin/env python
from flask import g

def user_info_block(user_dict):
    name = user_dict['display_name']
    photo = user_dict['images'][0]['url']
    img_tag = '<img src="{}" alt="{}" height="50" width="50">'
    return '{} {}'.format(img_tag.format(photo, name), name)

def get_track_info(track_dispenser):
    tracks = track_dispenser['items']
    while track_dispenser['next']:
        track_dispenser = g.sp.next(track_dispenser)
        tracks.extend(track_dispenser['items'])
    tracks = tracks[:100] # getting features breaks with larger requests
    # need to split tracks up into pages and allow for paging
    ids = [t['track']['id'] for t in tracks]
    features = g.sp.audio_features(ids)

    for track, feats in zip(tracks, features):
        t = {}
        t['tid'] = track['track']['id']
        t['timestamp'] = track['added_at']
        t['title'] = track['track']['name']
        t['artist'] = ', '.join([artist['name'] for artist in track['track']['artists']])
        t['album'] = track['track']['album']['name']
        t['release'] = track['track']['album']['release_date']
        t['popularity'] = track['track']['popularity']

        t['acousticness'] = feats['acousticness']
        t['danceability'] = feats['danceability']
        t['duration'] = feats['duration_ms']
        t['energy'] = feats['energy']
        t['instrumentalness'] = feats['instrumentalness']
        t['key'] = feats['key']
        t['liveness'] = feats['liveness']
        t['loudness'] = feats['loudness']
        t['mode'] = feats['mode']
        t['speechiness'] = feats['speechiness']
        t['tempo'] = feats['tempo']
        t['time_signature'] = feats['time_signature']
        t['valence'] = feats['valence']

        yield t

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
