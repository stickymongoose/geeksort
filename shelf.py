import tkinter as Tk
from constants import *
from enum import Enum
import hover
import game


_verbose = False

class StoreStyle(Enum):
    UprightOnly   = 1
    PreferUpright = 2
    PreferStack   = 3
    StackOnly     = 4

class StackSort(Enum):
    Weight = 1
    Size   = 2

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

    def trybox(self, box: game.Game):
        if box.z > self.heightleft:
            self.vprint(box,  "failed stack height",  box.z,  self.heightleft)
            return False

        if box.x <= self.width:
            self.addbox(box, "xz")
            self.vprint(box,  "passed stack xz",   box.x,  self.width )
            return True

        if box.y <= self.width:
            self.addbox(box, "yz")
            self.vprint(box,  "passed stack yz",   box.y,  self.width )
            return True

        self.vprint(box.name, "didn't fit ",  self.name)
        return False

    def addbox(self, box, dir):
        box.setdir( dir )
        self.games.append(box)
        self.heightleft = self.heightleft - box.shelfheight

    def finish(self):
        if GameStack.sortmethod == StackSort.Weight:
            self.games.sort(key=lambda s:s.w,  reverse=True)

        elif GameStack.sortmethod == StackSort.Size:
            # sort by the size of the stack's dimensions
            self.games.sort(key=lambda s:s.shelfwidth, reverse=True)

    def makewidgets(self,  owner, shelf):
        self.frame = Tk.Frame(owner, bg=SHELF_COLOR)
        self.frame.pack(side=Tk.LEFT,anchor=Tk.S)
        self.frame.bind("<Enter>", shelf.onEnter )
        self.frame.bind("<Button-1>", shelf.onClick )

        for g in self.games:
            g.makewidget(self.frame, center=True)


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

    def addboxlite(self, box):
        self.usedarea = self.usedarea + (box.shelfwidth * box.shelfheight)

        if box.w > 0.0:
            self.weight = self.weight + box.w
            self.wreported = self.wreported + 1

    def addbox(self, box, dir):
        box.setdir( dir )
        self.addboxlite(box)
        self.games.append(box)
        self.widthleft = self.widthleft - box.shelfwidth

    @staticmethod
    def setStoreStyle(style:StoreStyle):
        if style == StoreStyle.PreferUpright:
            Shelf.sortlist = [Shelf.tryVertical, Shelf.tryStack]
        elif style == StoreStyle.PreferStack:
            Shelf.sortlist = [Shelf.tryStack, Shelf.tryVertical]
        elif style == StoreStyle.UprightOnly:
            Shelf.sortlist = [Shelf.tryVertical]
        elif style == StoreStyle.StackOnly:
            Shelf.sortlist = [Shelf.tryStack]
        else:
            raise ValueError("Invalid StoreStyle: " + style)

    @staticmethod
    def tryVertical(self, box):
        if box.z <= self.widthleft:
            if box.y <= self.height:
                self.vprint(box,  "passed zy {}<={}, {}<={}".format(
                    box.z,  self.widthleft,
                    box.y,  self.height))
                self.addbox(box, "zy")
                return True

            if box.x <= self.height:
                self.vprint(box,  "passed zx {}<={}, {}<={}".format(
                    box.z,  self.widthleft,
                    box.x,  self.height))
                self.addbox(box, "zx")
                return True
        return False

    @staticmethod
    def tryStack(self, box):
        if box.z <= self.height:
            if box.x <= self.widthleft:
                self.vprint(box,  "passed xz {}<={}, {}<={}".format(
                    box.z,  self.height,
                    box.x,  self.widthleft))
                self.addstack(box,  "xz")
                return True

        # or the other?
        if box.y <= self.widthleft:
            self.vprint(box,  "passed yz {}<={}, {}<={}".format(
                    box.z,  self.height,
                    box.y,  self.widthleft))
            self.addstack(box,  "yz")
            return True

    def trybox(self,box):
        # if there's already stacks, check 'em out
        for s in self.stacks:
            if s.trybox(box):
                self.addboxlite(box)
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

    def addstack(self,  box: game.Game,  dir ):
        box.setdir(dir)
        stackname = "{}-{}".format(self.name,  len(self.stacks)+1)
        self.vprint("made stack",  stackname,  box, dir, box.shelfwidth)
        stack = GameStack( stackname,  box.shelfwidth, self.height)
        self.stacks.append( stack )
        self.widthleft = self.widthleft - box.shelfwidth
        stack.addbox(box,  dir)
        self.addboxlite(box)


    def addwidget(self, case, row):
        self.shlf = Tk.Frame(case
                         , height=self.height*SCALAR
                         , width=self.maxwidth*SCALAR
                         , bg=SHELF_COLOR, border=3, relief=Tk.SUNKEN)
        self.shlf.grid(row=row,pady=3,padx=5)
        self.shlf.pack_propagate(False)
        self.shlf.bind("<Enter>", self.onEnter)
        self.shlf.bind("<Button-1>", self.onClick)
        self.hovertext="{name}-{row}\n{w} x {h} x {d}\n{weight}{plus} lbs, ({wcnt}/{total})\n{used:3.0f}% Used".format(
            name=self.name, row=row
            , w=self.maxwidth, h=self.height, d=self.depth
            , plus="+" if self.wreported < len(self.games) else ""
            , weight=self.weight, wcnt=self.wreported, total = len(self.games)
            , used=(self.usedarea / self.totalarea)*100.0)

        for st in self.stacks:
            st.makewidgets(self.shlf, self)

        for g in self.games:
            g.makewidget(self.shlf)

    def onEnter(self, event):
        hover.Hover.inst.onEnter(self, event, [self.shlf]+[s.frame for s in self.stacks] )

    def onLeave(self, event):
        hover.Hover.inst.onLeave(self, event, [self.shlf]+[s.frame for s in self.stacks] )

    def onClick(self, event):
        print("###", self.name,"###")
        for st in self.stacks:
            print(st.name)
            for g in st.games:
                print("\t",  g.name)

        for g in self.games:
            print(g.name)

