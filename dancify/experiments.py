from html import escape

from flask import Blueprint, render_template, jsonify, request, g, url_for

from . import spotify_auth

bp = Blueprint('experiments', __name__)

@bp.route('/test', methods = ['GET'])
@spotify_auth.login_required
def test():
    return "Roger, Dodger."
