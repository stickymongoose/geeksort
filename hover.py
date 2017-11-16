import tkinter as Tk
from PIL import Image
from PIL import ImageTk
from constants import *
import shelf

class Hover:
    inst = None

    def __init__(self, owner):
        self.label = Tk.Label(owner, anchor=Tk.NW, compound=Tk.BOTTOM)
        self.stack = []
        Hover.inst = self # singleton
        self.dbglvl = Tk.Label(owner, anchor=Tk.NE)
        self.dbglvl.place(relx=1.0,  rely=0.0, anchor=Tk.NE)
        self.dbglvl.bind("<Button-1>", self.stackwipe)

    def setdbg(self):
        self.dbglvl.configure(text=str(len(self.stack))+"\n"+"\n".join(e.name for e in self.stack))

    def stackwipe(self, event):
        self.stack = []
        self.setdbg()

    def setimage(self, imgfile):
        w = 0
        if imgfile != None:
            imgraw = Image.open(imgfile)
            self.label.img = ImageTk.PhotoImage(imgraw)
            w = imgraw.size[0]
        else:
            self.label.img = ""

        self.label.configure(image=self.label.img, wraplength=w)

    def onEnter(self, caller, event, afflicted):
        self.label.after(200, self.onEnter_, caller, event, afflicted)

    def onEnter_(self, caller, event, afflicted):
        try:
            self.label.config(text=caller.hovertext)
        except AttributeError:
            self.label.config(text=None)

        try:
            self.setimage(caller.hoverimg)
        except AttributeError:
            self.setimage(None)

        self.label.update()

        self.onMove(event)

        if isinstance(caller, shelf.Shelf):
            self.stack = [caller]
        elif len(self.stack)!=0:
            self.stack = [self.stack[0],  caller]
        else:
            self.stack = [caller]

        for a in afflicted:
            a.bind("<Motion>", self.onMove)

        afflicted[0].bind("<Leave>", caller.onLeave)
        self.setdbg()
        #print("Entered", caller.name, len(self.stack))

    def onLeave(self, leaver, event, afflicted):

        for a in afflicted:
            a.unbind("<Motion>")
        #    a.unbind("<Leave>")

        #print("Left", leaver.name)
        # if we've left the topmost item, pop it and show the next
        try:
            self.stack.remove(leaver)
           # print("onLeave",  leaver.name,   len(self.stack))

            if len(self.stack) != 0:
                top(self.stack).onEnter(event)
            else:
                self.label.place_forget()
        except ValueError:
            #print("onLeave#",  leaver.name,   len(self.stack))
            pass


        self.setdbg()


    def onMove(self,event):
        # get the mouse's location on the current window
        win = self.label.winfo_toplevel()
        winx = win.winfo_rootx()
        winy = win.winfo_rooty()
        xpos = event.x_root - winx
        ypos = event.y_root - winy

        # determine if the text would run off the edge
        texth = self.label.winfo_height()
        textw = self.label.winfo_width()
        #print("onMove", textw, texth)
        EXTRA_X = 25 # a few extra pixels to eliminate some grossness
        #if xpos + textw + EXTRA_X >= win.winfo_width():
        if xpos > win.winfo_width() // 2:
            xpos = xpos - textw - EXTRA_X
        else:
            xpos = xpos + EXTRA_X

        EXTRA_Y = 5
        #print(ypos, texth, win.winfo_height())
        #if ypos + (texth) >= win.winfo_height():
        if ypos > win.winfo_height() // 2:
            ypos = ypos - texth - EXTRA_Y
        else:
            ypos = ypos + EXTRA_Y


        xpos = max(0, xpos)
        xpos = min(xpos, win.winfo_width()-textw)

        ypos = max(0, ypos)
        ypos = min(ypos, win.winfo_height()-texth)

        self.label.place(anchor=Tk.NW, x=xpos, y=ypos)






