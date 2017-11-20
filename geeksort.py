#!/usr/bin/env python
# -*- coding: utf-8 -*-

#requires pillow

import collection
import hover
import tkinter as Tk
import game
import shelf
import concurrent.futures


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
sgames = sorted(sgames, key=lambda x:x.longname)

cases = []
# TODO: make this customizable and possibly with a UI
with open("shelves.txt","r") as f:
    for line in f.read().splitlines():
        cases.append(shelf.Bookcase(line))

class GamePlaced(Exception):pass

# do all the sorting
unplaced = shelf.GameStack("Overflow", 300, 1000)
for b in sgames:
    try:
        #shelf._verbose = True
        for bc in cases:
            if bc.trybox(b):
                #print(b.name, "on",  s.name,  "-", bc.index(s))
                raise GamePlaced()

        #shelf._verbose = False

        print("No placed for ", b.name)
        #prefer the bigger dimension for a box
        unplaced.addbox(b, "xz" if b.x > b.y else "yz")
    except GamePlaced:
        continue

# sort unplaced
unplaced.finish()

#do post-sort fixing
for bc in cases:
    bc.finish()

totalarea = 0.0
totalused = 0.0
totalshelves = 0
for bc in cases:
    used, total = bc.getused()
    totalused += used
    totalarea += total
    totalshelves += 1


SQIN_TO_SQFEET = (1/(12*12))
window.title("Boardsort Results {:.02f}/{:.02f} sqft {:.01f}%".format(
      totalused*SQIN_TO_SQFEET
    , totalarea*SQIN_TO_SQFEET
    , (totalused/totalarea)*100.0))


mf = Tk.Frame(window)
mf.grid(column=0,row=1,sticky=(Tk.W,Tk.E,Tk.S,Tk.N))
#mf.columnconfigure(0,weight=1)
#mf.rowconfigure(0,weight=1)

searchframe = Tk.LabelFrame(window, text="Search Function")
searchframe.grid(column=0, row=0, pady=10, sticky=Tk.W, padx=5)
searchbox = Tk.Entry(searchframe,  width=100)
searchbox.pack(side=Tk.LEFT,  anchor=Tk.NW, pady=5, padx=5)
searchbox.request = 0

searchresults = Tk.Label(searchframe, width=20)
searchresults.pack(side=Tk.LEFT, anchor=Tk.NW, pady=5, padx=5)

def search():
    searchbox.request = 0
    text = searchbox.get()
    text = text.lower().replace(" ", "")
    matchcount = 0
    for b in cases:
        matchcount += b.search(text)
    matchcount +=  unplaced.search(text)
    searchresults.configure(text="{} Result{}".format(matchcount, "" if matchcount==1 else "s"))



def typed(event):
    searchbox.after_cancel(searchbox.request)
    searchbox.request = searchbox.after(250, search)

searchbox.bind("<Key>", typed)
searchbox.bind("<Return>", search)


for shelfIndex in range(len(cases)):
    bc = cases[shelfIndex]
    bc.makewidgets(mf, shelfIndex)

# only add an overflow shelf if we need it
if len(unplaced.games) > 0:
    unplaced.makewidgets(mf, index=len(cases))

# make it last so it's on top of everything
hover.Hover(window)

window.mainloop()

#for g in s.games:
#    print("%-30s%s\t%.2f\t%.2f\t%.2f" % (g.name, g.dir, g.x, g.y, g.z))


