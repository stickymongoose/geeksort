import tkinter as Tk
import tkinter.ttk as ttk
from constants import *

class SearchBox(Tk.LabelFrame):
    def __init__(self, window):
        Tk.LabelFrame.__init__(self, window, text="Search Function", bg="#f0f0f0")
        self.box = ttk.Entry(self,  width=100)
        self.box.pack(side=Tk.LEFT,  anchor=Tk.NW, pady=5, padx=5)
        self.requestid = 0

        self.results = Tk.Label(self, width=15, bg="#f0f0f0")
        self.results.pack(side=Tk.LEFT, anchor=Tk.NW, pady=5, padx=2)

        self.box.bind("<Key>", self.typed)
        self.box.bind("<Return>", self.search)

        self.searchlist = []

    def focus(self):
        self.box.focus()

    def register(self, searchable):
        self.searchlist.append(searchable)

    def unregister(self, unwanted):
        try:
            self.searchlist.remove(unwanted)
        except ValueError: pass

    def search(self):
        self.requestid = 0
        text = to_search(self.box.get())
        matchcount = 0
        for t in self.searchlist:
            matchcount += t.search(text)
        self.results.configure(text="{} Result{}".format(matchcount, "" if matchcount==1 else "s"))


    def typed(self, event):
        self.box.after_cancel(self.requestid)
        self.requestid = self.box.after(250, self.search)
