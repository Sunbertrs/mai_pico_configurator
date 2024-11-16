import sys
sys.path.insert(0, sys.path[0].replace("cmds",""))
from tkinter import messagebox
from communication import program_update

messagebox.showwarning("Exiting", "The program will now exit to update the firmware.")
program_update()
sys.exit()
