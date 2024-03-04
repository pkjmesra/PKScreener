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
class PKTask:
    def __init__(self, taskName=None, long_running_fn=None, long_running_fn_args=None, progress_fn=None):
        if taskName is None or taskName == "":
            raise ValueError("taskName cannot be None or empty string!")
        if long_running_fn is None:
            raise ValueError("long_running_fn cannot be None!")
        self.taskName = taskName
        self.progressStatusDict = None
        self.taskId = 0
        self.progress = 0
        self.total = 0
        self.long_running_fn = long_running_fn
        self.long_running_fn_args = long_running_fn_args
        self.progress_fn = progress_fn
        self.resultsDict = None
        self.result = None
        self.userData = None