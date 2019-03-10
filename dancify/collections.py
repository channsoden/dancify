#!/usr/bin/env python
from math import ceil

import numpy as np
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

def navpoints(page, pages):
    down = set(page+1 - np.logspace(0, np.log2(page), num=7, base=2).astype(int))
    up = set(page-1 + np.logspace(0, np.log2(max(1, pages-page)), num=7, base=2).astype(int))
    around = set([1, max(1, page-1), min(pages, page+1), pages])
    spread = sorted(list(up | down | around))
    return spread

@bp.route('/library/<int:page>')
@spotify_auth.login_required
def library(page):
    track_dispenser = g.sp.current_user_saved_tracks()
    return collection(track_dispenser, page, 'Saved Tracks')
    
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


@bp.route('/playlists/<uid>/<plid>/<int:page>')
@spotify_auth.login_required
def playlist(uid, plid, page):
    pl = g.sp.user_playlist(uid, playlist_id=plid)
    print(pl.keys())
    
    track_dispenser = g.sp.user_playlist_tracks(uid, playlist_id=plid)
    return collection(track_dispenser, page, 'get playlist name')

def collection(track_dispenser, page, collection_name):
    # Eventually should set these preferences and retrieve from g
    sort_key = None
    page_size = 100
    
    tracks = spotipy_fns.sort_tracks(track_dispenser, sort_key=sort_key)

    pages = ceil(len(tracks) / page_size)
    page = max(1, min(page, pages))
    pagination = navpoints(page, pages)
    page_urls = [(str(i), url_for('collections.library', page=i)) for i in pagination]
    track_selection = slice( (page-1)*100, page*100 )

    tracks = tracks[track_selection]
    tracks = spotipy_fns.get_track_info(tracks)

    columns = g.preferences['collections']['columns']

    class playlist_table(Table):
        for iname, xname in track_features.items():
            locals()[iname] = Col(xname, show = iname in columns)

    table = playlist_table(tracks)

    return render_template('/collections/collection.html',
                           collection=collection_name,
                           table=table.__html__(),
                           page_links = page_urls)

