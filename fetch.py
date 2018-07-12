#!/usr/bin/env python
# -*- coding: utf-8 -*-
import requests
import time
import os
from constants import *
import xml.etree.ElementTree as ET
from http.client import responses

import logging
logger = logging.getLogger(__name__)

class URITooLongError(Exception):
    pass

# return a request, but wait some seconds and retry if error
def _fetch(request, workfuncs):
    timeout = 5
    while True: #timeout <= 45.0: # unclear if an arbitrary timeout is good or not...
        r = requests.get( request )
        if r.status_code == 200:  # value returned
            return r.content
        logger.info( "Response: %d", r.status_code )
        if r.status_code == 414 or r.status_code == 500:  # request URI too long (or "busy" with XMLAPI1)
            logger.warning("URI was too long (%d)", len(request))
            raise URITooLongError("BGG-specified")
        else:
            if r.status_code == 429:
                timeout = timeout + 5
            else:
                logger.info( "Busy. Code: %d Trying again in %d", r.status_code, timeout)

            if workfuncs is not None:
                if r.status_code == 202:
                    workfuncs["Start"]("BGG has queued the request.\nChecking again in {:.0f} seconds...".format(timeout), WorkTypes.MESSAGE)
                else:
                    workfuncs["Start"]("BGG says '{}'.\nWaiting {:.0f} seconds...".format(responses[r.status_code], timeout), WorkTypes.MESSAGE)

            time.sleep(timeout)
            if workfuncs is not None:
                workfuncs["Stop"](WorkTypes.MESSAGE)
            timeout = timeout * 1.5

    logger.info("Timeout exceeded")
    raise Exception("Timeout exceeded")


def _one_attempt(func, request, delay=0, workfuncs=None):
    try:
        f = _fetch(request, workfuncs)
        time.sleep(delay)
        return func(f)
    except URITooLongError as e:
        logger.info("URI was too long")
        raise e  # toss this on on up
    except Exception as e:
        logger.exception("one attempt: {}".format(e))


def get_raw(func, request, delay=0, workfuncs=None) -> ET.ElementTree:
    """attempts to get raw data from the internet, without caching it like get_cached does"""
    for i in range(3):
        if i > 0:
            logger.info("Contacting bgg, attempt: %d", i)
        return _one_attempt(func, request, delay, workfuncs)
    else:
        logger.warning( "Too many errors")
        raise IOError


def get_cached(filename, func, request, delay=0, canexpire=True, workfuncs=None):
    """attempts to read a filename from disk, and if not present (or expired)
    Pulls it from the net via request"""
    for i in range(3):
        try:
            filetime = os.path.getmtime(filename)
            now = time.time()
            # if file is too old
            if canexpire and (now - filetime) >= MAX_CACHE_AGE:
                raise TimeoutError("File {} too old ({} >= {})".format(filename, now-filetime, MAX_CACHE_AGE))

            #logger.info("Loaded %s from cache", filename)
            return func(filename)
        except (FileNotFoundError, ET.ParseError, TimeoutError) as e:
            logger.info("Handled: %s", e)
            def cache_file(data, filen, fnc):
                with open(filen, "wb") as fh:
                    fh.write(data)
                return fnc(filen)

            return _one_attempt(lambda data: cache_file(data, filename, func), request, delay, workfuncs)
    else:
        logger.warning("Too many errors")
        raise IOError

