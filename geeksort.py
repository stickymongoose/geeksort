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
progresslogger = logging.getLogger("progressBar")

import tkinter as Tk
from tkinter import ttk
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




class GameFilters:
    def __init__(self, gameNodes, progressFunc, doneFunc):
        self.all = []
        self.unplaced = []
        self.sorted = []
        self.excluded = []
        self.filtered = []
        self.inBoxes = []
        self.noBoxes = []
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

        self.noData = [g for g in self.noBoxes if not g.hasbox]

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


class InfiniteStacks():
    def __init__(self):
        self.stacks = []

    def _add_stack(self, searchbox):
        self.stacks.append( shelf.GameStack("Overflow_{}".format(len(self.stacks)+1), 300, 120))
        self.searchbox.register( top(self.stacks) )

    def add_boxes(self, parent, boxlist, searchbox):
        self._add_stack(searchbox)

        for box in boxlist:
            while not top(self.stacks).try_box_lite(box):
                self.add_stack(searchbox)

        for s in self.stacks:
            s.finish()
            s.make_widgets(parent)

    def clear_games(self):
        for f in self.stacks:
            f.clear_games()
            f.destroy()

        self.stacks = []

    def hide(self):
        for s in self.stacks:
            s.hide()


class App:

    def __init__(self):
        collection.init()

        self.preferences = preferences.load(self)
        self.preferences.set_prefs()

        self.tkWindow = Tk.Tk()
        self.tkWindow.geometry("1500x800")
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
                logger.exception("{}: {}".format(c,e))

        # mf.columnconfigure(0,weight=1)
        # mf.rowconfigure(0,weight=1)
        self.stackUnplaced = InfiniteStacks()
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

        # Gotta set aside some space so the screen doesn't resize when we show/hide the progress bar
        spaceholder = ttk.Frame(self.tkWindow, width=240, height=60)
        spaceholder.grid(column=1, row=ROW_PROGRESS, sticky=Tk.NW, padx=10, columnspan=2)
        spaceholder.grid_propagate(False)
        spaceholder.bind("<Motion>", self.hover.onClear)
        topframe.bind("<Motion>", self.hover.onClear)

        self.make_progressbar(spaceholder)

        self.workerThread = None
        self.pref_window = None

    def exit(self):
        self.tkWindow.destroy()

    def prompt_name(self, errorMessage=None):
        namebox.NameBox(self.tkWindow, self, self.preferences, errorMessage)

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
        logger.info("clear_games: %s", threading.current_thread().name)
        self.stackUnplaced.clear_games()
        # reversed for speed and if/when we thread the UI we don't see them all shuffle over
        for bc in reversed(self.cases):
            bc.clear_games()
            
        if self.tkSideNotebook is not None:
            logger.info("Hid notebook")
            self.tkSideNotebook.grid_forget()
        else:
            logger.info("Didn't hide notebook--didn't exist")

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
        logger.info("+++Make shelves")
        self.clear_shelves()
        self.cases = shelf.read("shelves.txt")
        self._make_shelf_widgets()
        logger.info("---Made shelves")

    def clear_shelves(self):
        logger.info("+++Clear shelves")
        for c in self.cases:
            self.searchBox.unregister(c)
            c.clear_widgets()

        self.stackUnplaced.clear_games()
        logger.info("---Cleared shelves")

    def _make_shelf_widgets(self):
        logger.info("+++Make shelf widgets")
        
        for bc in self.cases:
            self.searchBox.register(bc)
            bc.make_shelf_widgets(self.tkFrame)
        logger.info("---Made shelf widgets")
        
    def collection_fetch(self, username, forcereload=False):
        logger.info("collection_fetch: %s", threading.current_thread().name)

        def _realfetch(self, username, forcereload):
            #self.start_work("Fetching collection for {}...".format(username), type=WorkTypes.IMAGE_FETCH)
            self.preferences.user = username
            game.Game._user = username
            workBlob = {"Start":self.start_work, "Progress":self.set_progress
                , "Stop":self.stop_work }
            try:
                collection.set_user(username, forcereload, workfuncs = workBlob )
            except collection.UserError as e:
                logger.warning("Invalid user: %s", username)
                self.tkWindow.after(0, lambda: self.prompt_name("Invalid User"))

            root = collection.get_collection(game.Game._user)

            collectionNodes = root.findall("./item") # get all items

            self.start_work("Fetching images for games...", type=WorkTypes.IMAGE_FETCH, progress=True)
            self.games = GameFilters(collectionNodes, self.set_progress, self.game_fetch_complete)

            # collection game in, so load the shelf collection
            savedcases, savedstack = shelf.load(username, self.games)
            if savedcases is not None or savedstack is not None:
                self.clear_shelves() # TODO: load in place, rather than have to nuke the old ones
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

        self.start_worker("fetch collection", _realfetch, (self, username, forcereload), "Fetcher")

    def game_fetch_complete(self):
        self.stop_work(WorkTypes.IMAGE_FETCH)

    def reload_games(self):
        self.collection_fetch(self.preferences.user, True)

    def reload_shelves(self):
        def _real_reload(self):
            self.clear_shelves()
            self.make_shelves()
            self.sort_games()

        self.start_worker("reload shelves", _real_reload, (self,), "Reloader")

    def resort_games(self):
        
        def _real_resort(self):
            self.games.make_lists()
            self.clear_games()
            self.sort_games()

        self.wait_for_worker("resort games")
        #self.start_worker("resort games, _real_resort, (self,), "Resorter")
        _real_resort(self)
    
    
    ######## Threading functions
    
    def start_worker(self, reason, target, args, name):
        self.wait_for_worker(reason)
        self.workerThread = threading.Thread(target=target, args=args, name=name)
        self.workerThread.start()
        
    def wait_for_worker(self, reason):
        if self.workerThread is not None:
            logger.info("THREAD: %s Waiting to %s", threading.current_thread().name, reason)
            self.workerThread.join()
            logger.info("THREAD: %s Done waiting to %s", threading.current_thread().name, reason)

            
    #### end of threading
    
    
    def sort_games(self):
        # print(("sort_games", threading.current_thread().name)
        sgames = self.games.get_sorted_boxes(self.preferences.sortFuncs, self.preferences.filterFuncs)

        class GamePlaced(Exception):pass

        # do all the sorting/placing
        self.games.unplaced = []
        self.start_work("Organizing shelves...", type=WorkTypes.SORT_GAMES)
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

        #self.start_work("Fixing up...", type=WorkTypes.SORT_GAMES)
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
                self.stackUnplaced.add_boxes(self.games.unplaced, self.tkFrame, self.searchBox)
            else:
                self.stackUnplaced.hide()

        # print(("versionless")

        # only add versionless shelf if we need it
        if len(self.games.excluded) + len(self.games.noData) + len(self.games.filtered) > 0:
            logger.info("We need a side panel, as we have %i excluded, %i no data, %i filtered"
                , len(self.games.excluded), len(self.games.noData), len(self.games.filtered))
               
            if self.tkSideNotebook is None:
                logger.info("Making side panel")
                self.tkSideNotebook = ttk.Notebook(self.tkWindow)
                #self.tkSideNotebook.pack(side=Tk.RIGHT, anchor=Tk.SW, padx=5)
                self.tkSideNotebook.bind("<Motion>", self.hover.inst.onClear)
                hover.Hover.inst.lift()

            self.tkSideNotebook.grid(column=2, row=ROW_SHELVES, sticky=Tk.NSEW, padx=5, pady=5)

            self.scrollNoDims = self._make_scroller(self.scrollNoDims, "No Dimensions", highestshelf, self.games.noData,
                                                    self.open_size_editor)

            self.scrollExclude = self._make_scroller(self.scrollExclude, "Excluded", highestshelf, self.games.excluded,
                                                     self.unexclude)

            self.scrollFilter = self._make_scroller(self.scrollFilter, "Filtered", highestshelf, self.games.filtered,
                                                    self.open_size_editor)

        elif self.tkSideNotebook is not None:
            logger.info("Don't need a notebook, hiding it")
            self.tkSideNotebook.grid_forget()
        else:
            logger.info("Don't need a notebook, but it doesn't exist.")

        # print(("stop work")
        self.stop_work(WorkTypes.SORT_GAMES)


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
        logger.info("%s Unexcluded", game.longname )
        game.excluded = False
        self.resort_games()

    def open_size_editor(self, game):
        sizewindow.Popup(self.tkWindow, game, self)

    def open_version_picker(self, game):
        webbrowser.open( GAME_VERSIONS_URL.format(id=game.id) )

    ####################### Progress bar functions
    
    def make_progressbar(self, parent):
        self.progressPct = Tk.DoubleVar(0.0)
        self.tkProgressActives = {}
    
        self.tkProgressFrm = ttk.Frame(parent)
        self.tkProgressLabel = ttk.Label(self.tkProgressFrm)
        self.tkProgressLabel.grid(row=0, column=0)
        self.tkProgressBarSpinner = ttk.Progressbar(self.tkProgressFrm, mode="indeterminate", length=200)
        self.tkProgressBarSpinner.start() # will never stop
        self.tkProgressBarPct = ttk.Progressbar(self.tkProgressFrm, mode="determinate", length=200
                                            , variable=self.progressPct)
        self.tkProgressBarSpinner.start() # will never stop
        self.tkProgressBarPct.grid(row=1, column=0)
        self.tkProgressBarSpinner.grid(row=2, column=0)
        self.tkProgressMsg = ttk.Label(self.tkProgressFrm)
        self.tkProgressMsg.grid(row=3, column=0)
        
    def _update_work(self):
        try:
            key = max(self.tkProgressActives, key=lambda key: self.tkProgressActives[key])
            label, ignored = self.tkProgressActives[key]
            
            needProgress = False
            needSpinner = False
            for ignored, (ignored, progress) in self.tkProgressActives.items():
                if progress:
                    needProgress = True
                else:
                    needSpinner = True
            
            if needProgress:
                self.tkProgressBarPct.grid(row=1, column=0)
            else:
                self.tkProgressBarPct.grid_forget()
            
            if needSpinner:
                self.tkProgressBarSpinner.grid(row=2, column=0)
            else:
                self.tkProgressBarSpinner.grid_forget()

            self.tkProgressLabel.configure(text=label)
            self.tkProgressFrm.pack(anchor=Tk.CENTER, expand=True)
        # progressActives is empty, so turn off the progress bar
        except ValueError:
            self.tkProgressFrm.pack_forget()
        
    def start_work(self, label, type, progress=False):
        """Queues up a progress bar, with priority given to higher-numbered types"""
        # print((threading.current_thread().name, "starts", type, label)
        progresslogger.info("Start %i %s, %s", type, label, progress)
        if type == WorkTypes.MESSAGE:
            self.tkProgressMsg.configure(text=label)
        else:
            self.tkProgressActives[type] = (label,progress)
            self.tkProgressFrm.after(0, self._update_work)
        #self._update_work()

    def set_progress(self, pct):
        #print("Progress", pct, threading.current_thread().getName())
        progresslogger.debug("Percent: %0.4f", pct)
        self.progressPct.set( pct * 100.0 )

    def stop_work(self, type):
        # print((threading.current_thread().name, "stops", type)
        progresslogger.info("Stop %i", type)
        if type == WorkTypes.MESSAGE:
            self.tkProgressMsg.configure(text="")
        try:
            self.tkProgressActives.pop(type)
        except KeyError:
            pass

        self.tkProgressFrm.after(0, self._update_work)
        #self._update_work()

    
            
    ###################### End of progress bar section


threading.current_thread().setName("mainThread")

logger.info("Starting App")
try:
    a = App()
    a.mainloop()
except Exception as e:
    logger.fatal("Exception: {}".format(e), exc_info=True)
logger.info("Left Mainloop")




