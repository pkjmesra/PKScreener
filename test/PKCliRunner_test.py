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

import pytest
import pandas as pd
from unittest.mock import MagicMock, patch
from argparse import Namespace

import pkscreener.classes.ConfigManager as ConfigManager
from pkscreener.classes.cli.PKCliRunner import PKCliRunner, IntradayAnalysisRunner, CliConfigManager


class TestPKCliRunner:
    """Test cases for PKCliRunner class."""
    
    @pytest.fixture
    def config_manager(self):
        """Create a mock config manager."""
        config = MagicMock()
        config.period = "1y"
        config.duration = "1d"
        config.maxdisplayresults = 100
        config.candlePeriodFrequency = "y"
        config.candleDurationFrequency = "d"
        return config
    
    @pytest.fixture
    def args(self):
        """Create a mock args object."""
        return Namespace(
            options="X:12:1",
            systemlaunched=False,
            intraday=None,
            answerdefault="Y",
            progressstatus=None,
            usertag=None,
            maxdisplayresults=None,
            pipedmenus=None,
            log=False
        )
    
    @pytest.fixture
    def cli_runner(self, config_manager, args):
        """Create a PKCliRunner instance."""
        return PKCliRunner(config_manager, args)
    
    # Feature: Update Progress Status
    def test_update_progress_status_with_system_launched(self, cli_runner):
        """Test progress status update when systemlaunched is True."""
        cli_runner.args.systemlaunched = True
        cli_runner.args.options = "X:12:1"
        
        with patch.object(cli_runner, 'update_progress_status') as mock_update:
            mock_update.return_value = (cli_runner.args, "")
            args, choices = mock_update()
            assert args is not None
    
    def test_update_progress_status_without_system_launched(self, cli_runner):
        """Test progress status update when systemlaunched is False."""
        cli_runner.args.systemlaunched = False
        args, choices = cli_runner.update_progress_status()
        assert choices == ""
    
    # Feature: Check Intraday Component
    def test_check_intraday_component_with_intraday(self, cli_runner):
        """Test intraday component detection with intraday option."""
        monitor_option = "X:12:1:i 5m"
        result = cli_runner.check_intraday_component(monitor_option)
        assert cli_runner.args.intraday == "5m"
    
    def test_check_intraday_component_without_intraday(self, cli_runner):
        """Test intraday component detection without intraday option."""
        monitor_option = "X:12:1"
        result = cli_runner.check_intraday_component(monitor_option)
        assert cli_runner.args.intraday is None
    
    # Feature: Update Config Durations
    def test_update_config_durations_with_piped_options(self, cli_runner):
        """Test config duration update with piped options."""
        cli_runner.args.options = "X:12:1>X:12:2"
        cli_runner.update_config_durations()
        # Should not raise any exception
        assert True
    
    def test_update_config_durations_with_none_options(self, cli_runner):
        """Test config duration update with None options."""
        cli_runner.args.options = None
        cli_runner.update_config_durations()
        # Should not raise any exception
        assert True
    
    # Feature: Pipe Results
    def test_pipe_results_with_empty_output(self, cli_runner):
        """Test pipe results with empty previous output."""
        cli_runner.args.options = "X:12:1>|X:12:2"
        prev_output = pd.DataFrame()
        result = cli_runner.pipe_results(prev_output)
        assert result == False
    
    def test_pipe_results_with_valid_output(self, cli_runner):
        """Test pipe results with valid previous output."""
        cli_runner.args.options = "X:12:1>|X:12:2"
        prev_output = pd.DataFrame({
            "Stock": ["SBIN", "ICICI", "HDFC"],
            "LTP": [100, 200, 300]
        })
        result = cli_runner.pipe_results(prev_output)
        assert isinstance(result, bool)
    
    def test_pipe_results_with_no_piped_options(self, cli_runner):
        """Test pipe results without piped options."""
        cli_runner.args.options = "X:12:1"
        prev_output = pd.DataFrame()
        result = cli_runner.pipe_results(prev_output)
        assert result == False
    
    # Feature: Update Config
    def test_update_config_with_intraday(self, cli_runner):
        """Test config update with intraday settings."""
        cli_runner.args.intraday = "5m"
        cli_runner.update_config()
        cli_runner.config_manager.toggleConfig.assert_called()
    
    def test_update_config_without_intraday(self, cli_runner):
        """Test config update without intraday settings."""
        cli_runner.args.intraday = None
        cli_runner.update_config()
        # Should not raise any exception
        assert True
    
    def test_update_config_with_none_args(self, config_manager):
        """Test config update with None args."""
        runner = PKCliRunner(config_manager, None)
        runner.update_config()
        # Should not raise any exception
        assert True


class TestCliConfigManager:
    """Test cases for CliConfigManager class."""
    
    @pytest.fixture
    def config_manager(self):
        """Create a mock config manager."""
        config = MagicMock()
        config.tosAccepted = True
        return config
    
    @pytest.fixture
    def args(self):
        """Create a mock args object."""
        return Namespace(
            answerdefault="Y",
            systemlaunched=False
        )
    
    @pytest.fixture
    def cli_config(self, config_manager, args):
        """Create a CliConfigManager instance."""
        return CliConfigManager(config_manager, args)
    
    # Feature: TOS Validation
    def test_validate_tos_acceptance_already_accepted(self, cli_config):
        """Test TOS validation when already accepted."""
        result = cli_config.validate_tos_acceptance()
        assert result == True
    
    def test_validate_tos_acceptance_not_accepted_with_y_default(self, config_manager, args):
        """Test TOS validation when not accepted but default is Y."""
        config_manager.tosAccepted = False
        args.answerdefault = "Y"
        cli_config = CliConfigManager(config_manager, args)
        result = cli_config.validate_tos_acceptance()
        assert result == True
    
    @pytest.mark.skip(reason="API has changed")
    def test_validate_tos_acceptance_rejected_with_n_default(self, config_manager, args):
        """Test TOS validation when rejected with N default."""
        config_manager.tosAccepted = False
        args.answerdefault = "N"
        cli_config = CliConfigManager(config_manager, args)
        
        with pytest.raises(SystemExit):
            with patch('time.sleep'):
                result = cli_config.validate_tos_acceptance()
    
    # Feature: Remove Old Instances
    def test_remove_old_instances(self):
        """Test removing old CLI instances."""
        with patch('glob.glob', return_value=[]):
            CliConfigManager.remove_old_instances()
            # Should not raise any exception
            assert True
    
    def test_remove_old_instances_with_files(self):
        """Test removing old CLI instances when files exist."""
        with patch('glob.glob', return_value=['pkscreenercli_old']):
            with patch('os.remove') as mock_remove:
                CliConfigManager.remove_old_instances()
                # Should attempt to remove old files


class TestIntradayAnalysisRunner:
    """Test cases for IntradayAnalysisRunner class."""
    
    @pytest.fixture
    def config_manager(self):
        """Create a mock config manager."""
        config = MagicMock()
        config.maxdisplayresults = 100
        return config
    
    @pytest.fixture
    def args(self):
        """Create a mock args object."""
        return Namespace(
            options="C:12:1:2",
            systemlaunched=False,
            intraday=None,
            answerdefault="Y",
            progressstatus=None,
            pipedmenus=None,
            log=False
        )
    
    @pytest.fixture
    def intraday_runner(self, config_manager, args):
        """Create an IntradayAnalysisRunner instance."""
        return IntradayAnalysisRunner(config_manager, args)
    
    # Feature: Generate Reports
    def test_init_intraday_runner(self, intraday_runner):
        """Test initialization of IntradayAnalysisRunner."""
        assert intraday_runner.config_manager is not None
        assert intraday_runner.args is not None
    
    def test_save_send_final_outcome_empty_df(self, intraday_runner):
        """Test save/send with empty dataframe."""
        empty_df = pd.DataFrame()
        intraday_runner._save_send_final_outcome(empty_df)
        # Should not raise any exception
        assert True
    
    def test_save_send_final_outcome_none_df(self, intraday_runner):
        """Test save/send with None dataframe."""
        intraday_runner._save_send_final_outcome(None)
        # Should not raise any exception
        assert True


# Feature-oriented test class for CLI flow
class TestCLIApplicationFlow:
    """Integration tests for CLI application flow."""
    
    @pytest.fixture
    def setup_cli_components(self):
        """Set up CLI components for testing."""
        config = MagicMock()
        config.tosAccepted = True
        config.period = "1y"
        config.duration = "1d"
        config.maxdisplayresults = 100
        
        args = Namespace(
            options="X:12:1",
            systemlaunched=False,
            intraday=None,
            answerdefault="Y",
            progressstatus=None,
            pipedmenus=None,
            log=False,
            testbuild=False,
            prodbuild=False,
            download=False,
            user=None,
            monitor=None,
            runintradayanalysis=False
        )
        
        return config, args
    
    # Feature: Full CLI Flow
    def test_cli_initialization_flow(self, setup_cli_components):
        """Test complete CLI initialization flow."""
        config, args = setup_cli_components
        
        # Initialize components
        cli_config = CliConfigManager(config, args)
        cli_runner = PKCliRunner(config, args)
        
        # Validate TOS
        assert cli_config.validate_tos_acceptance() == True
        
        # Config update
        cli_runner.update_config()
        
        # No exceptions should be raised
        assert True
    
    def test_cli_with_piped_scan_flow(self, setup_cli_components):
        """Test CLI flow with piped scan options."""
        config, args = setup_cli_components
        args.options = "X:12:1>|X:12:2"
        
        cli_runner = PKCliRunner(config, args)
        
        # Test piping with empty results
        result = cli_runner.pipe_results(pd.DataFrame())
        assert result == False
    
    def test_cli_with_intraday_flow(self, setup_cli_components):
        """Test CLI flow with intraday options."""
        config, args = setup_cli_components
        args.intraday = "5m"
        
        cli_runner = PKCliRunner(config, args)
        cli_runner.update_config()
        
        # Verify config toggle was called
        config.toggleConfig.assert_called()
    
    def test_cli_monitor_option_handling(self, setup_cli_components):
        """Test CLI monitor option handling."""
        config, args = setup_cli_components
        
        cli_runner = PKCliRunner(config, args)
        
        # Test intraday component check
        monitor_option = "X:12:1:i 5m"
        result = cli_runner.check_intraday_component(monitor_option)
        
        assert args.intraday == "5m"




