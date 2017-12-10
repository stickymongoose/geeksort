import shelf
import game
import pathlib
from constants import *
import pickle
import tkinter as Tk
import tkinter.ttk as ttk

class Preferences:
    def __init__(self):
        self.sortFuncs = ["bySize"]
        self.storeStyle = shelf.StoreStyle.PreferStack
        self.sideStyle = game.SidePreference.Left
        self.stackSort = shelf.StackSort.Size
        self.user = ""
        self.app = None

    def set_app(self, app):
        self.app = app

    def set_prefs(self, save_=True):
        print("Prefs set", self.storeStyle, self.sideStyle, self.stackSort)
        shelf.Shelf.set_store_style(self.storeStyle)
        shelf.GameStack.setStackSort(self.stackSort)
        game.Game.set_side_preference(self.sideStyle)
        try:
            self.app.set_sorts(*self.sortFuncs)
        except AttributeError:
            pass

        if save_:
            save(self)

    def __getstate__(self):
        d = self.__dict__.copy()
        del d["app"]
        return d

    def __setstate__(self, dict):
        self.__init__() # this doesn't seem to be called...
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
    def __init__(self, window, pref, sortfunc):
        Tk.Toplevel.__init__(self, window)
        self.title("Preferences")
        self.focus_force()
        self.pref = pref

        frm = Tk.Frame(self, borderwidth=10)
        frm.pack()

        PrefBundle(frm, "Shelving Choice:",   shelf.StoreStyle_names,    pref, "storeStyle", pref.set_prefs).pack()
        PrefBundle(frm, "Vertical Rotation:", game.SidePreference_names, pref, "sideStyle", pref.set_prefs).pack()
        PrefBundle(frm, "Stack Sort:",        shelf.StackSort_names,     pref, "stackSort", pref.set_prefs).pack()

        btn = Tk.Button(frm, text="Re-Sort Games", width=20, command=sortfunc)
        btn.bind("<Return>", btn["command"])
        btn.pack()

if __name__ == "__main__":
    root = Tk.Tk()
    root.update()

    def resort_games(self): pass
    class fakeApp: pass

    p = load(fakeApp)

    s = PreferencesUI(root, p, resort_games)
    # s.top.lift()
    # root.wait_window(s.top)

    root.mainloop()
