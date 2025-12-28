"""
ExecuteOptionHandlers - Execute option processing for PKScreener

This module contains handlers for different execute options (3, 4, 5, 6, 7, etc.)
that were previously in the main() function in globals.py.
"""

from typing import Any, Dict, List, Optional, Tuple

from PKDevTools.classes.ColorText import colorText
from PKDevTools.classes.OutputControls import OutputControls
from PKDevTools.classes.log import default_logger

from pkscreener.classes import ConsoleMenuUtility
from pkscreener.classes.CandlePatterns import CandlePatterns


def handle_execute_option_3(userPassedArgs, configManager) -> int:
    """Handle execute option 3 - force evaluate all stocks"""
    userPassedArgs.maxdisplayresults = max(configManager.maxdisplayresults, 2000)
    return configManager.volumeRatio


def handle_execute_option_4(executeOption: int, options: List[str]) -> int:
    """Handle execute option 4 - days for lowest volume"""
    daysForLowestVolume = 30
    if len(options) >= 4:
        if str(options[3]).isnumeric():
            daysForLowestVolume = int(options[3])
        elif str(options[3]).upper() == "D":
            daysForLowestVolume = 30
    else:
        daysForLowestVolume = ConsoleMenuUtility.PKConsoleMenuTools.promptDaysForLowestVolume()
    return daysForLowestVolume


def handle_execute_option_5(
    options: List[str],
    userPassedArgs,
    m2
) -> Tuple[Optional[int], Optional[int]]:
    """Handle execute option 5 - RSI values"""
    selectedMenu = m2.find("5")
    minRSI = 0
    maxRSI = 100
    
    if len(options) >= 5:
        if str(options[3]).isnumeric():
            minRSI = int(options[3])
            maxRSI = int(options[4])
        elif str(options[3]).upper() == "D" or userPassedArgs.systemlaunched:
            minRSI = 60
            maxRSI = 75
    else:
        minRSI, maxRSI = ConsoleMenuUtility.PKConsoleMenuTools.promptRSIValues()
    
    if not minRSI and not maxRSI:
        OutputControls().printOutput(
            f"{colorText.FAIL}\n  [+] Error: Invalid values for RSI! "
            f"Values should be in range of 0 to 100. Please try again!{colorText.END}"
        )
        OutputControls().takeUserInput("Press <Enter> to continue...")
        return None, None
    
    return minRSI, maxRSI


def handle_execute_option_6(
    options: List[str],
    userPassedArgs,
    defaultAnswer,
    user,
    m2,
    selectedChoice: Dict[str, str]
) -> Tuple[Optional[int], Optional[int]]:
    """Handle execute option 6 - reversal screening"""
    selectedMenu = m2.find("6")
    reversalOption = None
    maLength = None
    
    if len(options) >= 4:
        reversalOption = int(options[3])
        if reversalOption in [4, 6, 7, 10]:
            if len(options) >= 5:
                if str(options[4]).isnumeric():
                    maLength = int(options[4])
                elif str(options[4]).upper() == "D" or userPassedArgs.systemlaunched:
                    maLength = 50 if reversalOption == 4 else (3 if reversalOption in [7] else (2 if reversalOption in [10] else 7))
            elif defaultAnswer == "Y" and user is not None:
                maLength = 50 if reversalOption == 4 else (3 if reversalOption == 7 else 7)
            else:
                reversalOption, maLength = ConsoleMenuUtility.PKConsoleMenuTools.promptReversalScreening(selectedMenu)
    else:
        reversalOption, maLength = ConsoleMenuUtility.PKConsoleMenuTools.promptReversalScreening(selectedMenu)
    
    if reversalOption is None or reversalOption == 0 or maLength == 0:
        return None, None
    
    selectedChoice["3"] = str(reversalOption)
    if str(reversalOption) in ["7", "10"]:
        selectedChoice["4"] = str(maLength)
    
    return reversalOption, maLength


def handle_execute_option_7(
    options: List[str],
    userPassedArgs,
    defaultAnswer,
    user,
    m0, m2,
    selectedChoice: Dict[str, str],
    configManager
) -> Tuple[Optional[int], Optional[float], Optional[int]]:
    """
    Handle execute option 7 - chart patterns.
    Returns (respChartPattern, insideBarToLookback, maLength) or (None, None, None) on failure
    """
    import pkscreener.classes.ConfigManager as ConfigManager
    
    selectedMenu = m2.find("7")
    maLength = 0
    respChartPattern = None
    insideBarToLookback = 7
    
    if len(options) >= 4:
        respChartPattern = int(options[3])
        selectedChoice["3"] = options[3]
        
        if respChartPattern in [1, 2, 3]:
            insideBarToLookback, maLength = _handle_chart_pattern_1_2_3(
                options, userPassedArgs, defaultAnswer, user, selectedMenu, respChartPattern, configManager, ConfigManager
            )
        elif respChartPattern in [0, 4, 5, 6, 7, 8, 9]:
            insideBarToLookback = 0
            if respChartPattern == 6 or respChartPattern == 9:
                maLength = _handle_chart_pattern_6_9(
                    options, userPassedArgs, defaultAnswer, user, selectedMenu, respChartPattern
                )
        else:
            respChartPattern, insideBarToLookback = ConsoleMenuUtility.PKConsoleMenuTools.promptChartPatterns(selectedMenu)
    else:
        respChartPattern, insideBarToLookback = ConsoleMenuUtility.PKConsoleMenuTools.promptChartPatterns(selectedMenu)
        if respChartPattern in [4] and not userPassedArgs.systemlaunched:
            _configure_vcp_filters(configManager, ConfigManager)
        if maLength == 0:
            if respChartPattern in [3, 6, 9]:
                maLength = ConsoleMenuUtility.PKConsoleMenuTools.promptChartPatternSubMenu(selectedMenu, respChartPattern)
            elif respChartPattern in [1, 2]:
                maLength = 1
        if maLength == 4 and respChartPattern == 3:
            _configure_super_confluence(options, userPassedArgs, configManager, ConfigManager)
    
    if respChartPattern is None or insideBarToLookback is None or respChartPattern == 0:
        return None, None, None
    if maLength == 0 and respChartPattern in [1, 2, 3, 6, 9]:
        return None, None, None
    
    userPassedArgs.maxdisplayresults = (
        max(configManager.maxdisplayresults, 2000) 
        if respChartPattern in [3, 4, 5, 8, 9] 
        else min(
            configManager.maxdisplayresults,
            (userPassedArgs.maxdisplayresults if (userPassedArgs is not None and userPassedArgs.maxdisplayresults is not None) else configManager.maxdisplayresults)
        )
    )
    
    selectedChoice["3"] = str(respChartPattern)
    if respChartPattern in [1, 2, 3] and userPassedArgs is not None and userPassedArgs.pipedmenus is not None:
        selectedChoice["4"] = str(insideBarToLookback)
        selectedChoice["5"] = str(maLength)
    else:
        selectedChoice["4"] = str(maLength)
        selectedChoice["5"] = ""
    
    # Handle candlestick patterns
    if respChartPattern == 7:
        maLength = _handle_candlestick_patterns(userPassedArgs, m0, selectedChoice)
        if maLength is None:
            return None, None, None
    
    return respChartPattern, insideBarToLookback, maLength


def _handle_chart_pattern_1_2_3(options, userPassedArgs, defaultAnswer, user, selectedMenu, respChartPattern, configManager, ConfigManager):
    """Handle chart patterns 1, 2, 3"""
    insideBarToLookback = 7
    maLength = 0
    
    if len(options) >= 5:
        if "".join(str(options[4]).split(".")).isdecimal():
            insideBarToLookback = float(options[4])
        elif str(options[4]).upper() == "D" or userPassedArgs.systemlaunched:
            insideBarToLookback = 7 if respChartPattern in [1, 2] else 0.02
        if len(options) >= 6:
            if str(options[5]).isnumeric():
                maLength = int(options[5])
            elif str(options[5]).upper() == "D" or userPassedArgs.systemlaunched:
                maLength = 4  # Super Conf. up
    elif defaultAnswer == "Y" and user is not None:
        if maLength == 0:
            maLength = 4 if respChartPattern in [3] else 0
        insideBarToLookback = 7 if respChartPattern in [1, 2] else (0.008 if (maLength == 4 and respChartPattern == 3) else 0.02)
    else:
        respChartPattern, insideBarToLookback = ConsoleMenuUtility.PKConsoleMenuTools.promptChartPatterns(selectedMenu)
    
    if maLength == 0:
        maLength = ConsoleMenuUtility.PKConsoleMenuTools.promptChartPatternSubMenu(selectedMenu, respChartPattern)
    
    if respChartPattern == 3 and maLength == 4:  # Super conf.
        if insideBarToLookback >= 1:
            insideBarToLookback = 0.008  # Set it to default .8%
    
    return insideBarToLookback, maLength


def _handle_chart_pattern_6_9(options, userPassedArgs, defaultAnswer, user, selectedMenu, respChartPattern):
    """Handle chart patterns 6 and 9"""
    maLength = 0
    if len(options) >= 5:
        if str(options[4]).isnumeric():
            maLength = int(options[4])
        elif str(options[4]).upper() == "D" or userPassedArgs.systemlaunched:
            maLength = 1 if respChartPattern == 6 else 6  # Bollinger Bands Squeeze-Buy or MA-Support
    elif defaultAnswer == "Y" and user is not None:
        maLength = 4 if respChartPattern == 6 else 6  # Bollinger Bands Squeeze- Any/All or MA-Support
    else:
        maLength = ConsoleMenuUtility.PKConsoleMenuTools.promptChartPatternSubMenu(selectedMenu, respChartPattern)
    return maLength


def _configure_vcp_filters(configManager, ConfigManager):
    """Configure VCP filters"""
    userInput = str(
        input(
            f"  [+] Enable additional VCP filters like range and consolidation? "
            f"[Y/N, Current: {colorText.FAIL}{'y' if configManager.enableAdditionalVCPFilters else 'n'}{colorText.END}]: "
        ) or ('y' if configManager.enableAdditionalVCPFilters else 'n')
    ).lower()
    configManager.enableAdditionalVCPFilters = "y" in userInput
    
    if configManager.enableAdditionalVCPFilters:
        configManager.vcpRangePercentageFromTop = OutputControls().takeUserInput(
            f"  [+] Range percentage from top: [Recommended: 20] "
            f"(Current: {colorText.FAIL}{configManager.vcpRangePercentageFromTop}{colorText.END}): "
        ) or configManager.vcpRangePercentageFromTop
        
        configManager.vcpLegsToCheckForConsolidation = OutputControls().takeUserInput(
            f"  [+] Number of consolidation legs [Recommended: 3] "
            f"(Current: {colorText.FAIL}{configManager.vcpLegsToCheckForConsolidation}{colorText.END}): "
        ) or configManager.vcpLegsToCheckForConsolidation
        
        userInput = str(
            input(
                f"  [+] Enable additional 20/50-EMA filters? [Y/N, Current: "
                f"{colorText.FAIL}{'y' if configManager.enableAdditionalVCPEMAFilters else 'n'}{colorText.END}]: "
            ) or ('y' if configManager.isIntradayConfig() else 'n')
        ).lower()
        configManager.enableAdditionalVCPEMAFilters = "y" in userInput
    
    configManager.setConfig(ConfigManager.parser, default=True, showFileCreatedText=False)


def _configure_super_confluence(options, userPassedArgs, configManager, ConfigManager):
    """Configure super confluence settings"""
    if len(options) <= 5 and not userPassedArgs.systemlaunched:
        configManager.superConfluenceMaxReviewDays = OutputControls().takeUserInput(
            f"  [+] Max review days ({colorText.GREEN}Optimal = 3-7{colorText.END}, "
            f"Current: {colorText.FAIL}{configManager.superConfluenceMaxReviewDays}{colorText.END}): "
        ) or configManager.superConfluenceMaxReviewDays
        
        configManager.superConfluenceEMAPeriods = OutputControls().takeUserInput(
            f"  [+] EMA periods ({colorText.GREEN}Optimal = 8,21,55{colorText.END}, "
            f"Current: {colorText.FAIL}{configManager.superConfluenceEMAPeriods}{colorText.END}): "
        ) or configManager.superConfluenceEMAPeriods
        
        enable200SMA = OutputControls().takeUserInput(
            f"  [+] Enable SMA-200 check? [Y/N, Current: "
            f"{colorText.FAIL}{'y' if configManager.superConfluenceEnforce200SMA else 'n'}{colorText.END}]: "
        ) or ('y' if configManager.superConfluenceEnforce200SMA else 'n')
        configManager.superConfluenceEnforce200SMA = "y" in enable200SMA.lower()
        
        configManager.setConfig(ConfigManager.parser, default=True, showFileCreatedText=False)


def _handle_candlestick_patterns(userPassedArgs, m0, selectedChoice):
    """Handle candlestick pattern selection"""
    maLength = "0"
    if userPassedArgs is None or userPassedArgs.answerdefault is None:
        m0.renderCandleStickPatterns()
        filterOption = OutputControls().takeUserInput(colorText.FAIL + "  [+] Select option: ") or "0"
        cupnHandleIndex = str(CandlePatterns.reversalPatternsBullish.index("Cup and Handle") + 1)
        
        if filterOption == cupnHandleIndex:
            maLength = str(input(
                "[+] Default is to find dynamically using volatility. Press enter to use default.\n"
                "[+] Enter number of candles to consider for left cup side formation:"
            )) or "0"
        
        if str(filterOption).upper() not in ["0", "M", cupnHandleIndex]:
            maLength = str(filterOption)
        elif str(filterOption).upper() == "M":
            return None
        
        selectedChoice["4"] = filterOption
    
    return maLength


def handle_execute_option_8(options: List[str], userPassedArgs) -> Tuple[Optional[int], Optional[int]]:
    """Handle execute option 8 - CCI values"""
    minRSI = 0
    maxRSI = 100
    
    if len(options) >= 5:
        if "".join(str(options[3]).split(".")).isdecimal():
            minRSI = int(options[3])
        if "".join(str(options[4]).split(".")).isdecimal():
            maxRSI = int(options[4])
        if str(options[3]).upper() == "D":
            minRSI = -150
            maxRSI = 250
    else:
        minRSI, maxRSI = ConsoleMenuUtility.PKConsoleMenuTools.promptCCIValues()
    
    if not minRSI and not maxRSI:
        OutputControls().printOutput(
            f"{colorText.FAIL}\n  [+] Error: Invalid values for CCI! "
            f"Values should be in range of -300 to 500. Please try again!{colorText.END}"
        )
        OutputControls().takeUserInput("Press <Enter> to continue...")
        return None, None
    
    return minRSI, maxRSI


def handle_execute_option_9(options: List[str], configManager) -> Optional[float]:
    """Handle execute option 9 - volume ratio"""
    volumeRatio = configManager.volumeRatio
    
    if len(options) >= 4:
        if str(options[3]).isnumeric():
            volumeRatio = float(options[3])
        elif str(options[3]).upper() == "D":
            volumeRatio = configManager.volumeRatio
    else:
        volumeRatio = ConsoleMenuUtility.PKConsoleMenuTools.promptVolumeMultiplier()
    
    if volumeRatio <= 0:
        OutputControls().printOutput(
            f"{colorText.FAIL}\n  [+] Error: Invalid values for Volume Ratio! "
            f"Value should be a positive number. Please try again!{colorText.END}"
        )
        OutputControls().takeUserInput("Press <Enter> to continue...")
        return None
    
    configManager.volumeRatio = float(volumeRatio)
    return volumeRatio


def handle_execute_option_12(userPassedArgs, configManager):
    """Handle execute option 12 - intraday toggle"""
    candleDuration = (
        userPassedArgs.intraday 
        if (userPassedArgs is not None and userPassedArgs.intraday is not None) 
        else "15m"
    )
    configManager.toggleConfig(candleDuration=candleDuration)
    return candleDuration


def handle_execute_option_21(options: List[str], m2, selectedChoice: Dict[str, str]) -> Tuple[Optional[int], bool]:
    """
    Handle execute option 21 - MFI stats.
    Returns (popOption, show_mfi_only)
    """
    selectedMenu = m2.find("21")
    popOption = None
    
    if len(options) >= 4:
        popOption = int(options[3])
        if popOption >= 0 and popOption <= 9:
            pass
        else:
            popOption = None
    else:
        popOption = ConsoleMenuUtility.PKConsoleMenuTools.promptSubMenuOptions(selectedMenu)
    
    if popOption is None or popOption == 0:
        return None, False
    
    selectedChoice["3"] = str(popOption)
    return popOption, popOption in [1, 2, 4]


def handle_execute_option_22(options: List[str], m2, selectedChoice: Dict[str, str]) -> Optional[int]:
    """Handle execute option 22"""
    selectedMenu = m2.find("22")
    popOption = None
    
    if len(options) >= 4:
        popOption = int(options[3])
        if popOption >= 0 and popOption <= 3:
            pass
        else:
            popOption = None
    else:
        popOption = ConsoleMenuUtility.PKConsoleMenuTools.promptSubMenuOptions(selectedMenu)
    
    if popOption is None or popOption == 0:
        return None
    
    selectedChoice["3"] = str(popOption)
    return popOption


def handle_execute_option_30(userPassedArgs, configManager, screener) -> None:
    """Handle execute option 30 - ATR Trailing Stop"""
    import pkscreener.classes.ConfigManager as ConfigManager
    from pkscreener.classes import ConsoleUtility
    
    if userPassedArgs.options is None:
        ConsoleUtility.PKConsoleTools.clearScreen(forceTop=True)
        atrSensitivity = OutputControls().takeUserInput(
            f"{colorText.WARN}Enter the ATR Trailing Stop Sensitivity "
            f"({colorText.GREEN}Optimal:1{colorText.END}, Current={configManager.atrTrailingStopSensitivity}):"
        ) or configManager.atrTrailingStopSensitivity
        configManager.atrTrailingStopSensitivity = atrSensitivity
        
        atrPeriod = OutputControls().takeUserInput(
            f"{colorText.WARN}Enter the ATR Period value "
            f"({colorText.GREEN}Optimal:10{colorText.END}, Current={configManager.atrTrailingStopPeriod}):"
        ) or configManager.atrTrailingStopPeriod
        configManager.atrTrailingStopPeriod = atrPeriod
        
        atrEma = OutputControls().takeUserInput(
            f"{colorText.WARN}Enter the ATR EMA period "
            f"({colorText.GREEN}Optimal:200{colorText.END}, Current={configManager.atrTrailingStopEMAPeriod}):"
        ) or configManager.atrTrailingStopEMAPeriod
        configManager.atrTrailingStopEMAPeriod = atrEma
        
        configManager.setConfig(ConfigManager.parser, default=True, showFileCreatedText=False)
    
    screener.shouldLog = userPassedArgs.log
    screener.computeBuySellSignals(None)


def handle_execute_option_31(userPassedArgs) -> int:
    """Handle execute option 31 - DEEL Momentum. Returns maLength."""
    maLength = 0
    if userPassedArgs.options is None:
        beStrict = OutputControls().takeUserInput(
            f"{colorText.WARN}Strictly show only high momentum stocks? "
            f"({colorText.GREEN}Optimal:N{colorText.END}, Default=Y). Choose Y or N:"
        ) or "N"
        if beStrict.lower().startswith("y"):
            maLength = 1
    return maLength


def handle_execute_option_33(options: List[str], m2, selectedChoice: Dict[str, str], userPassedArgs) -> Optional[int]:
    """Handle execute option 33. Returns maLength."""
    selectedMenu = m2.find("33")
    maLength = 0
    
    if len(options) >= 4:
        if str(options[3]).isnumeric():
            maLength = int(options[3])
        elif str(options[3]).upper() == "D":
            maLength = 2
        else:
            maLength = 2
    elif len(options) >= 3:
        maLength = 2  # By default Bullish PDO/PDC
    else:
        maLength = ConsoleMenuUtility.PKConsoleMenuTools.promptSubMenuOptions(selectedMenu, defaultOption="2")
    
    if maLength == 0:
        return None
    
    selectedChoice["3"] = str(maLength)
    
    if maLength == 3:
        userPassedArgs.maxdisplayresults = max(100, userPassedArgs.maxdisplayresults or 100) * 20
    
    return maLength


def handle_execute_option_34(userPassedArgs, configManager) -> None:
    """Handle execute option 34 - Anchored AVWAP"""
    import pkscreener.classes.ConfigManager as ConfigManager
    
    if userPassedArgs.options is None:
        configManager.anchoredAVWAPPercentage = OutputControls().takeUserInput(
            f"{colorText.WARN}Enter the anchored-VWAP percentage gap "
            f"({colorText.GREEN}Optimal:1{colorText.END}, Current={configManager.anchoredAVWAPPercentage}):"
        ) or configManager.anchoredAVWAPPercentage
        configManager.setConfig(ConfigManager.parser, default=True, showFileCreatedText=False)


def handle_execute_option_42_43(executeOption: int, userPassedArgs) -> float:
    """Handle execute option 42 (Super Gainer) or 43 (Super Losers). Returns maLength."""
    if executeOption == 42:
        maLength = 10
        if userPassedArgs.options is None:
            maLength = OutputControls().takeUserInput(
                f"{colorText.WARN}Minimum Percent change for super gainers? "
                f"({colorText.GREEN}Optimal:15{colorText.END}, Default=10):"
            ) or 10
            if not str(maLength).replace("-", "").replace(".", "").isnumeric():
                maLength = 10
            else:
                maLength = float(maLength)
    else:  # executeOption == 43
        maLength = -10
        if userPassedArgs.options is None:
            maLength = OutputControls().takeUserInput(
                f"{colorText.WARN}Minimum Percent change for super losers? "
                f"({colorText.GREEN}Optimal:-10{colorText.END}, Default=-10):"
            ) or -10
            if not str(maLength).replace("-", "").replace(".", "").isnumeric():
                maLength = -10
            else:
                maLength = float(maLength)
                if maLength > 0:
                    maLength = 0 - maLength
    
    return maLength


def handle_execute_option_40(
    options: List[str],
    m2, m3, m4,
    userPassedArgs,
    selectedChoice: Dict[str, str]
) -> Tuple[Optional[bool], Optional[bool], Optional[List[str]]]:
    """
    Handle execute option 40 - SMA/EMA cross.
    Returns (respChartPattern, reversalOption, insideBarToLookback) or (None, None, None) on failure
    """
    from pkscreener.classes import ConsoleUtility
    
    ConsoleUtility.PKConsoleTools.clearScreen(forceTop=True)
    selectedMenu = m2.find("40")
    m3.renderForMenu(selectedMenu=selectedMenu, asList=(userPassedArgs is not None and userPassedArgs.options is not None))
    
    if userPassedArgs.options is not None:
        options = userPassedArgs.options.split(":")
    
    if len(options) >= 4:
        smaEMA = options[3]
        smaEMA = "2" if smaEMA == "D" else smaEMA
    else:
        smaEMA = OutputControls().takeUserInput(colorText.FAIL + "  [+] Select option: ") or "2"
    
    if smaEMA == "0":
        return None, None, None
    
    selectedChoice["3"] = str(smaEMA)
    respChartPattern = (smaEMA == "2")
    
    selectedMenu = m3.find(str(smaEMA))
    ConsoleUtility.PKConsoleTools.clearScreen(forceTop=True)
    m4.renderForMenu(selectedMenu=selectedMenu, asList=(userPassedArgs is not None and userPassedArgs.options is not None))
    
    if len(options) >= 5:
        smaDirection = options[4]
        smaDirection = "2" if smaDirection == "D" else smaDirection
    else:
        smaDirection = OutputControls().takeUserInput(colorText.FAIL + "  [+] Select option: ") or "2"
    
    if smaDirection == "0":
        return None, None, None
    
    selectedChoice["4"] = str(smaDirection)
    reversalOption = (smaDirection == "2")
    
    ConsoleUtility.PKConsoleTools.clearScreen(forceTop=True)
    
    if len(options) >= 6:
        smas = options[5]
        smas = "200" if smas == "D" else smas
    else:
        smas = OutputControls().takeUserInput(
            f"{colorText.FAIL}  [+] Price should cross which EMA/SMA(s) "
            f"(e.g. 200 or 8,9,21,55,200) [Default: 200]:"
        ) or "200"
    
    insideBarToLookback = smas.split(",")
    selectedChoice["5"] = str(smas)
    
    return respChartPattern, reversalOption, insideBarToLookback


def handle_execute_option_41(
    options: List[str],
    m2, m3, m4,
    userPassedArgs,
    selectedChoice: Dict[str, str]
) -> Tuple[Optional[str], Optional[bool]]:
    """
    Handle execute option 41 - Pivot point.
    Returns (respChartPattern, reversalOption) or (None, None) on failure
    """
    from pkscreener.classes import ConsoleUtility
    
    ConsoleUtility.PKConsoleTools.clearScreen(forceTop=True)
    selectedMenu = m2.find("41")
    m3.renderForMenu(selectedMenu=selectedMenu, asList=(userPassedArgs is not None and userPassedArgs.options is not None))
    
    if userPassedArgs.options is not None:
        options = userPassedArgs.options.split(":")
    
    if len(options) >= 4:
        pivotPoint = options[3]
        pivotPoint = "1" if pivotPoint == "D" else pivotPoint
    else:
        pivotPoint = OutputControls().takeUserInput(colorText.FAIL + "  [+] Select option: ") or "1"
    
    if pivotPoint == "0" or not str(pivotPoint).isnumeric():
        return None, None
    
    selectedChoice["3"] = str(pivotPoint)
    respChartPattern = pivotPoint
    
    selectedMenu = m3.find(str(pivotPoint))
    ConsoleUtility.PKConsoleTools.clearScreen(forceTop=True)
    m4.renderForMenu(selectedMenu=selectedMenu, asList=(userPassedArgs is not None and userPassedArgs.options is not None))
    
    if len(options) >= 5:
        priceDirection = options[4]
        priceDirection = "2" if priceDirection == "D" else priceDirection
    else:
        priceDirection = OutputControls().takeUserInput(colorText.FAIL + "  [+] Select option: ") or "2"
    
    if priceDirection == "0" or not str(priceDirection).isnumeric():
        return None, None
    
    selectedChoice["4"] = str(priceDirection)
    reversalOption = (priceDirection == "2")
    
    return respChartPattern, reversalOption

