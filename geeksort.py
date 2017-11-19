#!/usr/bin/env python
# -*- coding: utf-8 -*-

#requires pillow

import collection
import hover
import tkinter as Tk
import game
import shelf
import concurrent.futures

from constants import *


# make up a picture, created early so we can use the image data
window = Tk.Tk()


game.Game._user = "jadthegerbil"
root = collection.getcollection(game.Game._user)

allver = root.findall("./item")
allgames = []
gamesbyid = {}


def creategame(game):
    newgame = game.Game(game)
    gamesbyid[newgame.id] = newgame
    allgames.append( gamesbyid[newgame.id] )
    print(newgame.name,  len(allgames))

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


#for g in allver:
#    newgame = game.Game(g)
#    gamesbyid[newgame.id] = newgame
#    allgames.append( gamesbyid[newgame.id] )

boxgames   = [ b for b in allgames if b.exists ]
noboxgames = [ b for b in allgames if not b.exists ]


# TODO: make this modular and customizable
def sorts(box):
    return box.x * box.y * box.z
    #return game.colorbrightness( box.color )


shelf.Shelf.setStoreStyle(shelf.StoreStyle.PreferSide)
game.Game.setSidePreference(game.SidePreference.Left)
sgames = sorted(boxgames, key=sorts, reverse=True)

shelves = []
# TODO: make this customizable and possibly with a UI
with open("shelves.txt","r") as f:
    for line in f.read().splitlines():
        bits = line.split('\t')
        curshelf = []
        for i in range(3, len(bits)):
            name = "{}-{}".format(bits[0],  i-2)
            curshelf.append( shelf.Shelf(  name, bits[1], bits[i], bits[2] ) )
        shelves.append(curshelf)

class GamePlaced(Exception):pass

# do all the sorting
for b in sgames:
    try:
        #shelf._verbose = True
        for bc in shelves:
            for s in bc:
                if s.trybox(b):
                    #print(b.name, "on",  s.name,  "-", bc.index(s))
                    raise GamePlaced()
            #shelf._verbose = False

        print("No placed for ", b.name)
    except GamePlaced:
        continue

#do post-sort fixing
for bc in shelves:
    for s in bc:
        s.finish()

totalarea = 0.0
totalused = 0.0
totalshelves = 0
for bc in shelves:
    for s in bc:
        totalused = totalused + s.usedarea
        totalarea = totalarea + s.totalarea
        totalshelves = totalshelves + 1


SQIN_TO_SQFEET = (1/(12*12))
window.title("Boardsort Results {:.02f}/{:.02f} sqft {:.01f}%".format(
      totalused*SQIN_TO_SQFEET
    , totalarea*SQIN_TO_SQFEET
    , (totalused/totalarea)*100.0))


mf = Tk.Frame(window)
mf.grid(column=0,row=0,sticky=(Tk.W,Tk.E,Tk.S,Tk.N))
#mf.columnconfigure(0,weight=1)
#mf.rowconfigure(0,weight=1)



for shelfIndex in range(len(shelves)):
    bc = shelves[shelfIndex]

    can = Tk.Frame(mf, width=s.maxwidth*SCALAR
                    , bg=CASE_COLOR, border=2
                    , relief=Tk.RAISED)

    can.grid(row=0, column=shelfIndex, sticky=(Tk.W, Tk.E, Tk.S), padx=5)

    text = Tk.Label(can, text=bc[0].name, bg=CASE_COLOR, pady=0)
    text.grid(row=0, pady=0)
    for si in range(len(bc)):
        s = bc[si]
        s.addwidget(can,si+1)

# make it last so it's on top of everything
hover.Hover(window)

window.mainloop()

#for g in s.games:
#    print("%-30s%s\t%.2f\t%.2f\t%.2f" % (g.name, g.dir, g.x, g.y, g.z))


