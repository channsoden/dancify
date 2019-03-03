#!/usr/bin/env python

from flask import Blueprint, g, redirect, request, session, url_for

from . import spotipy_fns
from . import spotify_auth

bp = Blueprint('collections', __name__)

@bp.route('/playlists')
@spotify_auth.login_required
def playlists():
    lines = []
    lines.append( spotipy_fns.user_info_block(g.user) )
    lines.append( '' )
    lines.append( 'Playlists:' )

    
    list_dispenser = g.sp.current_user_playlists()
    lists = list_dispenser['items']
    while list_dispenser['next']:
        list_dispenser = g.sp.next(list_dispenser)
        lists.extend(list_dispenser['items'])
    lists.sort(key = lambda l: l['name'])

    print(lists[0])

    for pl in lists:
        link = '<a href="{}">{}</a>'.format(url_for('.playlist', uid=pl['owner']['id'], plid=pl['id']), pl['name'])
        lines.append(link)
            
    html = '<br />'.join(lines)
    return html

@bp.route('/playlists/<uid>/<plid>')
@spotify_auth.login_required
def playlist(uid, plid):
    lines = []
    lines.append( spotipy_fns.user_info_block(g.user) )
    lines.append( '' )
    lines.append( 'Tracks:' )
    lines.append( 'Name - Artist/s - Album' )

    track_dispenser = g.sp.user_playlist_tracks(uid, playlist_id=plid)
    tracks = track_dispenser['items']
    while track_dispenser['next']:
        track_dispenser = g.sp.next(track_dispenser)
        tracks.extend(track_dispenser['items'])

    print(tracks[0])

    for track in tracks:
        name = track['track']['name']
        artists = [artist['name'] for artist in track['track']['artists']]
        album = track['track']['album']['name']

        summary = '{} - {} - {}'.format(name, ', '.join(artists), album)
        lines.append(summary)

    return '<br />'.join(lines)

