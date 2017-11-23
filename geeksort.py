#!/usr/bin/env python
# -*- coding: utf-8 -*-

#requires pillow

import collection
import hover
import searchbox
import tkinter as Tk
from tkinter import ttk
import game
import shelf
import math
from constants import *

# TODO: make this customizable and possibly with a UI
def makeshelves(sbox):
    cases = []
    print("Making shelves...")
    with open("shelves.txt","r") as f:
        for line in f.read().splitlines():
            bc = shelf.Bookcase(line)
            cases.append(bc)
            sbox.register(bc)
    print("\bDone.")
    return cases

def collectionfetch(username):
    print("Fetching collection for {}...".format(username))
    game.Game._user = username
    root = collection.getcollection(game.Game._user)
    print("\bDone.")
    return root.findall("./item") # get all items

def makegames(collectionodes):
    print("Making games...\r")
    allgames = []
    for g in collectionodes:
        newgame = game.Game(g)
        allgames.append( newgame )
    print("\bDone")
    return allgames


def sortgames(games, funcs, cases):
    for f in funcs[::-1]:
        games = sorted(games, key=f)


    class GamePlaced(Exception):pass

    # do all the sorting
    unplaced = []
    print("Organizing shelves...")
    for g in games:
        try:
            #shelf._verbose = True
            for bc in cases:
                if bc.trybox(g):
                    #print(b.name, "on",  s.name,  "-", bc.index(s))
                    raise GamePlaced()

            #shelf._verbose = False
            unplaced.append(g)
        except GamePlaced:
            continue
    print("\bDone")

    #do post-sort fixing
    print("Finishing up...")
    for bc in cases:
        bc.finish()
    print("\bDone")
    return unplaced

# TODO: make this modular and customizable
def sizesort(box):
    return -(box.x * box.y * box.z)
    #return game.colorbrightness( box.color )


def makescrollablelist(title, values, actionfunc, casecount):
    frm = Tk.Frame(nb,height=math.ceil(highestshelf*IN_TO_PX), width=200, border=2, relief=Tk.SUNKEN)
    frm.pack_propagate(False)
    nb.add(frm, text=title)

    list = Tk.Listbox(frm)
    for g in values:
        list.insert(Tk.END, g.longname)
    list.pack(side=Tk.LEFT, fill=Tk.BOTH, expand=True)
    list.values = values
    list.bind("<Double-Button-1>", lambda e:actionfunc(e.widget.values[e.widget.curselection()[0]]))


    scroll = Tk.Scrollbar(frm)
    scroll.pack(side=Tk.RIGHT, fill=Tk.Y)

    list.config(yscrollcommand=scroll.set)
    scroll.config(command=list.yview)

    casecount += 1
    return frm, list, scroll

# make up a picture, created early so we can use the image data
allgamesxml = collectionfetch("jadthegerbil")
allgames = makegames(allgamesxml)


window = Tk.Tk()
searchbox = searchbox.SearchBox(window)
searchbox.grid(column=0, row=0, pady=10, sticky=Tk.W, padx=5)
cases = makeshelves(searchbox)

excluded   = [ b for b in allgames if b.excluded ]
sortedgames= [ b for b in allgames if not b.excluded ]
boxgames   = [ b for b in sortedgames if b.hasbox ]
noboxgames = [ b for b in sortedgames if not b.hasbox ]


shelf.Shelf.setStoreStyle(shelf.StoreStyle.PreferSide)
game.Game.setSidePreference(game.SidePreference.Left)
unplaced = sortgames(boxgames, [lambda x:x.longname, sizesort],  cases)


totalarea = 0.0
totalused = 0.0
print("Summing used amounts...")
for bc in cases:
    used, total = bc.getused()
    totalused += used
    totalarea += total
print("\bDone")


window.title("Boardsort Results {:.02f}/{:.02f} sqft {:.01f}%".format(
      totalused*SQIN_TO_SQFEET
    , totalarea*SQIN_TO_SQFEET
    , (totalused/totalarea)*100.0))


mf = Tk.Frame(window)
mf.grid(column=0,row=1,sticky=(Tk.W,Tk.E,Tk.S,Tk.N))
#mf.columnconfigure(0,weight=1)
#mf.rowconfigure(0,weight=1)


highestshelf = 0
for shelfIndex in range(len(cases)):
    bc = cases[shelfIndex]
    bc.makewidgets(mf, shelfIndex)
    highestshelf = max(bc.height, highestshelf)

casecount = len(cases)

# only add an overflow shelf if we need it
if len(unplaced) > 0:
    unplacedshelf = shelf.GameStack("Overflow", 300, 1000)
    searchbox.register(unplacedshelf)
    for b in unplaced:
        unplacedshelf.addbox(b, "xz" if b.x > b.y else "yz")
    unplacedshelf.finish()
    unplacedshelf.makewidgets(mf, index=casecount)
    casecount += 1

nb = ttk.Notebook(mf)
nb.grid(row=0, column=casecount, sticky=(Tk.W, Tk.E, Tk.S), padx=5)



# add a bunch of widgets for leftover things
if len(excluded) > 0:
    def unexclude(game):
        print("Unexcluded", game.longname )
    excluded.sort(key=lambda b:b.longname)
    makescrollablelist("Excluded",  excluded, unexclude, casecount)

# only add versionless shelf if we need it
if len(noboxgames) > 0:
    noboxgames.sort(key=lambda b:b.longname)
    noversions = [g for g in noboxgames if g.versionid == 0]
    nodata     = [g for g in noboxgames if g.versionid != 0 and not g.hasbox ] # assumption being, it has a version, but might not have a box

    makescrollablelist("No Dimensions", noversions, lambda:None, casecount)
    makescrollablelist("No Versions", nodata, lambda:None, casecount)



# make it last so it's on top of everything
hover.Hover(window)

window.mainloop()

#for g in s.games:
#    print("%-30s%s\t%.2f\t%.2f\t%.2f" % (g.name, g.dir, g.x, g.y, g.z))


