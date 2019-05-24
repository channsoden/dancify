#!/usr/bin/env python
import os, logging

from flask import Flask, render_template, current_app

def create_app(config, debug=False, testing=False):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config)

    app.debug = debug
    app.testing = testing

    # Configure logging
    if not app.testing:
        logging.basicConfig(level=logging.INFO)

    from . import db
    db.init_engine(app)

    from . import spotify_auth
    app.register_blueprint(spotify_auth.bp)
    with app.test_request_context():
        spotify_auth.init_authorizer()

    from . import preferences
    app.register_blueprint(preferences.bp)

    from . import music_collections
    app.register_blueprint(music_collections.bp)

    from . import dash_components
    dash_components.register_dashapp(app)

    from . import experiments
    app.register_blueprint(experiments.bp)

    @app.route('/')
    def index():
        return render_template('welcome.html')

    # Add an error handler. This is useful for debugging the live application,
    # however, you should disable the output of the exception for production
    # applications.
    @app.errorhandler(500)
    def server_error(e):
        return """
        An internal error occurred: <pre>{}</pre>
        See logs for full stacktrace.
        """.format(e), 500
    
    return app


