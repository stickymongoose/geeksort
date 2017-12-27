#!/usr/bin/env python
# -*- coding: utf-8 -*-
import requests
import time
import os
from constants import *
import xml.etree.ElementTree as ET
from http.client import responses

# return a request, but wait some seconds and retry if error
def _fetch(request, workfunc):
    timeout = 1.5
    while timeout <= 30.0:
        r = requests.get( request )
        #print( "Response: ", r.status_code )
        if r.status_code == 200:
            return r.content
        else:
            if r.status_code == 429:
                timeout = timeout + 5
            else:
                print( "Busy. Code: {} Trying again in {}".format(r.status_code, timeout))

            if workfunc is not None:
                if r.status_code == 202:
                    workfunc("BGG has queued the request.\nChecking again in {:.0f} seconds".format(timeout))
                else:
                    workfunc("BGG says '{}'.\nWaiting {:.0f} seconds".format(responses[r.status_code], timeout))
            time.sleep(timeout)
            timeout = timeout * 1.5
            continue
    print("Timeout exceeded")
    raise Exception


def get(filename, func, request, delay=0, canexpire=True, workfunc=None):
    for i in range(3):
        try:
            filetime = os.path.getmtime(filename)
            now = time.time()
            # if file is too old
            if canexpire and (now - filetime) >= MAX_CACHE_AGE:
                raise TimeoutError()

            return func()
        except (FileNotFoundError, ET.ParseError,TimeoutError):
            try:
                if i > 0:
                    print( "Contacting bgg, attempt: ", i+1 )
                f = _fetch(request, workfunc)
                with open(filename,"wb") as fh:
                    fh.write(f)
                time.sleep(delay)
            except Exception as e:
                print(e)
    else:
        print( "Too many errors")
        raise IOError
