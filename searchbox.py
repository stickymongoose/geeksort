import tkinter as Tk
from constants import *

class SearchBox(Tk.LabelFrame):
    def __init__(self, window):
        Tk.LabelFrame.__init__(self, window, text="Search Function")
        self.box = Tk.Entry(self,  width=100)
        self.box.pack(side=Tk.LEFT,  anchor=Tk.NW, pady=5, padx=5)
        self.requestid = 0

        self.results = Tk.Label(self, width=15)
        self.results.pack(side=Tk.LEFT, anchor=Tk.NW, pady=5, padx=2)

        self.box.bind("<Key>", self.typed)
        self.box.bind("<Return>", self.search)

        self.searchlist = []

    def register(self, searchable):
        self.searchlist.append(searchable)

    def unregister(self, unwanted):
        self.searchlist.remove(unwanted)

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
