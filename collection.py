#!/usr/bin/env python
# -*- coding: utf-8 -*-
import xml.etree.ElementTree as ET
import fetch
import os
import errno
import functools
from constants import *
#import concurrent.futures

# return collection for any user, but wait 2 seconds and retry if error. 10 total attempts.



@functools.lru_cache(maxsize=None)
def getcollection(user):
    filename = "collection_{}.xml".format(user)
    return fetch.get(filename, lambda: ET.parse(filename) , API_COLL_URL.format(id=user))

@functools.lru_cache(maxsize=5)
def gamefromdb(filename,  id):
    root = ET.parse(filename)
    return root.find("./item[@id='{}']".format(id))

@functools.lru_cache(maxsize=5)
def getgame(user, id):
    gamecol = getcollection(user)
    gameids = [el.get("objectid") for el in gamecol.findall("./item")]

    gameidstring = ",".join(sorted(gameids))


    filename = "games_{}.xml".format(user)
    gamedata = fetch.get(filename, lambda: gamefromdb(filename, id), API_GAME_URL.format(id=gameidstring))
    return gamedata

def validatefile(file):
    if not os.path.isfile(file):
        raise FileNotFoundError( errno.ENOENT, os.strerror(errno.ENOENT), file )

def urltolocal(imgurl):
    return "pics/" + imgurl[ imgurl.rfind("/")+1:]

def getimgspecific(imgurl):
    localimg = urltolocal(imgurl) # trim out just the file name
    # ensure the image exists, but don't use any part of it
    fetch.get(localimg, lambda: validatefile(localimg), imgurl)
    return localimg

def getimg(user, id):
    try:
        root = getcollection(user)
        thmb = root.find("./item[@objectid='{}']/version/item/thumbnail".format(id))
        if thmb == None:
            root = getgame(user, id)
            thmb = root.find("./thumbnail")
            if thmb == None:
                raise Exception()

        return getimgspecific(thmb.text)
    except Exception as e:
        print(e)
        return "pics/noimage.jpg"

if __name__ == "__main__":

    print(getimg("jadthegerbil", 114903))
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


