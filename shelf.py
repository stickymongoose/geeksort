import tkinter as Tk
from constants import *
from enum import Enum
import hover
import game


_verbose = False

class StoreStyle(Enum):
    SideOnly   = 1
    PreferSide = 2
    PreferStack   = 3
    StackOnly     = 4

class StackSort(Enum):
    Weight = 1
    Size   = 2

class Bookcase:
    def __init__(self, line):
        bits = line.split('\t')
        self.shelves = []
        self.name = bits[0]
        self.width = float(bits[1])
        depth = bits[2]
        heights = bits[3:]
        self.height = 0
        for i in range(len(heights)):
            name = "{}-{}".format(self.name,  i+1)
            self.shelves.append( Shelf(  name, self.width, heights[i], depth ) )
            self.height += float(heights[i])

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

    def make_shelf_widgets(self, owner, index):
        border=BOOKCASE_BORDER
        self.case = Tk.Frame(owner
                        #, width=(self.width*IN_TO_PX)+(border*2)
                        , bg=CASE_COLOR, border=border
                        , relief=Tk.RAISED)

        self.case.pack(side=Tk.LEFT, anchor=Tk.SW, padx=5)

        text = Tk.Label(self.case, text=self.name, bg=CASE_COLOR)
        text.grid(row=0, pady=0)

    def make_game_widgets(self):
        for si in range(len(self.shelves)):
            s = self.shelves[si]
            s.make_widget(self.case, si + 1)

    def clear_games(self):
        for s in self.shelves:
            s.clear_games()

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
        self.vprint("{}w {}h".format(w, h) )

    def vprint(self, *args,  **kwargs):
        if _verbose:
            print(self.name,  ":", args,  **kwargs)

    def try_box(self, box: game.Game):
        if box.z > self.heightleft:
            self.vprint(box,  "failed stack height",  box.z,  self.heightleft)
            return False

        if box.x <= self.width:
            self.add_box(box, "xz")
            self.vprint(box,  "passed stack xz",   box.x,  self.width )
            return True

        if box.y <= self.width:
            self.add_box(box, "yz")
            self.vprint(box,  "passed stack yz",   box.y,  self.width )
            return True

        self.vprint(box.name, "didn't fit ",  self.name)
        return False

    def add_box(self, box, dir):
        box.set_dir(dir)
        self.games.append(box)
        self.heightleft = self.heightleft - box.shelfheight

    def finish(self):
        if GameStack.sortmethod == StackSort.Weight:
            self.games.sort(key=lambda s:s.w,  reverse=True)

        elif GameStack.sortmethod == StackSort.Size:
            # sort by the size of the stack's dimensions
            self.games.sort(key=lambda s:s.shelfwidth, reverse=True)

    def make_widgets(self, owner, shelf=None, index=None):
        self.frame = Tk.Frame(owner, bg=SHELF_COLOR)

        if shelf is not None:
            self.frame.pack(side=Tk.LEFT, anchor=Tk.S)
            self.frame.bind("<Motion>", shelf.onMove )
            self.frame.bind("<Button-1>", shelf.onClick )
        else:
            self.frame.pack(side=Tk.LEFT, anchor=Tk.SW, padx=5)

        for g in self.games:
            g.make_widget(self.frame, center=True)

    def clear_games(self):
        for g in self.games:
            g.clear_widget()

        self.games = []

    def search(self, text):
        sum = 0
        for g in self.games:
            sum += g.search(text)

        return sum

class Shelf:
    sortlist = []

    def __init__(self,name,width,height,depth):
        self.name = name
        self.maxwidth = float(width)
        self.height = float(height)
        self.depth = float(depth)
        self.widthleft = self.maxwidth
        self.games = []
        self.stacks = []
        self.totalarea = self.maxwidth * self.height
        self.usedarea = 0.0
        self.weight = 0.0
        self.wreported = 0

    def vprint(self, *args,  **kwargs):
        if _verbose:
            print(self.name,  ":", args,  **kwargs)

    def __repr__(self):
        return u"%s %.1f (%.1f) x %.1f x %.1f (%s)" % (self.name, self.maxwidth, self.widthleft, self.height, self.depth, ", ".join(map(str, self.games)))

    def __str__(self):
        return u"%s %.1f (%.1f) x %.1f x %.1f (%s)" % (self.name, self.maxwidth, self.widthleft, self.height, self.depth, ", ".join(map(str, self.games)))

    def add_box_lite(self, box):
        self.usedarea = self.usedarea + (box.shelfwidth * box.shelfheight)

        if box.w > 0.0:
            self.weight = self.weight + box.w
            self.wreported = self.wreported + 1

    def add_box(self, box, dir):
        box.set_dir(dir)
        self.add_box_lite(box)
        self.games.append(box)
        self.widthleft = self.widthleft - box.shelfwidth

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
            raise ValueError("Invalid StoreStyle: " + style)

    @staticmethod
    def try_vertical(self, box):
        if box.z <= self.widthleft:
            if box.y <= self.height:
                self.vprint(box,  "passed zy {}<={}, {}<={}".format(
                    box.z,  self.widthleft,
                    box.y,  self.height))
                self.add_box(box, "zy")
                return True

            if box.x <= self.height:
                self.vprint(box,  "passed zx {}<={}, {}<={}".format(
                    box.z,  self.widthleft,
                    box.x,  self.height))
                self.add_box(box, "zx")
                return True
        return False

    @staticmethod
    def try_stack(self, box):
        if box.z <= self.height:
            if box.x <= self.widthleft:
                self.vprint(box,  "passed xz {}<={}, {}<={}".format(
                    box.z,  self.height,
                    box.x,  self.widthleft))
                self.add_stack(box, "xz")
                return True

        # or the other?
        if box.y <= self.widthleft:
            self.vprint(box,  "passed yz {}<={}, {}<={}".format(
                    box.z,  self.height,
                    box.y,  self.widthleft))
            self.add_stack(box, "yz")
            return True

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

        self.vprint(box,  "failed")
        return False

    def finish(self):
        for s in self.stacks:
            s.finish()

    def search(self, text):
        sum = 0
        for s in self.stacks:
            sum += s.search(text)

        for g in self.games:
            sum += g.search(text)

        if sum > 0:
            self.shlf.configure(bg=FOUND_COLOR)
            for st in self.stacks:
                st.frame.configure(bg=FOUND_COLOR)
        else:
            self.shlf.configure(bg=SHELF_COLOR)
            for st in self.stacks:
                st.frame.configure(bg=SHELF_COLOR)
        return sum

    def add_stack(self, box: game.Game, dir):
        box.set_dir(dir)
        stackname = "{}-{}".format(self.name,  len(self.stacks)+1)
        self.vprint("made stack",  stackname,  box, dir, box.shelfwidth)
        stack = GameStack( stackname,  box.shelfwidth, self.height)
        self.stacks.append( stack )
        self.widthleft = self.widthleft - box.shelfwidth
        stack.add_box(box, dir)
        self.add_box_lite(box)


    def make_widget(self, case, row):
        border = SHELF_BORDER

        height = (self.height   * IN_TO_PX) + (border * 2.0)
        self.frmwidth = (self.maxwidth * IN_TO_PX) + (border * 2.0)
        #print(self.name, self.frmwidth, height)
        self.shlf = Tk.Frame(case
                         , height=height
                         , width =self.frmwidth
                         , bg=SHELF_COLOR
                         , border=border
                         , relief=Tk.SUNKEN
                         #, relief=Tk.FLAT
                         )
        self.shlf.grid(row=row,pady=3,padx=5)
        self.shlf.pack_propagate(False)
        self.shlf.bind("<Motion>", self.onMove)
        self.shlf.bind("<Button-1>", self.onClick)

        self.hovertext="""{name}-{row}
{w} x {h} x {d}
{usedwidth}/{w}
{weight}{plus} lbs, ({wcnt}/{total})
{used:3.0f}% Used""".format(
            name=self.name, row=row
            , w=self.maxwidth, h=self.height, d=self.depth
            , usedwidth = self.maxwidth - self.widthleft
            , plus="+" if self.wreported < len(self.games) else ""
            , weight=round(self.weight, ROUND_PRECISION), wcnt=round(self.wreported, ROUND_PRECISION), total = len(self.games)
            , used=(self.usedarea / self.totalarea)*100.0)

        for st in self.stacks:
            st.make_widgets(self.shlf, self)

        for g in self.games:
            g.make_widget(self.shlf)

    def clear_games(self):
        for st in self.stacks:
            st.clear_games()

        for g in self.games:
            g.clear_widget()

        self.stacks = []
        self.games = []

    def onMove(self, event):
        hover.Hover.inst.onMove(self, event)

    def onClick(self, event):
        print("###", self.name,"###")
        sum = 0.0
        for st in self.stacks:
            print(st.name,  st.games[0].lblwidth)
            sum += st.games[0].lblwidth
            for g in st.games:
                print("\t",  g.name)


        for g in self.games:
            print(g.name,  g.lblwidth)
            sum += g.lblwidth

        print(sum,  self.frmwidth)

