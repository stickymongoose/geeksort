#!/usr/bin/env python
# -*- coding: utf-8 -*-

#requires pillow

import tkinter as Tk
from tkinter import ttk
from enum import IntEnum
import threading
import collection
import hover
import webbrowser
import searchbox
import game
import shelf
import sizewindow
import scrollable
#import scrwindow
import namebox
from constants import *

ROW_SEARCH = 10
ROW_PROGRESS = 10
ROW_SHELVES = 20

class WorkTypes(IntEnum):
    PROGRESS = 1
    FETCH = 2

class GameFilters:
    def __init__(self, gameNodes, progressFunc, doneFunc):
        self.all = []
        self.unplaced = []
        progressFunc( 0.0 )
        for index in range(len(gameNodes)):
            newgame = game.Game(gameNodes[index])
            self.all.append( newgame )
            #progressFunc( index / len(gameNodes) )
        collection.done_adding(doneFunc, progressFunc)
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
        return box.sortname

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

        self.tkFrame = Tk.Frame(self.tkWindow, border=15)
        self.tkFrame.grid(column=0, row=ROW_SHELVES, sticky=(Tk.W, Tk.E, Tk.S, Tk.N), columnspan=2)
        self.tkSideNotebook = None
        self.tkWindow.columnconfigure(0, weight=1)
        self.tkWindow.rowconfigure(ROW_SHELVES, weight=1)


        self.menu = Tk.Menu(self.tkWindow, tearoff=0)
        self.menu.add_command(label="Change User", command=self.prompt_name)
        self.tkWindow.config(menu=self.menu)


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

        self.tkWindow.after(100,func=self.prompt_name)

        self.searchBox = searchbox.SearchBox(self.tkWindow)
        self.searchBox.grid(column=0, row=ROW_SEARCH, pady=10, sticky=Tk.W, padx=5)

        self.progressPct = Tk.DoubleVar(0.0)
        self.tkProgressActives = {}
        self.tkProgressFrm = ttk.Frame(self.tkWindow)
        self.tkProgressLabel = ttk.Label(self.tkProgressFrm)
        self.tkProgressLabel.pack()
        self.tkProgressBar = ttk.Progressbar(self.tkProgressFrm, mode="indeterminate", length=200
                                             , variable=self.progressPct)
        self.tkProgressBar.pack()

        self.make_shelves()
        # TODO: Cache off
        self.sortFuncs = [Sort.bySize] #[Sort.byName, Sort.bySize]
        self.workerThread = None

    def prompt_name(self):
        namebox.NameBox(self.tkWindow, self)

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
            self.start_work("Fetching collection for {}...".format(username), type=WorkTypes.FETCH)
            game.Game._user = username
            root = collection.get_collection(game.Game._user)

            collectionNodes = root.findall("./item") # get all items

            self.start_work("Fetching data for games...", type=WorkTypes.FETCH, progress=True)
            self.games = GameFilters(collectionNodes, self.set_progress, self.game_fetch_complete)
            self.sort_games()

        self.clear_games()
        self.games = None

        if self.workerThread is not None:
            print("Waiting to fetch")
            self.workerThread.join()
            print("Done")
        self.workerThread = threading.Thread(target=_realfetch, args=(self, username), name="Fetcher")
        self.workerThread.start()

    def set_progress(self, pct):
        #print("Progress", pct, threading.current_thread().getName())
        self.progressPct.set( pct * 100.0 )

    def game_fetch_complete(self):
        self.stop_work(WorkTypes.FETCH)
        self.resort_games()

    def resort_games(self):
        def _real_resort(self):
            self.games.make_lists()
            self.clear_games()
            self.sort_games()

        if self.workerThread is not None:
            print("Waiting to resort")
            self.workerThread.join()
            print("Done")
        self.workerThread = threading.Thread(target=_real_resort, args=(self,), name="Resorter").start()

    def sort_games(self):
        sgames = self.games.get_sorted_boxes(self.sortFuncs)

        class GamePlaced(Exception):pass

        # do all the sorting
        self.games.unplaced = []
        self.start_work("Organizing shelves...", type=WorkTypes.PROGRESS)
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

        self.start_work("Fixing up...",type=WorkTypes.PROGRESS)
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
                self.tkSideNotebook.pack(side=Tk.RIGHT, anchor=Tk.SW, padx=5)

            self.scrollNoDims = self._make_scroller(self.scrollNoDims, "No Dimensions", highestshelf, self.games.noData,
                                                    self.open_version)

            self.scrollNoVers = self._make_scroller(self.scrollNoVers, "No Versions", highestshelf,
                                                    self.games.noVersions, self.open_version_picker)

            self.scrollExclude = self._make_scroller(self.scrollExclude, "Excluded", highestshelf, self.games.excluded,
                                                     self.unexclude)

        elif self.tkSideNotebook is not None:
            self.tkSideNotebook.pack_forget()

        self.stop_work(WorkTypes.PROGRESS)


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
        sizewindow.Popup(self.tkWindow, game, self)

    def open_version_picker(self, game):
        webbrowser.open( GAME_VERSIONS_URL.format(id=game.id) )

    def start_work(self, label: str, type, progress=False):
        """Queues up a progress bar, with priority given to higher-numbered types"""
        self.tkProgressActives[type] = (label,progress)
        self._update_work()

    def stop_work(self, type):
        self.tkProgressActives.pop(type)
        self._update_work()

    def _update_work(self):

        try:
            key = max(self.tkProgressActives, key=lambda key: self.tkProgressActives[key])
            label, progress = self.tkProgressActives[key]
            #print(key, label, progress)
            if progress:
                self.tkProgressBar.configure(mode="determinate")
                self.tkProgressBar.stop()
            else:
                self.tkProgressBar.configure(mode="indeterminate")
                self.tkProgressBar.start()

            self.tkProgressLabel.configure(text=label)
            self.tkProgressFrm.grid(column=1, row=ROW_PROGRESS, sticky=Tk.W)
        # progressActives is empty, so turn off the progress bar
        except ValueError:
            self.tkProgressFrm.grid_forget()
            self.tkProgressBar.stop()


# TODO: Cache off from preferences
shelf.Shelf.set_store_style(shelf.StoreStyle.PreferStack)
game.Game.set_side_preference(game.SidePreference.Left)

collection.init()

#Tk.SimpleDialog

a = App()
a.mainloop()
collection.shutdown()

# make up a picture, created early so we can use the image data
#a.collection_fetch("jadthegerbil")




