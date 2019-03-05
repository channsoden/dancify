#!/usr/bin/env python

from flask import Blueprint, g, redirect, request, session, url_for

from . import spotify_auth
from .collections import track_features

bp = Blueprint('preferences', __name__, url_prefix='/preferences')

@bp.route('/playlists', methods = ['GET', 'POST'])
@spotify_auth.login_required
def playlists():
    form = ['<form method="post">']
    col_checkbox = '<input type="checkbox" name="columns" value="{}" checked>'
    for c in track_features.keys():
        form.append( col_checkbox.format(c) )
    form.append( '</form>' )
    if request.method == 'POST':
        print(request.form.getlist('columns'))

    return ''.join(form)
