import tkinter as Tk
import tkinter.ttk as ttk
import sys
from constants import *


class NameBox(Tk.Toplevel):
    def __init__(self, window, app, pref, errorMessage=None):
        Tk.Toplevel.__init__(self, window)
        self.config(bg="#f0f0f0")
        self.title("User Name")
        self.focus_force()
        label = ttk.Label(self, text="BGG Username:", font="Sans 12 bold")
        label.grid(sticky=Tk.SW, pady=10, padx=10)
        self.box = ttk.Entry(self,  width=32, font="Sans 16 bold")
        self.box.grid(sticky=Tk.NSEW, pady=0, padx=10)

        self.box.insert(0,pref.user)
        self.app = app
        self.box.bind("<Return>", self.set_name)
        self.box.focus_force()

        frm = Tk.Frame(self, bg="#f0f0f0")
        if sys.platform == "darwin":
            frm.grid(pady=15, padx=10, sticky=Tk.E)
            okbtn = ttk.Button(frm,  text="OK", command=self.set_name, default=Tk.ACTIVE )#,     width=BTN_WIDTH, height=BTN_HEIGHT, bg=OK_BTN_COLOR)
            nokbtn = ttk.Button(frm, text="Cancel", command=self.destroy)#, width=BTN_WIDTH, height=BTN_HEIGHT,  bg=CANCEL_BTN_COLOR)

            okbtn.pack(side=Tk.RIGHT, padx=10)
            nokbtn.pack(side=Tk.LEFT, padx=10)
        else:
            frm.grid(pady=15, padx=10)
            okbtn = Tk.Button(frm, text="OK", command=self.set_name, width=BTN_WIDTH, height=BTN_HEIGHT, bg=OK_BTN_COLOR)
            nokbtn = Tk.Button(frm, text="Cancel", command=self.destroy, width=BTN_WIDTH, height=BTN_HEIGHT,  bg=CANCEL_BTN_COLOR)

            okbtn.pack(side=Tk.LEFT, padx=20)
            nokbtn.pack(side=Tk.RIGHT, padx=20)

        okbtn.bind("<Return>",  okbtn["command"])
        nokbtn.bind("<Return>", nokbtn["command"])

        self.grab_set()
        window.wait_window(self)
        self.grab_release()

    def set_name(self, event=None):
        self.app.collection_fetch(self.box.get())
        self.destroy()



if __name__ == "__main__":
    root = Tk.Tk()
    root.update()

    class fakeApp:
        def collection_fetch(self,text):
            print("Fetching:", text)

    class fakePref:
        def __init__(self):
            self.user = 'test'

    s = NameBox(root, fakeApp(), fakePref())
    # s.top.lift()
    # root.wait_window(s.top)

    root.mainloop()