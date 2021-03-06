from math import floor, ceil
import numpy as np
import pandas as pd
import dash_core_components as dcc
import dash_html_components as html
import dash_table as dt

from dancify.music_collections import track_features

color_scheme = {'offwhite': '#dedede',
                'lGray': '#858585',
                'mGray': '#535353',
                'dGray': '#404040',
                'green': '#1db954'}

grid_size = 350

filterables = ['Track', 'Artist', 'Album', 'Tags', 'Playlists']
graphables = ['Duration', 'Release', 'Popularity', 'Danceability',
              'Energy', 'Tempo', 'Key', 'Loudness', 'Mode',
              'Valence', 'Acousticness', 'Instrumentalness',
              'Liveness', 'Speechiness']

# Instructions
field_instructions = html.Div([html.P('Separate multiple search terms with commas. '
                                      'Terms beginning with “+” MUST be present in '
                                      'all tracks. Terms beginning with “-” CANNOT '
                                      'be present in any tracks (overrides “+”).'),
                               html.P('E.g. “blood, sugar, -sex, +magik” finds all '
                                      'tracks containing “magik”, but not “sex”, '
                                      'and either “blood” or “sugar”.')])

# Text field input elements
fields = {name: dcc.Input(type='text', id=name+'_input',
                          placeholder = 'Filter by {}'.format(name),
                          style = {'font-size': 22,
                                   'width': grid_size,
                                   'color': color_scheme['dGray']})
          for name in filterables}

# Sort order menu
sort_menu = dcc.Dropdown(id='sort-order',
                         options = [{'label':f, 'value': f} for f in track_features],
                         value='Added',
                         clearable=False)
sort_toggle = dcc.RadioItems(id='sort-toggle',
                             options=[{'label': 'Sort Ascending', 'value': True},
                                      {'label': 'Sort Descending', 'value': False}],
                             value=True,
                             labelStyle={'display': 'inline-block'},
                             className='button-like',
                             style = {'margin': 5})

# Controls for adding tags
add_tag_button = html.Button(id='add-tag-button', n_clicks=0, children='Add Tag',
                             title = 'Add tag to selected tracks',
                             style = {'margin': 5})
remove_tag_button = html.Button(id='remove-tag-button', n_clicks=0, children='Remove Tag',
                                title = 'Remove tag from selected tracks',
                                style = {'margin': 5})
tag_field = dcc.Input(type='text', id='tag-input', size=30,
                      placeholder = 'Enter tag',
                      style = {'font-size': 22,
                               'width': grid_size,
                               'color': color_scheme['dGray']})

# Controls for editing playlists
save_playlist_button = html.Button(id='save-playlist-button', n_clicks=0, children='Save as',
                                   title = 'Save selected tracks as a playlist (will overwrite)',
                                   style = {'margin': 4})
add_playlist_button = html.Button(id='add-playlist-button', n_clicks=0, children='Add',
                                  title = 'Add selected tracks to playlist',
                                  style = {'margin': 4})
remove_playlist_button = html.Button(id='remove-playlist-button', n_clicks=0, children='Remove',
                                     title = 'Remove selected tracks from playlist',
                                     style = {'margin': 4})
playlist_field = dcc.Input(type='text', id='playlist-input',
                           value='Dancify',
                           style = {'font-size': 22,
                                    'width': grid_size,
                                    'color': color_scheme['dGray']})
save_feedback = html.Div([], id='save-feedback',
                         style={'font-size':10})

# Slider elements
steps = {'Duration': 15,
         'Release': 1, # Need to coerce release dates into year only.
         'Popularity': 5,
         'Danceability': .05,
         'Energy': .05,
         'Tempo': 10,
         'Key': 1,
         'Loudness': 5,
         'Mode': 1,
         'Valence': .05,
         'Acousticness': .05,
         'Instrumentalness': .05,
         'Liveness': .05,
         'Speechiness': .05}

def mark_all(Min, Max, step):
    if (Max - Min) / step > 12:
        slider_marks = {'font-size': 12,
                        'color': color_scheme['offwhite'],
                        'writing-mode': 'vertical-rl'}
    elif (Max - Min) / step > 8:
        slider_marks = {'font-size': 16,
                        'color': color_scheme['offwhite'],
                        'writing-mode': 'vertical-rl'}
    else:
        slider_marks = {'font-size': 16,
                        'color': color_scheme['offwhite']}
    try:
        return {x: {'label': str(x), 'style': slider_marks}
                for x in range(Min, Max+int(step/2), step)}
    except:
        return {x: {'label': '{:.2f}'.format(x), 'style': slider_marks}
                for x in np.arange(Min, Max+step/2, step)}

sliders = {name: dcc.RangeSlider(id=name+'_slider',
                                 updatemode='mouseup',
                                 step=steps[name])
           for name in graphables}

# Graph elements
graph_font = {'size': 16, 'color': color_scheme['offwhite']}

graphs = {name: dcc.Graph(id=name+'_hist')
          for name in graphables}


def configure_slider(name, data):
    step = steps[name]
    slider_min = floor(min(data)/step)*step
    slider_max = ceil(max(data)/step)*step
    value = [slider_min, slider_max]
    marks = mark_all(slider_min, slider_max, step*2)
    return slider_min, slider_max, value, marks

def hist(name, xvalues):
    return {'data': [{'x': xvalues,
                      'name': name,
                      'type': 'histogram',
                      'marker': {'color': color_scheme['green']} }],
            'layout': {'autosize':False,
                       'width': grid_size,
                       'height': grid_size,
                       'yaxis': {'title': name,
                                 'titlefont': {'size': 20,
                                               'color': color_scheme['offwhite']},
                                 'ticks': '',
                                 'showticklabels': False},
                       'xaxis': {'tickcolor': color_scheme['offwhite'],
                                 'tickfont': graph_font },
                       'plot_bgcolor': color_scheme['mGray'],
                       'paper_bgcolor': color_scheme['mGray']} }

# Table element
columns = filterables + graphables
# It would be nice to remove the hot pink cell selection in the future.
# This doesn't seem to work, unfortunately.
#style_data_conditional = [{'if': {'state':'focused'}},
#                          {'backgroundColor': color_scheme['green']}],
# Would be even better to remove the cell selection entirely so
# that you don't have to double click links.
filtered_table = dt.DataTable(id='table',
                              columns=[{"name": c, "id": c} for c in columns],
                              row_selectable = 'multi',
                              page_action = 'native',
                              page_size = 25,
                              style_table = {'overflowX': 'scroll'},
                              style_as_list_view = True,
                              style_cell = {'minWidth': '0px',
                                            'maxWidth': '250px',
                                            'whiteSpace': 'no-wrap',
                                            'overflow': 'auto',
                                            'textOverflow': 'ellipsis',
                                            'backgroundColor': color_scheme['dGray'],
                                            'color': color_scheme['offwhite']},
                              style_header = {'textAlign': 'left',
                                              'backgroundColor': color_scheme['dGray'],
                                              'color': color_scheme['lGray']},

                              css = [{'selector': '.dash-cell div.dash-cell-value',
                                      'rule': 'display: inline; white-space: inherit; overflow: inherit; text-overflow: inherit;'}]
                              )

selection_feedback = html.Div([],
                              id='selection-info',
                              className='button-like',
                              style = {'width': '325px',
                                       'text-align': 'center'})
unmark_button = html.Button(id='unmark-button', n_clicks=0, children='Unmark All',
                            title = 'Select all tracks by removing all check marks',
                            style = {'margin': 5})
clear_filters_button = html.Button(id='clear-filters-button', n_clicks=0, children='Clear Filters',
                                   title = 'Remove all filters',
                                   style = {'margin': 5})
