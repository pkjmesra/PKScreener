#!/usr/bin/python3
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

"""
PKCliRunner - Refactored CLI Runner for PKScreener

This module handles the CLI application execution, including:
- Intraday analysis report generation
- Progress status updates
- Monitor and piped scan handling
- Configuration duration management
"""

import os
import sys
import traceback
from time import sleep

from PKDevTools.classes.ColorText import colorText
from PKDevTools.classes.log import default_logger
from PKDevTools.classes.PKDateUtilities import PKDateUtilities
from PKDevTools.classes.OutputControls import OutputControls
from PKDevTools.classes import Archiver

import pkscreener.classes.ConfigManager as ConfigManager


class PKCliRunner:
    """
    Handles CLI execution flow including application running,
    piped scans, and monitor modes.
    """
    
    def __init__(self, config_manager, args):
        """
        Initialize the CLI runner.
        
        Args:
            config_manager: Configuration manager instance
            args: Parsed command line arguments
        """
        self.config_manager = config_manager
        self.args = args
        self.results = None
        self.result_stocks = None
        self.plain_results = None
        self.db_timestamp = None
        self.elapsed_time = 0
        self.start_time = None
    
    def update_progress_status(self, monitor_options=None):
        """
        Update progress status for display.
        
        Args:
            monitor_options: Optional monitor options string
            
        Returns:
            tuple: (args, choices)
        """
        from pkscreener.classes.MenuOptions import PREDEFINED_SCAN_MENU_TEXTS, PREDEFINED_SCAN_MENU_VALUES
        
        choices = ""
        try:
            if self.args.systemlaunched or monitor_options is not None:
                options_to_use = self.args.options if monitor_options is None else monitor_options
                choices = f"--systemlaunched -a y -e -o '{options_to_use.replace('C:','X:').replace('D:','')}'"
                
                from pkscreener.classes.MenuOptions import INDICES_MAP
                search_choices = choices
                for index_key in INDICES_MAP.keys():
                    if index_key.isnumeric():
                        search_choices = search_choices.replace(f"X:{index_key}:", "X:12:")
                
                index_num = PREDEFINED_SCAN_MENU_VALUES.index(search_choices)
                selected_index_option = choices.split(":")[1]
                choices = f"P_1_{str(index_num + 1)}_{str(selected_index_option)}" if ">|" in choices else choices
                self.args.progressstatus = f"  [+] {choices} => Running {choices}"
                self.args.usertag = PREDEFINED_SCAN_MENU_TEXTS[index_num]
                self.args.maxdisplayresults = 2000
        except Exception as e:
            default_logger().debug(f"Error handling predefined scan: {e}")
            choices = ""
        
        return self.args, choices
    
    def check_intraday_component(self, monitor_option):
        """
        Check and handle intraday component in monitor option.
        
        Args:
            monitor_option: Monitor option string
            
        Returns:
            str: Modified monitor option
        """
        last_component = monitor_option.split(":")[-1]
        if "i" not in last_component:
            possible_positions = monitor_option.split(":i")
            if len(possible_positions) > 1:
                last_component = f"i {possible_positions[1]}"
        
        if "i" in last_component:
            # Switch to intraday scan
            monitor_option = monitor_option.replace(last_component, "")
            self.args.intraday = last_component.replace("i", "").strip()
            self.config_manager.toggleConfig(candleDuration=self.args.intraday, clearCache=False)
        else:
            # Switch to daily scan
            self.args.intraday = None
            self.config_manager.toggleConfig(candleDuration='1d', clearCache=False)
        
        return monitor_option
    
    def update_config_durations(self):
        """Update configuration durations based on args options."""
        if self.args is None or self.args.options is None:
            return
        
        next_ones = self.args.options.split(">")
        if len(next_ones) > 1:
            monitor_option = next_ones[0]
            if len(monitor_option) == 0:
                return
            
            last_component = ":".join(monitor_option.split(":")[-2:])
            if "i" in last_component and "," not in last_component and " " in last_component:
                if "i" in last_component.split(":")[-2]:
                    last_component = last_component.split(":")[-2]
                else:
                    last_component = last_component.split(":")[-1]
                
                # Switch to intraday scan
                self.args.intraday = last_component.replace("i", "").strip()
                self.config_manager.toggleConfig(candleDuration=self.args.intraday, clearCache=False)
            else:
                # Switch to daily scan
                self.args.intraday = None
                self.config_manager.toggleConfig(candleDuration='1d', clearCache=False)
    
    def pipe_results(self, prev_output):
        """
        Pipe results from previous scan to next scan.
        
        Args:
            prev_output: Previous scan output dataframe
            
        Returns:
            bool: Whether to continue with piped scan
        """
        if self.args is None or self.args.options is None:
            return False
        
        has_found_stocks = False
        next_ones = self.args.options.split(">")
        
        if len(next_ones) > 1:
            monitor_option = next_ones[1]
            if len(monitor_option) == 0:
                return False
            
            last_component = ":".join(monitor_option.split(":")[-2:])
            if "i" in last_component and "," not in last_component and " " in last_component:
                if "i" in last_component.split(":")[-2]:
                    last_component = last_component.split(":")[-2]
                else:
                    last_component = last_component.split(":")[-1]
                
                # Switch to intraday scan
                monitor_option = monitor_option.replace(last_component, "")
                self.args.intraday = last_component.replace("i", "").strip()
                self.config_manager.toggleConfig(candleDuration=self.args.intraday, clearCache=False)
            else:
                # Switch to daily scan
                self.args.intraday = None
                self.config_manager.toggleConfig(candleDuration='1d', clearCache=False)
            
            if monitor_option.startswith("|"):
                monitor_option = monitor_option.replace("|", "")
                monitor_options = monitor_option.split(":")
                
                if monitor_options[0].upper() in ["X", "C"] and monitor_options[1] != "0":
                    monitor_options[1] = "0"
                    monitor_option = ":".join(monitor_options)
                
                if "B" in monitor_options[0].upper() and monitor_options[1] != "30":
                    monitor_option = ":".join(monitor_options).upper().replace(
                        f"{monitor_options[0].upper()}:{monitor_options[1]}",
                        f"{monitor_options[0].upper()}:30:{monitor_options[1]}"
                    )
                
                # Pipe output from previous run
                if prev_output is not None and not prev_output.empty:
                    try:
                        prev_output.set_index("Stock", inplace=True)
                    except Exception:
                        pass  # Index may already be set or column may not exist
                    
                    prev_output_results = prev_output[~prev_output.index.duplicated(keep='first')]
                    prev_output_results = prev_output_results.index
                    has_found_stocks = len(prev_output_results) > 0
                    prev_output_results = ",".join(prev_output_results)
                    monitor_option = monitor_option.replace(":D:", ":")
                    monitor_option = f"{monitor_option}:{prev_output_results}"
            
            self.args.options = monitor_option.replace("::", ":")
            self.args.options = self.args.options + ":D:>" + ":D:>".join(next_ones[2:])
            self.args.options = self.args.options.replace("::", ":")
            return True and has_found_stocks
        
        return False
    
    def update_config(self):
        """Update configuration based on args."""
        if self.args is None:
            return
        
        self.config_manager.getConfig(ConfigManager.parser)
        
        if self.args.intraday:
            self.config_manager.toggleConfig(candleDuration=self.args.intraday, clearCache=False)
            if (self.config_manager.candlePeriodFrequency not in ["d", "mo"] or 
                self.config_manager.candleDurationFrequency not in ["m"]):
                self.config_manager.period = "1d"
                self.config_manager.duration = self.args.intraday
                self.config_manager.setConfig(ConfigManager.parser, default=True, showFileCreatedText=False)
        elif (self.config_manager.candlePeriodFrequency not in ["y", "max", "mo"] or 
              self.config_manager.candleDurationFrequency not in ["d", "wk", "mo", "h"]):
            if self.args.answerdefault is not None or self.args.systemlaunched:
                self.config_manager.period = "1y"
                self.config_manager.duration = "1d"
                self.config_manager.setConfig(ConfigManager.parser, default=True, showFileCreatedText=False)


class IntradayAnalysisRunner:
    """Handles intraday analysis report generation."""
    
    def __init__(self, config_manager, args):
        """
        Initialize the intraday analysis runner.
        
        Args:
            config_manager: Configuration manager instance
            args: Parsed command line arguments
        """
        self.config_manager = config_manager
        self.args = args
    
    def generate_reports(self):
        """Generate intraday analysis reports."""
        from pkscreener.globals import (
            main, isInterrupted, closeWorkersAndExit, 
            resetUserMenuChoiceOptions, showBacktestResults
        )
        from pkscreener.classes.MenuOptions import (
            menus, PREDEFINED_SCAN_MENU_TEXTS, 
            PREDEFINED_PIPED_MENU_ANALYSIS_OPTIONS, PREDEFINED_SCAN_MENU_VALUES
        )
        import pandas as pd
        from pkscreener.classes import Utility
        
        # Save and set max display results
        max_display_results = self.config_manager.maxdisplayresults
        self.config_manager.maxdisplayresults = 2000
        self.config_manager.setConfig(ConfigManager.parser, default=True, showFileCreatedText=False)
        
        run_options = []
        other_menus = []
        
        if len(self.args.options.split(":")) >= 4:
            run_options = [self.args.options]
        else:
            run_options = PREDEFINED_PIPED_MENU_ANALYSIS_OPTIONS
            if len(other_menus) > 0:
                run_options.extend(other_menus)
        
        optional_final_outcome_df = pd.DataFrame()
        cli_runner = PKCliRunner(self.config_manager, self.args)
        
        # Delete existing data from previous run
        self.config_manager.deleteFileWithPattern(
            rootDir=Archiver.get_user_data_dir(), 
            pattern="stock_data_*.pkl"
        )
        
        analysis_index = 1
        for run_option in run_options:
            try:
                run_option_name = f"--systemlaunched -a y -e -o '{run_option.replace('C:','X:').replace('D:','')}'"
                index_num = PREDEFINED_SCAN_MENU_VALUES.index(run_option_name)
                run_option_name = f"{'  [+] P_1_'+str(index_num + 1) if '>|' in run_option else run_option}"
            except Exception as e:
                default_logger().debug(e, exc_info=True)
                run_option_name = f"  [+] {run_option.replace('D:','').replace(':D','').replace(':','_').replace('_D','').replace('C_','X_')}"
            
            self.args.progressstatus = f"{run_option_name} => Running Intraday Analysis: {analysis_index} of {len(run_options)}..."
            
            # Update analysis options
            analysis_options = run_option.split("|")
            analysis_options[-1] = analysis_options[-1].replace("X:", "C:")
            run_option = "|".join(analysis_options)
            self.args.options = run_option
            
            try:
                results, plain_results = main(userArgs=self.args, optionalFinalOutcome_df=optional_final_outcome_df)
                
                if self.args.pipedmenus is not None:
                    while self.args.pipedmenus is not None:
                        results, plain_results = main(userArgs=self.args)
                
                if isInterrupted():
                    closeWorkersAndExit()
                    return
                
                run_piped_scans = True
                while run_piped_scans:
                    run_piped_scans = cli_runner.pipe_results(plain_results)
                    if run_piped_scans:
                        self.args, _ = cli_runner.update_progress_status()
                        results, plain_results = main(
                            userArgs=self.args, 
                            optionalFinalOutcome_df=optional_final_outcome_df
                        )
                
                if (results is not None and 
                    len(results) >= len(optional_final_outcome_df) and 
                    not results.empty and 
                    len(results.columns) > 5):
                    import numpy as np
                    if "%Chng" in results.columns and "EoDDiff" in results.columns:
                        optional_final_outcome_df = results
                
                if (optional_final_outcome_df is not None and 
                    "EoDDiff" not in optional_final_outcome_df.columns):
                    # File corrupted, re-download
                    self.config_manager.deleteFileWithPattern(
                        rootDir=Archiver.get_user_data_dir(), 
                        pattern="*stock_data_*.pkl"
                    )
                    self.config_manager.deleteFileWithPattern(
                        rootDir=Archiver.get_user_data_dir(), 
                        pattern="*intraday_stock_data_*.pkl"
                    )
                
                if isInterrupted():
                    break
                    
            except KeyboardInterrupt:
                closeWorkersAndExit()
                return
            except Exception as e:
                OutputControls().printOutput(e)
                if self.args.log:
                    traceback.print_exc()
            
            resetUserMenuChoiceOptions()
            analysis_index += 1
        
        # Restore settings
        self.config_manager.maxdisplayresults = max_display_results
        self.config_manager.setConfig(ConfigManager.parser, default=True, showFileCreatedText=False)
        
        # Save and send final outcome
        self._save_send_final_outcome(optional_final_outcome_df)
    
    def _save_send_final_outcome(self, optional_final_outcome_df):
        """
        Save and send final outcome dataframe.
        
        Args:
            optional_final_outcome_df: Final outcome dataframe
        """
        import pandas as pd
        from pkscreener.classes import Utility
        from pkscreener.globals import sendQuickScanResult, showBacktestResults
        
        if optional_final_outcome_df is None or optional_final_outcome_df.empty:
            return
        
        final_df = None
        try:
            optional_final_outcome_df.drop('FairValue', axis=1, inplace=True, errors="ignore")
            df_grouped = optional_final_outcome_df.groupby("Stock")
            
            for stock, df_group in df_grouped:
                if stock == "BASKET":
                    cols = ["Pattern", "LTP", "LTP@Alert", "SqrOffLTP", "SqrOffDiff", "EoDDiff", "DayHigh", "DayHighDiff"]
                    if final_df is None:
                        final_df = df_group[cols]
                    else:
                        final_df = pd.concat([final_df, df_group[cols]], axis=0)
        except Exception as e:
            default_logger().debug(f"Error processing intraday analysis: {e}")
        
        if final_df is None or final_df.empty:
            return
        
        with pd.option_context('mode.chained_assignment', None):
            final_df = final_df[["Pattern", "LTP@Alert", "LTP", "EoDDiff", "DayHigh", "DayHighDiff"]]
            final_df.rename(
                columns={
                    "Pattern": "Scan Name",
                    "LTP@Alert": "Basket Value@Alert",
                    "LTP": "Basket Value@EOD",
                    "DayHigh": "Basket Value@DayHigh",
                },
                inplace=True,
            )
            final_df.dropna(inplace=True)
            final_df.dropna(how="all", axis=1, inplace=True)
        
        mark_down = colorText.miniTabulator().tabulate(
            final_df,
            headers="keys",
            tablefmt=colorText.No_Pad_GridFormat,
            showindex=False
        ).encode("utf-8").decode(Utility.STD_ENCODING)
        
        showBacktestResults(final_df, optionalName="Intraday_Backtest_Result_Summary", choices="Summary")
        OutputControls().printOutput(mark_down)
        
        from PKDevTools.classes.Environment import PKEnvironment
        channel_id, _, _, _ = PKEnvironment().secrets
        
        if channel_id is not None and len(str(channel_id)) > 0:
            sendQuickScanResult(
                menuChoiceHierarchy="IntradayAnalysis (If you would have bought at alert time and sold at end of day or day high)",
                user=int(f"-{channel_id}"),
                tabulated_results=mark_down,
                markdown_results=mark_down,
                caption="Intraday Analysis Summary - Morning alert vs Market Close",
                pngName=f"PKS_IA_{PKDateUtilities.currentDateTime().strftime('%Y-%m-%d_%H:%M:%S')}",
                pngExtension=".png",
                forceSend=True
            )


class CliConfigManager:
    """Manages CLI-specific configuration and initialization."""
    
    def __init__(self, config_manager, args):
        """
        Initialize CLI config manager.
        
        Args:
            config_manager: Configuration manager instance
            args: Parsed command line arguments
        """
        self.config_manager = config_manager
        self.args = args
    
    @staticmethod
    def remove_old_instances():
        """Remove old CLI instances."""
        import glob
        pattern = "pkscreenercli*"
        this_instance = sys.argv[0]
        
        for f in glob.glob(pattern, root_dir=os.getcwd(), recursive=True):
            file_to_delete = (f if (os.sep in f and f.startswith(this_instance[:10])) 
                            else os.path.join(os.getcwd(), f))
            if not file_to_delete.endswith(this_instance):
                try:
                    os.remove(file_to_delete)
                except OSError:
                    pass  # File may be in use or already deleted
    
    def validate_tos_acceptance(self):
        """
        Validate Terms of Service acceptance.
        
        Returns:
            bool: True if TOS accepted, False otherwise
        """
        user_acceptance = self.config_manager.tosAccepted
        
        if not self.config_manager.tosAccepted:
            if (self.args is not None and 
                self.args.answerdefault is not None and 
                str(self.args.answerdefault).lower() == "n"):
                OutputControls().printOutput(
                    f"{colorText.FAIL}You seem to have passed disagreement to the Disclaimer and Terms Of Service of PKScreener by passing in {colorText.END}"
                    f"{colorText.WARN}--answerdefault N or -a N{colorText.END}. Exiting now!"
                )
                sleep(5)
                return False
            
            all_args = self.args.__dict__
            disclaimer_link = '\x1b[97m\x1b]8;;https://pkjmesra.github.io/PKScreener/Disclaimer.txt\x1b\\https://pkjmesra.github.io/PKScreener/Disclaimer.txt\x1b]8;;\x1b\\\x1b[0m'
            tos_link = '\x1b[97m\x1b]8;;https://pkjmesra.github.io/PKScreener/tos.txt\x1b\\https://pkjmesra.github.io/PKScreener/tos.txt\x1b]8;;\x1b\\\x1b[0m'
            
            for arg_key in all_args.keys():
                arg = all_args[arg_key]
                if arg is not None and arg:
                    user_acceptance = True
                    OutputControls().printOutput(
                        f"{colorText.GREEN}By using this Software and passing a value for [{arg_key}={arg}], you agree to\n"
                        f"[+] having read through the Disclaimer{colorText.END} ({disclaimer_link})\n"
                        f"[+]{colorText.GREEN} and accept Terms Of Service {colorText.END}({tos_link}){colorText.GREEN} of PKScreener. {colorText.END}\n"
                        f"[+] {colorText.WARN}If that is not the case, you MUST immediately terminate PKScreener by pressing Ctrl+C now!{colorText.END}"
                    )
                    sleep(2)
                    break
        
        if (not user_acceptance and 
            ((self.args is not None and self.args.answerdefault is not None and str(self.args.answerdefault).lower() != "y") or 
             (self.args is not None and self.args.answerdefault is None))):
            disclaimer_link = '\x1b[97m\x1b]8;;https://pkjmesra.github.io/PKScreener/Disclaimer.txt\x1b\\https://pkjmesra.github.io/PKScreener/Disclaimer.txt\x1b]8;;\x1b\\\x1b[0m'
            tos_link = '\x1b[97m\x1b]8;;https://pkjmesra.github.io/PKScreener/tos.txt\x1b\\https://pkjmesra.github.io/PKScreener/tos.txt\x1b]8;;\x1b\\\x1b[0m'
            
            user_acceptance = OutputControls().takeUserInput(
                f"{colorText.WARN}By using this Software, you agree to\n"
                f"[+] having read through the Disclaimer {colorText.END}({disclaimer_link}){colorText.WARN}\n"
                f"[+] and accept Terms Of Service {colorText.END}({tos_link}){colorText.WARN} of PKScreener ? {colorText.END}"
                f"(Y/N){colorText.GREEN} [Default: {colorText.END}{colorText.FAIL}N{colorText.END}{colorText.GREEN}] :{colorText.END}",
                defaultInput="N",
                enableUserInput=True
            ) or "N"
            
            if str(user_acceptance).lower() != "y":
                OutputControls().printOutput(
                    f"\n{colorText.WARN}You seem to have\n"
                    f"    [+] passed disagreement to the Disclaimer and \n"
                    f"    [+] not accepted Terms Of Service of PKScreener.\n{colorText.END}"
                    f"{colorText.FAIL}[+] You MUST read and agree to the disclaimer and MUST accept the Terms of Service to use PKScreener.{colorText.END}\n\n"
                    f"{colorText.WARN}Exiting now!{colorText.END}"
                )
                sleep(5)
                return False
        
        return True






