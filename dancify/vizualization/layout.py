from flask import g
import dash_core_components as dcc
import dash_html_components as html

from dancify.vizualization import elements


def collection():
    content = [dcc.Location(id='url', refresh=False),
               html.Div(id='page-header')]

    for graph in elements.graphs:
        content.append( html.Div(id=graph+'_hist') )
        content.append( html.Div(id=graph+'_slider') )

    content.append( html.Div(id='table') )
    content.append( html.Div(id='hidden-data', style={'display': 'none'}) )
    content.append( html.Div(id='preferences', style={'display': 'none'}) )

    return html.Div(content)

