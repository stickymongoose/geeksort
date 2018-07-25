#!/usr/bin/env python3

import tkinter as Tk
from tkinter import ttk
import logging
from contextlib import contextmanager
from constants import *

if __name__ == "__main__":
    from geeksort import setup_logging
    setup_logging()

progresslogger = logging.getLogger("progressbar")



class ProgressBar:
    def make(self, parent):
        self.progressPct = Tk.DoubleVar(0.0)
        self.tkProgressActives = {}

        self.tkProgressFrm = ttk.Frame(parent)
        self.tkProgressLabel = ttk.Label(self.tkProgressFrm)
        self.tkProgressLabel.grid(row=0, column=0)
        self.tkProgressBarSpinner = ttk.Progressbar(self.tkProgressFrm, mode="indeterminate", length=200)
        self.tkProgressBarSpinner.start()  # will never stop
        self.tkProgressBarPct = ttk.Progressbar(self.tkProgressFrm, mode="determinate", length=200
                                                , variable=self.progressPct)
        self.tkProgressBarSpinner.start()  # will never stop
        self.tkProgressBarPct.grid(row=1, column=0)
        self.tkProgressBarSpinner.grid(row=2, column=0)
        self.tkProgressMsg = ttk.Label(self.tkProgressFrm)
        self.tkProgressMsg.grid(row=3, column=0)


    def _update_work(self):
        if len(self.tkProgressActives) > 0:
            maxpct = (-1, -1)
            maxmsg = (-1, "")

            # check if we need a progress bar and/or a spinner
            needProgress = False
            needSpinner = False
            for type, (msg, progress, pct) in self.tkProgressActives.items():
                progresslogger.debug('Has: %i "%s" %f', type, msg, pct)
                if progress:
                    needProgress = True
                    if type > maxpct[0]:
                        maxpct = [type, pct]
                else:
                    needSpinner = True

                if type > maxmsg[0]:
                    maxmsg = [type,msg]

            progresslogger.debug('Top choice is %i "%s", %i %f', maxmsg[0], maxmsg[1], maxpct[0], maxpct[1])

            if needProgress:
                self.progressPct.set(maxpct[1])
                self.tkProgressBarPct.grid(row=1, column=0)
            else:
                self.tkProgressBarPct.grid_forget()

            if needSpinner:
                self.tkProgressBarSpinner.grid(row=2, column=0)
            else:
                self.tkProgressBarSpinner.grid_forget()

            self.tkProgressLabel.configure(text=maxmsg[1])
            self.tkProgressFrm.pack(anchor=Tk.CENTER, expand=True)
        # progressActives is empty, so turn off the progress bar
        else:
            self.tkProgressFrm.pack_forget()


    def start(self, label, type, progress=False):
        """Queues up a progress bar, with priority given to higher-numbered types"""
        # print((threading.current_thread().name, "starts", type, label)
        progresslogger.info("Start type: %i %s, %s", type, label, progress)
        if type == WorkTypes.MESSAGE:
            self.tkProgressMsg.configure(text=label)
        else:
            self.tkProgressActives[type] = [label, progress, 0]
            self.tkProgressFrm.after(0, self._update_work)
        # self._update_work()


    def set_percent(self, pct, type):
        # print("Progress", pct, threading.current_thread().getName())
        if type in self.tkProgressActives:
            progresslogger.debug("Percent: %i %0.4f", type, pct)
            self.tkProgressActives[type][2] = pct * 100.0
            self.tkProgressFrm.after(0, self._update_work)
        else:
            progresslogger.error("Can't Percent %0.4f for %i--not started", pct, type)


    def stop(self, type):
        # print((threading.current_thread().name, "stops", type)
        progresslogger.info("Stop %i", type)
        if type == WorkTypes.MESSAGE:
            self.tkProgressMsg.configure(text="")
        try:
            self.tkProgressActives.pop(type)
        except KeyError:
            pass

        self.tkProgressFrm.after(0, self._update_work)
        # self._update_work()

    #I feel there's gotta be some way to merge this with just start...
    # like open vs with open...
    @contextmanager
    def work(self, label, type, progress=False):
        self.start(label, type, progress)
        yield
        self.stop(type)

if __name__ == "__main__":
    t = Tk.Tk()
    p = ProgressBar()
    p.make(t)
    import time
    import threading
    def delayed():
        def _sub():
            p.start("Yes?", WorkTypes.GAME_DATA, progress=True)
            time.sleep(1)
            p.set_percent(0.5, WorkTypes.GAME_DATA)
            time.sleep(1)
            with p.work("No!", WorkTypes.QUEUED_UP, progress=True):
                time.sleep(2)
                p.set_percent(0.75, WorkTypes.QUEUED_UP)
                time.sleep(2)
            # should see the progress bar pop back down to 50%
            time.sleep(2)
            p.stop(WorkTypes.GAME_DATA)

        threading.Thread(target=_sub).start()

    t.after(1000,delayed)
    t.mainloop()


