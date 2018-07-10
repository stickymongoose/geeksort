#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
if sys.version_info[0] < 3:
    raise Exception("Python 3+ is required. Try re-running with python3 instead of python.")

import logging
import logging.config
import os
import json

def setup_logging( path='logging.json', default_level=logging.INFO ):
    """Setup logging configuration
    """

    # load configuration
    if os.path.exists(path):
        with open(path, 'rt') as f:
            config = json.load(f)

        logging.config.dictConfig(config)
        print("Logging configured from file", path)
    else:
        logging.basicConfig(level=default_level)
        print("Logging configured by default, as no file", path)

setup_logging()
logger = logging.getLogger(__name__)

import tkinter as Tk
from tkinter import ttk
from enum import IntEnum
from PIL import Image, ImageTk
import contrib.scrollingframe as scrollframe
import threading
import collection
import hover
import webbrowser
import searchbox
import game
import shelf
import sorts
import preferences
import sizewindow
import scrollable
import namebox

from constants import *

ROW_ICON_MENU = 0
ROW_SEARCH = 10
ROW_PROGRESS = 0
ROW_SHELVES = 20

class WorkTypes(IntEnum):
    PROGRESS = 1
    FETCH = 2



class GameFilters:
    def __init__(self, gameNodes, progressFunc, doneFunc):
        self.all = []
        self.unplaced = []
        self.sorted = []
        self.excluded = []
        self.filtered = []
        self.inBoxes = []
        self.noBoxes = []
        self.noVersions = []
        self.noData = []
        self.by_id = {}
        progressFunc( 0.0 )
        for index in range(len(gameNodes)):
            newgame = game.Game(gameNodes[index])
            self.all.append( newgame )
            self.by_id[newgame.id] = newgame
            #progressFunc( index / len(gameNodes) )
        collection.done_adding(doneFunc, progressFunc)
        self.make_lists()

    def find(self, id):
        return self.by_id[id]

    def make_lists(self):
        self.excluded = [b for b in self.all if b.excluded]
        self.sorted   = [b for b in self.all if not b.excluded]

        self.inBoxes   = [b for b in self.sorted if b.hasbox]
        self.noBoxes  = [b for b in self.sorted if not b.hasbox]

        self.noVersions = [g for g in self.noBoxes if g.versionid == 0]
        # assumption being, it has a version, but might not have a box
        self.noData = [g for g in self.noBoxes if g.versionid != 0 and not g.hasbox]

        self.noVersions.sort(key=sorts.Name)
        self.noData.sort(key=sorts.Name)

    def get_sorted_boxes(self, sortfuncs, filterfuncs):
        sortedboxes = []
        self.filtered = []
        class FailedFilter(Exception): pass

        if len(filterfuncs) > 0:
            for agame in self.inBoxes:
                try:
                    for func, op, values, rev in filterfuncs:
                        # some filters may return non-binary values
                        # but, we only wanna check filters that TRULY pass
                        if op(func(agame), *values) != True:
                            raise FailedFilter()

                except FailedFilter:
                    self.filtered.append(agame)
                    continue

                # passed all filters, success!
                sortedboxes.append(agame)
        else:
            sortedboxes = self.inBoxes



        # sort in reverse order, ie, less to more important
        # standard primary, secondary, tertiary key stuff
        for func, op, values, rev in sortfuncs[::-1]:
            #print(op(func(sortedboxes[0]), *values))
            sortedboxes.sort(key=lambda game:op(func(game), *values), reverse=rev)
        return sortedboxes



class App:

    def __init__(self):
        collection.init()
		
        self.preferences = preferences.load(self)
        self.preferences.set_prefs()

        self.tkWindow = Tk.Tk()
        self.tkWindow.geometry("800x600")
        self.tkWindow.config(bg="#f0f0f0")
        game.Game._app = self
        game.Game.init()

        self.tkScroll = scrollframe.Scrolling_Area(self.tkWindow, background="#f0f0f0")
        self.tkScroll.grid(column=0, row=ROW_SHELVES, sticky=Tk.NSEW, columnspan=2, padx=5, pady=5)

        self.tkFrame = self.tkScroll.innerframe
        self.tkFrame.config(bg="#f0f0f0")

        self.tkSideNotebook = None
        self.tkWindow.columnconfigure(0, weight=1)
        self.tkWindow.rowconfigure(ROW_SHELVES, weight=1)

        self.resort_img = ImageTk.PhotoImage(Image.open("pics/resort.png"))
        self.geek_img = ImageTk.PhotoImage(Image.open("pics/bgg_t.png"))
        self.shelves_img = ImageTk.PhotoImage(Image.open("pics/shelves.png"))
        self.search_img = ImageTk.PhotoImage(Image.open("pics/search.png"))

        self.iconMenu = Tk.Frame(self.tkWindow, background="#f0f0f0")

        self.iconMenu.grid(column=0, row=ROW_ICON_MENU, sticky=Tk.NSEW, columnspan=2, padx=5, pady=5)

        style = ttk.Style()
        style.configure("My.TButton", borderwidth=2)
        style.map("My.TButton",
                  relief=[("pressed", "sunken"),("selected", "sunken"), ("!selected", "raised")],
                  highlightbackground=[("selected", "#A8E4B3"), ("!selected", "blue")]
                  )

        ttk.Button(self.iconMenu, text="Change\nUser...", width=10, command=self.prompt_name, image=self.geek_img,
                   compound=Tk.TOP).pack(side=Tk.LEFT, fill=Tk.Y)
        ttk.Button(self.iconMenu, text="Reload\nCollection", width=10, command=self.reload_games, image=self.geek_img,
                   compound=Tk.TOP).pack(side=Tk.LEFT, fill=Tk.Y)
        ttk.Button(self.iconMenu, text="Reload\nShelves", width=10, command=self.reload_shelves, image=self.shelves_img,
                   compound=Tk.TOP).pack(side=Tk.LEFT, fill=Tk.Y)
        ttk.Button(self.iconMenu, text="Sort...", width=10, command=self.prompt_prefs, image=self.resort_img,
                   compound=Tk.TOP).pack(side=Tk.LEFT, fill=Tk.Y)
        self.searchbtn = ttk.Button(self.iconMenu, text="Search", width=10, command=self.toggle_search, image=self.search_img,
                   compound=Tk.TOP, style="My.TButton")
        self.searchbtn.pack(side=Tk.LEFT, fill=Tk.Y)
        self.menu = Tk.Menu(self.tkWindow, tearoff=0)



        filemenu = Tk.Menu(self.menu, tearoff=0)
        self.menu.add_cascade(menu=filemenu, label="File", underline=0)
        filemenu.add_command(label="Change User", command=self.prompt_name, underline=0)
        filemenu.add_command(label="Reload Collection from BGG", command=self.reload_games
                             , image=self.geek_img, underline=7, compound=Tk.RIGHT)
        filemenu.add_command(label="Reload Shelves.txt", command=self.reload_shelves, underline=7)
        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=self.exit, underline=1)

        sortingmenu = Tk.Menu(self.menu, tearoff=0)
        self.menu.add_cascade(menu=sortingmenu, label="Sorting", underline=0)
        sortingmenu.add_command(label="Change Criteria...", command=self.prompt_prefs, underline=0)

        self.tkWindow.config(menu=self.menu)

        self.tkWindow.title(TITLE_STRING)


        # make it last so it's on top of everything
        self.hover = hover.Hover(self.tkWindow)
        self.tkWindow.bind("<FocusIn>",  self.app_gain_focus)
        self.tkWindow.bind("<FocusOut>", self.app_lost_focus)

        self.tkFrame.bind("<Motion>", self.hover.onClear)

        for c in self.tkScroll.get_chrome():
            try:
                c.bind("<Motion>", self.hover.onClear)
            except Exception as e:
                print(c, e)

        # mf.columnconfigure(0,weight=1)
        # mf.rowconfigure(0,weight=1)
        self.stackUnplaced = shelf.GameStack("Overflow", 300, 1000)
        self.scrollNoVers = None
        self.scrollNoDims = None
        self.scrollExclude = None
        self.scrollFilter = None

        self.games = None
        self.cases = []


        self.tkWindow.after(100,func=self.prompt_name)

        topframe = ttk.Frame(self.tkWindow)
        topframe.grid(column=0, row=ROW_SEARCH, pady=10, sticky=Tk.W, padx=5)
        self.searchBox = searchbox.SearchBox(topframe)
        #self.searchBox.grid(column=0, row=0)
        self.searchBox.bind("<Motion>", self.hover.onClear)
        self.search_shown = False

        self.progressPct = Tk.DoubleVar(0.0)
        self.tkProgressActives = {}


        # Gotta set aside some space so the screen doesn't resize when we show/hide the progress bar
        spaceholder = ttk.Frame(self.tkWindow, width=240, height=60)
        spaceholder.grid(column=1, row=ROW_PROGRESS, sticky=Tk.W, padx=10)
        spaceholder.grid_propagate(False)
        spaceholder.bind("<Motion>", self.hover.onClear)
        topframe.bind("<Motion>", self.hover.onClear)

        self.tkProgressFrm = ttk.Frame(spaceholder)
        self.tkProgressLabel = ttk.Label(self.tkProgressFrm)
        self.tkProgressLabel.pack()
        self.tkProgressBar = ttk.Progressbar(self.tkProgressFrm, mode="indeterminate", length=200
                                             , variable=self.progressPct)
        self.tkProgressBar.pack()

        self.workerThread = None
        self.pref_window = None

    def exit(self):
        self.tkWindow.destroy()

    def prompt_name(self):
        namebox.NameBox(self.tkWindow, self, self.preferences)

    def prompt_prefs(self):
        if self.pref_window is None:
            self.pref_window = preferences.PreferencesUI(self.tkWindow, self.preferences, self.resort_games)
            self.pref_window.protocol("WM_DELETE_WINDOW", self.pref_closed)
        self.pref_window.focus_force()

    def pref_closed(self):
        self.pref_window.destroy()
        self.pref_window = None

    def app_gain_focus(self, event):
        self.hover.unblock()

    def app_lost_focus(self, event):
        self.hover.onClear(event)
        self.hover.block()

    def mainloop(self):
        self.tkWindow.mainloop()
        #while True:
        #    self.tkWindow.update_idletasks()
        #   if not self.pause_loop:
        #        self.tkWindow.update()
        collection.shutdown()

    def clear_games(self):
        #print("clear_games", threading.current_thread().name)
        self.stackUnplaced.clear_games()
        for b in reversed(self.cases):
            b.clear_games()

    def toggle_search(self):
        self.search_shown = not self.search_shown
        if self.search_shown:
            self.searchBox.grid(column=0, row=0)
            self.searchBox.focus()
            self.searchbtn.state(("selected",))
        else:
            self.searchBox.grid_forget()
            self.searchbtn.state(("!selected",))

    # TODO: make this customizable and possibly with a UI
    def make_shelves(self):
        self.cases = shelf.read("shelves.txt")
        self._make_shelf_widgets()

    def clear_shelves(self):
        for c in self.cases:
            self.searchBox.unregister(c)
            c.clear_widgets()

        self.stackUnplaced.clear_games()

    def _make_shelf_widgets(self):
        print("_make_shelf_widgets", threading.current_thread().name)

        for bc in self.cases:
            self.searchBox.register(bc)
            bc.make_shelf_widgets(self.tkFrame)

    def collection_fetch(self, username, forcereload=False):
        print("collection_fetch", threading.current_thread().name)

        def _realfetch(self, username, forcereload):
            #self.start_work("Fetching collection for {}...".format(username), type=WorkTypes.FETCH)
            self.preferences.user = username
            game.Game._user = username
            collection.set_user(username, forcereload, workfunc=lambda s: self.start_work(s, type=WorkTypes.FETCH))
            root = collection.get_collection(game.Game._user)

            collectionNodes = root.findall("./item") # get all items

            self.start_work("Fetching data for games...", type=WorkTypes.FETCH, progress=True)
            self.games = GameFilters(collectionNodes, self.set_progress, self.game_fetch_complete)

            # collection game in, so load the shelf collection
            savedcases, savedstack = shelf.load(username, self.games)
            if savedcases is not None or savedstack is not None:
                self.clear_shelves()

                self.cases = savedcases
                self.stackUnplaced = savedstack

                self._make_shelf_widgets()
                try:
                    self.stackUnplaced.make_widgets(self.tkFrame)
                except AttributeError:
                    pass

                self._after_sort(False)
            else:
                # no collection, make some shelves and sort everything
                self.make_shelves()
                self.sort_games()

        self.clear_games()
        self.games = None

        if self.workerThread is not None:
            print("Waiting to fetch", threading.current_thread().name)
            self.workerThread.join()
            print("Done", threading.current_thread().name)
        self.workerThread = threading.Thread(target=_realfetch, args=(self, username, forcereload), name="Fetcher")
        self.workerThread.start()

    def set_progress(self, pct):
        #print("Progress", pct, threading.current_thread().getName())
        self.progressPct.set( pct * 100.0 )

    def game_fetch_complete(self):
        self.stop_work(WorkTypes.FETCH)

    def reload_games(self):
        self.collection_fetch(self.preferences.user, True)

    def reload_shelves(self):
        def _real_reload(self):
            self.clear_shelves()
            self.make_shelves()
            self.sort_games()

        if self.workerThread is not None:
            print("Waiting to reload", threading.current_thread().name)
            self.workerThread.join()
            print("Done ", threading.current_thread().name)
        self.workerThread = threading.Thread(target=_real_reload, args=(self,), name="Reloader").start()


    def resort_games(self):
        
        def _real_resort(self):
            self.games.make_lists()
            self.clear_games()
            self.sort_games()

        if self.workerThread is not None:
            print("Waiting to resort", threading.current_thread().name)
            self.workerThread.join()
            print("Done", threading.current_thread().name)
        #self.workerThread = threading.Thread(target=_real_resort, args=(self,), name="Resorter").start()
        _real_resort(self)

    def sort_games(self):
        # print(("sort_games", threading.current_thread().name)
        sgames = self.games.get_sorted_boxes(self.preferences.sortFuncs, self.preferences.filterFuncs)

        class GamePlaced(Exception):pass

        # do all the sorting/placing
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

        shelf.save(game.Game._user, self.cases, self.stackUnplaced)

        self._after_sort()

    def _after_sort(self, checkUnplaced=True):
        # print(("_after_sort", threading.current_thread().name)

        totalarea = 0.0
        totalused = 0.0
        for bc in self.cases:
            used, total = bc.get_used()
            totalused += used
            totalarea += total

        # print(("set title")

        self.tkWindow.title("{} Results {:.02f}/{:.02f} sqft {:.01f}%".format(
            TITLE_STRING
            , totalused*SQIN_TO_SQFEET
            , totalarea*SQIN_TO_SQFEET
            , (totalused/totalarea)*100.0))

        # print(("shelf height and widgets")

        collection.block_pumping()
        highestshelf = 0
        for bc in self.cases:
            bc.make_game_widgets()
            highestshelf = max(bc.height, highestshelf)
        highestshelf += 5 # pixel wiggle... or is this in text lines?
        collection.allow_pumping()

        # print(("overflow")

        # only add an overflow shelf if we need it
        if checkUnplaced:
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

        # print(("versionless")

        # only add versionless shelf if we need it
        if len(self.games.excluded) + len(self.games.noData) + len(self.games.noVersions) + len(self.games.filtered) > 0:
            if self.tkSideNotebook is None:
                self.tkSideNotebook = ttk.Notebook(self.tkWindow)
                #self.tkSideNotebook.pack(side=Tk.RIGHT, anchor=Tk.SW, padx=5)
                self.tkSideNotebook.grid(column=2, row=ROW_SHELVES, sticky=Tk.NSEW, columnspan=2, padx=5, pady=5)
                self.tkSideNotebook.bind("<Motion>", self.hover.inst.onClear)
                hover.Hover.inst.lift()

            self.scrollNoDims = self._make_scroller(self.scrollNoDims, "No Dimensions", highestshelf, self.games.noData,
                                                    self.open_size_editor)

            self.scrollNoVers = self._make_scroller(self.scrollNoVers, "No Versions", highestshelf,
                                                    self.games.noVersions, self.open_version_picker)

            self.scrollExclude = self._make_scroller(self.scrollExclude, "Excluded", highestshelf, self.games.excluded,
                                                     self.unexclude)

            self.scrollFilter = self._make_scroller(self.scrollFilter, "Filtered", highestshelf, self.games.filtered,
                                                    self.open_size_editor)

        elif self.tkSideNotebook is not None:
            self.tkSideNotebook.pack_forget()

        # print(("stop work")
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

    def open_size_editor(self, game):
        sizewindow.Popup(self.tkWindow, game, self)

    def open_version_picker(self, game):
        webbrowser.open( GAME_VERSIONS_URL.format(id=game.id) )

    def start_work(self, label, type, progress=False):
        """Queues up a progress bar, with priority given to higher-numbered types"""
        # print((threading.current_thread().name, "starts", type, label)
        self.tkProgressActives[type] = (label,progress)
        self.tkProgressBar.after(0, self._update_work)
        #self._update_work()

    def stop_work(self, type):
        # print((threading.current_thread().name, "stops", type)
        try:
            self.tkProgressActives.pop(type)
        except KeyError:
            pass

        self.tkProgressBar.after(0, self._update_work)
        #self._update_work()

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
            self.tkProgressFrm.pack(anchor=Tk.CENTER, expand=True)
        # progressActives is empty, so turn off the progress bar
        except ValueError:
            self.tkProgressFrm.pack_forget()
            self.tkProgressBar.stop()


threading.current_thread().setName("mainThread")

logger.info("Starting App")
a = App()
a.mainloop()
logger.info("Left Mainloop")




