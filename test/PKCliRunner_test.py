"""
    The MIT License (MIT)

    Copyright (c) 2023 pkjmesra

Comprehensive unit tests for PKCliRunner module targeting high coverage.
"""

import os
import sys
import pytest
import pandas as pd
from unittest.mock import MagicMock, patch, PropertyMock
from argparse import Namespace

import pkscreener.classes.ConfigManager as ConfigManager
from pkscreener.classes.cli.PKCliRunner import PKCliRunner, IntradayAnalysisRunner, CliConfigManager


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def real_config():
    """Get real config manager."""
    return ConfigManager.tools()


@pytest.fixture
def mock_args():
    """Create a mock args object with all required attributes."""
    return Namespace(
        options="X:12:1",
        systemlaunched=False,
        intraday=None,
        answerdefault="Y",
        progressstatus=None,
        usertag=None,
        maxdisplayresults=None,
        pipedmenus=None,
        log=False,
        testbuild=False,
        prodbuild=False,
        download=False,
        user=None,
        monitor=None,
        runintradayanalysis=False
    )


# =============================================================================
# PKCliRunner Tests - Real Execution
# =============================================================================

class TestPKCliRunnerRealExecution:
    """Test PKCliRunner with real code execution."""
    
    def test_init_with_real_config(self, real_config, mock_args):
        """Test initialization with real config."""
        runner = PKCliRunner(real_config, mock_args)
        
        assert runner.config_manager == real_config
        assert runner.args == mock_args
        assert runner.results is None
        assert runner.elapsed_time == 0
    
    def test_init_with_none_args(self, real_config):
        """Test with None args."""
        runner = PKCliRunner(real_config, None)
        assert runner.args is None
    
    def test_update_progress_status_not_systemlaunched(self, real_config, mock_args):
        """Test update_progress_status when not system launched."""
        runner = PKCliRunner(real_config, mock_args)
        mock_args.systemlaunched = False
        
        args, choices = runner.update_progress_status()
        
        assert choices == ""
        assert args == mock_args
    
    def test_update_progress_status_systemlaunched(self, real_config, mock_args):
        """Test update_progress_status when system launched."""
        runner = PKCliRunner(real_config, mock_args)
        mock_args.systemlaunched = True
        mock_args.options = "X:12:1"
        
        args, choices = runner.update_progress_status()
        # Exception is caught - returns empty choices
        assert args is not None
    
    def test_update_progress_status_with_monitor_options(self, real_config, mock_args):
        """Test update_progress_status with monitor_options."""
        runner = PKCliRunner(real_config, mock_args)
        mock_args.systemlaunched = False
        
        args, choices = runner.update_progress_status(monitor_options="C:12:1")
        assert args is not None
    
    def test_update_progress_status_with_valid_predefined(self, real_config, mock_args):
        """Test update_progress_status with valid predefined option."""
        runner = PKCliRunner(real_config, mock_args)
        mock_args.systemlaunched = True
        mock_args.options = "C:12:1>|X:12:2"  # Option with pipe
        
        # Patch at the module level where it's imported
        with patch('pkscreener.classes.MenuOptions.PREDEFINED_SCAN_MENU_VALUES', 
                   ["--systemlaunched -a y -e -o 'X:12:1>|X:12:2'"]):
            with patch('pkscreener.classes.MenuOptions.PREDEFINED_SCAN_MENU_TEXTS', 
                       ['Test Scan']):
                args, choices = runner.update_progress_status()
                assert args is not None
    
    def test_check_intraday_component_with_intraday(self, real_config, mock_args):
        """Test check_intraday_component with intraday option."""
        runner = PKCliRunner(real_config, mock_args)
        
        result = runner.check_intraday_component("X:12:1:i 5m")
        
        assert mock_args.intraday == "5m"
    
    def test_check_intraday_component_without_intraday(self, real_config, mock_args):
        """Test check_intraday_component without intraday."""
        runner = PKCliRunner(real_config, mock_args)
        
        result = runner.check_intraday_component("X:12:1:2")
        
        assert mock_args.intraday is None
    
    def test_check_intraday_colon_i_format(self, real_config, mock_args):
        """Test check_intraday_component with :i format."""
        runner = PKCliRunner(real_config, mock_args)
        
        result = runner.check_intraday_component("X:12:i 15m")
        
        assert mock_args.intraday is not None
    
    def test_update_config_durations_none_args(self, real_config):
        """Test update_config_durations with None args."""
        runner = PKCliRunner(real_config, None)
        runner.update_config_durations()
        # Should not crash
    
    def test_update_config_durations_none_options(self, real_config, mock_args):
        """Test update_config_durations with None options."""
        runner = PKCliRunner(real_config, mock_args)
        mock_args.options = None
        runner.update_config_durations()
        # Should not crash
    
    def test_update_config_durations_no_pipe(self, real_config, mock_args):
        """Test update_config_durations without pipe."""
        runner = PKCliRunner(real_config, mock_args)
        mock_args.options = "X:12:1"
        runner.update_config_durations()
        # Should not crash
    
    def test_update_config_durations_with_pipe(self, real_config, mock_args):
        """Test update_config_durations with pipe."""
        runner = PKCliRunner(real_config, mock_args)
        mock_args.options = "X:12:1>X:12:2"
        runner.update_config_durations()
        # Should not crash
    
    def test_update_config_durations_with_intraday(self, real_config, mock_args):
        """Test update_config_durations with intraday."""
        runner = PKCliRunner(real_config, mock_args)
        mock_args.options = "X:12:1:i 5m>X:12:2"
        runner.update_config_durations()
        
        assert mock_args.intraday == "5m"
    
    def test_update_config_durations_empty_first(self, real_config, mock_args):
        """Test update_config_durations with empty first option."""
        runner = PKCliRunner(real_config, mock_args)
        mock_args.options = ">X:12:2"
        runner.update_config_durations()
        # Should return early
    
    def test_pipe_results_none_args(self, real_config):
        """Test pipe_results with None args."""
        runner = PKCliRunner(real_config, None)
        result = runner.pipe_results(pd.DataFrame())
        assert result == False
    
    def test_pipe_results_none_options(self, real_config, mock_args):
        """Test pipe_results with None options."""
        runner = PKCliRunner(real_config, mock_args)
        mock_args.options = None
        result = runner.pipe_results(pd.DataFrame())
        assert result == False
    
    def test_pipe_results_no_pipe(self, real_config, mock_args):
        """Test pipe_results without pipe."""
        runner = PKCliRunner(real_config, mock_args)
        mock_args.options = "X:12:1"
        result = runner.pipe_results(pd.DataFrame())
        assert result == False
    
    def test_pipe_results_empty_piped(self, real_config, mock_args):
        """Test pipe_results with empty piped option."""
        runner = PKCliRunner(real_config, mock_args)
        mock_args.options = "X:12:1>"
        result = runner.pipe_results(pd.DataFrame())
        assert result == False
    
    def test_pipe_results_empty_df(self, real_config, mock_args):
        """Test pipe_results with empty dataframe."""
        runner = PKCliRunner(real_config, mock_args)
        mock_args.options = "X:12:1>|X:12:2"
        result = runner.pipe_results(pd.DataFrame())
        assert result == False
    
    def test_pipe_results_valid_df(self, real_config, mock_args):
        """Test pipe_results with valid dataframe."""
        runner = PKCliRunner(real_config, mock_args)
        mock_args.options = "X:12:1>|X:12:2"
        
        # Stock column with string values
        df = pd.DataFrame({
            "Stock": ["SBIN", "ICICI"],
            "LTP": [100, 200]
        })
        
        result = runner.pipe_results(df)
        assert result == True
        assert "SBIN" in mock_args.options
    
    def test_pipe_results_x_option_to_0(self, real_config, mock_args):
        """Test pipe_results changes X option to 0."""
        runner = PKCliRunner(real_config, mock_args)
        mock_args.options = "X:12:1>|X:15:2"
        
        df = pd.DataFrame({"Stock": ["SBIN"], "LTP": [100]})
        runner.pipe_results(df)
        
        assert "X:0:" in mock_args.options
    
    def test_pipe_results_c_option_to_0(self, real_config, mock_args):
        """Test pipe_results changes C option to 0."""
        runner = PKCliRunner(real_config, mock_args)
        mock_args.options = "X:12:1>|C:15:2"
        
        df = pd.DataFrame({"Stock": ["SBIN"], "LTP": [100]})
        runner.pipe_results(df)
        
        assert "C:0:" in mock_args.options
    
    def test_pipe_results_b_option_adds_30(self, real_config, mock_args):
        """Test pipe_results adds 30 to B option."""
        runner = PKCliRunner(real_config, mock_args)
        mock_args.options = "X:12:1>|B:15:2"
        
        df = pd.DataFrame({"Stock": ["SBIN"], "LTP": [100]})
        runner.pipe_results(df)
        
        assert "B:30:" in mock_args.options
    
    def test_pipe_results_with_intraday(self, real_config, mock_args):
        """Test pipe_results with intraday in piped option."""
        runner = PKCliRunner(real_config, mock_args)
        mock_args.options = "X:12:1>|X:12:i 5m:2"
        
        df = pd.DataFrame({"Stock": ["SBIN"], "LTP": [100]})
        runner.pipe_results(df)
        
        assert mock_args.intraday == "5m"
    
    def test_pipe_results_duplicates_removed(self, real_config, mock_args):
        """Test pipe_results removes duplicates."""
        runner = PKCliRunner(real_config, mock_args)
        mock_args.options = "X:12:1>|X:12:2"
        
        df = pd.DataFrame({
            "Stock": ["SBIN", "SBIN", "ICICI"],
            "LTP": [100, 110, 200]
        })
        
        result = runner.pipe_results(df)
        assert result == True
    
    def test_pipe_results_multiple_pipes(self, real_config, mock_args):
        """Test pipe_results with multiple pipes."""
        runner = PKCliRunner(real_config, mock_args)
        mock_args.options = "X:12:1>|X:12:2>|X:12:3"
        
        df = pd.DataFrame({"Stock": ["SBIN"], "LTP": [100]})
        runner.pipe_results(df)
        
        assert ":D:>" in mock_args.options
    
    def test_update_config_none_args(self, real_config):
        """Test update_config with None args."""
        runner = PKCliRunner(real_config, None)
        runner.update_config()
        # Should not crash
    
    def test_update_config_with_intraday(self, real_config, mock_args):
        """Test update_config with intraday."""
        runner = PKCliRunner(real_config, mock_args)
        mock_args.intraday = "5m"
        
        runner.update_config()
        # Should not crash
    
    def test_update_config_without_intraday(self, real_config, mock_args):
        """Test update_config without intraday."""
        runner = PKCliRunner(real_config, mock_args)
        mock_args.intraday = None
        
        runner.update_config()
        # Should not crash


# =============================================================================
# IntradayAnalysisRunner Tests
# =============================================================================

class TestIntradayAnalysisRunnerRealExecution:
    """Test IntradayAnalysisRunner."""
    
    def test_init(self, real_config, mock_args):
        """Test initialization."""
        runner = IntradayAnalysisRunner(real_config, mock_args)
        
        assert runner.config_manager == real_config
        assert runner.args == mock_args
    
    def test_save_send_final_outcome_none(self, real_config, mock_args):
        """Test _save_send_final_outcome with None."""
        runner = IntradayAnalysisRunner(real_config, mock_args)
        runner._save_send_final_outcome(None)
    
    def test_save_send_final_outcome_empty(self, real_config, mock_args):
        """Test _save_send_final_outcome with empty df."""
        runner = IntradayAnalysisRunner(real_config, mock_args)
        runner._save_send_final_outcome(pd.DataFrame())
    
    def test_save_send_final_outcome_no_basket(self, real_config, mock_args):
        """Test _save_send_final_outcome without BASKET."""
        runner = IntradayAnalysisRunner(real_config, mock_args)
        df = pd.DataFrame({
            "Stock": ["SBIN"],
            "Pattern": ["Test"],
            "LTP": [100],
            "LTP@Alert": [95],
            "SqrOffLTP": [102],
            "SqrOffDiff": [2],
            "EoDDiff": [5],
            "DayHigh": [105],
            "DayHighDiff": [5]
        })
        runner._save_send_final_outcome(df)
    
    def test_save_send_final_outcome_with_basket(self, real_config, mock_args):
        """Test _save_send_final_outcome with BASKET."""
        runner = IntradayAnalysisRunner(real_config, mock_args)
        df = pd.DataFrame({
            "Stock": ["BASKET"],
            "Pattern": ["Scan1"],
            "LTP": [1000],
            "LTP@Alert": [950],
            "SqrOffLTP": [1010],
            "SqrOffDiff": [10],
            "EoDDiff": [50],
            "DayHigh": [1020],
            "DayHighDiff": [20]
        })
        
        with patch('pkscreener.globals.showBacktestResults'):
            with patch('pkscreener.globals.sendQuickScanResult'):
                with patch('PKDevTools.classes.Environment.PKEnvironment') as mock_env:
                    mock_env.return_value.secrets = (None, None, None, None)
                    runner._save_send_final_outcome(df)
    
    def test_save_send_final_outcome_with_channel(self, real_config, mock_args):
        """Test _save_send_final_outcome with channel."""
        runner = IntradayAnalysisRunner(real_config, mock_args)
        df = pd.DataFrame({
            "Stock": ["BASKET"],
            "Pattern": ["Scan1"],
            "LTP": [1000],
            "LTP@Alert": [950],
            "SqrOffLTP": [1010],
            "SqrOffDiff": [10],
            "EoDDiff": [50],
            "DayHigh": [1020],
            "DayHighDiff": [20]
        })
        
        with patch('pkscreener.globals.showBacktestResults'):
            with patch('pkscreener.globals.sendQuickScanResult') as mock_send:
                with patch('PKDevTools.classes.Environment.PKEnvironment') as mock_env:
                    mock_env.return_value.secrets = ("123456", None, None, None)
                    runner._save_send_final_outcome(df)
                    # sendQuickScanResult may or may not be called depending on code path
                    # Just verify no exception was raised
    
    def test_generate_reports_with_specific_options(self, real_config, mock_args):
        """Test generate_reports with specific options."""
        mock_args.options = "X:12:1:2"
        runner = IntradayAnalysisRunner(real_config, mock_args)
        
        with patch('pkscreener.globals.main', return_value=(pd.DataFrame(), pd.DataFrame())):
            with patch('pkscreener.globals.isInterrupted', return_value=False):
                with patch('pkscreener.globals.resetUserMenuChoiceOptions'):
                    with patch.object(runner, '_save_send_final_outcome'):
                        runner.generate_reports()
    
    def test_generate_reports_interrupted(self, real_config, mock_args):
        """Test generate_reports when interrupted."""
        mock_args.options = "X:12:1:2"
        runner = IntradayAnalysisRunner(real_config, mock_args)
        
        with patch('pkscreener.globals.main', return_value=(pd.DataFrame(), pd.DataFrame())):
            with patch('pkscreener.globals.isInterrupted', return_value=True):
                with patch('pkscreener.globals.closeWorkersAndExit'):
                    with patch('pkscreener.globals.resetUserMenuChoiceOptions'):
                        runner.generate_reports()
    
    def test_generate_reports_keyboard_interrupt(self, real_config, mock_args):
        """Test generate_reports with KeyboardInterrupt."""
        mock_args.options = "X:12:1:2"
        runner = IntradayAnalysisRunner(real_config, mock_args)
        
        with patch('pkscreener.globals.main', side_effect=KeyboardInterrupt()):
            with patch('pkscreener.globals.closeWorkersAndExit'):
                runner.generate_reports()
    
    def test_generate_reports_exception(self, real_config, mock_args):
        """Test generate_reports with exception."""
        mock_args.options = "X:12:1:2"
        mock_args.log = True
        runner = IntradayAnalysisRunner(real_config, mock_args)
        
        with patch('pkscreener.globals.main', side_effect=Exception("Test")):
            with patch('pkscreener.globals.isInterrupted', return_value=False):
                with patch('pkscreener.globals.resetUserMenuChoiceOptions'):
                    with patch.object(runner, '_save_send_final_outcome'):
                        runner.generate_reports()


# =============================================================================
# CliConfigManager Tests
# =============================================================================

class TestCliConfigManagerRealExecution:
    """Test CliConfigManager."""
    
    def test_init(self, real_config, mock_args):
        """Test initialization."""
        cli_config = CliConfigManager(real_config, mock_args)
        
        assert cli_config.config_manager == real_config
        assert cli_config.args == mock_args
    
    def test_remove_old_instances_no_files(self):
        """Test remove_old_instances with no files."""
        with patch('glob.glob', return_value=[]):
            CliConfigManager.remove_old_instances()
    
    def test_remove_old_instances_with_files(self):
        """Test remove_old_instances with files."""
        with patch('glob.glob', return_value=['pkscreenercli_old']):
            with patch('os.remove') as mock_remove:
                with patch('os.getcwd', return_value='/test'):
                    with patch.object(sys, 'argv', ['pkscreenercli_new']):
                        CliConfigManager.remove_old_instances()
                        mock_remove.assert_called()
    
    def test_remove_old_instances_handles_error(self):
        """Test remove_old_instances handles OSError."""
        with patch('glob.glob', return_value=['pkscreenercli_old']):
            with patch('os.remove', side_effect=OSError()):
                with patch('os.getcwd', return_value='/test'):
                    with patch.object(sys, 'argv', ['pkscreenercli_new']):
                        CliConfigManager.remove_old_instances()
    
    def test_validate_tos_already_accepted(self, real_config, mock_args):
        """Test validate_tos when already accepted."""
        real_config.tosAccepted = True
        cli_config = CliConfigManager(real_config, mock_args)
        
        result = cli_config.validate_tos_acceptance()
        assert result == True
    
    def test_validate_tos_rejected_with_n(self, real_config, mock_args):
        """Test validate_tos rejected with -a N."""
        real_config.tosAccepted = False
        mock_args.answerdefault = "N"
        cli_config = CliConfigManager(real_config, mock_args)
        
        with patch('pkscreener.classes.cli.PKCliRunner.sleep'):
            result = cli_config.validate_tos_acceptance()
        
        assert result == False
    
    def test_validate_tos_accepted_via_truthy_arg(self, real_config, mock_args):
        """Test validate_tos accepted via truthy arg."""
        real_config.tosAccepted = False
        mock_args.answerdefault = None
        mock_args.testbuild = True
        cli_config = CliConfigManager(real_config, mock_args)
        
        with patch('pkscreener.classes.cli.PKCliRunner.sleep'):
            result = cli_config.validate_tos_acceptance()
        
        assert result == True
    
    def test_validate_tos_user_accepts(self, real_config, mock_args):
        """Test validate_tos user accepts."""
        real_config.tosAccepted = False
        for attr in vars(mock_args):
            setattr(mock_args, attr, None if not isinstance(getattr(mock_args, attr), bool) else False)
        mock_args.answerdefault = None
        cli_config = CliConfigManager(real_config, mock_args)
        
        with patch('pkscreener.classes.cli.PKCliRunner.OutputControls') as mock_output:
            mock_output.return_value.takeUserInput.return_value = "Y"
            result = cli_config.validate_tos_acceptance()
        
        assert result == True
    
    def test_validate_tos_user_rejects(self, real_config, mock_args):
        """Test validate_tos user rejects."""
        real_config.tosAccepted = False
        for attr in vars(mock_args):
            setattr(mock_args, attr, None if not isinstance(getattr(mock_args, attr), bool) else False)
        mock_args.answerdefault = None
        cli_config = CliConfigManager(real_config, mock_args)
        
        with patch('pkscreener.classes.cli.PKCliRunner.OutputControls') as mock_output:
            mock_output.return_value.takeUserInput.return_value = "N"
            with patch('pkscreener.classes.cli.PKCliRunner.sleep'):
                result = cli_config.validate_tos_acceptance()
        
        assert result == False


# =============================================================================
# Module Tests
# =============================================================================

class TestModuleImports:
    """Test module imports."""
    
    def test_all_classes_exported(self):
        """Test that all classes are exported."""
        from pkscreener.classes.cli import PKCliRunner, IntradayAnalysisRunner, CliConfigManager
        
        assert PKCliRunner is not None
        assert IntradayAnalysisRunner is not None
        assert CliConfigManager is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
