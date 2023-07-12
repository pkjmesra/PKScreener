from enum import Enum

class MenuRenderStyle(Enum):
    STANDALONE = 1
    TWO_PER_ROW = 2
    THREE_PER_ROW = 3

class menu:
    def __init__(self):
        self.menuKey = ''
        self.menuText = ''
        self.submenu = None
        self.level = 0
        self.isException = None
        self.hasLeftSibling = False

    def create(self, key, text, level=0, isException=False):
        self.menuKey = str(key)
        self.menuText = text
        self.level = level
        self.isException = isException
    
    def render(self):
        t = ''
        if self.isException:
            t = f'\n\n     {self.menuKey} > {self.menuText}'
        elif not self.menuKey.isnumeric():
            t = f'\n     {self.menuKey} > {self.menuText}'
        else:
            # 9 to adjust an extra space when 10 becomes a 2 digit number
            spaces = '     ' if int(self.menuKey) <= 9 else '    '
            if not self.hasLeftSibling:
                t = f'\n{spaces}{self.menuKey} > {self.menuText}'
            else:
                t = f'\t{self.menuKey} > {self.menuText}'
        return t

# This Class manages application menus
class menus:

    def __init__(self):
        self.level = 0
        self.menuDict = {}

    def fromDictionary(self, rawDictionary={}, 
                       renderStyle=MenuRenderStyle.STANDALONE, 
                       renderExceptionKeys=[]):
        tabLevel = 0
        for key in rawDictionary:
            m = menu()
            m.create(key, rawDictionary[key], level=self.level)
            if key in renderExceptionKeys:
                m.isException = True
            elif str(key).isnumeric():
                m.hasLeftSibling= False if tabLevel == 0 else True
                tabLevel = tabLevel + 1
                if tabLevel >= renderStyle:
                    tabLevel = 0
            self.menuDict[str(key)] = m
        return self
    
    def render(self):
        menuText = ''
        for k in self.menuDict.keys():
            m = self.menuDict[k]
            menuText = menuText + m.render()
        return menuText

    def find(self, key=None):
        if key is not None:
            try:
                return self.menuDict[key]
            except:
                return None
        return None

