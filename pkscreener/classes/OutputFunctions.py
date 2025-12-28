"""
OutputFunctions - Output and display functions for PKScreener

This module contains functions for displaying results, formatting output,
saving files, and sending notifications.
"""

import os
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from PKDevTools.classes.ColorText import colorText
from PKDevTools.classes.OutputControls import OutputControls
from PKDevTools.classes.PKDateUtilities import PKDateUtilities
from PKDevTools.classes import Archiver
from PKDevTools.classes.log import default_logger
from PKDevTools.classes.Telegram import (
    is_token_telegram_configured, send_document, send_message, send_photo
)

from pkscreener.classes import Utility, ConsoleUtility, ImageUtility
from pkscreener.classes.Utility import STD_ENCODING
from pkscreener.classes.Backtest import backtestSummary
from pkscreener.classes.PKScanRunner import PKScanRunner
from pkscreener.classes.MenuOptions import INDICES_MAP


def format_run_option_name(user_passed_args, selected_choice: Dict[str, str]) -> str:
    """Get formatted run option name"""
    run_option_name = PKScanRunner.getFormattedChoices(user_passed_args, selected_choice)
    
    if user_passed_args and user_passed_args.progressstatus is not None:
        if ":0:" in run_option_name or "_0_" in run_option_name:
            run_option_name = user_passed_args.progressstatus.split("=>")[0].split("  [+] ")[1].strip()
    
    return run_option_name


def get_index_name(run_option_name: str) -> str:
    """Get index name from run option"""
    if not run_option_name or not run_option_name.startswith("P"):
        return ""
    
    parts = run_option_name.split('_')
    if len(parts) >= 4:
        last_part = parts[-1]
        if last_part.isnumeric():
            idx = int(last_part)
            if idx <= int(list(INDICES_MAP.keys())[-2]):
                return f" for {INDICES_MAP.get(last_part, '')}"
    return ""


def show_backtest_results(
    backtest_df: pd.DataFrame,
    sort_key: str = "Stock",
    optional_name: str = "backtest_result",
    choices: Dict[str, str] = None,
    menu_choice_hierarchy: str = "",
    user_passed_args=None,
    elapsed_time: float = 0
):
    """Show backtest results"""
    pd.set_option("display.max_rows", 800)
    
    if backtest_df is None or len(backtest_df) == 0:
        OutputControls().printOutput(
            f"{colorText.FAIL}No backtest results to display.{colorText.END}"
        )
        return
    
    # Sort results
    if sort_key in backtest_df.columns:
        try:
            backtest_df = backtest_df.sort_values(sort_key, ascending=False)
        except Exception:
            pass
    
    # Format and display
    try:
        tabulated = colorText.miniTabulator().tabulate(
            backtest_df, headers="keys",
            tablefmt=colorText.No_Pad_GridFormat,
            maxcolwidths=Utility.tools.getMaxColumnWidths(backtest_df)
        ).encode("utf-8").decode(STD_ENCODING)
        
        OutputControls().printOutput(tabulated, enableMultipleLineOutput=True)
    except Exception as e:
        default_logger().debug(e, exc_info=True)
        OutputControls().printOutput(str(backtest_df))


def finish_backtest_data_cleanup(
    backtest_df: pd.DataFrame,
    df_xray: Optional[pd.DataFrame],
    default_answer=None
) -> Optional[pd.DataFrame]:
    """Finish backtest data cleanup and display results"""
    if df_xray is not None and len(df_xray) > 10:
        show_backtest_results(df_xray, sortKey="Date", optionalName="Insights")
    
    summary_df = backtestSummary(backtest_df)
    
    if backtest_df is not None and "Date" in backtest_df.columns:
        backtest_df.loc[:, "Date"] = backtest_df.loc[:, "Date"].apply(
            lambda x: x.replace("-", "/")
        )
    
    show_backtest_results(backtest_df)
    show_backtest_results(summary_df, optionalName="Summary")
    
    return summary_df


def scan_output_directory(backtest: bool = False) -> str:
    """Get output directory for scan results"""
    if backtest:
        return Archiver.get_user_reports_dir()
    return Archiver.get_user_outputs_dir()


def get_backtest_report_filename(
    sort_key: str = "Stock",
    optional_name: str = "backtest_result",
    choices: Dict[str, str] = None
) -> Tuple[str, str]:
    """Get backtest report filename"""
    if choices is None:
        choices = {}
    
    choice_str = "_".join([v for v in choices.values() if v])
    if not choice_str:
        choice_str = "default"
    
    filename = f"PKS_{optional_name}_{choice_str}.html"
    directory = Archiver.get_user_reports_dir()
    
    return directory, filename


def save_screen_results_encoded(encoded_text: str, output_dir: str = None) -> Optional[str]:
    """Save screen results to encoded file"""
    if encoded_text is None or len(encoded_text) == 0:
        return None
    
    try:
        if output_dir is None:
            output_dir = os.path.join(Archiver.get_user_outputs_dir(), "DeleteThis")
        
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = PKDateUtilities.currentDateTime().strftime("%d-%m-%y_%H.%M.%S")
        filename = f"results_{timestamp}.txt"
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(encoded_text)
        
        return f"{filename}~{timestamp.split('_')[0]}~{timestamp.split('_')[1]}"
    except Exception as e:
        default_logger().debug(e, exc_info=True)
        return None


def read_screen_results_decoded(filename: str = None, output_dir: str = None) -> Optional[str]:
    """Read screen results from encoded file"""
    if filename is None:
        return None
    
    try:
        if output_dir is None:
            output_dir = os.path.join(Archiver.get_user_outputs_dir(), "DeleteThis")
        
        filepath = os.path.join(output_dir, filename)
        
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()
    except Exception as e:
        default_logger().debug(e, exc_info=True)
    
    return None


def show_option_error_message():
    """Show option error message - only in interactive mode"""
    # Only show error message and wait if in interactive mode
    if not OutputControls().enableUserInput:
        return  # Skip error message in non-interactive/bot mode
    
    from time import sleep
    OutputControls().printOutput(
        f"{colorText.FAIL}\n  [+] Please enter a valid option & Try Again!{colorText.END}"
    )
    sleep(2)
    ConsoleUtility.PKConsoleTools.clearScreen(forceTop=True)


def cleanup_local_results():
    """Cleanup local results"""
    try:
        output_dir = Archiver.get_user_outputs_dir()
        delete_folder = os.path.join(output_dir, "DeleteThis")
        
        if os.path.exists(delete_folder):
            import shutil
            shutil.rmtree(delete_folder, ignore_errors=True)
        
        os.makedirs(delete_folder, exist_ok=True)
    except Exception as e:
        default_logger().debug(e, exc_info=True)


def reformat_table(
    summary_text: str,
    header_dict: Dict[str, str],
    colored_text: str,
    sorting: bool = True
) -> str:
    """Reformat table with custom headers"""
    if summary_text is None:
        return colored_text
    
    try:
        # Apply header replacements
        for old_header, new_header in header_dict.items():
            colored_text = colored_text.replace(old_header, new_header)
    except Exception as e:
        default_logger().debug(e, exc_info=True)
    
    return colored_text


def remove_unknowns(
    screen_results: pd.DataFrame,
    save_results: pd.DataFrame
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Remove unknown/invalid rows from results"""
    if screen_results is None or len(screen_results) == 0:
        return screen_results, save_results
    
    try:
        # Remove rows where all values are '-' or empty
        mask = (screen_results != '-').any(axis=1)
        screen_results = screen_results[mask]
        
        if save_results is not None and len(save_results) > 0:
            save_results = save_results[save_results.index.isin(screen_results.index)]
    except Exception as e:
        default_logger().debug(e, exc_info=True)
    
    return screen_results, save_results


def removed_unused_columns(
    screen_results: pd.DataFrame,
    save_results: pd.DataFrame,
    drop_additional_columns: List[str] = None,
    user_args=None
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Remove unused columns from results"""
    if drop_additional_columns is None:
        drop_additional_columns = []
    
    columns_to_drop = list(drop_additional_columns)
    
    if user_args and hasattr(user_args, 'options') and user_args.options:
        if user_args.options.upper().startswith("C"):
            columns_to_drop.append("FairValue")
    
    for col in columns_to_drop:
        if screen_results is not None and col in screen_results.columns:
            screen_results.drop(col, axis=1, inplace=True, errors="ignore")
        if save_results is not None and col in save_results.columns:
            save_results.drop(col, axis=1, inplace=True, errors="ignore")
    
    return screen_results, save_results


def describe_user(user_passed_args):
    """Describe the current user"""
    if user_passed_args is None or user_passed_args.user is None:
        return
    
    try:
        from PKDevTools.classes.DBManager import DBManager
        db = DBManager()
        
        if db.url is not None and db.token is not None:
            user_info = db.userInfo(int(user_passed_args.user))
            if user_info is not None:
                default_logger().debug(f"User: {user_info}")
    except Exception as e:
        default_logger().debug(e, exc_info=True)


def user_report_name(user_menu_options: Dict[str, str]) -> str:
    """Generate user report name from menu options"""
    if user_menu_options is None:
        return "report"
    
    parts = [v for v in user_menu_options.values() if v]
    return "_".join(parts) if parts else "report"


def get_performance_stats() -> str:
    """Get performance statistics"""
    # This would typically gather and format performance metrics
    return ""


def get_mfi_stats(pop_option: int) -> Optional[pd.DataFrame]:
    """Get MFI statistics"""
    # Implementation depends on specific MFI calculation
    return None


def toggle_user_config(config_manager):
    """Toggle user configuration"""
    import pkscreener.classes.ConfigManager as ConfigManager
    config_manager.setConfig(ConfigManager.parser, default=False, showFileCreatedText=True)


def reset_config_to_default(config_manager, force: bool = False):
    """Reset configuration to default"""
    import pkscreener.classes.ConfigManager as ConfigManager
    config_manager.getConfig(ConfigManager.parser)
    if force:
        config_manager.setConfig(ConfigManager.parser, default=True, showFileCreatedText=False)

