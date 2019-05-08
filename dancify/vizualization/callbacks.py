from datetime import datetime as dt
from collections import defaultdict
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

# temporary variable to use until I figure out sql
tags = defaultdict(set)

# Chains of callbacks will throw many TypeError exceptions while they
# wait for their upstream elements to load.
class CallbackChain(Exception):
    pass

def register_callbacks(dashapp):
    dashapp.config['suppress_callback_exceptions'] = False

    @spotify_auth.login_required
    @dashapp.callback([Output('page-header', 'children'),
                       Output('hidden-data', 'children'),
                       Output('preferences', 'children'),
                       Output('dynamic-content', 'children')],
                      [Input('url', 'pathname')])
    def load_collection(pathname):
        if not pathname:
            raise CallbackChain('URL element not yet loaded.')
        
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

        print('loaded collection')
        
        return (html.H1(collection_name),
                collection.to_json(date_format='iso', orient='split'),
                json.dumps(columns),
                dynamic_layout)

    # Tags can be added to the filtered collection.
    register_tag_controls(dashapp)
    for hist in elements.graphables:
        # Each slider is configured to entire collection.
        register_slider(dashapp, hist)
    ## Visible table filtered by sliders and search fields.
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
        if not json_data:
            raise CallbackChain('Hidden data not yet loaded.')
        collection = pd.read_json(json_data, orient='split')
        return elements.configure_slider(hist, collection[hist])
        
def register_table(dashapp):
    inputs = [Input('hidden-data', 'children'),
              Input('update-button', 'n_clicks_timestamp'),
              Input('preferences', 'children'),
              Input('tags', 'children')]
    slider_ids = [slider+'_slider' for slider in elements.graphables]
    inputs += [Input(slider_id, 'value') for slider_id in slider_ids]
    field_ids = [field+'_input' for field in elements.filterables]
    states = [State(field_id, 'value') for field_id in field_ids]

    @dashapp.callback([Output('table', 'data'),
                       Output('table', 'columns')],
                      inputs,
                      states)
    def update_table(*args):
        json_data = args[0]
        update_time = args[1]
        preferences = args[2]
        json_tags = args[3]
        slider_values = args[4:4+len(elements.graphables)]
        field_values = args[4+len(elements.graphables):]
        
        if (not preferences or
            not json_data or
            not json_tags):
            # URL element has not yet loaded.
            raise CallbackChain('Hidden data not yet loaded.')

        columns = json.loads(preferences)
        tags = json.loads(json_tags)
        collection = pd.read_json(json_data, orient='split')

        collection['Tags'] = [', '.join([tag for tag, state in tags[sid].items() if state])
                        for sid in collection['ID']]
        
        collection = filter_collection(collection, field_values, slider_values, columns)
                
        columns = [{"name": c, "id": c} for c in columns]

        return (collection.to_dict("rows"), columns)

def filter_collection(collection, field_values, slider_values, columns):
    for col, val in zip(elements.filterables, field_values):
        if val:
            include, exclude, mandatory = parse_search_terms(val)
            hits = ~collection[col].astype(bool)
            for term in include:
                hits |= str_contains(collection[col], term)
            collection = collection.loc[hits]
            for term in exclude:
                collection = collection.loc[~str_contains(collection[col], term)]
            for term in mandatory:
                collection = collection.loc[str_contains(collection[col], term)]
    for col, val in zip(elements.graphables, slider_values):
        if val and (col in columns):
            collection = collection.loc[(collection[col] >= val[0]) & (collection[col] <= val[1])]
    return collection

def parse_search_terms(query):
    include = []
    exclude = []
    mandatory = []
    for term in query.split(','):
        term = term.strip()
        if not term:
            pass
        elif term[0] == '-':
            exclude.append(term[1:])
        elif term[0] == '+':
            mandatory.append(term[1:])
        else:
            include.append(term)

    return include, exclude, mandatory

def str_contains(series, query):
    query = query.lower()
    return series.str.lower().str.contains(query)
            
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
            raise CallbackChain('Not rendering {}'.format(hist_id))


def register_tag_controls(dashapp):
    @dashapp.callback(Output('tags', 'children'),
                      [Input('add-tag-button', 'n_clicks_timestamp'),
                       Input('remove-tag-button', 'n_clicks_timestamp'),
                       Input('hidden-data', 'children')],
                      [State('table', 'data'),
                       State('tag-input', 'value'),
                       State('tags', 'children')])
    def update_tags(add_time, remove_time, hidden_data, songs, tag, tags):
        if tags:
            tags = json.loads(tags)
        else:
            # Load tags from the DB
            # Tags are stored as dict of booleans since json cannot do sets.
            collection = pd.read_json(hidden_data, orient='split')
            tags = {ID:{} for ID in collection['ID']}



        if tag:
            # Validate the tag by removing commas which
            # will be used in searching as logical and.
            tag = tag.lower().replace(',', '')

            # This callback gets called on page load,
            # so either time-stamp will be None until
            # button is pressed.
            if not add_time:
                add_time = 0
            if not remove_time:
                remove_time = 0
                
            if add_time > remove_time:
                for song in songs:
                    # Add the tags to the DB
                    
                    # And update tags in table.
                    tags[song['ID']][tag] = True
            if remove_time > add_time:
                for song in songs:
                    # Remove the tags from the DB
                    
                    # And update tags in table.
                    tags[song['ID']][tag] = False
                
        return json.dumps(tags)

    
