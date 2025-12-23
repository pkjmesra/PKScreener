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
import platform
import pandas as pd

from PKDevTools.classes.OutputControls import OutputControls
from PKDevTools.classes.ColorText import colorText
from PKDevTools.classes.log import default_logger
from PKDevTools.classes.Utils import random_user_agent

from pkscreener.classes import VERSION, Changelog, Utility
from pkscreener.classes.ArtTexts import getArtText
from pkscreener.classes.Utility import marketStatus, STD_ENCODING, lastScreened
import pkscreener.classes.Fetcher as Fetcher


class PKConsoleTools:
    """
    Utility class for managing console-related operations.
    
    This class provides static methods for:
    - Screen clearing and terminal management
    - Developer information display
    - Screened results persistence (save/load)
    - Backtest output formatting
    """
    
    # Singleton instance of the stock data fetcher
    fetcher = Fetcher.screenerStockDataFetcher()
    
    # ========================================================================
    # Screen Management Methods
    # ========================================================================
    
    @staticmethod
    def clearScreen(userArgs=None, clearAlways=False, forceTop=False):
        """
        Clear the console screen and optionally display the application header.
        
        Args:
            userArgs: Command-line arguments object containing runtime flags
            clearAlways: Force screen clear regardless of other conditions
            forceTop: Force cursor to move to the top of the screen
            
        Note:
            - Returns early if running in 'timeit' mode
            - Returns early if running as RUNNER or in production build mode
            - Returns early if running intraday analysis
        """
        # Skip clearing in timing/benchmark mode
        if 'timeit' in os.environ.keys():
            return
            
        # Skip clearing in RUNNER mode or production builds
        if "RUNNER" in os.environ.keys() or (userArgs is not None and userArgs.prodbuild):
            if userArgs is not None and userArgs.v:
                os.environ["RUNNER"] = "LOCAL_RUN_SCANNER"
            return
            
        # Skip clearing during intraday analysis
        if userArgs is not None and userArgs.runintradayanalysis:
            return
            
        if clearAlways or OutputControls().enableMultipleLineOutput:
            PKConsoleTools._setTerminalColors()
            if clearAlways:
                PKConsoleTools._clearTerminal()
            OutputControls().moveCursorToStartPosition()
            
        try:
            forceTop = OutputControls().enableMultipleLineOutput
            if forceTop and OutputControls().lines == 0:
                OutputControls().lines = 9
                OutputControls().moveCursorToStartPosition()
                
            if clearAlways or OutputControls().enableMultipleLineOutput:
                art = colorText.GREEN + f"{getArtText()}\n" + colorText.END + f"{marketStatus()}"
                OutputControls().printOutput(
                    art.encode('utf-8').decode(STD_ENCODING),
                    enableMultipleLineOutput=True
                )
        except KeyboardInterrupt:
            raise KeyboardInterrupt
        except Exception as e:
            default_logger().debug(e, exc_info=True)
    
    @staticmethod
    def _setTerminalColors():
        """Set terminal background and foreground colors based on platform."""
        if platform.system() == "Windows":
            try:
                os.system('color 0f')  # Black background, white foreground
            except:
                pass
        elif "Darwin" not in platform.system():
            try:
                os.system('setterm -background black -foreground white -store')
            except:
                pass
    
    @staticmethod
    def _clearTerminal():
        """Clear the terminal screen based on the current platform."""
        if platform.system() == "Windows":
            os.system("cls")
        else:
            os.system("clear")
    
    # ========================================================================
    # Developer Information Methods
    # ========================================================================
    
    @staticmethod
    def showDevInfo(defaultAnswer=None):
        """
        Display developer information, version, and download statistics.
        
        Args:
            defaultAnswer: If provided, skip the user prompt at the end
            
        Returns:
            str: Formatted string containing all developer information
        """
        OutputControls().printOutput("\n" + Changelog.changelog())
        
        # Build information strings
        devInfo = "\n[👨🏻‍💻] Developer: PK (PKScreener) 🇮🇳"
        versionInfo = "[🚦] Version: %s" % VERSION
        homePage = (
            "[🏡] Home Page: https://github.com/pkjmesra/PKScreener\n"
            "[🤖] Telegram Bot:@nse_pkscreener_bot\n"
            "[🚨] Channel:https://t.me/PKScreener\n"
            "[💬] Discussions:https://t.me/PKScreeners"
        )
        issuesInfo = "[🚩] Read/Post Issues here: https://github.com/pkjmesra/PKScreener/issues"
        communityInfo = "[📢] Join Community Discussions: https://github.com/pkjmesra/PKScreener/discussions"
        latestInfo = "[⏰] Download latest software from https://github.com/pkjmesra/PKScreener/releases/latest"
        freeInfo = "[💰] PKScreener had been free for a long time"
        donationInfo = (
            ", but owing to cost/budgeting issues, only a basic set of features will always "
            "remain free for everyone. Consider donating to help cover the basic server costs "
            "or subscribe to premium.\n[💸] Please donate whatever you can: PKScreener@APL using "
            "UPI(India) or https://github.com/sponsors/pkjmesra 🙏🏻"
        )
        
        # Fetch download statistics
        totalDownloads = PKConsoleTools._fetchDownloadStats()
        downloadsInfo = f"[🔥] Total Downloads: {totalDownloads}"
        
        # Print colored output
        OutputControls().printOutput(colorText.WARN + devInfo + colorText.END)
        OutputControls().printOutput(colorText.WARN + versionInfo + colorText.END)
        OutputControls().printOutput(colorText.GREEN + downloadsInfo + colorText.END)
        OutputControls().printOutput(homePage + colorText.END)
        OutputControls().printOutput(colorText.FAIL + issuesInfo + colorText.END)
        OutputControls().printOutput(colorText.GREEN + communityInfo + colorText.END)
        OutputControls().printOutput(colorText.BLUE + latestInfo + colorText.END)
        OutputControls().printOutput(
            colorText.GREEN + freeInfo + colorText.END +
            colorText.FAIL + donationInfo + colorText.END
        )
        
        if defaultAnswer is None:
            OutputControls().takeUserInput(
                colorText.FAIL + "  [+] Press <Enter> to continue!" + colorText.END
            )
            
        return (
            f"\n{Changelog.changelog()}\n\n{devInfo}\n{versionInfo}\n\n"
            f"{downloadsInfo}\n{homePage}\n{issuesInfo}\n{communityInfo}\n"
            f"{latestInfo}\n{freeInfo}{donationInfo}"
        )
    
    @staticmethod
    def _fetchDownloadStats():
        """
        Fetch total download statistics from PyPI.
        
        Returns:
            str: Total download count (e.g., "200k+") or actual count if available
        """
        totalDownloads = "200k+"
        try:
            resp = PKConsoleTools.fetcher.fetchURL(
                url="https://static.pepy.tech/badge/pkscreener",
                headers={'user-agent': f'{random_user_agent()}'},
                timeout=2
            )
            if resp is not None and resp.status_code == 200:
                totalDownloads = resp.text.split("</text>")[-2].split(">")[-1]
        except Exception:
            pass
        return totalDownloads
    
    # ========================================================================
    # Results Persistence Methods
    # ========================================================================
    
    @staticmethod
    def setLastScreenedResults(df, df_save=None, choices=None):
        """
        Save the most recently screened results to disk.
        
        This method persists results in two formats:
        1. A pickle file containing the full DataFrame
        2. A text file (per scan choice) containing stock symbols
        
        Args:
            df: The screened results DataFrame
            df_save: Optional DataFrame to save (may differ from df)
            choices: The scan choices string (used for filename)
        """
        try:
            # Ensure output directory exists
            outputFolder = os.path.join(os.getcwd(), 'actions-data-scan')
            if not os.path.isdir(outputFolder):
                os.makedirs(
                    os.path.dirname(os.path.join(os.getcwd(), f"actions-data-scan{os.sep}")),
                    exist_ok=True
                )
            
            fileName = os.path.join(outputFolder, f"{choices}.txt")
            items = []
            needsWriting = False
            finalStocks = ""
            
            # Load existing stocks if file exists
            if os.path.isfile(fileName):
                if df is not None and len(df) > 0:
                    items = PKConsoleTools._loadExistingStocks(fileName)
                    stockList = sorted(list(filter(None, list(set(items)))))
                    finalStocks = ",".join(stockList)
            else:
                needsWriting = True
            
            # Process and save new results
            if df is not None and len(df) > 0:
                with pd.option_context('mode.chained_assignment', None):
                    df.sort_values(by=["Stock"], ascending=True, inplace=True)
                    df.to_pickle(lastScreened)
                    
                    if choices is not None and df_save is not None:
                        newStocks = PKConsoleTools._extractStockSymbols(df_save)
                        items.extend(newStocks)
                        stockList = sorted(list(filter(None, list(set(items)))))
                        finalStocks = ",".join(stockList)
                        needsWriting = True
            
            # Write to file if needed
            if needsWriting:
                with open(fileName, 'w') as f:
                    f.write(finalStocks)
                    
        except IOError as e:
            default_logger().debug(e, exc_info=True)
            OutputControls().printOutput(
                colorText.FAIL +
                f"{e}\n  [+] Failed to save recently screened result table on disk! Skipping.." +
                colorText.END
            )
        except KeyboardInterrupt:
            raise KeyboardInterrupt
        except Exception as e:
            default_logger().debug(e, exc_info=True)
    
    @staticmethod
    def _loadExistingStocks(fileName):
        """Load existing stock symbols from a file."""
        with open(fileName, 'r') as fe:
            stocks = fe.read()
            return stocks.replace("\n", "").replace("\"", "").split(",")
    
    @staticmethod
    def _extractStockSymbols(df_save):
        """Extract stock symbols from a DataFrame."""
        df_s = df_save.copy()
        df_s.reset_index(inplace=True)
        return df_s["Stock"].to_json(
            orient='records', lines=True
        ).replace("\n", "").replace("\"", "").split(",")
    
    @staticmethod
    def getLastScreenedResults(defaultAnswer=None):
        """
        Load and display the most recently screened results from disk.
        
        Args:
            defaultAnswer: If provided, skip the user prompt at the end
        """
        try:
            df = pd.read_pickle(lastScreened)
            if df is not None and len(df) > 0:
                OutputControls().printOutput(
                    colorText.GREEN +
                    "\n  [+] Showing recently screened results..\n" +
                    colorText.END
                )
                
                # Sort by volume if available
                sortColumn = "volume" if "volume" in df.keys() else df.keys()[0]
                df.sort_values(by=[sortColumn], ascending=False, inplace=True)
                
                OutputControls().printOutput(
                    colorText.miniTabulator().tabulate(
                        df,
                        headers="keys",
                        tablefmt=colorText.No_Pad_GridFormat,
                        maxcolwidths=Utility.tools.getMaxColumnWidths(df)
                    ).encode("utf-8").decode(STD_ENCODING)
                )
                
                OutputControls().printOutput(
                    colorText.WARN +
                    "  [+] Note: Trend calculation is based on number of recent days "
                    "to screen as per your configuration." +
                    colorText.END
                )
            else:
                OutputControls().printOutput("Nothing to show here!")
                
        except FileNotFoundError as e:
            default_logger().debug(e, exc_info=True)
            OutputControls().printOutput(
                colorText.FAIL +
                "  [+] Failed to load recently screened result table from disk! Skipping.." +
                colorText.END
            )
        
        if defaultAnswer is None:
            OutputControls().takeUserInput(
                colorText.GREEN +
                "  [+] Press <Enter> to continue.." +
                colorText.END
            )
    
    # ========================================================================
    # Backtest Formatting Methods
    # ========================================================================
    
    @staticmethod
    def formattedBacktestOutput(outcome, pnlStats=False, htmlOutput=True):
        """
        Format backtest outcome values with appropriate colors.
        
        Args:
            outcome: The numeric outcome value (percentage)
            pnlStats: Whether this is a P&L statistic (affects coloring logic)
            htmlOutput: Whether output is for HTML (affects threshold colors)
            
        Returns:
            str: Colored string representation of the outcome
        """
        if not pnlStats:
            if htmlOutput:
                if outcome >= 80:
                    return f'{colorText.GREEN}{"%.2f%%" % outcome}{colorText.END}'
                if outcome >= 60:
                    return f'{colorText.WARN}{"%.2f%%" % outcome}{colorText.END}'
                return f'{colorText.FAIL}{"%.2f%%" % outcome}{colorText.END}'
            else:
                return f'{colorText.GREEN}{"%.2f%%" % outcome}{colorText.END}'
        else:
            if outcome >= 0:
                return f'{colorText.GREEN}{"%.2f%%" % outcome}{colorText.END}'
            return f'{colorText.FAIL}{"%.2f%%" % outcome}{colorText.END}'
    
    @staticmethod
    def getFormattedBacktestSummary(x, pnlStats=False, columnName=None):
        """
        Format a backtest summary value with appropriate styling.
        
        Args:
            x: The value to format (may contain '%')
            pnlStats: Whether this is a P&L statistic
            columnName: The column name (affects formatting for specific columns)
            
        Returns:
            The formatted value or original if no formatting needed
        """
        if x is not None and "%" in str(x):
            values = x.split("%")
            if (
                len(values) == 2 and
                columnName is not None and
                ("-Pd" in columnName or "Overall" in columnName)
            ):
                return "{0}{1}".format(
                    PKConsoleTools.formattedBacktestOutput(
                        float(values[0]),
                        pnlStats=pnlStats,
                        htmlOutput=False
                    ),
                    values[1],
                )
        return x
