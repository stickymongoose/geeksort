#!/usr/bin/env python
# -*- coding: utf-8 -*-

SCALAR = 6
CASE_COLOR="#C6813F"
SHELF_COLOR="#6B4522"
FOUND_COLOR="#AFAF00"

BRIGHT_CUTOFF = 0.25

INSET_STRIDE = 5
SAMPLE_STRIDE = 10
COLOR_CUTOFF = 250*3
NEEDED_SAMPLES = 20
ALPHA_CUTOFF = 240


GAME_BORDER = 1
SHELF_BORDER = 2
BOOKCASE_BORDER = 2

# accessor to get the 'top' of a list-stack easily
def top(l):
    if len(l) == 0:
        return None

    return l[ len(l)-1]


