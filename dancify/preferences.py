#!/usr/bin/env python

from flask import Blueprint, g, redirect, request, session, url_for, render_template

from dancify import spotify_auth
from dancify.collections import track_features

defaults = {'collections': {'columns': ['Track', 'Artist', 'Album', 'Added'] } }

bp = Blueprint('preferences', __name__, url_prefix='/preferences')

@bp.route('/collections', methods = ['GET', 'POST'])
@spotify_auth.login_required
def collections():
    if request.method == 'POST':
        g.preferences['collections']['columns'] = request.form.getlist('columns')
        session['preferences'] = g.preferences
    
    return render_template('preferences/collections.html', track_features=track_features)

@bp.before_app_request
def load_preferences():
    # Should load various preferences from session, setting defaults if None
    # Store preferences in g
    prefs = session.get('preferences')
    if prefs is None:
        # Set some defaults for this new session.
        g.preferences = defaults
    else:
        g.preferences = prefs
