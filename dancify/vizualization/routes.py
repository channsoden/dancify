#!/usr/bin/env python
from flask import Blueprint, g, redirect, request, session, url_for, render_template

import dash
import dash_core_components as dcc
import dash_html_components as html

from . import spotify_auth

def register_dashapps(app):
    from dancify.vizualization.layout import layout
    from dancify.vizualization.callbacks import register_callbacks

    # Meta tags for viewport responsiveness
    meta_viewport = {"name": "viewport", "content": "width=device-width, initial-scale=1, shrink-to-fit=no"}

    
    collection_viz = dash.Dash(__name__,
                               server=app,
                               url_base_pathname='/viz/<arbitrary>',
                               meta_tags=[meta_viewport])

    collection_viz.title = 'Collection Viz'
    collection_viz.layout = layout
    register_callbacks(collection_viz)
