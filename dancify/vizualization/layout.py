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

    graphs = []
    for graph in elements.graphs:
        pair = html.Div([html.Div(id=graph+'_hist',
                                  style = {'background': elements.color_scheme['dGray'],
                                           'align': 'center'}),
                         html.Div(id=graph+'_slider',
                                  style = {'align': 'center'}),
                         html.Br() ],
                        style = {'align': 'center'},
                        className='five columns')
        graphs.append(pair)

    content.append( html.Div(graphs, id = 'graphs', className = 'twelve columns') )

    table = dt.DataTable(id='table',
                         columns=[{"name": c, "id": c} for c in elements.graphs],
                         **elements.table_style)
    content.append( html.Div([table], className = 'twelve columns') )
    
    content.append( html.Div(id='hidden-data', style={'display': 'none'}) )
    content.append( html.Div(id='preferences', style={'display': 'none'}) )

    return html.Div(content)

