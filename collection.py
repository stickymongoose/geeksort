#!/usr/bin/env python
# -*- coding: utf-8 -*-
import xml.etree.ElementTree as ET
import fetch
import os
import errno
import functools
import pathlib
from constants import *
#import concurrent.futures

# return collection for any user, but wait 2 seconds and retry if error. 10 total attempts.

def init():
    try:
        os.mkdir(pathlib.Path(CACHE_DIR))
    except OSError:
        pass

    try:
        os.mkdir(pathlib.Path(CACHE_DIR) / "pics")
    except OSError:
        pass


@functools.lru_cache(maxsize=None)
def get_collection(user):
    filename = pathlib.Path(CACHE_DIR) / "collection_{}.xml".format(user)
    return fetch.get(filename, lambda: ET.parse(filename) , API_COLL_URL.format(id=user))


@functools.lru_cache(maxsize=5)
def game_from_db(filename, id):
    root = ET.parse(filename)
    return root.find("./item[@id='{}']".format(id))


@functools.lru_cache(maxsize=5)
def get_game(user, id):
    gamecol = get_collection(user)
    gameids = [el.get("objectid") for el in gamecol.findall("./item")]

    gameidstring = ",".join(sorted(gameids))


    filename = pathlib.Path(CACHE_DIR) / "games_{}.xml".format(user)
    gamedata = fetch.get(filename, lambda: game_from_db(filename, id), API_GAME_URL.format(id=gameidstring))
    return gamedata


def validate_file(file):
    if not os.path.isfile(file):
        raise FileNotFoundError( errno.ENOENT, os.strerror(errno.ENOENT), file )


def url_to_local(imgurl):
    return pathlib.Path(CACHE_DIR) / "pics" / imgurl[imgurl.rfind("/")+1:]


def get_img_specific(imgurl):
    localimg = url_to_local(imgurl) # trim out just the file name
    # ensure the image exists, but don't use any part of it
    fetch.get(localimg, lambda: validate_file(localimg), imgurl)
    return localimg


def get_img(user, id):
    try:
        root = get_collection(user)
        thumb = root.find("./item[@objectid='{}']/version/item/thumbnail".format(id))
        if thumb is None:
            root = get_game(user, id)
            thumb = root.find("./thumbnail")
            if thumb is None:
                raise Exception()

        return get_img_specific(thumb.text)
    except Exception as e:
        print(e)
        return "pics/noimage.jpg"


if __name__ == "__main__":

    print(get_img("jadthegerbil", 114903))
#
#    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
#        pile = {executor.submit(gamedata.get, g, 1.2): g for g in gameids}
#        for g in concurrent.futures.as_completed(pile):
#            gid = pile[g]
#            try:
#                #print("Finished:",  g.result(),  id)
#                print("<--", gid)
#            except Exception as e:
#                print('%r generated an exception: %s' % (id, e))
    print("Done.")
    #gamedata.getids(gameids)
    #getimgs("jadthegerbil", g)


##    versionpics = [thmb.text for thmb in root.findall("./item/version/item/thumbnail")]
##    vlabels = [ "pics/" + img[ img.rfind("/")+1: ] for img in versionpics ]
##    v = list(zip(versionpics, vlabels))
##    for ituple in v:
##        print(ituple)
##        fetch.get(ituple[1], lambda: open(ituple[1],"rb"), ituple[0])
##
##    gameids = [el.get("objectid") for el in root.findall("./item")]
##    for g in gameids:
##        game.get(g)


