#!/usr/bin/env python

from flask import Blueprint, g, redirect, request, session, url_for, render_template
from sqlalchemy.sql import select

from dancify import spotify_auth
from dancify.music_collections import track_features
from dancify.db import get_db, preferences_table

defaults = {'collections': {'columns': ['Track', 'Artist', 'Tags', 'Danceability', 'Energy', 'Tempo', 'Valence'] } }

bp = Blueprint('preferences', __name__, url_prefix='/preferences')

@bp.route('/collections', methods = ['GET', 'POST'])
@spotify_auth.login_required
def collections():
    if request.method == 'POST':
        g.preferences['collections']['columns'] = request.form.getlist('columns')
        conn = get_db()
        collection_code = encode_preferences(g.preferences['collections']['columns'], list(track_features.keys()))
        u = preferences_table.update().\
            where(preferences_table.c.user_id == g.user['id']).\
            values(collections=collection_code)
        conn.execute(u)
    
    return render_template('preferences/collections.html', track_features=track_features)

@bp.before_app_request
def load_preferences():
    # Load preferences from DB, setting defaults if necessary.
    # Store preferences in g
    conn = get_db()
    s = select([preferences_table]).where(preferences_table.c.user_id == g.user['id'])
    result = conn.execute(s).fetchone()

    if result is None:
        g.preferences = defaults
        collection_code = encode_preferences(defaults['collections']['columns'], list(track_features.keys()))
        conn.execute(preferences_table.insert(), {'user_id':g.user['id'], 'collections':collection_code})
    else:
        prefs = {'collections': {'columns': decode_preferences(result['collections'], list(track_features.keys())) } }
        g.preferences = prefs

def encode_preferences(prefs, order):
    binary = []
    for setting in order:
        if setting in prefs:
            binary.append('1')
        else:
            binary.append('0')
    binstring = ''.join(binary)
    return int(binstring, 2)

def decode_preferences(intcode, order):
    intcode = int(intcode)
    prefs = []
    binstring = bin(intcode)[2:]
    for val, setting in zip(binstring[::-1], order[::-1]):
        if int(val):
            prefs.append(setting)
    return prefs[::-1]
