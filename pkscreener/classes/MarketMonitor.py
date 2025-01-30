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

# This code defines a MarketMonitor class that manages the monitoring of stock market data. 
# It utilizes the Singleton design pattern to ensure only one instance of the class exists. 
# The class initializes with a list of monitors and various configuration parameters, 
# and provides methods for updating and displaying stock data, handling alerts, 
# and formatting output for a console or Telegram integration. 
# Key functionalities include refreshing the monitor data, saving results, 
# and managing display options based on user-defined settings.

class MarketMonitor(SingletonMixin, metaclass=SingletonType):
    def __init__(self,monitors=[], maxNumResultsPerRow=3,maxNumColsInEachResult=6,maxNumRowsInEachResult=10,maxNumResultRowsInMonitor=2,pinnedIntervalWaitSeconds=30,alertOptions=[]):
        super(MarketMonitor, self).__init__()
        if monitors is not None and len(monitors) > 0:
            
            self.monitors = monitors[:maxNumResultRowsInMonitor*maxNumResultsPerRow]
            self.monitorIndex = 0
            self.monitorPositions = {}
            self.monitorResultStocks = {}
            self.alertOptions = alertOptions
            self.hiddenColumns = ""
            self.alertStocks = []
            self.pinnedIntervalWaitSeconds = pinnedIntervalWaitSeconds
            # self.monitorNames = {}
            # We are going to present the dataframes in a 3x3 matrix with limited set of columns
            rowIndex = 0
            colIndex = 0
            self.maxNumResultRowsInMonitor = maxNumResultRowsInMonitor
            self.maxNumRowsInEachResult = maxNumRowsInEachResult
            self.maxNumColsInEachResult = maxNumColsInEachResult
            self.maxNumResultsPerRow = maxNumResultsPerRow
            maxColIndex = self.maxNumColsInEachResult * self.maxNumResultsPerRow - 1
            self.lines = 0
            for monitorKey in self.monitors:
                self.monitorPositions[monitorKey] = [rowIndex,colIndex]
                # self.monitorNames[monitorKey] = ""
                colIndex += self.maxNumColsInEachResult
                if colIndex > maxColIndex:
                    colIndex = 0
                    rowIndex += self.maxNumRowsInEachResult
            columns = []
            colNameIndex = 0
            maxColIndex = min(maxColIndex,len(self.monitorPositions)*self.maxNumColsInEachResult -1)
            while colNameIndex <= maxColIndex:
                columns.append(f"A{colNameIndex +1}")
                colNameIndex += 1
            self.monitor_df = pd.DataFrame(columns=columns)
            self.isPinnedSingleMonitorMode = len(self.monitorPositions.keys()) == 1

    def currentMonitorOption(self):
        try:
            option = None
            maxIndex = len(self.monitors) -1
            option = str(self.monitors[self.monitorIndex:self.monitorIndex+1][0])
            self.monitorIndex += 1
            if self.monitorIndex > maxIndex:
                self.monitorIndex = 0
        except: # pragma: no cover
            pass
        return option

    def saveMonitorResultStocks(self, results_df):
        if results_df is None or results_df.empty:
            prevOutput_results = "NONE"
        else:
            prevOutput_results = results_df[~results_df.index.duplicated(keep='first')]
            prevOutput_results = prevOutput_results.index
            # # Maybe the index is an int ?
            # prevOutput_results = [str(stock) for stock in prevOutput_results]
            try:
                lastSavedResults = self.monitorResultStocks[str(self.monitorIndex)]
                if lastSavedResults is not None and len(lastSavedResults) > 0:
                    lastSavedResults = lastSavedResults.split(",")
                    s = set(lastSavedResults)
                    self.alertStocks = [x for x in prevOutput_results if x not in s]
                else:
                    self.alertStocks = []
            except: # pragma: no cover
                pass
            prevOutput_results = ",".join(prevOutput_results)
        self.monitorResultStocks[str(self.monitorIndex)] = prevOutput_results

    def refresh(self, screen_df:pd.DataFrame=None, screenOptions=None, chosenMenu="", dbTimestamp="", telegram=False):
        highlightRows = []
        highlightCols = []
        if screen_df is None or screen_df.empty or screenOptions is None:
            return
        screen_monitor_df = screen_df.copy()
        monitorPosition = self.monitorPositions.get(screenOptions)

        from pkscreener.classes import Utility

        if self.isPinnedSingleMonitorMode:
            screen_monitor_df = screen_monitor_df[screen_monitor_df.columns[:14]]
            self.monitor_df = screen_monitor_df
        else:
            screen_monitor_df.reset_index(inplace=True)
            screen_monitor_df = screen_monitor_df[["Stock", "LTP", "%Chng","52Wk-H","RSI/i" if "RSI/i" in screen_monitor_df.columns else "RSI","Volume"]].head(self.maxNumRowsInEachResult-1)
            # Import Utility here since Utility has dependency on PKScheduler which in turn has dependency on 
            # multiprocessing, which behaves erratically if imported at the top.
            screen_monitor_df.loc[:, "%Chng"] = screen_monitor_df.loc[:, "%Chng"].astype(str).apply(
                        lambda x: Utility.tools.roundOff(str(x).split("% (")[0] + colorText.END,0)
                    )
            screen_monitor_df.loc[:, "52Wk-H"] = screen_monitor_df.loc[:, "52Wk-H"].astype(str).apply(
                lambda x: Utility.tools.roundOff(x,0)
            )
            screen_monitor_df.loc[:, "Volume"] = screen_monitor_df.loc[:, "Volume"].astype(str).apply(
                lambda x: Utility.tools.roundOff(x,0)
            )
            screen_monitor_df.rename(columns={"%Chng": "Ch%","Volume":"Vol","52Wk-H":"52WkH", "RSI":"RSI/i"}, inplace=True)
            telegram_df = self.updateDataFrameForTelegramMode(telegram, screen_monitor_df)
        
        
        if monitorPosition is not None:
            startRowIndex, startColIndex = monitorPosition
            if not self.monitor_df.empty:
                OutputControls().moveCursorUpLines(self.lines)
            if not self.isPinnedSingleMonitorMode:
                firstColIndex = startColIndex
                rowIndex = 0
                colIndex = 0
                highlightRows = [startRowIndex]
                highlightCols = []
                while rowIndex <= len(screen_monitor_df):
                    for col in screen_monitor_df.columns:
                        if rowIndex == 0:
                            # Column names to be repeated for each refresh in respective headers
                            cleanedScreenOptions = screenOptions.replace(":D","")
                            widgetHeader = self.getScanOptionName(cleanedScreenOptions)
                            if len(widgetHeader) <= 0:
                                if cleanedScreenOptions.startswith("|"):
                                    cleanedScreenOptions = cleanedScreenOptions.replace("|","")
                                    pipedFrom = ""
                                    if cleanedScreenOptions.startswith("{"):
                                        pipedFrom = cleanedScreenOptions.split("}")[0] + "}:"
                                    cleanedScreenOptions = pipedFrom + ":".join(cleanedScreenOptions.split(":")[2:])
                                    cleanedScreenOptions = cleanedScreenOptions.replace(">X:0:","")
                                widgetHeader = ":".join(cleanedScreenOptions.split(":")[:4])
                                if "i " in screenOptions:
                                    widgetHeader = f'{":".join(widgetHeader.split(":")[:3])}:i:{cleanedScreenOptions.split("i ")[-1]}'
                            self.monitor_df.loc[startRowIndex,[f"A{startColIndex+1}"]] = colorText.HEAD+(widgetHeader if startColIndex==firstColIndex else col)+colorText.END
                            highlightCols.append(startColIndex)
                        else:
                            if colIndex == 0:
                                stockNameDecorated = screen_monitor_df.iloc[rowIndex-1,colIndex]
                                stockName = Utility.tools.stockNameFromDecoratedName(stockNameDecorated)
                                stockName = (f"{colorText.BOLD}{colorText.WHITE_FG_BRED_BG}{stockNameDecorated}{colorText.END}") if stockName in self.alertStocks else stockNameDecorated
                                self.monitor_df.loc[startRowIndex, [f"A{startColIndex+1}"]] = stockName
                            else:
                                self.monitor_df.loc[startRowIndex, [f"A{startColIndex+1}"]] = screen_monitor_df.iloc[rowIndex-1,colIndex]
                            colIndex += 1
                        startColIndex += 1
                    _, startColIndex= monitorPosition
                    rowIndex += 1
                    colIndex = 0
                    highlightRows.append(startRowIndex+1)
                    startRowIndex += 1
            else:
                stocks = list(self.monitor_df.index)
                updatedStocks = []
                for stock in stocks:
                    stockName = Utility.tools.stockNameFromDecoratedName(stock)
                    stockName = (f"{colorText.BOLD}{colorText.WHITE_FG_BRED_BG}{stock}{colorText.END}") if stockName in self.alertStocks else stock
                    updatedStocks.append(stockName)
                self.monitor_df.reset_index(inplace=True)
                self.monitor_df["Stock"] = updatedStocks
                self.monitor_df.set_index("Stock",inplace=True)

        self.monitor_df = self.monitor_df.replace(np.nan, "-", regex=True)
        latestScanMenuOption = f"  [+] {dbTimestamp} (Dashboard) > " + f"{chosenMenu[:190]} [{screenOptions}]"
        OutputControls().printOutput(
            colorText.FAIL
            + latestScanMenuOption[:200]
            + colorText.END
            , enableMultipleLineOutput=True
        )
        tabulated_results = colorText.miniTabulator().tabulate(
            self.monitor_df, tablefmt=colorText.No_Pad_GridFormat,
            headers="keys" if self.isPinnedSingleMonitorMode else (),
            highlightCharacter=colorText.HEAD+"="+colorText.END,
            showindex=self.isPinnedSingleMonitorMode,
            highlightedRows=highlightRows,
            highlightedColumns=highlightCols,
            maxcolwidths=Utility.tools.getMaxColumnWidths(self.monitor_df)
        )
        console_results = ""
        if self.isPinnedSingleMonitorMode:
            copyScreenResults = self.monitor_df.copy()
            hiddenColumns = self.hiddenColumns.split(",")
            for col in copyScreenResults.columns:
                if col in hiddenColumns:
                    copyScreenResults.drop(col, axis=1, inplace=True, errors="ignore")
            try:
                console_results = colorText.miniTabulator().tabulate(
                        copyScreenResults, headers="keys", tablefmt=colorText.No_Pad_GridFormat,
                        maxcolwidths=Utility.tools.getMaxColumnWidths(copyScreenResults)
                    )
            except: # pragma: no cover
                console_results = tabulated_results
        numRecords = len(tabulated_results.splitlines())
        self.lines = numRecords #+ 1 #(1 if len(self.monitorResultStocks.keys()) <= self.maxNumColsInEachResult else 0) # 1 for the progress bar at the bottom and 1 for the chosenMenu option
        OutputControls().printOutput(tabulated_results if not self.isPinnedSingleMonitorMode else console_results, enableMultipleLineOutput=True)
        
        if not telegram and ((screenOptions in self.alertOptions and numRecords > 1) or len(self.alertStocks) > 0): # Alert conditions met? Sound alert!
            Utility.tools.alertSound(beeps=5)
        if not self.isPinnedSingleMonitorMode:
            if telegram:
                self.updateIfRunningInTelegramBotMode(screenOptions, chosenMenu, dbTimestamp, telegram, telegram_df)
        else:
            sleep(self.pinnedIntervalWaitSeconds)

    def updateDataFrameForTelegramMode(self, telegram, screen_monitor_df):
        telegram_df = None
        if telegram:
            telegram_df = screen_monitor_df[["Stock", "LTP", "Ch%", "Vol"]]
            try:
                telegram_df.loc[:, "Stock"] = telegram_df.loc[:, "Stock"].apply(
                    lambda x: x.split('\x1b')[3].replace('\\','') if 'http' in x else x
                )
                cols = ["LTP", "Ch%", "Vol"]
                for col in cols:
                    telegram_df.loc[:, col] = telegram_df.loc[:, col].apply(
                        lambda x: x.replace(colorText.FAIL,"").replace(colorText.GREEN,"").replace(colorText.WARN,"").replace(colorText.BOLD,"").replace(colorText.END,"")
                    )
                telegram_df.loc[:, "LTP"] = telegram_df.loc[:, "LTP"].apply(
                    lambda x: str(int(round(float(x),0)))
                )
                telegram_df.loc[:, "Ch%"] = telegram_df.loc[:, "Ch%"].apply(
                    lambda x: f'{int(round(float(x.replace("%","")),0))}%'
                )
                telegram_df.loc[:, "Vol"] = telegram_df.loc[:, "Vol"].apply(
                    lambda x: f'{int(round(float(x.replace("x","")),0))}x'
                )
                with SuppressOutput(suppress_stderr=True, suppress_stdout=True):
                    for col in telegram_df.columns:
                        telegram_df[col] = telegram_df[col].astype(str)
            except: # pragma: no cover
                pass
        return telegram_df

    def updateIfRunningInTelegramBotMode(self, screenOptions, chosenMenu, dbTimestamp, telegram, telegram_df):
        if telegram and telegram_df is not None:
            STD_ENCODING=sys.stdout.encoding if sys.stdout is not None else 'utf-8'
            
            telegram_df_tabulated = colorText.miniTabulator().tabulate(
                            telegram_df,
                            headers="keys",
                            tablefmt=colorText.No_Pad_GridFormat,
                            showindex=False,
                            maxcolwidths=[None,None,4,3]
                        ).encode("utf-8").decode(STD_ENCODING).replace("-K-----S-----C-----R","-K-----S----C---R").replace("%  ","% ").replace("=K=====S=====C=====R","=K=====S====C===R").replace("Vol  |","Vol|").replace("x  ","x")
            telegram_df_tabulated = telegram_df_tabulated.replace("-E-----N-----E-----R","-E-----N----E---R").replace("=E=====N=====E=====R","=E=====N====E===R")
            choiceSegments = chosenMenu.split(">")
            optionName = self.getScanOptionName(screenOptions)
            chosenMenu = f"{choiceSegments[-2]}>{choiceSegments[-1]}" if (len(choiceSegments)>=4 or len(choiceSegments[-1]) <= 10) else f"{choiceSegments[-1]}"
            result_output = f"Latest data as of:{dbTimestamp}\n<b>{optionName}{chosenMenu}</b> [{screenOptions}]\n<pre>{telegram_df_tabulated}</pre>"
            try:
                filePath = os.path.join(Archiver.get_user_data_dir(), f"monitor_outputs_{self.monitorIndex}.txt")
                f = open(filePath, "w")
                f.write(result_output)
                f.close()
            except: # pragma: no cover
                pass

    def getScanOptionName(self, screenOptions):
        from pkscreener.classes.MenuOptions import PREDEFINED_SCAN_MENU_VALUES
        if screenOptions is None:
            return ""
        choices = f"--systemlaunched -a y -e -o '{screenOptions.replace('C:','X:').replace('D:','')}'"
        indexNum = -1
        try:
            indexNum = PREDEFINED_SCAN_MENU_VALUES.index(choices)
        except: # pragma: no cover
            pass
        optionName = ""
        if indexNum >= 0:
            optionName = f"{('P_1_'+str(indexNum +1)+':') if '>|' in choices else optionName}"
        return optionName