#!/usr/bin/env python
# -*- coding: utf-8 -*-
import requests
import time
import os
from constants import *
import xml.etree.ElementTree as ET
from http.client import responses

class URITooLongError(Exception):
    pass

# return a request, but wait some seconds and retry if error
def _fetch(request, workfunc):
    timeout = 5
    while timeout <= 45.0:
        r = requests.get( request )
        #print( "Response: ", r.status_code )
        if r.status_code == 200:  # value returned
            return r.content
        if r.status_code == 414 or r.status_code == 500:  # request URI too long (or "busy" with XMLAPI1)
            print("URI was too long ({})".format(len(request)))
            raise URITooLongError
        else:
            if r.status_code == 429:
                timeout = timeout + 5
            else:
                print( "Busy. Code: {} Trying again in {}".format(r.status_code, timeout))

            if workfunc is not None:
                if r.status_code == 202:
                    workfunc("BGG has queued the request.\nChecking again in {:.0f} seconds...".format(timeout))
                else:
                    workfunc("BGG says '{}'.\nWaiting {:.0f} seconds...".format(responses[r.status_code], timeout))
            time.sleep(timeout)
            timeout = timeout * 1.5
            continue
    print("Timeout exceeded")
    raise Exception("Timeout exceeded")


def _one_attempt(func, request, delay=0, workfunc=None):
    try:
        f = _fetch(request, workfunc)
        time.sleep(delay)
        return func(f)
    except URITooLongError as e:
        raise e  # toss this on on up
    except Exception as e:
        print(e)


def get_raw(func, request, delay=0, workfunc=None):
    """attempts to get raw data from the internet, without caching it like get_cached does"""
    for i in range(3):
        if i > 0:
            print("Contacting bgg, attempt: ", i + 1)
        return _one_attempt(func, request, delay, workfunc)
    else:
        print( "Too many errors")
        raise IOError


def get_cached(filename, func, request, delay=0, canexpire=True, workfunc=None):
    """attempts to read a filename from disk, and if not present (or expired)
    Pulls it from the net via request"""
    for i in range(3):
        try:
            filetime = os.path.getmtime(filename)
            now = time.time()
            # if file is too old
            if canexpire and (now - filetime) >= MAX_CACHE_AGE:
                raise TimeoutError("File too old")

            return func(filename)
        except (FileNotFoundError, ET.ParseError, TimeoutError) as e:
            #print("Handled Error: ", e)
            def cache_file(data, filen, fnc):
                with open(filen, "wb") as fh:
                    fh.write(data)
                fnc(filen)

            return _one_attempt(lambda data: cache_file(data, filename, func), request, delay, workfunc)
    else:
        print( "Too many errors")
        raise IOError

