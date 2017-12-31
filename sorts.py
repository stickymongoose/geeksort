import game
import tkinter as Tk
import tkinter.ttk as ttk
from PIL import Image, ImageTk
import functools
import operator
import contrib.mixed_fractions as mixed_fractions
import setlist
from constants import top

FILTER_WIDTH = 450

DEFAULT_LIST = "Any"

BGG_RATINGS = [ "10 - Outstanding, will always enjoy playing"
              , "9 - Excellent, very much enjoy playing"
              , "8 - Very Good, enjoy playing and would suggest it"
              , "7 - Good, usually willing to play"
              , "6 - Ok, will play if in the mood"
              , "5 - Mediocre, take it or leave it"
              , "4 - Not So Good, but could play again"
              , "3 - Bad, likely won't play this again"
              , "2 - Very Bad, won't play ever again"
              , "1 - Awful, defies description"
              ]

WEIGHT_VALUES = [ "1 - Light"
                , "1.5"
                , "2 - Medium Light"
                , "2.5"
                , "3 - Medium"
                , "3.5"
                , "4 - Medium Heavy"
                , "4.5"
                , "5 - Heavy"
                ]

EMPTY = ""

# GENERAL FUNCTORS
def Name(g):
    return g.sortname

def Size(g):
    return -(g.x * g.y * g.z)

def Brightness(g):
    return game.color_brightness(g.color)

def Weight(g):
    return g.w

def Players(g):
    return g.players


def identity(a):
    return a

def not_contains(a,b):
    return b not in a

def between(v, a, b):
    return min(a, b) <= v and v <= max(a, b)

def any_list(array:list, string:str):
    if string == DEFAULT_LIST:
        return array
    data = string.split(", ")
    return any(elt in array for elt in data)

def all_list(array:list, string:str):
    if string == DEFAULT_LIST:
        return array
    data = string.split(", ")
    return all(elt in array for elt in data)


# Field-fillers
class FieldFactory_Base():
    def add_widget(self, owner):
        return [], []

    def convert_field(self, field):
        return field.lower()


class FieldFactory_Entry(FieldFactory_Base):
    def __init__(self, count, width):
        FieldFactory_Base.__init__(self)
        self.count = count
        self.width = width

    def add_widget(self, owner):
        tkWidgets = []
        vars = []
        for i in range(self.count):
            if i > 0:
                l = ttk.Label(owner, text="and")
                l.pack(side=Tk.LEFT, padx=5, anchor=Tk.W)
                tkWidgets.append(l)
            v = Tk.StringVar(owner)
            e = ttk.Entry(owner, textvariable=v, width=self.width)
            e.pack(side=Tk.LEFT, anchor=Tk.W)
            tkWidgets.append(e)
            vars.append(v)
        return tkWidgets, vars


class FieldFactory_EntryNum(FieldFactory_Entry):
    def convert_field(self, field):
        return float(mixed_fractions.Mixed(field))

class FieldFactory_SelMenu(FieldFactory_Base):
    def __init__(self, data):
        FieldFactory_Base.__init__(self)
        self.data = data

    def add_widget(self, owner):
        tkWidgets = []
        vars = []

        menu = Tk.Menu(owner, tearoff=0)
        tkWidgets.append(menu)

        te = Tk.StringVar(menu, DEFAULT_LIST)
        menuBtn = ttk.Menubutton(owner, textvariable=te, menu=menu
                                 , direction=Tk.RIGHT, width=20)
        menuBtn.pack(side=Tk.LEFT, anchor=Tk.W)
        tkWidgets.append(menuBtn)

        # sort by occurrence of item
        #prioritysorted = sorted(self.data.items(), key=lambda val: (-val[1], val[0]))
        for key in sorted(self.data):
            v = Tk.StringVar(menu, value=EMPTY)
            menu.add_checkbutton(label=key, variable=v
                                 , command=functools.partial(FieldFactory_SelMenu.post_menu, menuBtn, menu)
                                 , onvalue=key, offvalue=EMPTY)
            vars.append(v)

        menu.vars = vars
        menu.configure(postcommand=lambda:FieldFactory_SelMenu.adjust_label(te, menu))

        return tkWidgets, [te] # for the purposes of computing a match, the label is fine

    def convert_field(self, field):
        return field

    @staticmethod
    def adjust_label(te:Tk.StringVar, menu):
        temp = ", ".join(var.get() for var in menu.vars if var.get() is not EMPTY)
        if len(temp) == 0:
            te.set(DEFAULT_LIST)
        else:
            te.set(temp)

    @staticmethod
    def post_menu(menuBtn, menu, *vars):
        root = menuBtn
        x = 0
        y = 0
        # need to sum up all the X/Ys as we go, to place the menu in the right place
        while root.master is not None:
            x += root.winfo_x()
            y += root.winfo_y()
            root = root.master

        # we need to calculate where to put the menu
        # to sort of fake a pop-up multi picker, reopen the menu
        x = x + root.winfo_rootx() + menuBtn.winfo_width()
        y = y + root.winfo_rooty()
        menu.post(x, y)



class FieldFactory_FixedSelMenu(FieldFactory_Base):
    def __init__(self, count, data):
        FieldFactory_Base.__init__(self)
        self.count = count
        self.data = data

    def add_widget(self, owner):
        tkWidgets = []
        vars = []
        for i in range(self.count):
            if i > 0:
                l = ttk.Label(owner, text="and")
                l.pack(side=Tk.LEFT, padx=5, anchor=Tk.W)
                tkWidgets.append(l)
            w, v = self.__make_picker(owner)
            tkWidgets += w
            vars += v
        return tkWidgets, vars

    def __make_picker(self, owner):
        menu = Tk.Menu(owner, tearoff=0)

        te = Tk.IntVar(menu)
        self.__set_value(te, self.data[len(self.data) // 2])
        menuBtn = ttk.Menubutton(owner, textvariable=te, menu=menu
                                 , direction=Tk.RIGHT, width=3)
        menuBtn.pack(side=Tk.LEFT, anchor=Tk.W)

        for rating in self.data:
            menu.add_command(label=rating, command=functools.partial(self.__set_value, te, rating))

        return [menu, menuBtn], [te]

    def __set_value(self, te, rating, *values):
        te.set( float(rating.split(" - ")[0] ) )

    def convert_field(self, field):
        return field



# Big ol' pile of metadata

DATA_OP_LABELS = 0
DATA_FIELDS = 1
DATA_OPS = 2

NoEntry        = FieldFactory_Base()
WideEntry      = FieldFactory_Entry(1, 20)
NarrowEntry    = FieldFactory_EntryNum(1, 8)
DblNarrowEntry = FieldFactory_EntryNum(2, 8)

RatingEntry    = FieldFactory_FixedSelMenu(1, BGG_RATINGS)
DblRatingEntry = FieldFactory_FixedSelMenu(2, BGG_RATINGS)

WeightEntry    = FieldFactory_FixedSelMenu(1, WEIGHT_VALUES)
DblWeightEntry = FieldFactory_FixedSelMenu(2, WEIGHT_VALUES)

FamilyFactory = FieldFactory_SelMenu(setlist.Families)
CatFactory = FieldFactory_SelMenu(setlist.Categories)
MechFactory = FieldFactory_SelMenu(setlist.Mechanics)
DesiFactory = FieldFactory_SelMenu(setlist.Designers)
ArtFactory = FieldFactory_SelMenu(setlist.Artists)
PubFactory = FieldFactory_SelMenu(setlist.Publishers)

AnyOf = "are any of"
AllOf = "are all of"


def NUMERICAL(onefield, twofield):
     return \
     [("as is",        NoEntry,  identity)
     ,("equals",       onefield, operator.eq)
     ,("less than",    onefield, operator.lt)
     ,("greater than", onefield, operator.gt)
     ,("between",      twofield, between)]

STRING_DATA = \
    [("as is",           NoEntry,      identity)
    ,("contains",        WideEntry,    operator.contains )
    ,("doesn't contain", WideEntry,    not_contains )]

NUMBER_DATA = NUMERICAL(NarrowEntry, DblNarrowEntry)
RATING_DATA = NUMERICAL(RatingEntry, DblRatingEntry)
WEIGHT_DATA = NUMERICAL(WeightEntry, DblWeightEntry)

NOTHING_DATA = [("as is", NoEntry, identity)]


FAMILY_DATA = [(AnyOf, FamilyFactory, any_list)
            , (AllOf, FamilyFactory, all_list)]

CAT_DATA  = [(AnyOf, CatFactory,   any_list)
            ,(AllOf, CatFactory,   all_list)]

MECH_DATA = [(AnyOf, MechFactory,  any_list)
            ,(AllOf, MechFactory,  all_list)]

DESI_DATA = [(AnyOf, DesiFactory,  any_list)
            ,(AllOf, DesiFactory,  all_list)]

ART_DATA =  [(AnyOf, ArtFactory,  any_list)
            ,(AllOf, ArtFactory,  all_list)]


PUB_DATA =  [(AnyOf, PubFactory,   any_list)
            ,(AllOf, PubFactory,   all_list)]


DATA_STRINGS = 0
DATA_TYPES = 1
DATA_FUNC = 2
FUNC_ID = 3
RAW_DATA = [("Name",             STRING_DATA,   Name)
          , ("Size",             NUMBER_DATA,   Size)
          , ("Color Brightness", NUMBER_DATA,   Brightness)
          , ("Physical Weight",  NUMBER_DATA,   Weight)
          , ("Rating (Average)", RATING_DATA,   lambda g:g.rating_ave)
          , ("Rating (Ranked)",  RATING_DATA,   lambda g:g.rating_bayes)
          , ("Rating (Mine)",    RATING_DATA,   lambda g:g.rating_user)
          , ("Complexity",       WEIGHT_DATA,   lambda g:g.weight)
          , ("Min Players",      NUMBER_DATA,   lambda g:g.minplayers)
          , ("Max Players",      NUMBER_DATA,   lambda g:g.maxplayers)
          , ("Min Playing Time", NUMBER_DATA,   lambda g:g.minplaytime)
          , ("Max Playing Time", NUMBER_DATA,   lambda g:g.maxplaytime)
          , ("# of Plays",       NUMBER_DATA,   lambda g:g.num_plays)
          , ("Family",           FAMILY_DATA,   lambda g:g.families)
          , ("Category",         CAT_DATA,      lambda g:g.categories)
          , ("Mechanics",        MECH_DATA,     lambda g:g.mechanics)
          , ("Designer",         DESI_DATA,     lambda g:g.designers)
          , ("Artist",           ART_DATA,      lambda g:g.artists)
          , ("Publisher",        PUB_DATA,      lambda g:g.publishers)
          # @TODO, add more, or revisit this to be a bit more expansive
    ]

ALL_TYPE_DATA = list(zip(*RAW_DATA))


class OpMenu(ttk.OptionMenu):
    def __init__(self, master, values, changefunc, *args, **kwargs):
        ttk.OptionMenu.__init__(self, master, None)
        self._variable = Tk.StringVar(self)
        self.configure(textvariable=self._variable)
        self.set_menu(values[0], *values)
        self._variable.trace('w', self.__var_adjust)
        self.values = values
        self.changefunc = changefunc

    def __var_adjust(self, *vars):
        if self.changefunc is not None:
            var = self._variable.get()
            self.changefunc( self.values.index(var) )


class FilterEntryUI(Tk.Frame):
    def __init__(self, master, *args, **kwargs):
        Tk.Frame.__init__(self, master, width=150, height=15, *args, **kwargs)

        self.tkOp = None
        self.tkValues = []
        self.vars = []
        self.type = None
        self.op_labels = None
        self.op_data = None
        self.op_func = None
        self.field_data = None
        self.field_factory = None

        self.tkField = OpMenu(self, ALL_TYPE_DATA[DATA_STRINGS], self.__field_changed)
        self.tkField.pack(side=Tk.LEFT, anchor=Tk.W)

        self.__field_changed(0)

    def __field_changed(self, index):
        # Called when the field we're accessing changes
        # used to set up the appropriate ops and comparisons
        try:
            self.tkOp.destroy()
        except AttributeError:
            pass

        # wiggle up the rest of the filter based on what's been chosen
        self.type_data  = ALL_TYPE_DATA[DATA_TYPES][index]
        self.field_func = ALL_TYPE_DATA[DATA_FUNC][index]

        type_data = list(zip(*self.type_data))

        self.__rem_values()
        self.op_labels = None
        self.op_data = None
        self.op_func = None
        self.field_data = None

        if len(type_data):
            self.op_labels = type_data[DATA_OP_LABELS]
            self.field_data = type_data[DATA_FIELDS]
            self.op_data = type_data[DATA_OPS]

            self.tkOp = OpMenu(self, self.op_labels, self.__set_value)
            self.tkOp.pack(side=Tk.LEFT, anchor=Tk.W)
            self.__set_value(0) # has to happen BEFORE the pack

    def __set_value(self, index):
        # Changes up what the appropriate fields are
        self.__rem_values()

        self.op_func = self.op_data[index]
        self.field_factory = self.field_data[index]
        self.tkValues, self.vars = self.field_factory.add_widget(self)

    def __rem_values(self):
        # kills off all fields and values
        try:
            for v in self.tkValues:
                v.destroy()
        except AttributeError:
            pass

        self.vars = []

    def action(self):
        vals = [self.field_factory.convert_field(v.get()) for v in self.vars]
        return self.field_func, self.op_func, vals

    def set(self, func, op, vals):
        funcIndex = ALL_TYPE_DATA[DATA_FUNC].index(func)
        self.tkField._variable.set(ALL_TYPE_DATA[DATA_STRINGS][funcIndex])

        opIndex = self.op_data.index(op)
        self.tkOp._variable.set(self.op_labels[opIndex])

        for v in range(len(vals)):
            self.vars[v].set(vals[v])


class FilterBuilderUI(Tk.Frame):
    """Main widget that builds a sort/filter option.
    It's constituent parts are FilterEntryUIs"""

    addimg = None
    subimg = None
    upimg = None
    dnimg = None

    @staticmethod
    def init():
        FilterBuilderUI.addimg = ImageTk.PhotoImage(Image.open("pics/add.png"))
        FilterBuilderUI.subimg = ImageTk.PhotoImage(Image.open("pics/del.png"))
        FilterBuilderUI.upimg  = ImageTk.PhotoImage(Image.open("pics/arrow_up.png"))
        FilterBuilderUI.dnimg  = ImageTk.PhotoImage(Image.open("pics/arrow_dn.png"))

    def __init__(self, owner, *args, **kwargs):
        Tk.Frame.__init__(self, owner, *args, **kwargs)

        if FilterBuilderUI.addimg is None:
            FilterBuilderUI.init()

        self.list_items = []

        self.fbFrame = Tk.Frame(self)
        self.fbFrame.pack(anchor=Tk.NW)

        # divider/width-enforcer
        Tk.Frame(self, border=2, relief=Tk.RIDGE, bg=self["bg"], width=FILTER_WIDTH) \
            .pack(pady=0, fill=Tk.X, padx=2)

        ttk.Button(self, image=FilterBuilderUI.addimg, command=self.__add)\
            .pack(side=Tk.LEFT, padx=(10, 0), anchor=Tk.W)

    def set(self, preload):
        for func, op, values, reversed in preload:
            self.__add()
            justadded = top(self.list_items)
            justadded.entry.set(func, op, values)
            if reversed:
                self.__toggle(justadded)


    def __add(self):
        frm = Tk.Frame(self.fbFrame, bg=self["bg"])

        subfrm = Tk.Frame(frm, bg=self["bg"])
        killbtn     = ttk.Button(subfrm, image=FilterBuilderUI.subimg, command=functools.partial(self.__sub, frm))
        frm.upbtn   = ttk.Button(subfrm, image=FilterBuilderUI.upimg, command=functools.partial(self.__up, frm))
        frm.downbtn = ttk.Button(subfrm, image=FilterBuilderUI.dnimg, command=functools.partial(self.__down, frm))
        frm.reverbtn = ttk.Button(subfrm, text="▲A-Z", command=functools.partial(self.__toggle, frm), width=6)

        frm.spacer = Tk.Frame(frm, border=2, relief=Tk.RIDGE, bg="lightgray", width=FILTER_WIDTH)

        new = FilterEntryUI(subfrm, bg=self["bg"])
        frm.reversed = False
        frm.entry = new  # so we can track it later

        killbtn.grid(column=0, row=0, rowspan=2, sticky=Tk.W, padx=(10, 0))
        frm.upbtn.grid(column=1, row=0, sticky=Tk.NW)
        frm.downbtn.grid(column=1, row=1, sticky=Tk.SW)
        frm.reverbtn.grid(column=3, row=0, rowspan=2, sticky=Tk.W)
        new.grid(column=2, row=0, rowspan=2, sticky=Tk.W)

        subfrm.pack(anchor=Tk.NW, pady=5)
        frm.spacer.pack(anchor=Tk.NW, pady=5)


        self.list_items.append(frm)
        self.__reorder()
        try:
            self.master.master.update_height()
        except AttributeError:
            pass

    def __sub(self, frame):
        frame.destroy()
        self.list_items.remove(frame)
        self.__reorder()
        try:
            self.master.master.update_height()
        except AttributeError:
            pass

    def __up(self, frame):
        li = self.list_items
        index = li.index(frame)
        if index > 0:
            li[index], li[index-1] = li[index-1], li[index]
        self.__reorder()

    def __down(self, frame):
        li = self.list_items
        index = li.index(frame)
        if index < len(li)-1:
            li[index], li[index + 1] = li[index + 1], li[index]

        self.__reorder()

    def __toggle(self, frame):
        frame.reversed = not frame.reversed
        if frame.reversed:
            frame.reverbtn.configure(text="▼Z-A")
        else:
            frame.reverbtn.configure(text="▲A-Z")


    def __reorder(self):
        length = len(self.list_items)
        for i in range(length):
            frm = self.list_items[i]
            frm.grid(row=i+10, sticky=Tk.NW, pady=(5,0))

            FilterBuilderUI.__config_btn(frm.upbtn,  length > 1 and i > 0)
            FilterBuilderUI.__config_btn(frm.downbtn, length > 1 and i < length-1)

    @staticmethod
    def __config_btn(btn, enabled):
        if enabled:
            btn.configure(state=Tk.NORMAL)
        else:
            btn.configure(state=Tk.DISABLED)

    def get_actions(self):
        return [ a.entry.action() +(a.reversed,) for a in self.list_items ]



if __name__=="__main__":
    fbui = None

    class fakeGame:
        def __init__(self):
            self.sortname = "game"
            self.x = 5
            self.y = 7
            self.z = 9
            self.w = 11
            self.color = "#FF00FF"
            self.minplayers = 3
            self.maxplayers = 8
            self.publishers = ["A"]

    def do_it():
        agame = fakeGame()
        result = fbui.get_actions()
        print(result)
        for func, op, values, rev in result:
             print( op(func(agame), *values, rev))

    root = Tk.Tk()
    #FilterBuilderUI.init()
    fbui = FilterBuilderUI(root)
    fbui.pack()

    setlist.append(setlist.Publishers, ["A", "B"])

    Tk.Button(root, text="Compute", command=do_it).pack()

    root.mainloop()
