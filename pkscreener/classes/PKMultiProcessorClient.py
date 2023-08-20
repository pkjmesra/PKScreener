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

import logging
import multiprocessing
import os
import sys
from queue import Empty

# usage: pkscreenercli.exe [-h] [-a ANSWERDEFAULT] [-c CRONINTERVAL] [-d] [-e] [-o OPTIONS] [-p] [-t] [-l] [-v]
# pkscreenercli.exe: error: unrecognized arguments: --multiprocessing-fork parent_pid=4620 pipe_handle=708
# https://github.com/pyinstaller/pyinstaller/wiki/Recipe-Multiprocessing
# Module multiprocessing is organized differently in Python 3.4+
try:
    # Python 3.4+
    if sys.platform.startswith("win"):
        import multiprocessing.popen_spawn_win32 as forking
    else:
        import multiprocessing.popen_fork as forking
except ImportError:
    print("Contact developer! Your platform does not support multiprocessing!")
    input("Exiting now...")
    sys.exit(0)


class PKMultiProcessorClient(multiprocessing.Process):
    def __init__(
        self,
        processorMethod,
        task_queue,
        result_queue,
        processingCounter,
        processingResultsCounter,
        objectDictionary,
        proxyServer,
        keyboardInterruptEvent,
        defaultLogger,
    ):
        multiprocessing.Process.__init__(self)
        self.multiprocessingForWindows()
        assert (
            processorMethod is not None
        ), "processorMethod argument must not be None. This is the meyhod that will do the processing."
        assert task_queue is not None, "task_queue argument must not be None."
        assert result_queue is not None, "result_queue argument must not be None."
        self.processorMethod = processorMethod
        self.task_queue = task_queue
        self.result_queue = result_queue
        # processingCounter and processingResultsCounter
        # are sunchronized counters that can be used within
        # processorMethod via hostRef.processingCounter
        # or hostRef.processingResultsCounter
        self.processingCounter = processingCounter
        self.processingResultsCounter = processingResultsCounter
        # A helper object dictionary that can contain anything
        # and can be accessed using hostRef.objectDictionary
        # within processorMethod
        self.objectDictionary = objectDictionary
        # A proxyServer that can contain proxyServer info
        # and can be accessed using hostRef.proxyServer
        # within processorMethod
        self.proxyServer = proxyServer
        # A logger that can contain logger reference
        # and can be accessed using hostRef.default_logger
        # within processorMethod
        self.default_logger = defaultLogger

        self.keyboardInterruptEvent = keyboardInterruptEvent
        if defaultLogger is not None:
            self.default_logger.info("StockConsumer initialized.")
        else:
            # Let's get the root logger by default
            self.default_logger = logging.getLogger(name=None)

    def run(self):
        try:
            while not self.keyboardInterruptEvent.is_set():
                try:
                    next_task = self.task_queue.get()
                    if next_task is not None:
                        # Inject a reference to this instance of the client
                        # so that the task can still get access back to it.
                        next_task = (*(next_task), self)
                except Empty as e:
                    self.default_logger.debug(e, exc_info=True)
                    continue
                if next_task is None:
                    self.default_logger.info("No next task in queue")
                    self.task_queue.task_done()
                    break
                answer = self.processorMethod(*(next_task))
                self.task_queue.task_done()
                self.default_logger.info(f"Task done. Result:{answer}")
                self.result_queue.put(answer)
        except Exception as e:
            self.default_logger.debug(e, exc_info=True)
            sys.exit(0)

    def multiprocessingForWindows(self):
        if sys.platform.startswith("win"):
            # First define a modified version of Popen.
            class _Popen(forking.Popen):
                def __init__(self, *args, **kw):
                    if hasattr(sys, "frozen"):
                        # We have to set original _MEIPASS2 value from sys._MEIPASS
                        # to get --onefile mode working.
                        os.putenv("_MEIPASS2", sys._MEIPASS)
                    try:
                        super(_Popen, self).__init__(*args, **kw)
                    finally:
                        if hasattr(sys, "frozen"):
                            # On some platforms (e.g. AIX) 'os.unsetenv()' is not
                            # available. In those cases we cannot delete the variable
                            # but only set it to the empty string. The bootloader
                            # can handle this case.
                            if hasattr(os, "unsetenv"):
                                os.unsetenv("_MEIPASS2")
                            else:
                                os.putenv("_MEIPASS2", "")

            # Second override 'Popen' class with our modified version.
            forking.Popen = _Popen
