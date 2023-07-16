'''
 *  Project             :   Screenipy
 *  Author              :   Pranjal Joshi
 *  Created             :   28/04/2021
 *  Description         :   Class for maintaining changelog
'''

from classes.ColorText import colorText

changelog = colorText.BOLD + '[ChangeLog]\n' + colorText.END + colorText.BLUE + '''
[0.01]
1. First release

--- END ---
''' + colorText.END
