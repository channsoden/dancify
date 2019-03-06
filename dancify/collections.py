#!/usr/bin/env python
from math import ceil

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

@bp.route('/library/<int:page>')
@spotify_auth.login_required
def library(page):
    # Eventually should set these preferences and retrieve from g
    sort_key = None
    page_size = 100
    
    track_dispenser = g.sp.current_user_saved_tracks()
    tracks = sort_tracks(track_dispenser, sort_key=sort_key)

    pages = ceil(len(tracks) / page_size)
    page = max(1, min(page, pages))
    page_navigations = set([1, page-10, page-5, page-4, page-3, page-2, page-1, page+1, page+2, page+3, page+4, page+5, page+10, pages])
    page_urls = [url_for('collections.library', page=i) for i in 
    track_selection = slice( (page-1)*100, page*100 )
    
    tracks = spotipy_fns.get_track_info(track_dispenser)

    columns = g.preferences['collections']['columns']

    class playlist_table(Table):
        for iname, xname in track_features.items():
            locals()[iname] = Col(xname, show = iname in columns)

    table = playlist_table(tracks)

    return render_template('/collections/collection.html', collection='Saved Tracks', table=table.__html__())
    
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
    tracks = spotipy_fns.get_track_info(track_dispenser)
        
    columns = g.preferences['collections']['columns']

    class playlist_table(Table):
        for iname, xname in track_features.items():
            locals()[iname] = Col(xname, show = iname in columns)

    table = playlist_table(tracks)
        
    return render_template('/collections/collection.html', collection='collection name', table=table.__html__())

