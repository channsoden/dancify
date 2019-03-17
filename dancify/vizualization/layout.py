import numpy as np

import dash_core_components as dcc
import dash_html_components as html

example_layout = html.Div([
    html.H1('Collection'),
    dcc.Dropdown(
        id='my-dropdown',
        options=[
            {'label': 'Coke', 'value': 'COKE'},
            {'label': 'Tesla', 'value': 'TSLA'},
            {'label': 'Apple', 'value': 'AAPL'}
        ],
        value='COKE'
    ),
    dcc.Graph(id='my-graph')
], style={'width': '500'})


layout = html.Div([dcc.Location(id='url', refresh=False),
                   html.Div(id='page-content')
])



    
