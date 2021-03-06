from datetime import datetime as dt
import json

from flask import g

import pandas as pd
import numpy as np
from dash import no_update
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
from sqlalchemy.sql import select

from dancify import spotify_auth, spotipy_fns
from dancify.db import get_db, tag_table
from dancify.vizualization import elements, layout


def register_callbacks(dashapp):
    dashapp.config['suppress_callback_exceptions'] = False

    @spotify_auth.login_required
    @dashapp.callback([Output('description', 'children'),
                       Output('hidden-data', 'children'),
                       Output('preferences', 'children'),
                       Output('dynamic-content', 'children')],
                      [Input('url', 'pathname')])
    def load_collection(pathname):
        if not pathname:
            return (no_update, no_update, no_update, no_update, no_update)
        columns = g.preferences['collections']['columns']
        plf =  'Playlists' in columns
        # These two steps are expensive because they must wait for responses from Spotify.
        tracks, plid, description = parse_viz_path(pathname)
        collection_json = get_collection_data(tracks, playlist_feature=plf, plid=plid)
        dynamic_layout = layout.generate_dynamic_content(columns)
        return (description,
                collection_json,
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

    
def parse_viz_path(pathname):
    pathname = pathname.strip('/').split('/')[1:]
    plid = None
    if pathname[0] == 'library':
        track_dispenser = g.sp.current_user_saved_tracks()
        tracks = spotipy_fns.sort_tracks(track_dispenser, sort_key=None)
        desc = 'Your Spotify library.'
    elif pathname[0] == 'artist':
        # linkin park: localhost:5000/viz/artist/6XyY86QOPPrYVGvF9ch6wz
        artid = pathname[1]
        tracks = spotipy_fns.get_artist_tracks(artid)
        desc = spotipy_fns.describe_artist(artid)
    elif pathname[0] == 'album':
        # A Thousand Suns: localhost:5000/viz/album/113yjuFZEqkkbuLi4sEBxo
        albid = pathname[1]
        tracks = spotipy_fns.get_album_info(albid)
        desc = spotipy_fns.describe_album(albid)
    elif pathname[0] == 'playlist':
        uid, plid = pathname[1:]
        pl = g.sp.user_playlist(uid, playlist_id=plid)
        track_dispenser = pl['tracks']
        tracks = spotipy_fns.sort_tracks(track_dispenser, sort_key=None)
        desc = pl['description'] + ' [{} songs]'.format(pl['tracks']['total'])
    else:
        tracks = []
    desc = html.P(desc)
    return tracks, plid, desc

def get_collection_data(tracks, playlist_feature='False', plid = None):
    if not tracks:
        return {}
    collection = spotipy_fns.get_track_info(tracks)
    collection['Release'] = pd.to_datetime(collection['Release']).dt.year
    collection['Duration'] = collection['Duration'] / 1000 # convert to seconds
    collection['Tempo'] = collection['Tempo'].round()
    if playlist_feature:
        # This feature takes a long time to load, so only do it if you have to.
        if plid:
            exclude = [plid]
        else:
            exclude = []
        collection['Playlists'] = spotipy_fns.playlist_membership(collection['ID'],
                                                                  exclude = exclude)
    else:
        collection['Playlists'] = ['' for t in collection['ID']]
    return collection.to_json(date_format='iso', orient='split')
        
def register_slider(dashapp, hist):
    slider_id = hist+'_slider'

    @dashapp.callback([Output(slider_id, 'min'),
                       Output(slider_id, 'max'),
                       Output(slider_id, 'value'),
                       Output(slider_id, 'marks')],
                      [Input('hidden-data', 'children'),
                       Input('clear-filters-button', 'n_clicks')])
    def update_slider(json_data, nclicks):
        if not json_data:
            return (no_update, no_update, no_update, no_update)
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
                       Output('table', 'columns')],
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
            return (no_update, no_update)

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

        # Format floats
        for col in columns:
            if collection[col].dtype == float:
                collection[col] = ['{:0.2f}'.format(n) for n in collection[col]]
                
        columns = [{"name": c, "id": c, "presentation": "markdown"}
                   for c in columns]
                      
        return (collection.to_dict("rows"),
                columns)

    @dashapp.callback(Output('table', 'selected_rows'),
                      [Input('unmark-button', 'n_clicks')])
    def unmark_all(nclicks):
        return []

    field_outputs = [Output(field_id, 'value') for field_id in field_ids]
    @dashapp.callback(field_outputs,
                      [Input('clear-filters-button', 'n_clicks')])
    def clear_fields(nclicks):
        return tuple('' for fid in field_ids)
    
    @dashapp.callback(Output('selection-info', 'children'),
                      [Input('table', 'data'),
                       Input('table', 'selected_rows')])
    def update_selection_info(rows, selected_rows):
        if selected_rows:
            selection_info = '{} songs selected'.format(len(selected_rows))
            return selection_info
        elif rows:
            selection_info = '{} songs selected'.format(len(rows))
            return selection_info
        else:
            return no_update


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
            return no_update


def register_tag_controls(dashapp):
    @dashapp.callback([Output('tags', 'children'),
                       Output('tag-input', 'value')],
                      [Input('add-tag-button', 'n_clicks_timestamp'),
                       Input('remove-tag-button', 'n_clicks_timestamp'),
                       Input('hidden-data', 'children')],
                      [State('table', 'data'),
                       State('table', 'selected_rows'),
                       State('tag-input', 'value'),
                       State('tags', 'children')])
    def update_tags(add_time, remove_time, hidden_data, songs, selected_songs, tag, tags):
        if not hidden_data:
            return (no_update, no_update)
        if selected_songs:
            songs = [songs[i] for i in selected_songs]
        
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
                       State('table', 'selected_rows'),
                       State('playlist-input', 'value')])
    def edit_playlist(save_time, add_time, remove_time, songs, selected_songs, playlist_name):
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

            if selected_songs:
                song_ids = [songs[i]['ID'] for i in selected_songs]
            else:
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
