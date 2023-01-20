import csv
import curses
import curses.ascii


from spef.controls.control import get_function_for_key
from spef.controls.functions import *
from spef.modules.bash import Bash_action
from spef.utils.printing import *
from spef.utils.screens import *
from spef.utils.logger import *
from spef.utils.loading import load_user_logs_from_file


# return number of lines needed to print given buffer
# space (number) = length of space between key and line
def calculate_total_len_lines(user_logs, space, max_cols, start_at=None, stop_at=None):
    total_len = 0
    for idx, item in enumerate(user_logs):
        if start_at is not None and idx < start_at:
            continue
        if stop_at is not None and idx >= stop_at:
            return total_len

        date, m_type, message = item
        date, m_type, message = str(date), str(m_type).lower(), str(message).strip()
        key = f" {date} | {m_type} | "
        free_space = max_cols - len(key) - space
        line = message
        if len(line) > free_space:
            sublines = parse_line_into_sublines(line, free_space)
            total_len += len(sublines)
        else:
            total_len += 1
    return total_len


def logs_viewing(stdscr, env):
    curses.curs_set(0)
    screen, win = env.get_screen_for_current_mode()

    max_cols = win.end_x - win.begin_x - 1
    max_rows = win.end_y - win.begin_y
    logs_len = calculate_total_len_lines(env.user_logs, 0, max_cols)

    rewrite_all_wins(env)

    while True:
        """print user logs"""
        show_logs(env)

        key = stdscr.getch()

        try:
            function = get_function_for_key(env, key)
            if function is not None:
                logs_len, env, exit_program = run_function(
                    stdscr, env, function, key, logs_len
                )
                if exit_program:
                    return env
        except Exception as err:
            log("logs view | " + str(err) + " | " + str(traceback.format_exc()))
            env.set_exit_mode()
            return env


def run_function(stdscr, env, fce, key, logs_len):
    screen, win = env.get_screen_for_current_mode()

    max_cols = win.end_x - win.begin_x - 1
    max_rows = win.end_y - win.begin_y

    # ==================== EXIT PROGRAM ====================
    if fce == EXIT_PROGRAM:
        env.set_exit_mode()
        return logs_len, env, True
    # ======================= BASH =======================
    elif fce == BASH_SWITCH:
        hex_key = "{0:x}".format(key)
        env.bash_action = Bash_action()
        env.bash_action.set_exit_key(("0" if len(hex_key) % 2 else "") + str(hex_key))
        env.bash_active = True
        return logs_len, env, True
    # ======================= FOCUS =======================
    elif fce == CHANGE_FOCUS:
        env.switch_to_next_mode()
        return logs_len, env, True
    # ======================= RESIZE =======================
    elif fce == RESIZE_WIN:
        env = resize_all(stdscr, env)
        screen, win = env.get_screen_for_current_mode()
        rewrite_all_wins(env)
        max_cols = win.end_x - win.begin_x - 1
        max_rows = win.end_y - win.begin_y
        logs_len = calculate_total_len_lines(env.user_logs, 0, max_cols)
    # ======================= ARROWS =======================
    elif fce == CURSOR_UP:
        if win.row_shift > 0:
            win.row_shift -= 1
    elif fce == CURSOR_DOWN:
        shifted = calculate_total_len_lines(
            env.user_logs, 0, max_cols, stop_at=win.row_shift
        )
        if logs_len >= shifted + max_rows:
            win.row_shift += 1
    # ===================== OPEN FILE ======================
    elif fce == OPEN_FILE:
        user_logs_file = os.path.join(DATA_DIR, USER_LOGS_FILE)
        if os.path.isfile(user_logs_file):
            env.set_file_to_open(user_logs_file)
            env.set_view_mode()
            return logs_len, env, True
    # =================== CLEAR USER LOG ===================
    elif fce == CLEAR_LOG:
        user_logs_file = os.path.join(DATA_DIR, USER_LOGS_FILE)
        with open(user_logs_file, "w+"):
            pass
        env.user_logs = load_user_logs_from_file()
        env.user_logs_printed = []
        env.user_logs_printed_shift = 0
        go_down_in_user_logs(env)
        env.windows.logs.reset()
        logs_len = calculate_total_len_lines(env.user_logs, 1, max_cols)

    env.update_win_for_current_mode(win)
    return logs_len, env, False


def add_to_user_logs(env, m_type, message):
    date = datetime.datetime.now().strftime("%d/%m/%y-%H:%M")

    if str(m_type).lower().strip() in ["e", "error"]:
        m_type = "ERROR  "
    elif str(m_type).lower().strip() in ["w", "warning"]:
        m_type = "WARNING"
    else:
        m_type = "INFO   "

    user_logs_file = os.path.join(DATA_DIR, USER_LOGS_FILE)
    with open(user_logs_file, "a") as f:
        csv_writer = csv.writer(
            f, delimiter="|", quotechar='"', quoting=csv.QUOTE_MINIMAL
        )
        csv_writer.writerow([date, m_type, message])

    env.user_logs.append((date, m_type, message))
    go_down_in_user_logs(env)
    show_logs(env)


def go_down_in_user_logs(env):
    while True:
        max_cols = env.windows.logs.end_x - env.windows.logs.begin_x - 1
        max_rows = env.windows.logs.end_y - env.windows.logs.begin_y
        row_shift = env.windows.logs.row_shift
        logs_len = calculate_total_len_lines(env.user_logs, 0, max_cols)
        shifted = calculate_total_len_lines(
            env.user_logs, 0, max_cols, stop_at=row_shift
        )
        if logs_len >= shifted + max_rows:
            env.windows.logs.row_shift += 1
        else:
            break
