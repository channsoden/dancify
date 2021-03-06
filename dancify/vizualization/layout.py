from flask import g
import dash_core_components as dcc
import dash_html_components as html

from dancify.vizualization import elements

def collection():
    content = [dcc.Location(id='url', refresh=False),
               html.Div(id='description'),
               html.Div(id='dynamic-content')]

    selection_panel = html.Div([elements.selection_feedback,
                                elements.unmark_button,
                                elements.clear_filters_button],
                               id='selection-panel')
    
    
    sort_panel = html.Div([elements.sort_toggle,
                           elements.sort_menu],
                          id='sort-panel')
    
    tag_panel = html.Div([elements.add_tag_button,
                          elements.remove_tag_button,
                          elements.tag_field],
                         id='tag-panel')

    playlist_panel = html.Div([elements.save_playlist_button,
                               elements.add_playlist_button,
                               elements.remove_playlist_button,
                               elements.playlist_field,
                               elements.save_feedback],
                              id='playlist-panel')
    
    controls = html.Div([selection_panel, sort_panel, tag_panel, playlist_panel],
                        id='controls',
                        className = 'graphGrid',
                        style = {'marginBottom': 10})
    content.append( controls )
    
    content.append( elements.filtered_table )
    content.append( html.Div(id='hidden-data', style={'display': 'none'}) )
    content.append( html.Div(id='preferences', style={'display': 'none'}) )
    content.append( html.Div(id='tags', style={'display': 'none'}) )
    hidden_components = list(elements.fields.values()) + \
                        list(elements.sliders.values()) + \
                        list(elements.graphs.values()) + \
                        [html.Div([], id='null')] # This is a null container for buttons that have no output.
    content.append( html.Div(hidden_components,
                             id='hidden-components', style={'display': 'none'}) )

    return html.Div(content)

def generate_dynamic_content(columns):
    fields = [col for col in columns if col in elements.filterables]
    field_container = [html.Div([field+'  ',
                                 elements.fields[field]],
                                id = field+'_container',
                                style = {'padding': 5})
                       for field in fields]
    field_div = html.Div([html.Div(field_container, id = 'fields',
                                   className = 'graphGrid'),
                          elements.field_instructions])
    
    graphs = [col for col in columns if col in elements.graphables]
    graph_container = [html.Div([elements.graphs[graph],
                                 html.Div([elements.sliders[graph]],
                                          style = {'width': 275,
                                                   'margin-left': 50,
                                                   'margin-right':25})],
                                id = graph+'_container',
                                style = {'marginBottom': 30})
                       for graph in graphs]
    graph_div = html.Div(graph_container, id = 'graphs',
                         style = {'marginBottom':75},
                         className = 'graphGrid')
    
    return (field_div, graph_div)

def init_fields(columns):
    fields = []
    for field in columns:
        container_id = field+'_container'
        input_id = field+'_input'
        pair = html.Div([field+'  ', dcc.Input(type='text', id=input_id)],
                        id = container_id)
        fields.append(pair)
        fields.append(html.Br())
    fields.append(  )

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

    

    
