import tkinter as Tk
from PIL import Image, ImageTk

from contrib.mixed_fractions import Mixed
import webbrowser
from constants import *
import enum

class Units(enum.IntEnum):
    US_FRACTION = 0
    US_DECIMAL = 1
    METRIC = 2

UNIT_DATA = { Units.US_FRACTION:{"title":"Imperial, Fractions", "len":"in", "weight":"lb"}
            , Units.US_DECIMAL: {"title":"Imperial, Decimal",   "len":"in", "weight":"lb"}
            , Units.METRIC:     {"title":"Metric",              "len":"cm", "weight":"kg"}
            }

GUESS_MESSAGE = "* Version was guesstimated, and may not be the one in your collection"

class Popup:

    def __init__(self, master, game, app):
        self.top = Tk.Toplevel(master)
        self.top.title( "Editing Dimensions")
        self.top.focus_force()
        self.target = game
        self.app = app

        self.unitstr = Tk.StringVar()
        self.lenunit = Tk.StringVar()
        self.weightunit = Tk.StringVar()
        CHUNK_PAD = 10

        insetframe = Tk.Frame(self.top)
        insetframe.pack(padx=CHUNK_PAD, pady=CHUNK_PAD)

        # game name header
        Tk.Label(insetframe, text=game.longname, justify=Tk.CENTER, font=("Helvetica", 14), wraplength=270+CHUNK_PAD).pack(pady=0)
        versionname = "{vn}{guess}".format(vn=game.versionname, guess="*" if game.guesstimated else "")
        Tk.Label(insetframe, text=versionname, justify=Tk.CENTER, font=("Helvetica", 11), wraplength=270+CHUNK_PAD).pack(pady=0)

        # picture header
        headerframe = Tk.Frame(insetframe)
        headerframe.pack(pady=0, padx=0)
        self.imglength = Tk.PhotoImage(file="pics/length.gif")
        self.imgwidth = Tk.PhotoImage(file="pics/width.gif")
        self.imgdepth = Tk.PhotoImage(file="pics/depth.gif")
        #l = Tk.Label(insetframe, image=self.boxbg, compound=Tk.TOP)
        #l.pack(pady=0, padx=0)
        pic = Tk.Label(headerframe, image=game.hoverimgTk)
        pic.grid(row=1, column=1)
        #pic.pack(pady=0, padx=0)
        Tk.Label(headerframe, image=self.imgwidth).grid(row=1, column=2)
        Tk.Label(headerframe, image=self.imglength).grid(row=2, column=1)
        Tk.Label(headerframe, image=self.imgdepth).grid(row=1, column=0, sticky=Tk.N)


        # data entry
        midframe = Tk.Frame(insetframe, padx=10)
        midframe.pack(pady=0)

        Tk.Label(midframe, text="Length").grid(row=0, column=0, pady=0, sticky=Tk.E, padx=0)
        Tk.Label(midframe, text="Width" ).grid(row=1, column=0, pady=3, sticky=Tk.E, padx=0)
        Tk.Label(midframe, text="Depth" ).grid(row=2, column=0, pady=3, sticky=Tk.E, padx=0)
        Tk.Label(midframe, text="Weight").grid(row=3, column=0, pady=0, sticky=Tk.E, padx=0)

        Tk.Label(midframe, width=2, justify=Tk.LEFT, textvariable=self.lenunit).grid(row=0, column=2, pady=0, sticky=Tk.W, padx=0)
        Tk.Label(midframe, width=2, justify=Tk.LEFT, textvariable=self.lenunit).grid(row=1, column=2, pady=3, sticky=Tk.W, padx=0)
        Tk.Label(midframe, width=2, justify=Tk.LEFT, textvariable=self.lenunit).grid(row=2, column=2, pady=3, sticky=Tk.W, padx=0)
        Tk.Label(midframe, width=2, justify=Tk.LEFT, textvariable=self.weightunit).grid(row=3, column=2, pady=0, sticky=Tk.W, padx=0)

        # data entry widgets
        fields = ["x", "y", "z", "w"]
        for i in range(len(fields)):
            val = fields[i]
            var = Tk.StringVar()
            setattr(self, val+"var", var)
            var.set(getattr(game, val+"raw")) # pull the raw data off the game

            widget = Tk.Entry(midframe,  textvariable=var, width=18, justify=Tk.RIGHT
                    , validate="focusout", highlightthickness=1, highlightbackground="white")

            widget.config(validatecommand=(widget.register(self.validateentry), "%P", "%W"))
            widget.grid(row=i, column=1, padx=0, pady=2)
            widget.var = var # so we can access it later
            widget.isweight = 'w' in val
            setattr(self, val, widget)

        self.x.focus_force()
        # unit selection

        unitdata = UNIT_DATA[Units.US_FRACTION]
        self.unitstr.set(unitdata['title'])
        self.oldunit =  -1
        self.unitchange(unitdata['title'])

        cb = Tk.OptionMenu(midframe,  self.unitstr,  *[u['title'] for u in UNIT_DATA.values()],  command=self.unitchange)
        cb.config(justify=Tk.LEFT, width=15)
        cb.grid(row=4, column=1)

        # divider
        Tk.Frame(insetframe, border=2, relief=Tk.RIDGE, bg="grey").pack(pady=8, fill=Tk.X, padx=2)

        # buttons
        self.geekimg = ImageTk.PhotoImage(Image.open("pics/bgg_t.png"))
        bggbtn = Tk.Button(insetframe, text="Edit Entry on BGG", command=self.openurl
            , bg=BGG_BTN_COLOR, compound=Tk.RIGHT, image=self.geekimg,  padx=15)
        bggbtn.pack(pady=5)
        if game.guesstimated:
            Tk.Label(insetframe, text=GUESS_MESSAGE, justify=Tk.CENTER, font=("Helvetica", 8), wraplength=180+CHUNK_PAD).pack(pady=0)

        Tk.Frame(insetframe, border=2, relief=Tk.RIDGE, bg="grey").pack(pady=8, fill=Tk.X, padx=2)

        btnframe = Tk.Frame(insetframe)
        btnframe.pack(pady=5)
        okbtn  = Tk.Button(btnframe, text="OK",     width=BTN_WIDTH, height=BTN_HEIGHT, command=self.commit, bg=OK_BTN_COLOR)
        nokbtn = Tk.Button(btnframe, text="Cancel", width=BTN_WIDTH, height=BTN_HEIGHT, command=self.close, bg=CANCEL_BTN_COLOR)


        okbtn.pack(side=Tk.LEFT, padx=20)
        nokbtn.pack(side=Tk.RIGHT, padx=20)

        master.wait_window(self.top)

    def convert(self, val, scale=True, islen=True):
        try:
            val = val.get()
        except:
            pass

        if scale and self.unit == Units.METRIC:
            multi = CM_TO_IN if islen else KG_TO_LB
        else:
            multi = 1.0

        v = float(Mixed(val))*multi
        if self.unit == Units.US_FRACTION:
            return roundFraction(v, DENOM_LIMIT)
        return v


    def validateentry(self, val,  widgetpath):
        widget = self.top.nametowidget(widgetpath)

        try:
            v = self.convert(val, scale=False,  islen=widget.isweight) # check if it'd parse output
            if v < 0: # no negative values
                raise ValueError()
            widget.config(highlightbackground="white") # assumption: this is the default color

            self.formatwidget(widget, v)

            return True
        except Exception as e:
            print(e)
            widget.config(highlightbackground="red")
            return False

    def formatwidget(self, widget, val=None):
        if val == None:
            val = widget.var.get()

        #if widget.isweight:
        num = float(Mixed(val))
        #else:
        #    num = roundFraction(float(Mixed(val)), DENOM_LIMIT)

        if self.unit == Units.US_FRACTION:
            res = str( Mixed(num).limit_denominator(DENOM_LIMIT) )
            widget.var.set(res)
        else:
            widget.var.set(str(round(num, ROUND_PRECISION)))

        # need to turn validation back on to prevent infinite loop
        widget.after_idle(lambda:widget.config(validate='focusout'))

    def commit(self):
        temp = {}
        failed = False
        for f in ["x", "y", "z", "w"]:
            widget = getattr(self, f)
            try:
                temp[f] = self.convert( widget )
            except ValueError:
                failed = True
                widget.config(bg="red")
                widget.after(500, lambda x:x.config(bg="white"), widget ) # assumption: this is the default color

        if failed:
            self.top.bell()
        else:
            self.close()
            self.target.set_size_and_adjust(*temp.values())
            self.app.resort_games()

    def unitchange(self, newtitle):

        self.unit = [k for k, v in UNIT_DATA.items() if v['title'] == newtitle][0]

        # gotta use the get()s, as if we just do != it checks the pointers

        if self.oldunit == self.unit:
            return # do nothing

        unitdata = UNIT_DATA[self.unit]

        self.lenunit.set(    unitdata['len'] )
        self.weightunit.set( unitdata['weight'] )


        multi_len = multi_weight = 1.0

        if self.oldunit == Units.METRIC: # switching FROM Metric
            multi_len, multi_weight = CM_TO_IN,  KG_TO_LB

        elif self.unit == Units.METRIC: # switching TO Metric
            multi_len, multi_weight = IN_TO_CM,  LB_TO_KG

        #convert the fields
        entryfields = [self.x, self.y, self.z, self.w]
        multis = [multi_len]*3+[multi_weight]
        for entry, multi in zip(entryfields, multis):
            v = float(Mixed(entry.get())) * multi
            self.formatwidget(entry, v)

        self.oldunit = self.unit

    def close(self):
        self.top.destroy()

    def openurl(self):
        webbrowser.open(VERSION_EDIT_URL.format(id=self.target.versionid))

if __name__=="__main__":
    root = Tk.Tk()

    root.update()
    #Tk.Label(root, text="Butt").pack()

    class fakeGame:
        def setsize(self, x, y, z, w): pass

    class fakeApp:
        pass

    fakegame = fakeGame()
    fakeapp = fakeApp()


    #boximage = "pics/pic1993208_t.jpg"
    boximage = CACHE_DIR + "/pics/pic1961827_t.jpg"
    fakegame.hoverimgTk = ImageTk.PhotoImage(Image.open(boximage))
    fakegame.versionid = 13123
    fakegame.versionname = "Something"
    fakegame.guesstimated = True

    fakegame.x = fakegame.y = fakegame.z = 10.125
    fakegame.w = 2.5
    fakegame.longname = "Castle of Mad King Ludwig"
    s = Popup(root, fakegame, fakeapp)
    #s.top.lift()
    #root.wait_window(s.top)

    root.mainloop()

