from datetime import datetime as dt
import json

from flask import g

import pandas as pd
import numpy as np
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
from sqlalchemy.sql import select

from dancify import spotify_auth, spotipy_fns
from dancify.db import get_db, tag_table
from dancify.vizualization import elements, layout

# Chains of callbacks will throw many TypeError exceptions while they
# wait for their upstream elements to load.
class CallbackChain(Exception):
    pass

def register_callbacks(dashapp):
    dashapp.config['suppress_callback_exceptions'] = False

    @spotify_auth.login_required
    @dashapp.callback([Output('page-header', 'children'),
                       Output('playlist-info', 'children'),
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
            playlist_info = 'Your Spotify library.'
        else:
            uid, plid = pathname[:2]
            pl = g.sp.user_playlist(uid, playlist_id=plid)
            track_dispenser = pl['tracks']
            collection_name = pl['name']
            playlist_info = pl['description']

        tracks = spotipy_fns.sort_tracks(track_dispenser, sort_key=None)
        collection = spotipy_fns.get_track_info(tracks)
        collection['Release'] = pd.to_datetime(collection['Release']).dt.year
        collection['Duration'] = collection['Duration'] / 1000 # convert to seconds

        playlist_info += ' [{} songs]'.format(len(collection))
        dynamic_layout = layout.generate_dynamic_content(columns)

        return (html.H1(collection_name),
                playlist_info,
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
    register_playlist_controls(dashapp)

        
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
              Input('preferences', 'children'),
              Input('tags', 'children'),
              Input('sort-order', 'value'),
              Input('sort-toggle', 'value')]
    slider_ids = [slider+'_slider' for slider in elements.graphables]
    inputs += [Input(slider_id, 'value') for slider_id in slider_ids]
    field_ids = [field+'_input' for field in elements.filterables]
    inputs += [Input(field_id, 'n_submit') for field_id in field_ids]
    states = [State(field_id, 'value') for field_id in field_ids]

    @dashapp.callback([Output('table', 'data'),
                       Output('table', 'columns'),
                       Output('selection-info', 'children')],
                      inputs,
                      states)
    def update_table(*args):
        json_data = args[0]
        preferences = args[1]
        json_tags = args[2]
        sort_order = args[3]
        sort_ascending = args[4]
        slider_start = 5
        submit_start = slider_start + len(elements.graphables)
        field_start = submit_start + len(elements.filterables)
        slider_values = args[slider_start:submit_start]
        field_submits = args[submit_start:field_start]
        field_values = args[field_start:]
        
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
        if collection[sort_order].dtype == collection['Track'].dtype:
            # Convert to lower case for sorting
            if sort_ascending:
                collection = collection.iloc[collection[sort_order].str.lower().argsort()]
            else:
                collection = collection.iloc[collection[sort_order].str.lower().argsort()[::-1]]
        else:
            # Numbers sort fine.
            collection.sort_values(by = [sort_order], inplace = True, ascending=sort_ascending)
                
        columns = [{"name": c, "id": c} for c in columns]

        selection_info = html.H3('  {} songs selected'.format(len(collection)))
                      
        return (collection.to_dict("rows"),
                columns,
                selection_info)

def filter_collection(collection, field_values, slider_values, columns):
    for col, val in zip(elements.filterables, field_values):
        if val:
            include, exclude, mandatory = parse_search_terms(val)
            for term in mandatory:
                collection = collection.loc[str_contains(collection[col], term)]
            for term in exclude:
                collection = collection.loc[~str_contains(collection[col], term)]
            if include:
                hits = np.zeros(len(collection[col])).astype(bool)
            else:
                hits = np.ones(len(collection[col])).astype(bool)
            for term in include:
                hits |= str_contains(collection[col], term)
            collection = collection.loc[hits]
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
    @dashapp.callback([Output('tags', 'children'),
                       Output('tag-input', 'value')],
                      [Input('add-tag-button', 'n_clicks_timestamp'),
                       Input('remove-tag-button', 'n_clicks_timestamp'),
                       Input('hidden-data', 'children')],
                      [State('table', 'data'),
                       State('tag-input', 'value'),
                       State('tags', 'children')])
    def update_tags(add_time, remove_time, hidden_data, songs, tag, tags):
        conn = get_db()

        if tags:
            tags = json.loads(tags)
        else:
            # Load tags from the DB
            # Tags are stored as dict of booleans since json cannot do sets.
            collection = pd.read_json(hidden_data, orient='split')
            s = select([tag_table]).where((tag_table.c.user_id == g.user['id']) &
                                          (tag_table.c.song_id.in_(list(collection['ID']))))
            result = conn.execute(s)
            tags = {song_id:{} for song_id in collection['ID']}
            for row in result:
                tags[row['song_id']][row['tag']] = True

        if tag:
            # Canonize the tag by removing commas which
            # will be used in searching as logical and.
            tag = tag.lower().replace(',', '')

            # This callback gets called on page load,
            # so either time-stamp will be None until
            # button is pressed.
            if not add_time:
                add_time = 0
            if not remove_time:
                remove_time = 0

            # Unfortunately this function will fire when the hidden
            # data table is updated as well. This should only be
            # when the page first loads, and as long as it stays
            # that way it should be fine.
            
            if add_time > remove_time:
                rows = []
                for song in songs:
                    try:
                        exists = tags[song['ID']][tag]
                    except KeyError:
                        exists = False

                    if not exists:
                        # Add the tag to the DB.
                        rows.append({'user_id':g.user['id'], 'song_id':song['ID'], 'tag':tag})
                        # Update tags in the table.
                        tags[song['ID']][tag] = True

                conn.execute(tag_table.insert(), rows)
                
            if remove_time > add_time:
                song_IDs = []
                for song in songs:
                    # Remove the tags from the DB
                    song_IDs.append(song['ID'])
                    # And update tags in table.
                    tags[song['ID']][tag] = False
                conn.execute(tag_table.delete().where(
                    (tag_table.c.user_id == g.user['id']) &
                    (tag_table.c.tag == tag) &
                    (tag_table.c.song_id.in_(song_IDs)) )
                )
                
        return json.dumps(tags), ''

def register_playlist_controls(dashapp):
    @dashapp.callback(Output('save-feedback', 'children'),
                      [Input('save-playlist-button', 'n_clicks_timestamp'),
                       Input('add-playlist-button', 'n_clicks_timestamp'),
                       Input('remove-playlist-button', 'n_clicks_timestamp')],
                      [State('table', 'data'),
                       State('playlist-input', 'value')])
    def edit_playlist(save_time, add_time, remove_time, songs, playlist_name):
        if playlist_name and songs:
            # This callback gets called on page load,
            # so all time-stamps will be None until a
            # button is pressed.
            if not save_time:
                save_time = 0
            if not add_time:
                add_time = 0
            if not remove_time:
                remove_time = 0

            song_ids = [song['ID'] for song in songs]

            # Save playlist as
            if save_time > add_time and save_time > remove_time:
                snapshot, error = spotipy_fns.overwrite_playlist(playlist_name, song_ids)
                if snapshot:
                    time = dt.fromtimestamp(save_time / 1000)
                    return '{} saved at {}:{}:{:02d}.'.format(playlist_name, time.hour, time.minute, time.second)
                else:
                    return 'Error: {}'.format(error)

            # Add tracks to playlist
            elif add_time > save_time and add_time > remove_time:
                snapshot, error = spotipy_fns.add_tracks_to_playlist(playlist_name, song_ids)
                if snapshot:
                    time = dt.fromtimestamp(add_time / 1000)
                    return 'Tracks added to {} at {}:{}:{:02d}.'.format(playlist_name, time.hour, time.minute, time.second)
                else:
                    return 'Error: {}'.format(error)
            # Remove tracks from playlist
            elif remove_time > add_time and remove_time > add_time:
                snapshot, error = spotipy_fns.remove_tracks_from_playlist(playlist_name, song_ids)
                if snapshot:
                    time = dt.fromtimestamp(remove_time / 1000)
                    return 'Tracks removed from {} at {}:{}:{:02d}.'.format(playlist_name, time.hour, time.minute, time.second)
                else:
                    return 'Error: {}'.format(error)

            else:
                return ''
        else:
            return ''
