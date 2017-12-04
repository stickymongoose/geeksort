#!/usr/bin/env python
# -*- coding: utf-8 -*-

#requires pillow

import tkinter as Tk
from tkinter import ttk

import threading
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
    def __init__(self, gameNodes, progressFunc, doneFunc):
        self.all = []
        self.unplaced = []
        progressFunc( 0.0 )
        for index in range(len(gameNodes)):
            newgame = game.Game(gameNodes[index])
            self.all.append( newgame )
            progressFunc( index / len(gameNodes) )
        collection.done_adding(doneFunc)
        self.make_lists()

    def make_lists(self):

        self.excluded = [b for b in self.all if b.excluded]
        self.sorted   = [b for b in self.all if not b.excluded]

        self.inBoxes   = [b for b in self.sorted if b.hasbox]
        self.noBoxes  = [b for b in self.sorted if not b.hasbox]

        self.noVersions = [g for g in self.noBoxes if g.versionid == 0]
        # assumption being, it has a version, but might not have a box
        self.noData = [g for g in self.noBoxes if g.versionid != 0 and not g.hasbox]

        self.noVersions.sort(key=Sort.byName)
        self.noData.sort(key=Sort.byName)

    def get_sorted_boxes(self, sortfuncs):
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
        game.Game._app = self
        game.Game.init()

        self.tkFrame = Tk.Frame(self.tkWindow,border=15)
        self.tkFrame.grid(column=0, row=1, sticky=(Tk.W, Tk.E, Tk.S, Tk.N),columnspan=20)
        self.tkSideNotebook = None



        # self.menu = Tk.Menu(self.tkFrame, tearoff=0)
        # self.menu.add_command(label="Undo", command=lambda: print("Undo"))
        # self.menu.add_command(label="Redo", command=lambda: print("Redo"))
        # self.tkWindow.config(menu=self.menu)
        #
        # self.tkFrame.bind("<Button-3>", lambda e:self.menu.post(e.x_root, e.y_root))

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

        self.progressPct = Tk.DoubleVar(0.0)
        self.tkProgressFrm = ttk.Frame(self.tkWindow)
        self.tkProgressLabel = ttk.Label(self.tkProgressFrm)
        self.tkProgressLabel.pack()
        self.tkProgressBar = ttk.Progressbar(self.tkProgressFrm, mode="indeterminate", length=200
                                             , variable=self.progressPct)
        self.tkProgressBar.pack()

        self.make_shelves()
        # TODO: Cache off
        self.sortFuncs = [Sort.byName, Sort.bySize]

        self.tkWindow.after(0, self.collection_fetch, "jadthegerbil")

        #self.collection_fetch("jadthegerbil")


    def mainloop(self):
        self.tkWindow.mainloop()
        #while True:
        #    self.tkWindow.update_idletasks()
        #   if not self.pause_loop:
        #        self.tkWindow.update()

    def clear_games(self):
        for b in self.cases:
            b.clear_games()

        self.stackUnplaced.clear_games()


    # TODO: make this customizable and possibly with a UI
    def make_shelves(self):
        self.cases = shelf.read("shelves.txt")

        for bc in self.cases:
          self.searchBox.register(bc)
          bc.make_shelf_widgets(self.tkFrame)

    def collection_fetch(self, username):
        def _realfetch(self,username):
            self.start_work("Fetching collection for {}...".format(username))
            game.Game._user = username
            root = collection.get_collection(game.Game._user)

            collectionNodes = root.findall("./item") # get all items

            self.start_work("Fetching data for games...", True)
            self.games = GameFilters(collectionNodes, self.set_progress, self.resort_games)
            self.sort_games()

        threading.Thread(target=_realfetch, args=(self, username)).start()

    def set_progress(self, pct):
        self.progressPct.set( pct * 100.0 )

    def resort_games(self):
        def _real_resort(self):
            self.games.make_lists()
            self.clear_games()
            self.sort_games()

        threading.Thread(target=_real_resort, args=(self,)).start()

    def sort_games(self):
        sgames = self.games.get_sorted_boxes(self.sortFuncs)

        class GamePlaced(Exception):pass

        # do all the sorting
        self.games.unplaced = []
        self.start_work("Organizing shelves...")
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

        self.start_work("Fixing up...")
        #do post-sort fixing
        for bc in self.cases:
            bc.finish()

        self._after_sort()

    def _after_sort(self):
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
        for bc in self.cases:
            bc.make_game_widgets()
            highestshelf = max(bc.height, highestshelf)
        highestshelf += 5 # pixel wiggle... or is this in text lines?

        # only add an overflow shelf if we need it
        if len(self.games.unplaced) > 0:
            self.searchBox.register(self.stackUnplaced)
            for b in self.games.unplaced:
                if b.x >= b.y:
                    self.stackUnplaced.add_box(b, game.HorizLong)
                else:
                    self.stackUnplaced.add_box(b, game.HorizShort)

            self.stackUnplaced.finish()
            self.stackUnplaced.make_widgets(self.tkFrame)
        else:
            self.stackUnplaced.hide()

        # only add versionless shelf if we need it
        if len(self.games.excluded) + len(self.games.noData) + len(self.games.noVersions) > 0:
            if self.tkSideNotebook is None:
                self.tkSideNotebook = ttk.Notebook(self.tkFrame)
                self.tkSideNotebook.pack(side=Tk.LEFT, anchor=Tk.SW, padx=5)

            self.scrollNoDims = self._make_scroller(self.scrollNoDims, "No Dimensions", highestshelf, self.games.noData,
                                                    self.open_version)

            self.scrollNoVers = self._make_scroller(self.scrollNoVers, "No Versions", highestshelf,
                                                    self.games.noVersions, self.open_version_picker)

            self.scrollExclude = self._make_scroller(self.scrollExclude, "Excluded", highestshelf, self.games.excluded,
                                                     self.unexclude)

        elif self.tkSideNotebook is not None:
            self.tkSideNotebook.pack_forget()

        self.stop_work()


    def _make_scroller(self, scroller, name, height, list, func):
        if len(list) > 0:
            if scroller is None:
                scroller = scrollable.ScrollableList(self.tkSideNotebook, name, height, func)
            scroller.set_list(list)
            self.searchBox.register(scroller)

        elif scroller is not None:
            scroller.hide()

        return scroller

    # add a bunch of widgets for leftover things
    def unexclude(self, game):
        print("Unexcluded", game.longname )
        game.excluded = False
        self.resort_games()

    def open_version(self, game):
        s = sizewindow.Popup(self.tkWindow, game)
        print("Window open")
        self.tkWindow.wait_window(s.top)
        print("And we're back")

    def open_version_picker(self, game):
        print(game.longname)
        webbrowser.open( GAME_VERSIONS_URL.format(id=game.id) )

    def start_work(self, label: str, progress=False):
        self.tkProgressFrm.grid(column=1, row=0)

        if progress:
            self.tkProgressBar.configure(mode="determinate")
            self.tkProgressBar.stop()
        else:
            self.tkProgressBar.configure(mode="indeterminate")
            self.tkProgressBar.start()
        self.tkProgressLabel.configure(text=label)

    def stop_work(self):
        self.tkProgressFrm.grid_forget()
        self.tkProgressBar.stop()


# TODO: Cache off from preferences
shelf.Shelf.set_store_style(shelf.StoreStyle.PreferSide)
game.Game.set_side_preference(game.SidePreference.Left)

collection.init()

#Tk.SimpleDialog

a = App()
a.mainloop()

# make up a picture, created early so we can use the image data
#a.collection_fetch("jadthegerbil")




