import sys
from collections import deque
from datetime import datetime
from enum import IntEnum
from multiprocessing import Lock

from src.Loggerz.Singleton import Singleton
from src.TerminalUtils import TerminalUtils
from src.TerminalUtils.TerminalUtils import TerminalColors, TerminalMovements


class LoggerzLevel(IntEnum):
    EPHEMERAL = 0
    """
    This should be used as additional and non-critical output that is meant to last for short time and then overwritten
    """

    DEBUG = 1
    """
    Use this only for debug logs. Link entering/exiting methods or state
    which low level operation are being performed.
    """

    VERBOSE = 2
    """
    Use it for extra information. For example log a state change, or when the
    program perform high level operation.
    """

    INFO = 3
    """
    Use it to inform a potential user about what is going on. Use it only to
    provide information targeted to a non-developer audience.
    """

    TITLE = 4
    """
    This should be used to print a title-like log
    """

    SUCCESS = 5
    """
    Use it when something has succeeded and it is worth inform the user.
    """

    WARNING = 6
    """
    Use it to signal an unexpected situation that should not occur but does
    not prevent the program to continue.
    """

    ERROR = 7
    """
    Use it to signal that an error has occurred and the program will try to
    continue anyway, so the output might be not what the user expect.
    """

    FATAL = 8
    """
    Use it to signal an unrecoverable error that makes the program stop.
    """


class LoggerzMessage():
    def __init__(self, log_level: LoggerzLevel, originator: str, message: str, timestamp: str, sticky: bool):
        self.log_level = log_level
        self.originator = originator
        self.message = message
        self.timestamp = timestamp
        self.sticky = sticky

        self.number_of_lines = None

    def get_number_of_lines(self):
        if self.number_of_lines is None:
            self.number_of_lines = self.message.count('\n') + 1  # (endlines in the message) + (final \n)
            if self.sticky:
                self.number_of_lines += 1  # a sticky is always preceded by a blank line

        return self.number_of_lines


class Loggerz(metaclass=Singleton):
    def __init__(self):
        self.mutex = Lock()
        self.target_log_level = LoggerzLevel.INFO
        self.long_prefix = False
        self.print_timestamp = True
        self.originator_width = 10

        isatty = sys.stdout.isatty()
        self.enable_color = isatty
        self.enable_terminal_movements = isatty

        self.max_ephemeral_messages = 4
        self.current_ephemeral_messages = deque()
        self.current_sticky_message = None

    def blank_line(self, log_level: LoggerzLevel):
        self.log(log_level, None, None)

    def log(self, log_level: LoggerzLevel, originator: str, message: str, sticky=False):
        if log_level >= self.target_log_level:

            output = ""
            now = datetime.now().strftime('%H:%M:%S.%f')[:-3]
            loggerz_message = LoggerzMessage(log_level, originator, message, now, sticky)

            # build delete temporary lines
            output += self.__build_delete_tmp_lines()

            if sticky:
                self.current_sticky_message = loggerz_message
            elif loggerz_message.log_level == LoggerzLevel.EPHEMERAL:
                self.current_ephemeral_messages.append(loggerz_message)
                while len(self.current_ephemeral_messages) > self.max_ephemeral_messages:
                    self.current_ephemeral_messages.popleft()
            elif originator is None or message is None:
                output += "\n"
            else:
                self.current_ephemeral_messages.clear()
                output += self.__build_log(loggerz_message)

            # build rewrite temporary lines
            output += self.__build_rewrite_tmp_lines()

            self.mutex.acquire()
            print(output, end="")
            self.mutex.release()

    def __build_delete_tmp_lines(self) -> str:
        if not self.enable_terminal_movements:
            return ""
        else:
            erase_forward = ""
            rewind_lines = 0
            # ephemerals
            for logger_message in self.current_ephemeral_messages:
                erase_forward += TerminalMovements.ERASE_LINE_FORWARD
                erase_forward += TerminalUtils.move_cursor_down(1)
                rewind_lines += 1
                for i in range(1, logger_message.get_number_of_lines()):
                    erase_forward += TerminalMovements.ERASE_LINE_FORWARD
                    erase_forward += TerminalUtils.move_cursor_down(1)
                    rewind_lines += 1
            # sticky
            if self.current_sticky_message is not None:
                erase_forward += TerminalMovements.ERASE_LINE_FORWARD
                erase_forward += TerminalUtils.move_cursor_down(1)
                rewind_lines += 1
                for i in range(1, self.current_sticky_message.get_number_of_lines()):
                    erase_forward += TerminalMovements.ERASE_LINE_FORWARD
                    erase_forward += TerminalUtils.move_cursor_down(1)
                    rewind_lines += 1

            return erase_forward + TerminalUtils.move_cursor_up(rewind_lines)

    def __build_rewrite_tmp_lines(self) -> str:
        if not self.enable_terminal_movements:
            return ""
        else:
            output = ""
            rewind_lines = 0
            # ephemerals
            for logger_message in self.current_ephemeral_messages:
                output += self.__build_log(logger_message)
                rewind_lines += logger_message.get_number_of_lines()
            # sticky
            if self.current_sticky_message is not None:
                output += self.__build_log(self.current_sticky_message)
                rewind_lines += self.current_sticky_message.get_number_of_lines()

            output += TerminalUtils.move_cursor_up(rewind_lines)

            return output

    def __build_log(self, loggerz_message: LoggerzMessage) -> str:
        output = ""
        prefix_symbol = ""
        prefix_info = ""

        if not loggerz_message.sticky:
            # prefix
            prefix_symbol += "[" + self.__get_log_prefix_as_string(loggerz_message.log_level) + "]"
            if self.print_timestamp:
                prefix_info += " "
                prefix_info += loggerz_message.timestamp
            prefix_info += " ["
            prefix_info += loggerz_message.originator.ljust(self.originator_width, " ")
            prefix_info += "] "

        # message
        message = self.__add_pad_after_endline(loggerz_message.message, len(prefix_symbol) + len(prefix_info),
                                               loggerz_message.sticky)
        if message.count('\n') > 0:
            message = self.__add_color_string_after_endline(message, loggerz_message.log_level, loggerz_message.sticky)

        # glue all together
        if loggerz_message.sticky:
            output += "\n"  # always put a blank before a sticky
        output += self.__get_color_string_for(loggerz_message.log_level, loggerz_message.sticky)
        output += prefix_symbol
        output += self.__get_color_reset_string_premessage_for(loggerz_message.log_level, loggerz_message.sticky)
        output += prefix_info
        output += message
        output += self.__get_color_reset_string_postmessage_for(loggerz_message.log_level, loggerz_message.sticky)
        output += "\n"

        return output

    def remove_sticky(self):
        output = self.__build_delete_tmp_lines()
        self.current_sticky_message = None
        output += self.__build_rewrite_tmp_lines()
        self.mutex.acquire()
        print(output, end="")
        self.mutex.release()

    def set_target_log_level(self, target_log_level: LoggerzLevel):
        if target_log_level >= LoggerzLevel.EPHEMERAL:
            self.target_log_level = target_log_level

    def set_long_prefix(self, long_prefix: bool):
        self.long_prefix = long_prefix

    def set_originator_width(self, originator_width: int):
        self.originator_width = originator_width

    def set_max_ephemeral_messages(self, max_ephemeral_messages: int):
        self.max_ephemeral_messages = max_ephemeral_messages

    def set_enable_terminal_movements(self, enable_terminal_movements: bool):
        self.enable_terminal_movements = enable_terminal_movements

    def set_enable_color(self, enable_color: bool):
        self.enable_color = enable_color

    def print_timestamp(self, print_timestamp: bool):
        self.print_timestamp = print_timestamp

    def __get_log_prefix_as_string(self, log_level) -> str:
        if log_level == LoggerzLevel.EPHEMERAL:
            return "EPHEMER" if self.long_prefix else "_"
        elif log_level == LoggerzLevel.DEBUG:
            return "DEBUG  " if self.long_prefix else "|"
        elif log_level == LoggerzLevel.VERBOSE:
            return "VERBOSE" if self.long_prefix else ":"
        elif log_level == LoggerzLevel.INFO:
            return "INFO   " if self.long_prefix else "."
        elif log_level == LoggerzLevel.TITLE:
            return "TITLE  " if self.long_prefix else "#"
        elif log_level == LoggerzLevel.SUCCESS:
            return "SUCCESS" if self.long_prefix else "+"
        elif log_level == LoggerzLevel.WARNING:
            return "WARNING" if self.long_prefix else "!"
        elif log_level == LoggerzLevel.ERROR:
            return "ERROR  " if self.long_prefix else "-"
        elif log_level == LoggerzLevel.FATAL:
            return "FATAL  " if self.long_prefix else "x"
        else:
            return "UNKNOWN" if self.long_prefix else "?"

    def __add_pad_after_endline(self, message: str, pad_lenght: int, sticky: bool) -> str:
        if not sticky:
            pos = 0

            pos = message.find('\n', pos)
            while pos >= 0:
                pos += 1  # skip the \n
                message = message[:pos] + "⤷ ".rjust(pad_lenght, " ") + message[pos:]
                pos += pad_lenght
                pos = message.find('\n', pos)

        return message

    def __get_color_string_for(self, log_level: LoggerzLevel, sticky: bool):
        if not self.enable_color:
            return ""
        else:
            if sticky:
                return TerminalColors.BG_GREEN + TerminalColors.BLACK

            if log_level == LoggerzLevel.EPHEMERAL:
                return TerminalColors.LIGHT_BLUE
            elif log_level == LoggerzLevel.DEBUG:
                return TerminalColors.DARK_GREY
            elif log_level == LoggerzLevel.VERBOSE:
                return TerminalColors.DARK_GREY
            elif log_level == LoggerzLevel.INFO:
                return ""  # do not have color
            elif log_level == LoggerzLevel.TITLE:
                return TerminalColors.LIGHT_YELLOW
            elif log_level == LoggerzLevel.SUCCESS:
                return TerminalColors.LIGHT_GREEN
            elif log_level == LoggerzLevel.WARNING:
                return TerminalColors.LIGHT_YELLOW
            elif log_level == LoggerzLevel.ERROR:
                return TerminalColors.LIGHT_RED
            elif log_level == LoggerzLevel.FATAL:
                return TerminalColors.LIGHT_RED

    def __get_color_inmessage_string_for(self, log_level: LoggerzLevel, sticky: bool):
        if not self.enable_color:
            return ""
        else:
            if sticky:
                return TerminalColors.BG_GREEN + TerminalColors.BLACK

            if log_level == LoggerzLevel.EPHEMERAL:
                return TerminalColors.LIGHT_BLUE
            elif log_level == LoggerzLevel.DEBUG:
                return TerminalColors.DARK_GREY
            elif log_level == LoggerzLevel.VERBOSE:
                return ""  # color has already been reset before the message
            elif log_level == LoggerzLevel.INFO:
                return ""  # do not have color
            elif log_level == LoggerzLevel.TITLE:
                return TerminalColors.LIGHT_YELLOW
            elif log_level == LoggerzLevel.SUCCESS:
                return ""  # color has already been reset before the message
            elif log_level == LoggerzLevel.WARNING:
                return ""  # color has already been reset before the message
            elif log_level == LoggerzLevel.ERROR:
                return ""  # color has already been reset before the message
            elif log_level == LoggerzLevel.FATAL:
                return TerminalColors.LIGHT_RED

    def __get_color_reset_string_premessage_for(self, log_level: LoggerzLevel, sticky: bool):
        if not self.enable_color:
            return ""
        else:
            if sticky:
                return ""  # extend color to the whole message

            if log_level == LoggerzLevel.EPHEMERAL:
                return ""  # extend color to the whole message
            elif log_level == LoggerzLevel.DEBUG:
                return ""  # extend color to the whole message
            elif log_level == LoggerzLevel.VERBOSE:
                return TerminalColors.DEFAULT
            elif log_level == LoggerzLevel.INFO:
                return ""  # do not have color
            elif log_level == LoggerzLevel.TITLE:
                return ""  # extend color to the whole message
            elif log_level == LoggerzLevel.SUCCESS:
                return TerminalColors.DEFAULT
            elif log_level == LoggerzLevel.WARNING:
                return TerminalColors.DEFAULT
            elif log_level == LoggerzLevel.ERROR:
                return TerminalColors.DEFAULT
            elif log_level == LoggerzLevel.FATAL:
                return ""  # extend color to the whole message

    def __add_color_string_after_endline(self, message: str, log_level: LoggerzLevel, sticky: bool) -> str:
        pos = 0

        pos = message.find('\n', pos)
        while pos >= 0:
            to_add = self.__get_color_reset_string_postmessage_for(log_level, sticky)
            message = message[:pos] + to_add + message[pos:]  # renew color after \n
            pos += len(to_add) + 1  # skip to_add and the \n

            to_add = self.__get_color_inmessage_string_for(log_level, sticky)
            message = message[:pos] + to_add + message[pos:]  # renew color after \n
            pos += len(to_add)  # skip to_add

            pos = message.find('\n', pos)

        return message

    def __get_color_reset_string_postmessage_for(self, log_level: LoggerzLevel, sticky: bool):
        if not self.enable_color:
            return ""
        else:
            if sticky:
                return TerminalMovements.ERASE_LINE_FORWARD + TerminalColors.BG_DEFAULT + TerminalColors.DEFAULT

            if log_level == LoggerzLevel.EPHEMERAL:
                return TerminalColors.DEFAULT
            elif log_level == LoggerzLevel.DEBUG:
                return TerminalColors.DEFAULT
            elif log_level == LoggerzLevel.VERBOSE:
                return ""  # color has already been reset before the message
            elif log_level == LoggerzLevel.INFO:
                return TerminalColors.DEFAULT
            elif log_level == LoggerzLevel.TITLE:
                return TerminalColors.DEFAULT
            elif log_level == LoggerzLevel.SUCCESS:
                return ""  # color has already been reset before the message
            elif log_level == LoggerzLevel.WARNING:
                return ""  # color has already been reset before the message
            elif log_level == LoggerzLevel.ERROR:
                return ""  # color has already been reset before the message
            elif log_level == LoggerzLevel.FATAL:
                return TerminalColors.DEFAULT

    def cleanup(self):
        output = self.__build_delete_tmp_lines()
        output += TerminalMovements.ERASE_SCREEN_FORWARD

        self.mutex.acquire()
        print(output, end="")
        self.mutex.release()
