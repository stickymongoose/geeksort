#!/usr/bin/env python
# -*- coding: utf-8 -*-

#requires pillow

import tkinter as Tk
from tkinter import ttk

import os
import collection
import hover
import webbrowser
import searchbox
import game
import shelf
import sizewindow
import scrollable
from constants import *


class GameFilters:
    def __init__(self, gameNodes):
        self.all = []
        self.unplaced = []
        print("Making games...\r")
        for g in gameNodes:
            newgame = game.Game(g)
            self.all.append( newgame )
        print("\bDone")

        self.excluded = [b for b in self.all if b.excluded]
        self.sorted   = [b for b in self.all if not b.excluded]

        self.inBoxes   = [b for b in self.sorted if b.hasbox]
        self.noBoxes  = [b for b in self.sorted if not b.hasbox]

        self.noVersions = [g for g in self.noBoxes if g.versionid == 0]
        # assumption being, it has a version, but might not have a box
        self.noData = [g for g in self.noBoxes if g.versionid != 0 and not g.hasbox]

        self.noVersions.sort(key=Sort.byName)
        self.noData.sort(key=Sort.byName)

    def getSortedBoxes(self, sortfuncs):
        sortedboxes = self.inBoxes

        for f in sortfuncs[::-1]:
            sortedboxes.sort(key=f)
        return sortedboxes


class Sort:
    @staticmethod
    def byName(box):
        return box.longname

    @staticmethod
    def bySize(box):
        return -(box.x * box.y * box.z)

    @staticmethod
    def byColor(box):
        return game.color_brightness(box.color)


class App:

    def __init__(self):
        self.tkWindow = Tk.Tk()

        self.tkFrame = Tk.Frame(self.tkWindow,border=15)
        self.tkFrame.grid(column=0, row=1, sticky=(Tk.W, Tk.E, Tk.S, Tk.N))
        self.tkSideNotebook = None

        # make it last so it's on top of everything
        self.hover = hover.Hover(self.tkWindow)

        self.tkFrame.bind("<Motion>", self.hover.onClear)

        # mf.columnconfigure(0,weight=1)
        # mf.rowconfigure(0,weight=1)
        self.stackUnplaced = shelf.GameStack("Overflow", 300, 1000)
        self.scrollNoVers = None
        self.scrollNoDims = None
        self.scrollExclude = None

        self.games = None

        self.searchBox = searchbox.SearchBox(self.tkWindow)
        self.searchBox.grid(column=0, row=0, pady=10, sticky=Tk.W, padx=5)

        self.make_shelves()
        # TODO: Cache off
        self.sortFuncs = [Sort.byName, Sort.bySize]
        self.collection_fetch("jadthegerbil")

    def clear_games(self):
        for b in self.cases:
            b.clear_games()

        self.stackUnplaced.clear_games()


    # TODO: make this customizable and possibly with a UI
    def make_shelves(self):
        self.cases = []
        with open("shelves.txt","r") as f:
            for line in f.read().splitlines():
                bc = shelf.Bookcase(line)
                self.cases.append(bc)
                self.searchBox.register(bc)

    def collection_fetch(self, username):
        print("Fetching collection for {}...".format(username))
        game.Game._user = username
        root = collection.get_collection(game.Game._user)
        print("\bDone.")

        collectionNodes = root.findall("./item") # get all items

        self.games = GameFilters(collectionNodes)
        self.sort_games()

    def sort_games(self):
        self.clear_games()
        sgames = self.games.getSortedBoxes(self.sortFuncs)

        class GamePlaced(Exception):pass

        # do all the sorting
        self.games.unplaced = []
        print("Organizing shelves...")
        for g in sgames:
            try:
                #shelf._verbose = True
                for bc in self.cases:
                    if bc.try_box(g):
                        #print(b.name, "on",  s.name,  "-", bc.index(s))
                        raise GamePlaced()

                #shelf._verbose = False
                self.games.unplaced.append(g)
            except GamePlaced:
                continue
        print("\bDone")

        #do post-sort fixing
        for bc in self.cases:
            bc.finish()

        self.post_sort()

    def post_sort(self):
        totalarea = 0.0
        totalused = 0.0
        for bc in self.cases:
            used, total = bc.get_used()
            totalused += used
            totalarea += total

        self.tkWindow.title("Boardsort Results {:.02f}/{:.02f} sqft {:.01f}%".format(
              totalused*SQIN_TO_SQFEET
            , totalarea*SQIN_TO_SQFEET
            , (totalused/totalarea)*100.0))

        highestshelf = 0
        for shelfIndex in range(len(self.cases)):
            bc = self.cases[shelfIndex]
            bc.make_shelf_widgets(self.tkFrame, shelfIndex)
            bc.make_game_widgets()
            highestshelf = max(bc.height, highestshelf)

        casecount = len(self.cases)

        # only add an overflow shelf if we need it
        if len(self.games.unplaced) > 0:
            self.searchBox.register(self.stackUnplaced)
            for b in self.games.unplaced:
                self.stackUnplaced.add_box(b, "xz" if b.x > b.y else "yz")

            self.stackUnplaced.finish()
            self.stackUnplaced.make_widgets(self.tkFrame, index=casecount)
            casecount += 1

        # only add versionless shelf if we need it
        if len(self.games.excluded) + len(self.games.noData) + len(self.games.noVersions) > 0:
            self.tkSideNotebook = ttk.Notebook(self.tkFrame)
            self.tkSideNotebook.pack(side=Tk.LEFT, anchor=Tk.SW, padx=5)

            if len(self.games.noData) > 0:
                self.scrollNoDims = scrollable.ScrollableList(self.tkSideNotebook, "No Dimensions"
                                                              , highestshelf, self.games.noData, self.open_version, casecount)
                self.searchBox.register(self.scrollNoDims)

            if len(self.games.noVersions) > 0:
                self.scrollNoVers = scrollable.ScrollableList(self.tkSideNotebook, "No Versions"
                                                              , highestshelf, self.games.noVersions, self.open_version_picker, casecount)
                self.searchBox.register(self.scrollNoVers)

            if len(self.games.excluded) > 0:
                exc = scrollable.ScrollableList(self.tkSideNotebook, "Excluded"
                                                , highestshelf, self.games.excluded, self.unexclude, casecount)
                self.searchBox.register(exc)


    # add a bunch of widgets for leftover things
    def unexclude(self, game):
        print("Unexcluded", game.longname )

    def open_version(self, game):
        s = sizewindow.Popup(self.tkWindow, game)
        self.tkWindow.wait_window(s.top)

    def open_version_picker(self, game):
        print(game.longname)
        webbrowser.open( GAME_VERSIONS_URL.format(id=game.id) )


# TODO: Cache off from preferences
shelf.Shelf.set_store_style(shelf.StoreStyle.PreferSide)
game.Game.set_side_preference(game.SidePreference.Left)

try: os.mkdir(CACHE_DIR)
except OSError:
    pass


a = App()

# make up a picture, created early so we can use the image data
#a.collection_fetch("jadthegerbil")


a.tkWindow.mainloop()



