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
import uuid

import numpy as np
import pandas as pd

from PKDevTools.classes.ColorText import colorText
from PKDevTools.classes.OutputControls import OutputControls
from PKDevTools.classes.PKDateUtilities import PKDateUtilities
from PKDevTools.classes.log import default_logger
from PKDevTools.classes import Archiver

from pkscreener.classes import Utility, ImageUtility
from pkscreener.classes.Utility import STD_ENCODING


class ResultsManager:
    """
    Manages processing, formatting, and display of scan results.
    Handles data transformation, column management, and result presentation.
    """
    
    def __init__(self, config_manager, user_passed_args=None):
        """
        Initialize ResultsManager.
        
        Args:
            config_manager: Configuration manager instance
            user_passed_args: User passed arguments
        """
        self.config_manager = config_manager
        self.user_passed_args = user_passed_args
        
    def label_data_for_printing(self, screen_results, save_results, volume_ratio, 
                                execute_option, reversal_option, menu_option, 
                                menu_choice_hierarchy):
        """
        Label and format data for printing to console.
        
        Args:
            screen_results: Screen results dataframe
            save_results: Save results dataframe
            volume_ratio: Volume ratio for formatting
            execute_option: Execute option selected
            reversal_option: Reversal option selected
            menu_option: Menu option selected
            menu_choice_hierarchy: Menu choice hierarchy string
            
        Returns:
            tuple: (screen_results, save_results) formatted dataframes
        """
        if save_results is None:
            return None, None
            
        try:
            is_trading = PKDateUtilities.isTradingTime() and not PKDateUtilities.isTodayHoliday()[0]
            
            # Handle RSI column formatting
            if (("RUNNER" not in os.environ.keys() and 
                (is_trading or (self.user_passed_args and self.user_passed_args.monitor) or 
                 ("RSIi" in save_results.columns))) and 
                self.config_manager.calculatersiintraday):
                screen_results['RSI'] = screen_results['RSI'].astype(str) + "/" + screen_results['RSIi'].astype(str)
                save_results['RSI'] = save_results['RSI'].astype(str) + "/" + save_results['RSIi'].astype(str)
                screen_results.rename(columns={"RSI": "RSI/i"}, inplace=True)
                save_results.rename(columns={"RSI": "RSI/i"}, inplace=True)
                
            # Determine sort key based on options
            sort_key, ascending = self._get_sort_key(
                menu_choice_hierarchy, execute_option, reversal_option, 
                is_trading, save_results, screen_results
            )
            
            # Apply sorting
            self._apply_sorting(screen_results, save_results, sort_key, ascending)
            
            # Clean up columns
            self._cleanup_columns(screen_results, save_results, execute_option, 
                                  reversal_option, menu_option)
            
            # Format volume column
            self._format_volume_column(screen_results, save_results, volume_ratio)
            
            # Rename columns
            self._rename_columns(screen_results, save_results)
            
        except Exception as e:
            default_logger().debug(e, exc_info=True)
            
        screen_results.dropna(how="all" if menu_option not in ["F"] else "any", axis=1, inplace=True)
        save_results.dropna(how="all" if menu_option not in ["F"] else "any", axis=1, inplace=True)
        
        return screen_results, save_results
    
    def _get_sort_key(self, menu_choice_hierarchy, execute_option, reversal_option, 
                      is_trading, save_results, screen_results):
        """Get the sort key and ascending order for results."""
        sort_key = ["volume"] if "RSI" not in menu_choice_hierarchy else (
            "RSIi" if (is_trading or "RSIi" in save_results.columns) else "RSI"
        )
        ascending = [False if "RSI" not in menu_choice_hierarchy else True]
        
        if execute_option == 21:
            if reversal_option in [3, 5, 6, 7]:
                sort_key = ["MFI"]
                ascending = [reversal_option in [6, 7]]
            elif reversal_option in [8, 9]:
                sort_key = ["FVDiff"]
                ascending = [reversal_option in [9]]
        elif execute_option == 7:
            if reversal_option in [3]:
                sort_key = ["SuperConfSort"] if "SuperConfSort" in save_results.columns else ["volume"]
                ascending = [False]
            elif reversal_option in [4]:
                sort_key = ["deviationScore"] if "deviationScore" in save_results.columns else ["volume"]
                ascending = [True] if "deviationScore" in save_results.columns else [False]
        elif execute_option == 23:
            sort_key = ["bbands_ulr_ratio_max5"] if "bbands_ulr_ratio_max5" in screen_results.columns else ["volume"]
            ascending = [False]
        elif execute_option == 27:  # ATR Cross
            sort_key = ["ATR"] if "ATR" in screen_results.columns else ["volume"]
            ascending = [False]
        elif execute_option == 31:  # DEEL Momentum
            sort_key = ["%Chng"]
            ascending = [False]
            
        return sort_key, ascending
    
    def _apply_sorting(self, screen_results, save_results, sort_key, ascending):
        """Apply sorting to results dataframes."""
        try:
            try:
                screen_results[sort_key] = screen_results[sort_key].replace(
                    "", np.nan).replace(np.inf, np.nan).replace(-np.inf, np.nan).astype(float)
            except:
                pass
            try:
                save_results[sort_key] = save_results[sort_key].replace(
                    "", np.nan).replace(np.inf, np.nan).replace(-np.inf, np.nan).astype(float)
            except:
                pass
            screen_results.sort_values(by=sort_key, ascending=ascending, inplace=True)
            save_results.sort_values(by=sort_key, ascending=ascending, inplace=True)
        except Exception as e:
            default_logger().debug(e, exc_info=True)
    
    def _cleanup_columns(self, screen_results, save_results, execute_option, 
                         reversal_option, menu_option):
        """Clean up columns that should be removed."""
        columns_to_delete = ["MFI", "FVDiff", "ConfDMADifference", "bbands_ulr_ratio_max5", "RSIi"]
        
        if menu_option not in ["F"]:
            columns_to_delete.extend(["ScanOption"])
        if "EoDDiff" in save_results.columns:
            columns_to_delete.extend(["Trend", "Breakout"])
        if "SuperConfSort" in save_results.columns:
            columns_to_delete.extend(["SuperConfSort"])
        if "deviationScore" in save_results.columns:
            columns_to_delete.extend(["deviationScore"])
        if (self.user_passed_args is not None and 
            self.user_passed_args.options is not None and 
            self.user_passed_args.options.upper().startswith("C")):
            columns_to_delete.append("FairValue")
            
        if execute_option == 27 and "ATR" in screen_results.columns:
            screen_results['ATR'] = screen_results['ATR'].astype(str)
            screen_results['ATR'] = colorText.GREEN + screen_results['ATR'] + colorText.END
            
        for column in columns_to_delete:
            if column in save_results.columns:
                save_results.drop(column, axis=1, inplace=True, errors="ignore")
                screen_results.drop(column, axis=1, inplace=True, errors="ignore")
                
    def _format_volume_column(self, screen_results, save_results, volume_ratio):
        """Format the volume column."""
        if "Stock" in screen_results.columns:
            screen_results.set_index("Stock", inplace=True)
        if "Stock" in save_results.columns:
            save_results.set_index("Stock", inplace=True)
            
        screen_results["volume"] = screen_results["volume"].astype(str)
        save_results["volume"] = save_results["volume"].astype(str)
        
        screen_results.loc[:, "volume"] = screen_results.loc[:, "volume"].apply(
            lambda x: Utility.tools.formatRatio(
                float(ImageUtility.PKImageTools.removeAllColorStyles(x)), 
                volume_ratio
            ) if len(str(x).strip()) > 0 else ''
        )
        save_results.loc[:, "volume"] = save_results.loc[:, "volume"].apply(
            lambda x: str(x) + "x"
        )
        
    def _rename_columns(self, screen_results, save_results):
        """Rename columns for display."""
        days_to_lookback = self.config_manager.daysToLookback
        rename_map = {
            "Trend": f"Trend({days_to_lookback}Prds)",
            "Breakout": f"Breakout({days_to_lookback}Prds)",
        }
        screen_results.rename(columns=rename_map, inplace=True)
        save_results.rename(columns=rename_map, inplace=True)
        
    def remove_unknowns(self, screen_results, save_results):
        """
        Remove rows containing 'Unknown' values.
        
        Args:
            screen_results: Screen results dataframe
            save_results: Save results dataframe
            
        Returns:
            tuple: (screen_results, save_results) filtered dataframes
        """
        for col in screen_results.keys():
            screen_results = screen_results[
                screen_results[col].astype(str).str.contains("Unknown") == False
            ]
        for col in save_results.keys():
            save_results = save_results[
                save_results[col].astype(str).str.contains("Unknown") == False
            ]
        return screen_results, save_results
    
    def remove_unused_columns(self, screen_results, save_results, drop_additional_columns=None):
        """
        Remove unused columns from results.
        
        Args:
            screen_results: Screen results dataframe
            save_results: Save results dataframe
            drop_additional_columns: Additional columns to drop
            
        Returns:
            str: Summary returns string
        """
        if drop_additional_columns is None:
            drop_additional_columns = []
            
        periods = self.config_manager.periodsRange
        
        if (self.user_passed_args is not None and 
            self.user_passed_args.backtestdaysago is not None and 
            int(self.user_passed_args.backtestdaysago) < 22):
            drop_additional_columns.append("22-Pd")
            
        summary_returns = ""
        
        for period in periods:
            if save_results is not None:
                with pd.option_context('mode.chained_assignment', None):
                    save_results.drop(f"LTP{period}", axis=1, inplace=True, errors="ignore")
                    save_results.drop(f"Growth{period}", axis=1, inplace=True, errors="ignore")
                    
                if len(drop_additional_columns) > 0:
                    for col in drop_additional_columns:
                        if col in save_results.columns:
                            save_results.drop(col, axis=1, inplace=True, errors="ignore")
                            
            if screen_results is not None:
                with pd.option_context('mode.chained_assignment', None):
                    screen_results.drop(f"LTP{period}", axis=1, inplace=True, errors="ignore")
                    screen_results.drop(f"Growth{period}", axis=1, inplace=True, errors="ignore")
                    
                if len(drop_additional_columns) > 0:
                    for col in drop_additional_columns:
                        if col in screen_results.columns:
                            screen_results.drop(col, axis=1, inplace=True, errors="ignore")
                            
        return summary_returns
    
    def save_screen_results_encoded(self, encoded_text):
        """
        Save screen results to a file with UUID name.
        
        Args:
            encoded_text: Text to save
            
        Returns:
            str: Filename with timestamp
        """
        uuid_filename = str(uuid.uuid4())
        to_be_deleted_folder = os.path.join(Archiver.get_user_outputs_dir(), "DeleteThis")
        os.makedirs(to_be_deleted_folder, exist_ok=True)
        
        file_path = os.path.join(to_be_deleted_folder, uuid_filename)
        
        try:
            with open(file_path, 'w', encoding="utf-8") as f:
                f.write(encoded_text)
        except:
            pass
            
        return f'{uuid_filename}~{PKDateUtilities.currentDateTime().strftime("%Y-%m-%d %H:%M:%S.%f%z").replace(" ", "~")}'
    
    def read_screen_results_decoded(self, filename):
        """
        Read screen results from a saved file.
        
        Args:
            filename: Name of the file to read
            
        Returns:
            str: Contents of the file or None
        """
        to_be_deleted_folder = os.path.join(Archiver.get_user_outputs_dir(), "DeleteThis")
        os.makedirs(to_be_deleted_folder, exist_ok=True)
        
        file_path = os.path.join(to_be_deleted_folder, filename)
        contents = None
        
        try:
            with open(file_path, 'r', encoding="utf-8") as f:
                contents = f.read()
        except:
            pass
            
        return contents
    
    def format_table_results(self, results_df, max_column_widths=None):
        """
        Format results as a tabulated string.
        
        Args:
            results_df: Results dataframe
            max_column_widths: Maximum column widths
            
        Returns:
            str: Tabulated results string
        """
        if results_df is None or len(results_df) == 0:
            return ""
            
        if max_column_widths is None:
            max_column_widths = Utility.tools.getMaxColumnWidths(results_df)
            
        return colorText.miniTabulator().tabulate(
            results_df,
            headers="keys",
            tablefmt=colorText.No_Pad_GridFormat,
            maxcolwidths=max_column_widths
        ).encode("utf-8").decode(STD_ENCODING)
    
    def reformat_table_for_html(self, summary_text, header_dict, colored_text, sorting=True):
        """
        Reformat table text for HTML output.
        
        Args:
            summary_text: Summary text to prepend
            header_dict: Dictionary of headers
            colored_text: HTML colored text
            sorting: Whether to include sorting functionality
            
        Returns:
            str: Reformatted HTML string
        """
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
    
    def get_latest_trade_datetime(self, stock_dict_primary):
        """
        Get the latest trade date and time from stock data.
        
        Args:
            stock_dict_primary: Primary stock dictionary
            
        Returns:
            tuple: (last_trade_date, last_trade_time)
        """
        stocks = list(stock_dict_primary.keys())
        if not stocks:
            return None, None
            
        stock = stocks[0]
        
        try:
            last_trade_date = PKDateUtilities.currentDateTime().strftime("%Y-%m-%d")
            last_trade_time_ist = PKDateUtilities.currentDateTime().strftime("%H:%M:%S")
            
            df = pd.DataFrame(
                data=stock_dict_primary[stock]["data"],
                columns=stock_dict_primary[stock]["columns"],
                index=stock_dict_primary[stock]["index"]
            )
            
            ts = df.index[-1]
            last_traded = pd.to_datetime(ts, unit='s', utc=True)
            last_trade_date = last_traded.strftime("%Y-%m-%d")
            last_trade_time = last_traded.strftime("%H:%M:%S")
            
            if last_trade_time == "00:00:00":
                last_trade_time = last_trade_time_ist
        except:
            pass
            
        return last_trade_date, last_trade_time






