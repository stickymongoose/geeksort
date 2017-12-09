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
_queued_cnt = 0
_threads = []

THREAD_COUNT = 10

def init():
    try:
        os.mkdir(pathlib.Path(CACHE_DIR))
    except OSError:
        pass

    try:
        os.mkdir(pathlib.Path(CACHE_DIR) / "pics")
    except OSError:
        pass

    for i in range(THREAD_COUNT):
        t = threading.Thread(target=pump_queue, name="Fetcher {}".format(i))
        t.start()
        _threads.append(t)

def shutdown():
    global _q_continue
    _q_continue = False
    for t in _threads:
        t.join()

def pump_queue():
    while True:
        try:
            #print(threading.current_thread().name, "tried")
            user, game = _q.get(timeout=1)
            #print(threading.current_thread().name, "got", game.name)
            game.set_image(get_img(user, game.id))
            _q.task_done()
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
        #print("Done Adding..", _queued_cnt, _q.qsize())
        while not _q.empty():
            progressfunc_(get_progress())
            time.sleep(0.05)
        #print("Finished it up")

        func_()

    threading.Thread(target=_done_adding, args=(func,progressfunc), name="DoneAdder").start()

def get_progress():
    return (_queued_cnt - _q.qsize()) / _queued_cnt


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


