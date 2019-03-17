from datetime import datetime as dt

from flask import g

import pandas_datareader as pdr
from dash.dependencies import Input
from dash.dependencies import Output
import dash_core_components as dcc
import dash_html_components as html
import dash_table as dt

from dancify import spotify_auth, spotipy_fns

def hist(id, xvalues):
    graph = dcc.Graph(id=id,
                      figure={'data': [{'x': xvalues,
                                        'name': id,
                                        'type': 'histogram'}],
                              'layout': {'autosize':False,
                                         'width': 500,
                                         'height': 500,
                                         'yaxis': {'title': id}}})
    return graph

color_scheme = {'offwhite': '#dedede',
                'lGray': '#858585',
                'mGray': '#535353',
                'dGray': '#404040',
                'green': '#1db954'}

table_style = {'style_table': {'overflowX': 'scroll'},
               'style_as_list_view': True,
               'style_cell': {'minWidth': '0px',
                              'maxWidth': '250px',
                              'whiteSpace': 'no-wrap',
                              'overflow': 'hidden',
                              'textOverflow': 'ellipsis',
                              'backgroundColor': color_scheme['dGray'],
                              'color': color_scheme['offwhite']},
               'style_header': {'backgroundColor': color_scheme['dGray'],
                                'color': color_scheme['lGray']},
               'css': [{'selector': '.dash-cell div.dash-cell-value',
                        'rule': 'display: inline; white-space: inherit; overflow: inherit; text-overflow: inherit;'}]}


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
        
    return collection_name, tracks
    
def register_callbacks(dashapp):
    @spotify_auth.login_required
    @dashapp.callback(Output('page-content', 'children'),
              [Input('url', 'pathname')])
    def display_page(pathname):
        collection_name, collection = get_collection(pathname)
        columns = g.preferences['collections']['columns']

        nograph = ['ID', 'Track', 'Artist', 'Album', 'Added', 'Time Signature']
        hists = [col for col in columns if col not in nograph]
        hists = html.Div([hist(col, collection[col])
                          for col in hists])

        table = dt.DataTable(id='table',
                             columns=[{"name": i, "id": i} for i in columns],
                             data=collection.to_dict("rows"),
                             **table_style)

        
        
        return html.Div([hists, table])
