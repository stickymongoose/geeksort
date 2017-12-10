import tkinter as Tk
import tkinter.ttk as ttk


class NameBox(Tk.Toplevel):
    def __init__(self, window, app, pref):
        Tk.Toplevel.__init__(self, window)
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

        frm =  Tk.Frame(self)
        frm.grid(pady=15, padx=10)
        okbtn = Tk.Button(frm, text="OK", width=15, height=2, command=self.set_name, bg="lightgreen")
        nokbtn = Tk.Button(frm, text="Cancel", width=15, height=2, command=self.destroy, bg="red2")

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

    s = NameBox(root, fakeApp(),"user")
    # s.top.lift()
    # root.wait_window(s.top)

    root.mainloop()