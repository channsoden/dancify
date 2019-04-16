from datetime import datetime as dt
import json

from flask import g

import pandas as pd
import pandas_datareader as pdr
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
import dash_table as dt

from dancify import spotify_auth, spotipy_fns
from dancify.vizualization import elements, layout
    
def register_callbacks(dashapp):
    dashapp.config['suppress_callback_exceptions'] = True

    @spotify_auth.login_required
    @dashapp.callback([Output('page-header', 'children'),
                       Output('dynamic-content', 'children'),
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

        fields, graphs, dynamic_layout = layout.generate_dynamic_content(columns)

        for hist in graphs:
            # Each slider is configured to entire collection.
            register_slider(dashapp, hist)
        # Visible table filtered by sliders and search fields.
        register_table(dashapp, fields, graphs)
        for hist in graphs:
            # Graphs show data from visible table
            register_histogram(dashapp, hist)
        
        return (html.H1(collection_name),
                dynamic_layout,
                collection.to_json(date_format='iso', orient='split'),
                json.dumps(columns))
        
def register_slider(dashapp, hist):
    slider_id = hist+'_slider'

    @dashapp.callback(Output(slider_id, 'children'),
                      [Input('hidden-data', 'children')])
    def update_slider(json_data):
        collection = pd.read_json(json_data, orient='split')
        slider = elements.slider(hist, collection[hist])
        return slider

def str_contains(series, query):
    query = query.lower()
    return series.str.lower().str.contains(query)
    
def register_table(dashapp, fields, graphs):
    inputs = [Input('hidden-data', 'children'),
              Input('update-button', 'n_clicks')]
    slider_ids = [slider+'_slider' for slider in graphs]
    inputs += [Input(slider_id, 'value') for slider_id in slider_ids]
    field_ids = [field+'_input' for field in fields]
    states = [State(field_id, 'value') for field_id in field_ids]
    
    @dashapp.callback([Output('table', 'data'),
                       Output('table', 'columns')],
                      inputs,
                      states)
    def update_table(*args):
        json_data = args[0]
        nclicks = args[1]
        slider_values = args[2:2+len(graphs)]
        field_values = args[2+len(graphs):]
                
        collection = pd.read_json(json_data, orient='split')
        view = collection
        for col, val in zip(fields, field_values):
            if val:
                view = view.loc[str_contains(view[col], val)]
        for col, val in zip(graphs, slider_values):
            view = view.loc[(view[col] >= val[0]) & (view[col] <= val[1])]

        columns = fields + graphs
        columns = [{"name": c, "id": c} for c in columns]

        return (view.to_dict("rows"), columns)

def register_histogram(dashapp, hist):
    hist_id = hist+'_hist'
    
    @dashapp.callback(Output(hist_id, 'children'),
                      [Input('table', 'data')])
    def update_hist(rows, preferences):
        try:
            data = pd.DataFrame(rows)
            graph = elements.hist(hist, data[hist])
            return html.Div( [graph] )
        except KeyError:
            # The table probably isn't loaded yet.
            html.Div( [], style={'display': 'none'} )

