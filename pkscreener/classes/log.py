# -*- coding: utf-8 -*-
"""
    The MIT License (MIT)

    Copyright (c) 2023 pkjmesra

    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in all
    copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
    SOFTWARE.

"""
import inspect
import logging
import os
import sys
import tempfile
import time
import warnings

# from inspect import getcallargs, getfullargspec
from collections import OrderedDict
from functools import wraps

try:
    from collections.abc import Iterable
except ImportError:
    from collections import Iterable

from itertools import *

__all__ = [
    "redForegroundText",
    "greenForegroundText",
    "line_break",
    "clear_screen",
    "set_cursor",
    "setup_custom_logger",
    "default_logger",
    "log_to",
    "tracelog",
    "suppress_stdout_stderr",
]
__trace__ = False
__filter__ = None
__DEBUG__ = False


class colors:
    """Colors class:
    Reset all colors with colors.reset
    Two subclasses fg for foreground and bg for background.
    Use as colors.subclass.colorname.
    i.e. colors.fg.red or colors.bg.green
    Also, the generic bold, disable, underline, reverse, strikethrough,
    and invisible work with the main class
    i.e. colors.bold
    """

    reset = "\033[0m"
    bold = "\033[01m"
    disable = "\033[02m"
    underline = "\033[04m"
    reverse = "\033[07m"
    strikethrough = "\033[09m"
    invisible = "\033[08m"

    class fg:
        black = "\033[30m"
        red = "\033[31m"
        green = "\033[32m"
        orange = "\033[33m"
        blue = "\033[34m"
        purple = "\033[35m"
        cyan = "\033[36m"
        lightgrey = "\033[37m"
        darkgrey = "\033[90m"
        lightred = "\033[91m"
        lightgreen = "\033[92m"
        yellow = "\033[93m"
        lightblue = "\033[94m"
        pink = "\033[95m"
        lightcyan = "\033[96m"

    class bg:
        black = "\033[40m"
        red = "\033[41m"
        green = "\033[42m"
        orange = "\033[43m"
        blue = "\033[44m"
        purple = "\033[45m"
        cyan = "\033[46m"
        lightgrey = "\033[47m"


class filterlogger:
    def __init__(self, logger=None):
        self._logger = logger

    @property
    def logger(self):
        return self._logger

    @property
    def level(self):
        return self.logger.level

    @property
    def isDebugging(self):
        return self.level == logging.DEBUG

    @level.setter
    def level(self, level):
        self.logger.setLevel(level)

    @staticmethod
    def getlogger(logger):
        global __filter__
        # if __filter__ is not None:
        return filterlogger(logger=logger)
        # else:
        #   return logger

    def flush(self):
        for h in self.logger.handlers:
            h.flush()

    def addHandlers(self, log_file_path=None, levelname=logging.NOTSET):
        if log_file_path is None:
            log_file_path = os.path.join(tempfile.gettempdir(), "pkscreener-logs.txt")
        trace_formatter = logging.Formatter(
            fmt="\n%(asctime)s - %(name)s - %(levelname)s - %(filename)s - %(module)s - %(funcName)s - %(lineno)d\n%(message)s\n"
        )

        consolehandler = None
        filehandler = logging.FileHandler(log_file_path)
        filehandler.setFormatter(trace_formatter)
        filehandler.setLevel(levelname)
        self.logger.addHandler(filehandler)
        if levelname == logging.DEBUG:
            consolehandler = logging.StreamHandler()
            consolehandler.setFormatter(trace_formatter)
            consolehandler.setLevel(levelname)
            self.logger.addHandler(consolehandler)
            global __DEBUG__
            __DEBUG__ = True
            self.logger.debug("Logging started. Filter:{}".format(filter))
        return consolehandler, filehandler

    def debug(self, e, exc_info=False):
        global __filter__
        __DEBUG__ = self.level == logging.DEBUG
        if not self.level == logging.DEBUG:
            return
        line = str(e)
        try:
            frame = inspect.stack()[1]
            # filename = (frame[0].f_code.co_filename).rsplit('/', 1)[1]
            components = str(frame).split(",")
            filename = components[4].split("/")[-1].split("\\")[-1]
            line = "{} - {} - {}\n{}".format(
                filename, components[5], components[6], line
            )
        except Exception as e:
            pass
        if __DEBUG__:
            if __filter__ is None:
                self.logger.debug(line, exc_info=exc_info)
                return
            if __filter__ in line.upper():
                self.logger.debug(line, exc_info=exc_info)
        elif self.level == logging.INFO:
            self.info(line)

    def info(self, line):
        global __filter__
        __DEBUG__ = self.level == logging.DEBUG
        if not self.logger.level == logging.DEBUG:
            return
        frame = inspect.stack()[1]
        # filename = (frame[0].f_code.co_filename).rsplit('/', 1)[1]
        components = str(frame).split(",")
        filename = components[4].split("/")[-1].split("\\")[-1]
        line = "{} - {} - {}\n{}".format(filename, components[5], components[6], line)
        if __filter__ is None:
            self.logger.info(line)
            return
        if __filter__ in line.upper():
            self.logger.info(line)

    def warn(self, line):
        global __filter__
        if __filter__ is None:
            self.logger.warn(line)
            return

        if __filter__ in line.upper():
            self.logger.warn(line)

    def error(self, line):
        self.logger.error(line)

    def setLevel(self, level):
        self.logger.setLevel(level)

    def critical(self, line):
        self.logger.critical(line)

    def addHandler(self, hdl):
        self.logger.addHandler(hdl)

    def removeHandler(self, hdl):
        self.logger.removeHandler(hdl)

    logging.shutdown()


def setup_custom_logger(
    name,
    levelname=logging.DEBUG,
    trace=False,
    log_file_path="pkscreener-logs.txt",
    filter=None,
):
    # console_info_formatter = logging.Formatter(fmt='\n%(levelname)s - %(filename)s(%(funcName)s - %(lineno)d)\n%(message)s\n')
    global __trace__
    __trace__ = trace

    global __filter__
    __filter__ = filter if filter is None else filter.upper()
    logger = logging.getLogger(name)
    logger.setLevel(levelname)

    consolehandler, filehandler = default_logger().addHandlers(
        log_file_path=log_file_path, levelname=levelname
    )
    if levelname == logging.DEBUG:
        global __DEBUG__
        __DEBUG__ = True
    if trace:
        tracelogger = logging.getLogger("pkscreener_file_logger")
        tracelogger.setLevel(levelname)
        tracelogger.addHandler(consolehandler)
        if levelname == logging.DEBUG:
            tracelogger.addHandler(filehandler)
        logger.debug("Tracing started")
    # Turn off pystan warnings
    warnings.simplefilter("ignore", DeprecationWarning)
    warnings.simplefilter("ignore", FutureWarning)

    return logger


def default_logger():
    return filterlogger.getlogger(logging.getLogger("pkscreener"))


def file_logger():
    return filterlogger.getlogger(logging.getLogger("pkscreener_file_logger"))


def trace_log(line):
    global __trace__
    if default_logger().level == logging.DEBUG:
        default_logger().info(line)
    else:
        file_logger().info(line)


def flatten(l):
    """Flatten a list (or other iterable) recursively"""
    for el in l:
        if isinstance(el, Iterable) and not isinstance(el, str):
            for sub in flatten(el):
                yield sub
        else:
            yield el


def getargnames(func):
    """Return an iterator over all arg names, including nested arg names and varargs.
    Goes in the order of the functions argspec, with varargs and
    keyword args last if present."""
    (
        args,
        varargs,
        varkw,
        defaults,
        kwonlyargs,
        kwonlydefaults,
        annotations,
    ) = inspect.getfullargspec(func)
    return chain(flatten(args), filter(None, [varargs, varkw]))


def getcallargs_ordered(func, *args, **kwargs):
    """Return an OrderedDict of all arguments to a function.
    Items are ordered by the function's argspec."""
    argdict = inspect.getcallargs(func, *args, **kwargs)
    return OrderedDict((name, argdict[name]) for name in getargnames(func))


def describe_call(func, *args, **kwargs):
    yield "Calling %s with args:" % func.__name__
    for argname, argvalue in getcallargs_ordered(func, *args, **kwargs).items():
        yield "\t%s = %s" % (argname, repr(argvalue))


def log_to(logger_func):
    """A decorator to log every call to function (function name and arg values).
    logger_func should be a function that accepts a string and logs it
    somewhere. The default is logging.debug.
    If logger_func is None, then the resulting decorator does nothing.
    This is much more efficient than providing a no-op logger
    function: @log_to(lambda x: None).
    """
    if logger_func is not None:

        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                global __DEBUG__
                if __DEBUG__:
                    frame = inspect.stack()[1]
                    components = str(frame).split(",")
                    filename = components[
                        4
                    ]  # (frame[0].f_code.co_filename).rsplit('/', 1)[1]
                    func_description = "{} - {} - {}".format(
                        filename, components[5], components[6]
                    )
                    description = func_description
                    for line in describe_call(func, *args, **kwargs):
                        description = description + "\n" + line
                    logger_func(description)
                    startTime = time.time()
                    ret_val = func(*args, **kwargs)
                    time_spent = time.time() - startTime
                    logger_func(
                        "\n%s called (%s): %.3f  (TIME_TAKEN)"
                        % (func_description, func.__name__, time_spent)
                    )
                    return ret_val
                else:
                    return func(*args, **kwargs)

            return wrapper

    else:
        decorator = lambda x: x
    return decorator


tracelog = log_to(trace_log)

# def timeit(method):
#     def timed(*args, **kw):
#         ts = time.time()
#         result = method(*args, **kw)
#         te = time.time()
#         if 'log_time' in kw:
#             name = kw.get('log_name', method.__name__.upper())
#             kw['log_time'][name] = int((te - ts) * 1000)
#         else:
#             print ('%r  %2.2f ms' % \
#                   (method.__name__, (te - ts) * 1000))
#         return result
#     return timed


class suppress_stdout_stderr(object):
    """
    A context manager for doing a "deep suppression" of stdout and stderr in
    Python, i.e. will suppress all print, even if the print originates in a
    compiled C/Fortran sub-function.
       This will not suppress raised exceptions, since exceptions are printed
    to stderr just before a script exits, and after the context manager has
    exited (at least, I think that is why it lets exceptions through).

    """

    def __init__(self):
        # Open a pair of null files
        self.null_fds = [os.open(os.devnull, os.O_RDWR) for x in range(2)]
        # Save the actual stdout (1) and stderr (2) file descriptors.
        self.save_fds = [os.dup(1), os.dup(2)]

    def __enter__(self):
        # Assign the null pointers to stdout and stderr.
        os.dup2(self.null_fds[0], 1)
        os.dup2(self.null_fds[1], 2)

    def __exit__(self, *_):
        # Re-assign the real stdout/stderr back to (1) and (2)
        os.dup2(self.save_fds[0], 1)
        os.dup2(self.save_fds[1], 2)
        # Close the null files
        for fd in self.null_fds + self.save_fds:
            os.close(fd)


def line_break():
    print("-" * 25)


def clear_screen():
    os.system("clear" if os.name == "posix" else "cls")


def set_cursor():
    sys.stdout.write("\033[F")
    sys.stdout.write("\033[K")


def redForegroundText(text):
    print("\n" + colors.fg.red + text + colors.reset)


def greenForegroundText(text):
    print("\n" + colors.fg.green + text + colors.reset)
