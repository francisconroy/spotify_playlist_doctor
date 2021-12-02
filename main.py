import sys
import urllib
import requests

import spotipy
from spotipy.oauth2 import SpotifyOAuth

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=sys.argv[1],
                                               client_secret=sys.argv[2],
                                               redirect_uri="http://localhost:9000",
                                               scope="playlist-modify-private"))


def get_name_artist(pl_item):
    name = pl_item['name']
    artist = pl_item["artists"][0]["name"]
    return name, artist


def print_track_artist_information(pl_item, tab=0):
    t = '\t'
    print(f"{t * tab}Track: {pl_item['name']}\n{t * tab}Album: {pl_item['album']['name']}\n{t * tab}Artists:")
    for artist in pl_item['artists']:
        print(f"{t * tab}\t{artist['name']}")


# results = sp.current_user_playlists(limit=50, offset=1)
PL_ID = "6kIBfB0XrNbrT6wsP5MHaw"
results = sp.playlist_items(PL_ID)
plid = sp.playlist(PL_ID)

update_list = []  # update list, old track, new track
while results:
    for i, pl_item in enumerate(results['items']):
        totalidx = i + int(results["offset"])
        if pl_item["is_local"]:
            print("\n")
            print(f"track {totalidx} of {results['total']}")
            print_track_artist_information(pl_item["track"])
            name, artist = get_name_artist(pl_item["track"])
            try:
                ser_results = sp.search(f"track:{name} artist:{artist}", limit=3, market="AU")
            except requests.exceptions.ReadTimeout:
                print("Request timed out!")
            tracks = ser_results.get("tracks", {}).get("items", [])
            if tracks:
                print("\nPOTENTIAL MATCHES FOUND!")
                for idx, sr in enumerate(tracks):
                    print(f"{idx}.")
                    ser_name, ser_artist = get_name_artist(sr)
                    print_track_artist_information(sr, 1)
                try:
                    intval = int(input("\nPlease select the track ID or [enter] to skip"))
                except ValueError:
                    continue
                update_list.append(totalidx, tracks[intval]["uri"])

    if results['next']:
        results = sp.next(results)
    else:
        results = None

y = input("Updates selected, backup and archive? [Y/y to continue]:")
if y in ['Y', 'y']:
    with open("backup.csv", 'w') as writefile:
        for tup in update_list:
            writefile.write(",".join([str(x) for x in tup]) + '\n')
    old_uids, new_uids = zip(*update_list)
    retry = True
    while retry:
        try:
            sp.playlist_remove_local_tracks(PL_ID, old_uids, plid["snapshot_id"])
        except requests.exceptions.ReadTimeout:
            retry = input("Type e to break out or enter to continue") != "e"
    while retry:
        try:
            sp.playlist_add_items(PL_ID, new_uids)
        except requests.exceptions.ReadTimeout:
            retry = input("Type e to break out or enter to continue") != "e"
