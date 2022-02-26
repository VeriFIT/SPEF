
from pygments import highlight
from pygments import lexers
from pygments.formatter import Formatter

from utils.logger import *

""" ======================= SYNTAX HIGHLIGHTER ========================= """

# https://pygments.org/docs/formatterdevelopment/

class CursesFormatter(Formatter):
    def __init__(self, **options):
        Formatter.__init__(self, **options)
        self.styles = {}

        for token, style in self.style:
            col_number = ''
            """ get color number from style['color'] (ex: #000045 --> 45) """
            if style['color']:
                full_col = '%s' % style['color']
                col_number = full_col[-2:] # only last two numbers
            self.styles[token] = col_number

    def format(self, tokensource, outfile):
        lastval = ''
        lasttype = None

        """ create list of tuples with style and text of tokens """
        tokens = []
        for ttype, value in tokensource:
            while ttype not in self.styles:
                ttype = ttype.parent
            if ttype == lasttype:
                lastval += value
            else:
                if lastval:
                    tokens.append((self.styles[lasttype], lastval))
                lastval = value
                lasttype = ttype
        if lastval:
            tokens.append((self.styles[lasttype], lastval))

        """ token list correction """
        same_style_text = ''
        last_style = None
        if tokens != []:
            style, text = tokens.pop(0)
            if style == '':
                style = "00"
            same_style_text = text
            last_style = style

        while tokens:
            style, text = tokens.pop(0)
            if style == '':
                style = "00"
            if style == last_style: # same style
                same_style_text += text
            else: # new style
                outfile.write(str(last_style)+"|"+str(same_style_text)+'\n')
                last_style = style
                same_style_text = text
    
        if same_style_text:
            outfile.write(str(last_style)+"|"+str(same_style_text)+'\n')


def parse_code(file_name, code):
    try:
        lexer = lexers.get_lexer_for_filename(file_name, stripnl=False)
        curses_format = CursesFormatter(style='ncurses')

        text = highlight(code, lexer, curses_format)
        raw_tokens = text.splitlines()
        raw_tokens = raw_tokens[:-1] # remove last new line


        """ parse string tokens to list of tuples (style, text) """
        last_style = ""
        parsed_tokens = []
        while raw_tokens:
            token = raw_tokens.pop(0)
            parts = token.split("|",1)
            if len(parts) == 2:
                style, text = parts
                last_style = style
                parsed_tokens.append((int(style), text))
            else:
                parsed_tokens.append((int(last_style), '\n'+str(token)))

        # log(str(parsed_tokens))
        """ split tokens to separate lines """
        result = []
        for token in parsed_tokens:
            style, text = token
            text_lines = text.splitlines(True) # keep separator (new line)
            for text_line in text_lines:
                result.append((style, text_line))

        return result

    except Exception as err:
        log("get syntax highlight for code | "+str(err))
        return None
