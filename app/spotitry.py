#!/usr/bin/env python
import sys

from api_fns import connect, get_playlist_tracks, get_features, print_track
from spotigraphs import feature_hist, path_distances
from song_graph import song_graph, song_distance

connect()

if len(sys.argv) > 1:
    uri = sys.argv[1].split(':')
    usridx = uri.index('user')
    listidx = uri.index('playlist')
    user = uri[usridx+1]
    playlist = uri[listidx+1]
else:
    user = '1218350953'
    user = '12159233923'
    playlist = '3NspcUmKkHovunKrd12y1i'
    playlist = 'spotify:user:1218350953:playlist:3NspcUmKkHovunKrd12y1i'
    playlist = 'spotify:user:12159233923:playlist:4BYu1SsCghZN7gatWp7OA0'
       
uris = get_playlist_tracks(user, playlist)
features = [get_features(uri) for uri in uris]

feature_hist(features, 'tempo')


graph = song_graph(features, min_dist=0, max_dist=3)

for x in range(1):
    playlist = graph.generate_playlist(duration=60)

    playlist_songs = graph.full_library[playlist] 
    for i, songA in enumerate(playlist_songs[:-1]):
        songB = playlist_songs[i+1]
        print_track(songA['uri'])
        print(song_distance(songA, songB))
    print_track(songB['uri'])

    print()
    
