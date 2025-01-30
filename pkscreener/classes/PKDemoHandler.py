#!/usr/bin/python3
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
import sys
from PKDevTools.classes.OutputControls import OutputControls
from PKDevTools.classes.ColorText import colorText

class PKDemoHandler:

    @classmethod
    def demoForMenu(self,menu):
        # Default: View Various PKScreener Subscription Options
        asciinemaLink = "https://asciinema.org/a/EHYIQBbCP8CAJIAFjWaFGkEEX"
        match menu.menuKey:
            case "F":
                # F > Find a stock in scanners
                asciinemaLink = "https://asciinema.org/a/7TA8H8pq94YmTqsrVvtLCpPel"
            case "M":
                asciinemaLink = "https://asciinema.org/a/NKBXhxc2iWbpxcll35JqwfpuQ"
            case _: # P_1_1
                asciinemaLink = "https://asciinema.org/a/b31Tp78QLSzZcxcxCzH7Rljog"
        
        OutputControls().printOutput(f"\n[+] {colorText.GREEN}Please check this out in your browser:{colorText.END}\n\n[+] {colorText.FAIL}\x1b[97m\x1b]8;;{asciinemaLink}\x1b\\{asciinemaLink}\x1b]8;;\x1b\\\x1b[0m{colorText.END}\n")
        input("Press any key to exit...")
        sys.exit(0)