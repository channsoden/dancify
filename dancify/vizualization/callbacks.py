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


def get_collection(pathname):
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
    tracks = spotipy_fns.get_track_info(tracks)
    tracks['Release'] = pd.to_datetime(tracks['Release']).dt.year
    tracks['Duration'] = tracks['Duration'] / 1000 # convert to seconds
    
    return collection_name, tracks
    
def register_callbacks(dashapp):
    dashapp.config['suppress_callback_exceptions'] = True

    @spotify_auth.login_required
    @dashapp.callback([Output('page-header', 'children'),
                       Output('hidden-data', 'children'),
                       Output('preferences', 'children')],
                      [Input('url', 'pathname')])
    def configure_layout(pathname):
        columns = g.preferences['collections']['columns']

        # This step is expensive, since it must wait for responses from Spotify.
        collection_name, collection = get_collection(pathname)

        return (html.H1(collection_name),
                collection.to_json(date_format='iso', orient='split'),
                json.dumps(columns))

    for hist in elements.graphs:
        register_slider(dashapp, hist)
        register_histogram(dashapp, hist)
        
    register_table(dashapp)

def register_slider(dashapp, hist):
    slider_id = hist+'_slider'

    @dashapp.callback(Output(slider_id, 'children'),
                      [Input('hidden-data', 'children'),
                       Input('preferences', 'children')])
    def render_slider(json_data, preferences):
        columns = json.loads(preferences)
        if hist not in columns:
            return None
        
        collection = pd.read_json(json_data, orient='split')
        slider = elements.slider(hist, collection[hist])
        return slider


def register_histogram(dashapp, hist):
    hist_id = hist+'_hist'
    slider_id = hist+'_slider'
    
    @dashapp.callback(Output(hist_id, 'children'),
                      [Input(slider_id, 'value'),
                       Input('hidden-data', 'children'),
                       Input('preferences', 'children')])
    def render_hist(slider_value, json_data, preferences):
        collection = pd.read_json(json_data, orient='split')
        columns = json.loads(preferences)
        view = collection[hist]
        if slider_value:
            report = html.H2('Slider at: {}, {}'.format(*slider_value))
            view = view.loc[(view >= slider_value[0]) & (view <= slider_value[1])]
        else:
            report = html.H2('No slider value: {}'.format(slider_value))
        graph = elements.hist(hist, view)
        if hist in columns:
            return html.Div( [report, graph] )
        else:
            return html.Div( [graph], style={'display': 'none'} )

def register_table(dashapp):
    slider_ids = [slider+'_slider' for slider in elements.graphs]
    slider_inputs = [Input(slider_id, 'value') for slider_id in slider_ids]
    
    @dashapp.callback(Output('table', 'children'),
                      [Input('hidden-data', 'children'),
                       Input('preferences', 'children')] + \
                       slider_inputs)
    def render_table(*inputs):
        json_data = inputs[0]
        preferences = inputs[1]
        sliders = inputs[2:]
        collection = pd.read_json(json_data, orient='split')
        columns = json.loads(preferences)
        view = collection
        for col, slider in zip(elements.graphs, sliders):
            if slider:
                print('filtering on', col)
                view = view.loc[(view[col] >= slider[0]) & (view[col] <= slider[1])]
                print(view[col])
                print(len(view.to_dict("rows")))
                print(slider[0], type(slider[0]), slider[1], type(slider[1]))
                
        table = dt.DataTable(id='table',
                             columns=[{"name": i, "id": i} for i in columns],
                             data=view.to_dict("rows"),
                             **elements.table_style)  
        return table
