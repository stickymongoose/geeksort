import tkinter as Tk
import tkinter.ttk as ttk
import math

from constants import *


class ScrollableList:
    starImage = None

    def __init__(self, owner: ttk.Notebook, title, highestshelf, values, actionfunc, casecount):
        self.frm = Tk.Frame(owner, height=math.ceil(highestshelf*IN_TO_PX), width=200, border=2, relief=Tk.SUNKEN)
        self.frm.pack_propagate(False)
        owner.add(self.frm, text=title, compound=Tk.TOP)
        self.tabid = owner.index(Tk.END)-1 # bit of a kludge to get the tabid, since I'm not sure why .add doesn't return it...
        self.title = title
        self.owner = owner

        print(title, self.tabid)

        self.list = Tk.Listbox(self.frm)
        for g in values:
            self.list.insert(Tk.END, g.longname)
            g.make_image()
        self.list.pack(side=Tk.LEFT, fill=Tk.BOTH, expand=True)
        self.list.values = values
        self.list.bind("<Double-Button-1>", lambda evnt:actionfunc(evnt.widget.values[evnt.widget.curselection()[0]]))

        scroll = Tk.Scrollbar(self.frm)
        scroll.pack(side=Tk.RIGHT, fill=Tk.Y)

        self.list.config(yscrollcommand=scroll.set)
        scroll.config(command=self.list.yview)

        casecount += 1

    def search(self, text):
        matches = 0
        for i in range(len(self.list.values)):
            g = self.list.values[i]
            if g.search(text):
                matches += 1
                self.list.itemconfig(i, {"bg":"yellow"})
            else:
                self.list.itemconfig(i, {"bg":"white"}) # assumption, this is the original color


        if matches > 0:
            if ScrollableList.starImage == None:
                ScrollableList.starImage = Tk.PhotoImage(file="pics/found.gif")
            self.owner.tab(self.tabid, image=ScrollableList.starImage) # seemingly no way to color code a tab...
        else:
            self.owner.tab(self.tabid, image="")

        return matches


