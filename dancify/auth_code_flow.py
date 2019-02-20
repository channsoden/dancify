#!/usr/bin/env python
import spotipy
import spotipy.util as util

scope = 'user-library-read'

username = '' # '12159233923'

token = util.prompt_for_user_token(username, scope, redirect_uri = 'http://localhost/')

if token:
    sp = spotipy.Spotify(auth=token)
    results = sp.current_user_saved_tracks()
    for item in results['items']:
        track = item['track']
        print(track['name'] + ' - ' + track['artists'][0]['name'])
else:
    print("Can't get token for", username)

