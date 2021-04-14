def get_move_cursor_up_as_string(lines: int):
    if lines > 0:
        return '\033[' + str(lines) + 'A'
    else:
        return ""


class TerminalMovements:
    ERASE_LINE_FORWARD = '\033[0K'
    ERASE_LINE = '\033[2K'
    ERASE_SCREEN_FORWARD = '\033[0J'


class TerminalColors:
    BG_GREEN = '\033[42m'

    BLACK = '\033[30m'
    DARK_GREY = '\033[90m'
    LIGHT_GREEN = '\033[92m'
    LIGHT_YELLOW = '\033[93m'
    LIGHT_RED = '\033[91m'
    LIGHT_BLUE = '\033[34m'
    DEFAULT = '\033[39m'
    BG_DEFAULT = '\033[49m'
