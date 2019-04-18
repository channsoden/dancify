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
    dashapp.config['suppress_callback_exceptions'] = False

    @spotify_auth.login_required
    @dashapp.callback([Output('page-header', 'children'),
                       Output('dynamic-content', 'children'),
                       Output('hidden-data', 'children'),
                       Output('preferences', 'children')],
                      [Input('url', 'pathname')])
    def load_collection(pathname):
        if not pathname:
            # Url object has not yet loaded.
            return (None, None, None, None)
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

        dynamic_layout = layout.generate_dynamic_content(columns)

        return (html.H1(collection_name),
                dynamic_layout,
                collection.to_json(date_format='iso', orient='split'),
                json.dumps(columns))

    for hist in elements.graphables:
        # Each slider is configured to entire collection.
        register_slider(dashapp, hist)
    # Visible table filtered by sliders and search fields.
    register_table(dashapp)
    for hist in elements.graphables:
        # Graphs show data from visible table
        register_histogram(dashapp, hist)
        
def register_slider(dashapp, hist):
    slider_id = hist+'_slider'

    @dashapp.callback([Output(slider_id, 'min'),
                       Output(slider_id, 'max'),
                       Output(slider_id, 'value'),
                       Output(slider_id, 'marks')],
                      [Input('hidden-data', 'children')])
    def update_slider(json_data):
        collection = pd.read_json(json_data, orient='split')
        return elements.configure_slider(hist, collection[hist])

def str_contains(series, query):
    query = query.lower()
    return series.str.lower().str.contains(query)
    
def register_table(dashapp):
    inputs = [Input('hidden-data', 'children'),
              Input('update-button', 'n_clicks'),
              Input('preferences', 'children')]
    slider_ids = [slider+'_slider' for slider in elements.graphables]
    inputs += [Input(slider_id, 'value') for slider_id in slider_ids]
    field_ids = [field+'_input' for field in elements.filterables]
    states = [State(field_id, 'value') for field_id in field_ids]

    print('table registering')
    input()
    
    @dashapp.callback([Output('table', 'data'),
                       Output('table', 'columns')],
                      inputs,
                      states)
    def update_table(*args):
        json_data = args[0]
        nclicks = args[1]
        preferences = args[2]
        slider_values = args[3:3+len(elements.graphables)]
        field_values = args[3+len(elements.graphables):]

        columns = json.loads(preferences)
        print('update table sees these columns:')
        print(columns)
        input()
        
        collection = pd.read_json(json_data, orient='split')
        view = collection
        for col, val in zip(elements.filterables, field_values):
            if val:
                view = view.loc[str_contains(view[col], val)]
        for col, val in zip(elements.graphables, slider_values):
            if col in columns:
                view = view.loc[(view[col] >= val[0]) & (view[col] <= val[1])]

        columns = [{"name": c, "id": c} for c in columns]

        return (view.to_dict("rows"), columns)

def register_histogram(dashapp, hist):
    hist_id = hist+'_hist'
    
    @dashapp.callback(Output(hist_id, 'figure'),
                      [Input('table', 'data')])
    def update_hist(rows):
        collection = pd.DataFrame(rows)
        try:
            new_figure = elements.hist(hist, collection[hist])
            return new_figure
        except KeyError:
            # This feature is deselected in preferences, so doesn't appear in the table.
            return None
        

