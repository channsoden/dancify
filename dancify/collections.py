#!/usr/bin/env python

from flask import Blueprint, g, redirect, request, session, url_for, render_template
from flask_table import Table, Col

from . import spotipy_fns
from . import spotify_auth

bp = Blueprint('collections', __name__)

track_features = {
    'tid': 'ID',
    'title': 'Track',
    'artist': 'Artist',
    'album': 'Album',
    'popularity': 'Popularity',
    'release': 'Release',
    'timestamp': 'Added',
    'acousticness': 'Acousticness',
    'danceability': 'Danceability',
    'duration': 'Duration',
    'energy': 'Energy',
    'instrumentalness': 'Instrumentalness',
    'key': 'Key',
    'liveness': 'Liveness',
    'loudness': 'Loudness',
    'mode': 'Mode',
    'speechiness': 'Speechiness',
    'tempo': 'Tempo',
    'time_signature': 'Time Signature',
    'valence': 'Valence'
}

@bp.route('/playlists')
@spotify_auth.login_required
def playlists():
    list_dispenser = g.sp.current_user_playlists()
    lists = list_dispenser['items']
    while list_dispenser['next']:
        list_dispenser = g.sp.next(list_dispenser)
        lists.extend(list_dispenser['items'])
    lists.sort(key = lambda l: l['name'])

    return render_template('collections/playlists.html', lists=lists)


@bp.route('/playlists/<uid>/<plid>')
@spotify_auth.login_required
def playlist(uid, plid):
    track_dispenser = g.sp.user_playlist_tracks(uid, playlist_id=plid)
    tracks = track_dispenser['items']
    while track_dispenser['next']:
        track_dispenser = g.sp.next(track_dispenser)
        tracks.extend(track_dispenser['items'])
    features = g.sp.audio_features([t['track']['id'] for t in tracks])
        
    columns = session.get('playlist_prefs')['columns'] # should actually add this to g in a load prefs step beforehand

    class playlist_table(Table):
        for iname, xname in track_features.items():
            locals()[iname] = Col(xname, show = iname in columns)
        
    rows = []
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

        rows.append(t)

    table = playlist_table(rows)
        
    return render_template('/collections/collection.html', collection='collection name', table=table.__html__())

