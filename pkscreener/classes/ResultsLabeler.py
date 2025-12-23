"""
ResultsLabeler - Results labeling and formatting for PKScreener

This module handles:
- Labeling data for printing
- Sorting results by appropriate columns
- Removing unused columns
- Formatting volume and other fields
"""

import numpy as np
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
from PKDevTools.classes.ColorText import colorText
from PKDevTools.classes.PKDateUtilities import PKDateUtilities
from PKDevTools.classes.log import default_logger

from pkscreener.classes import Utility, ImageUtility


class ResultsLabeler:
    """
    Handles labeling and formatting of screening results.
    
    This class encapsulates the labelDataForPrinting function from globals.py.
    """
    
    def __init__(self, config_manager, menu_choice_hierarchy=""):
        self.config_manager = config_manager
        self.menu_choice_hierarchy = menu_choice_hierarchy
    
    def label_data_for_printing(
        self,
        screen_results: pd.DataFrame,
        save_results: pd.DataFrame,
        volume_ratio: float,
        execute_option: int,
        reversal_option: int,
        menu_option: str,
        user_passed_args=None
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Label and format data for printing.
        
        Args:
            screen_results: Screen results dataframe
            save_results: Save results dataframe
            volume_ratio: Volume ratio
            execute_option: Execute option
            reversal_option: Reversal option
            menu_option: Menu option
            user_passed_args: User passed arguments
            
        Returns:
            Tuple of (screen_results, save_results)
        """
        if save_results is None:
            return screen_results, save_results
        
        try:
            # Add RSI intraday column if applicable
            screen_results, save_results = self._add_rsi_intraday(
                screen_results, save_results, user_passed_args
            )
            
            # Determine sort key and order
            sort_key, ascending = self._get_sort_key(
                execute_option, reversal_option, save_results
            )
            
            # Apply sorting
            screen_results, save_results = self._apply_sorting(
                screen_results, save_results, sort_key, ascending
            )
            
            # Remove unused columns
            screen_results, save_results = self._remove_unused_columns(
                screen_results, save_results, execute_option, menu_option, user_passed_args
            )
            
            # Set index if needed
            if "Stock" in screen_results.columns:
                screen_results.set_index("Stock", inplace=True)
            if "Stock" in save_results.columns:
                save_results.set_index("Stock", inplace=True)
            
            # Format volume
            screen_results, save_results = self._format_volume(
                screen_results, save_results, volume_ratio
            )
            
            # Rename trend columns
            screen_results, save_results = self._rename_trend_columns(
                screen_results, save_results
            )
            
        except Exception as e:
            default_logger().debug(e, exc_info=True)
        
        # Drop all-NA columns
        how = "all" if menu_option not in ["F"] else "any"
        screen_results.dropna(how=how, axis=1, inplace=True)
        save_results.dropna(how=how, axis=1, inplace=True)
        
        return screen_results, save_results
    
    def _add_rsi_intraday(
        self,
        screen_results: pd.DataFrame,
        save_results: pd.DataFrame,
        user_passed_args
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Add RSI intraday column if applicable"""
        import os
        
        is_trading = PKDateUtilities.isTradingTime() and not PKDateUtilities.isTodayHoliday()[0]
        should_add = (
            "RUNNER" not in os.environ.keys() and
            (is_trading or 
             (user_passed_args and user_passed_args.monitor) or
             "RSIi" in save_results.columns) and
            self.config_manager.calculatersiintraday
        )
        
        if should_add and "RSIi" in screen_results.columns:
            screen_results['RSI'] = (
                screen_results['RSI'].astype(str) + "/" + 
                screen_results['RSIi'].astype(str)
            )
            save_results['RSI'] = (
                save_results['RSI'].astype(str) + "/" + 
                save_results['RSIi'].astype(str)
            )
            screen_results.rename(columns={"RSI": "RSI/i"}, inplace=True)
            save_results.rename(columns={"RSI": "RSI/i"}, inplace=True)
        
        return screen_results, save_results
    
    def _get_sort_key(
        self,
        execute_option: int,
        reversal_option: int,
        save_results: pd.DataFrame
    ) -> Tuple[List[str], List[bool]]:
        """Determine sort key and order based on options"""
        is_trading = PKDateUtilities.isTradingTime() and not PKDateUtilities.isTodayHoliday()[0]
        
        # Default sort
        if "RSI" not in self.menu_choice_hierarchy:
            sort_key = ["volume"]
            ascending = [False]
        else:
            sort_key = ["RSIi"] if (is_trading or "RSIi" in save_results.columns) else ["RSI"]
            ascending = [True]
        
        # Option-specific sorting
        if execute_option == 21:
            if reversal_option in [3, 5, 6, 7]:
                sort_key = ["MFI"]
                ascending = [reversal_option in [6, 7]]
            elif reversal_option in [8, 9]:
                sort_key = ["FVDiff"]
                ascending = [reversal_option in [9]]
        
        elif execute_option == 7:
            if reversal_option == 3:
                if "SuperConfSort" in save_results.columns:
                    sort_key = ["SuperConfSort"]
                    ascending = [False]
                else:
                    sort_key = ["volume"]
                    ascending = [False]
            elif reversal_option == 4:
                if "deviationScore" in save_results.columns:
                    sort_key = ["deviationScore"]
                    ascending = [True]
                else:
                    sort_key = ["volume"]
                    ascending = [False]
        
        elif execute_option == 23:
            sort_key = (
                ["bbands_ulr_ratio_max5"] 
                if "bbands_ulr_ratio_max5" in save_results.columns 
                else ["volume"]
            )
            ascending = [False]
        
        elif execute_option == 27:  # ATR Cross
            sort_key = ["ATR"] if "ATR" in save_results.columns else ["volume"]
            ascending = [False]
        
        elif execute_option == 31:  # DEEL Momentum
            sort_key = ["%Chng"]
            ascending = [False]
        
        return sort_key, ascending
    
    def _apply_sorting(
        self,
        screen_results: pd.DataFrame,
        save_results: pd.DataFrame,
        sort_key: List[str],
        ascending: List[bool]
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Apply sorting to results"""
        try:
            try:
                screen_results[sort_key] = (
                    screen_results[sort_key]
                    .replace("", np.nan)
                    .replace(np.inf, np.nan)
                    .replace(-np.inf, np.nan)
                    .astype(float)
                )
            except Exception:
                pass
            
            try:
                save_results[sort_key] = (
                    save_results[sort_key]
                    .replace("", np.nan)
                    .replace(np.inf, np.nan)
                    .replace(-np.inf, np.nan)
                    .astype(float)
                )
            except Exception:
                pass
            
            screen_results.sort_values(by=sort_key, ascending=ascending, inplace=True)
            save_results.sort_values(by=sort_key, ascending=ascending, inplace=True)
            
        except Exception as e:
            default_logger().debug(e, exc_info=True)
        
        return screen_results, save_results
    
    def _remove_unused_columns(
        self,
        screen_results: pd.DataFrame,
        save_results: pd.DataFrame,
        execute_option: int,
        menu_option: str,
        user_passed_args
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Remove unused columns from results"""
        columns_to_delete = [
            "MFI", "FVDiff", "ConfDMADifference", 
            "bbands_ulr_ratio_max5", "RSIi"
        ]
        
        if menu_option not in ["F"]:
            columns_to_delete.extend(["ScanOption"])
        
        if "EoDDiff" in save_results.columns:
            columns_to_delete.extend(["Trend", "Breakout"])
        
        if "SuperConfSort" in save_results.columns:
            columns_to_delete.extend(["SuperConfSort"])
        
        if "deviationScore" in save_results.columns:
            columns_to_delete.extend(["deviationScore"])
        
        if user_passed_args and user_passed_args.options:
            if user_passed_args.options.upper().startswith("C"):
                columns_to_delete.append("FairValue")
        
        # Handle ATR Cross special case
        if execute_option == 27 and "ATR" in screen_results.columns:
            screen_results['ATR'] = screen_results['ATR'].astype(str)
            screen_results['ATR'] = colorText.GREEN + screen_results['ATR'] + colorText.END
        
        for column in columns_to_delete:
            if column in save_results.columns:
                save_results.drop(column, axis=1, inplace=True, errors="ignore")
                screen_results.drop(column, axis=1, inplace=True, errors="ignore")
        
        return screen_results, save_results
    
    def _format_volume(
        self,
        screen_results: pd.DataFrame,
        save_results: pd.DataFrame,
        volume_ratio: float
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Format volume column"""
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
        
        return screen_results, save_results
    
    def _rename_trend_columns(
        self,
        screen_results: pd.DataFrame,
        save_results: pd.DataFrame
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Rename trend-related columns"""
        days = self.config_manager.daysToLookback
        rename_dict = {
            "Trend": f"Trend({days}Prds)",
            "Breakout": f"Breakout({days}Prds)",
        }
        
        screen_results.rename(columns=rename_dict, inplace=True)
        save_results.rename(columns=rename_dict, inplace=True)
        
        return screen_results, save_results
    
    def remove_unused_columns_for_output(
        self,
        screen_results: pd.DataFrame,
        save_results: pd.DataFrame,
        drop_additional_columns: List[str] = None,
        user_args=None
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Remove unused columns for output display"""
        if drop_additional_columns is None:
            drop_additional_columns = []
        
        columns_to_drop = list(drop_additional_columns)
        
        # Add common columns to drop
        if user_args and hasattr(user_args, 'options') and user_args.options:
            if user_args.options.upper().startswith("C"):
                columns_to_drop.extend(["FairValue"])
        
        for col in columns_to_drop:
            if col in screen_results.columns:
                screen_results.drop(col, axis=1, inplace=True, errors="ignore")
            if col in save_results.columns:
                save_results.drop(col, axis=1, inplace=True, errors="ignore")
        
        return screen_results, save_results
    
    def remove_unknowns(
        self,
        screen_results: pd.DataFrame,
        save_results: pd.DataFrame
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Remove rows with unknown/invalid data"""
        if screen_results is None or len(screen_results) == 0:
            return screen_results, save_results
        
        # Remove rows where all values are '-' or empty
        try:
            mask = (screen_results != '-').any(axis=1)
            screen_results = screen_results[mask]
            
            if save_results is not None and len(save_results) > 0:
                save_results = save_results[save_results.index.isin(screen_results.index)]
        except Exception as e:
            default_logger().debug(e, exc_info=True)
        
        return screen_results, save_results


def label_data_for_printing_impl(
    screen_results: pd.DataFrame,
    save_results: pd.DataFrame,
    config_manager,
    volume_ratio: float,
    execute_option: int,
    reversal_option: int,
    menu_option: str,
    menu_choice_hierarchy: str = "",
    user_passed_args=None
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Implementation of labelDataForPrinting for delegation from globals.py.
    
    This function provides a procedural interface to the ResultsLabeler class.
    """
    import os
    
    if save_results is None:
        return screen_results, save_results
    
    try:
        is_trading = PKDateUtilities.isTradingTime() and not PKDateUtilities.isTodayHoliday()[0]
        is_monitor = user_passed_args is not None and user_passed_args.monitor
        calculate_rsi_intraday = config_manager.calculatersiintraday
        
        # Add RSI intraday column if applicable
        if ("RUNNER" not in os.environ.keys() and 
            (is_trading or is_monitor or ("RSIi" in save_results.columns)) and 
            calculate_rsi_intraday):
            screen_results['RSI'] = screen_results['RSI'].astype(str) + "/" + screen_results['RSIi'].astype(str)
            save_results['RSI'] = save_results['RSI'].astype(str) + "/" + save_results['RSIi'].astype(str)
            screen_results.rename(columns={"RSI": "RSI/i"}, inplace=True)
            save_results.rename(columns={"RSI": "RSI/i"}, inplace=True)
        
        # Determine sort key and order
        sort_key = ["volume"] if "RSI" not in menu_choice_hierarchy else (
            "RSIi" if (is_trading or "RSIi" in save_results.columns) else "RSI"
        )
        ascending = [False if "RSI" not in menu_choice_hierarchy else True]
        
        # Override based on execute option
        if execute_option == 21:
            if reversal_option in [3, 5, 6, 7]:
                sort_key = ["MFI"]
                ascending = [reversal_option in [6, 7]]
            elif reversal_option in [8, 9]:
                sort_key = ["FVDiff"]
                ascending = [reversal_option in [9]]
        elif execute_option == 7:
            if reversal_option in [3]:
                if "SuperConfSort" in save_results.columns:
                    sort_key = ["SuperConfSort"]
                    ascending = [False]
                else:
                    sort_key = ["volume"]
                    ascending = [False]
            elif reversal_option in [4]:
                if "deviationScore" in save_results.columns:
                    sort_key = ["deviationScore"]
                    ascending = [True]
                else:
                    sort_key = ["volume"]
                    ascending = [False]
        elif execute_option == 23:
            sort_key = ["bbands_ulr_ratio_max5"] if "bbands_ulr_ratio_max5" in screen_results.columns else ["volume"]
            ascending = [False]
        elif execute_option == 27:  # ATR Cross
            sort_key = ["ATR"] if "ATR" in screen_results.columns else ["volume"]
            ascending = [False]
        elif execute_option == 31:  # DEEL Momentum
            sort_key = ["%Chng"]
            ascending = [False]
        
        # Apply sorting
        try:
            try:
                screen_results[sort_key] = screen_results[sort_key].replace(
                    "", np.nan
                ).replace(np.inf, np.nan).replace(-np.inf, np.nan).astype(float)
            except:
                pass
            try:
                save_results[sort_key] = save_results[sort_key].replace(
                    "", np.nan
                ).replace(np.inf, np.nan).replace(-np.inf, np.nan).astype(float)
            except:
                pass
            screen_results.sort_values(by=sort_key, ascending=ascending, inplace=True)
            save_results.sort_values(by=sort_key, ascending=ascending, inplace=True)
        except Exception as e:
            default_logger().debug(e, exc_info=True)
        
        # Columns to delete
        columns_to_be_deleted = ["MFI", "FVDiff", "ConfDMADifference", "bbands_ulr_ratio_max5", "RSIi"]
        if menu_option not in ["F"]:
            columns_to_be_deleted.extend(["ScanOption"])
        if "EoDDiff" in save_results.columns:
            columns_to_be_deleted.extend(["Trend", "Breakout"])
        if "SuperConfSort" in save_results.columns:
            columns_to_be_deleted.extend(["SuperConfSort"])
        if "deviationScore" in save_results.columns:
            columns_to_be_deleted.extend(["deviationScore"])
        if (user_passed_args is not None and 
            user_passed_args.options is not None and 
            user_passed_args.options.upper().startswith("C")):
            columns_to_be_deleted.append("FairValue")
        if execute_option == 27 and "ATR" in screen_results.columns:  # ATR Cross
            screen_results['ATR'] = screen_results['ATR'].astype(str)
            screen_results['ATR'] = colorText.GREEN + screen_results['ATR'] + colorText.END
        
        for column in columns_to_be_deleted:
            if column in save_results.columns:
                save_results.drop(column, axis=1, inplace=True, errors="ignore")
                screen_results.drop(column, axis=1, inplace=True, errors="ignore")
        
        # Set index
        if "Stock" in screen_results.columns:
            screen_results.set_index("Stock", inplace=True)
        if "Stock" in save_results.columns:
            save_results.set_index("Stock", inplace=True)
        
        # Format volume
        screen_results["volume"] = screen_results["volume"].astype(str)
        save_results["volume"] = save_results["volume"].astype(str)
        screen_results.loc[:, "volume"] = screen_results.loc[:, "volume"].apply(
            lambda x: Utility.tools.formatRatio(
                float(ImageUtility.PKImageTools.removeAllColorStyles(x)), volume_ratio
            ) if len(str(x).strip()) > 0 else ''
        )
        save_results.loc[:, "volume"] = save_results.loc[:, "volume"].apply(
            lambda x: str(x) + "x"
        )
        
        # Rename columns
        days = config_manager.daysToLookback
        screen_results.rename(
            columns={
                "Trend": f"Trend({days}Prds)",
                "Breakout": f"Breakout({days}Prds)",
            },
            inplace=True,
        )
        save_results.rename(
            columns={
                "Trend": f"Trend({days}Prds)",
                "Breakout": f"Breakout({days}Prds)",
            },
            inplace=True,
        )
    except Exception as e:
        default_logger().debug(e, exc_info=True)
    
    screen_results.dropna(how="all" if menu_option not in ["F"] else "any", axis=1, inplace=True)
    save_results.dropna(how="all" if menu_option not in ["F"] else "any", axis=1, inplace=True)
    
    return screen_results, save_results
