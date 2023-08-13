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
from pkscreener.classes.ColorText import colorText
from pkscreener.classes.MenuOptions import menu, menus


# This Class manages user menu choices
class choices:
    level0MenuChoice = None
    level1MenuChoice = None
    level2MenuChoice = None
    level3MenuChoice = None
    level4MenuChoice = None

    def __init__(self):
        self.selectedChoices = 10
        self.menuLevel = 0
        self.menu = None

    def getChoice(self):
        choice = input(colorText.BOLD + colorText.FAIL + "[+] Select option:")
        print(colorText.END, "")
        return choice

    def renderChoices(self):
        m = menus()
