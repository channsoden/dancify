#!/usr/bin/env python
import dash
from flask.helpers import get_root_path

from dancify.vizualization import layout
from dancify.vizualization.callbacks import register_callbacks

def register_dashapp(app):
    # Meta tags for viewport responsiveness
    meta_viewport = {"name": "viewport", "content": "width=device-width, initial-scale=1, shrink-to-fit=no"}

    dashapp = dash.Dash(__name__,
                        server=app,
                        url_base_pathname='/viz/',
                        assets_folder=get_root_path(__name__) + '/vizualization/assets/',
                        meta_tags=[meta_viewport])

    dashapp.title = 'Dancify'
    dashapp.layout = layout.collection()
    register_callbacks(dashapp)

