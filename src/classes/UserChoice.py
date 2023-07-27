
from classes.MenuOptions import menu, menus
from classes.ColorText import colorText

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
        choice = input(colorText.BOLD + colorText.FAIL + '[+] Select option:')
        print(colorText.END, '')
        return choice

    def renderChoices(self):
        m = menus()
