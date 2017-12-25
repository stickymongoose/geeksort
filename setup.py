import sys
import os
from cx_Freeze import setup, Executable

hacky_path = r'C:/Users/jtudisco/AppData/Local/Programs/Python/Python36-32'
os.environ['TCL_LIBRARY'] = hacky_path + r'/tcl/tcl8.6'
os.environ['TK_LIBRARY'] = hacky_path + r'/tcl/tk8.6'

includes = []
include_files = [
    hacky_path + r"/DLLs/tcl86t.dll",
    hacky_path + r"/DLLs/tk86t.dll",
    "README.md",
    "shelves.txt"
]

subdirs = ["pics"]

for dir in subdirs:
    for files in os.listdir(dir):
        include_files.append( (dir + "/" + files, dir + "/" + files) )

packages = ["os", "idna"]
path = sys.path+['modules']

# Dependencies are automatically detected, but it might need fine tuning.
build_exe_options = {
    "packages" : packages,
    'path' : path,
    'includes' : includes,
    'include_files' : include_files
}

# GUI applications require a different base on Windows (the default is for a
# console application).
base = None
if sys.platform == "win32":
    base = "Win32GUI"

executables = [
    Executable('geeksort.py', base=base)
]

setup(  name = "geeksort",
        version = "0.5",
        author= 'Jtudisco',
        description = "My GUI application!",
        options = {"build_exe": build_exe_options},
        executables = executables)