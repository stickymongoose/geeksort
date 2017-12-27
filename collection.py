#!/usr/bin/env python
# -*- coding: utf-8 -*-
import xml.etree.ElementTree as ET
import fetch
import os
import errno
import functools
import pathlib
import time
from constants import *
import queue
import threading
#import concurrent.futures

_q = queue.Queue()
_q_continue = True
_q_blocked = False
_queued_cnt = 0
_threads = []

_collection_xml = None
_game_xml = None

THREAD_COUNT = 3

def init():
    try:
        os.makedirs(pathlib.Path(CACHE_DIR) / "pics", exist_ok=True)
    except Exception:
        # assumption, exist_ok means we won't be getting OSError 17 (EEXIST)
        raise

    for i in range(THREAD_COUNT):
        t = threading.Thread(target=pump_queue, name="Fetcher {}".format(i))
        t.start()
        _threads.append(t)

def shutdown():
    global _q_continue
    _q_continue = False
    for t in _threads:
        t.join()

def set_user(user, forcereload=False, workfunc=None):
    print("User set to", user)
    global _collection_xml, _game_xml
    print("Fetching collection data...")
    if workfunc is not None:
        workfunc("Fetching collection for {}...".format(user))

    collection_filename = pathlib.Path(CACHE_DIR) / "collection_{}.xml".format(user)

    if forcereload:
        try:
            os.remove(collection_filename)
        except FileNotFoundError:
            pass

    _collection_xml = fetch.get(collection_filename, lambda: ET.parse(collection_filename), API_COLL_URL.format(id=user), workfunc=workfunc)

    print("Fetching game data...")
    collection = _collection_xml.findall("./item")
    if len(collection) > 0:
        gameids = [el.get("objectid") for el in collection]
        gameidstring = ",".join(sorted(gameids))
        game_filename = pathlib.Path(CACHE_DIR) / "games_{}.xml".format(user)

        if forcereload:
            try:
                os.remove(game_filename)
            except FileNotFoundError:
                pass

        if workfunc is not None:
            workfunc("Fetching game data for {} games...".format(len(collection)))
        _game_xml = fetch.get(game_filename, lambda:ET.parse(game_filename), API_GAME_URL.format(id=gameidstring), workfunc=workfunc)

        if _game_xml.getroot().tag == "div":
            print("Data fetch went bad. Reason: {}. Trying again.".format(_game_xml.getroot().text.strip()))
            set_user(user, True)
        else:
            returned_count = len(list(_game_xml.getroot()))
            if len(gameids) != returned_count:
                if not forcereload:
                    print("Did not receive enough game ids! Expected {}, but got {}. Trying again forcefully".format(len(gameids), returned_count))
                    set_user(user,True)
                else:
                    raise SortException("Did not receive enough game ids! Expected {}, but got {}".format(len(gameids), returned_count))
    else:
        print("{} has no games in their collection.".format(user))

def pump_queue():
    while True:
        if _q_blocked:
            time.sleep(0.02)
            continue

        try:
            #print(threading.current_thread().name, "tried")
            user, game = _q.get(timeout=1)
            #print(threading.current_thread().name, "got", game.name)
            game.set_image(get_img(user, game.id))
            _q.task_done()
            #time.sleep(0.01)
        except queue.Empty:
            if _q_continue:
                #print(threading.current_thread().name, "idled")
                continue
            #print(threading.current_thread().name, "bailed!")
            break

    #print(threading.current_thread().name, "done pumping")


def queue_img(user, game):
    global _queued_cnt
    _q.put( (user, game) )
    _queued_cnt += 1

def done_adding(func, progressfunc):
    def _done_adding(func_, progressfunc_):
        #_q.join()
        print("Done Adding..", _queued_cnt, _q.qsize(), threading.current_thread().getName())
        while not _q.empty():
            progressfunc_(get_progress())
            time.sleep(0.05)
        print("Finished it up")

        func_()

    threading.Thread(target=_done_adding, args=(func,progressfunc), name="DoneAdder").start()

def block_pumping():
    global _q_blocked
    _q_blocked = True

def allow_pumping():
    global _q_blocked
    _q_blocked = False


def get_progress():
    return (_queued_cnt - _q.qsize()) / _queued_cnt

def get_collection(user):
    return _collection_xml


def get_game(user, id):
    return _game_xml.find("./item[@id='{}']".format(id))


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
                raise ModuleNotFoundError()

        return get_img_specific(thumb.text)
    except ModuleNotFoundError:
        print("No Thumbnail or version for", id)
    except Exception as e:
        print("Root failed", e, id)
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


