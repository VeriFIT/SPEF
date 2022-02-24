import curses

from pygments.style import Style
from pygments.token import Keyword, Name, Comment, String, Error, Text, \
     Number, Operator, Generic, Whitespace, Punctuation, Other, Literal


"""
styles_dir = /home/naty/.local/lib/python3.9/site-packages/pygments/styles

cp curses.py /home/naty/.local/lib/python3.9/site-packages/pygments/styles/

"""


"""
* style for ncurses (similar to visual code colors)
* color is represented by number of curses.color_pair defined in coloring.py
"""
class CursesStyle(Style):
    default_style = ""

    HL_PURPLE = "#000040"
    HL_BLUE = "#000041"
    HL_LIGHT_BLUE = "#000042"
    HL_YELLOW = "#000043"
    HL_CYAN = "#000044"
    HL_GREEN = "#000045"
    HL_PASTEL_GREEN = "#000046"
    HL_ORANGE = "#000047"
    HL_RED = "#000048"

    styles = {
        Comment:                   HL_GREEN,

        Keyword:                   HL_BLUE,
        Keyword.Namespace:         HL_PURPLE,

        # Name:                      HL_LIGHT_GRAY,
        Name.Attribute:            HL_YELLOW,
        Name.Class:                HL_CYAN,
        Name.Constant:             HL_BLUE,
        Name.Decorator:            HL_YELLOW,
        Name.Exception:            HL_CYAN,
        Name.Function:             HL_YELLOW,
        Name.Other:                HL_YELLOW,
        Name.Tag:                  HL_PURPLE,
        Name.Variable:             HL_LIGHT_BLUE,

        Number:                    HL_PASTEL_GREEN,
        Literal:                   HL_PASTEL_GREEN,
        Literal.Date:              HL_ORANGE,
        String:                    HL_ORANGE,
        String.Escape:             HL_PASTEL_GREEN,
        # Text:                      HL_LIGHT_GRAY,

        # Operator:                  HL_LIGHT_GRAY,
        # Punctuation:               HL_LIGHT_GRAY,
        Error:                     HL_RED,

        Generic.Deleted:           HL_PURPLE,
        Generic.Inserted:          HL_YELLOW,
        Generic.Output:            HL_BLUE,
        Generic.Prompt:            HL_PURPLE,
        Generic.Subheading:        HL_GREEN,
    }
