#!/usr/bin/env python
# -*- coding: utf-8 -*-
import requests
import time
import xml.etree.ElementTree as ET

# return a request, but wait some seconds and retry if error
def _fetch(request):
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
                print( "Busy. Code: {} Trying again in {}".format(r.status_code, timeout ))
            time.sleep(timeout)
            timeout = timeout * 1.5
            continue
    print("Timeout exceeded")
    raise Exception

def get(filename, func, request, delay=0):

    for i in range(3):
        try:
            return func()
        except (FileNotFoundError, ET.ParseError):
            try:
                print( "Contacting bgg, attempt: ", i+1 )
                f = _fetch(request)
                with open(filename,"wb") as fh:
                    fh.write(f)
                time.sleep(delay)
            except Exception as e:
                print(e)
    else:
        print( "Too many errors")
        raise IOError