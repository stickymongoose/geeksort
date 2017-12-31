#!/usr/bin/env python
# -*- coding: utf-8 -*-
import unicodedata
import tkinter as Tk
from enum import IntEnum
from PIL import Image, ImageTk
from constants import *
from contrib.mixed_fractions import Mixed
import collection
import averagecolor
import hover
import webbrowser
import sizewindow
import setlist
import numpy

VerticalLong = "zy"
VerticalShort = "zx"
HorizLong = "xz"
HorizShort = "yz"

UNFOUND_GAME_NAME = "<Unknown>"
VERY_SMALL_STDDEV = 3 # stddev within 3 cubic inches = just fiiine

# TODO: Adjust this message based on guesstimation method
GUESSED_MESSAGE =\
"""Size approximated, based on the largest size in BGG.
If it's too large, it probably selected a Jumbo Edition"""


def get_text(node, path, default):
    try:
        return node.find(path).text
    except:
        return default

def get_value(node, path, default, attr="value"):
    try:
        return node.find(path).get(attr).strip()
    except:
        return default

def get_valuef(node, path, default="0.0"):
    return float(get_value(node, path, default))

def get_valuer(node, path, rounding=BOX_PRECISION):
    f = get_valuef(node, path)
    return ceilFraction(f, rounding)

def get_node_values(node, type, defaults=[], node_name="link", attr="value", strip=""):
    items = node.findall("{}[@type='{}']".format(node_name, type))
    if len(items) > 0:
        out = []
        for v in items:
            out.append(get_value(v, ".", None, attr).strip(strip))
        return out
    return defaults

def color_brightness(rgb):
    r = (rgb>>16) & 0xff
    g = (rgb>>8 ) & 0xff
    b = (rgb>>0 ) & 0xff
    # SUPER-approximate brightness (RGB->YUV) formula simplification
    y = (2*r + 1*b + 3*g)/(255.0*6.0)
    return y

class SidePreference(IntEnum):
    Left = 0
    Right = 1

class SizePreference(IntEnum):
    Biggest = 0
    MostCommon = 1
    Average = 2

SidePreference_names = ["Left", "Right"]
SidePreference_pics = ["pics/ori_left.png", "pics/ori_right.png"]


class ActionMenu(Tk.Menu):
    def __init__(self, root, game):
        Tk.Menu.__init__(self, root, tearoff=0, title=game.name)
        self.game = game
        if game.excluded:
            self.add_command(label="Unexclude from Sort", command=self.toggle_exclude, underline=3)
        else:
            self.add_command(label="Exclude from Sort", command=self.toggle_exclude, underline=1)

        self.geekimg = geekimg = ImageTk.PhotoImage(Image.open("pics/bgg_t.png"))

        self.add_command(label="Edit Size...", command=self.edit_size, underline=5)
        self.add_separator()
        self.add_command(label="To Game Entry", image=geekimg, compound=Tk.LEFT
                         , command=self.to_bgg, underline=7)
        self.add_command(label="To Version List", image=geekimg, compound=Tk.LEFT
                         , command=self.to_version_selector, underline=15)

        if game.guesstimated:
            self.add_command(label="To Guesstimated Version Entry", image=geekimg, compound=Tk.LEFT
                             , command=self.to_version, underline=7)
            self.add_command(label="To Guesstimated Version Editor", image=geekimg, compound=Tk.LEFT
                             , command=self.to_version_edit, underline=7)
        elif game.versionid != 0:
            self.add_command(label="To Version Entry", image=geekimg, compound=Tk.LEFT
                             , command=self.to_version, underline=7)
            self.add_command(label="To Version Editor", image=geekimg, compound=Tk.LEFT
                             , command=self.to_version_edit, underline=7)

    def toggle_exclude(self):
        self.game.excluded = not self.game.excluded
        Game._app.resort_games()

    def edit_size(self):
        sizewindow.Popup(self, self.game, Game._app)

    def to_bgg(self):
        webbrowser.open(GAME_URL.format(id=self.game.id))

    def to_version_selector(self):
        webbrowser.open(GAME_VERSIONS_URL.format(id=self.game.id))

    def to_version(self):
        webbrowser.open(VERSION_URL.format(id=self.game.versionid))

    def to_version_edit(self):
        webbrowser.open(VERSION_EDIT_URL.format(id=self.game.versionid))


class Game:
    _user = None
    _app = None
    _sidepreference = SidePreference.Left
    _sizepreference = SizePreference.Biggest

    _not_ready_img = None
    _guessed_img = None

    @staticmethod
    def init():
        Game._not_ready_img = Tk.PhotoImage(file="pics/notready.gif")
        Game._guessed_img   = Tk.PhotoImage(file="pics/guessed.gif")

    @staticmethod
    def set_side_preference(side:SidePreference):
        Game._sidepreference = side

    @staticmethod
    def set_size_preference(size: SizePreference):
        Game._sizepreference = size

    def __init__(self, xmlfromcollection):

        self.set_highlighted(False)
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
        self.searchname = to_search(self.longname)
        self.sortname = to_sort(self.longname)
        #should other ones go away...?

        #self.name = textwrap.shorten(self.longname,30)
        self.name = self.longname[:30]

        self.hoverimgurl = None
        self.hoverimgraw = None
        self.color = 0x808080
        collection.queue_img(Game._user, self)


        self.tkLabel = None

        # get if the user wants to exclude
        self.excluded = EXCLUDE_COMMENT in get_text(xmlfromcollection, "comment", "").lower()

        # ratings
        self.rating_user = self.rating_ave = self.rating_bayes = -1
        self.minplayers = self.maxplayers = -1
        self.minplaytime = self.maxplaytime = -1
        self.num_plays = int(get_text(xmlfromcollection, "numplays", 0))
        self.weight = -1

        try:
            stats = xmlfromcollection.find("stats")

            # while we could (ab)use reflection to just attach these to our class,
            # I can't think of a good way to then have it default to good values if not found
            self.minplayers = int(stats.get("minplayers", -1))
            self.maxplayers = int(stats.get("maxplayers", -1))
            self.minplaytime = int(stats.get("minplaytime", -1))
            self.maxplaytime = int(stats.get("maxplaytime", -1))
            rating = stats.find("rating")
            try:
                # rating may be returned as "N/A", so we cast it to a float to see if it's that
                self.rating_user = get_valuef(rating, ".", "-1")
            except ValueError:
                pass

            self.types = get_node_values(rating, "ranks/rank", node_name="family", attr="friendlyname", strip=" Game Rank")

            self.rating_bayes = get_valuef(rating, "bayesaverage")
            self.rating_ave   = get_valuef(rating, "average")
        except Exception as e:
            print(self.name, e)
            pass

        # game data we can't get from the collection's data
        #self.expansions = []
        self.year_published = self.min_age = 0

        self.categories = self.mechanics = self.families = []
        self.designers = self.artists = self.publishers = self.types = []
        gd = collection.get_game(Game._user, self.id)
        try:
            self.year_published = get_value(gd, "yearpublished", 0)
            self.min_age    = get_value(gd, "minage", 0)
            self.categories = get_node_values(gd, "boardgamecategory")
            self.mechanics  = get_node_values(gd, "boardgamemechanic")
            self.families   = get_node_values(gd, "boardgamefamily")
            self.designers  = get_node_values(gd, "boardgamedesigner")
            self.artists    = get_node_values(gd, "boardgameartist")
            self.publishers = get_node_values(gd, "boardgamepublisher")

            self.weight = get_valuef(gd, "statistics/ratings/averageweight")

        except ValueError as e:
            print(e)
            pass

        # dimensions
        self.xraw = self.x = 0.0
        self.yraw = self.y = 0.0
        self.zraw = self.z = 0.0
        self.wraw = self.w = self.density = 0.0
        self.hasbox = False
        self.versionid = 0
        self.versionname = ""
        self.guesstimated = False

        try:
            versionitem = xmlfromcollection.find("version/item")

            self.versionid = int(versionitem.get("id"))
            self.versionname = get_value(versionitem, "name", UNFOUND_GAME_NAME)

            self.set_size(get_valuef(versionitem, "width")
                          , get_valuef(versionitem, "length")
                          , get_valuef(versionitem, "depth")
                          , get_valuef(versionitem, "weight")
                          )

            # get more exact data from the actual owned version
            self.year_published = get_value(versionitem, "yearpublished", self.year_published)
            self.categories = get_node_values(versionitem, "boardgamecategory", self.categories)
            self.mechanics  = get_node_values(versionitem, "boardgamemechanic", self.mechanics)
            self.families   = get_node_values(versionitem, "boardgamefamily", self.families)
            self.designers  = get_node_values(versionitem, "boardgamedesigner", self.designers)
            self.artists    = get_node_values(versionitem, "boardgameartist", self.artists)
            self.publishers = get_node_values(versionitem, "boardgamepublisher", self.publishers)
        except Exception as e:
            # no version data, best guess it.
            self.set_size_by_guess(gd.findall("versions/item"))

            #print("No version for",  self.name,  GAME_URL.format(id=self.id))
            pass

        # now that we're done with all the possible adding, add each to the set list
        setlist.append(setlist.Types, self.types)
        setlist.append(setlist.Categories, self.categories)
        setlist.append(setlist.Mechanics, self.mechanics)
        setlist.append(setlist.Families, self.families)
        setlist.append(setlist.Designers, self.designers)
        setlist.append(setlist.Artists, self.artists)
        setlist.append(setlist.Publishers, self.publishers)

    def set_image(self, url):
        self.hoverimgurl = url
        self.hoverimgraw = Image.open(self.hoverimgurl)
        self.color = self.get_ave_color()

        try:
            self.make_image()
            self._make_box_art()
            self.set_size_and_adjust(self.xraw, self.yraw, self.zraw, self.wraw)
            self.set_highlighted(self.highlighted)
        except:
            pass

    def set_size_by_guess(self, nodes):
        sizes = []
        for n in nodes:
            x = get_valuef(n, "width")
            y = get_valuef(n, "length")
            z = get_valuef(n, "depth")
            w = get_valuef(n, "weight")
            name = get_value(n, "name", UNFOUND_GAME_NAME)
            id = int(n.get("id"))

            if x+y+z > 0:
                rawobj  = {"size":(x, y, z, w), "name":name, "id":id}
                #sortobj = [ceilFraction(x, BOX_PRECISION)
                #        , ceilFraction(y, BOX_PRECISION)
                #        , ceilFraction(z, BOX_PRECISION)
                #          ]
                #sortobj.sort(reverse=True) # sort from big to small
                #sortkey = sortobj[0] * 1000000 + sortobj[1] * 1000 + sortobj[2]  # make a hashable key
                sortkey = ceilFraction(x, BOX_PRECISION) * ceilFraction(y, BOX_PRECISION) * ceilFraction(z, BOX_PRECISION)
                sizes.append((sortkey, rawobj))

        if len(sizes) > 0:
            sizes.sort(reverse=True, key=lambda key: key[1]["size"][3]) # as a tie-breaker, prefer the heaviest
            sizes.sort(reverse=True, key=lambda key: key[0])
            self.guesstimated = True
            if Game._sizepreference == SizePreference.Biggest:
                # need to throw away some outliers, as some are just... busted
                m = 2 # what's a good value for this?
                just_weights, ignored = zip(*sizes)
                stddev = numpy.std(just_weights)
                # for s in sizes:
                #     print(s)

                # if the data is nearly perfectly in agreement, then just use the topmost
                if stddev < VERY_SMALL_STDDEV:
                    filter_sizes = sizes
                else:
                    mean = numpy.mean(just_weights)
                    # outlier exclusion, filter away anything too far beyond the stddev
                    filter_sizes = [s for s in sizes if abs(s[0] - mean) < m * stddev]

                    if len(filter_sizes) == 0:
                        # print("########")
                        # print(self.name, stddev, mean)
                        # for s in sizes:
                        #     print(s)
                        filter_sizes = sizes

                choice = filter_sizes[0][1] # Top item, sortobj ([0] is the sort key)
                print("##: Guesstimated:", self.name, choice)
                self.set_size(*(choice["size"]))
                self.versionname = choice["name"]
                self.versionid = choice["id"]

            elif Game._sizepreference == SizePreference.MostCommon or Game._sizepreference == SizePreference.Average:
                # TODO: Figure out how to do this... Is volume truly the best way?
                pass

    def set_size(self, x, y, z, w):
        self.xraw = x
        self.yraw = y
        self.zraw = z
        self.wraw = w
        self.x = ceilFraction(x, BOX_PRECISION)
        self.y = ceilFraction(y, BOX_PRECISION)
        self.z = ceilFraction(z, BOX_PRECISION)
        self.w = ceilFraction(w, BOX_PRECISION)
        self.density = 0
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

            except AttributeError as e:
                pass

            except (IOError,FileNotFoundError) as e:
                print(self.name, e)
                pass

        try:
            self.hasbox = (self.x + self.y + self.z) > 0.0
            self.density = self.w/(self.z * min(self.x,self.y))
        except ArithmeticError as e:
            #print(self.name, e)
            #link = VERSION_URL.format(id=self.versionid)
            #print("Zero size for",  self.name,  self.x, self.y, self.z, link)
            pass

    def set_size_and_adjust(self,x,y,z,w):
        self.set_size(x, y, z, w)
        self.tkLabel.configure(image=self.boximgTk)


    def get_ave_color(self, bPrint = False):
        return averagecolor.calcfromdata(self.hoverimgraw)

    def get_color(self, bPrint = False):
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
            print("Return {:06x}".format(col))
        return col


    def make_image(self):
        if self.hoverimgraw is not None:
            self.hoverimgTk = ImageTk.PhotoImage(self.hoverimgraw)
        else:
            self.hoverimgTk = None

    def make_lite_hover(self):
        self.hovertext = "{self.longname}\n{self.versionname}\n{x}\" x {y}\" x {z}\"\n{w} lbs".format(self=self,
                                        x=makeFraction(self.xraw),
                                        y=makeFraction(self.yraw),
                                        z=makeFraction(self.zraw),
                                        w=makeFraction(self.wraw)
                                        )

    def make_widget(self, shelf, center=False):
        try:
            self.make_image()
            self._make_box_art()
        except: pass

        self.hovertext = "{self.longname}\n{self.versionname}\n{x}\" x {y}\" x {z}\"\n{w} lbs\n{humdir} ({self.dir})".format(
            self=self, humdir=self.get_human_dir(),
            x=makeFraction(self.xraw),
            y=makeFraction(self.yraw),
            z=makeFraction(self.zraw),
            w=makeFraction(self.wraw))

        #color = "#{:06x}".format( self.color )
        border = GAME_BORDER

        # scale the border down to accomodate for the fact that it happens on the OUTSIDE of the label
        # if we let it shrink, it'll make things bigger than they should be
        while True:
            self.lblwidth = (self.shelfwidth *IN_TO_PX) - (border*2.0)
            self.lblheight= (self.shelfheight*IN_TO_PX) - (border*2.0)

            if min(self.lblwidth,  self.lblheight) > 0:
                break # our border is fine, die

            border -= 1

            if border == -1:
                border = 0
                self.lblwidth = max(1, self.lblwidth)
                self.lblheight = max(1, self.lblheight)
                break

        self.lblwidth  = int(self.lblwidth+1)
        self.lblheight = int(self.lblheight+1)

        self.tkLabel = Tk.Label(shelf
                                , width =self.lblwidth
                                , height=self.lblheight
                                #, text=self.name
                                #, image=self.boximgTk
                                , relief=Tk.RAISED
                                #, wraplength=(self.shelfwidth * IN_TO_PX)-2
                                , borderwidth=border
                                #, bg="red"
                                #, bg=color
                                , compound="center"
                                #, fg=fontcolor
                                #, font=("Footlight MT","10", "bold")
                                #, highlightcolor="red"
                                #,  takefocus=1
                                )

        try:
            self.tkLabel.configure(image=self.boximgTk)
        except:
            while True:
                try:
                    self.tkLabel.configure(image=Game._not_ready_img)
                    break
                except Tk.TclError:
                    print("Picture error?")
                    Game.init()

        self.tkLabel.bind("<Motion>", self.onMove)

        self.tkLabel.bind("<Button-1>", self.onClick)
        self.tkLabel.bind("<Button-3>", self.onRClick)

        if center:
            self.tkLabel.pack(side=Tk.BOTTOM, anchor=Tk.S)
        else:
            self.tkLabel.pack(side=Tk.LEFT, anchor=Tk.SW)

        # reset this to adjust the things we've made
        self.set_highlighted(self.highlighted)

        if self.guesstimated:
            self.tkIcon = Tk.Label(self.tkLabel, image=Game._guessed_img)
            self.tkIcon.place(relx=0, rely=0)
            self.tkIcon.hovertext = GUESSED_MESSAGE
            self.tkIcon.bind("<Motion>", self.onMoveGuessed)


    def clear_widget(self):
        try:
            self.tkLabel.destroy()
        except AttributeError:
            pass

        self.tkLabel = None
        self.hoverimgTk = None # Does this release it?
        self.boximgTk = None

    def _make_box_art(self):
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
        self.set_highlighted(not self.highlighted)
        print(self.name, self.lblwidth,  self.lblheight, "{:06x}".format(self.color))

    def onRClick(self, event):
        hover.Hover.inst.onClear(None)
        a = ActionMenu(self.tkLabel, self)
        a.post(event.x_root, event.y_root)

    def onMove(self, event):
        hover.Hover.inst.onMove(self, event)

    def onMoveGuessed(self, event):
        hover.Hover.inst.onMove(self.tkIcon, event)

    def search(self, text):
        if len(text)==0:
            self.set_highlighted(False)
            return 0

        matched = text in self.searchname
        try:
            if matched:
                self.tkLabel.config(state=Tk.ACTIVE, bg='yellow', relief=Tk.RAISED)
            else:
                self.tkLabel.config(state=Tk.DISABLED, bg='black', relief=Tk.FLAT)
        except AttributeError:
            pass # may not have self.label

        return int(matched)

    def set_highlighted(self, highlighted):
        self.highlighted = highlighted
        try:
            if highlighted:
                self.tkLabel.config(state=Tk.DISABLED, bg='yellow')
            else:
                color = "#{:06x}".format( self.color )
                self.tkLabel.config(state=Tk.NORMAL, bg=color)
        except AttributeError:
            pass

    def set_dir(self, dir):
        self.dir = dir
        self.shelfwidth  = getattr(self, dir[:1])
        self.shelfheight = getattr(self, dir[1:])
        self.rotated = dir[:1] == 'z'

        # depth is whatever direction is not the last one
        self.shelfdepth  = getattr(self, re.sub(dir[:1]+'?'+dir[1:]+'?', '', "xyz"))

    def get_human_dir(self):
        dirs = {VerticalLong: "Up", VerticalShort: "Side", HorizLong: "Flat, Bottom", HorizShort: "Flat, Side"}
        return dirs[self.dir]


def freeze_games(gamelist):
    return [(g.id, g.dir) for g in gamelist]

def thaw_games(gamedb, gamelist):
    out = []
    for id, dir in gamelist:
        g = gamedb.find(id)
        g.set_dir(dir)
        out.append(g)

    return out