import sys
import urllib

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
results = sp.playlist_items(PL_ID, limit=3)  # TODO remove limit

update_list = []  # update list, old track, new track
while results:
    for i, pl_item in enumerate(results['items']):
        if pl_item["is_local"]:
            print("\n")
            print_track_artist_information(pl_item["track"])
            name, artist = get_name_artist(pl_item["track"])
            ser_results = sp.search(f"track:{name} artist:{artist}", limit=3)
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
                update_list.append((i+int(results["offset"]), tracks[intval]["uri"]))

    results = {"next":None}  # TODO remove this testing hack

    if results['next']:
        results = sp.next(results)
    else:
        results = None

y = input("Updates selected, backup and archive? [Y/y to continue]:")
if y in ['Y', 'y']:
    with open("backup.csv", 'w') as writefile:
        for tup in update_list:
            writefile.write(",".join([str(x) for x in tup])+'\n')
    old_uids, new_uids = zip(*update_list)
    result = sp.playlist_add_items(PL_ID, new_uids)
    sp.playlist_remove_local_tracks(PL_ID, old_uids, result["snapshot_id"])
