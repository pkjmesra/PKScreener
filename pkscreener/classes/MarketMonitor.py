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
import os
import sys
import pandas as pd
import numpy as np
from time import sleep

from PKDevTools.classes.Singleton import SingletonType, SingletonMixin
from PKDevTools.classes.OutputControls import OutputControls
from PKDevTools.classes.ColorText import colorText
from PKDevTools.classes import Archiver
from PKDevTools.classes.SuppressOutput import SuppressOutput
from PKDevTools.classes.log import default_logger


class MarketMonitor(SingletonMixin, metaclass=SingletonType):
    """
    A singleton class for monitoring stock market data in real-time.
    
    This class manages a dashboard display of multiple stock screening monitors,
    with support for:
    - Grid-based display of multiple monitors
    - Pinned single monitor mode for focused tracking
    - Alert notifications for new stocks
    - Telegram integration for remote monitoring
    
    The monitor displays data in a matrix format, showing key metrics like
    LTP (Last Traded Price), change percentage, 52-week high, RSI, and volume.
    
    Attributes:
        monitors (list): List of monitor option strings
        monitorIndex (int): Current monitor index for cycling
        monitorPositions (dict): Grid positions for each monitor
        monitorResultStocks (dict): Cached stock results per monitor
        alertOptions (list): Monitor options that trigger alerts
        alertStocks (list): Newly detected stocks for alerting
        alertedStocks (dict): Already alerted stocks per monitor
        isPinnedSingleMonitorMode (bool): Whether in single monitor focus mode
    """
    
    # ========================================================================
    # Initialization
    # ========================================================================
    
    def __init__(
        self,
        monitors=None,
        maxNumResultsPerRow=3,
        maxNumColsInEachResult=6,
        maxNumRowsInEachResult=10,
        maxNumResultRowsInMonitor=2,
        pinnedIntervalWaitSeconds=30,
        alertOptions=None
    ):
        """
        Initialize the MarketMonitor.
        
        Args:
            monitors: List of monitor option strings to track
            maxNumResultsPerRow: Maximum monitors per row in grid
            maxNumColsInEachResult: Maximum columns per monitor widget
            maxNumRowsInEachResult: Maximum rows per monitor widget
            maxNumResultRowsInMonitor: Maximum rows of widgets
            pinnedIntervalWaitSeconds: Refresh interval for pinned mode
            alertOptions: Monitor options that should trigger alerts
        """
        super(MarketMonitor, self).__init__()
        
        monitors = monitors or []
        alertOptions = alertOptions or []
        
        if monitors is not None and len(monitors) > 0:
            self._initializeMonitorState(
                monitors, maxNumResultsPerRow, maxNumColsInEachResult,
                maxNumRowsInEachResult, maxNumResultRowsInMonitor,
                pinnedIntervalWaitSeconds, alertOptions
            )
    
    def _initializeMonitorState(
        self, monitors, maxNumResultsPerRow, maxNumColsInEachResult,
        maxNumRowsInEachResult, maxNumResultRowsInMonitor,
        pinnedIntervalWaitSeconds, alertOptions
    ):
        """Initialize internal state for monitor management."""
        # Limit monitors to grid capacity
        maxMonitors = maxNumResultRowsInMonitor * maxNumResultsPerRow
        self.monitors = monitors[:maxMonitors]
        
        # Monitor state tracking
        self.monitorIndex = 0
        self.monitorPositions = {}
        self.monitorResultStocks = {}
        self.alertOptions = alertOptions
        self.hiddenColumns = ""
        self.alertStocks = []
        self.alertedStocks = {}
        self.pinnedIntervalWaitSeconds = pinnedIntervalWaitSeconds
        
        # Grid configuration
        self.maxNumResultRowsInMonitor = maxNumResultRowsInMonitor
        self.maxNumRowsInEachResult = maxNumRowsInEachResult
        self.maxNumColsInEachResult = maxNumColsInEachResult
        self.maxNumResultsPerRow = maxNumResultsPerRow
        self.lines = 0
        
        # Calculate grid positions for each monitor
        self._calculateMonitorPositions()
        
        # Initialize DataFrame with grid columns
        self._initializeMonitorDataFrame()
        
        self.isPinnedSingleMonitorMode = len(self.monitorPositions.keys()) == 1
    
    def _calculateMonitorPositions(self):
        """Calculate grid positions for each monitor widget."""
        rowIndex = 0
        colIndex = 0
        maxColIndex = self.maxNumColsInEachResult * self.maxNumResultsPerRow - 1
        
        for monIndex, monitorKey in enumerate(self.monitors):
            self.alertedStocks[str(monIndex)] = []
            self.monitorPositions[monitorKey] = [rowIndex, colIndex]
            
            colIndex += self.maxNumColsInEachResult
            if colIndex > maxColIndex:
                colIndex = 0
                rowIndex += self.maxNumRowsInEachResult
    
    def _initializeMonitorDataFrame(self):
        """Initialize the monitor DataFrame with proper columns."""
        maxColIndex = self.maxNumColsInEachResult * self.maxNumResultsPerRow - 1
        maxColIndex = min(maxColIndex, len(self.monitorPositions) * self.maxNumColsInEachResult - 1)
        columns = [f"A{i + 1}" for i in range(maxColIndex + 1)]
        self.monitor_df = pd.DataFrame(columns=columns)
    
    # ========================================================================
    # Monitor Cycling
    # ========================================================================
    
    def currentMonitorOption(self):
        """
        Get the current monitor option and advance to the next.
        
        Returns:
            str or None: The current monitor option string
        """
        try:
            option = None
            maxIndex = len(self.monitors) - 1
            option = str(self.monitors[self.monitorIndex:self.monitorIndex + 1][0])
            self.monitorIndex += 1
            if self.monitorIndex > maxIndex:
                self.monitorIndex = 0
        except:
            pass
        return option
    
    # ========================================================================
    # Result Management
    # ========================================================================
    
    def saveMonitorResultStocks(self, results_df):
        """
        Save and track stock results for alert detection.
        
        Compares new results with previously saved results to detect
        newly appearing stocks that should trigger alerts.
        
        Args:
            results_df: DataFrame of screening results
        """
        try:
            # Ensure alert storage exists for current monitor
            if len(self.alertedStocks.keys()) < self.monitorIndex + 1:
                self.alertedStocks[str(self.monitorIndex)] = []
            
            self.alertStocks = []
            lastSavedResults = self.monitorResultStocks.get(str(self.monitorIndex), "")
            lastSavedResults = lastSavedResults.split(",") if lastSavedResults else []
        except:
            lastSavedResults = []
        
        # Extract current results
        if results_df is None or results_df.empty:
            prevOutput_results = "NONE"
        else:
            prevOutput_results = results_df[~results_df.index.duplicated(keep='first')]
            prevOutput_results = ",".join(prevOutput_results.index)
        
        # Preserve previous results if current is empty
        if (len(self.monitorResultStocks.keys()) > self.monitorIndex and
            str(self.monitorIndex) in self.monitorResultStocks.keys() and
            len(self.monitorResultStocks[str(self.monitorIndex)]) > 0 and
            prevOutput_results == "NONE"):
            prevOutput_results = self.monitorResultStocks[str(self.monitorIndex)]
        
        # Detect newly added stocks
        addedStocks = list(set(prevOutput_results.split(',')) - set(lastSavedResults))
        if len(self.alertStocks) != len(addedStocks) and len(addedStocks) > 0:
            self.alertStocks = addedStocks
        
        # Filter out already alerted stocks
        diffAlerts = list(set(self.alertStocks) - set(self.alertedStocks[str(self.monitorIndex)]))
        if len(diffAlerts) > 0:
            self.alertStocks = diffAlerts
            self.alertedStocks[str(self.monitorIndex)].extend(diffAlerts)
        else:
            self.alertStocks = []
        
        # Update saved results
        if len(addedStocks) > 0:
            self.monitorResultStocks[str(self.monitorIndex)] = prevOutput_results
    
    # ========================================================================
    # Display Refresh
    # ========================================================================
    
    def refresh(
        self,
        screen_df: pd.DataFrame = None,
        screenOptions=None,
        chosenMenu="",
        dbTimestamp="",
        telegram=False
    ):
        """
        Refresh the monitor display with new data.
        
        Updates the dashboard with new screening results, handles
        alert detection, and manages display for both console and
        Telegram modes.
        
        Args:
            screen_df: DataFrame of screening results
            screenOptions: The screening option string
            chosenMenu: Human-readable menu path
            dbTimestamp: Timestamp of the data
            telegram: Whether running in Telegram bot mode
        """
        if screen_df is None or screen_df.empty or screenOptions is None:
            return
        
        from pkscreener.classes import Utility, ImageUtility
        
        highlightRows = []
        highlightCols = []
        telegram_df = None
        screen_monitor_df = screen_df.copy()
        monitorPosition = self.monitorPositions.get(screenOptions)
        
        # Update display based on mode
        if self.isPinnedSingleMonitorMode:
            telegram_df = self._refreshPinnedMode(screen_monitor_df, ImageUtility, telegram)
        else:
            screen_monitor_df, telegram_df = self._prepareGridModeData(
                screen_monitor_df, ImageUtility, telegram
            )
        
        if monitorPosition is not None:
            if self.isPinnedSingleMonitorMode:
                self._updatePinnedDisplay(ImageUtility)
            else:
                highlightRows, highlightCols = self._updateGridDisplay(
                    screen_monitor_df, screenOptions, monitorPosition, ImageUtility
                )
        
        # Render output
        self.monitor_df = self.monitor_df.replace(np.nan, "-", regex=True)
        self._displayMonitorOutput(
            screenOptions, chosenMenu, dbTimestamp, telegram, telegram_df,
            highlightRows, highlightCols, monitorPosition, ImageUtility
        )
    
    def _refreshPinnedMode(self, screen_monitor_df, ImageUtility, telegram):
        """Handle refresh for pinned single monitor mode."""
        screen_monitor_df = screen_monitor_df[screen_monitor_df.columns[:14]]
        self.monitor_df = screen_monitor_df
        
        if "RUNNER" in os.environ.keys():
            self.monitor_df.reset_index(inplace=True)
            with pd.option_context('mode.chained_assignment', None):
                self.monitor_df = self.monitor_df[[
                    "Stock", "LTP", "%Chng", "52Wk-H",
                    "RSI/i" if "RSI/i" in self.monitor_df.columns else "RSI",
                    "volume"
                ]]
                
                # Format columns
                self.monitor_df.loc[:, "%Chng"] = self.monitor_df.loc[:, "%Chng"].astype(str).apply(
                    lambda x: ImageUtility.PKImageTools.roundOff(
                        str(x).split("% (")[0] + colorText.END, 0
                    )
                )
                self.monitor_df.loc[:, "52Wk-H"] = self.monitor_df.loc[:, "52Wk-H"].astype(str).apply(
                    lambda x: ImageUtility.PKImageTools.roundOff(x, 0)
                )
                self.monitor_df.loc[:, "volume"] = self.monitor_df.loc[:, "volume"].astype(str).apply(
                    lambda x: ImageUtility.PKImageTools.roundOff(x, 0)
                )
                
                self.monitor_df.rename(columns={
                    "%Chng": "Ch%", "volume": "Vol",
                    "52Wk-H": "52WkH", "RSI": "RSI/i"
                }, inplace=True)
                
                telegram_df = self.updateDataFrameForTelegramMode(
                    telegram or "RUNNER" in os.environ.keys(),
                    self.monitor_df
                )
                self.monitor_df.set_index("Stock", inplace=True)
        
        return telegram_df if "RUNNER" in os.environ.keys() else None
    
    def _prepareGridModeData(self, screen_monitor_df, ImageUtility, telegram):
        """Prepare data for grid display mode."""
        screen_monitor_df.reset_index(inplace=True)
        with pd.option_context('mode.chained_assignment', None):
            rsi_col = "RSI/i" if "RSI/i" in screen_monitor_df.columns else "RSI"
            screen_monitor_df = screen_monitor_df[[
                "Stock", "LTP", "%Chng", "52Wk-H", rsi_col, "volume"
            ]].head(self.maxNumRowsInEachResult - 1)
            
            # Format columns
            screen_monitor_df.loc[:, "%Chng"] = screen_monitor_df.loc[:, "%Chng"].astype(str).apply(
                lambda x: ImageUtility.PKImageTools.roundOff(
                    str(x).split("% (")[0] + colorText.END, 0
                )
            )
            screen_monitor_df.loc[:, "52Wk-H"] = screen_monitor_df.loc[:, "52Wk-H"].astype(str).apply(
                lambda x: ImageUtility.PKImageTools.roundOff(x, 0)
            )
            screen_monitor_df.loc[:, "volume"] = screen_monitor_df.loc[:, "volume"].astype(str).apply(
                lambda x: ImageUtility.PKImageTools.roundOff(x, 0)
            )
            screen_monitor_df.rename(columns={
                "%Chng": "Ch%", "volume": "Vol",
                "52Wk-H": "52WkH", "RSI": "RSI/i"
            }, inplace=True)
        
        telegram_df = self.updateDataFrameForTelegramMode(
            telegram or "RUNNER" in os.environ.keys(),
            screen_monitor_df
        )
        
        return screen_monitor_df, telegram_df
    
    def _updatePinnedDisplay(self, ImageUtility):
        """Update display for pinned single monitor mode."""
        stocks = list(self.monitor_df.index)
        updatedStocks = []
        
        for stock in stocks:
            stockName = ImageUtility.PKImageTools.stockNameFromDecoratedName(stock)
            if stockName in self.alertStocks:
                stockName = f"{colorText.BOLD}{colorText.WHITE_FG_BRED_BG}{stock}{colorText.END}"
            else:
                stockName = stock
            updatedStocks.append(stockName)
        
        self.monitor_df.reset_index(inplace=True)
        with pd.option_context('mode.chained_assignment', None):
            self.monitor_df["Stock"] = updatedStocks
        self.monitor_df.set_index("Stock", inplace=True)
    
    def _updateGridDisplay(self, screen_monitor_df, screenOptions, monitorPosition, ImageUtility):
        """Update grid display with monitor widget."""
        startRowIndex, startColIndex = monitorPosition
        highlightRows = [startRowIndex]
        highlightCols = []
        
        if not self.monitor_df.empty:
            OutputControls().moveCursorUpLines(self.lines)
        
        firstColIndex = startColIndex
        rowIndex = 0
        colIndex = 0
        
        while rowIndex <= len(screen_monitor_df):
            for col in screen_monitor_df.columns:
                if rowIndex == 0:
                    # Column headers
                    cleanedScreenOptions = screenOptions.replace(":D", "")
                    widgetHeader = self._getWidgetHeader(cleanedScreenOptions, screenOptions)
                    
                    self.monitor_df.loc[startRowIndex, [f"A{startColIndex + 1}"]] = (
                        colorText.HEAD +
                        (widgetHeader if startColIndex == firstColIndex else col) +
                        colorText.END
                    )
                    highlightCols.append(startColIndex)
                else:
                    # Data rows
                    if colIndex == 0:
                        stockNameDecorated = screen_monitor_df.iloc[rowIndex - 1, colIndex]
                        stockName = ImageUtility.PKImageTools.stockNameFromDecoratedName(stockNameDecorated)
                        if stockName in self.alertStocks:
                            stockName = (
                                f"{colorText.BOLD}{colorText.WHITE_FG_BRED_BG}"
                                f"{stockNameDecorated}{colorText.END}"
                            )
                        else:
                            stockName = stockNameDecorated
                        self.monitor_df.loc[startRowIndex, [f"A{startColIndex + 1}"]] = stockName
                    else:
                        self.monitor_df.loc[startRowIndex, [f"A{startColIndex + 1}"]] = (
                            screen_monitor_df.iloc[rowIndex - 1, colIndex]
                        )
                    colIndex += 1
                
                startColIndex += 1
            
            _, startColIndex = monitorPosition
            rowIndex += 1
            colIndex = 0
            highlightRows.append(startRowIndex + 1)
            startRowIndex += 1
        
        return highlightRows, highlightCols
    
    def _getWidgetHeader(self, cleanedScreenOptions, screenOptions):
        """Generate widget header text from screen options."""
        widgetHeader = self.getScanOptionName(cleanedScreenOptions)
        
        if len(widgetHeader) <= 0:
            if cleanedScreenOptions.startswith("|"):
                cleanedScreenOptions = cleanedScreenOptions.replace("|", "")
                pipedFrom = ""
                if cleanedScreenOptions.startswith("{"):
                    pipedFrom = cleanedScreenOptions.split("}")[0] + "}:"
                cleanedScreenOptions = pipedFrom + ":".join(cleanedScreenOptions.split(":")[2:])
                cleanedScreenOptions = cleanedScreenOptions.replace(">X:0:", "")
            
            widgetHeader = ":".join(cleanedScreenOptions.split(":")[:4])
            if "i " in screenOptions:
                widgetHeader = (
                    f'{":".join(widgetHeader.split(":")[:3])}:i:'
                    f'{cleanedScreenOptions.split("i ")[-1]}'
                )
        
        return widgetHeader
    
    def _displayMonitorOutput(
        self, screenOptions, chosenMenu, dbTimestamp, telegram, telegram_df,
        highlightRows, highlightCols, monitorPosition, ImageUtility
    ):
        """Display the formatted monitor output."""
        from pkscreener.classes import Utility
        
        latestScanMenuOption = (
            f"  [+] {dbTimestamp} (Dashboard) > "
            f"{chosenMenu[:190]} [{screenOptions}]"
        )
        OutputControls().printOutput(
            colorText.FAIL + latestScanMenuOption[:200] + colorText.END,
            enableMultipleLineOutput=True
        )
        
        # Render main table
        tabulated_results = colorText.miniTabulator().tabulate(
            self.monitor_df,
            tablefmt=colorText.No_Pad_GridFormat,
            headers="keys" if self.isPinnedSingleMonitorMode else (),
            highlightCharacter=colorText.HEAD + "=" + colorText.END,
            showindex=self.isPinnedSingleMonitorMode,
            highlightedRows=highlightRows,
            highlightedColumns=highlightCols,
            maxcolwidths=Utility.tools.getMaxColumnWidths(self.monitor_df)
        )
        
        # Render console output (with hidden columns removed)
        console_results = self._getConsoleResults(tabulated_results, Utility)
        
        numRecords = len(tabulated_results.splitlines())
        self.lines = numRecords
        
        OutputControls().printOutput(
            tabulated_results if not self.isPinnedSingleMonitorMode else console_results,
            enableMultipleLineOutput=True
        )
        
        # Handle alerts and Telegram updates
        self._handleAlertsAndTelegram(
            screenOptions, chosenMenu, dbTimestamp, telegram, telegram_df,
            numRecords, monitorPosition
        )
    
    def _getConsoleResults(self, tabulated_results, Utility):
        """Get console results with hidden columns removed."""
        if not self.isPinnedSingleMonitorMode:
            return tabulated_results
        
        copyScreenResults = self.monitor_df.copy()
        hiddenColumns = self.hiddenColumns.split(",")
        
        for col in copyScreenResults.columns:
            if col in hiddenColumns:
                copyScreenResults.drop(col, axis=1, inplace=True, errors="ignore")
        
        try:
            return colorText.miniTabulator().tabulate(
                copyScreenResults,
                headers="keys",
                tablefmt=colorText.No_Pad_GridFormat,
                maxcolwidths=Utility.tools.getMaxColumnWidths(copyScreenResults)
            )
        except:
            return tabulated_results
    
    def _handleAlertsAndTelegram(
        self, screenOptions, chosenMenu, dbTimestamp, telegram, telegram_df,
        numRecords, monitorPosition
    ):
        """Handle alert sounds and Telegram updates."""
        from pkscreener.classes import Utility
        
        shouldAlert = (
            (screenOptions in self.alertOptions and numRecords > 1) or
            len(self.alertStocks) > 0
        )
        
        if not telegram and shouldAlert:
            Utility.tools.alertSound(beeps=5)
        
        if not self.isPinnedSingleMonitorMode:
            if telegram:
                self.updateIfRunningInTelegramBotMode(
                    screenOptions, chosenMenu, dbTimestamp, telegram, telegram_df
                )
        else:
            pinnedAlertCondition = (
                (screenOptions in self.alertOptions and numRecords > 3) or
                len(self.alertStocks) > 0
            )
            
            if pinnedAlertCondition:
                self._handlePinnedModeAlert(
                    screenOptions, chosenMenu, dbTimestamp, telegram_df
                )
                Utility.tools.alertSound(beeps=5)
            
            sleep(self.pinnedIntervalWaitSeconds)
    
    def _handlePinnedModeAlert(self, screenOptions, chosenMenu, dbTimestamp, telegram_df):
        """Handle alerts in pinned single monitor mode."""
        if telegram_df is not None:
            telegram_df.reset_index(inplace=True)
            notify_df = telegram_df[telegram_df["Stock"].isin(self.alertStocks)]
            notify_df = notify_df[["Stock", "LTP", "Ch%", "Vol"]].head(50)
            
            if len(notify_df) > 0:
                notify_output = self.updateIfRunningInTelegramBotMode(
                    screenOptions, chosenMenu, dbTimestamp, False,
                    notify_df, maxcolwidths=None
                )
                if len(notify_output) > 0:
                    from PKDevTools.classes.pubsub.publisher import PKUserService
                    PKUserService().notify_user(
                        scannerID=self.getScanOptionName(screenOptions),
                        notification=notify_output
                    )
    
    # ========================================================================
    # Telegram Integration
    # ========================================================================
    
    def updateDataFrameForTelegramMode(self, telegram, screen_monitor_df):
        """
        Prepare DataFrame for Telegram display.
        
        Strips color codes and formats values for Telegram's text display.
        
        Args:
            telegram: Whether Telegram mode is active
            screen_monitor_df: The monitor DataFrame
            
        Returns:
            DataFrame formatted for Telegram, or None
        """
        if not telegram:
            return None
        
        telegram_df = screen_monitor_df[["Stock", "LTP", "Ch%", "Vol"]]
        
        try:
            # Clean stock names
            telegram_df.loc[:, "Stock"] = telegram_df.loc[:, "Stock"].apply(
                lambda x: x.split('\x1b')[3].replace('\\', '') if 'http' in x else x
            )
            
            # Clean color codes from numeric columns
            color_codes = [
                colorText.FAIL, colorText.GREEN, colorText.WARN,
                colorText.BOLD, colorText.END
            ]
            for col in ["LTP", "Ch%", "Vol"]:
                telegram_df.loc[:, col] = telegram_df.loc[:, col].apply(
                    lambda x: self._stripColorCodes(x, color_codes)
                )
            
            # Format values
            telegram_df.loc[:, "LTP"] = telegram_df.loc[:, "LTP"].apply(
                lambda x: str(int(round(float(x), 0)))
            )
            telegram_df.loc[:, "Ch%"] = telegram_df.loc[:, "Ch%"].apply(
                lambda x: f'{int(round(float(x.replace("%", "")), 0))}%'
            )
            telegram_df.loc[:, "Vol"] = telegram_df.loc[:, "Vol"].apply(
                lambda x: f'{int(round(float(x.replace("x", "")), 0))}x'
            )
            
            with SuppressOutput(suppress_stderr=True, suppress_stdout=True):
                for col in telegram_df.columns:
                    telegram_df[col] = telegram_df[col].astype(str)
        except:
            pass
        
        return telegram_df
    
    def _stripColorCodes(self, value, color_codes):
        """Strip color codes from a value."""
        result = value
        for code in color_codes:
            result = result.replace(code, "")
        return result
    
    def updateIfRunningInTelegramBotMode(
        self, screenOptions, chosenMenu, dbTimestamp, telegram, telegram_df,
        maxcolwidths=None
    ):
        """
        Generate output for Telegram bot mode.
        
        Creates formatted HTML output suitable for Telegram messages.
        
        Args:
            screenOptions: Current screen options string
            chosenMenu: Menu path chosen
            dbTimestamp: Data timestamp
            telegram: Whether to save to file
            telegram_df: DataFrame for Telegram
            maxcolwidths: Column width limits
            
        Returns:
            str: Formatted output string
        """
        maxcolwidths = maxcolwidths if maxcolwidths is not None else [None, None, 4, 3]
        result_output = ""
        telegram_df_tabulated = ""
        
        if telegram_df is not None:
            STD_ENCODING = sys.stdout.encoding if sys.stdout is not None else 'utf-8'
            
            try:
                telegram_df_tabulated = colorText.miniTabulator().tabulate(
                    telegram_df,
                    headers="keys",
                    tablefmt=colorText.No_Pad_GridFormat,
                    showindex=False,
                    maxcolwidths=maxcolwidths
                ).encode("utf-8").decode(STD_ENCODING)
                
                # Clean up formatting
                telegram_df_tabulated = self._cleanTelegramOutput(telegram_df_tabulated)
            except Exception as e:
                default_logger().debug(e, exc_info=True)
            
            # Build output string
            choiceSegments = chosenMenu.split(">")
            optionName = self.getScanOptionName(screenOptions)
            
            if len(choiceSegments) >= 4 or len(choiceSegments[-1]) <= 10:
                chosenMenu = f"{choiceSegments[-2]}>{choiceSegments[-1]}"
            else:
                chosenMenu = f"{choiceSegments[-1]}"
            
            result_output = (
                f"Latest data as of {dbTimestamp}\n"
                f"<b>[{optionName}] {chosenMenu}</b> [{screenOptions}]\n"
                f"<pre>{telegram_df_tabulated}</pre>"
            )
            
            # Save to file if in Telegram mode
            if telegram:
                self._saveTelegramOutput(result_output)
        
        return result_output
    
    def _cleanTelegramOutput(self, text):
        """Clean up formatting in Telegram output."""
        replacements = [
            ("-K-----S-----C-----R", "-K-----S----C---R"),
            ("%  ", "% "),
            ("=K=====S=====C=====R", "=K=====S====C===R"),
            ("Vol  |", "Vol|"),
            ("x  ", "x"),
            ("-E-----N-----E-----R", "-E-----N----E---R"),
            ("=E=====N=====E=====R", "=E=====N====E===R"),
        ]
        
        result = text
        for old, new in replacements:
            result = result.replace(old, new)
        return result
    
    def _saveTelegramOutput(self, result_output):
        """Save Telegram output to file."""
        try:
            filePath = os.path.join(
                Archiver.get_user_data_dir(),
                f"monitor_outputs_{self.monitorIndex}.txt"
            )
            with open(filePath, "w") as f:
                f.write(result_output)
        except:
            pass
    
    # ========================================================================
    # Utility Methods
    # ========================================================================
    
    def getScanOptionName(self, screenOptions):
        """
        Get a human-readable name for screen options.
        
        Looks up predefined scan names or generates a formatted name
        from the option string.
        
        Args:
            screenOptions: The screen options string
            
        Returns:
            str: Human-readable option name
        """
        from pkscreener.classes.MenuOptions import PREDEFINED_SCAN_MENU_VALUES
        
        if screenOptions is None:
            return ""
        
        baseIndex = 12
        baseIndices = str(screenOptions).split(":")
        if len(baseIndices) > 1:
            baseIndex = baseIndices[1]
        
        choices = (
            f"--systemlaunched -a y -e -o "
            f"'{str(screenOptions).replace('C:', 'X:').replace('D:', '')}'"
        )
        
        indexNum = -1
        try:
            indexNum = PREDEFINED_SCAN_MENU_VALUES.index(choices)
        except:
            pass
        
        optionName = str(screenOptions).replace(':D', '').replace(':', '_')
        
        if indexNum >= 0:
            if '>|' in choices:
                optionName = f"P_1_{indexNum + 1}_{baseIndex}"
        
        return optionName
