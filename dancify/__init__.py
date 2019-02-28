#!/usr/bin/env python
import os, json, requests, base64, urllib

from flask import Flask, request, redirect

import spotipy_fns

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

    @app.route('/')
    def index():
        if g.user:
            return spotipy_fns.user_info_block(g.user)
        else:
            return 'Not logged in'
    
    from . import db
    db.init_app(app)

    from . import spotify_auth
    app.register_blueprint(spotify_auth.bp)

    @app.route('/playlists')
    @spotify_auth.login_required():
    def playlists():
        lines = []
        lines.append( spotipy_fns.user_info_block(g.user) )
        lines.append( '' )
        lines.append( 'Playlists:' )
        results = g.sp.current_user_playlists()
        for item in results['items']:
            lines.append( str(item['name']) )
        html = '<br />'.join(lines)
        return html
    
    return app





"""
from data import authorize_sheets

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
