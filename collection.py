#!/usr/bin/env python
# -*- coding: utf-8 -*-
import xml.etree.ElementTree as ET
import fetch
import os
import errno
import functools
import pathlib
import time
import numpy
from constants import *
import queue
import threading
import logging
logger = logging.getLogger(__name__)
pumplogger = logging.getLogger("pumpthreads")
#import concurrent.futures

MAX_URI_LENGTH = 7000 # absolutely a guess
MAX_OLD_API_GAME_COUNT = 300 # seems to work well without returning a nebulous 504

class UserError(Exception):
    pass

_q = queue.Queue()
_q_continue = True
_q_blocked = False
_queued_cnt = 0
_threads = []

_collection_xml = None
_game_xml = None

THREAD_COUNT = 3


def chunks(ls, n):
    return numpy.array_split(ls, n)


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


def _fetch_collection(user, forcereload=False, workfuncs=None) -> ET.ElementTree:
    logger.info("Fetching collection data...")
    workfuncs["Start"]("Fetching collection for {}...".format(user), type=WorkTypes.COLLECTION_FETCH, progress=False)

    collection_filename = pathlib.Path(CACHE_DIR) / "collection_{}.xml".format(user)

    if forcereload:
        try:
            os.remove(collection_filename)
        except FileNotFoundError:
            pass

    return fetch.get_cached(collection_filename, ET.parse, API_COLL_URL.format(id=user), workfuncs=workfuncs
                            , promptsIfOld={"title" : "Collection Out of Date"
            , "msg" : "Collection data for {user} is over {{age:2.1f}} day(s) old.\n\nDo you want to update it from BGG?".format(user=user)})


def _filter_games(allgameIds, workfuncs):

    # due to the current API, if there's an invalid game ID, it ruins the whole batch
    # since this is a rare occurrence, we'll special case it and use the old API

    chunkcount = MAX_OLD_API_GAME_COUNT
    found = []
    remaining = set(allgameIds)
    while True:
        try:
            chunkedListGen = (allgameIds[i:i+chunkcount] for i in range(0, len(allgameIds),chunkcount))
            for gameIds in chunkedListGen:
                logger.info("Attempting piecemeal filter, %d out of %d", len(gameIds), len(allgameIds))
                gameidstrings = ",".join(gameIds)
                getrequest = OLD_API_GAME_URL.format(ids=gameidstrings)
                if len(getrequest) >= MAX_URI_LENGTH:
                    raise fetch.URITooLongError()
                
                fetchedxml = fetch.get_raw(lambda data: ET.ElementTree(ET.fromstring(data)), getrequest,
                                           workfuncs=workfuncs, throw504=True)

                for g in fetchedxml.getroot().findall("./boardgame"):
                    id = g.get("objectid")
                    found.append(id)
                    remaining.remove(id)

        except (fetch.URITooLongError, TimeoutError):
            logger.warning("URI too long for the recovery filter (%d bytes). Ugh!", len(getrequest))
            chunkcount >>= 1
        else:
            break

    return found, list(remaining)


def _fetch_games(collectionXml, user, forcereload=False, workfuncs=None):
    if len(collectionXml) == 0:
        logger.warning("%s has no games in their collection.", user)
        return []

    game_filename = pathlib.Path(CACHE_DIR) / "games_{}.xml".format(user)
    if forcereload:
        try:
            os.remove(game_filename)
        except FileNotFoundError:
            pass

    allgameids = sorted(set([el.get("objectid") for el in collectionXml]), key=int)

    chunkcount = 1
    # URIs might get too long, attempt to batch it
    while True:
        if chunkcount == 1:
            workfuncs["Start"]("Fetching game data for {} games...".format(len(collectionXml)), WorkTypes.GAME_DATA)
        else:
            workfuncs["Start"]("Fetching game data for {} games...".format(len(collectionXml)), WorkTypes.GAME_DATA_PIECEMEAL, progress=True)
        try:
            temp_xml = None
            chunkindex = 0
            for gameids in chunks(allgameids, chunkcount):
                workfuncs["Progress"](chunkindex/chunkcount)
                while True: # we need some way to re-enter after filtering
                    gameidstrings = ",".join(gameids)
                    getrequest = API_GAME_URL.format(ids=gameidstrings)
                    if len(getrequest) >= MAX_URI_LENGTH:
                        raise fetch.URITooLongError("Self-selected")
                    
                    if chunkcount == 1:
                        logger.info("Attempting cache fetch")
                        logger.debug(getrequest)
                        fetchedxml = fetch.get_cached(game_filename, ET.parse, getrequest, workfuncs=workfuncs, promptsIfOld=
                        {"title":"Game Data", "msg":"Game Data is over {age:2.1f} days old. Do you want to fetch new data from BGG?"})
                    else:

                        logger.info("Attempting piecemeal fetch, %d out of %d", len(gameids), len(allgameids))
                        logging.debug(getrequest)
                        fetchedxml = fetch.get_raw(lambda data: ET.ElementTree(ET.fromstring(data)), getrequest,
                                                   workfuncs=workfuncs)

                    if fetchedxml is None:
                        logger.warning("Data fetch for chunk count %i returned no XML. Not sure what to do, so, bailing", chunkcount)
                        return ET.ElementTree()

                    elif fetchedxml.getroot().tag == "div":
                        logger.warning("Data fetch went bad. Reason: %s. Pivoting to ID-filter.", fetchedxml.getroot().text.strip())
                        workfuncs["Start"]("Recovering from some bad IDs", WorkTypes.FILTER_FETCH)
                        gameids, badids = _filter_games(gameids, workfuncs)
                        workfuncs["Stop"](WorkTypes.FILTER_FETCH)
                        logger.warning("Game ids %s removed from list, trying again", ", ".join(badids))

                    else:
                        returned_count = len(list(fetchedxml.getroot()))
                        if True:  # len(gameids) == returned_count:
                            logger.info("Requested and received %d games.", returned_count)
                            # got the right stuff
                            if temp_xml is None:
                                # first fetch start it off
                                temp_xml = fetchedxml
                                logger.info("no temp, it's now %d", returned_count)
                            else:
                                # subsequent fetches get appended
                                for kid in fetchedxml.getroot():
                                    temp_xml.getroot().append(kid)
                                logger.info("had a temp, it's now %d", len(temp_xml.getroot()))
                            break # leave the inner while True
                        # else:
                        #     # wrong number of elements (rare?)
                        #     if not forcereload:
                        #         # this branch is bit smelly, but at this time I'm not sure why we'd get such results
                        #         logger.warnig("Did not receive enough game ids! Expected %d, but got %d. Trying again forcefully", len(gameids), returned_count))
                        #         return set_user(user, forcereload=True, workfunc=workfunc, chunkcount=chunkcount)
                        #     else:
                        #         raise SortException("Did not receive enough game ids! Expected {}, but got {}".format(len(gameids), returned_count))
                chunkindex += 1
        except fetch.URITooLongError as e:
            chunkcount <<= 1
            logger.warning("%s URI was too long (%d bytes, %d games). Trying again in %d chunks", e, len(gameidstrings),
                                                                                            len(gameids),
                                                                                            chunkcount)
        else:
            break  # out of the while True

    # we've successfully read everything
    temp_xml.write(game_filename)
    logger.info("Read a total of %d games", len(temp_xml.getroot()))
    return temp_xml


def set_user(user, forcereload=False, workfuncs=None):
    logger.info("User set to %s", user)
    global _collection_xml, _game_xml
    _collection_xml = _fetch_collection(user, forcereload, workfuncs)
    workfuncs["Stop"](WorkTypes.COLLECTION_FETCH)

    if _collection_xml is not None:
        errorMessage = _collection_xml.getroot().find("./error/message")
        if errorMessage is not None:
            _collection_xml = ET.fromstring("<items totalitems='0'></items>")
            raise UserError(errorMessage)

        logger.info("Received %s games", _collection_xml.getroot().get("totalitems").strip())
    else:
        logger.warning("Received no games. Possibly an invalid user, or something went wrong. ")

    logger.info("+++Fetching game data...")
    _game_xml = _fetch_games(_collection_xml.findall("./item"), user, forcereload, workfuncs=workfuncs)
    logger.info("---Fetched game data...")
    workfuncs["Stop"](WorkTypes.GAME_DATA)
    workfuncs["Stop"](WorkTypes.GAME_DATA_PIECEMEAL)


def pump_queue():
    while _q_continue:
        if _q_blocked:
            time.sleep(0.02)
            continue

        try:
            pumplogger.debug("%s tried", threading.current_thread().name)
            user, game = _q.get(timeout=1)
            pumplogger.debug("%s got %s", threading.current_thread().name, game.name)
            game.set_image(get_img(user, game.id))
            _q.task_done()
            #time.sleep(0.01)
        except queue.Empty:
            if _q_continue:
                pumplogger.debug("%s idled", threading.current_thread().name)
                continue
            pumplogger.debug("%s bailed!", threading.current_thread().name)
            break

    pumplogger.debug("%s done pumping", threading.current_thread().name)


def queue_img(user, game):
    global _queued_cnt
    _q.put( (user, game) )
    _queued_cnt += 1

def done_adding(func, progressfunc):
    def _done_adding(func_, progressfunc_):
        #_q.join()
        logging.info("Done Adding.. %d %d %s", _queued_cnt, _q.qsize(), threading.current_thread().getName())
        lastprogress = 0.0
        while not _q.empty() and _q_continue:
            lastprogress = max(get_progress(), lastprogress)
            progressfunc_(lastprogress)
            time.sleep(0.05)
        logger.info("Finished it up")

        func_()

    t = threading.Thread(target=_done_adding, args=(func,progressfunc), name="DoneAdder")
    t.start()
    _threads.append(t)

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
    fetch.get_cached(localimg, validate_file, imgurl)
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

        # for some reason, some games have no text in the thumbnail field.
        # how vexing!
        if thumb.text is None:
            return "pics/noimage.jpg"

        return get_img_specific(thumb.text)
    except ModuleNotFoundError:
        logger.warning("No Thumbnail or version for %d", id)
    except Exception as e:
        logger.warning("Root failed id {}: {}".format(id, e), exc_info=True)
    return "pics/noimage.jpg"


if __name__ == "__main__":

    print( _filter_games(["1","2","3","5","7","12","13","18","22","35"], None) )


#    print(get_img("jadthegerbil", 114903))
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
#    print("Done.")
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


