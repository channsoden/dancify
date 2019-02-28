#!/usr/bin/env python
import os, functools, urllib

from flask import Blueprint, g, redirect, request, session, url_for

import spotipy
from spotipy import oauth2 as sp_oauth2

# Get client keys from environment
client_id = os.getenv('SPOTIFY_CLIENT_ID')
client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')

# Spotify URLs
spotify_auth_url = 'https://accounts.spotify.com/authorize'
spotify_token_url = 'https://accounts.spotify.com/api/token'
spotify_api_base_url = "https://api.spotify.com"
api_version = "v1"
spotify_api_url = "{}/{}".format(spotify_api_base_url, api_version)

# Auth parameters
scope = "user-library-read playlist-read-private"
state = ""
show_dialog_bool = True
show_dialog_str = str(show_dialog_bool).lower()


bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/login')
def login():
    # Server-side Parameters
    # Should use flask.url_for()
    #client_side_url = "http://localhost:5000"
    #redirect_uri = "{}/callback/q".format(client_side_url)
    
    auth_query_parameters = {
        "response_type": "code",
        "redirect_uri": url_for('auth.spotify_callback', _external=True),
        "scope": scope,
        # "state": state,
        # "show_dialog": show_dialog_str,
        "client_id": client_id
    }
    
    url_args = ['{}={}'.format(key, urllib.parse.quote(val.encode('utf-8')))
                for key,val in auth_query_parameters.items()]
    url_args = '&'.join(url_args)
    auth_url = '{}/?{}'.format(spotify_auth_url, url_args)
    return redirect(auth_url)

@bp.route('/callback/q')
def spotify_callback():
    response_code = request.args['code']
    authorizer = sp_oauth2.SpotifyOAuth(client_id,
                                        client_secret,
                                        url_for('auth.spotify_callback', _external=True),
                                        scope=scope,
                                        cache_path=None)
    token = authorizer.get_access_token(response_code)['access_token']
    if token:
        # The auth token should be stored in the flask.session
        # session values are stored in cookies sent to user, so I don't need to keep user's spotify tokens
        session.clear()
        session['sp_token'] = token
        sp = spotipy.Spotify(auth=token)
        return redirect(url_for('playlists'))
    else:
        return("Failed to get authentication token.")


@bp.before_app_request
def load_logged_in_user():
    token = session.get('sp_token')

    if token is None:
        g.user = None
    else:
        g.sp = spotipy.Spotify(auth=token)
        g.user = g.sp.current_user()

@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))

        return view(**kwargs)

    return wrapped_view



