![Example of Geeksort](web/example.png)

## What is this?
Maybe you've got a lot of board games. Maybe you don't have a lot of shelves. Maybe you just like things organized.
Well, GeekSort's for you. 

This assumes that you have a [BoardGameGeek](www.boardgamegeek.com) account with the games you wanted sorted.

# Getting Started
## For the impatient
If you're raring to start sorting games onto your shelves and don't care about the most up-to-date version, this is for you.

1. **Download** the most recent build for your platform. Currently, just windows, [here](https://bitbucket.org/geeksort/geeksort/downloads/)

2. **Unzip the package** into a place you like.

3. Jump down to **Operating Instructions**.

## For the advanced
You want the cutting edge. Or maybe you want to help push the edge further. Well, brave traveler, you're going to need to get source.

0. You'll need Python 3.6.4...ish to run GeekSort from source.
* For Windows folks, get it [here](https://www.python.org/downloads/)
* For Mac Folks... [here?](https://www.python.org/downloads/mac-osx/), unless it's installed already...
* For Linux Users, run your appropriate package getter to get the latest version.

0. Create a BitBucket account [here](https://bitbucket.org/account/signup/) or [log in](https://bitbucket.org/account/signin/)

1. **Create a directory** to work out of. Say, Desktop/geeksort

2. Click the plus (+) on the leftmost toolbar of Bitbucket and Click **Clone This Repository** and copy the link. ![Plus Location](web/sidepanel.png)

3. Open up **a command window** in the directory you just made.

4. **Paste the link**, and add a . to the end, like `git clone https://<user>@bitbucket.org/geeksort/geeksort.git .`

5. Wait.

6. Run `pip3 install -r requirements.txt` to get all the updates (some folks may just run pip instead).

7. Wait.

8. Run Geeksort with `python3 geeksort.py`. **Note**: Your setup may not have python3 installed as `python3`, and you may need to use `python` instead.


# Operating Instructions
1. Find a tape measure, yard/meter stick, or appropriate schematics from the internet for your shelves.

2. Edit Shelves.txt in your favorite text editor.

3. Following the instructions therein, edit the dimensions to match your shelves
**Note that this step will eventually be streamlined**

4. Launch the executable.

5. Enter your name when prompted.

6. WAIT. This step can take a long time, depending on how overloaded the BGG servers are. Can easily take several minutes.

7. Once everything's ready, it'll populate your shelves in a default manner.

8. At this point, you can experiment with different sorting methods in the Preferences tab, or edit some games.

9. Right-clicking on a game on the shelves or the overflow list to the right opens up more options, such as visiting BGG to edit or review, or excluding (temporarily) from being shelved.

## Some of my games have blue question marks!

Chances are you it had to guess on the sizes/versions of your games. These games are marked with a blue question mark (?).
Due to the wide variety of games sizes, GeekSort will guess based on the largest one, and be conservative. To adjust this behavior,
right click on the most egregious games (OGRE Designer's Edition, for example), and adjust your collection's version.
After you've done several, you must then reload your collection manually for GeekSort to get the updated sizes.

## I have some games I don't want sorted!
When sorting your games, you can specify a Filter, which will exclude any games that match from being put on shelves.

For a more targeted approach, you can exclude games by right-clicking and selecting Exclude. 
**Note:** This will last until the next time you update your game collection from BGG.
For a more permanent solution, go to that game's page (via the right click menu), and add **#GeekSort-Exclude** as a comment.
It's not the prettiest solution, but there seemingly isn't an API for reading the tags.  This may eventually be cached off locally.

## These sorts are sub-optimal! They could definitely fit better!

* Packing things into boxes is a known problem in computer science, and many different algorithms exist.
  To keep the problem simpler (and GeekSort actually released), it's currently a very greedy packing attempt.
  It starts at the topleft-most shelf, and starts slotting in games, moving on to the next available shelf if there's no space.
  As such, you can trick it a bit to get better sorting results
* Try adjusting your sort preferences, rearranging options around
* If you're concerned about space, make sure that sorting by Size, As-is is always the last item.
* Try experimenting with different shelf ordering by rearranging Shelves.txt (more dynamic options are slated for later). 

## I found a problem. Where do I go?

Try checking out the [subreddit](www.reddit.com/r/geeksort), or the [Trello board](https://trello.com/b/GtFVkybB/issue-tracking), 
which is linked at the [GeekSort BitBucket](https://bitbucket.org/geeksort/geeksort/) page.


## I like this, I want to help!

Check out the [Trello board](https://trello.com/b/GtFVkybB/issue-tracking) with steps on how to join/post. 

# Attribution
## Icons
Icons attributed to https://material.io/icons/ under Apache License Version 2.0. 
Icons have been modified a bit for color
Not all icons are from Material.io; just the good looking ones.

## Libraries
All libraries in contrib/ are external to this project, but may have been modified to fix bugs or add features.

### Accordion.py
Author: Miguel Martinez Lopez
Was forked from Revision 5
MIT License
[home](http://code.activestate.com/recipes/580781-metro-accordion-for-tkinter/)

### Scrolling Frame
Author: Miguel Martinez Lopez
Version 0.22
[home](https://github.com/ActiveState/code/blob/master/recipes/Python/580640_Scrolling_frame_mouse_wheel/recipe-580640.py)

### Mixed_fractions.py
Mixed Fraction Class 1.0.3  by JB0x2D1 (Jeremy Beck)
[home](https://sourceforge.net/projects/pythonmixedfractionsclass/)



