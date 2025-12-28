"""
BacktestUtils - Backtesting utilities for PKScreener

This module handles:
- Backtest result processing
- Backtest report generation
- Backtest data cleanup
"""

import os
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
from PKDevTools.classes.ColorText import colorText
from PKDevTools.classes.OutputControls import OutputControls
from PKDevTools.classes.PKDateUtilities import PKDateUtilities
from PKDevTools.classes import Archiver
from PKDevTools.classes.log import default_logger

from pkscreener.classes import Utility, ConsoleUtility
from pkscreener.classes.Utility import STD_ENCODING
from pkscreener.classes.Backtest import backtest, backtestSummary


def get_backtest_report_filename(
    sort_key: str = "Stock",
    optional_name: str = "backtest_result",
    choices: Dict[str, str] = None
) -> Tuple[str, str]:
    """
    Get the filename for backtest report.
    
    Args:
        sort_key: Key to sort by
        optional_name: Optional name for the report
        choices: Menu choices dictionary
        
    Returns:
        Tuple of (directory, filename)
    """
    if choices is None:
        choices = {}
    
    choice_str = "_".join([v for v in choices.values() if v])
    if not choice_str:
        choice_str = "default"
    
    filename = f"PKS_{optional_name}_{choice_str}.html"
    directory = Archiver.get_user_reports_dir()
    
    return directory, filename


def finish_backtest_data_cleanup(
    backtest_df: pd.DataFrame,
    df_xray: Optional[pd.DataFrame],
    config_manager,
    default_answer=None,
    show_backtest_results_cb=None
) -> Optional[pd.DataFrame]:
    """
    Finish backtest data cleanup and display results.
    
    Args:
        backtest_df: Backtest dataframe
        df_xray: X-Ray analysis dataframe
        config_manager: Configuration manager
        default_answer: Default answer for prompts
        show_backtest_results_cb: Callback to show backtest results
        
    Returns:
        Summary dataframe
    """
    if backtest_df is None:
        return None
    
    # Show X-Ray insights if available
    if df_xray is not None and len(df_xray) > 10 and show_backtest_results_cb:
        show_backtest_results_cb(df_xray, sortKey="Date", optionalName="Insights")
    
    # Get summary
    summary_df = backtestSummary(backtest_df)
    
    # Format dates
    if "Date" in backtest_df.columns:
        backtest_df.loc[:, "Date"] = backtest_df.loc[:, "Date"].apply(
            lambda x: x.replace("-", "/")
        )
    
    # Show results
    if show_backtest_results_cb:
        show_backtest_results_cb(backtest_df)
        show_backtest_results_cb(summary_df, optionalName="Summary")
    
    return summary_df


def prepare_grouped_xray(
    backtest_period: int,
    backtest_df: pd.DataFrame,
    config_manager
) -> Optional[pd.DataFrame]:
    """
    Prepare grouped X-Ray analysis of backtest results.
    
    Args:
        backtest_period: Backtest period in days
        backtest_df: Backtest dataframe
        config_manager: Configuration manager
        
    Returns:
        X-Ray dataframe or None
    """
    from pkscreener.classes import PortfolioXRay
    
    if backtest_df is None or len(backtest_df) == 0:
        return None
    
    try:
        xray = PortfolioXRay.PortfolioXRay()
        return xray.prepareGroupedXRay(backtest_period, backtest_df)
    except Exception as e:
        default_logger().debug(e, exc_info=True)
        return None


def show_sorted_backtest_data(
    backtest_df: pd.DataFrame,
    summary_df: pd.DataFrame,
    sort_keys: Dict[str, str],
    default_answer=None
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Show sorted backtest data.
    
    Args:
        backtest_df: Backtest dataframe
        summary_df: Summary dataframe
        sort_keys: Dictionary mapping keys to column names
        default_answer: Default answer for prompts
        
    Returns:
        Tuple of (backtest_df, summary_df)
    """
    if backtest_df is None:
        return backtest_df, summary_df
    
    # If default answer is provided, don't ask for sort key
    if default_answer is not None:
        return backtest_df, summary_df
    
    # Display sort options
    sort_options = ", ".join([f"{k}={v}" for k, v in sort_keys.items()])
    OutputControls().printOutput(
        f"{colorText.WARN}Sort options: {sort_options}{colorText.END}"
    )
    
    return backtest_df, summary_df


def tabulate_backtest_results(
    save_results: pd.DataFrame,
    max_allowed: int = 0,
    force: bool = False
) -> str:
    """
    Tabulate backtest results for display.
    
    Args:
        save_results: Results dataframe
        max_allowed: Maximum allowed results
        force: Force tabulation even if empty
        
    Returns:
        Tabulated string
    """
    if save_results is None or (len(save_results) == 0 and not force):
        return ""
    
    try:
        if max_allowed > 0 and len(save_results) > max_allowed:
            save_results = save_results.head(max_allowed)
        
        tabulated = colorText.miniTabulator().tabulate(
            save_results,
            headers="keys",
            tablefmt=colorText.No_Pad_GridFormat,
            maxcolwidths=Utility.tools.getMaxColumnWidths(save_results)
        ).encode("utf-8").decode(STD_ENCODING)
        
        return tabulated
        
    except Exception as e:
        default_logger().debug(e, exc_info=True)
        return str(save_results)


def take_backtest_inputs(
    user_passed_args,
    selected_choice: Dict[str, str],
    default_answer=None
) -> Tuple[int, bool]:
    """
    Take backtest inputs from user.
    
    Args:
        user_passed_args: User passed arguments
        selected_choice: Selected menu choices
        default_answer: Default answer for prompts
        
    Returns:
        Tuple of (backtest_period, should_continue)
    """
    backtest_period = 30
    
    if user_passed_args and user_passed_args.backtestdaysago is not None:
        try:
            backtest_period = int(user_passed_args.backtestdaysago)
        except ValueError:
            pass
    
    if default_answer is None:
        try:
            period_input = OutputControls().takeUserInput(
                f"{colorText.WARN}Enter backtest period in days (default=30): {colorText.END}"
            ) or "30"
            backtest_period = int(period_input)
        except ValueError:
            backtest_period = 30
    
    return backtest_period, True


def scan_output_directory(backtest: bool = False) -> str:
    """
    Scan output directory for reports.
    
    Args:
        backtest: Whether scanning for backtest reports
        
    Returns:
        Directory path
    """
    if backtest:
        return Archiver.get_user_reports_dir()
    return Archiver.get_user_outputs_dir()


class BacktestResultsHandler:
    """Handles backtest results processing and display"""
    
    def __init__(self, config_manager, user_passed_args=None):
        self.config_manager = config_manager
        self.user_passed_args = user_passed_args
        self.backtest_df: Optional[pd.DataFrame] = None
        self.summary_df: Optional[pd.DataFrame] = None
    
    def process_backtest_results(
        self,
        backtest_period: int,
        start_time: float,
        result: Any,
        sample_days: int
    ) -> Optional[pd.DataFrame]:
        """Process backtest results"""
        if result is None:
            return self.backtest_df
        
        try:
            result_df = backtest(
                result[0],
                result[1],
                result[2],
                result[3],
                result[4],
                backtest_period
            )
            
            if result_df is not None:
                if self.backtest_df is None:
                    self.backtest_df = result_df
                else:
                    self.backtest_df = pd.concat([self.backtest_df, result_df], axis=0)
                    
        except Exception as e:
            default_logger().debug(e, exc_info=True)
        
        return self.backtest_df
    
    def show_results(
        self,
        sort_key: str = "Stock",
        optional_name: str = "backtest_result",
        choices: Dict[str, str] = None,
        elapsed_time: float = 0,
        menu_choice_hierarchy: str = ""
    ):
        """Show backtest results"""
        if self.backtest_df is None or len(self.backtest_df) == 0:
            OutputControls().printOutput(
                f"{colorText.FAIL}No backtest results to display.{colorText.END}"
            )
            return
        
        # Display summary
        OutputControls().printOutput(
            f"\n{colorText.GREEN}Backtest Results for {menu_choice_hierarchy}{colorText.END}"
        )
        OutputControls().printOutput(
            f"{colorText.WARN}Completed in {elapsed_time:.2f} seconds{colorText.END}"
        )
        
        # Sort and display
        if sort_key in self.backtest_df.columns:
            self.backtest_df = self.backtest_df.sort_values(sort_key, ascending=False)
        
        tabulated = tabulate_backtest_results(self.backtest_df)
        OutputControls().printOutput(tabulated)
    
    def get_summary(self) -> Optional[pd.DataFrame]:
        """Get backtest summary"""
        if self.backtest_df is None:
            return None
        
        self.summary_df = backtestSummary(self.backtest_df)
        return self.summary_df
    
    def save_to_file(
        self,
        choices: Dict[str, str] = None
    ) -> Optional[str]:
        """Save backtest results to file"""
        if self.backtest_df is None:
            return None
        
        directory, filename = get_backtest_report_filename(choices=choices)
        filepath = os.path.join(directory, filename)
        
        try:
            self.backtest_df.to_html(filepath, index=False)
            OutputControls().printOutput(
                f"{colorText.GREEN}Results saved to: {filepath}{colorText.END}"
            )
            return filepath
        except Exception as e:
            default_logger().debug(e, exc_info=True)
            return None


def show_backtest_results_impl(
    backtest_df: pd.DataFrame,
    sort_key: str = "Stock",
    optional_name: str = "backtest_result",
    choices: str = None,
    menu_choice_hierarchy: str = "",
    selected_choice: Dict[str, str] = None,
    user_passed_args=None,
    elapsed_time: float = 0,
    config_manager=None,
    reformat_table_cb=None,
    get_report_filename_cb=None,
    scan_output_directory_cb=None
):
    """
    Implementation of showBacktestResults for delegation from globals.py.
    
    This function provides a procedural interface for displaying backtest results.
    """
    from pkscreener.classes.Utility import STD_ENCODING
    from pkscreener.classes import Utility
    from pkscreener.classes.PKScanRunner import PKScanRunner
    from pkscreener.classes.AssetsManager import PKAssetsManager
    from PKDevTools.classes.Committer import Committer
    
    pd.set_option("display.max_rows", 800)
    
    if backtest_df is None or backtest_df.empty or len(backtest_df) < 1:
        OutputControls().printOutput("Empty backtest dataframe encountered! Cannot generate the backtest report")
        return
    
    backtest_df.drop_duplicates(inplace=True)
    
    # Build summary text
    summary_text = (
        f"Auto-generated in {round(elapsed_time, 2)} sec. as of "
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
    
    # Tabulate results
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
            OutputControls().printOutput("ValueError! Going ahead without any column width restrictions!")
            tabulated_text = colorText.miniTabulator().tabulate(
                backtest_df,
                headers="keys",
                tablefmt=colorText.No_Pad_GridFormat,
                showindex=False,
            ).encode("utf-8").decode(STD_ENCODING)
    
    OutputControls().printOutput(colorText.FAIL + summary_text + colorText.END + "\n")
    OutputControls().printOutput(tabulated_text + "\n")
    
    # Get filename
    if get_report_filename_cb:
        choices_str, filename = get_report_filename_cb(sort_key, optional_name, choices=choices)
    else:
        if choices is None:
            choices_str = PKScanRunner.getFormattedChoices(user_passed_args, selected_choice).strip() if user_passed_args and selected_choice else ""
        else:
            choices_str = choices
        filename = f"PKScreener_{choices_str}_{optional_name}_{sort_key if sort_key else 'Default'}Sorted.html"
    
    # Build header dict
    header_dict = {0: "<th></th>"}
    index = 1
    for col in backtest_df.columns:
        if col != "Stock":
            header_dict[index] = f"<th>{col}</th>"
            index += 1
    
    colored_text = backtest_df.to_html(index=False)
    summary_text_html = summary_text.replace("\n", "<br />")
    
    if "Summary" in optional_name:
        summary_text_html = (
            f"{summary_text_html}<br /><input type='checkbox' id='chkActualNumbers' "
            f"name='chkActualNumbers' value='0'><label for='chkActualNumbers'>"
            f"Sort by actual numbers (Stocks + Date combinations of results. "
            f"Higher the count, better the prediction reliability)</label><br>"
        )
    
    if reformat_table_cb:
        colored_text = reformat_table_cb(summary_text_html, header_dict, colored_text, sorting=True)
    
    # Get output directory
    if scan_output_directory_cb:
        output_dir = scan_output_directory_cb(True)
    else:
        dir_name = "Backtest-Reports"
        output_dir = os.path.join(os.getcwd(), dir_name)
        if not os.path.isdir(output_dir):
            os.makedirs(os.path.dirname(os.path.join(os.getcwd(), f"{dir_name}{os.sep}")), exist_ok=True)
    
    filename = os.path.join(output_dir, filename)
    
    # Save file
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
        if config_manager and config_manager.alwaysExportToExcel:
            excel_sheet_name = filename.split(os.sep)[-1].replace("PKScreener_", "").replace(".html", "")
            default_answer = user_passed_args.answerdefault if user_passed_args else None
            PKAssetsManager.promptSaveResults(
                sheetName=excel_sheet_name, 
                df_save=backtest_df, 
                defaultAnswer=default_answer, 
                pastDate=None
            )
    except Exception:
        pass
    
    # Handle summary row
    if last_summary_row is not None and reformat_table_cb:
        oneline_text = last_summary_row.to_html(header=False, index=False)
        oneline_text = reformat_table_cb(summary_text_html, header_dict, oneline_text, sorting=False)
        oneline_summary_file = f"PKScreener_{choices_str}_OneLine_{optional_name}.html"
        oneline_summary_file = os.path.join(output_dir, oneline_summary_file)
        
        try:
            os.remove(oneline_summary_file)
        except Exception:
            pass
        finally:
            oneline_text = (
                f"{oneline_text}<td class='w'>"
                f"{PKDateUtilities.currentDateTime().strftime('%Y/%m/%d')}</td>"
                f"<td class='w'>{round(elapsed_time, 2)}</td>"
            )
            with open(oneline_summary_file, "w") as f:
                f.write(oneline_text)
            if "RUNNER" in os.environ.keys():
                Committer.execOSCommand(f"git add {oneline_summary_file} -f >/dev/null 2>&1")


def tabulate_backtest_results_impl(
    save_results: pd.DataFrame,
    max_allowed: int = 0,
    force: bool = False,
    config_manager=None,
    get_summary_cb=None
) -> Tuple[str, str]:
    """
    Implementation of tabulateBacktestResults for delegation from globals.py.
    
    Returns:
        Tuple of (tabulated_backtest_summary, tabulated_backtest_detail)
    """
    from pkscreener.classes import Utility
    from pkscreener.classes.Utility import STD_ENCODING
    
    if "PKDevTools_Default_Log_Level" not in os.environ.keys():
        if ("RUNNER" not in os.environ.keys()) or ("RUNNER" in os.environ.keys() and not force):
            return None, None
    
    if config_manager and not config_manager.showPastStrategyData:
        return None, None
    
    tabulated_backtest_summary = ""
    tabulated_backtest_detail = ""
    
    if get_summary_cb:
        summary_df, detail_df = get_summary_cb(save_results)
    else:
        return None, None
    
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
            + "\n  [+] For chosen scan, summary of correctness from past: [Example, 70% of (100) under 1-Pd, means out of 100 stocks that were in the scan result in the past, 70% of them gained next day.)"
            + colorText.END
        )
        OutputControls().printOutput(tabulated_backtest_summary)
    
    if tabulated_backtest_detail != "":
        OutputControls().printOutput(
            colorText.FAIL
            + "\n  [+] 1 to 30 period gain/loss % on respective date for matching stocks from earlier predictions:[Example, 5% under 1-Pd, means the stock price actually gained 5% the next day from given date.]"
            + colorText.END
        )
        OutputControls().printOutput(tabulated_backtest_detail)
    
    return tabulated_backtest_summary, tabulated_backtest_detail


def finish_backtest_data_cleanup_impl(
    backtest_df: pd.DataFrame,
    df_xray: pd.DataFrame,
    default_answer=None,
    config_manager=None,
    show_backtest_cb=None,
    backtest_summary_cb=None
) -> Tuple[pd.DataFrame, bool, Dict[str, str]]:
    """
    Implementation of FinishBacktestDataCleanup for delegation from globals.py.
    
    Returns:
        Tuple of (summary_df, sorting, sortKeys)
    """
    from pkscreener.classes.PKTask import PKTask
    from pkscreener.classes.PKScheduler import PKScheduler
    from pkscreener.classes.Portfolio import PortfolioCollection
    
    # Show XRay results
    if df_xray is not None and len(df_xray) > 10:
        if show_backtest_cb:
            show_backtest_cb(df_xray, sortKey="Date", optionalName="Insights")
    
    # Get summary
    summary_df = backtest_summary_cb(backtest_df) if backtest_summary_cb else None
    
    # Format dates
    backtest_df.loc[:, "Date"] = backtest_df.loc[:, "Date"].apply(
        lambda x: x.replace("-", "/")
    )
    
    # Show results
    if show_backtest_cb:
        show_backtest_cb(backtest_df)
        if summary_df is not None:
            show_backtest_cb(summary_df, optionalName="Summary")
    
    sorting = False if default_answer is not None else True
    tasks_list = []
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
    
    if config_manager and config_manager.enablePortfolioCalculations:
        if 'RUNNER' not in os.environ.keys():
            task1 = PKTask("PortfolioLedger", long_running_fn=PortfolioCollection().getPortfoliosAsDataframe)
            task2 = PKTask("PortfolioLedgerSnapshots", long_running_fn=PortfolioCollection().getLedgerSummaryAsDataframe)
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
            if task.result is not None and show_backtest_cb:
                show_backtest_cb(task.result, sortKey=None, optionalName=task.taskName)
    
    return summary_df, sorting, sort_keys


def prepare_grouped_xray_impl(
    backtest_period: int,
    backtest_df: pd.DataFrame,
    user_passed_args,
    remove_unused_columns_cb=None
) -> Optional[pd.DataFrame]:
    """
    Implementation of prepareGroupedXRay for delegation from globals.py.
    
    Returns:
        XRay DataFrame
    """
    import numpy as np
    from halo import Halo
    from pkscreener.classes.PKTask import PKTask
    from pkscreener.classes.PKScheduler import PKScheduler
    from pkscreener.classes import PortfolioXRay
    
    df_grouped = backtest_df.groupby("Date")
    user_passed_args.backtestdaysago = backtest_period
    df_xray = None
    group_counter = 0
    tasks_list = []
    
    for calc_for_date, df_group in df_grouped:
        group_counter += 1
        func_args = (
            df_group, user_passed_args, calc_for_date,
            f"Portfolio X-Ray | {calc_for_date} | {group_counter} of {len(df_grouped)}"
        )
        task = PKTask(
            f"Portfolio X-Ray | {calc_for_date} | {group_counter} of {len(df_grouped)}",
            long_running_fn=PortfolioXRay.performXRay,
            long_running_fn_args=func_args
        )
        task.total = len(df_grouped)
        tasks_list.append(task)
    
    try:
        if 'RUNNER' not in os.environ.keys():
            PKScheduler.scheduleTasks(
                tasks_list,
                f"Portfolio X-Ray for ({len(df_grouped)})",
                showProgressBars=False,
                timeout=600
            )
        else:
            # On Github CI, let's run synchronously
            for task in tasks_list:
                task.long_running_fn(*(task,))
        
        for task in tasks_list:
            p_df = task.result
            if p_df is not None:
                if df_xray is not None:
                    df_xray = pd.concat([df_xray, p_df.copy()], axis=0)
                else:
                    df_xray = p_df.copy()
        
        # Remove unused columns
        if remove_unused_columns_cb:
            remove_unused_columns_cb(
                None, backtest_df,
                ["Consol.", "Breakout", "RSI", "Pattern", "CCI"],
                userArgs=user_passed_args
            )
        
        df_xray = df_xray.replace(np.nan, "", regex=True)
        df_xray = PortfolioXRay.xRaySummary(df_xray)
        df_xray.loc[:, "Date"] = df_xray.loc[:, "Date"].apply(
            lambda x: x.replace("-", "/")
        )
    except Exception as e:
        default_logger().debug(e, exc_info=True)
    
    return df_xray


def show_sorted_backtest_data_impl(
    backtest_df: pd.DataFrame,
    summary_df: pd.DataFrame,
    sort_keys: Dict[str, str],
    default_answer=None,
    show_backtest_cb=None
) -> bool:
    """
    Implementation of showSortedBacktestData for delegation from globals.py.
    
    Returns:
        Boolean indicating if sorting should continue
    """
    from pkscreener.classes import ConsoleUtility
    
    OutputControls().printOutput(
        colorText.FAIL
        + "  [+] Would you like to sort the results?"
        + colorText.END
    )
    OutputControls().printOutput(
        colorText.GREEN
        + "  [+] Press :\n   [+] s, v, t, m : sort by Stocks, Volume, Trend, MA-Signal\n   [+] d : sort by date\n   [+] 1,2,3...30 : sort by period\n   [+] n : Exit sorting\n"
        + colorText.END
    )
    
    sorting = True
    if default_answer is None:
        choice = OutputControls().takeUserInput(colorText.FAIL + "  [+] Select option:")
        OutputControls().printOutput(colorText.END, end="")
        
        if choice.upper() in sort_keys.keys():
            ConsoleUtility.PKConsoleTools.clearScreen(forceTop=True)
            if show_backtest_cb:
                show_backtest_cb(backtest_df, sort_keys[choice.upper()])
                show_backtest_cb(summary_df, optionalName="Summary")
        else:
            sorting = False
    else:
        OutputControls().printOutput("Finished backtesting!")
        sorting = False
    
    return sorting
