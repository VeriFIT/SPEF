from pygments.style import Style
import pygments.token as token


"""
* style for ncurses (similar to visual code colors)
* color is represented by number of curses.color_pair defined in utils/coloring.py
"""


class NcursesStyle(Style):

    """mapping to ncurses colors defined in coloring.py file"""

    HL_PURPLE = "#000040"
    HL_BLUE = "#000041"
    HL_LIGHT_BLUE = "#000042"
    HL_YELLOW = "#000043"
    HL_CYAN = "#000044"
    HL_GREEN = "#000045"
    HL_PASTEL_GREEN = "#000046"
    HL_ORANGE = "#000047"
    HL_RED = "#000048"
    HL_OLIVE = "#000049"
    HL_PINK = "#000050"

    HL_NORMAL = "#000055"

    default_style = HL_NORMAL

    # https://svn.python.org/projects/external/Pygments-1.3.1/docs/build/tokens.html
    # fmt: off
    styles = {
        token.Comment: HL_GREEN,
        token.Comment.Preproc: HL_PURPLE,
        token.Comment.Special: HL_NORMAL,
        token.Keyword: HL_BLUE,
        # Keyword.Constant:          "",
        # Keyword.Declaration:       "", # var
        token.Keyword.Namespace: HL_PURPLE,  # import, package
        # Keyword.Pseudo:            "",
        # Keyword.Reserved:          "",
        # Keyword.Type:              "", # int, char
        token.Name: HL_NORMAL,
        token.Name.Attribute: HL_YELLOW,
        token.Name.Builtin: HL_LIGHT_BLUE,  # self, this
        # Name.Builtin.Pseudo:       "",
        token.Name.Class: HL_CYAN,
        token.Name.Constant: HL_BLUE,  # const
        token.Name.Decorator: HL_YELLOW,
        # Name.Entity:               HL_LIGHT_BLUE,
        token.Name.Exception: HL_CYAN,
        token.Name.Function: HL_YELLOW,
        # Name.Label:                "",
        # Name.Namespace:            HL_LIGHT_BLUE, # import path or name folowing the module/namespace keyword
        token.Name.Other: HL_YELLOW,
        token.Name.Tag: HL_PURPLE,
        token.Name.Variable: HL_LIGHT_BLUE,
        token.Number: HL_PASTEL_GREEN,  # HL_PINK
        token.Literal: HL_PASTEL_GREEN,  # HL_PINK
        token.Literal.Date: HL_ORANGE,
        token.String: HL_ORANGE,
        token.String.Escape: HL_PASTEL_GREEN,  # HL_PINK
        token.String.Interpol: HL_BLUE,
        token.Text: HL_NORMAL,
        token.Operator: HL_NORMAL,
        token.Operator.Word: HL_BLUE,
        token.Punctuation: HL_NORMAL,
        token.Error: HL_RED,
        token.Generic.Deleted: HL_PURPLE,
        token.Generic.Inserted: HL_YELLOW,
        token.Generic.Output: HL_BLUE,
        token.Generic.Prompt: HL_PURPLE,
        token.Generic.Subheading: HL_PURPLE,
    }
