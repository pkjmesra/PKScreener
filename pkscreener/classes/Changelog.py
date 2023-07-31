'''
 *  Project             :   Screenipy
 *  Author              :   Pranjal Joshi
 *  Created             :   28/04/2021
 *  Description         :   Class for maintaining changelog
'''

from pkscreener.classes.ColorText import colorText
from pkscreener.classes.OtaUpdater import OTAUpdater

whatsNew = OTAUpdater.showWhatsNew()
changelog = colorText.BOLD + '[ChangeLog]\n' + colorText.END + colorText.BLUE + whatsNew + '''

--- END ---
''' + colorText.END
