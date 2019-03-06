#!/usr/bin/env python
import os, functools, urllib

from flask import Blueprint, g, redirect, request, session, url_for

import spotipy
from spotipy import oauth2 as sp_oauth2

authorizer = None
def init_authorizer():
    global authorizer
    if authorizer is None:
        # Get client keys from environment
        client_id = os.getenv('SPOTIFY_CLIENT_ID')
        client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')

        # Auth parameters
        scope = "user-library-read playlist-read-private"
        state = ""
        show_dialog_bool = True
        show_dialog_str = str(show_dialog_bool).lower()
        
        authorizer = sp_oauth2.SpotifyOAuth(client_id,
                                            client_secret,
                                            url_for('auth.spotify_callback', _external=True),
                                            scope=scope,
                                            cache_path=None)

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/login')
def login():
    auth_url = authorizer.get_authorize_url()
    return redirect(auth_url)

@bp.route('/callback/q')
def spotify_callback():
    response_code = request.args['code']
    token_info  = authorizer.get_access_token(response_code)
    if token_info['access_token']:
        # The auth token should be stored in the flask.session
        # session values are stored in cookies sent to user, so I don't need to keep user's spotify tokens
        session.clear()
        session['token_info'] = token_info
        return redirect(url_for('index'))
    else:
        return("Failed to get authentication token.")


@bp.before_app_request
def load_logged_in_user():
    token_info = session.get('token_info')

    if token_info is None:
        g.user = None
    else:
        if authorizer._is_token_expired(token_info):
            token_info = authorizer.refresh_access_token(token_info['refresh_token'])
            session['token_info'] = token_info

        g.sp = spotipy.Spotify(auth=token_info['access_token'])
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



