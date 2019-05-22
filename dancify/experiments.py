from flask import Blueprint

from . import spotipy_fns
from . import spotify_auth

bp = Blueprint('experiments', __name__)

@bp.route('/test')
@spotify_auth.login_required
def test():
    return 'Success'
