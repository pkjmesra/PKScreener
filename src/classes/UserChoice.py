
from classes.MenuOptions import menu, menus

# This Class manages user menu choices
class choices:

    def __init__(self):
        self.selectedChoices = 10
        self.menuLevel = 0
        self.menu = None
    
    def getChoice(self):
        return input(f'[+] Select option:')

    def renderChoices(self):
        m = menus()
