import shelf
import game, sys
import pathlib
from constants import *
import pickle
import tkinter as Tk
import tkinter.ttk as ttk
from PIL import Image, ImageTk
import contrib.accordion as accordion
import sorts
import logging
logger = logging.getLogger(__name__)

VERT_STYLE = "Vert.TRadiobutton"

class Preferences:
    def __init__(self):
        self.sortFuncs = [(sorts.Size, sorts.identity, [], False)] # default, sort by size
        self.filterFuncs = []
        self.storeStyle = shelf.StoreStyle.PreferStack
        self.sideStyle = game.SidePreference.Left
        self.stackSort = shelf.StackSort.Size
        self.shelfOrder = shelf.ShelfOrder.VerticalFirst
        self.user = ""
        self.app = None

    def set_app(self, app):
        self.app = app

    def set_prefs(self, save_=True):
        shelf.Shelf.set_store_style(self.storeStyle)
        shelf.GameStack.setStackSort(self.stackSort)
        game.Game.set_side_preference(self.sideStyle)
        try:
            self.app.set_sorts(self.sortFuncs, self.filterFuncs)
        except AttributeError:
            pass

        if save_:
            save(self)

    @staticmethod
    def switch_values(in_, out_, data):
        return [(out_[in_.index(func)], op, values, rev) for (func, op, values, rev) in data]


    def __getstate__(self):
        d = self.__dict__.copy()
        del d["app"]

        justlabels = [label for (label, data, func) in sorts.RAW_DATA]
        justfuncs  = [func for (label, data, func) in sorts.RAW_DATA]

        # translate funcs (which may be lambdas, and thus not pickleable
        # to their strings, which... are better than nothing
        d["sortFuncs"]   = Preferences.switch_values(justfuncs, justlabels, d["sortFuncs"])
        d["filterFuncs"] = Preferences.switch_values(justfuncs, justlabels, d["filterFuncs"])
        return d

    def __setstate__(self, dict):
        self.__init__() # this doesn't seem to be called normally, so force it

        justlabels = [label for (label, data, func) in sorts.RAW_DATA]
        justfuncs = [func for (label, data, func) in sorts.RAW_DATA]

        # translate funcs (which may be lambdas, and thus not pickleable
        # to their strings, which... are better than nothing
        dict["sortFuncs"]   = Preferences.switch_values(justlabels, justfuncs, dict["sortFuncs"])
        dict["filterFuncs"] = Preferences.switch_values(justlabels, justfuncs, dict["filterFuncs"])

        self.__dict__.update(dict)
        self.set_prefs(False)


def load(app):
    try:
        with open(pathlib.Path(CACHE_DIR) / "prefs.pkl", "rb") as file:
            p = pickle.load(file)

    except (FileNotFoundError, EOFError):
        p = Preferences()

    except pickle.UnpicklingError as e:
        logger.exception("Pickle error: {}".format(e))
        p = Preferences()

    p.set_app(app)
    return p


def save(pref):
    with open(pathlib.Path(CACHE_DIR) / "prefs.pkl", "wb") as file:
        pickle.dump(pref, file)


class PrefBundle(Tk.Frame):
    def __init__(self, window, text, values, pref, out_var, adjustFunc):
        Tk.Frame.__init__(self, window, width=220, height=25)
        self.grid_propagate(False)
        self.var = Tk.StringVar(self)
        self.var.trace('w', self.onVarAdjust)
        self.values = values
        self.pref = pref
        self.out_var = out_var
        self.adjustFunc = adjustFunc

        self.make(text, values)

    def make(self, text, values):
        ttk.Label(self, text=text, width=15)\
            .grid(row=0, column=0, sticky=Tk.E)

        ttk.OptionMenu(self, self.var, values[getattr(self.pref, self.out_var)], *values)\
            .grid(row=0, column=1, sticky=Tk.W)

    def onVarAdjust(self, *vars):
        setattr(self.pref, self.out_var, self.values.index(self.var.get()))
        #print(getattr(self.pref, self.out_var))
        self.adjustFunc()

class PrefBundleRadio(PrefBundle):
    def __init__(self, window, text, values, icons, pref, out_var, adjustFunc):
        self.icons = []
        for i in icons:
            image = ImageTk.PhotoImage(Image.open(i))
            self.icons.append(image)
        # has to happen afterwards so that make() works
        PrefBundle.__init__(self, window, text, values, pref, out_var, adjustFunc)
        self.var.set(values[getattr(self.pref, self.out_var)])

    @staticmethod
    def init():
        s = ttk.Style()
        if sys.platform == "darwin":
            s.theme_use("alt")
        s.layout(VERT_STYLE,
                 [
                     ('Radiobutton.padding',
                      {'children':
                           [('Radiobutton.indicator', {'side': Tk.BOTTOM, 'sticky': Tk.S}),
                            # Just need to change indicator's 'side' value
                            ('Radiobutton.focus', {'side': Tk.BOTTOM,
                                                   'children':
                                                       [('Radiobutton.label', {'sticky': Tk.NSEW, 'side' : Tk.BOTTOM})],
                                                   'sticky': Tk.S})
                            ],
                       'sticky': Tk.NSEW, 'side' : Tk.BOTTOM}),
                     #('Radiobutton.label', {'justify' : Tk.CENTER})
                 ])
        s.map(VERT_STYLE,
              #              foreground=[('disabled', 'yellow'),
              #                          ('pressed', 'red'),
              #                          ('active', 'blue')],
              background=[('selected', '#A8E4B3'),
                          ('active', '#D3E2D5')],
              #              highlightcolor=[('focus', 'green'),
              #                              ('!focus', 'red')],
              #             relief=[('pressed', 'groove'),
              #                     ('!pressed', 'ridge')]
              )

    def make(self, text, values):
        frm = ttk.LabelFrame(self, text=text, padding=5)
        frm.pack()
        for value, icon, index in zip(values, self.icons, range(len(self.icons), 0, -1)):
            ttk.Radiobutton(frm, style=VERT_STYLE, text=value, variable=self.var, value=value, image=icon, compound=Tk.TOP)\
                .pack(side=Tk.LEFT)
            # divider
            if index > 1:
                Tk.Frame(frm, border=2, relief=Tk.RIDGE, bg="lightgray", height=40) \
                    .pack(pady=2, fill=Tk.Y, padx=5, side=Tk.LEFT)


class PreferencesUI(Tk.Toplevel):
    def __init__(self, window, pref:Preferences, resortfunc):
        Tk.Toplevel.__init__(self, window)

        PrefBundleRadio.init()

        self.title("Preferences")
        self.focus_force()
        self.pref = pref

        self.resort_func = resortfunc

        self.sort_img = ImageTk.PhotoImage(Image.open("pics/sort.png"))
        self.filter_img= ImageTk.PhotoImage(Image.open("pics/filter.png"))
        self.resort_img = ImageTk.PhotoImage(Image.open("pics/resort.png"))
        self.setting_img = ImageTk.PhotoImage(Image.open("pics/settings.png"))

        frm = Tk.Frame(self, borderwidth=10, bg="#f0f0f0")
        frm.pack(anchor=Tk.SW, side=Tk.LEFT, fill=Tk.BOTH, expand=1)

        acc = accordion.Accordion(frm, sorts.FILTER_WIDTH)
        acc.pack(anchor=Tk.NW, fill=Tk.X, expand=1)
        sortchord = acc.create_chord("Sorting Criteria", cursor=None, image=self.sort_img).body
        self.sortWidget = sorts.FilterBuilderUI(sortchord, bg="#f0f0f0")
        self.sortWidget.pack(anchor=Tk.W, fill=Tk.BOTH, expand=1)
        self.sortWidget.set(self.pref.sortFuncs)

        filtchord = acc.create_chord("Filtering Criteria", cursor=None, image=self.filter_img).body
        self.filtWidget = sorts.FilterBuilderUI(filtchord, bg="#f0f0f0")
        self.filtWidget.pack(anchor=Tk.W, fill=Tk.BOTH, expand=1)
        self.filtWidget.set(self.pref.filterFuncs)

        setchord = acc.create_chord("Settings", cursor=None, image=self.setting_img, background="lightgray").body

        PrefBundleRadio(setchord, "Shelving Choice", shelf.StoreStyle_names, shelf.StoreStyle_pics, pref, "storeStyle", pref.set_prefs)\
            .pack(pady=5)

        subfrm = Tk.Frame(setchord, bg="lightgray")
        subfrm.pack(pady=5)
        PrefBundleRadio(subfrm, "Vertical Rotation", game.SidePreference_names, game.SidePreference_pics, pref, "sideStyle",  pref.set_prefs)\
            .pack(padx=10, side=Tk.LEFT)
        PrefBundleRadio(subfrm, "Stack Sort", shelf.StackSort_names, shelf.StackSort_pics, pref, "stackSort", pref.set_prefs)\
            .pack(padx=10, side=Tk.LEFT)
        PrefBundleRadio(subfrm, "Shelf Order", shelf.ShelfOrder_names, shelf.ShelfOrder_pics, pref, "shelfOrder", pref.set_prefs) \
            .pack(padx=10, side=Tk.RIGHT)

        Tk.Frame(frm, border=2, relief=Tk.RIDGE, bg="lightgray").pack(pady=8, fill=Tk.X, padx=2)

        btn = ttk.Button(frm, text="Re-Sort Games", width=BTN_WIDTH, command=self.resort, image=self.resort_img, compound=Tk.LEFT)
        btn.bind("<Return>", btn["command"])
        btn.pack()

    def resort(self):
        self.pref.sortFuncs = self.sortWidget.get_actions()
        self.pref.filterFuncs = self.filtWidget.get_actions()
        save(self.pref)
        self.resort_func()

if __name__ == "__main__":
    root = Tk.Tk()
    root.update()

    def resort_games(self): pass
    class fakeApp: pass

    p = load(fakeApp)

    fbui = PreferencesUI(root, p, resort_games)
    # s.top.lift()
    # root.wait_window(s.top)

    root.mainloop()
