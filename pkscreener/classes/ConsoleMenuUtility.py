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

from PKDevTools.classes.OutputControls import OutputControls
from PKDevTools.classes.ColorText import colorText
from PKDevTools.classes.log import default_logger

from pkscreener.classes import ConfigManager
from pkscreener.classes.ConsoleUtility import PKConsoleTools
from pkscreener.classes.MenuOptions import menus

# Class for managing misc console menu utility methods
class PKConsoleMenuTools:
    configManager = ConfigManager.tools()
    configManager.getConfig(ConfigManager.parser)

    # Prompt for asking RSI
    def promptRSIValues():
        PKConsoleTools.clearScreen(forceTop=True)
        try:
            minRSI, maxRSI = int(
                input(
                    colorText.WARN
                    + "\n  [+] Enter Min RSI value (Default=55): "
                    + colorText.END
                ) or 55
            ), int(
                input(
                    colorText.WARN
                    + "  [+] Enter Max RSI value (Default=68): "
                    + colorText.END
                ) or "68"
            )
            if (
                (minRSI >= 0 and minRSI <= 100)
                and (maxRSI >= 0 and maxRSI <= 100)
                and (minRSI <= maxRSI)
            ):
                return (minRSI, maxRSI)
            raise ValueError
        except ValueError as e:  # pragma: no cover
            default_logger().debug(e, exc_info=True)
            return (0, 0)

    # Prompt for asking CCI
    def promptCCIValues(minCCI=None, maxCCI=None):
        PKConsoleTools.clearScreen(forceTop=True)
        if minCCI is not None and maxCCI is not None:
            return minCCI, maxCCI
        try:
            minCCI, maxCCI = int(
                input(
                    colorText.WARN
                    + "\n  [+] Enter Min CCI value (Default=110): "
                    + colorText.END
                ) or "110"
            ), int(
                input(
                    colorText.WARN
                    + "  [+] Enter Max CCI value (Default=300): "
                    + colorText.END
                ) or "300"
            )
            if minCCI <= maxCCI:
                return (minCCI, maxCCI)
            raise ValueError
        except ValueError as e:  # pragma: no cover
            default_logger().debug(e, exc_info=True)
            return (-100, 100)

    # Prompt for asking Volume ratio
    def promptVolumeMultiplier(volumeRatio=None):
        PKConsoleTools.clearScreen(forceTop=True)
        if volumeRatio is not None:
            return volumeRatio
        try:
            volumeRatio = float(
                input(
                    colorText.WARN
                    + "\n  [+] Enter Min Volume ratio value (Default = 2.5): "
                    + colorText.END
                ) or "2.5"
            )
            if volumeRatio > 0:
                return volumeRatio
            raise ValueError
        except ValueError as e:  # pragma: no cover
            default_logger().debug(e, exc_info=True)
            return 2

    def promptMenus(menu):
        PKConsoleTools.clearScreen(forceTop=True)
        m = menus()
        m.level = menu.level if menu is not None else 0
        return m.renderForMenu(menu)

    def promptChartPatternSubMenu(menu,respChartPattern):
        PKConsoleTools.clearScreen(forceTop=True)
        m3 = menus()
        m3.renderForMenu(menu,asList=True)
        lMenu =  m3.find(str(respChartPattern))
        maLength = PKConsoleMenuTools.promptSubMenuOptions(lMenu,defaultOption= "4" if respChartPattern == 3 else "1" )
        return maLength
    
    # Prompt for submenu options
    def promptSubMenuOptions(menu=None, defaultOption="1"):
        try:
            PKConsoleMenuTools.promptMenus(menu=menu)
            resp = int(
                input(
                    colorText.WARN
                    + """  [+] Select Option:"""
                    + colorText.END
                ) or defaultOption
            )
            if resp >= 0 and resp <= 10:
                return resp
            raise ValueError
        except ValueError as e:  # pragma: no cover
            default_logger().debug(e, exc_info=True)
            OutputControls().takeUserInput(
                colorText.FAIL
                + "\n  [+] Invalid Option Selected. Press <Enter> to try again..."
                + colorText.END
            )
            return None

    # Prompt for Reversal screening
    def promptReversalScreening(menu=None):
        try:
            PKConsoleMenuTools.promptMenus(menu=menu)
            resp = int(
                input(
                    colorText.WARN
                    + """  [+] Select Option:"""
                    + colorText.END
                ) or "3"
            )
            if resp >= 0 and resp <= 10:
                if resp == 4:
                    try:
                        defaultMALength = 9 if PKConsoleMenuTools.configManager.duration.endswith("m") else 50
                        maLength = int(
                            input(
                                colorText.WARN
                                + f"\n  [+] Enter MA Length (E.g. 9,10,20,50 or 200) (Default={defaultMALength}): "
                                + colorText.END
                            ) or str(defaultMALength)
                        )
                        return resp, maLength
                    except ValueError as e:  # pragma: no cover
                        default_logger().debug(e, exc_info=True)
                        OutputControls().printOutput(
                            colorText.FAIL
                            + "\n[!] Invalid Input! MA Length should be single integer value!\n"
                            + colorText.END
                        )
                        raise ValueError
                elif resp == 6:
                    try:
                        maLength = int(
                            input(
                                colorText.WARN
                                + "\n  [+] Enter NR timeframe [Integer Number] (E.g. 4, 7, etc.) (Default=4): "
                                + colorText.END
                            ) or "4"
                        )
                        return resp, maLength
                    except ValueError as e:  # pragma: no cover
                        default_logger().debug(e, exc_info=True)
                        OutputControls().printOutput(
                            colorText.FAIL
                            + "\n[!] Invalid Input! NR timeframe should be single integer value!\n"
                            + colorText.END
                        )
                        raise ValueError
                elif resp in [7,10]:
                    m3 = menus()
                    m3.renderForMenu(menu,asList=True)
                    lMenu =  m3.find(str(resp))
                    return resp, PKConsoleMenuTools.promptSubMenuOptions(lMenu)
                return resp, None
            raise ValueError
        except ValueError as e:  # pragma: no cover
            default_logger().debug(e, exc_info=True)
            OutputControls().takeUserInput(
                colorText.FAIL
                + "\n  [+] Invalid Option Selected. Press <Enter> to try again..."
                + colorText.END
            )
            return None, None

    # Prompt for Reversal screening
    def promptChartPatterns(menu=None):
        try:
            PKConsoleMenuTools.promptMenus(menu=menu)
            resp = int(
                input(
                    colorText.WARN
                    + """  [+] Select Option:"""
                    + colorText.END
                ) or "3"
            )
            if resp == 1 or resp == 2:
                candles = int(
                    input(
                        colorText.WARN
                        + "\n  [+] How many candles (TimeFrame) to look back Inside Bar formation? (Default=3): "
                        + colorText.END
                    ) or "3"
                )
                return (resp, candles)
            if resp == 3:
                percent = float(
                    input(
                        colorText.WARN
                        + "\n  [+] Enter Percentage within which all MA/EMAs should be (Ideal: 0.1-2%)? (Default=0.8): "
                        + colorText.END
                    ) or "0.8"
                )
                return (resp, percent / 100.0)
            if resp >= 0 and resp <= 9:
                return resp, 0
            raise ValueError
        except ValueError as e:  # pragma: no cover
            default_logger().debug(e, exc_info=True)
            OutputControls().takeUserInput(
                colorText.FAIL
                + "\n  [+] Invalid Option Selected. Press <Enter> to try again..."
                + colorText.END
            )
            return (None, None)
