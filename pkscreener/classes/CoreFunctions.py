"""
CoreFunctions - Core scanning and processing functions for PKScreener

This module contains the core scanning functions that were previously
in globals.py. These functions handle the actual scanning execution,
result processing, and backtest operations.
"""

import logging
import time
from datetime import datetime, UTC
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
from alive_progress import alive_bar

from PKDevTools.classes.ColorText import colorText
from PKDevTools.classes.OutputControls import OutputControls
from PKDevTools.classes.PKDateUtilities import PKDateUtilities
from PKDevTools.classes.log import default_logger

from pkscreener.classes import Utility
from pkscreener.classes.Backtest import backtest, backtestSummary
from pkscreener.classes.PKScanRunner import PKScanRunner


def get_review_date(user_passed_args=None, criteria_date_time=None) -> str:
    """Get the review date for screening"""
    if criteria_date_time is not None:
        return criteria_date_time
    review_date = PKDateUtilities.tradingDate().strftime('%Y-%m-%d')
    if user_passed_args is not None and user_passed_args.backtestdaysago is not None:
        review_date = PKDateUtilities.nthPastTradingDateStringFromFutureDate(
            int(user_passed_args.backtestdaysago)
        )
    return review_date


def get_max_allowed_results_count(iterations: int, testing: bool, config_manager, user_passed_args) -> int:
    """Calculate maximum allowed results count"""
    max_display = config_manager.maxdisplayresults
    if user_passed_args and user_passed_args.maxdisplayresults is not None:
        max_display = int(user_passed_args.maxdisplayresults)
    return iterations * max_display if not testing else 1


def get_iterations_and_stock_counts(num_stocks: int, iterations: int) -> Tuple[int, int]:
    """Calculate iterations and stocks per iteration for optimal processing"""
    if num_stocks <= 2500:
        return 1, num_stocks
    
    original_iterations = iterations
    ideal_max_per_iteration = 100
    iterations = int(num_stocks * iterations / ideal_max_per_iteration) + 1
    num_stocks_per_iteration = int(num_stocks / iterations)
    
    if num_stocks_per_iteration < 10:
        num_stocks_per_iteration = num_stocks if (iterations == 1 or num_stocks <= iterations) \
            else int(num_stocks / iterations)
        iterations = original_iterations
    
    if num_stocks_per_iteration > 500:
        num_stocks_per_iteration = 500
        iterations = int(num_stocks / num_stocks_per_iteration) + 1
    
    return iterations, num_stocks_per_iteration


def process_single_result(
    menu_option: str,
    backtest_period: int,
    result: Any,
    lst_screen: List,
    lst_save: List,
    backtest_df: Optional[pd.DataFrame]
) -> Optional[pd.DataFrame]:
    """Process a single scan result"""
    if result is not None:
        lst_screen.append(result[0])
        lst_save.append(result[1])
        sample_days = result[4]
        
        if menu_option == "B":
            backtest_df = update_backtest_results(
                backtest_period, result, sample_days, backtest_df
            )
    
    return backtest_df


def update_backtest_results(
    backtest_period: int,
    result: Any,
    sample_days: int,
    backtest_df: Optional[pd.DataFrame]
) -> Optional[pd.DataFrame]:
    """Update backtest results with new data"""
    if result is None:
        return backtest_df
    
    try:
        result_df = backtest(
            result[0], result[1], result[2], result[3], result[4], backtest_period
        )
        
        if result_df is not None:
            if backtest_df is None:
                backtest_df = result_df
            else:
                backtest_df = pd.concat([backtest_df, result_df], axis=0)
                
    except Exception as e:
        default_logger().debug(e, exc_info=True)
    
    return backtest_df


def run_scanners(
    menu_option: str,
    items: List,
    tasks_queue,
    results_queue,
    num_stocks: int,
    backtest_period: int,
    iterations: int,
    consumers: List,
    screen_results: pd.DataFrame,
    save_results: pd.DataFrame,
    backtest_df: Optional[pd.DataFrame],
    testing: bool,
    config_manager,
    user_passed_args,
    keyboard_interrupt_event,
    keyboard_interrupt_fired_ref: List[bool],
    criteria_date_time_ref: List[Any],
    scan_cycle_running_ref: List[bool],
    start_time_ref: List[float],
    elapsed_time_ref: List[float]
) -> Tuple[pd.DataFrame, pd.DataFrame, Optional[pd.DataFrame]]:
    """
    Run scanners on all items.
    
    Note: *_ref parameters are single-element lists used to pass mutable references
    """
    result = None
    backtest_df = None
    
    review_date = get_review_date(user_passed_args, criteria_date_time_ref[0])
    max_allowed = get_max_allowed_results_count(iterations, testing, config_manager, user_passed_args)
    
    try:
        original_num_stocks = num_stocks
        iterations, num_stocks_per_iteration = get_iterations_and_stock_counts(num_stocks, iterations)
        
        # Print header
        stock_type = 'Scanners' if menu_option in ['F'] else 'Stocks'
        OutputControls().printOutput(
            f"{colorText.GREEN}  [+] For {review_date}, total {stock_type} under review: "
            f"{num_stocks} over {iterations} iterations...{colorText.END}"
        )
        
        if not user_passed_args.download:
            action = 'Screening' if menu_option == 'X' else \
                     ('Analysis' if menu_option == 'C' else \
                      ('Look-up' if menu_option in ['F'] else 'Backtesting.'))
            stock_type = 'Stock' if menu_option not in ['C'] else 'Intraday'
            
            OutputControls().printOutput(
                f"{colorText.WARN}  [+] Starting {stock_type} {action}. "
                f"Press Ctrl+C to stop!{colorText.END}"
            )
            
            if user_passed_args.progressstatus is not None:
                OutputControls().printOutput(
                    f"{colorText.GREEN}{user_passed_args.progressstatus}{colorText.END}"
                )
        else:
            OutputControls().printOutput(
                f"{colorText.FAIL}  [+] Download ONLY mode (OHLCV for period:"
                f"{config_manager.period}, candle-duration:{config_manager.duration})! "
                f"Stocks will not be screened!{colorText.END}"
            )
        
        bar, spinner = Utility.tools.getProgressbarStyle()
        
        with alive_bar(num_stocks, bar=bar, spinner=spinner) as progressbar:
            lst_screen = []
            lst_save = []
            result = None
            backtest_df = None
            
            if not scan_cycle_running_ref[0]:
                start_time_ref[0] = time.time()
            scan_cycle_running_ref[0] = True
            
            def process_results_callback(result_item, processed_count, result_df, *other_args):
                nonlocal backtest_df
                (m_option, bt_period, res, ls_screen, ls_save) = other_args
                
                bt_df = process_single_result(
                    m_option, bt_period, result_item, ls_screen, ls_save, result_df
                )
                
                progressbar()
                progressbar.text(
                    f"{colorText.GREEN}"
                    f"{'Remaining' if user_passed_args.download else ('Found' if m_option in ['X','F'] else 'Analysed')} "
                    f"{len(ls_screen) if not user_passed_args.download else processed_count} "
                    f"{'Stocks' if m_option in ['X'] else 'Records'}"
                    f"{colorText.END}"
                )
                
                # Handle live results for option 29
                if result_item is not None and _should_show_live_results(ls_screen, user_passed_args):
                    _show_live_results(ls_screen)
                
                if keyboard_interrupt_fired_ref[0]:
                    return False, bt_df
                
                return not ((testing and len(ls_screen) >= 1) or 
                           len(ls_screen) >= max_allowed), bt_df
            
            other_args = (menu_option, backtest_period, result, lst_screen, lst_save)
            
            backtest_df, result = PKScanRunner.runScan(
                user_passed_args, testing, num_stocks, iterations, items,
                num_stocks_per_iteration, tasks_queue, results_queue,
                original_num_stocks, backtest_df, *other_args,
                resultsReceivedCb=process_results_callback
            )
        
        OutputControls().moveCursorUpLines(3 if OutputControls().enableMultipleLineOutput else 1)
        elapsed_time_ref[0] = time.time() - start_time_ref[0]
        
        if menu_option in ["X", "G", "C", "F"]:
            screen_results = pd.DataFrame(lst_screen)
            save_results = pd.DataFrame(lst_save)
    
    except KeyboardInterrupt:
        _handle_keyboard_interrupt(
            keyboard_interrupt_event, keyboard_interrupt_fired_ref,
            user_passed_args, consumers, tasks_queue, testing
        )
    except Exception as e:
        default_logger().debug(e, exc_info=True)
        OutputControls().printOutput(
            f"{colorText.FAIL}\nException:\n{e}\n"
            f"  [+] Terminating Script, Please wait...{colorText.END}"
        )
        PKScanRunner.terminateAllWorkers(
            userPassedArgs=user_passed_args, consumers=consumers,
            tasks_queue=tasks_queue, testing=testing
        )
        logging.shutdown()
    
    # Update criteria datetime
    _update_criteria_datetime(result, save_results, user_passed_args, criteria_date_time_ref)
    
    return screen_results, save_results, backtest_df


def _should_show_live_results(lst_screen: List, user_passed_args) -> bool:
    """Check if live results should be shown"""
    if user_passed_args.monitor:
        return False
    if len(lst_screen) == 0:
        return False
    if user_passed_args is None or user_passed_args.options is None:
        return False
    
    try:
        return user_passed_args.options.split(":")[2] in ["29"]
    except (IndexError, AttributeError):
        return False


def _show_live_results(lst_screen: List):
    """Show live results for option 29"""
    scr_df = pd.DataFrame(lst_screen)
    existing_columns = ["Stock", "%Chng", "LTP", "volume"]
    new_columns = ["BidQty", "AskQty", "LwrCP", "UprCP", "VWAP", "DayVola", "Del(%)"]
    existing_columns.extend(new_columns)
    
    available_cols = [c for c in existing_columns if c in scr_df.columns]
    if not available_cols:
        return
    
    scr_df = scr_df[available_cols]
    if "volume" in scr_df.columns and "BidQty" in scr_df.columns:
        scr_df.sort_values(by=["volume", "BidQty"], ascending=False, inplace=True)
    
    tabulated_results = colorText.miniTabulator().tb.tabulate(
        scr_df, headers="keys", showindex=False,
        tablefmt=colorText.No_Pad_GridFormat,
        maxcolwidths=Utility.tools.getMaxColumnWidths(scr_df)
    )
    table_length = 2 * len(lst_screen) + 5
    OutputControls().printOutput('\n' + tabulated_results)
    OutputControls().moveCursorUpLines(table_length)


def _handle_keyboard_interrupt(
    keyboard_interrupt_event,
    keyboard_interrupt_fired_ref: List[bool],
    user_passed_args,
    consumers,
    tasks_queue,
    testing: bool
):
    """Handle keyboard interrupt during scanning"""
    try:
        if keyboard_interrupt_event:
            keyboard_interrupt_event.set()
        keyboard_interrupt_fired_ref[0] = True
        
        OutputControls().printOutput(
            f"{colorText.FAIL}\n  [+] Terminating Script, Please wait...{colorText.END}"
        )
        
        PKScanRunner.terminateAllWorkers(
            userPassedArgs=user_passed_args, consumers=consumers,
            tasks_queue=tasks_queue, testing=testing
        )
        logging.shutdown()
    except KeyboardInterrupt:
        pass


def _update_criteria_datetime(result, save_results, user_passed_args, criteria_date_time_ref):
    """Update criteria datetime from results"""
    if result is None or len(result) < 1:
        return
    
    if criteria_date_time_ref[0] is None:
        if user_passed_args and user_passed_args.backtestdaysago is not None:
            criteria_date_time_ref[0] = result[2].copy().index[
                -1 - int(user_passed_args.backtestdaysago)
            ]
        else:
            if user_passed_args.slicewindow is None:
                criteria_date_time_ref[0] = result[2].copy().index[-1]
            else:
                criteria_date_time_ref[0] = datetime.strptime(
                    user_passed_args.slicewindow.replace("'", ""),
                    "%Y-%m-%d %H:%M:%S.%f%z"
                )
        
        local_tz = datetime.now(UTC).astimezone().tzinfo
        exchange_tz = PKDateUtilities.currentDateTime().astimezone().tzinfo
        
        if local_tz != exchange_tz:
            criteria_date_time_ref[0] = PKDateUtilities.utc_to_ist(
                criteria_date_time_ref[0], localTz=local_tz
            )
    
    # Add Date column if missing
    if save_results is not None and len(save_results) > 0 and "Date" not in save_results.columns:
        temp_df = result[2].copy()
        temp_df.reset_index(inplace=True)
        temp_df = temp_df.tail(1)
        temp_df.rename(columns={"index": "Date"}, inplace=True)
        
        target_date = (temp_df["Date"].iloc[0] if "Date" in temp_df.columns 
                      else str(temp_df.iloc[:, 0][0]))
        save_results["Date"] = str(target_date).split(" ")[0]

