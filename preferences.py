import shelf
import game
import pathlib
from constants import *
import pickle
import tkinter as Tk
import tkinter.ttk as ttk
import contrib.accordion as accordion
import sorts

class Preferences:
    def __init__(self):
        self.sortFuncs = [(sorts.Size, sorts.identity, [], False)] # default, sort by size
        self.filterFuncs = []
        self.storeStyle = shelf.StoreStyle.PreferStack
        self.sideStyle = game.SidePreference.Left
        self.stackSort = shelf.StackSort.Size
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
        print(e)
        p = Preferences()

    p.set_app(app)
    return p


def save(pref):
    with open(pathlib.Path(CACHE_DIR) / "prefs.pkl", "wb") as file:
        pickle.dump(pref, file)


class PrefBundle(Tk.Frame):
    def __init__(self, window, text, values, pref, out_var, wigglefunc):
        Tk.Frame.__init__(self, window, width=220, height=25)
        self.grid_propagate(False)
        self.var = Tk.StringVar(self)
        self.var.trace('w', self.var_wiggle)
        self.values = values
        self.pref = pref
        self.out_var = out_var
        self.wigglefunc = wigglefunc

        ttk.Label(self, text=text, width=15)\
            .grid(row=0, column=0, sticky=Tk.E)
        ttk.OptionMenu(self, self.var, values[getattr(self.pref, self.out_var)], *values)\
            .grid(row=0, column=1, sticky=Tk.W)

    def var_wiggle(self, *vars):
        setattr(self.pref, self.out_var, self.values.index(self.var.get()))
        self.wigglefunc()


class PreferencesUI(Tk.Toplevel):
    def __init__(self, window, pref:Preferences, resortfunc):
        Tk.Toplevel.__init__(self, window)
        self.title("Preferences")
        self.focus_force()
        self.pref = pref

        self.resort_func = resortfunc

        frm = Tk.Frame(self, borderwidth=10)
        frm.pack(anchor=Tk.SW, side=Tk.LEFT)

        acc = accordion.Accordion(frm, 450)
        acc.pack(anchor=Tk.NW)
        sortchord = acc.create_chord("Sorting Criteria").body
        self.sortWidget = sorts.FilterBuilderUI(sortchord)
        self.sortWidget.pack(anchor=Tk.W)

        filtchord = acc.create_chord("Filtering Criteria").body
        self.filtWidget = sorts.FilterBuilderUI(filtchord)
        self.filtWidget.pack(anchor=Tk.W)

        PrefBundle(frm, "Shelving Choice:",   shelf.StoreStyle_names,    pref, "storeStyle", pref.set_prefs).pack()
        PrefBundle(frm, "Vertical Rotation:", game.SidePreference_names, pref, "sideStyle",  pref.set_prefs).pack()
        PrefBundle(frm, "Stack Sort:",        shelf.StackSort_names,     pref, "stackSort",  pref.set_prefs).pack()

        btn = Tk.Button(frm, text="Re-Sort Games", width=20, command=self.resort)
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
