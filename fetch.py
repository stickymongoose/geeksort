#!/usr/bin/env python
# -*- coding: utf-8 -*-
import requests
import time
import os
from constants import *
import xml.etree.ElementTree as ET
from http.client import responses
from tkinter import messagebox

import logging
logger = logging.getLogger(__name__)

class URITooLongError(Exception):
    pass

# return a request, but wait some seconds and retry if error
def _fetch(request, progbar, throw504):
    timeout = 5
    while True: #timeout <= 45.0: # unclear if an arbitrary timeout is good or not...
        r = requests.get( request )
        if r.status_code == 200:  # value returned
            return r.content
        logger.info( "Response: %d", r.status_code )
        
        if r.status_code == 504 and throw504:
            raise TimeoutError("504'd")
        if r.status_code == 414 or r.status_code == 500:  # request URI too long (or "busy" with XMLAPI1)
            logger.warning("URI was too long (%d)", len(request))
            raise URITooLongError("BGG-specified")
        else:
            if r.status_code == 429:
                timeout += 5
            else:
                logger.info( "Busy. Code: %d Trying again in %d", r.status_code, timeout)

            if progbar is None:
                time.sleep(timeout)
            else:

                if r.status_code == 202:
                    line = "BGG has queued the request.\nChecking again in {:.0f} seconds...".format(timeout)
                else:
                    line = "BGG says '{}'.\nWaiting {:.0f} seconds...".format(responses[r.status_code], timeout)

                with progbar.work(line, WorkTypes.QUEUED_UP, progress=True):
                    for t in range(0, int(timeout), 1):
                        progbar.set_percent(t/timeout, WorkTypes.QUEUED_UP)
                        time.sleep(1)

            timeout *= 1.5

    logger.info("Timeout exceeded")
    raise Exception("Timeout exceeded")


def _one_attempt(func, request, delay=0, progbar=None, throw504=False):
    try:
        f = _fetch(request, progbar, throw504)
        time.sleep(delay)
        return func(f)

    except URITooLongError as e:
        logger.info("URI was too long")
        raise e  # toss this on on up

    except Exception as e:
        logger.exception("one attempt: {}".format(e))
        raise e # toss all?


def get_raw(func, request, delay=0, progbar=None, throw504=False) -> ET.ElementTree:
    """attempts to get raw data from the internet, without caching it like get_cached does"""
    for i in range(3):
        if i > 0:
            logger.info("Contacting bgg, attempt: %d", i)
        return _one_attempt(func, request, delay, progbar, throw504)
    else:
        logger.warning( "Too many errors")
        raise IOError


def try_cache(filename, func, promptsIfOld=None):
    try:
        filetime = os.path.getmtime(filename)
        now = time.time()
        age = (now - filetime) / (24 * 60 * 60)  # age in days
        # if file is too old
        if age >= MAX_CACHE_AGE:
            if promptsIfOld is None or messagebox.askyesno(promptsIfOld["title"]
                    , promptsIfOld["msg"].format(age=age)
                    , default=messagebox.NO):
                raise TimeoutError("File {} too old ({} >= {})".format(filename, age, MAX_CACHE_AGE))

        # logger.info("Loaded %s from cache", filename)
        return func(filename)

    except (FileNotFoundError, ET.ParseError, TimeoutError) as e:
        logger.info("Handled: %s", e)
        return None


def get_cached(filename, func, request, delay=0, promptsIfOld=None, progbar=None):
    """attempts to read a filename from disk, and if not present (or expired)
    Pulls it from the net via request"""
    for i in range(3):
        result = try_cache(filename, func, promptsIfOld)
        if result is not None:
            logger.info("%s filename loaded from cache", filename)
            return result

        def cache_file(data, filen, fnc):
            with open(filen, "wb") as fh:
                fh.write(data)
            return fnc(filen)

        return _one_attempt(lambda data: cache_file(data, filename, func), request, delay, progbar)
    else:
        logger.warning("Too many errors")
        raise IOError

