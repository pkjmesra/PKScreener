"""
MenuNavigation - Menu navigation and choice handling for PKScreener

This module handles all menu-related operations including:
- Top-level menu choices
- Scanner menu choices
- Secondary menu handling (Help, Update, Config)
- Menu initialization and rendering
"""

import os
import sys
import urllib
from time import sleep
from typing import Dict, List, Optional, Tuple, Any

import numpy as np
import pandas as pd
from PKDevTools.classes.ColorText import colorText
from PKDevTools.classes.OutputControls import OutputControls
from PKDevTools.classes.PKDateUtilities import PKDateUtilities
from PKDevTools.classes import Archiver
from PKDevTools.classes.log import default_logger

from pkscreener.classes import Utility, ConsoleUtility, ImageUtility, AssetsManager
from pkscreener.classes.MenuOptions import menus
from pkscreener.classes.OtaUpdater import OTAUpdater
from pkscreener.classes.PKAnalytics import PKAnalyticsService
import pkscreener.classes.ConfigManager as ConfigManager


class MenuNavigator:
    """
    Handles menu navigation and user choices.
    
    This class encapsulates menu-related logic that was previously
    scattered in globals.py.
    """
    
    def __init__(self, config_manager, m0=None, m1=None, m2=None, m3=None, m4=None):
        self.config_manager = config_manager
        self.m0 = m0 or menus()
        self.m1 = m1 or menus()
        self.m2 = m2 or menus()
        self.m3 = m3 or menus()
        self.m4 = m4 or menus()
        self.selected_choice = {"0": "", "1": "", "2": "", "3": "", "4": ""}
        self.n_value_for_menu = 0
    
    def get_download_choices(self, default_answer=None, user_passed_args=None):
        """Get choices when download mode is active"""
        args_intraday = user_passed_args is not None and user_passed_args.intraday is not None
        intraday_config = self.config_manager.isIntradayConfig()
        intraday = intraday_config or args_intraday
        
        exists, cache_file = AssetsManager.PKAssetsManager.afterMarketStockDataExists(intraday)
        if exists:
            should_replace = AssetsManager.PKAssetsManager.promptFileExists(
                cache_file=cache_file, defaultAnswer=default_answer
            )
            if should_replace == "N":
                OutputControls().printOutput(
                    cache_file + colorText.END +
                    " already exists. Exiting as user chose not to replace it!"
                )
                PKAnalyticsService().send_event("app_exit")
                sys.exit(0)
            else:
                pattern = f"{'intraday_' if intraday else ''}stock_data_*.pkl"
                self.config_manager.deleteFileWithPattern(
                    rootDir=Archiver.get_user_data_dir(), 
                    pattern=pattern
                )
        return "X", 12, 0, {"0": "X", "1": "12", "2": "0"}
    
    def get_historical_days(self, num_stocks: int, testing: bool) -> int:
        """Calculate historical days for backtesting"""
        return 2 if testing else self.config_manager.backtestPeriod
    
    def get_test_build_choices(
        self, 
        index_option=None, 
        execute_option=None, 
        menu_option=None
    ):
        """Get choices for test build mode"""
        if menu_option is not None:
            return (
                str(menu_option),
                index_option if index_option is not None else 1,
                execute_option if execute_option is not None else 0,
                {
                    "0": str(menu_option),
                    "1": str(index_option) if index_option is not None else "1",
                    "2": str(execute_option) if execute_option is not None else "0",
                },
            )
        return "X", 1, 0, {"0": "X", "1": "1", "2": "0"}
    
    def get_top_level_menu_choices(
        self,
        startup_options: Optional[str],
        test_build: bool,
        download_only: bool,
        default_answer=None,
        user_passed_args=None,
        last_scan_output_stock_codes=None
    ):
        """
        Get top-level menu choices from user or startup options.
        
        Returns:
            Tuple of (options, menu_option, index_option, execute_option)
        """
        execute_option = None
        menu_option = None
        index_option = None
        options = []
        
        if startup_options is not None:
            options = startup_options.split(":")
            menu_option = options[0] if len(options) >= 1 else None
            index_option = options[1] if len(options) >= 2 else None
            execute_option = options[2] if len(options) >= 3 else None
        
        if test_build:
            menu_option, index_option, execute_option, self.selected_choice = \
                self.get_test_build_choices(
                    index_option=index_option,
                    execute_option=execute_option,
                    menu_option=menu_option,
                )
        elif download_only:
            menu_option, index_option, execute_option, self.selected_choice = \
                self.get_download_choices(
                    default_answer=default_answer,
                    user_passed_args=user_passed_args
                )
            intraday = (user_passed_args.intraday if user_passed_args else False) or \
                       self.config_manager.isIntradayConfig()
            file_prefix = "INTRADAY_" if intraday else ""
            _, cache_file_name = AssetsManager.PKAssetsManager.afterMarketStockDataExists(intraday)
            Utility.tools.set_github_output(f"{file_prefix}DOWNLOAD_CACHE_FILE_NAME", cache_file_name)
        
        index_option = 0 if last_scan_output_stock_codes is not None else index_option
        return options, menu_option, index_option, execute_option
    
    def get_scanner_menu_choices(
        self,
        test_build=False,
        download_only=False,
        startup_options=None,
        menu_option=None,
        index_option=None,
        execute_option=None,
        default_answer=None,
        user=None,
        init_execution_cb=None,
        init_post_level0_cb=None,
        init_post_level1_cb=None,
    ):
        """
        Get scanner-specific menu choices.
        
        Returns:
            Tuple of (menu_option, index_option, execute_option, selected_choice)
        """
        try:
            if menu_option is None and init_execution_cb:
                selected_menu = init_execution_cb(menuOption=menu_option)
                menu_option = selected_menu.menuKey
            
            if menu_option in ["H", "U", "T", "E", "Y"]:
                self.handle_secondary_menu_choices(
                    menu_option, test_build, default_answer=default_answer, user=user
                )
                ConsoleUtility.PKConsoleTools.clearScreen(forceTop=True)
            elif menu_option in ["X", "C"]:
                if init_post_level0_cb:
                    index_option, execute_option = init_post_level0_cb(
                        menuOption=menu_option,
                        indexOption=index_option,
                        executeOption=execute_option,
                    )
                if init_post_level1_cb:
                    index_option, execute_option = init_post_level1_cb(
                        indexOption=index_option, 
                        executeOption=execute_option
                    )
        except KeyboardInterrupt:
            OutputControls().takeUserInput(
                colorText.FAIL + "  [+] Press <Enter> to Exit!" + colorText.END
            )
            PKAnalyticsService().send_event("app_exit")
            sys.exit(0)
        except Exception as e:
            default_logger().debug(e, exc_info=True)
        
        return menu_option, index_option, execute_option, self.selected_choice
    
    def handle_scanner_execute_option4(self, execute_option: int, options: List[str]):
        """Handle execute option 4 (lowest volume scanner)"""
        try:
            if len(options) >= 4:
                if str(options[3]).upper() == "D":
                    days_for_lowest_volume = 5
                else:
                    days_for_lowest_volume = int(options[3])
            else:
                days_for_lowest_volume = int(
                    input(
                        colorText.WARN +
                        "\n  [+] The Volume should be lowest since last how many candles? (Default = 5)"
                    ) or "5"
                )
        except ValueError as e:
            default_logger().debug(e, exc_info=True)
            OutputControls().printOutput(colorText.END)
            OutputControls().printOutput(
                colorText.FAIL +
                "  [+] Error: Non-numeric value entered! Please try again!" +
                colorText.END
            )
            OutputControls().takeUserInput("Press <Enter> to continue...")
            return None
        
        OutputControls().printOutput(colorText.END)
        self.n_value_for_menu = days_for_lowest_volume
        return days_for_lowest_volume
    
    def handle_secondary_menu_choices(
        self,
        menu_option: str,
        testing=False,
        default_answer=None,
        user=None,
        user_passed_args=None,
        results_contents_encoded=None,
        send_message_cb=None,
        toggle_config_cb=None,
        version=None
    ):
        """Handle secondary menu options (H, U, T, E, Y)"""
        if menu_option == "H":
            self._show_send_help_info(default_answer, user, send_message_cb)
        elif menu_option == "U":
            OTAUpdater.checkForUpdate(version or "0.0", skipDownload=testing)
            if default_answer is None:
                OutputControls().takeUserInput("Press <Enter> to continue...")
        elif menu_option == "T":
            self._handle_period_duration_menu(
                user_passed_args, default_answer, 
                results_contents_encoded, toggle_config_cb
            )
        elif menu_option == "E":
            self.config_manager.setConfig(ConfigManager.parser)
        elif menu_option == "Y":
            self._show_send_config_info(default_answer, user, send_message_cb)
    
    def _show_send_config_info(self, default_answer=None, user=None, send_message_cb=None):
        """Show and optionally send configuration info"""
        config_data = self.config_manager.showConfigFile(
            defaultAnswer='Y' if user is not None else default_answer
        )
        if user is not None and send_message_cb:
            send_message_cb(
                message=ImageUtility.PKImageTools.removeAllColorStyles(config_data),
                user=user
            )
        if default_answer is None:
            input("Press any key to continue...")
    
    def _show_send_help_info(self, default_answer=None, user=None, send_message_cb=None):
        """Show and optionally send help info"""
        help_data = ConsoleUtility.PKConsoleTools.showDevInfo(
            defaultAnswer='Y' if user is not None else default_answer
        )
        if user is not None and send_message_cb:
            send_message_cb(
                message=ImageUtility.PKImageTools.removeAllColorStyles(help_data),
                user=user
            )
        if default_answer is None:
            input("Press any key to continue...")
    
    def _handle_period_duration_menu(
        self, 
        user_passed_args, 
        default_answer, 
        results_contents_encoded,
        toggle_config_cb
    ):
        """Handle period/duration configuration menu"""
        if user_passed_args is None or user_passed_args.options is None:
            selected_menu = self.m0.find("T")
            self.m1.renderForMenu(selectedMenu=selected_menu)
            period_option = OutputControls().takeUserInput(
                colorText.FAIL + "  [+] Select option: "
            ) or ('L' if self.config_manager.period == '1y' else 'S')
            OutputControls().printOutput(colorText.END, end="")
            
            if period_option is None or period_option.upper() not in ["L", "S", "B"]:
                return
            
            ConsoleUtility.PKConsoleTools.clearScreen(forceTop=True)
            
            if period_option.upper() in ["L", "S"]:
                self._handle_period_selection(period_option)
            elif period_option.upper() == "B":
                self._handle_backtest_mode(
                    user_passed_args, results_contents_encoded
                )
        elif user_passed_args.options is not None:
            options = user_passed_args.options.split(":")
            selected_menu = self.m0.find(options[0])
            self.m1.renderForMenu(selectedMenu=selected_menu, asList=True)
            selected_menu = self.m1.find(options[1])
            self.m2.renderForMenu(selectedMenu=selected_menu, asList=True)
            
            if options[2] in ["1", "2", "3", "4"]:
                selected_menu = self.m2.find(options[2])
                period_durations = selected_menu.menuText.split("(")[1].split(")")[0].split(", ")
                self.config_manager.period = period_durations[0]
                self.config_manager.duration = period_durations[1]
                self.config_manager.setConfig(
                    ConfigManager.parser, default=True, showFileCreatedText=False
                )
            elif toggle_config_cb:
                toggle_config_cb()
        elif toggle_config_cb:
            toggle_config_cb()
    
    def _handle_period_selection(self, period_option: str):
        """Handle period/duration selection"""
        selected_menu = self.m1.find(period_option)
        self.m2.renderForMenu(selectedMenu=selected_menu)
        duration_option = OutputControls().takeUserInput(colorText.FAIL + "  [+] Select option: ") or "1"
        OutputControls().printOutput(colorText.END, end="")
        
        if duration_option is None or duration_option.upper() not in ["1", "2", "3", "4", "5"]:
            return
        
        ConsoleUtility.PKConsoleTools.clearScreen(forceTop=True)
        
        if duration_option.upper() in ["1", "2", "3", "4"]:
            selected_menu = self.m2.find(duration_option)
            period_durations = selected_menu.menuText.split("(")[1].split(")")[0].split(", ")
            self.config_manager.period = period_durations[0]
            self.config_manager.duration = period_durations[1]
            self.config_manager.setConfig(
                ConfigManager.parser, default=True, showFileCreatedText=False
            )
            self.config_manager.deleteFileWithPattern(
                rootDir=Archiver.get_user_data_dir(), pattern="*stock_data_*.pkl*"
            )
        elif duration_option.upper() == "5":
            self.config_manager.setConfig(
                ConfigManager.parser, default=False, showFileCreatedText=True
            )
            self.config_manager.deleteFileWithPattern(
                rootDir=Archiver.get_user_data_dir(), pattern="*stock_data_*.pkl*"
            )
    
    def _handle_backtest_mode(self, user_passed_args, results_contents_encoded):
        """Handle quick backtest mode selection"""
        last_trading_date = PKDateUtilities.nthPastTradingDateStringFromFutureDate(
            n=(22 if self.config_manager.period == '1y' else 15)
        )
        backtest_days_ago = OutputControls().takeUserInput(
            f"{colorText.FAIL}  [+] Enter no. of days/candles in the past as starting candle\n"
            f"  [+] You can also enter a past date in {colorText.END}{colorText.GREEN}YYYY-MM-DD{colorText.END}"
            f"{colorText.FAIL} format\n"
            f"  [+] (e.g. {colorText.GREEN}10{colorText.END} or {colorText.GREEN}0{colorText.END} for today "
            f"or {colorText.GREEN}{last_trading_date}{colorText.END}):"
        ) or ('22' if self.config_manager.period == '1y' else '15')
        
        OutputControls().printOutput(colorText.END, end="")
        
        if len(str(backtest_days_ago)) >= 3 and "-" in str(backtest_days_ago):
            try:
                backtest_days_ago = abs(PKDateUtilities.trading_days_between(
                    d1=PKDateUtilities.dateFromYmdString(str(backtest_days_ago)),
                    d2=PKDateUtilities.currentDateTime()
                ))
            except Exception as e:
                default_logger().debug(e, exc_info=True)
                OutputControls().printOutput("An error occurred! Going ahead with default inputs.")
                backtest_days_ago = '22' if self.config_manager.period == '1y' else '15'
                sleep(3)
        
        launcher = f'"{sys.argv[0]}"' if " " in sys.argv[0] else sys.argv[0]
        launcher = f"python3.12 {launcher}" if launcher.endswith(".py") or launcher.endswith('.py"') else launcher
        
        params = []
        if user_passed_args:
            if user_passed_args.user is not None:
                params.append(f" -u {user_passed_args.user}")
            if user_passed_args.log:
                params.append(" -l")
            if user_passed_args.telegram:
                params.append(" --telegram")
            if user_passed_args.stocklist:
                params.append(f" --stocklist {user_passed_args.stocklist}")
            if user_passed_args.slicewindow:
                params.append(f" --slicewindow {user_passed_args.slicewindow}")
        if results_contents_encoded:
            params.append(f" --fname {results_contents_encoded}")
        
        extra_params = "".join(params)
        
        OutputControls().printOutput(
            f"{colorText.GREEN}Launching PKScreener in quick backtest mode.{colorText.END}\n"
            f"{colorText.FAIL}{launcher} --backtestdaysago {int(backtest_days_ago)}{extra_params}{colorText.END}\n"
            f"{colorText.WARN}Press Ctrl + C to exit quick backtest mode.{colorText.END}"
        )
        sleep(2)
        os.system(
            f"{launcher} --systemlaunched -a Y -e --backtestdaysago {int(backtest_days_ago)}{extra_params}"
        )
        ConsoleUtility.PKConsoleTools.clearScreen(clearAlways=True, forceTop=True)
    
    def ensure_menus_loaded(self, menu_option=None, index_option=None, execute_option=None):
        """Ensure menu dictionaries are loaded"""
        try:
            if len(self.m0.menuDict.keys()) == 0:
                self.m0.renderForMenu(asList=True)
            if len(self.m1.menuDict.keys()) == 0:
                self.m1.renderForMenu(selectedMenu=self.m0.find(menu_option), asList=True)
            if len(self.m2.menuDict.keys()) == 0:
                self.m2.renderForMenu(selectedMenu=self.m1.find(index_option), asList=True)
        except Exception as e:
            default_logger().debug(e, exc_info=True)
    
    def get_summary_correctness_of_strategy(self, result_df, summary_required=True):
        """Get summary and detail dataframes for strategy correctness"""
        from pkscreener.classes.BacktestUtils import get_backtest_report_filename
        
        summary_df = None
        detail_df = None
        
        try:
            if result_df is None or len(result_df) == 0:
                return None, None
            
            results = result_df.copy()
            
            if summary_required:
                _, report_name_summary = get_backtest_report_filename(optionalName="Summary")
                dfs = pd.read_html(
                    f"https://pkjmesra.github.io/PKScreener/Backtest-Reports/{report_name_summary.replace('_X_', '_B_').replace('_G_', '_B_').replace('_S_', '_B_')}",
                    encoding="UTF-8",
                    attrs={'id': 'resultsTable'}
                )
            
            _, report_name_detail = get_backtest_report_filename()
            dfd = pd.read_html(
                f"https://pkjmesra.github.io/PKScreener/Backtest-Reports/{report_name_detail.replace('_X_', '_B_').replace('_G_', '_B_').replace('_S_', '_B_')}",
                encoding="UTF-8",
                attrs={'id': 'resultsTable'}
            )
            
            if summary_required and dfs is not None and len(dfs) > 0:
                df = dfs[0]
                summary_df = df[df["Stock"] == "SUMMARY"]
                for col in summary_df.columns:
                    summary_df.loc[:, col] = summary_df.loc[:, col].apply(
                        lambda x: ConsoleUtility.PKConsoleTools.getFormattedBacktestSummary(x, columnName=col)
                    )
                summary_df = summary_df.replace(np.nan, "", regex=True)
            
            if dfd is not None and len(dfd) > 0:
                df = dfd[0]
                results.reset_index(inplace=True)
                detail_df = df[df["Stock"].isin(results["Stock"])]
                for col in detail_df.columns:
                    detail_df.loc[:, col] = detail_df.loc[:, col].apply(
                        lambda x: ConsoleUtility.PKConsoleTools.getFormattedBacktestSummary(x, pnlStats=True, columnName=col)
                    )
                detail_df = detail_df.replace(np.nan, "", regex=True)
                detail_df.loc[:, "volume"] = detail_df.loc[:, "volume"].apply(
                    lambda x: Utility.tools.formatRatio(x, self.config_manager.volumeRatio)
                )
                detail_df.sort_values(["Stock", "Date"], ascending=[True, False], inplace=True)
                detail_df.rename(columns={"LTP": "LTP on Date"}, inplace=True)
                
        except urllib.error.HTTPError as e:
            if "HTTP Error 404" not in str(e):
                default_logger().debug(e, exc_info=True)
        except Exception as e:
            default_logger().debug(e, exc_info=True)
        
        return summary_df, detail_df
    
    def update_menu_choice_hierarchy(
        self, 
        selected_choice: Dict[str, str],
        user_passed_args=None
    ) -> str:
        """Update and return the menu choice hierarchy string"""
        choice_values = [v for v in selected_choice.values() if v]
        hierarchy = " > ".join(choice_values)
        
        if user_passed_args and hasattr(user_passed_args, 'pipedtitle') and user_passed_args.pipedtitle:
            hierarchy = f"{hierarchy} | {user_passed_args.pipedtitle}"
        
        return hierarchy
    
    def handle_exit_request(self, execute_option):
        """Handle exit request"""
        if execute_option is not None and str(execute_option).upper() == "Z":
            OutputControls().takeUserInput(
                colorText.FAIL + "  [+] Press <Enter> to Exit!" + colorText.END
            )
            PKAnalyticsService().send_event("app_exit")
            sys.exit(0)
    
    def handle_menu_xbg(self, menu_option: str, index_option, execute_option):
        """Handle menu options X, B, G"""
        if menu_option in ["X", "B", "G"]:
            self.selected_choice["0"] = menu_option
            if index_option is not None:
                self.selected_choice["1"] = str(index_option)
            if execute_option is not None:
                self.selected_choice["2"] = str(execute_option)


def update_menu_choice_hierarchy_impl(
    user_passed_args,
    selected_choice: Dict[str, str],
    config_manager,
    n_value_for_menu,
    level0_menu_dict,
    level1_x_menu_dict,
    level1_p_menu_dict,
    level2_x_menu_dict,
    level2_p_menu_dict,
    level3_reversal_dict,
    level3_chart_pattern_dict,
    level3_popular_stocks_dict,
    level3_potential_profitable_dict,
    level4_lorenzian_dict,
    level4_confluence_dict,
    level4_bbands_sqz_dict,
    level4_ma_signal_dict,
    price_cross_sma_ema_direction_dict,
    price_cross_sma_ema_type_dict,
    price_cross_pivot_point_type_dict,
    candlestick_dict
) -> str:
    """
    Build and return the menu choice hierarchy string.
    
    This function constructs a human-readable path showing the user's menu selections.
    """
    from PKDevTools.classes.ColorText import colorText
    from PKDevTools.classes.OutputControls import OutputControls
    from PKDevTools.classes.PKDateUtilities import PKDateUtilities
    from PKDevTools.classes.log import default_logger
    from pkscreener.classes import ConsoleUtility
    from pkscreener.classes.PKScanRunner import PKScanRunner
    from pkscreener.classes.PKAnalytics import PKAnalyticsService
    
    menu_choice_hierarchy = ""
    
    try:
        menu_choice_hierarchy = f'{level0_menu_dict[selected_choice["0"]].strip()}'
        top_level_menu_dict = level1_x_menu_dict if selected_choice["0"] not in "P" else level1_p_menu_dict
        level2_menu_dict = level2_x_menu_dict if selected_choice["0"] not in "P" else level2_p_menu_dict
        
        if len(selected_choice["1"]) > 0:
            menu_choice_hierarchy = f'{menu_choice_hierarchy}>{top_level_menu_dict[selected_choice["1"]].strip()}'
        if len(selected_choice["2"]) > 0:
            menu_choice_hierarchy = f'{menu_choice_hierarchy}>{level2_menu_dict[selected_choice["2"]].strip()}'
        
        if selected_choice["0"] not in "P":
            menu_choice_hierarchy = _add_level3_hierarchy(
                menu_choice_hierarchy, selected_choice,
                level3_reversal_dict, level3_chart_pattern_dict,
                level3_popular_stocks_dict, level3_potential_profitable_dict,
                level4_lorenzian_dict, level4_confluence_dict,
                level4_bbands_sqz_dict, level4_ma_signal_dict,
                price_cross_sma_ema_direction_dict, price_cross_sma_ema_type_dict,
                price_cross_pivot_point_type_dict, candlestick_dict
            )
        
        # Add intraday suffix if applicable
        is_intraday = (user_passed_args is not None and user_passed_args.intraday) or config_manager.isIntradayConfig()
        if "Intraday" not in menu_choice_hierarchy and is_intraday:
            menu_choice_hierarchy = f"{menu_choice_hierarchy}(Intraday)"
        
        # Replace N- placeholder with actual value
        menu_choice_hierarchy = menu_choice_hierarchy.replace("N-", f"{n_value_for_menu}-")
        
    except Exception:
        pass
    
    # Clear screen and print the hierarchy
    ConsoleUtility.PKConsoleTools.clearScreen(forceTop=True)
    
    needs_calc = user_passed_args is not None and user_passed_args.backtestdaysago is not None
    past_date = ""
    if needs_calc:
        past_date = f"[ {PKDateUtilities.nthPastTradingDateStringFromFutureDate(int(user_passed_args.backtestdaysago))} ]"
    
    report_title = ""
    if user_passed_args is not None and user_passed_args.pipedtitle is not None:
        report_title = f"{user_passed_args.pipedtitle}|"
    
    run_option_name = PKScanRunner.getFormattedChoices(user_passed_args, selected_choice)
    if user_passed_args is not None and user_passed_args.progressstatus is not None:
        if ":0:" in run_option_name or "_0_" in run_option_name:
            run_option_name = user_passed_args.progressstatus.split("=>")[0].split("  [+] ")[1].strip()
    
    if run_option_name is not None:
        report_title = f"{run_option_name} | {report_title}"
    
    if len(run_option_name) >= 5:
        PKAnalyticsService().send_event(run_option_name)
    
    piped_suffix = ""
    if user_passed_args is not None and user_passed_args.pipedmenus is not None:
        piped_suffix = f" (Piped Scan Mode) [{user_passed_args.pipedmenus}] {past_date}"
    
    OutputControls().printOutput(
        f"{colorText.FAIL}  [+] You chose: {report_title} {menu_choice_hierarchy}{piped_suffix}{colorText.END}"
    )
    default_logger().info(menu_choice_hierarchy)
    
    return menu_choice_hierarchy


def _add_level3_hierarchy(
    hierarchy: str,
    selected_choice: Dict[str, str],
    level3_reversal_dict,
    level3_chart_pattern_dict,
    level3_popular_stocks_dict,
    level3_potential_profitable_dict,
    level4_lorenzian_dict,
    level4_confluence_dict,
    level4_bbands_sqz_dict,
    level4_ma_signal_dict,
    price_cross_sma_ema_direction_dict,
    price_cross_sma_ema_type_dict,
    price_cross_pivot_point_type_dict,
    candlestick_dict
) -> str:
    """Add level 3 menu hierarchy based on execute option"""
    
    exec_option = selected_choice["2"]
    
    if exec_option == "6":  # Reversal
        hierarchy += f'>{level3_reversal_dict[selected_choice["3"]].strip()}'
        if len(selected_choice) >= 5 and selected_choice["3"] in ["7", "10"]:
            hierarchy += f'>{level4_lorenzian_dict[selected_choice["4"]].strip()}'
    
    elif exec_option in ["30"]:
        if len(selected_choice) >= 3:
            hierarchy += f'>{level4_lorenzian_dict[selected_choice["3"]].strip()}'
    
    elif exec_option == "7":  # Chart Patterns
        hierarchy += f'>{level3_chart_pattern_dict[selected_choice["3"]].strip()}'
        if len(selected_choice) >= 5:
            if selected_choice["3"] == "3":
                hierarchy += f'>{level4_confluence_dict[selected_choice["4"]].strip()}'
            elif selected_choice["3"] == "6":
                hierarchy += f'>{level4_bbands_sqz_dict[selected_choice["4"]].strip()}'
            elif selected_choice["3"] == "9":
                hierarchy += f'>{level4_ma_signal_dict[selected_choice["4"]].strip()}'
            elif selected_choice["3"] == "7":
                candle_name = candlestick_dict.get(selected_choice["4"], "No Filter")
                hierarchy += f'>{candle_name.strip() if selected_choice["4"] != "0" else "No Filter"}'
    
    elif exec_option == "21":  # Popular Stocks
        hierarchy += f'>{level3_popular_stocks_dict[selected_choice["3"]].strip()}'
    
    elif exec_option == "33":  # Potential Profitable
        hierarchy += f'>{level3_potential_profitable_dict[selected_choice["3"]].strip()}'
    
    elif exec_option == "40":  # Price Cross SMA/EMA
        hierarchy += f'>{price_cross_sma_ema_direction_dict[selected_choice["3"]].strip()}'
        hierarchy += f'>{price_cross_sma_ema_type_dict[selected_choice["4"]].strip()}'
    
    elif exec_option == "41":  # Pivot Points
        hierarchy += f'>{price_cross_pivot_point_type_dict[selected_choice["3"]].strip()}'
        hierarchy += f'>{price_cross_sma_ema_direction_dict[selected_choice["4"]].strip()}'
    
    return hierarchy

