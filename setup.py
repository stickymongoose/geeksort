import sys
import os
import shutil
import subprocess
from cx_Freeze import setup, Executable
from constants import GS_VERSION

hacky_path = r'C:/Users/jtudisco/AppData/Local/Programs/Python/Python36-32'
os.environ['TCL_LIBRARY'] = hacky_path + r'/tcl/tcl8.6'
os.environ['TK_LIBRARY'] = hacky_path + r'/tcl/tk8.6'

includes = []
include_files = [
    hacky_path + r"/DLLs/tcl86t.dll",
    hacky_path + r"/DLLs/tk86t.dll",
    "README.md",
    "shelves.txt",
    "logging.json"
]

excludes = ['PyQt5',  'scipy', 'tcl']

subdirs = ["pics"]

for dir in subdirs:
    for files in os.listdir(dir):
        include_files.append( (dir + "/" + files, dir + "/" + files) )

packages = ["os", "numpy", "idna"]
path = sys.path+['modules']

# Dependencies are automatically detected, but it might need fine tuning.
build_exe_options = {
    "packages" : packages,
    'path' : path,
    'includes' : includes,
    'include_files' : include_files,
    'excludes' : excludes,
    'optimize' : 2
}

# GUI applications require a different base on Windows (the default is for a
# console application).
base = None
if sys.platform == "win32":
    base = "Win32GUI"

executables = [
    Executable('geeksort.py', base=base)
]

shutil.rmtree("build", ignore_errors=True )

setup(  name = "geeksort",
        version = GS_VERSION,
        author= 'Jtudisco',
        description = "GeekSort",
        options = {"build_exe": build_exe_options},
        executables = executables)

subprocess.run("7z a -r build\geeksort-win-v{}.7z build\exe.win32-3.6".format(GS_VERSION.replace(".","")))