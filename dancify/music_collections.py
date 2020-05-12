#!/usr/bin/env python
from math import ceil
from collections import OrderedDict

import numpy as np

from flask import Blueprint, g, redirect, request, session, url_for, render_template

from . import spotipy_fns
from . import spotify_auth

bp = Blueprint('collections', __name__)

track_features = OrderedDict([('ID', 'ID - Spotify track ID'),
                              ('Track', 'Track - Track title'),
                              ('Artist', 'Artist - Artist name/s'),
                              ('Album', 'Album - Album name'),
                              ('Tags', 'Tags - Your Dancify tags'),
                              ('Playlists', 'Playlists - The playlists you have added the song to. '\
                               'WARNING: This feature adds significantly to loading times.'),
                              ('Duration', 'Duration - Track duration in seconds'),
                              ('Added', 'Added - Date the song was added to the collection'),
                              ('Release', 'Release - Release date of the track/album'),
                              ('Popularity', 'Popularity - From 0 (least popular) to 100 (most popular)'),
                              ('Danceability', 'Danceability - From 0 (least danceable) to 1 (most danceable)'),
                              ('Energy', 'Energy - From 0 (lowest energy) to 1 (most energy)'),
                              ('Tempo', 'Tempo - In beats per minute'),
                              ('Time Signature', 'Time Signature - The number of beats per bar'),
                              ('Key', 'Key - In Pitch Class notation. 0 is C, 1 is C#/Db, 2 is D, etc.'),
                              ('Loudness', 'Loudness - Average volume of the track, in dB'),
                              ('Mode', 'Mode - 0 for Minor, 1 for Major'),
                              ('Valence', 'Valence - Overall emotion of the track. From 0 (negative) to 1 (positive)'),
                              ('Acousticness', 'Acousticness - From 0 (least likely to be acoustic) to 1 (most likely to be acoustic)'),
                              ('Instrumentalness', 'Instrumentalness - From 0 (least likely to be instrumental) to 1 (most likely to be instrumental)'),
                              ('Liveness', 'Liveness - From 0 (least likely to be live) to 1 (most likely to be live)'),
                              ('Speechiness', 'Speechiness - From 0 (most likely to be music) to 1 (most likely to be spoken word)')])

def navpoints(page, pages):
    down = set(page+1 - np.logspace(0, np.log2(page), num=7, base=2).astype(int))
    up = set(page-1 + np.logspace(0, np.log2(max(1, pages-page)), num=7, base=2).astype(int))
    around = set([1, max(1, page-1), min(pages, page+1), pages])
    spread = sorted(list(up | down | around))
    return spread
    
@bp.route('/playlists')
@spotify_auth.login_required
def playlists():
    list_dispenser = g.sp.current_user_playlists()
    lists = list_dispenser['items']
    while list_dispenser['next']:
        list_dispenser = g.sp.next(list_dispenser)
        lists.extend(list_dispenser['items'])
    lists.sort(key = lambda l: l['name'].lower())
    for l in lists:
        l['viz_url'] = '/playlists/{}/{}'.format(l['owner']['id'], l['id'])

    return render_template('collections/playlists.html', lists=lists)


@bp.route('/playlists/<uid>/<plid>')
@spotify_auth.login_required
def playlist_page(uid, plid):
    pl = g.sp.user_playlist(uid, playlist_id=plid)
    desc = pl['description'] + ' [{} songs]'.format(pl['tracks']['total'])
    dash_url = url_for('/viz/') + 'playlist/' + '{}/{}'.format(uid, plid)
    return render_template('/collections/collection.html',
                           title = pl['name'],
                           description = desc,
                           dash_url = dash_url)

@bp.route('/library')
@spotify_auth.login_required
def library_page():
    dash_url = url_for('/viz/') + 'library'
    return render_template('/collections/collection.html',
                           title = 'Library',
                           description = 'Your Spotify library.',
                           dash_url = dash_url)

def pop_scale(popularity):
    if popularity <= 0:
        return 'very obscure'
    elif popularity <= 10:
        return 'obscure'
    elif popularity <= 30:
        return 'somewhat obscure'
    elif popularity <= 50:
        return 'moderately well known'
    elif popularity <= 70:
        return 'well known'
    elif popularity <= 90:
        return 'famous'
    elif popularity <= 95:
        return 'very famous'
    else:
        return 'mega famous'

@bp.route('/artist/<artid>')
@spotify_auth.login_required
def artist_page(artid):
    artist = g.sp.artist(artid)
    dash_url = url_for('/viz/') + 'artist/' + artid
    return render_template('/collections/collection.html',
                           title = artist['name'],
                           dash_url = dash_url)

@bp.route('/album/<albid>')
@spotify_auth.login_required
def album_page(albid):
    album = g.sp.album(albid)
    dash_url = url_for('/viz/') + 'album/' + albid
    return render_template('/collections/collection.html',
                           title = album['name'],
                           description = desc,
                           dash_url = dash_url)

@bp.route('/defunct_library/<int:page>')
@spotify_auth.login_required
def defunct_library(page):
    # can I keep some of this in local storage so that I don't have to make as many fetches
    track_dispenser = g.sp.current_user_saved_tracks()
    sort_key = None # Eventually should set this preference and retrieve from g
    tracks = spotipy_fns.sort_tracks(track_dispenser, sort_key=sort_key)
    viz_url = '{}library'.format(url_for('/viz/'))
    return collection(tracks, page, 'Saved Tracks', viz_url)

def defunct_collection(tracks, page, collection_name, viz_url):
    # Eventually should set this preference and retrieve from g
    page_size = 100
    pages = ceil(len(tracks) / page_size)
    page = max(1, min(page, pages))
    pagination = navpoints(page, pages)
    page_urls = [(str(i), url_for('collections.library', page=i)) for i in pagination]
    track_selection = slice( (page-1)*100, page*100 )
    tracks = tracks[track_selection]
    
    tracks = spotipy_fns.get_track_info(tracks)
    columns = g.preferences['collections']['columns']

    table = tracks.to_html(columns = columns,
                           border = 0,
                           index = False,
                           justify = 'left')

    return render_template('/collections/collection.html',
                           collection=collection_name,
                           viz_url = viz_url,                           
                           table=table,
                           page_links = page_urls)

