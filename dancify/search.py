from html import escape

from flask import Blueprint, render_template, request, url_for
from spotipy.exceptions import SpotifyException
import pandas as pd

from . import spotipy_fns
from . import spotify_auth

bp = Blueprint('search', __name__)

# Pandas will truncate long strings for pretty printing
# in your console etc, but this also applies to long html
# code in dataframes to be exported as html.
pd.set_option('display.max_colwidth', -1)

@bp.route('/search', methods = ['GET', 'POST'])
@spotify_auth.login_required
def search():
    results = ''
    if request.method == 'POST':
        try:
            results = spotipy_fns.search(**request.form)
        except SpotifyException:
            # No search query.
            pass
        results = search_table(results)
        print(results)
    return render_template('search.html', results=results)

columns = ['track', 'artists', 'owner', 'album', 'playlist', 'show', 'episode']
linkable = ['artists', 'playlist', 'album']
def search_table(results):
    qtype = list(results.keys())[0][:-1]
    if not results[qtype+'s']['items']:
        return 'No results found.'

    playlist_link = '<a href="'+url_for('/viz/')+'playlist/{}/{}" target="_blank">{}</a>'
    artist_link = '<a href="'+url_for('/viz/')+'artist/{}" target="_blank">{}</a>'
    album_link = '<a href="'+url_for('/viz/')+'album/{}" target="_blank">{}</a>'
    data = []
    for item in results[qtype+'s']['items']:
        if qtype == 'playlist':
            link = playlist_link.format(item['owner']['id'],
                                        item['id'],
                                        escape(item['name']))
            row = {'Playlist': link,
                   'Owner': escape(item['owner']['display_name'])}
        else:
            if qtype == 'artist':
                link = artist_link.format(item['id'],
                                          escape(item['name']))
                row = {capitalize(qtype): link}
            elif qtype == 'album':
                link = album_link.format(item['id'],
                                          escape(item['name']))
                row = {capitalize(qtype): link}
            else:
                row = {capitalize(qtype): escape(item['name'])}
            for prop in item.keys():
                if prop == 'artists':
                    # Multiple artists need to be unpacked from list.
                    artists = ', '.join([artist_link.format(a['id'],
                                                            escape(a['name']))
                                         for a in item['artists']])
                    row['Artist'] = artists
                elif prop == 'album':
                    link = album_link.format(item['album']['id'],
                                             escape(item['album']['name']))
                    row['Album'] = link
                elif (prop in columns and
                      prop != qtype):
                    row[capitalize(prop)] = escape(item[prop]['name'])
                else:
                    pass
        data.append(row)
    df = pd.DataFrame(data)
    colOrder = [capitalize(qtype)] + [col for col in df.columns
                                      if col != capitalize(qtype)]
    return df.to_html(index = False,
                      columns = colOrder,
                      table_id = 'search_results',
                      classes = 'search-table',
                      escape = False)

def capitalize(s):
    return s[0].upper() + s[1:]
