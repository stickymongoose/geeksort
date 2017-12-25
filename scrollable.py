import tkinter as Tk
import tkinter.ttk as ttk
import math

from constants import *
import hover

class ScrollableList:
    starImage = None

    def __init__(self, owner: ttk.Notebook, title, highestshelf, actionfunc):
        self.frm = Tk.Frame(owner, height=math.ceil(highestshelf*IN_TO_PX), width=200, border=2, relief=Tk.SUNKEN)
        self.frm.pack_propagate(False)
        owner.add(self.frm, text=title, compound=Tk.TOP)
        self.tabid = owner.index(Tk.END)-1 # bit of a kludge to get the tabid, since I'm not sure why .add doesn't return it...
        self.title = title
        self.owner = owner

        self.tkList = Tk.Listbox(self.frm)
        self.tkList.bind("<Double-Button-1>", lambda evnt:actionfunc(evnt.widget.values[evnt.widget.curselection()[0]]))
        self.tkList.bind("<Button-3>", self.onRClick)
        self.tkList.pack(side=Tk.LEFT, fill=Tk.BOTH, expand=True)
        self.tkList.bind("<Motion>", self.onHover)

        scroll = Tk.Scrollbar(self.frm)
        scroll.pack(side=Tk.RIGHT, fill=Tk.Y)


        self.tkList.config(yscrollcommand=scroll.set)
        scroll.config(command=self.tkList.yview)


    def _convert_to_index(self, event):
        index = self.tkList.index("@{},{}".format(event.x, event.y))

        # there's seemingly a bug where it doesn't return out-of-range indices
        # at the bottom of the window, so we gotta cheat a bit
        if index == len(self.tkList.values)-1:
            (x,y,w,h) = self.tkList.bbox(index)
            if event.y > y+h:
                index = -1

        if index >= 0 and index < len(self.tkList.values):
            return self.tkList.values[index]

        return None


    def onRClick(self, event):
        game = self._convert_to_index(event)
        hover.Hover.inst.onClear(event)

        if game is not None:
            game.onRClick(event)


    def onHover(self, event):
        game = self._convert_to_index(event)

        if game is not None:
            hover.Hover.inst.onMove(game, event)
        else:
            hover.Hover.inst.onClear(event)


    def set_list(self, values):
        self.tkList.delete(0, Tk.END)
        for g in values:
            self.tkList.insert(Tk.END, g.longname)
            g.make_image()
            g.make_lite_hover()
        self.tkList.values = values


    def hide(self):
        self.tkList.pack_forget()

    def search(self, text):
        matches = 0
        for i in range(len(self.tkList.values)):
            g = self.tkList.values[i]
            if g.search(text):
                matches += 1
                self.tkList.itemconfig(i, {"bg": "yellow"})
            else:
                self.tkList.itemconfig(i, {"bg": "white"}) # assumption, this is the original color


        if matches > 0:
            if ScrollableList.starImage == None:
                ScrollableList.starImage = Tk.PhotoImage(file="pics/found.gif")
            self.owner.tab(self.tabid, image=ScrollableList.starImage) # seemingly no way to color code a tab...
        else:
            self.owner.tab(self.tabid, image="")

        return matches


