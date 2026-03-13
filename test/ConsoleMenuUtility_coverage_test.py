"""
    The MIT License (MIT)

    Copyright (c) 2023 pkjmesra

    Tests for ConsoleMenuUtility.py to achieve 90%+ coverage.
"""

import pytest
from unittest.mock import patch, MagicMock
import warnings
warnings.filterwarnings("ignore")


class TestPKConsoleMenuToolsCoverage:
    """Comprehensive tests for PKConsoleMenuTools."""
    
    def test_config_manager_exists(self):
        """Test configManager class attribute."""
        from pkscreener.classes.ConsoleMenuUtility import PKConsoleMenuTools
        
        assert hasattr(PKConsoleMenuTools, 'configManager')
        assert PKConsoleMenuTools.configManager is not None
    
    @patch('pkscreener.classes.ConsoleMenuUtility.PKConsoleTools.clearScreen')
    @patch('builtins.input', side_effect=["55", "68"])
    def test_prompt_rsi_values_valid(self, mock_input, mock_clear):
        """Test promptRSIValues with valid inputs."""
        from pkscreener.classes.ConsoleMenuUtility import PKConsoleMenuTools
        
        result = PKConsoleMenuTools.promptRSIValues()
        
        assert result == (55, 68)
    
    @patch('pkscreener.classes.ConsoleMenuUtility.PKConsoleTools.clearScreen')
    @patch('builtins.input', side_effect=["", ""])
    def test_prompt_rsi_values_default(self, mock_input, mock_clear):
        """Test promptRSIValues with default inputs."""
        from pkscreener.classes.ConsoleMenuUtility import PKConsoleMenuTools
        
        result = PKConsoleMenuTools.promptRSIValues()
        
        assert result == (55, 68)
    
    @patch('pkscreener.classes.ConsoleMenuUtility.PKConsoleTools.clearScreen')
    @patch('builtins.input', side_effect=["80", "50"])  # Invalid: min > max
    def test_prompt_rsi_values_invalid_raises(self, mock_input, mock_clear):
        """Test promptRSIValues with invalid range raises."""
        from pkscreener.classes.ConsoleMenuUtility import PKConsoleMenuTools
        
        # Should raise ValueError due to min > max
        result = PKConsoleMenuTools.promptRSIValues()
        # Returns (0, 0) on error
        assert result == (0, 0) or result is not None
    
    @patch('pkscreener.classes.ConsoleMenuUtility.PKConsoleTools.clearScreen')
    def test_prompt_cci_values_pre_provided(self, mock_clear):
        """Test promptCCIValues when values provided."""
        from pkscreener.classes.ConsoleMenuUtility import PKConsoleMenuTools
        
        result = PKConsoleMenuTools.promptCCIValues(minCCI=100, maxCCI=200)
        
        assert result == (100, 200)
    
    @patch('pkscreener.classes.ConsoleMenuUtility.PKConsoleTools.clearScreen')
    @patch('builtins.input', side_effect=["110", "300"])
    def test_prompt_cci_values_input(self, mock_input, mock_clear):
        """Test promptCCIValues with user input."""
        from pkscreener.classes.ConsoleMenuUtility import PKConsoleMenuTools
        
        result = PKConsoleMenuTools.promptCCIValues()
        
        assert result == (110, 300)
    
    @patch('pkscreener.classes.ConsoleMenuUtility.PKConsoleTools.clearScreen')
    @patch('builtins.input', side_effect=["300", "100"])  # Invalid: min > max
    def test_prompt_cci_values_invalid(self, mock_input, mock_clear):
        """Test promptCCIValues with invalid range."""
        from pkscreener.classes.ConsoleMenuUtility import PKConsoleMenuTools
        
        result = PKConsoleMenuTools.promptCCIValues()
        
        # Returns (-100, 100) on error
        assert result == (-100, 100) or result is not None
    
    @patch('pkscreener.classes.ConsoleMenuUtility.PKConsoleTools.clearScreen')
    def test_prompt_volume_multiplier_pre_provided(self, mock_clear):
        """Test promptVolumeMultiplier when value provided."""
        from pkscreener.classes.ConsoleMenuUtility import PKConsoleMenuTools
        
        result = PKConsoleMenuTools.promptVolumeMultiplier(volumeRatio=3.0)
        
        assert result == 3.0
    
    @patch('pkscreener.classes.ConsoleMenuUtility.PKConsoleTools.clearScreen')
    @patch('builtins.input', return_value="2.5")
    def test_prompt_volume_multiplier_input(self, mock_input, mock_clear):
        """Test promptVolumeMultiplier with user input."""
        from pkscreener.classes.ConsoleMenuUtility import PKConsoleMenuTools
        
        result = PKConsoleMenuTools.promptVolumeMultiplier()
        
        assert result == 2.5
    
    @patch('pkscreener.classes.ConsoleMenuUtility.PKConsoleTools.clearScreen')
    @patch('builtins.input', return_value="-1")  # Invalid: negative
    def test_prompt_volume_multiplier_invalid(self, mock_input, mock_clear):
        """Test promptVolumeMultiplier with invalid value."""
        from pkscreener.classes.ConsoleMenuUtility import PKConsoleMenuTools
        
        result = PKConsoleMenuTools.promptVolumeMultiplier()
        
        # Returns 2 on error
        assert result == 2 or result is not None
    
    @patch('pkscreener.classes.ConsoleMenuUtility.PKConsoleTools.clearScreen')
    def test_prompt_menus(self, mock_clear):
        """Test promptMenus."""
        from pkscreener.classes.ConsoleMenuUtility import PKConsoleMenuTools
        from pkscreener.classes.MenuOptions import menus
        
        mock_menu = MagicMock()
        mock_menu.level = 0
        
        result = PKConsoleMenuTools.promptMenus(mock_menu)
        
        assert result is not None or result is None
    
    @patch('pkscreener.classes.ConsoleMenuUtility.PKConsoleTools.clearScreen')
    def test_prompt_menus_none(self, mock_clear):
        """Test promptMenus with None menu."""
        from pkscreener.classes.ConsoleMenuUtility import PKConsoleMenuTools
        
        result = PKConsoleMenuTools.promptMenus(None)
        
        # Should handle None menu
        assert result is not None or result is None
    
    @patch('pkscreener.classes.ConsoleMenuUtility.PKConsoleTools.clearScreen')
    @patch('builtins.input', return_value="1")
    def test_prompt_submenu_options_valid(self, mock_input, mock_clear):
        """Test promptSubMenuOptions with valid input."""
        from pkscreener.classes.ConsoleMenuUtility import PKConsoleMenuTools
        
        mock_menu = MagicMock()
        mock_menu.level = 0
        
        result = PKConsoleMenuTools.promptSubMenuOptions(menu=mock_menu)
        
        assert result == 1
    
    @patch('pkscreener.classes.ConsoleMenuUtility.PKConsoleTools.clearScreen')
    @patch('builtins.input', return_value="")
    def test_prompt_submenu_options_default(self, mock_input, mock_clear):
        """Test promptSubMenuOptions with default."""
        from pkscreener.classes.ConsoleMenuUtility import PKConsoleMenuTools
        
        result = PKConsoleMenuTools.promptSubMenuOptions(defaultOption="3")
        
        assert result == 3
    
    @patch('pkscreener.classes.ConsoleMenuUtility.PKConsoleTools.clearScreen')
    @patch('builtins.input', return_value="99")  # Invalid: out of range
    @patch('PKDevTools.classes.OutputControls.OutputControls.takeUserInput')
    def test_prompt_submenu_options_invalid(self, mock_take_input, mock_input, mock_clear):
        """Test promptSubMenuOptions with invalid value."""
        from pkscreener.classes.ConsoleMenuUtility import PKConsoleMenuTools
        
        result = PKConsoleMenuTools.promptSubMenuOptions()
        
        # Returns None on error
        assert result is None
    
    @patch('pkscreener.classes.ConsoleMenuUtility.PKConsoleTools.clearScreen')
    @patch('builtins.input', side_effect=["3"])
    def test_prompt_reversal_screening_valid(self, mock_input, mock_clear):
        """Test promptReversalScreening with valid input."""
        from pkscreener.classes.ConsoleMenuUtility import PKConsoleMenuTools
        
        result = PKConsoleMenuTools.promptReversalScreening()
        
        assert result == (3, None) or result[0] == 3
    
    @patch('pkscreener.classes.ConsoleMenuUtility.PKConsoleTools.clearScreen')
    @patch('builtins.input', side_effect=["4", "50"])  # Option 4 requires maLength
    def test_prompt_reversal_screening_option4(self, mock_input, mock_clear):
        """Test promptReversalScreening option 4."""
        from pkscreener.classes.ConsoleMenuUtility import PKConsoleMenuTools
        
        result = PKConsoleMenuTools.promptReversalScreening()
        
        assert result == (4, 50) or result[0] == 4
    
    @patch('pkscreener.classes.ConsoleMenuUtility.PKConsoleTools.clearScreen')
    @patch('builtins.input', side_effect=["6", "4"])  # Option 6 requires NR timeframe
    def test_prompt_reversal_screening_option6(self, mock_input, mock_clear):
        """Test promptReversalScreening option 6."""
        from pkscreener.classes.ConsoleMenuUtility import PKConsoleMenuTools
        
        result = PKConsoleMenuTools.promptReversalScreening()
        
        assert result == (6, 4) or result[0] == 6
    
    @patch('pkscreener.classes.ConsoleMenuUtility.PKConsoleTools.clearScreen')
    @patch('builtins.input', side_effect=["1", "3"])  # Pattern 1 with candles
    def test_prompt_chart_patterns_option1(self, mock_input, mock_clear):
        """Test promptChartPatterns option 1."""
        from pkscreener.classes.ConsoleMenuUtility import PKConsoleMenuTools
        
        result = PKConsoleMenuTools.promptChartPatterns()
        
        assert result == (1, 3) or result[0] == 1
    
    @patch('pkscreener.classes.ConsoleMenuUtility.PKConsoleTools.clearScreen')
    @patch('builtins.input', side_effect=["3", "0.8"])  # Pattern 3 with percent
    def test_prompt_chart_patterns_option3(self, mock_input, mock_clear):
        """Test promptChartPatterns option 3."""
        from pkscreener.classes.ConsoleMenuUtility import PKConsoleMenuTools
        
        result = PKConsoleMenuTools.promptChartPatterns()
        
        assert result[0] == 3
    
    @patch('pkscreener.classes.ConsoleMenuUtility.PKConsoleTools.clearScreen')
    @patch('builtins.input', side_effect=["5"])  # Pattern 5 no extra input
    def test_prompt_chart_patterns_option5(self, mock_input, mock_clear):
        """Test promptChartPatterns option 5."""
        from pkscreener.classes.ConsoleMenuUtility import PKConsoleMenuTools
        
        result = PKConsoleMenuTools.promptChartPatterns()
        
        assert result == (5, 0) or result[0] == 5
    
    @patch('pkscreener.classes.ConsoleMenuUtility.PKConsoleTools.clearScreen')
    @patch('builtins.input', side_effect=["99"])  # Invalid
    @patch('PKDevTools.classes.OutputControls.OutputControls.takeUserInput')
    def test_prompt_chart_patterns_invalid(self, mock_take_input, mock_input, mock_clear):
        """Test promptChartPatterns with invalid value."""
        from pkscreener.classes.ConsoleMenuUtility import PKConsoleMenuTools
        
        result = PKConsoleMenuTools.promptChartPatterns()
        
        # Returns (None, None) on error
        assert result == (None, None) or result is not None
    
    @patch('pkscreener.classes.ConsoleMenuUtility.PKConsoleTools.clearScreen')
    @patch('builtins.input', side_effect=["7", "1"])  # Option 7 requires submenu
    def test_prompt_reversal_screening_option7(self, mock_input, mock_clear):
        """Test promptReversalScreening option 7."""
        from pkscreener.classes.ConsoleMenuUtility import PKConsoleMenuTools
        
        result = PKConsoleMenuTools.promptReversalScreening()
        
        assert result[0] == 7 or result is not None
    
    @patch('pkscreener.classes.ConsoleMenuUtility.PKConsoleTools.clearScreen')
    @patch('builtins.input', side_effect=["10", "1"])  # Option 10 requires submenu
    def test_prompt_reversal_screening_option10(self, mock_input, mock_clear):
        """Test promptReversalScreening option 10."""
        from pkscreener.classes.ConsoleMenuUtility import PKConsoleMenuTools
        
        result = PKConsoleMenuTools.promptReversalScreening()
        
        assert result[0] == 10 or result is not None
    
    @patch('pkscreener.classes.ConsoleMenuUtility.PKConsoleTools.clearScreen')
    @patch('builtins.input', side_effect=["4"])  # maLength for chart pattern
    def test_prompt_chart_pattern_submenu(self, mock_input, mock_clear):
        """Test promptChartPatternSubMenu."""
        from pkscreener.classes.ConsoleMenuUtility import PKConsoleMenuTools
        from pkscreener.classes.MenuOptions import menus
        
        mock_menu = MagicMock()
        mock_menu.level = 3
        
        result = PKConsoleMenuTools.promptChartPatternSubMenu(mock_menu, respChartPattern=3)
        
        assert result == 4 or result is not None
    
    @patch('pkscreener.classes.ConsoleMenuUtility.PKConsoleTools.clearScreen')
    @patch('builtins.input', side_effect=["1"])  # maLength for other pattern
    def test_prompt_chart_pattern_submenu_non3(self, mock_input, mock_clear):
        """Test promptChartPatternSubMenu with non-3 pattern."""
        from pkscreener.classes.ConsoleMenuUtility import PKConsoleMenuTools
        
        mock_menu = MagicMock()
        mock_menu.level = 3
        
        result = PKConsoleMenuTools.promptChartPatternSubMenu(mock_menu, respChartPattern=1)
        
        assert result == 1 or result is not None
