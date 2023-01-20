from spef.utils.logger import *

"""
- init setting:
* exit_key is set to any key
* first jump to current working directory
* there is no command to run
"""


class Bash_action:
    def __init__(self):
        self.type = None
        # hex value of key (if None, read any key to exit bash)
        self.exit_key = None

        # first go to current working directory (in env) then execute command
        self.run_in_cwd = True
        self.cmd = ""

    def dont_jump_to_cwd(self):
        self.run_in_cwd = False

    def set_exit_key(self, key):
        self.exit_key = key

    def add_command(self, cmd):
        self.cmd = cmd
