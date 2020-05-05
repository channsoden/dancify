#!/usr/bin/env python
import os, functools

from flask import Blueprint, g, redirect, request, session, url_for, current_app

import spotipy
from spotipy import oauth2 as sp_oauth2

authorizer = None
def init_authorizer():
    global authorizer
    if authorizer is None:
        # Get client keys from config
        client_id = current_app.config['SPOTIFY_CLIENT_ID']
        client_secret = current_app.config['SPOTIFY_CLIENT_SECRET']

        # Auth parameters
        scope = "user-library-read playlist-read-private playlist-modify-private"
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
    #str_token_info  = authorizer.get_access_token(response_code,
    #                                              as_dict=False,
    #                                              check_cache=False)
    #BQAbxEyRPN6jinMcma8WTj_Kqi3gtZ_fe65DCx7FarJS1Lul28BDgOP4Pe0wZ0aQoHkViqIMZvUfAxVcvspR61IP6MkVY2Ke45e0XscfYyw8zLUzne2CNlCrZ8kfMS5z39-XxW3XiO5egFoXHb54FYr46p_oZyzHxOmkXAF2dHKUnYIGXy0k0NldUEW6yEnZXk-3dw

    token_info  = authorizer.get_access_token(response_code,
                                              check_cache=False)
    {'access_token': 'BQDRtVWs21L_zIJ1C_QdlLYhjbCZhUNtV4PWvB-QBP_wc2eqUXVhwM67DZW3yydz4ZQmpgjHtRirbGmwHvPb1CU_epz1fMTWhX6nTJZwBs8Ppo0wjWzlbrvXOKcTjTN7dDt-pOMl3lTwBAw-ZwNFGHbJDzuo5v59a-Nuzy1PdAiVpKarXViFUREGtjX2THiU-5ByTg',
     'token_type': 'Bearer',
     'expires_in': 3600,
     'refresh_token': 'AQAOIZVdBCU8rRQ8Bs9Z-mxAXRtw8LjGYpUIkgwXE34jj0UVEOU5g91aKkyevC2feu3Tph-DAo3bqEDMaRmOdL4xCVZlLGJ2nDOWYO_I_6uqhK0XXr9CYaky2rJNbzzGC1w',
     'scope': 'playlist-modify-private playlist-read-private user-library-read',
     'expires_at': 1588201481}
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
        if sp_oauth2.is_token_expired(token_info):
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



