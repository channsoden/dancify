#!/usr/bin/env python
from collections import defaultdict
import time, datetime
from html import escape

import pandas as pd
from flask import g, url_for
import dash_html_components as html

def user_info_block(user_dict):
    name = escape(user_dict['display_name'])
    photo = user_dict['images'][0]['url']
    img_tag = '<img src="{}" alt="{}" height="50" width="50">'
    return '{} {}'.format(img_tag.format(photo, name), name)

def describe_artist(artid):
    artist = g.sp.artist(artid)
    popularity = '{} ({}/100)'.format(pop_scale(artist['popularity']), artist['popularity'])
    if len(artist['genres']) > 1:
        genres = 'the ' + ', '.join(artist['genres'][:-1]) + ' and ' + artist['genres'][-1] + ' genres'
    elif len(artist['genres']) == 1:
        genres = 'the ' + artist['genres'][0] + ' genre'
    else:
        genres = 'an unclassified genre'
    desc = '{} is {} and performs in {}.'
    return desc.format(artist['name'], popularity, genres)

def describe_album(albid):
    album = g.sp.album(albid)
    artists = [a['name'] for a in album['artists']]
    if len(artists) > 1:
        artists = ', '.join(artists[:-1]) + ' and ' + artists[-1]
    else:
        artists = artists[0]
    if len(album['genres']) > 1:
        genres = 'the ' + ', '.join(album['genres'][:-1]) + ' and ' + album['genres'][-1] + ' genres'
    elif len(album['genres']) == 1:
        genres = 'the ' + album['genres'][0] + ' genre'
    else:
        genres = 'an unclassified genre'
    desc = 'A {} {} by {} in {}. [{} tracks]'
    return desc.format(album['release_date'].split('-')[0],
                       album['album_type'],
                       artists,
                       genres,
                       album['tracks']['total'])

def sort_tracks(track_dispenser, sort_key=None):
    # this is slow for large collections
    tracks = track_dispenser['items']
    while track_dispenser['next']:
        track_dispenser = g.sp.next(track_dispenser)
        tracks.extend(track_dispenser['items'])
    if sort_key:
        tracks.sort(key=sort_key)
    return tracks

def get_artist_tracks(artid):
    disco = g.sp.artist_albums(artid)
    tracks = []
    for album in disco['items']:
        album_tracks = get_album_tracks(album)
        tracks.extend(album_tracks)
    return tracks

def get_album_info(albid):
    album = g.sp.album(albid)
    tracks = get_album_tracks(album)
    return tracks

def get_album_tracks(album):
    # This reformat is fairly useless, but makes the data
    # look like tracks returned by the Spotipy playlist api.
    album_tracks = g.sp.album_tracks(album['id'])
    tracks = []
    for t in album_tracks['items']:
        t['album'] = album
        t['popularity'] = None # Not sure how to get popularity outside of pl context.
        tracks.append({'added_at': time.strftime('%Y-%m-%dT%H:%M:%S%Z'),
                       'track': t})
    return tracks


def get_track_info(tracks):
    ids = [t['track']['id'] for t in tracks]
    features = []
    for i in range(0, len(ids), 100):
        rqst = g.sp.audio_features(ids[i:i+100])
        features.extend(rqst)

    # Link Artist and Album columns to their viz pages.
    # Use markdown for this https://github.com/plotly/dash-table/issues/222
    # need to update dash_table
    artist_link = '[{}](' + url_for('/viz/')  + 'artist/{}' + ')'
    album_link = '[{}](' + url_for('/viz/')  + 'album/{}' + ')'

    df = []
    for track, feats in zip(tracks, features):
        t = {}
        t['ID'] = track['track']['id']
        t['Added'] = track['added_at']
        t['Track'] = escape(track['track']['name'])
        t['Artist'] = ', '.join([artist_link.format(escape(artist['name']),
                                                    artist['id'])
                                 for artist in track['track']['artists']])
        t['Album'] = album_link.format(escape(track['track']['album']['name']),
                                       track['track']['album']['id'])
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

def overwrite_playlist(playlist_name, tracks):
    if len(tracks) > 10000:
        return None, 'Playlist too long. (Max 10,000 tracks.)'
    
    playlist = get_user_playlist(playlist_name)
    if not playlist:
        playlist = g.sp.user_playlist_create(g.user['id'],
                                             playlist_name,
                                             public = False,
                                             description = 'Made by Dancify.')

    snapshot = g.sp.user_playlist_replace_tracks(g.user['id'], playlist['id'], tracks[:100])
    i = 100
    while i < len(tracks):
        snapshot = g.sp.user_playlist_add_tracks(g.user['id'], playlist['id'], tracks[i:i+100])
        i += 100

    return snapshot, None

def get_user_playlist(playlist_name):
    list_dispenser = g.sp.current_user_playlists()
    lists = list_dispenser['items']
    while list_dispenser['next']:
        list_dispenser = g.sp.next(list_dispenser)
        lists.extend(list_dispenser['items'])

    for l in lists:
        if (l['name'] == playlist_name) and (l['owner']['id'] == g.user['id']):
            return l

    return None

def add_tracks_to_playlist(playlist_name, tracks):
    playlist = get_user_playlist(playlist_name)
    if not playlist:
        return None, 'Playlist not found.'

    if (len(tracks) + playlist['tracks']['total']) > 10000:
        return None, 'Playlist too long. (Max 10,000 tracks.)'
        
    i = 0
    while i < len(tracks):
        snapshot = g.sp.user_playlist_add_tracks(g.user['id'], playlist['id'], tracks[i:i+100])
        i += 100

    return snapshot, None

def remove_tracks_from_playlist(playlist_name, tracks):
    playlist = get_user_playlist(playlist_name)
    if not playlist:
        return None, 'Playlist not found.'

    i = 0
    while i < len(tracks):
        snapshot = g.sp.user_playlist_remove_all_occurrences_of_tracks(g.user['id'], playlist['id'], tracks[i:i+100])
        i += 100

    return snapshot, None

def playlist_membership(tracks, exclude = []):
    # This is extremely slow because it requires requesting all tracks from
    # each of the user's playlists.
    # e.g. with 109 playlists takes about 29 seconds
    list_dispenser = g.sp.current_user_playlists()
    memberships = defaultdict(set)
    extract_memberships(memberships, list_dispenser['items'], exclude = exclude)
    while list_dispenser['next']:
        list_dispenser = g.sp.next(list_dispenser)
        extract_memberships(memberships, list_dispenser['items'], exclude = exclude)
    memberships = [', '.join(sorted(list(memberships[t]), key=lambda s: s.lower()))
                   for t in tracks]
    return memberships

def extract_memberships(memberships, lists, exclude = []):
    uid = g.sp.me()['id']
    playlist_link = '[{}](' + url_for('/viz/')  + 'playlist/' + uid + '/{}' + ')'
    for pl in lists:
        if pl['id'] in exclude:
            continue
        # This request takes a significant amount of time. (1/4 second)
        pl = g.sp.user_playlist(g.user['id'], playlist_id=pl['id'])
        track_dispenser = pl['tracks']
        tracks = sort_tracks(track_dispenser)
        for t in tracks:
            memberships[t['track']['id']].add(playlist_link.format(escape(pl['name']),
                                                                   pl['id']))


def search(album='', artist='', general='', genre='',
           minDate='', maxDate='', track='', qtype='track',
           hipster=False, new=False):
    query = []
    if album:
        query.append('album:'+album)
    if artist:
        query.append('artist:'+artist)
    if general:
        query.append(general)
    if genre:
        query.append('genre:'+genre)
    if track:
        query.append('track:'+track)
    if hipster:
        query.append('tag:hipster')
    if new:
        query.append('tag:new')
        
    if minDate and maxDate:
        query.append('year:'+minDate+'-'+maxDate)
    elif minDate:
        current_year = int(datetime.now().year)
        query.append('year:'+minDate+'-'+current_year)
    elif maxDate:
        query.append('year:0-'+maxDate)
    else:
        pass

    query = ' '.join(query)
    result = g.sp.search(query, limit=10, offset=0, type=qtype, market=None)

    #result[qtype+'s'].keys() = dict_keys(['href', 'items', 'limit', 'next', 'offset', 'previous', 'total'])

    return result

    
