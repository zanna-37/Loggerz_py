from __future__ import annotations

import sys
from collections import deque
from datetime import datetime
from enum import IntEnum
from multiprocessing import Lock

from loggerz.singleton.Singleton import Singleton
from loggerz.terminal_utils import TerminalUtils
from loggerz.terminal_utils.TerminalUtils import TerminalColors, TerminalMovements


class State(IntEnum):
    OFF = 0
    ON = 1
    AUTO = 2


def erase_next_n_lines_and_rewind_as_string(erase_next_n_lines):
    output = ""
    for i in range(erase_next_n_lines):
        output += TerminalMovements.ERASE_LINE_FORWARD
        output += "\n"
    output += TerminalUtils.get_move_cursor_up_as_string(erase_next_n_lines)
    return output


class Loggerz(metaclass=Singleton):
    def __init__(self):
        self.__mutex = Lock()
        self.__target_log_level = LogLevel.INFO
        self.__long_prefix = False
        self.__print_timestamp = True
        self.__originator_width = 10

        # Perform a check to disable some features by default if they are not supported
        self.__colors_enabled: bool = None
        self.__terminal_movements_enabled: bool = None
        self.set_color_mode(State.AUTO)
        self.set_terminal_movements_mode(State.AUTO)

        # Volatile lines
        self.max_ephemeral_messages = 4
        self.ephemeral_logs = deque()
        self.current_sticky_message = None

    def cleanup(self):
        output = self.__delete_volatile_lines_as_string()
        output += TerminalMovements.ERASE_SCREEN_FORWARD

        self.__do_print(output)

    def blank_line(self, log_level: LogLevel):
        if self.__should_be_logged(log_level):
            self.__prepare_and_print("\n")

    def log(self, log_level: LogLevel, originator: str, message: str, sticky=False):
        if self.__should_be_logged(log_level):
            self.__prepare_and_print(self.__do_log, (log_level, originator, message, sticky))

    def __do_log(self, log_level: LogLevel, originator: str, message: str, sticky: bool) -> str:
        output = ""
        now = datetime.now().strftime('%H:%M:%S.%f')[:-3]
        new_log = Loggerz.Logz(log_level, originator, message, now, sticky)

        if sticky:
            self.current_sticky_message = new_log  # Do not print but store for later
        elif new_log.log_level == LogLevel.EPHEMERAL:
            self.ephemeral_logs.append(new_log)  # Do not print but store for later
            while len(self.ephemeral_logs) > self.max_ephemeral_messages:  # Trim old ephemeral logs
                self.ephemeral_logs.popleft()
        else:
            self.ephemeral_logs.clear()  # Any new non-ephemeral log removes all the previous ephemerals
            output += self.__build_log(new_log)  # To be printed

        return output

    def remove_sticky(self):
        self.__prepare_and_print(self.__do_remove_sticky)

    def __do_remove_sticky(self):
        self.current_sticky_message = None

    def __should_be_logged(self, log_level: LogLevel) -> bool:
        return log_level >= self.target_log_level

    def __prepare_and_print(self, fun_to_call_or_output, args=None):
        output = ""
        output += self.__delete_volatile_lines_as_string()

        if callable(fun_to_call_or_output):
            result = fun_to_call_or_output() if args is None else fun_to_call_or_output(*args)  # TODO change me
            if result is not None:
                output += result
        else:
            output += fun_to_call_or_output

        output += self.__write_volatile_lines_as_string()

        self.__do_print(output)

    def __do_print(self, output: str):
        self.__mutex.acquire()
        print(output, end="")
        self.__mutex.release()

    def __delete_volatile_lines_as_string(self) -> str:
        output = ""
        if self.__terminal_movements_enabled:
            erase_next_n_lines = 0

            # Ephemeral logs
            for logger_message in self.ephemeral_logs:
                erase_next_n_lines += 1
                for i in range(1, logger_message.get_number_of_lines()):  # Account for multiline
                    erase_next_n_lines += 1

            # Sticky log
            if self.current_sticky_message is not None:
                erase_next_n_lines += 1
                for i in range(1, self.current_sticky_message.get_number_of_lines()):
                    erase_next_n_lines += 1

            output = erase_next_n_lines_and_rewind_as_string(erase_next_n_lines)

        return output

    def __write_volatile_lines_as_string(self) -> str:
        output = ""
        if self.__terminal_movements_enabled:
            rewind_lines = 0

            # Ephemeral logs
            for log in self.ephemeral_logs:
                output += self.__build_log(log)
                rewind_lines += log.get_number_of_lines()

            # Sticky log
            if self.current_sticky_message is not None:
                output += self.__build_log(self.current_sticky_message)
                rewind_lines += self.current_sticky_message.get_number_of_lines()

            output += TerminalUtils.get_move_cursor_up_as_string(rewind_lines)

        return output

    def __build_log(self, log: Logz) -> str:
        output = ""
        prefix_symbol = ""
        prefix_info = ""

        # Prefix
        if not log.sticky:  # Don't print the prefix when sticky
            prefix_symbol += "[" + self.__get_log_prefix_as_string(log.log_level) + "]"

            if self.__print_timestamp:
                prefix_info += " "
                prefix_info += log.timestamp

            prefix_info += " ["
            prefix_info += log.originator.ljust(self.__originator_width, " ")
            prefix_info += "] "

        # Message
        message = self.__add_pad_after_endline(log.message, len(prefix_symbol) + len(prefix_info), log.sticky)
        if message.count('\n') > 0:
            message = self.__re_add_color_string_after_endline(message, log.log_level, log.sticky)

        # All together
        if log.sticky:
            output += "\n"  # Always put a blank before a sticky
        output += self.__get_color_string_for(log.log_level, log.sticky, True)
        output += prefix_symbol
        output += self.__get_color_reset_string_for(log.log_level, log.sticky, True)
        output += prefix_info
        output += message
        output += self.__get_color_reset_string_for(log.log_level, log.sticky, False)
        output += "\n"

        return output

    def set_target_log_level(self, target_log_level: LogLevel):
        if target_log_level >= LogLevel.EPHEMERAL:
            self.target_log_level = target_log_level

    def set_long_prefix(self, long_prefix: bool):
        self.long_prefix = long_prefix

    def set_originator_width(self, originator_width: int):
        self.originator_width = originator_width

    def set_max_ephemeral_messages(self, max_ephemeral_messages: int):
        self.max_ephemeral_messages = max_ephemeral_messages

    def set_terminal_movements_mode(self, terminal_movements_mode: State):
        if terminal_movements_mode == State.ON:
            self.__terminal_movements_enabled = True
        elif terminal_movements_mode == State.OFF:
            self.__terminal_movements_enabled = False
        elif terminal_movements_mode == State.AUTO:
            self.__terminal_movements_enabled = sys.stdout.isatty()

    def set_color_mode(self, color_mode: State):
        if color_mode == State.ON:
            self.__colors_enabled = True
        elif color_mode == State.OFF:
            self.__colors_enabled = False
        elif color_mode == State.AUTO:
            self.__colors_enabled = sys.stdout.isatty()

    def set_print_timestamp(self, print_timestamp: bool):
        self.__print_timestamp = print_timestamp

    def __get_log_prefix_as_string(self, log_level) -> str:
        if log_level == LogLevel.EPHEMERAL:
            return "EPHEMER" if self.__long_prefix else "_"
        elif log_level == LogLevel.DEBUG:
            return "DEBUG  " if self.__long_prefix else "|"
        elif log_level == LogLevel.VERBOSE:
            return "VERBOSE" if self.__long_prefix else ":"
        elif log_level == LogLevel.INFO:
            return "INFO   " if self.__long_prefix else "."
        elif log_level == LogLevel.TITLE:
            return "TITLE  " if self.__long_prefix else "#"
        elif log_level == LogLevel.SUCCESS:
            return "SUCCESS" if self.__long_prefix else "+"
        elif log_level == LogLevel.WARNING:
            return "WARNING" if self.__long_prefix else "!"
        elif log_level == LogLevel.ERROR:
            return "ERROR  " if self.__long_prefix else "-"
        elif log_level == LogLevel.FATAL:
            return "FATAL  " if self.__long_prefix else "x"
        else:
            return "UNKNOWN" if self.__long_prefix else "?"

    def __add_pad_after_endline(self, message: str, pad_lenght: int, sticky: bool) -> str:
        if not sticky:
            pos = 0

            pos = message.find('\n', pos)
            while pos >= 0:
                pos += 1  # skip the \n
                message = message[:pos] + "⤷ ".rjust(pad_lenght, " ") + message[pos:]
                pos += pad_lenght  # skip the pad
                pos = message.find('\n', pos)

        return message

    def __get_color_string_for(self, log_level: LogLevel, sticky: bool, before_prefix: bool):
        if not self.__colors_enabled:
            return ""
        else:
            if sticky:
                return TerminalColors.BG_GREEN + TerminalColors.BLACK

            if log_level == LogLevel.EPHEMERAL:
                return TerminalColors.LIGHT_BLUE
            elif log_level == LogLevel.DEBUG:
                return TerminalColors.DARK_GREY
            elif log_level == LogLevel.VERBOSE:
                return TerminalColors.DARK_GREY if before_prefix else ""
            elif log_level == LogLevel.INFO:
                return "" if before_prefix else ""  # Don't have color
            elif log_level == LogLevel.TITLE:
                return TerminalColors.LIGHT_YELLOW
            elif log_level == LogLevel.SUCCESS:
                return TerminalColors.LIGHT_GREEN if before_prefix else ""
            elif log_level == LogLevel.WARNING:
                return TerminalColors.LIGHT_YELLOW if before_prefix else ""
            elif log_level == LogLevel.ERROR:
                return TerminalColors.LIGHT_RED if before_prefix else ""
            elif log_level == LogLevel.FATAL:
                return TerminalColors.LIGHT_RED

    def __get_color_reset_string_for(self, log_level: LogLevel, sticky: bool, before_message: bool):
        if not self.__colors_enabled:
            return ""
        else:
            if sticky:
                return "" if before_message else TerminalMovements.ERASE_LINE_FORWARD + TerminalColors.BG_DEFAULT + TerminalColors.DEFAULT

            if log_level == LogLevel.EPHEMERAL:
                return "" if before_message else TerminalColors.DEFAULT
            elif log_level == LogLevel.DEBUG:
                return "" if before_message else TerminalColors.DEFAULT
            elif log_level == LogLevel.VERBOSE:
                return TerminalColors.DEFAULT if before_message else ""
            elif log_level == LogLevel.INFO:
                return "" if before_message else ""  # Don't have color
            elif log_level == LogLevel.TITLE:
                return "" if before_message else TerminalColors.DEFAULT
            elif log_level == LogLevel.SUCCESS:
                return TerminalColors.DEFAULT if before_message else ""
            elif log_level == LogLevel.WARNING:
                return TerminalColors.DEFAULT if before_message else ""
            elif log_level == LogLevel.ERROR:
                return TerminalColors.DEFAULT if before_message else ""
            elif log_level == LogLevel.FATAL:
                return "" if before_message else TerminalColors.DEFAULT

    def __re_add_color_string_after_endline(self, message: str, log_level: LogLevel, sticky: bool) -> str:
        pos = 0

        pos = message.find('\n', pos)
        while pos >= 0:
            color_string = self.__get_color_reset_string_for(log_level, sticky, False)
            message = message[:pos] + color_string + message[pos:]  # remove color before \n
            pos += len(color_string) + 1  # skip the color_string and the \n

            color_string = self.__get_color_string_for(log_level, sticky, False)
            message = message[:pos] + color_string + message[pos:]  # renew color after \n
            pos += len(color_string)  # skip the color_string

            pos = message.find('\n', pos)

        return message

    class Logz():
        def __init__(self, log_level: LogLevel, originator: str, message: str, timestamp: str, sticky: bool):
            self.log_level = log_level
            self.originator = originator
            self.message = message
            self.timestamp = timestamp
            self.sticky = sticky

            self.__number_of_lines = None

        def get_number_of_lines(self):
            if self.__number_of_lines is None:
                self.__number_of_lines = self.message.count('\n') + 1  # (endlines in the message) + (final \n)
                if self.sticky:
                    self.__number_of_lines += 1  # a sticky is always preceded by a blank line

            return self.__number_of_lines


class LogLevel(IntEnum):
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
