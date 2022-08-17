
from utils.logger import *

"""
- init setting:
* exit_key is set to any key
* first jump to current working directory
* there is no command to run
"""
class Bash_action():
    def __init__(self):
        self.type = None
        self.exit_key = None # hex value of key (if None, read any key to exit bash)

        self.run_in_cwd = True # first go to current working directory (in env) then execute command
        self.cmd = ""

    def dont_jump_to_cwd(self):
        self.run_in_cwd = False

    def set_exit_key(self, key):
        self.exit_key = key

    def add_command(self, cmd):
        self.cmd = cmd
