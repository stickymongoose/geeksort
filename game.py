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

def gettext(node, path, default):
    try:
        return node.find(path).text
    except:
        return default

def getvalue(node, path, default, attr="value"):
    try:
        return node.find(path).get(attr).strip()
    except:
        return default

def getvaluef(node, path, default="0.0"):
    return float(getvalue(node, path, default))

def getvaluer(node, path, rounding=4):
    f = getvaluef(node, path)
    return math.ceil(f*rounding)/rounding

def colorbrightness(rgb):
    r = (rgb>>16) & 0xff
    g = (rgb>>8 ) & 0xff
    b = (rgb>>0 ) & 0xff
    # SUPER-approximate brightness (RGB->YUV) formula simplification
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

    def __init__(self, xmlfromcollection):

        self.sethighlighted( False )
        # get the unicode name, convert it, re-encode it
        self.name = xmlfromcollection.find("name").text.strip()
        self.name = unicodedata.normalize('NFKD', self.name)
        self.name = self.name.encode('ASCII','ignore').decode()

        # fix up any weird characters/spacing
        self.name = re.sub("\s+\r?\n?"," ", self.name)
        self.name = self.name.replace(u"–", "-")
        self.name = self.name.replace("&amp;","&")
        self.name = self.name.replace("&#039;","'")
        self.id = int(xmlfromcollection.get("objectid"))

        self.longname = self.name
        self.searchname = self.longname.lower()
        self.searchname = self.searchname.replace(" ", "")
        #should other ones go away...?

        #self.name = textwrap.shorten(self.longname,30)
        self.name = self.longname[:30]

        #gd = collection.getgame(Game._user, self.id)
        #self.averating = getvaluef(gd, "./statistics/ratings/average")
        self.hoverimgurl = collection.getimg(Game._user, self.id)
        self.hoverimgraw = Image.open(self.hoverimgurl)
        self.color = self.getavecolor()

        # get if the user wants to exclude
        self.excluded = EXCLUDE_COMMENT in gettext(xmlfromcollection,"comment", "").lower()

        # ratings
        self.rating = self.minplayers = self.maxplayers = self.minplaytime = self.maxplaytime = -1
        try:
            stats = xmlfromcollection.find("stats")

            #while we could (ab)use reflection to just attach these to our class,
            # I can't think of a good way to then have it default to good values if not found
            self.minplayers = stats.get("minplayers", -1)
            self.maxplayers = stats.get("maxplayers", -1)
            self.minplaytime = stats.get("minplaytime", -1)
            self.maxplaytime = stats.get("maxplaytime", -1)
            rating = stats.find("rating")
            try:
                # rating may be returned as "N/A", so we cast it to a float to see if it's that
                self.rating = getvaluef(rating, ".", "-1")
            except ValueError:
                self.rating = -1.0

        except:
            pass

        # dimensions
        self.x = self.y = self.z = self.w = self.density = 0.0
        self.hasbox = False
        self.versionid = 0

        try:
            versionitem = xmlfromcollection.find("version/item")

            self.versionid = int(versionitem.get("id"))
            self.x = getvaluer(versionitem, "width")
            self.y = getvaluer(versionitem, "length")
            self.z = getvaluer(versionitem, "depth")
            self.w = getvaluer(versionitem, "weight")


            # if somebody goofed on the 'depth', switch it
            if self.z > max(self.x,self.y):
                #print("## {} {}<->{} ({})".format(self.longname, self.z, self.y, self.x))
                self.y, self.z = self.z, self.y

            #some of the data is confusing/wrong, so let's use the picture as the deciding factor
            if self.x != self.y: # unless it's the same, save the time
                try:
                    w, h = self.hoverimgraw.size
                    if (w>h) != (self.x>self.y):
                        #print("$$ {} {}<->{} ({} {})".format(self.name, self.x, self.y, w, h))
                        self.x, self.y = self.y, self.x

                except (IOError,FileNotFoundError,AttributeError):
                    pass

            try:
                self.hasbox = (self.x + self.y + self.z) > 0.0
                self.density = self.w/(self.z * min(self.x,self.y))
            except ArithmeticError:
                #link = VERSION_URL.format(id=self.versionid)
                #print("Zero size for",  self.name,  self.x, self.y, self.z, link)
                pass
        except: # no version data
            #print("No version for",  self.name,  GAME_URL.format(id=self.id))
            pass


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
        self.hoverimgTk = ImageTk.PhotoImage(self.hoverimgraw)
        self.makeboxart()

        self.hovertext = "{self.longname}\n{self.x} x {self.y} x {self.z}\n{self.w} lbs\n{humdir} ({self.dir})".format(
            self=self, humdir=self.gethumandir())

        #color = "#{:06x}".format( self.color )
        border = GAME_BORDER

        # scale the border down to accomodate for the fact that it happens on the OUTSIDE of the label
        # if we let it shrink, it'll make things bigger than they should be
        while True:
            self.lblwidth = (self.shelfwidth *IN_TO_PX) - (border*2.0)
            self.lblheight= (self.shelfheight*IN_TO_PX) - (border*2.0)

            if min(self.lblwidth,  self.lblheight) > 0:
                break # our border is fine, die

            border = border - 1

            if border == -1:
                border = 0
                self.lblwidth = max(1, self.lblwidth)
                self.lblheight = max(1, self.lblheight)
                break

        self.label = Tk.Label(shelf
                              , width =self.lblwidth
                              , height=self.lblheight
                              #, text=self.name
                              , image=self.boximgTk
                              , relief=Tk.RAISED
                              #, wraplength=(self.shelfwidth * IN_TO_PX)-2
                              , borderwidth=border
                              #, bg=color
                              , compound="center"
                              #, fg=fontcolor
                              #, font=("Footlight MT","10", "bold")
                              #, highlightcolor="red"
                              #,  takefocus=1
                              )

        self.label.bind("<Enter>",self.onEnter )

        self.label.bind("<Button-1>", self.onClick )

        if center:
            self.label.pack(side=Tk.BOTTOM,anchor=Tk.S)
        else:
            self.label.pack(side=Tk.LEFT,  anchor=Tk.SW)

        # reset this to adjust the things we've made
        self.sethighlighted(self.highlighted)


    def makeboxart(self):
        img = self.hoverimgraw.copy()

        # determine the ratio of our deciding side (height or width)
        if self.rotated:
            ratio = (self.shelfheight*IN_TO_PX) / img.width
        else:
            ratio = (self.shelfwidth*IN_TO_PX) / img.width

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
                img = img.crop((img.width-self.shelfwidth*IN_TO_PX
                                , 0
                                , img.width
                                , img.height ))
            else:
                img = img.transpose(Image.ROTATE_90)
                img = img.crop((0
                                , 0
                                , self.shelfwidth*IN_TO_PX
                                , img.height ))

        else:
            img = img.crop((0
                            , 0
                            , img.width
                            , self.shelfheight*IN_TO_PX ))
        self.boximgTk = ImageTk.PhotoImage(img)

    def onClick(self, event):
        #self.getcolor(True)
        self.sethighlighted(not self.highlighted)
        print(self.name, self.lblwidth,  self.lblheight)

    def onEnter(self, event):
        hover.Hover.inst.onEnter(self, event, [self.label])

    def onLeave(self, event):
        hover.Hover.inst.onLeave(self, event, [self.label])

    def search(self, text):
        if len(text)==0:
            self.sethighlighted(False)
            return 0

        matched = text in self.searchname
        if matched:
            self.label.config(state=Tk.ACTIVE, bg='yellow', relief=Tk.RAISED)
        else:
            self.label.config(state=Tk.DISABLED, bg='black', relief=Tk.FLAT)
        return int(matched)

    def sethighlighted(self, highlighted, bg='yellow'):
        self.highlighted = highlighted
        try:
            if highlighted:
                self.label.config(state=Tk.DISABLED, bg='yellow')
            else:
                color = "#{:06x}".format( self.color )
                self.label.config(state=Tk.NORMAL, bg=color)
        except AttributeError:
            pass

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
