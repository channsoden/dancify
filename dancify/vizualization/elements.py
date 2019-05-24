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
                          style = {'font-size': 22,
                                   'width': 400,
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
                             style = {'margin': 5})
remove_tag_button = html.Button(id='remove-tag-button', n_clicks=0, children='Remove Tag',
                                style = {'margin': 5})
tag_field = dcc.Input(type='text', id='tag-input', size=30,
                          style = {'font-size': 22,
                                   'width': 400,
                                   'color': color_scheme['dGray']})

# Controls for editing playlists
save_playlist_button = html.Button(id='save-playlist-button', n_clicks=0, children='Save as',
                                   style = {'margin': 5})
add_playlist_button = html.Button(id='add-playlist-button', n_clicks=0, children='Add',
                                   style = {'margin': 5})
remove_playlist_button = html.Button(id='remove-playlist-button', n_clicks=0, children='Remove',
                                   style = {'margin': 5})
playlist_field = dcc.Input(type='text', id='playlist-input',
                           value='Dancify',
                           style = {'font-size': 22,
                                    'width': 400,
                                    'color': color_scheme['dGray']})

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
                       'width': 400,
                       'height': 400,
                       'yaxis': {'title': name,
                                 'titlefont': {'size': 20,
                                               'color': color_scheme['offwhite']},
                                 'ticks': '',
                                 'showticklabels': False},
                       'xaxis': {'tickcolor': color_scheme['offwhite'],
                                 'tickfont': graph_font },
                       'plot_bgcolor': color_scheme['dGray'],
                       'paper_bgcolor': color_scheme['dGray']} }

# Table element
columns = filterables + graphables
filtered_table = dt.DataTable(id='table',
                              columns=[{"name": c, "id": c} for c in columns],
                              filtering = False,
                              sorting = False,
                              row_selectable = False,
                              style_table = {'overflowX': 'scroll'},
                              style_as_list_view = True,
                              style_cell = {'minWidth': '0px',
                                            'maxWidth': '250px',
                                            'whiteSpace': 'no-wrap',
                                            'overflow': 'hidden',
                                            'textOverflow': 'ellipsis',
                                            'backgroundColor': color_scheme['dGray'],
                                            'color': color_scheme['offwhite']},
                              style_header = {'backgroundColor': color_scheme['dGray'],
                                              'color': color_scheme['lGray']},
                              pagination_mode = 'fe',
                              pagination_settings = {'displayed_pages': 1,
                                                     'current_page': 0,
                                                     'page_size': 50},
                              navigation = 'page',
                              css = [{'selector': '.dash-cell div.dash-cell-value',
                                      'rule': 'display: inline; white-space: inherit; overflow: inherit; text-overflow: inherit;'}]
                              )
