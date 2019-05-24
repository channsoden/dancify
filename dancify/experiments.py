from flask import Blueprint

from . import spotipy_fns
from . import spotify_auth

bp = Blueprint('experiments', __name__)

tracks = ['5qYEM2wsezbb37E786zIxm', '0a4Nn45rgxlUaP3IiUILXD', '5boPxQ6Eu3jEK94mMe5X1r']

@bp.route('/test')
@spotify_auth.login_required
def test():
    return 'success'
#str(spotipy_fns.playlist_membership(tracks, exclude = ['3hszEgAE2s6cTVrp35n2nm']))

