#!/usr/bin/env python
# -*- coding: utf-8 -*-

import math

IN_TO_PX = 6
IN_TO_CM = 2.54
CM_TO_IN = 1/IN_TO_CM

LB_TO_KG = 0.45359237
KG_TO_LB = 1/LB_TO_KG


CASE_COLOR="#C6813F"
SHELF_COLOR="#6B4522"
FOUND_COLOR="#AFAF00"

BRIGHT_CUTOFF = 0.25

INSET_STRIDE = 5
SAMPLE_STRIDE = 10
COLOR_CUTOFF = 250*3
NEEDED_SAMPLES = 20
ALPHA_CUTOFF = 240

SQIN_TO_SQFEET = (1/(12*12))

GAME_BORDER = 1
SHELF_BORDER = 2
BOOKCASE_BORDER = 2

DENOM_LIMIT = 16 # for the display of fractional inches, let's go with 16ths
BOX_PRECISION = 4 # boxes we'll round up to nearest 4th of an inch
ROUND_PRECISION=3 # show 3 degrees of precision

NO_BOX_X = 3
NO_BOX_Y = 3
NO_BOX_Z = 10

EXCLUDE_COMMENT = "#geeksort-exclude"

VERSION_URL = "https://boardgamegeek.com/item/correction/boardgameversion/{id}"
GAME_URL    = "https://boardgamegeek.com/boardgame/{id}"
GAME_VERSIONS_URL = "https://boardgamegeek.com/boardgame/{id}/xxx/versions"
API_COLL_URL    = 'http://www.boardgamegeek.com/xmlapi2/collection?username={id}&own=1&version=1&stats=1'
API_GAME_URL    = 'http://www.boardgamegeek.com/xmlapi2/thing?id={id}&stats=1&version=1'

CACHE_DIR = "cache"

def ceilFraction(val, factor):
    return math.ceil(val*factor)/factor

def roundFraction(val, factor):
    return round(val*factor)/factor

# accessor to get the 'top' of a list-stack easily
def top(l):
    if len(l) == 0:
        return None

    return l[ len(l)-1]


