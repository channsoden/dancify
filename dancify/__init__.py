#!/usr/bin/env python
import os, json, requests, base64, urllib

from flask import Flask, request, redirect

import spotipy
import spotipy.oauth2 as sp_oauth2

#from data import authorize_sheets
#import spotipy_fns


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'dancify.sqlite'),
        )
    if test_config is None:
        # load the instance config when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        # dir alread exist
        pass

    @app.route('/hello')
    def hello():
        return "Hello, World!"

    from . import db
    db.init_app(app)

    from . import auth
    app.register_blueprint(auth.bp)
    
    return app

"""

# Get client keys from environment
client_id = os.getenv('SPOTIFY_CLIENT_ID')
client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')

# Spotify URLs
spotify_auth_url = 'https://accounts.spotify.com/authorize'
spotify_token_url = 'https://accounts.spotify.com/api/token'
spotify_api_base_url = "https://api.spotify.com"
api_version = "v1"
spotify_api_url = "{}/{}".format(spotify_api_base_url, api_version)

# Server-side Parameters
client_side_url = "http://localhost:5000"
redirect_uri = "{}/callback/q".format(client_side_url)
scope = "user-library-read playlist-read-private"
state = ""
show_dialog_bool = True
show_dialog_str = str(show_dialog_bool).lower()

auth_query_parameters = {
    "response_type": "code",
    "redirect_uri": redirect_uri,
    "scope": scope,
    # "state": state,
    # "show_dialog": show_dialog_str,
    "client_id": client_id
}

# Spotipy object
sp = None

@app.route('/')
def hello():
    if sp:
        lines = []
        lines.append( spotipy_fns.user_info_block(sp.current_user()) )
        lines.append( '' )
        lines.append( 'Playlists:' )
        results = sp.current_user_playlists()
        for item in results['items']:
            lines.append( str(item['name']) )
        html = '<br />'.join(lines)
        return html
    else:
        return redirect('{}/login'.format(client_side_url)) # use url_for


@app.route("/login")
def spotify_oauth():
    url_args = '&'.join(['{}={}'.format(key, urllib.parse.quote(val.encode('utf-8'))) for key,val in auth_query_parameters.items()])
    auth_url = '{}/?{}'.format(spotify_auth_url, url_args)
    return redirect(auth_url)

@app.route("/callback/q")
def spotify_callback():
    response_code = request.args['code']
    authorizer = sp_oauth2.SpotifyOAuth(client_id, client_secret, redirect_uri, scope=scope, cache_path=None)
    token = authorizer.get_access_token(response_code)['access_token']
    if token:
        print(token)
        global sp # the spotipy object should be unique to the session
        # the auth token should be stored in the flask.session
        # session values are stored in cookies sent to user, so I don't need to keep user's spotify tokens
        # but maybe I should encrypt the token and store it in my db so that users don't have to keep loggin in to spotify?
        sp = spotipy.Spotify(auth=token)
        return redirect(client_side_url)
    else:
        return("Failed to get authentication token.")



@app.route('/class_data')
def class_data():
    # The ID and range of a sample spreadsheet.
    SAMPLE_SPREADSHEET_ID = '1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms'
    SAMPLE_RANGE_NAME = 'Class Data!A2:E'

    # Call the Sheets API
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                                range=SAMPLE_RANGE_NAME).execute()
    values = result.get('values', [])

    lines = []
    if not values:
        lines.append('No data found.')
    else:
        lines.append('Name, Major:')
        for row in values:
            # Print columns A and E, which correspond to indices 0 and 4.
            lines.append('{}, {}'.format(row[0], row[4]))

    html = '<br />'.join(lines)
    return html

@app.route('/playlist/<ID>')
def view_playlist(ID):
    return 'Playlist ID: {}'.format(ID)

# If modifying these scopes, delete the file token.pickle.
sheets_scopes = ['https://www.googleapis.com/auth/spreadsheets.readonly']


if __name__ == '__main__':
    #    service = None
    #    authorize_sheets()
    app.run(debug=True, host='0.0.0.0')
"""
