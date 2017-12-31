# global sets of data
from collections import defaultdict

Types      = defaultdict(lambda:0)
Categories = defaultdict(lambda:0)
Mechanics  = defaultdict(lambda:0)
Families   = defaultdict(lambda:0)
Designers  = defaultdict(lambda:0)
Artists    = defaultdict(lambda:0)
Publishers = defaultdict(lambda:0)


def append(d:defaultdict, new:list):
    for n in new:
        d[n] += 1