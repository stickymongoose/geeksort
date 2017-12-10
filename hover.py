import tkinter as Tk
from PIL import Image
from PIL import ImageTk
from constants import *
import shelf

HOVER_WIDTH=200
HOVER_HEIGHT=220

class Hover:
    inst = None

    def __init__(self, owner):
        self.tkFrame = Tk.Frame(owner, width=HOVER_WIDTH, height=HOVER_HEIGHT)
        #self.frame.pack_propagate(False)
        self.tkLabel = Tk.Label(self.tkFrame, anchor=Tk.N, compound=Tk.BOTTOM)
        self.tkLabel.pack()
        Hover.inst = self # singleton

        self.lastSet = None
        # In the event the user can mouse quickly enough, just hide this
        # then it'll adjust for the ones underneath it and redraw it in the right place
        self.tkFrame.bind("<Enter>", self.onClear)
        self.tkLabel.bind("<Enter>", self.onClear)

    def set_image(self, imgfile):
        w = 0
        if imgfile is not None:
            self.tkLabel.img = imgfile
            if isinstance(imgfile, str):
                imgfile = Image.open(imgfile)
                self.tkLabel.img = ImageTk.PhotoImage(imgfile)
            w = self.tkLabel.img.width()
        else:
            self.tkLabel.img = ""

        self.tkLabel.configure(image=self.tkLabel.img, wraplength=w)

    def set(self, caller):
        if self.lastSet is caller:
            return

        self.lastSet = caller

        try:
            self.tkLabel.config(text=caller.hovertext)
        except AttributeError:
            self.tkLabel.config(text="")

        try:
            self.set_image(caller.hoverimgTk)
        except AttributeError:
            try:
                self.set_image(caller.hoverimgurl)
            except AttributeError:
                self.set_image(None)

        self.tkLabel.update()
        #print("Entered", caller.name, len(self.stack))

    def onClear(self, event):
        self.tkFrame.place_forget()

    def onMove(self, caller, event):
        self.set(caller)

        # get the mouse's location on the current window
        win = self.tkFrame.winfo_toplevel()
        winx = win.winfo_rootx()
        winy = win.winfo_rooty()
        xpos = event.x_root - winx
        ypos = event.y_root - winy

        # determine if the text would run off the edge
        #texth = HOVER_HEIGHT
        #textw = HOVER_WIDTH
        texth = self.tkLabel.winfo_height()
        textw = self.tkLabel.winfo_width()

        #print("onMove", textw, texth)
        EXTRA_X = 25 # a few extra pixels to eliminate some grossness
        #if xpos + textw + EXTRA_X >= win.winfo_width():
        if xpos > win.winfo_width() // 2:
            xpos -= textw + EXTRA_X
        else:
            xpos += EXTRA_X

        EXTRA_Y = 5
        #print(ypos, texth, win.winfo_height())
        #if ypos + (texth) >= win.winfo_height():
        if ypos > win.winfo_height() // 2:
            ypos -= texth + EXTRA_Y
        else:
            ypos += EXTRA_Y


        xpos = max(0, xpos)
        xpos = min(xpos, win.winfo_width()-textw)

        ypos = max(0, ypos)
        ypos = min(ypos, win.winfo_height()-texth)

        self.tkFrame.place(anchor=Tk.NW, x=xpos, y=ypos)






