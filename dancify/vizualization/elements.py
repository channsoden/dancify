from math import floor, ceil
import numpy as np
import pandas as pd
import dash_core_components as dcc

color_scheme = {'offwhite': '#dedede',
                'lGray': '#858585',
                'mGray': '#535353',
                'dGray': '#404040',
                'green': '#1db954'}

graphs = ['Duration', 'Release', 'Popularity', 'Danceability',
         'Energy', 'Tempo', 'Key', 'Loudness', 'Mode',
         'Valence', 'Acousticness', 'Instrumentalness',
         'Liveness', 'Speechiness']

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

slider_marks = {'font-size': 16, 'color': color_scheme['offwhite']}  

def mark_all(Min, Max, step):
    try:
        return {x: {'label': str(x), 'style': slider_marks}
                for x in range(Min, Max, step)}
    except:
        return {x: {'label': '{:.2f}'.format(x), 'style': slider_marks}
                for x in np.arange(Min, Max, step)}

def slider(name, data):
    step = steps[name]
    slider_min = floor(min(data)/step)*step
    slider_max = ceil(max(data)/step)*step
    
    return dcc.RangeSlider(id=name+'_slider',
                           updatemode='mouseup',
                           min=slider_min,
                           max=slider_max,
                           step=step,
                           value=[slider_min, slider_max],
                           marks=mark_all(slider_min, slider_max, step))

graph_font = {'size': 16, 'color': color_scheme['offwhite']}

def hist(name, xvalues):
    return dcc.Graph(figure={'data': [{'x': xvalues,
                                       'name': name,
                                       'type': 'histogram',
                                       'marker': {'color': color_scheme['green']} }],
                             'layout': {'autosize':False,
                                        'width': 500,
                                        'height': 500,
                                        'yaxis': {'title': name,
                                                  'titlefont': {'size': 20,
                                                                'color': color_scheme['offwhite']},
                                                  'ticks': '',
                                                  'showticklabels': False},
                                        'xaxis': {'tickcolor': color_scheme['offwhite'],
                                                  'tickfont': graph_font },
                                        'plot_bgcolor': color_scheme['dGray'],
                                        'paper_bgcolor': color_scheme['dGray']} })

table_style = {'filtering': False,
               'sorting': False,
               'sorting_type': 'multi',
               'style_table': {'overflowX': 'scroll'},
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
               'pagination_mode': 'fe',
               'pagination_settings': {'displayed_pages': 1,
                                       'current_page': 0,
                                       'page_size': 50},
               'navigation': 'page',
               'css': [{'selector': '.dash-cell div.dash-cell-value',
                        'rule': 'display: inline; white-space: inherit; overflow: inherit; text-overflow: inherit;'}]}
