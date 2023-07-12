from enum import Enum
from classes.ColorText import colorText

level0MenuDict = {'X': 'Scanners', 'S': 'Strategies', 'B': 'Backtests'}
level0MenuDictAdditional = {'E': 'Edit user configuration',
                            'Y': 'View your user configuration',
                            'U': 'Check for software update',
                            'H': 'Help / About Developer',
                            'Z': 'Exit (Ctrl + C)'
                            }
level1_X_MenuDict = {'W': 'Screen stocks from my own Watchlist',
                  'N': 'Nifty Prediction using Artifical Intelligence (Use for Gap-Up/Gap-Down/BTST/STBT)',
                  'E': 'Live Index Scan : 5 EMA for Intraday',
                  '0': 'Screen stocks by the stock names (NSE Stock Code)',
                  '1': 'Nifty 50          ',
                  '2': 'Nifty Next 50     ',
                  '3': 'Nifty 100         ',
                  '4': 'Nifty 200         ',
                  '5': 'Nifty 500         ',
                  '6': 'Nifty Smallcap 50 ',
                  '7': 'Nifty Smallcap 100',
                  '8': 'Nifty Smallcap 250',
                  '9': 'Nifty Midcap 50   ',
                  '10': 'Nifty Midcap 100',
                  '11': 'Nifty Midcap 150',
                  '12': 'Nifty (All Stocks)',
                  '13': 'Newly Listed (IPOs in last 2 Year)        ',
                  '14': 'F&O Stocks Only',
                  'M': 'Back to the Top/Main menu',
                  'Z': 'Exit (Ctrl + C)'
                  }
level2_X_MenuDict = {'0': 'Full Screening (Shows Technical Parameters without any criterion)',
                  '1': 'Probable Breakouts              ',
                  '2': 'Recent Breakouts & Volumes',
                  '3': 'Consolidating stocks            ',
                  '4': 'Lowest Volume in last \'N\'-days (Early Breakout Detection)',
                  '5': 'RSI screening                   ',
                  '6': 'Reversal Signals',
                  '7': 'Stocks making Chart Patterns    ',
                  '8': 'CCI outside of the given range',
                  '9': 'Volume gainers                  ',
                  '10': 'Closing at least 2% up since last 3 days',
                  '11': 'Short term bullish stocks       ',
                  '12': '15 Minute Price & Volume breakout',
                  '13': 'Bullish RSI & MACD Intraday     ',
                  '14': 'NR4 Daily Today',
                  '15': '52 week low breakout            ',
                  '16': '10 days low breakout',
                  '17': '52 week high breakout           ',
                  '18': 'Bullish Aroon Crossover',
                  '19': 'MACD Historgram x below 0       ',
                  '20': 'RSI entering bullish territory',
                  '21': 'Bearish CCI crossover           ',
                  '22': 'RSI crosses above 30 and price higher than psar',
                  '23': 'Intraday Momentum Build-up      ',
                  '24': 'Extremely bullish daily close',
                  '25': 'Rising RSI                      ',
                  '26': 'Dividend Yield',
                  '42': 'Show Last Screened Results',
                  'M': 'Back to the Top/Main menu',
                  'Z': 'Exit (Ctrl + C)'}
level3_X_Reversal_MenuDict = {'1': 'Buy Signals (Bullish Reversal)',
                          '2':'Sell Signals (Bearish Reversal)',
                          '3': 'Momentum Gainers (Rising Bullish Momentum)',
                          '4': 'Reversal at Moving Average (Bullish Reversal)',
                          '5': 'Volume Spread Analysis (Bullish VSA Reversal)',
                          '6': 'Narrow Range (NRx) Reversal',
                          '0': 'Cancel'
                          }
level3_X_ChartPattern_MenuDict = {'1': 'Bullish Inside Bar (Flag) Pattern',
                              '2':'Bearish Inside Bar (Flag) Pattern',
                              '3': 'The Confluence (50 & 200 MA/EMA)',
                              '4': 'VCP (Experimental)',
                              '5': 'Buying at Trendline (Ideal for Swing/Mid/Long term)',
                              '6': 'Narrow Range (NRx) Reversal',
                              '0': 'Cancel'
                              }

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
        self.menuDict = {}
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

    def renderForMenu(self, selectedMenu=None):
        if selectedMenu is None and self.level == 0:
            # Top level Application Main menu
            return
        elif selectedMenu is not None:
            if self.level == 1:
                # sub-menu of the top level main selected menu
                return
            elif self.level == 1:
                # next levelsub-menu of the selected sub-menu
                return
        
    def find(self, key=None):
        if key is not None:
            try:
                return self.menuDict[key]
            except:
                return None
        return None

    # def renderLevel0Menus(self):
    #     print(colorText.BOLD + colorText.WARN +
    #         '[+] Select a menu option:' + colorText.END)
    #     toggleText = 'T > Toggle between long-term (Default)' + colorText.WARN + ' [Current]'+ colorText.END + ' and Intraday user configuration\n' if not configManager.isIntradayConfig() else 'T > Toggle between long-term (Default) and Intraday' + colorText.WARN + ' [Current]' +  colorText.END + ' user configuration'
    #     print(colorText.BOLD + Utility.tools.promptMenus(level0MenuDict) + '''

    #  ''' + toggleText + Utility.tools.promptMenus(level0MenuDictAdditional,['E','U']) + '''

    # Enter your choice >  (default is ''' + colorText.WARN + 'X > Scanners) ''' + colorText.END
    #         )
    