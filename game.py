#!/usr/bin/env python
# -*- coding: utf-8 -*-
import unicodedata
import re
import tkinter as Tk
import math
from enum import Enum
from PIL import Image
from PIL import ImageTk

from constants import *
import collection
import averagecolor
import hover

def getvalue(node, name):
    return float(node.find(name).get("value"))

def sizevalue(node,name):
    f = getvalue(node, name)
    return math.ceil(f*4)/4.0

def colorbrightness(rgb):
    r = (rgb>>16) & 0xff
    g = (rgb>>8 ) & 0xff
    b = (rgb>>0 ) & 0xff
    y = (2*r + 1*b + 3*g)/(255.0*6.0)
    return y

class SidePreference(Enum):
    Left = 1
    Right = 2

class Game:
    _user = None
    _hover = None
    _sidepreference = SidePreference.Left

    @staticmethod
    def setSidePreference(side:SidePreference):
        Game._sidepreference = side

    def __init__(self, hold):
        elt = hold.find("./version/item")
        # get the unicode name, convert it, re-encode it
        self.name = hold.find("name").text.strip()
        self.name = unicodedata.normalize('NFKD', self.name)
        self.name = self.name.encode('ASCII','ignore').decode()

        # fix up any weird characters/spacing
        self.name = re.sub("\s+\r?\n?"," ", self.name)
        self.name = self.name.replace(u"–", "-")
        self.name = self.name.replace("&amp;","&")
        self.name = self.name.replace("&#039;","'")
        self.id = int(hold.get("objectid"))

        self.longname = self.name
        #self.name = textwrap.shorten(self.longname,30)
        self.name = self.longname[:30]

        #gd = collection.getgame(Game._user, self.id)
        #self.averating = getvalue(gd, "./statistics/ratings/average")
        self.hoverimgurl = collection.getimg(Game._user, self.id)
        self.hoverimgraw = Image.open(self.hoverimgurl)
        self.hoverimgTk = ImageTk.PhotoImage(self.hoverimgraw)
        self.color = self.getavecolor()

        self.x = self.y = self.z = self.w = self.density = 0.0
        self.exists = False
        self.versionid = 0

        if elt is not None:
            self.versionid = int(elt.get("id"))
            self.x = sizevalue(elt, "width")
            self.y = sizevalue(elt, "length")
            self.z = sizevalue(elt, "depth")
            self.w = sizevalue(elt, "weight")


            # if somebody goofed on the 'depth', switch it
            if self.z > max(self.x,self.y):
                #print("## {} {}<->{} ({})".format(self.longname, self.z, self.y, self.x))
                self.y, self.z = self.z, self.y

            #some of the data is confusing/wrong, so let's use the picture as the deciding factor
            if self.x != self.y: # unless it's the same, save the time
                try:
                    #imgfile = collection.getimgspecific(elt.find("./thumbnail").text)
                    #with Image.open(imgfile) as imgraw:
                    #    w,h = imgraw.size
                    w, h = self.hoverimgraw.size
                    if (w>h) != (self.x>self.y):
                        #print("$$ {} {}<->{} ({} {})".format(self.name, self.x, self.y, w, h))
                        self.x, self.y = self.y, self.x

                except (IOError,FileNotFoundError,AttributeError):
                    pass


            try:
                self.exists = (self.x + self.y + self.z) > 0.0
                self.density = self.w/(self.z * min(self.x,self.y))
            except ArithmeticError:
                link = "https://boardgamegeek.com/boardgameversion/{}".format(self.versionid)
                print("Zero size for",  self.name,  self.x,
                self.y, self.z, link)
                pass
        else: # no version data
            print("No version for",  self.name,  "https://boardgamegeek.com/boardgame/{}".format(self.id))


    def getavecolor(self, bPrint = False):
        return averagecolor.calcfromdata(self.hoverimgraw)

    def getcolor(self,  bPrint = False):
        if bPrint:
            print("Starting", self.name, self.dir)
        try:
            w,h = self.hoverimgraw.size
            # check the corners of the image, jumping in increments if white

            # if box is stored zy or yz, then we want to check the left side
            if "y" in self.dir:
                vals = range(0,h-1, h//SAMPLE_STRIDE)
                coords = [(0, y) for y in vals]
                walkvalue = (1,0)
            else:
                vals = range(0, w-1, w//SAMPLE_STRIDE)
                coords = [(x,h-1) for x in vals]
                walkvalue = (0,1)
            avergb = [255,255,255]
            samples = []

            # loop breaker
            class ColorFound(Exception):pass

            try:
                for inset in range(0, min(w,h)//2, INSET_STRIDE):
                    xinset = inset * walkvalue[0]
                    yinset = inset * walkvalue[1]
                    for x,y in coords:
                        coord = (x+xinset, y-yinset)
                        col = self.hoverimgraw.getpixel(coord)

                        if len(col) > 3 and col[3] <= ALPHA_CUTOFF:
                            if bPrint:
                                print(coord, col, "alpha failed")
                        elif sum( col[:3] ) > COLOR_CUTOFF:
                            if bPrint:
                                print(coord, col, "color failed")
                        else:
                            samples.append( col )
                            if bPrint:
                                print(coord, col, "passed")


                    if len(samples) < NEEDED_SAMPLES:
                        continue

                    avergb = [ int( (sum(col)/len(samples))+0.5) for col in zip(*samples)]
                    if bPrint:
                        print("Finished with {}/{}".format(len(samples),len(coords)), avergb)
                    raise ColorFound
            except ColorFound:
                pass


            col = avergb[0]<<16 | avergb[1]<<8 | avergb[2]
        except (IndexError) as e:
            print(self.name, "failed color testing: ", e)
            col = 0xFFFFFF # just let it be white anyway

        if bPrint:
            print("Return {:x}".format(col))
        return col



    def makewidget(self, shelf,  center=False):
        # use the id, guaranteed unique, apply some sauce, and you got a unique color
        #self.rgb = (self.id * 161616) % 0xffffff

        color = "#{:06x}".format( self.color )
        #print(self.name, color)
        #self.box = Tk.Frame(shelf, bg=color
        #             , width=self.shelfwidth*SCALAR
        #             , height=self.shelfheight*SCALAR)
        #if center:
        #    self.box.pack(side=Tk.BOTTOM,anchor=Tk.S)
        #else:
        #    self.box.pack(side=Tk.LEFT,anchor=Tk.S)

        #self.box.bind("<Enter>",self.onEnter )
        #self.box.bind("<Button-1>", self.onClick )


        #self.box.pack_propagate(False)

        self.makeboxart()

        self.hovertext = "{self.longname}\n{self.x} x {self.y} x {self.z}\n{self.w} lbs\n{humdir} ({self.dir})".format(
            self=self, humdir=self.gethumandir())

        #fontcolor = "white" if colorbrightness(self.color) < BRIGHT_CUTOFF else "black"

        #self.label = Tk.Label(self.box
        self.label = Tk.Label(shelf, width=self.shelfwidth*SCALAR, height=self.shelfheight*SCALAR
                              #, text=self.name
                              , image=self.boximgraw
                              , relief=Tk.RAISED
                              #, wraplength=(self.shelfwidth * SCALAR)-2
                              , bg=color
                              #, fg=fontcolor
                              #, font=("Footlight MT","10", "bold")
                              )

        #if self.rotated:
        #    self.label.configure(anchor=Tk.E)

        self.label.bind("<Enter>",self.onEnter )

        self.label.bind("<Button-1>", self.onClick )
        #self.label.place(anchor=Tk.N, relx=.5, rely=0)
        if center:
            self.label.pack(side=Tk.BOTTOM,anchor=Tk.S)
        else:
            self.label.pack(side=Tk.LEFT,anchor=Tk.S)

    def makeboxart(self):
        img = self.hoverimgraw.copy()

        # determine the ratio of our deciding side (height or width)
        if self.rotated:
            ratio = (self.shelfheight*SCALAR) / img.width
        else:
            ratio = (self.shelfwidth*SCALAR) / img.width

        # shrink our image to fit our new size
        img = img.resize((int(ratio*img.width+1)
                        , int(ratio*img.height+1))
                        , Image.ANTIALIAS)

        # crop/transpose the image to the "top" of the thumbnail
        # luckily MOST games seem to put their name on the top.
        # We COULD try and be smart (somehow?) and find the name elsewise, but...
        if self.rotated:
            if Game._sidepreference == SidePreference.Right:
                img = img.transpose(Image.ROTATE_270)
                img = img.crop((img.width-self.shelfwidth*SCALAR
                                , 0
                                , img.width
                                , img.height ))
            else:
                img = img.transpose(Image.ROTATE_90)
                img = img.crop((0
                                , 0
                                , self.shelfwidth*SCALAR
                                , img.height ))

        else:
            img = img.crop((0
                            , 0
                            , img.width
                            , self.shelfheight*SCALAR ))
        self.boximgraw = ImageTk.PhotoImage(img)

    def onClick(self, event):
        self.getcolor(True)

    def onEnter(self, event):
        hover.Hover.inst.onEnter(self, event, [self.label])

    def onLeave(self, event):
        hover.Hover.inst.onLeave(self, event, [self.label])

    def setdir(self, dir):
        self.dir = dir
        self.shelfwidth  = getattr(self, dir[:1])
        self.shelfheight = getattr(self, dir[1:])
        self.rotated = dir[:1] == 'z'

        # depth is whatever direction is not the last one
        self.shelfdepth  = getattr(self, re.sub(dir[:1]+'?'+dir[1:]+'?', '', "xyz"))

    def gethumandir(self):
        dirs = {"zy":"Up", "zx":"Side", "xz":"Flat, Bottom", "yz":"Flat, Side"}
        return dirs[self.dir];

    def __repr__(self):
        return u"%s %.1f x %.1f x %.1f x %.3f (%.3f)" % (self.name, self.x, self.y, self.z, self.w, self.density)

    def __str__(self):
        return self.name
