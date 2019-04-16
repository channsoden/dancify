from flask import g
import dash_core_components as dcc
import dash_html_components as html
import dash_table as dt

from dancify.vizualization import elements

def collection():
    content = [dcc.Location(id='url', refresh=False),
               html.Div([html.A("Logout", href='/auth/logout'),
                         '   ',
                         html.A("Playlists", href='/playlists'),
                         '   ',
                         html.A("Library", href='/viz/library'),
                         '   ',
                         html.A("Preferences", href='/preferences/collections')],
                        style = {'text-align': 'right'}),
               html.Div(id='page-header')]

    content.append( html.Div(id='dynamic-content') )
    
    content.append( html.Div(id='hidden-data', style={'display': 'none'}) )
    content.append( html.Div(id='preferences', style={'display': 'none'}) )

    return html.Div(content)

def generate_dynamic_content(columns, df):
    fields = [col for col in columns if col in elements.fields]
    graphs = [col for col in columns if col in elements.graphs]
    table = dt.DataTable(id='table',
                         columns=[{"name": c, "id": c} for c in elements.graphs],
                         data=df.to_dict("rows"),
                         **elements.table_style)
    dynamics = (init_fields(fields), init_graphs(graphs, df), table)
    return fields, graphs, dynamics

def init_fields(columns):
    fields = []
    for field in columns:
        container_id = field+'_container'
        input_id = field+'_input'
        pair = html.Div([field+'  ', dcc.Input(type='text', id=input_id)],
                        id = container_id)
        fields.append(pair)
        fields.append(html.Br())
    fields.append( html.Button(id='update-button', n_clicks=0, children='Update') )

    return html.Div(fields, id = 'fields')

def init_graphs(columns, df):
    graphs = []
    for graph in columns:
        pair = html.Div([html.Div([elements.hist(graph, df[graph])], id=graph+'_hist'),
                         html.Div([elements.slider(graph, df[graph])], id=graph+'_slider'),
                         html.Br() ],
                        style = {'align': 'center'})
        graphs.append(pair)

    return html.Div(graphs, id = 'graphs') # , className = 'graphgrid'

    

    
