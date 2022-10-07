import logging
import re
import sys

import requests
import spotipy
from spotipy.oauth2 import SpotifyOAuth

TRACK_URL_REGEX = r"https:\/\/open\.spotify\.com\/track\/(?P<track_id>[\d\w]*)\?si=[\d\w]*"
URL_FMT_STRING = "spotify:track:{}"

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=sys.argv[1],
                                               client_secret=sys.argv[2],
                                               redirect_uri="http://localhost:9000",
                                               scope="playlist-modify-private"))


# This version has a different working principle. Locates tracks that are local only then prompts for a TRACK URL to replace the track.
# If no URL is given the option is provided to remove the track OR skip.
# If the URL is given and processed successfully the new track is added and the previous one removed.


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

            newurl = input("\nPLEASE PROVIDE A SUITABLE REPLACEMENT URL:")
            print("\nSEARCHING...")
            matdat = re.match(TRACK_URL_REGEX, newurl)
            if matdat is not None:
                track_id = matdat.group("track_id")
            else:
                action = input("Invalid URL given! (r)emove track, (e)xit or (s)kip:")
                if action == 'r':
                    update_list.append((totalidx, None))
                    continue
                elif action == 's':
                    continue
                elif action == 'e':
                    results = None
                    break
                else:
                    logging.error("INVALID ACTION GIVEN!")
            try:
                ser_results = sp.track(track_id)
            except Exception:
                logging.exception("Exception getting track info!")
                continue

            print("\nMatch found!\n")
            try:
                print_track_artist_information(ser_results)
                update_list.append((totalidx, ser_results["uri"]))
            except Exception:
                logging.exception("Could not add to update_list!")
                continue
            # except requests.exceptions.ReadTimeout:
            #     print("Request timed out!")
            #     continue
            # except requests.exceptions.HTTPError:
            #     logging.exception("HTTP Error")
            #     continue
            # except spotipy.exceptions.SpotifyException:
            #     logging.exception("SpotifyException")
            #     continue

    if results is not None and results.get('next'):
        results = sp.next(results)
    else:
        results = None

if not update_list:
    print("No updates required")
    exit()

y = input("Updates selected, backup and archive? [Y/y to continue]:")
if y in ['Y', 'y']:
    with open("backup.csv", 'w') as writefile:
        for tup in update_list:
            writefile.write(",".join([str(x) for x in tup]) + '\n')
    old_uids, new_uids = zip(*update_list)
    new_uids = [x for x in new_uids if x is not None]  # remove the Nones
    retry = True
    while retry:
        try:
            sp.playlist_remove_local_tracks(PL_ID, old_uids, plid["snapshot_id"])
        except requests.exceptions.ReadTimeout:
            retry = input("Type e to break out or enter to continue") != "e"
        else:
            break
    while retry:
        try:
            if new_uids:
                sp.playlist_add_items(PL_ID, new_uids)
        except requests.exceptions.ReadTimeout:
            retry = input("Type e to break out or enter to continue") != "e"
        else:
            break

# https://open.spotify.com/track/1Thv8uCYzyOFC7PME9J936?si=835f99ddd37a463d

# https: // open.spotify.com / track / 24hYr62Cz2iA3OOef8mykI?si=622cec1c676140cd
# '24hYr62Cz2iA3OOef8mykI'
