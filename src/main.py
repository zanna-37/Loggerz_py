import sys
from time import sleep

from src.Loggerz.Loggerz import Loggerz

LogLevel = Loggerz.LogLevel

if __name__ == '__main__':

    if not sys.stdout.isatty():
        print("This terminal do not support colors and cursor movement!")
        print("Some features will not be available unless forcefully enabled")

    log = Loggerz()
    log.set_target_log_level(Loggerz.LogLevel.EPHEMERAL)
    # log.set_enable_terminal_movements(False)

    log.blank_line(LogLevel.FATAL)
    log.log(LogLevel.TITLE, "main", "NORMAL BEHAVIOR")
    log.log(LogLevel.DEBUG, "main-norm", "This is a DEBUG log")
    log.log(LogLevel.VERBOSE, "main-norm", "This is a VERBOSE log")
    log.log(LogLevel.INFO, "main-norm", "This is a INFO log")
    log.log(LogLevel.SUCCESS, "main-norm", "This is a SUCCESS log")
    log.log(LogLevel.WARNING, "main-norm", "This is a WARNING log")
    log.log(LogLevel.ERROR, "main-norm", "This is a ERROR log")
    log.log(LogLevel.FATAL, "main-norm", "This is a FATAL log")
    sleep(2)

    log.blank_line(LogLevel.FATAL)
    log.log(LogLevel.TITLE, "main", "GO MULTILINE\nEVEN IN THE TITLES")
    log.log(LogLevel.SUCCESS, "main-multi", "This is\na multiline log!\nEnjoy!")
    sleep(2)

    log.blank_line(LogLevel.FATAL)
    log.set_long_prefix(True)
    log.log(LogLevel.TITLE, "main", "USE LONG SYNTAX")
    log.log(LogLevel.DEBUG, "main-long", "This is a DEBUG log")
    log.log(LogLevel.VERBOSE, "main-long", "This is a VERBOSE log")
    log.log(LogLevel.INFO, "main-long", "This is a INFO log")
    log.log(LogLevel.SUCCESS, "main-long", "This is a SUCCESS log")
    log.log(LogLevel.WARNING, "main-long", "This is a WARNING log")
    log.log(LogLevel.ERROR, "main-long", "This is a ERROR log")
    log.log(LogLevel.FATAL, "main-long", "This is a FATAL log")
    log.set_long_prefix(False)
    sleep(2)

    log.set_color_mode(False)
    log.blank_line(LogLevel.FATAL)
    log.log(LogLevel.TITLE, "main", "NO COLORS")
    log.log(LogLevel.DEBUG, "main-norm", "This is a DEBUG log")
    log.log(LogLevel.VERBOSE, "main-norm", "This is a VERBOSE log")
    log.log(LogLevel.INFO, "main-norm", "This is a INFO log")
    log.log(LogLevel.SUCCESS, "main-norm", "This is a SUCCESS log")
    log.log(LogLevel.WARNING, "main-norm", "This is a WARNING log")
    log.log(LogLevel.ERROR, "main-norm", "This is a ERROR log")
    log.log(LogLevel.FATAL, "main-norm", "This is a FATAL log")
    log.set_color_mode(True)
    sleep(2)

    log.blank_line(LogLevel.FATAL)
    log.log(LogLevel.TITLE, "main", "A STICKY LOG")
    log.log(LogLevel.INFO, "main-long", "Progress bar example...")
    PROGRESS_BAR_MAX = 50
    for i in range(PROGRESS_BAR_MAX + 1):
        sleep(7 / PROGRESS_BAR_MAX)
        progress_bar = "[" + ">".rjust(i, "-").ljust(PROGRESS_BAR_MAX, " ") + "]"
        log.log(LogLevel.INFO, "main-sticky", progress_bar, True)
        if i == PROGRESS_BAR_MAX / 2:
            log.log(LogLevel.INFO, "main-long", "50% done...")
    log.log(LogLevel.INFO, "main-long", "100% done!")
    sleep(2)
    log.remove_sticky()

    log.blank_line(LogLevel.FATAL)
    log.log(LogLevel.TITLE, "main", "EPHEMERAL LOGS")
    log.log(LogLevel.INFO, "main-eph", "This log will stay")
    log.log(LogLevel.INFO, "main-eph", "The max ephemeral messages is 4 by default, but can be changed")
    log.log(LogLevel.EPHEMERAL, "main-eph", "ephemeral 1")
    sleep(1)
    log.log(LogLevel.EPHEMERAL, "main-eph", "ephemeral 2")
    sleep(1)
    log.log(LogLevel.EPHEMERAL, "main-eph", "ephemeral 3")
    sleep(1)
    log.log(LogLevel.EPHEMERAL, "main-eph", "ephemeral 4")
    sleep(1)
    log.log(LogLevel.EPHEMERAL, "main-eph", "ephemeral 5")
    sleep(1)
    log.log(LogLevel.EPHEMERAL, "main-eph", "ephemeral 6")
    sleep(1)
    log.log(LogLevel.EPHEMERAL, "main-eph", "ephemeral 7")
    sleep(1)
    log.log(LogLevel.EPHEMERAL, "main-eph", "ephemeral 8")
    log.log(LogLevel.INFO, "", "We can also have a sticky present!\nAnd it can be multiline too!!!", True)
    sleep(1)
    log.log(LogLevel.EPHEMERAL, "main-eph", "ephemeral 9")
    sleep(1)
    log.log(LogLevel.EPHEMERAL, "main-eph", "ephemeral 10")
    sleep(1)
    log.log(LogLevel.EPHEMERAL, "main-eph", "ephemeral 11")
    sleep(1)
    log.log(LogLevel.EPHEMERAL, "main-eph", "ephemeral 12")
    sleep(1)
    log.log(LogLevel.EPHEMERAL, "main-eph", "ephemeral 13")
    sleep(1)
    log.log(LogLevel.EPHEMERAL, "main-eph", "ephemeral 14")
    sleep(1)
    log.log(LogLevel.EPHEMERAL, "main-eph", "ephemeral 15")

    sleep(1)
    log.log(LogLevel.INFO, "main-eph", "A new log squashes the ephemerals")
    sleep(2)

    log.blank_line(LogLevel.FATAL)
    log.log(LogLevel.TITLE, "main", "THE END")

    log.cleanup()
