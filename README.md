**Getting started using GeekSort for the impatient**
If you're raring to start sorting games onto your shelves and don't care about the most up-to-date version, this is for you.
1. Download the most recent build for your platform
2. Unzip the package into the appropriate place.
3. Jump down to Once Installed below


## Once Installed##
1. Find a tape measure, yard/meter stick, or appropriate schematics from the internet for your shelves.
2. Edit Shelves.txt in your favorite text editor.
3. Following the instructions therein, edit the dimensions to match your shelves
* Note that this step is expected to change eventually
4. Launch the executable.
5. Enter your name when prompted.
6. WAIT. This step can take a long time, depending on how overloaded the BGG servers are. Can easily take several minutes.
7. Once everything's ready, it'll populate your shelves in a default manner!
8. At this point, you can experiment with different sorting methods in the Preferences tab, or edit some games.

** Some of my games have blue question marks! **
Chances are you it had to guess on the sizes/versions of your games. These games are marked with a blue question mark (?).
Due to the wide variety of games sizes, GeekSort will guess based on the largest one, and be conservative. To adjust this behavior,
right click on the most egregious games (OGRE Designer's Edition, for example), and adjust your collection's version.
After you've done several, you must then reload your collection manually for GeekSort to get the updated sizes.

** These sorts are sub-optimal! They could definitely fit better! **
* Packing things into boxes is a known problem in computer science, and many different algorithms exist.
  To keep the problem simpler (and GeekSort actually released), it's currently a very greedy packing attempt.
  It starts at the topleft-most shelf, and starts slotting in games, moving on to the next available shelf if there's no space.
  As such, you can trick it a bit to get better sorting results
* Try adjusting your sort preferences, rearranging options around
* If you're concerned about space, make sure that sorting by Size, As-is is always the last item.
* Try experimenting with different shelf ordering by rearranging Shelves.txt (more dynamic options are slated for later). 

** I found a problem. Where do I go? **
Try checking out the subreddit at www.reddit.com/r/geeksort, or the trello board at https://trello.com/b/GtFVkybB/issue-tracking.


