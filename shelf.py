import tkinter as Tk
from constants import *
from enum import IntEnum
import hover
import game
import pathlib
import pickle
import sorts
import logging
logger = logging.getLogger(__name__)
verboselogger = logger.getChild("verbose")

from contrib.mixed_fractions import Mixed


_verbose = False
_app = None

class StoreStyle(IntEnum):
    SideOnly    = 0
    PreferSide  = 1
    PreferStack = 2
    StackOnly   = 3

StoreStyle_names = ["Vertical Only", "Prefer Vertical", "Prefer Horizontal", "Horizontal Only"]
StoreStyle_pics = ["pics/vert_only.png", "pics/vert_first.png", "pics/horiz_first.png", "pics/horiz_only.png"]


class StackSort(IntEnum):
    Weight = 0
    Size   = 1

StackSort_names = ["Weight", "Size"]
StackSort_pics = ["pics/weight.png", "pics/size.png"]

class Bookcase:
    def __init__(self, line, ismetric):
        bits = line.split()
        # since spaces are parsed out, we gotta use hyphens or underscores to separate
        bits = [b.replace("-", " ").replace("_", " ") for b in bits]
        self.shelves = []
        self.name = bits[0]

        self.width = float(Mixed(bits[1]))
        depth = float(Mixed(bits[2]))
        heights = [ float(Mixed(h)) for h in bits[3:] ]
        self.height = 0.0

        self.tkCase = None

        # native BGG dimensions are inches, so... we'll honor that
        if ismetric:
            self.width *= CM_TO_IN
            depth *= CM_TO_IN
            heights = [ h * CM_TO_IN for h in heights ]

        for i in range(len(heights)):
            name = "{}-{}".format(self.name,  i+1)
            self.shelves.append( Shelf( name, self.width, heights[i], depth ) )
            self.height += heights[i]

    def __getstate__(self):
        s = self.__dict__.copy()
        del s['tkCase']
        return s

    def __setstate__(self, dict):
        logger.info("Unpickling Bookcase state")
        dict['tkCase'] = None
        self.__dict__.update(dict)

    def thaw(self, gamedb):
        for s in self.shelves:
            s.thaw(gamedb)

    def try_box(self, box):
        for shelf in self.shelves:
            if shelf.try_box(box):
                return True
        return False

    def finish(self):
        for shelf in self.shelves:
            shelf.finish()

    def get_used(self):
        used = 0.0
        total = 0.0
        for s in self.shelves:
            used += s.usedarea
            total += s.totalarea
        return used, total

    def make_shelf_widgets(self, owner):
        if self.tkCase is not None:
            logger.info("%s told to make its widgets, but already had them.", self.name)
            return
        
    
        border=BOOKCASE_BORDER
        self.tkCase = Tk.Frame(owner
                               #, width=(self.width*IN_TO_PX)+(border*2)
                               , bg=CASE_COLOR, border=border
                               , relief=Tk.RAISED)

        self.tkCase.pack(side=Tk.LEFT, anchor=Tk.SW, padx=5)
        self.tkCase.bind("<Motion>", hover.Hover.inst.onClear)

        text = Tk.Label(self.tkCase, text=self.name, bg=CASE_COLOR)
        text.grid(row=0, pady=0)
        for si in range(len(self.shelves)):
            s = self.shelves[si]
            s.make_widget(self.tkCase, si + 1)
        logger.info("%s told to make its widgets: %r", self.name, self.tkCase)

    def make_game_widgets(self):
        for s in self.shelves:
            s.make_game_widgets()


    def clear_games(self):
        # reversed for speed and if/when we thread the UI we don't see them disappear and reshuffle
        for s in reversed(self.shelves):
            s.clear_games()

    def clear_widgets(self):
        logger.info("%s clearing its widgets", self.name)
        self.clear_games()
        try:
            self.tkCase.destroy()
        except:
            pass
        self.tkCase = None

    def search(self, text):
        sum = 0
        for s in self.shelves:
            sum += s.search(text)
        return sum

class GameStack:
    sortmethod = StackSort.Size

    @staticmethod
    def setStackSort(method:StackSort):
        GameStack.sortmethod = method

    def __init__(self, name, w:float,h:float):
        self.name = name
        self.width=w
        self.maxheight=h
        self.heightleft = self.maxheight
        self.games = []
        self.tkFrame = None
        self.vprint("created {}w {}h".format(w, h) )

    def __getstate__(self):
        s = self.__dict__.copy()
        del s['tkFrame']
        thaw_list = game.freeze_games(s['games'])
        del s['games']
        s['thaw_list'] = thaw_list
        return s

    def __setstate__(self, dict):
        logger.info("Unpickling GameStack state")
        dict['tkFrame'] = None
        dict['games'] = []
        self.__dict__.update(dict)

    def thaw(self, gamedb):
        self.games = game.thaw_games(gamedb, self.thaw_list)
        delattr(self, "thaw_list")


    def vprint(self, *args,  **kwargs):
        verboselogger.debug("%s:%s", self.name, " ".join(str(s) for s in args))

    def try_box(self, box: game.Game):
        # if the box is too tall, just bail
        if box.z > self.heightleft:
            self.vprint(box,  "failed stack height",  box.z,  self.heightleft)
            return False

        # try the smallest dimension
        if box.x < box.y:
            if box.x <= self.width:
                self.add_box(box, game.HorizLong)
                self.vprint(box,  "passed stack xz",   box.x,  self.width )
                return True

        elif box.y <= self.width:
            self.add_box(box, game.HorizShort)
            self.vprint(box,  "passed stack yz",   box.y,  self.width )
            return True

        self.vprint(box.name, "didn't fit ",  self.name)
        return False

    def add_box(self, box, dir):
        box.set_dir(dir)
        self.games.append(box)
        self.heightleft -= box.shelfheight

    def finish(self):
        if GameStack.sortmethod == StackSort.Weight:
            self.games.sort(key=sorts.Weight,  reverse=True)

        elif GameStack.sortmethod == StackSort.Size:
            # sort by the size of the stack's dimensions
            self.games.sort(key=lambda s:s.shelfwidth, reverse=True)

    def make_widgets(self, owner, shelf=None, index=None):
        self.tkFrame = Tk.Frame(owner)

        if shelf is not None:
            self.tkFrame.configure(bg=SHELF_COLOR)
            self.tkFrame.pack(side=Tk.LEFT, anchor=Tk.S)
            self.tkFrame.bind("<Motion>", shelf.onMove)
            self.tkFrame.bind("<Button-1>", shelf.onClick)
        else:
            self.tkFrame.pack(side=Tk.LEFT, anchor=Tk.SW, padx=SHELF_SPACING)

        for g in self.games:
            g.make_widget(self.tkFrame, center=True)

    def hide(self):
        try:
            self.tkFrame.pack_forget()
        except AttributeError:
            pass

    def clear_games(self):
        for g in reversed(self.games):
            g.clear_widget()

        try:
            self.tkFrame.pack_forget()
            self.tkFrame.destroy()
        except AttributeError: pass

        self.games = []
        self.heightleft = self.maxheight

    def search(self, text):
        sum = 0
        for g in self.games:
            sum += g.search(text)

        return sum


class Shelf:
    sortlist = []

    def __init__(self, name, width, height, depth):
        self.name = name
        self.maxwidth = width
        self.height = height
        self.depth = depth
        self.widthleft = self.maxwidth
        self.games = []
        self.stacks = []
        self.totalarea = self.maxwidth * self.height
        self.usedarea = 0.0
        self.weight = 0.0
        self.wreported = 0
        self.tkShelf = None
        self.frmwidth = 0.0
        self.hovertext = ""

    def __getstate__(self):
        s = self.__dict__.copy()
        del s['tkShelf']
        thaw_list = game.freeze_games(s['games'])
        del s['games']
        s['thaw_list'] = thaw_list
        return s
        
    def __setstate__(self, dict):
        logger.info("Unpickling Shelf state")
        dict['tkShelf'] = None
        dict['games'] = []
        self.__dict__.update(dict)

    def thaw(self, gamedb):
        self.games = game.thaw_games(gamedb, self.thaw_list)
        delattr(self, "thaw_list")

        for s in self.stacks:
            s.thaw(gamedb)

    def vprint(self, *args,  **kwargs):
        verboselogger.debug("%s:%s", self.name, " ".join(str(s) for s in args))

    def add_box_lite(self, box):
        self.usedarea += (box.shelfwidth * box.shelfheight)

        if box.w > 0.0:
            self.weight += box.w
            self.wreported += 1

    def add_box(self, box, dir):
        box.set_dir(dir)
        self.add_box_lite(box)
        self.games.append(box)
        self.widthleft -= box.shelfwidth

    @staticmethod
    def set_store_style(style:StoreStyle):
        if style == StoreStyle.PreferSide:
            Shelf.sortlist = [Shelf.try_vertical, Shelf.try_stack]

        elif style == StoreStyle.PreferStack:
            Shelf.sortlist = [Shelf.try_stack, Shelf.try_vertical]

        elif style == StoreStyle.SideOnly:
            Shelf.sortlist = [Shelf.try_vertical]

        elif style == StoreStyle.StackOnly:
            Shelf.sortlist = [Shelf.try_stack]

        else:
            raise ValueError("Invalid StoreStyle: " + str(style))

    def try_vertical(self, box):
        # early out if the box is too wide
        if box.z > self.widthleft:
            return False

        # pick smallest to see if it fits
        if box.y < box.x:
            if box.y <= self.height:
                self.vprint(box,  "passed zy {}<={}, {}<={}".format(
                    box.z,  self.widthleft,
                    box.y,  self.height))
                self.add_box(box, game.VerticalLong)
                return True

        elif box.x <= self.height:
            self.vprint(box,  "passed zx {}<={}, {}<={}".format(
                box.z,  self.widthleft,
                box.x,  self.height))
            self.add_box(box, game.VerticalShort)
            return True
        return False

    def try_stack(self, box):
        # early out if the box is too tall
        if box.z > self.height:
            return False

        # check the smallest dimension
        if box.x < box.y:
            if box.x <= self.widthleft:
                self.vprint(box,  "passed xz {}<={}, {}<={}".format(
                    box.z,  self.height,
                    box.x,  self.widthleft))
                self.add_stack(box, game.HorizShort)
                return True

        elif box.y <= self.widthleft:
            self.vprint(box,  "passed yz {}<={}, {}<={}".format(
                    box.z,  self.height,
                    box.y,  self.widthleft))
            self.add_stack(box, game.HorizLong)
            return True

        return False

    def try_box(self, box):
        # if there's already stacks, check 'em out
        for s in self.stacks:
            if s.try_box(box):
                self.add_box_lite(box)
                return True

        for sortfunc in Shelf.sortlist:
            if sortfunc(self, box):
                return True

        # if the box didn't fit on its side, we can reject if it won't fit by height

        self.vprint("couldn't fit", box)
        return False

    def finish(self):
        for s in self.stacks:
            s.finish()

    def search(self, text):
        count = 0
        for s in self.stacks:
            count += s.search(text)

        for g in self.games:
            count += g.search(text)

        if count > 0:
            self.tkShelf.configure(bg=FOUND_COLOR)
            for st in self.stacks:
                st.tkFrame.configure(bg=FOUND_COLOR)
        else:
            self.tkShelf.configure(bg=SHELF_COLOR)
            for st in self.stacks:
                st.tkFrame.configure(bg=SHELF_COLOR)
        return count

    def add_stack(self, box: game.Game, dir):
        box.set_dir(dir)
        stackname = "{}-{}".format(self.name,  len(self.stacks)+1)
        self.vprint("made stack",  stackname,  box, dir, box.shelfwidth)
        stack = GameStack( stackname,  box.shelfwidth, self.height )
        self.stacks.append( stack )
        self.widthleft -= box.shelfwidth
        stack.add_box(box, dir)
        self.add_box_lite(box)


    def make_widget(self, case, row):
        border = SHELF_BORDER

        height = (self.height * IN_TO_PX) + (border * 2.0)
        self.frmwidth = int((self.maxwidth * IN_TO_PX) + (border * 2.0) + 1 + SHELF_FUDGE_WIDTH)
        #print(self.name, self.frmwidth, height)
        self.tkShelf = Tk.Frame(case
                                , height=height
                                , width =self.frmwidth
                                , bg=SHELF_COLOR
                                , border=border
                                , relief=Tk.SUNKEN
                                #, relief=Tk.FLAT
                                )
        self.tkShelf.grid(row=row, pady=3, padx=SHELF_SPACING)
        self.tkShelf.pack_propagate(False)
        self.tkShelf.bind("<Motion>", self.onMove)
        self.tkShelf.bind("<Button-1>", self.onClick)

        self.hovertext="""{name}-{row}
{w}" x {h}" x {d}"
{usedwidth}" / {w}" used by {total} games
{used:3.0f}% of space utilized
{weight}{plus} lbs, ({wcnt}/{total})""".format(
            name=self.name, row=row
            , w=makeFraction(self.maxwidth), h=makeFraction(self.height), d=makeFraction(self.depth)
            , usedwidth=makeFraction(self.maxwidth - self.widthleft)
            , plus="+" if self.wreported < len(self.games) else ""
            , weight=makeFraction(self.weight), wcnt=self.wreported
            , total=len(self.games)
            , used=(self.usedarea / self.totalarea)*100.0)

    def clear_widgets(self):
        self.clear_games()
        self.tkShelf.destroy()
        self.tkShelf = None

    def make_game_widgets(self):
        for st in self.stacks:
            st.make_widgets(self.tkShelf, self)

        for g in self.games:
            g.make_widget(self.tkShelf)

    def clear_games(self):
        for st in self.stacks:
            st.clear_games()

        for g in self.games:
            g.clear_widget()

        self.widthleft = self.maxwidth
        self.usedarea = 0.0
        self.weight = 0.0
        self.wreported = 0

        self.stacks = []
        self.games = []

    def onMove(self, event):
        hover.Hover.inst.onMove(self, event)

    def onClick(self, event):
        total_width = 0.0
        total_realwidth = 0.0
        print("###", self.name)
        for st in self.stacks:
            print(st.name,  st.games[0].lblwidth, st.games[0].shelfwidth)
            total_width += st.games[0].lblwidth
            total_realwidth += st.games[0].shelfwidth
            for g in st.games:
                print("\t",  g.name)


        for g in self.games:
            print(g.name,  g.lblwidth, g.shelfwidth)
            total_width += g.lblwidth
            total_realwidth += g.shelfwidth

        print(total_width, self.frmwidth, total_realwidth, self.maxwidth)
        print("###", self.name)

def read(filename):
    cases = []

    with open(filename, "r") as f:
        metric = False
        for line in f.read().splitlines():
            line = line.strip()
            if line.startswith('#'):
                continue
            if len(line) == 0:
                continue
            if line.lower().startswith('unit'):
                if "cm" in line.lower():
                    metric = True
                continue
            bc = Bookcase(line, metric)
            cases.append(bc)
    return cases


def load(user, gamedb):
    try:
        with open(pathlib.Path(CACHE_DIR) / "shelves_{}.pkl".format(user), "rb") as file:
            cases = pickle.load(file)
            stack = pickle.load(file)
            for c in cases:
                c.thaw(gamedb)
            stack.thaw(gamedb)
            return cases, stack
    except (FileNotFoundError, EOFError):
        # expected, totally okay if it's not here
        pass

    except pickle.UnpicklingError as e:
        logger.exception("Pickle error {}".format(e))

    return None, None


def save(user, cases, stacks):
    try:
        with open(pathlib.Path(CACHE_DIR) / "shelves_{}.pkl".format(user), "wb") as file:
            pickle.dump(cases, file)
            pickle.dump(stacks, file)

    except (TypeError, pickle.PicklingError) as e:
        print(e)
