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
import concurrent.futures
from constants import *

# make up a picture, created early so we can use the image data
window = Tk.Tk()
searchbox = searchbox.SearchBox(window)
searchbox.grid(column=0, row=0, pady=10, sticky=Tk.W, padx=5)


cases = []
# TODO: make this customizable and possibly with a UI

print("Making shelves...")
with open("shelves.txt","r") as f:
    for line in f.read().splitlines():
        bc = shelf.Bookcase(line)
        cases.append(bc)
        searchbox.register(bc)

print("\bDone.")

print("Fetching collection...")
game.Game._user = "jadthegerbil"
root = collection.getcollection(game.Game._user)
print("\bDone.")

allver = root.findall("./item")
allgames = []
gamesbyid = {}


print("Making games...\r")
if 1:
    for g in allver:
        newgame = game.Game(g)
        gamesbyid[newgame.id] = newgame
        allgames.append( gamesbyid[newgame.id] )
else:
    with concurrent.futures.ThreadPoolExecutor(max_workers=25) as executor:
        gamecreator = {executor.submit(game.Game, g): g for g in allver}
        for future in concurrent.futures.as_completed(gamecreator):
            gamexml = gamecreator[future]
            try:
                newgame = future.result()
                gamesbyid[newgame.id] = newgame
                allgames.append( gamesbyid[newgame.id] )
            except Exception as ex:
                print("GameId {} tossed exception, {}".format( gamexml.get("objectid"),  ex))

print("\bDone")
#for g in allver:
#    newgame = game.Game(g)
#    gamesbyid[newgame.id] = newgame
#    allgames.append( gamesbyid[newgame.id] )

excluded = [ b for b in allgames if b.excluded ]
sortgames = [ b for b in allgames if not b.excluded ]


boxgames   = [ b for b in sortgames if b.hasbox ]
noboxgames = [ b for b in sortgames if not b.hasbox ]


# TODO: make this modular and customizable
def sorts(box):
    return box.x * box.y * box.z
    #return game.colorbrightness( box.color )


shelf.Shelf.setStoreStyle(shelf.StoreStyle.PreferSide)
game.Game.setSidePreference(game.SidePreference.Left)
sgames = sorted(boxgames, key=sorts, reverse=True)
sgames = sorted(sgames, key=lambda x:x.longname)


class GamePlaced(Exception):pass

# do all the sorting
unplaced = []
print("Organizing shelves...")
for b in sgames:
    try:
        #shelf._verbose = True
        for bc in cases:
            if bc.trybox(b):
                #print(b.name, "on",  s.name,  "-", bc.index(s))
                raise GamePlaced()

        #shelf._verbose = False
        unplaced.append(b)
    except GamePlaced:
        continue
print("\bDone")

#do post-sort fixing
print("Finishing up...")
for bc in cases:
    bc.finish()
print("\bDone")

totalarea = 0.0
totalused = 0.0
totalshelves = 0
print("Summing used amounts...")
for bc in cases:
    used, total = bc.getused()
    totalused += used
    totalarea += total
    totalshelves += 1
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


def makescrollablelist(title, values, actionfunc):
    global casecount
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

# add a bunch of widgets for leftover things
if len(excluded) > 0:
    def unexclude(game):
        print("Unexcluded", game.longname )
    excluded.sort(key=lambda b:b.longname)
    makescrollablelist("Excluded",  excluded, unexclude)

# only add versionless shelf if we need it
if len(noboxgames) > 0:
    noboxgames.sort(key=lambda b:b.longname)
    noversions = [g for g in noboxgames if g.versionid == 0]
    nodata     = [g for g in noboxgames if g.versionid != 0 and not g.hasbox ] # assumption being, it has a version, but might not have a box
    if len(noversions)+len(nodata)==len(noboxgames):
        print("Mismatch!", len(noversions), len(nodata), len(noboxgames))

    makescrollablelist("No Dimensions", noversions, lambda:None)
    makescrollablelist("No Versions", nodata, lambda:None)



# make it last so it's on top of everything
hover.Hover(window)

window.mainloop()

#for g in s.games:
#    print("%-30s%s\t%.2f\t%.2f\t%.2f" % (g.name, g.dir, g.x, g.y, g.z))


