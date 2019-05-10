#!/usr/bin/env python
import os, json, requests, base64, urllib

from flask import Flask, g, request, redirect, url_for, render_template

from . import spotipy_fns, dash_components

def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'dancify.sqlite'),
        SERVER_NAME='localhost:5000',
        )
    if test_config is None:
        # load the instance config when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        # dir alread exist
        pass
    
    from . import db
    db.init_app(app)

    from . import spotify_auth
    app.register_blueprint(spotify_auth.bp)
    with app.test_request_context():
        spotify_auth.init_authorizer()

    from . import preferences
    app.register_blueprint(preferences.bp)

    from . import collections
    app.register_blueprint(collections.bp)

    dash_components.register_dashapp(app)
    
    @app.route('/')
    def index():
        return render_template('welcome.html')
        
    return app


