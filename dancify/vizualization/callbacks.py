from datetime import datetime as dt
import json

from flask import g

import pandas as pd
import pandas_datareader as pdr
from dash.dependencies import Input
from dash.dependencies import Output
import dash_core_components as dcc
import dash_html_components as html
import dash_table as dt

from dancify import spotify_auth, spotipy_fns
from dancify.vizualization import elements, layout
    
def register_callbacks(dashapp):
    dashapp.config['suppress_callback_exceptions'] = True

    @spotify_auth.login_required
    @dashapp.callback([Output('page-header', 'children'),
                       Output('hidden-data', 'children'),
                       Output('preferences', 'children')],
                      [Input('url', 'pathname')])
    def load_collection(pathname):
        columns = g.preferences['collections']['columns']

        # This step is expensive, since it must wait for responses from Spotify.
        pathname = pathname.strip('/').split('/')[1:]

        if pathname[0] == 'library':
            track_dispenser = g.sp.current_user_saved_tracks()
            collection_name = 'Library'
        else:
            uid, plid = pathname[:2]
            pl = g.sp.user_playlist(uid, playlist_id=plid)
            track_dispenser = pl['tracks']
            collection_name = pl['name']

        tracks = spotipy_fns.sort_tracks(track_dispenser, sort_key=None)
        collection = spotipy_fns.get_track_info(tracks)
        collection['Release'] = pd.to_datetime(collection['Release']).dt.year
        collection['Duration'] = collection['Duration'] / 1000 # convert to seconds

        return (html.H1(collection_name),
                collection.to_json(date_format='iso', orient='split'),
                json.dumps(columns))

    for hist in elements.graphs:
        # Each slider is configured to entire collection.
        register_slider(dashapp, hist)
    # Visible table filtered by sliders.
    register_table(dashapp)
    for hist in elements.graphs:
        # Graphs show data from visible table
        register_histogram(dashapp, hist)

def register_slider(dashapp, hist):
    slider_id = hist+'_slider'

    @dashapp.callback(Output(slider_id, 'children'),
                      [Input('hidden-data', 'children'),
                       Input('preferences', 'children')])
    def update_slider(json_data, preferences):
        columns = json.loads(preferences)
        if hist not in columns:
            return None
        
        collection = pd.read_json(json_data, orient='split')
        slider = elements.slider(hist, collection[hist])
        return slider

def register_table(dashapp):
    inputs = [Input('hidden-data', 'children'),
              Input('preferences', 'children')]
    slider_ids = [slider+'_slider' for slider in elements.graphs]
    inputs += [Input(slider_id, 'value') for slider_id in slider_ids]
    
    @dashapp.callback([Output('table', 'data'),
                       Output('table', 'columns')],
                      inputs)
    def update_table(*inputs):
        json_data = inputs[0]
        preferences = inputs[1]
        sliders = inputs[2:]
        
        collection = pd.read_json(json_data, orient='split')
        view = collection
        for col, slider in zip(elements.graphs, sliders):
            if slider:
                view = view.loc[(view[col] >= slider[0]) & (view[col] <= slider[1])]

        columns = json.loads(preferences)
        columns = [{"name": c, "id": c} for c in columns]

        return (view.to_dict("rows"), columns)

def register_histogram(dashapp, hist):
    hist_id = hist+'_hist'
    
    @dashapp.callback(Output(hist_id, 'children'),
                      [Input('table', 'data'),
                       Input('preferences', 'children')])
    def update_hist(rows, preferences):
        columns = json.loads(preferences)
        if hist in columns:
            data = pd.DataFrame(rows)
            graph = elements.hist(hist, data[hist])
            return html.Div( [graph] )
        else:
            return html.Div( [], style={'display': 'none'} )
