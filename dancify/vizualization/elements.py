from math import floor, ceil
import numpy as np
import pandas as pd
import dash_core_components as dcc
import dash_html_components as html
import dash_table as dt

color_scheme = {'offwhite': '#dedede',
                'lGray': '#858585',
                'mGray': '#535353',
                'dGray': '#404040',
                'green': '#1db954'}

filterables = ['Track', 'Artist', 'Album']
graphables = ['Duration', 'Release', 'Popularity', 'Danceability',
              'Energy', 'Tempo', 'Key', 'Loudness', 'Mode',
              'Valence', 'Acousticness', 'Instrumentalness',
              'Liveness', 'Speechiness']

# Text field input elements
fields = {name: dcc.Input(type='text', id=name+'_input')
          for name in filterables}
update_button = html.Button(id='update-button', n_clicks=0, children='Update')

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

slider_marks = {'font-size': 16, 'color': color_scheme['offwhite']}  

def mark_all(Min, Max, step):
    try:
        return {x: {'label': str(x), 'style': slider_marks}
                for x in range(Min, Max, step)}
    except:
        return {x: {'label': '{:.2f}'.format(x), 'style': slider_marks}
                for x in np.arange(Min, Max, step)}

sliders = {name: dcc.RangeSlider(id=name+'_slider',
                                 updatemode='mouseup',
                                 step=steps[name])
           for name in graphables}

# Graph elements
graph_font = {'size': 16, 'color': color_scheme['offwhite']}

graphs = {name: dcc.Graph(id=name+'_hist')
          for name in graphables}


def configure_slider(name, data):
    slider_min = floor(min(data)/step)*step
    slider_max = ceil(max(data)/step)*step
    value = [slider_min, slider_max],
    step = steps[name]
    marks = mark_all(slider_min, slider_max, step)
    return slider_min, slider_max, value, marks

def hist(name, xvalues):
    return {'data': [{'x': xvalues,
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
                       'paper_bgcolor': color_scheme['dGray']} }

# Table element
columns = filterables + graphables
filtered_table = dt.DataTable(id='table',
                              columns=[{"name": c, "id": c} for c in columns],
                              filtering = False,
                              sorting = False,
                              sorting_type = 'multi',
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
