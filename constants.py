#!/usr/bin/env python
# -*- coding: utf-8 -*-

import math
import re
from contrib.mixed_fractions import Mixed

IN_TO_PX = 8
IN_TO_CM = 2.54
CM_TO_IN = 1/IN_TO_CM

LB_TO_KG = 0.45359237
KG_TO_LB = 1/LB_TO_KG


CASE_COLOR="#C6813F"
SHELF_COLOR="#6B4522"
FOUND_COLOR="#AFAF00"

BTN_WIDTH=15
BTN_HEIGHT=2 # in lines, just because

GS_VERSION = "0.5.5"
TITLE_STRING = "GeekSort v" + GS_VERSION

RESORT_BTN_COLOR = "#E0E0FF"
OK_BTN_COLOR = "darkseagreen1"
CANCEL_BTN_COLOR = "#ffc0c0"
BGG_BTN_COLOR = "lightblue"

BRIGHT_CUTOFF = 0.25

INSET_STRIDE = 5
SAMPLE_STRIDE = 10
COLOR_CUTOFF = 250*3
NEEDED_SAMPLES = 20
ALPHA_CUTOFF = 240

MAX_CACHE_AGE = 8*60*60 # only 8 hours

SQIN_TO_SQFEET = (1/(12*12))

GAME_BORDER = 1
SHELF_BORDER = 2
BOOKCASE_BORDER = 2
SHELF_FUDGE_WIDTH = 9 # Not sure why we need this, but without, shelves are too narrow

DENOM_LIMIT = 16 # for the display of fractional inches, let's go with 16ths
VULGAR_LIMIT = 8 # for tighter display, gotta use 8ths
BOX_PRECISION = 4 # boxes we'll round up to nearest 4th of an inch
ROUND_PRECISION=3 # show 3 degrees of precision

SHELF_SPACING = 5

EXCLUDE_COMMENT = "#geeksort-exclude"

VERSION_URL = "https://boardgamegeek.com/item/boardgameversion/{id}/xxx"
VERSION_EDIT_URL = "https://boardgamegeek.com/item/correction/boardgameversion/{id}"
GAME_URL    = "https://boardgamegeek.com/boardgame/{id}"
GAME_VERSIONS_URL = "https://boardgamegeek.com/boardgame/{id}/xxx/versions"
API_COLL_URL    = 'https://www.boardgamegeek.com/xmlapi2/collection?username={id}&own=1&version=1&stats=1'
API_GAME_URL    = 'https://www.boardgamegeek.com/xmlapi2/thing?id={ids}&stats=1&versions=1'
OLD_API_GAME_URL    = 'https://www.boardgamegeek.com/xmlapi/boardgame/{ids}'


CACHE_DIR = "__cache__"

def ceilFraction(val, factor):
    return math.ceil(val*factor)/factor


def roundFraction(val, factor):
    return round(val*factor)/factor


def makeFraction(num):
    asfrac = str(Mixed(roundFraction(num, VULGAR_LIMIT)).limit_denominator(VULGAR_LIMIT))
    asfrac = asfrac.replace(" 1/8", u"⅛")
    asfrac = asfrac.replace(" 1/4", u"¼")
    asfrac = asfrac.replace(" 3/8", u"⅜")
    asfrac = asfrac.replace(" 1/2", u"½")
    asfrac = asfrac.replace(" 5/8", u"⅝")
    asfrac = asfrac.replace(" 3/4", u"¾")
    asfrac = asfrac.replace(" 7/8", u"⅞")
    return asfrac


# accessor to get the 'top' of a list-stack easily
def top(l):
    if len(l) == 0:
        return None

    return l[len(l)-1]


def to_search(t):
    t = t.strip().lower()
    return re.sub(":| |-", "", t)


def to_sort(t):
    t = t.strip().lower()
    #TODO: See if there's a smarter way to get more languages... is NLTK the universal way?
    return re.sub("^(a|an|the|el|la|los|las|die|der|das|le|la|l'|les) ", "", t)


class SortException(Exception): pass