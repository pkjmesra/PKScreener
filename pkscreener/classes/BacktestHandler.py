#!/usr/bin/env python
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
import urllib

import numpy as np
import pandas as pd

from PKDevTools.classes.ColorText import colorText
from PKDevTools.classes.OutputControls import OutputControls
from PKDevTools.classes.PKDateUtilities import PKDateUtilities
from PKDevTools.classes.log import default_logger
from PKDevTools.classes.Committer import Committer
from PKDevTools.classes import Archiver

from pkscreener.classes import Utility, ConsoleUtility
from pkscreener.classes.Utility import STD_ENCODING
from pkscreener.classes.Backtest import backtest, backtestSummary
from pkscreener.classes import PortfolioXRay
from pkscreener.classes.PKScanRunner import PKScanRunner
from pkscreener.classes.AssetsManager import PKAssetsManager


class BacktestHandler:
    """
    Handles all backtesting operations for the PKScreener application.
    Includes methods for running backtests, processing results, and generating reports.
    """
    
    def __init__(self, config_manager, user_passed_args=None):
        """
        Initialize BacktestHandler.
        
        Args:
            config_manager: Configuration manager instance
            user_passed_args: User passed arguments
        """
        self.config_manager = config_manager
        self.user_passed_args = user_passed_args
        self.elapsed_time = 0
        
    def get_historical_days(self, num_stocks, testing):
        """
        Get the number of historical days for backtesting.
        
        Args:
            num_stocks: Number of stocks to process
            testing: Whether in testing mode
            
        Returns:
            int: Number of historical days
        """
        return 2 if testing else self.config_manager.backtestPeriod
    
    def take_backtest_inputs(self, menu_option=None, index_option=None, 
                             execute_option=None, backtest_period=0):
        """
        Take backtest inputs from user.
        
        Args:
            menu_option: Menu option selected
            index_option: Index option selected
            execute_option: Execute option selected
            backtest_period: Pre-set backtest period
            
        Returns:
            tuple: (index_option, execute_option, backtest_period)
        """
        g10k = '"Growth of 10k"'
        OutputControls().printOutput(
            colorText.GREEN
            + f"  [+] For {g10k if menu_option == 'G' else 'backtesting'}, "
            "you can choose from (1,2,3,4,5,10,15,22,30) or any other custom periods (< 1y)."
        )
        
        try:
            if backtest_period == 0:
                backtest_period = int(
                    input(
                        colorText.FAIL
                        + f"  [+] Enter {g10k if menu_option == 'G' else 'backtesting'} period "
                        f"(Default is {15 if menu_option == 'G' else 30} [days]): "
                    )
                )
        except Exception as e:
            default_logger().debug(e, exc_info=True)
            
        if backtest_period == 0:
            backtest_period = 3 if menu_option == "G" else 30
            
        return index_option, execute_option, backtest_period
    
    def update_backtest_results(self, backtest_period, start_time, result, 
                                sample_days, backtest_df, selected_choice):
        """
        Update backtest results with new data.
        
        Args:
            backtest_period: Period for backtesting
            start_time: Start time of the backtest
            result: Result tuple from screening
            sample_days: Number of sample days
            backtest_df: Existing backtest dataframe
            selected_choice: Selected choice dictionary
            
        Returns:
            pd.DataFrame: Updated backtest dataframe
        """
        import time
        
        sell_signal = (
            str(selected_choice["2"]) in ["6", "7"] and str(selected_choice["3"]) in ["2"]
        ) or selected_choice["2"] in ["15", "16", "19", "25"]
        
        backtest_df = backtest(
            result[3],
            result[2],
            result[1],
            result[0],
            backtest_period,
            sample_days,
            backtest_df,
            sell_signal,
        )
        
        self.elapsed_time = time.time() - start_time
        return backtest_df
    
    def get_summary_correctness_of_strategy(self, result_df, summary_required=True):
        """
        Get summary of correctness for a strategy from historical data.
        
        Args:
            result_df: Results dataframe
            summary_required: Whether to include summary
            
        Returns:
            tuple: (summary_df, detail_df)
        """
        summary_df = None
        detail_df = None
        
        try:
            if result_df is None or len(result_df) == 0:
                return None, None
                
            results = result_df.copy()
            
            if summary_required:
                _, report_name_summary = self.get_backtest_report_filename(optional_name="Summary")
                dfs = pd.read_html(
                    f"https://pkjmesra.github.io/PKScreener/Backtest-Reports/"
                    f"{report_name_summary.replace('_X_', '_B_').replace('_G_', '_B_').replace('_S_', '_B_')}",
                    encoding="UTF-8",
                    attrs={'id': 'resultsTable'}
                )
                
            _, report_name_detail = self.get_backtest_report_filename()
            dfd = pd.read_html(
                f"https://pkjmesra.github.io/PKScreener/Backtest-Reports/"
                f"{report_name_detail.replace('_X_', '_B_').replace('_G_', '_B_').replace('_S_', '_B_')}",
                encoding="UTF-8",
                attrs={'id': 'resultsTable'}
            )
            
            if summary_required and dfs is not None and len(dfs) > 0:
                df = dfs[0]
                summary_df = df[df["Stock"] == "SUMMARY"]
                
                for col in summary_df.columns:
                    summary_df.loc[:, col] = summary_df.loc[:, col].apply(
                        lambda x: ConsoleUtility.PKConsoleTools.getFormattedBacktestSummary(
                            x, columnName=col
                        )
                    )
                summary_df = summary_df.replace(np.nan, "", regex=True)
                
            if dfd is not None and len(dfd) > 0:
                df = dfd[0]
                results.reset_index(inplace=True)
                detail_df = df[df["Stock"].isin(results["Stock"])]
                
                for col in detail_df.columns:
                    detail_df.loc[:, col] = detail_df.loc[:, col].apply(
                        lambda x: ConsoleUtility.PKConsoleTools.getFormattedBacktestSummary(
                            x, pnlStats=True, columnName=col
                        )
                    )
                detail_df = detail_df.replace(np.nan, "", regex=True)
                detail_df.loc[:, "volume"] = detail_df.loc[:, "volume"].apply(
                    lambda x: Utility.tools.formatRatio(x, self.config_manager.volumeRatio)
                )
                detail_df.sort_values(
                    ["Stock", "Date"], ascending=[True, False], inplace=True
                )
                detail_df.rename(
                    columns={"LTP": "LTP on Date"},
                    inplace=True,
                )
        except urllib.error.HTTPError as e:
            if "HTTP Error 404" in str(e):
                pass
            else:
                default_logger().debug(e, exc_info=True)
        except Exception as e:
            default_logger().debug(e, exc_info=True)
            
        return summary_df, detail_df
    
    def tabulate_backtest_results(self, save_results, max_allowed=0, force=False):
        """
        Tabulate backtest results for display.
        
        Args:
            save_results: Save results dataframe
            max_allowed: Maximum allowed results to show
            force: Whether to force tabulation
            
        Returns:
            tuple: (tabulated_backtest_summary, tabulated_backtest_detail)
        """
        if "PKDevTools_Default_Log_Level" not in os.environ.keys():
            if ("RUNNER" not in os.environ.keys()) or ("RUNNER" in os.environ.keys() and not force):
                return None, None
                
        if not self.config_manager.showPastStrategyData:
            return None, None
            
        tabulated_backtest_summary = ""
        tabulated_backtest_detail = ""
        
        summary_df, detail_df = self.get_summary_correctness_of_strategy(save_results)
        
        if summary_df is not None and len(summary_df) > 0:
            tabulated_backtest_summary = colorText.miniTabulator().tabulate(
                summary_df,
                headers="keys",
                tablefmt=colorText.No_Pad_GridFormat,
                showindex=False,
                maxcolwidths=Utility.tools.getMaxColumnWidths(summary_df)
            ).encode("utf-8").decode(STD_ENCODING)
            
        if detail_df is not None and len(detail_df) > 0:
            if max_allowed != 0 and len(detail_df) > 2 * max_allowed:
                detail_df = detail_df.head(2 * max_allowed)
                
            tabulated_backtest_detail = colorText.miniTabulator().tabulate(
                detail_df,
                headers="keys",
                tablefmt=colorText.No_Pad_GridFormat,
                showindex=False,
                maxcolwidths=Utility.tools.getMaxColumnWidths(detail_df)
            ).encode("utf-8").decode(STD_ENCODING)
            
        if tabulated_backtest_summary != "":
            OutputControls().printOutput(
                colorText.FAIL
                + "\n  [+] For chosen scan, summary of correctness from past: "
                "[Example, 70% of (100) under 1-Pd, means out of 100 stocks that were "
                "in the scan result in the past, 70% of them gained next day.)"
                + colorText.END
            )
            OutputControls().printOutput(tabulated_backtest_summary)
            
        if tabulated_backtest_detail != "":
            OutputControls().printOutput(
                colorText.FAIL
                + "\n  [+] 1 to 30 period gain/loss % on respective date for "
                "matching stocks from earlier predictions:"
                "[Example, 5% under 1-Pd, means the stock price actually gained 5% "
                "the next day from given date.]"
                + colorText.END
            )
            OutputControls().printOutput(tabulated_backtest_detail)
            
        return tabulated_backtest_summary, tabulated_backtest_detail
    
    def show_backtest_results(self, backtest_df, sort_key="Stock", 
                              optional_name="backtest_result", 
                              menu_choice_hierarchy="", selected_choice=None, choices=None):
        """
        Show and save backtest results.
        
        Args:
            backtest_df: Backtest results dataframe
            sort_key: Column to sort by
            optional_name: Name suffix for the file
            menu_choice_hierarchy: Menu choice hierarchy string
            selected_choice: Selected choice dictionary
            choices: Pre-formatted choices string
        """
        pd.set_option("display.max_rows", 800)
        
        if backtest_df is None or backtest_df.empty or len(backtest_df) < 1:
            OutputControls().printOutput(
                "Empty backtest dataframe encountered! Cannot generate the backtest report"
            )
            return
            
        backtest_df.drop_duplicates(inplace=True)
        
        summary_text = (
            f"Auto-generated in {round(self.elapsed_time, 2)} sec. as of "
            f"{PKDateUtilities.currentDateTime().strftime('%d-%m-%y %H:%M:%S IST')}\n"
            f"{menu_choice_hierarchy.replace('Backtests', 'Growth of 10K' if optional_name == 'Insights' else 'Backtests')}"
        )
        
        last_summary_row = None
        
        if "Summary" not in optional_name:
            if sort_key is not None and len(sort_key) > 0:
                backtest_df.sort_values(by=[sort_key], ascending=False, inplace=True)
        else:
            last_row = backtest_df.iloc[-1, :]
            if last_row.iloc[0] == "SUMMARY":
                last_summary_row = pd.DataFrame(last_row).transpose()
                last_summary_row.set_index("Stock", inplace=True)
                last_summary_row = last_summary_row.iloc[:, last_summary_row.columns != "Stock"]
                
            if "Insights" in optional_name:
                summary_text = f"{summary_text}\nActual returns at a portfolio level with 1-stock each based on selected scan-parameters:"
            else:
                summary_text = f"{summary_text}\nOverall Summary of (correctness of) Strategy Prediction Positive outcomes:"
                
        tabulated_text = ""
        
        if backtest_df is not None and len(backtest_df) > 0:
            try:
                tabulated_text = colorText.miniTabulator().tabulate(
                    backtest_df,
                    headers="keys",
                    tablefmt=colorText.No_Pad_GridFormat,
                    showindex=False,
                    maxcolwidths=Utility.tools.getMaxColumnWidths(backtest_df)
                ).encode("utf-8").decode(STD_ENCODING)
            except ValueError:
                OutputControls().printOutput(
                    "ValueError! Going ahead without any column width restrictions!"
                )
                tabulated_text = colorText.miniTabulator().tabulate(
                    backtest_df,
                    headers="keys",
                    tablefmt=colorText.No_Pad_GridFormat,
                    showindex=False,
                ).encode("utf-8").decode(STD_ENCODING)
                
        OutputControls().printOutput(colorText.FAIL + summary_text + colorText.END + "\n")
        OutputControls().printOutput(tabulated_text + "\n")
        
        choices, filename = self.get_backtest_report_filename(sort_key, optional_name, choices=choices)
        
        header_dict = {0: "<th></th>"}
        index = 1
        for col in backtest_df.columns:
            if col != "Stock":
                header_dict[index] = f"<th>{col}</th>"
                index += 1
                
        colored_text = backtest_df.to_html(index=False)
        summary_text = summary_text.replace("\n", "<br />")
        
        if "Summary" in optional_name:
            summary_text = (
                f"{summary_text}<br /><input type='checkbox' id='chkActualNumbers' "
                f"name='chkActualNumbers' value='0'><label for='chkActualNumbers'>"
                f"Sort by actual numbers (Stocks + Date combinations of results. "
                f"Higher the count, better the prediction reliability)</label><br>"
            )
            
        colored_text = self._reformat_table_for_html(summary_text, header_dict, colored_text, sorting=True)
        
        # Save the file
        output_folder = self.scan_output_directory(backtest=True)
        filename = os.path.join(output_folder, filename)
        
        try:
            os.remove(filename)
        except Exception:
            pass
        finally:
            colored_text = colored_text.encode('utf-8').decode(STD_ENCODING)
            with open(filename, "w") as f:
                f.write(colored_text)
            if "RUNNER" in os.environ.keys():
                Committer.execOSCommand(f"git add {filename} -f >/dev/null 2>&1")
                
        # Save in excel if configured
        try:
            if self.config_manager.alwaysExportToExcel:
                excel_sheetname = filename.split(os.sep)[-1].replace("PKScreener_", "").replace(".html", "")
                PKAssetsManager.promptSaveResults(
                    sheetName=excel_sheetname,
                    df_save=backtest_df,
                    defaultAnswer=self.user_passed_args.answerdefault if self.user_passed_args else None,
                    pastDate=None
                )
        except:
            pass
            
        # Handle summary row
        if last_summary_row is not None:
            oneline_text = last_summary_row.to_html(header=False, index=False)
            oneline_text = self._reformat_table_for_html(summary_text, header_dict, oneline_text, sorting=False)
            
            oneline_summary_file = f"PKScreener_{choices}_OneLine_{optional_name}.html"
            oneline_summary_file = os.path.join(output_folder, oneline_summary_file)
            
            try:
                os.remove(oneline_summary_file)
            except Exception:
                pass
            finally:
                oneline_text = (
                    f"{oneline_text}<td class='w'>"
                    f"{PKDateUtilities.currentDateTime().strftime('%Y/%m/%d')}</td>"
                    f"<td class='w'>{round(self.elapsed_time, 2)}</td>"
                )
                with open(oneline_summary_file, "w") as f:
                    f.write(oneline_text)
                if "RUNNER" in os.environ.keys():
                    Committer.execOSCommand(f"git add {oneline_summary_file} -f >/dev/null 2>&1")
                    
    def _reformat_table_for_html(self, summary_text, header_dict, colored_text, sorting=True):
        """Reformat table text for HTML output."""
        if sorting:
            table_text = (
                "<!DOCTYPE html><html><head><script type='application/javascript' "
                "src='https://pkjmesra.github.io/pkjmesra/pkscreener/classes/tableSorting.js' ></script>"
                "<style type='text/css'>body, table {background-color: black; color: white;} "
                "table, th, td {border: 1px solid white;} "
                "th {cursor: pointer; color:white; text-decoration:underline;} "
                ".r {color:red;font-weight:bold;} "
                ".br {border-color:green;border-width:medium;} "
                ".w {color:white;font-weight:bold;} "
                ".g {color:lightgreen;font-weight:bold;} "
                ".y {color:yellow;} "
                ".bg {background-color:darkslategrey;} "
                ".bb {background-color:black;} "
                "input#searchReports { width: 220px; } "
                "table thead tr th { background-color: black; position: sticky; z-index: 100; top: 0; } "
                "</style></head><body><span style='color:white;' >"
            )
            colored_text = colored_text.replace(
                "<table",
                f"{table_text}{summary_text}<br />"
                "<input type='text' id='searchReports' onkeyup='searchReportsByAny()' "
                "placeholder='Search for stock/scan reports..' title='Type in a name/ID'><table"
            )
            colored_text = colored_text.replace("<table ", "<table id='resultsTable' ")
            colored_text = colored_text.replace(
                '<tr style="text-align: right;">',
                '<tr style="text-align: right;" class="header">'
            )
            
            for key in header_dict.keys():
                if key > 0:
                    colored_text = colored_text.replace(
                        header_dict[key], f"<th>{header_dict[key][4:]}"
                    )
                else:
                    colored_text = colored_text.replace(
                        header_dict[key], f"<th>Stock{header_dict[key][4:]}"
                    )
        else:
            colored_text = colored_text.replace('<table border="1" class="dataframe">', "")
            colored_text = colored_text.replace("<tbody>", "")
            colored_text = colored_text.replace("<tr>", "")
            colored_text = colored_text.replace("</tr>", "")
            colored_text = colored_text.replace("</tbody>", "")
            colored_text = colored_text.replace("</table>", "")
            
        # Replace color styles
        colored_text = colored_text.replace(colorText.BOLD, "")
        colored_text = colored_text.replace(f"{colorText.GREEN}", "<span class='g'>")
        colored_text = colored_text.replace(f"{colorText.FAIL}", "<span class='r'>")
        colored_text = colored_text.replace(f"{colorText.WARN}", "<span class='y'>")
        colored_text = colored_text.replace(f"{colorText.WHITE}", "<span class='w'>")
        colored_text = colored_text.replace("<td><span class='w'>", "<td class='br'><span class='w'>")
        colored_text = colored_text.replace(colorText.END, "</span>")
        colored_text = colored_text.replace("\n", "")
        
        if sorting:
            colored_text = colored_text.replace("</table>", "</table></span></body></html>")
            
        return colored_text
    
    def get_backtest_report_filename(self, sort_key="Stock", optional_name="backtest_result", 
                                     selected_choice=None, choices=None):
        """
        Get the filename for backtest report.
        
        Args:
            sort_key: Column used for sorting
            optional_name: Optional name suffix
            selected_choice: Selected choice dictionary
            choices: Pre-formatted choices string
            
        Returns:
            tuple: (choices, filename)
        """
        if choices is None and selected_choice is not None:
            choices = PKScanRunner.getFormattedChoices(self.user_passed_args, selected_choice).strip()
        elif choices is None:
            choices = "Unknown"
            
        filename = (
            f"PKScreener_{choices.strip()}_{optional_name.strip()}_"
            f"{sort_key.strip() if sort_key is not None else 'Default'}Sorted.html"
        )
        return choices.strip(), filename.strip()
    
    def scan_output_directory(self, backtest=False):
        """
        Get the output directory for scan results.
        
        Args:
            backtest: Whether this is for backtest output
            
        Returns:
            str: Path to output directory
        """
        dir_name = 'actions-data-scan' if not backtest else "Backtest-Reports"
        output_folder = os.path.join(os.getcwd(), dir_name)
        
        if not os.path.isdir(output_folder):
            OutputControls().printOutput(f"Creating {dir_name} directory now...")
            os.makedirs(os.path.dirname(os.path.join(os.getcwd(), f"{dir_name}{os.sep}")), exist_ok=True)
            
        return output_folder
    
    def finish_backtest_data_cleanup(self, backtest_df, df_xray, default_answer=None):
        """
        Clean up and finalize backtest data.
        
        Args:
            backtest_df: Backtest dataframe
            df_xray: X-ray dataframe
            default_answer: Default answer for prompts
            
        Returns:
            tuple: (summary_df, sorting, sort_keys)
        """
        from pkscreener.classes.PKTask import PKTask
        from pkscreener.classes.PKScheduler import PKScheduler
        from pkscreener.classes.Portfolio import PortfolioCollection
        
        if df_xray is not None and len(df_xray) > 10:
            self.show_backtest_results(df_xray, sort_key="Date", optional_name="Insights")
            
        summary_df = backtestSummary(backtest_df)
        backtest_df.loc[:, "Date"] = backtest_df.loc[:, "Date"].apply(
            lambda x: x.replace("-", "/")
        )
        
        self.show_backtest_results(backtest_df)
        self.show_backtest_results(summary_df, optional_name="Summary")
        
        sorting = False if default_answer is not None else True
        
        sort_keys = {
            "S": "Stock",
            "D": "Date",
            "1": "1-Pd",
            "2": "2-Pd",
            "3": "3-Pd",
            "4": "4-Pd",
            "5": "5-Pd",
            "10": "10-Pd",
            "15": "15-Pd",
            "22": "22-Pd",
            "30": "30-Pd",
            "T": "Trend",
            "V": "volume",
            "M": "MA-Signal",
        }
        
        if self.config_manager.enablePortfolioCalculations:
            tasks_list = []
            
            if 'RUNNER' not in os.environ.keys():
                task1 = PKTask(
                    "PortfolioLedger",
                    long_running_fn=PortfolioCollection().getPortfoliosAsDataframe
                )
                task2 = PKTask(
                    "PortfolioLedgerSnapshots",
                    long_running_fn=PortfolioCollection().getLedgerSummaryAsDataframe
                )
                tasks_list = [task1, task2]
                PKScheduler.scheduleTasks(
                    tasksList=tasks_list,
                    label=f"Portfolio Calculations Report Export(Total={len(tasks_list)})",
                    timeout=600
                )
            else:
                for task in tasks_list:
                    task.long_running_fn(*(task,))
                    
            for task in tasks_list:
                if task.result is not None:
                    self.show_backtest_results(task.result, sort_key=None, optional_name=task.taskName)
                    
        return summary_df, sorting, sort_keys
    
    def show_sorted_backtest_data(self, backtest_df, summary_df, sort_keys, default_answer=None):
        """
        Show sorted backtest data interactively.
        
        Args:
            backtest_df: Backtest dataframe
            summary_df: Summary dataframe
            sort_keys: Dictionary of sort key mappings
            default_answer: Default answer for prompts
            
        Returns:
            bool: Whether to continue sorting
        """
        OutputControls().printOutput(
            colorText.FAIL
            + "  [+] Would you like to sort the results?"
            + colorText.END
        )
        OutputControls().printOutput(
            colorText.GREEN
            + "  [+] Press :\n   [+] s, v, t, m : sort by Stocks, Volume, Trend, MA-Signal\n"
            "   [+] d : sort by date\n   [+] 1,2,3...30 : sort by period\n   [+] n : Exit sorting\n"
            + colorText.END
        )
        
        if default_answer is None:
            choice = OutputControls().takeUserInput(colorText.FAIL + "  [+] Select option:")
            OutputControls().printOutput(colorText.END, end="")
            
            if choice.upper() in sort_keys.keys():
                ConsoleUtility.PKConsoleTools.clearScreen(forceTop=True)
                self.show_backtest_results(backtest_df, sort_keys[choice.upper()])
                self.show_backtest_results(summary_df, optional_name="Summary")
            else:
                return False
        else:
            OutputControls().printOutput("Finished backtesting!")
            return False
            
        return True




