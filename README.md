# DP

* install.sh
* spef


* python 3.9
* yaml
* pygments
* jinja2



* `pip install pyyaml`
* `pip install Pygments`
* `pip install jinja2`

* treba vlozit ncurses style do pygments
pygments_dir=`python -c 'import pygments as _; print(_.__path__[0])'`
cp src/ncurses.py $pygments_dir/styles/





* `docker build -f Dockerfile -t test .`

sudo mkdir /sys/fs/cgroup/systemd
sudo mount -t cgroup -o none,name=systemd cgroup /sys/fs/cgroup/systemd


Warning:
* The curses package is part of the Python standard library, however, the Windows version of Python doesn't include the curses module. If you're using Windows, you have to run: `pip install windows-curses`


### features
# GLOBAL
* delete --> confirm
# FILE
* state of file: saved / unsaved
* mode: edit / manage
# BROWS
* quick view: on / off





# ################################################################33
Help:


F1          'show_help': SHOW_HELP,
F10         'exit_program': EXIT_PROGRAM,
TAB         'change_focus': CHANGE_FOCUS,
RESIZE      'resize_win': RESIZE_WIN,
SLASH   'filter': FILTER,

CTRL O      'bash_switch': BASH_SWITCH,

UP          'cursor_up': CURSOR_UP,
DOWN        'cursor_down': CURSOR_DOWN,
LEFT        'cursor_left': CURSOR_LEFT,
RIGHT       'cursor_right': CURSOR_RIGHT,

DELETE      'delete': DELETE_CHAR,
BACKSPACE   'backspace': BACKSPACE_CHAR,

************** USER INPUT **************

ESC         'exit_user_input': EXIT_USER_INPUT
ENTER       'save_input': SAVE_INPUT,
ASCII       'print_char': PRINT_CHAR,
CTRL LEFT   'move_left': MOVE_LEFT,
CTRL RIGHT  'move_right': MOVE_RIGHT}

************** MENU **************

ESC         'exit_menu': EXIT_MENU,
ENTER       'save_option': SAVE_OPTION,
1..9A..Z    'select_by_idx': SELECT_BY_IDX,
F3          'select_option': SELECT_OPTION,
CTRL LEFT   'move_left': MOVE_LEFT,
CTRL RIGHT  'move_right': MOVE_RIGHT}


************** FILTER **************

F4          'aggregate': AGGREGATE_FILTER,
F8          'remove_filter': REMOVE_FILTER,
ESC         'exit_filter': EXIT_FILTER,
ASCII       'print_char': PRINT_CHAR,
ENTER       'save_filter': SAVE_FILTER}

************** NOTES **************

F2          'edit_note': EDIT_NOTE,
0           'add_custom_note': ADD_CUSTOM_NOTE,
F9          'add_typical_note': ADD_TYPICAL_NOTE,
F5          'go_to_note': GO_TO_NOTE,
F6          'save_as_typical_note': SAVE_AS_TYPICAL_NOTE,
F8          'delete_note': DELETE_NOTE,
ESC         'exit_notes': EXIT_NOTES,

************** TAGS **************

F2          'edit_tag': EDIT_TAG,
F3          'add_tag': ADD_TAG,
F8          'delete_tag': DELETE_TAG,
F4          'open_tag_file': OPEN_TAG_FILE,

************** FILE **************
 
F2          'save_file': SAVE_FILE,
F3          'show_or_hide_tags': SHOW_OR_HIDE_TAGS,
F4          'show_supported_data': SHOW_SUPPORTED_DATA,
F5          'show_or_hide_line_numbers': SHOW_OR_HIDE_LINE_NUMBERS,
F6          'show_or_hide_note_highlight': SHOW_OR_HIDE_NOTE_HIGHLIGHT,
F7          'open_note_management': OPEN_NOTE_MANAGEMENT,
F8          'reload_file_from_last_save': RELOAD_FILE_FROM_LAST_SAVE,
F9          'show_typical_notes': SHOW_TYPICAL_NOTES,
a           'set_edit_file_mode': SET_EDIT_FILE_MODE,
ESC         'set_manage_file_mode': SET_MANAGE_FILE_MODE,
ENTER       'print_new_line': PRINT_NEW_LINE,
ASCII       'print_char': PRINT_CHAR,
0           'add_custom_note': ADD_CUSTOM_NOTE,
1..9A..Z    'add_typical_note': ADD_TYPICAL_NOTE,
CTRL UP     'go_to_prev_note': GO_TO_PREV_NOTE,
CTRL DOWN   'go_to_next_note': GO_TO_NEXT_NOTE,
CTRL R      'reload_original_buff': RELOAD_ORIGINAL_BUFF}


************** BROWS **************
F2          'open_menu': OPEN_MENU,
F3          'quick_view_on_off': QUICK_VIEW_ON_OFF,
F4          'open_file': OPEN_FILE,
F5          'go_to_tags': GO_TO_TAGS,
F6          'show_or_hide_cached_files': SHOW_OR_HIDE_CACHED_FILES,
F8          'delete_file': DELETE_FILE,


