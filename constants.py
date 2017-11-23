#!/usr/bin/env python
# -*- coding: utf-8 -*-

IN_TO_PX = 6
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

NO_BOX_X = 3
NO_BOX_Y = 3
NO_BOX_Z = 10

EXCLUDE_COMMENT = "#geeksort-exclude"

VERSION_URL = "https://boardgamegeek.com/boardgameversion/{id}"
GAME_URL    = "https://boardgamegeek.com/boardgame/{id}"
API_COLL_URL    = 'http://www.boardgamegeek.com/xmlapi2/collection?username={id}&own=1&version=1&stats=1'
API_GAME_URL    = 'http://www.boardgamegeek.com/xmlapi2/thing?id={id}&stats=1&version=1'


# accessor to get the 'top' of a list-stack easily
def top(l):
    if len(l) == 0:
        return None

    return l[ len(l)-1]


