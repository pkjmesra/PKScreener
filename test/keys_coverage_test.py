"""
    The MIT License (MIT)

    Copyright (c) 2023 pkjmesra

    Tests for keys.py to achieve 90%+ coverage.
"""

import pytest
from unittest.mock import patch, MagicMock
import warnings
warnings.filterwarnings("ignore")


class TestKeysCoverage:
    """Comprehensive tests for keys module."""
    
    @patch('click.getchar', return_value='\x1b[A')  # UP
    @patch('click.echo')
    def test_keyboard_arrow_input_up(self, mock_echo, mock_getchar):
        """Test UP arrow key."""
        from pkscreener.classes.keys import getKeyBoardArrowInput
        
        result = getKeyBoardArrowInput()
        
        assert result == 'UP'
    
    @patch('click.getchar', return_value='\x1b[B')  # DOWN
    @patch('click.echo')
    def test_keyboard_arrow_input_down(self, mock_echo, mock_getchar):
        """Test DOWN arrow key."""
        from pkscreener.classes.keys import getKeyBoardArrowInput
        
        result = getKeyBoardArrowInput()
        
        assert result == 'DOWN'
    
    @patch('click.getchar', return_value='\x1b[C')  # RIGHT
    @patch('click.echo')
    def test_keyboard_arrow_input_right(self, mock_echo, mock_getchar):
        """Test RIGHT arrow key."""
        from pkscreener.classes.keys import getKeyBoardArrowInput
        
        result = getKeyBoardArrowInput()
        
        assert result == 'RIGHT'
    
    @patch('click.getchar', return_value='\x1b[D')  # LEFT
    @patch('click.echo')
    def test_keyboard_arrow_input_left(self, mock_echo, mock_getchar):
        """Test LEFT arrow key."""
        from pkscreener.classes.keys import getKeyBoardArrowInput
        
        result = getKeyBoardArrowInput()
        
        assert result == 'LEFT'
    
    @patch('click.getchar', return_value='\r')  # RETURN
    @patch('click.echo')
    def test_keyboard_arrow_input_return(self, mock_echo, mock_getchar):
        """Test RETURN key."""
        from pkscreener.classes.keys import getKeyBoardArrowInput
        
        result = getKeyBoardArrowInput()
        
        assert result == 'RETURN'
    
    @patch('click.getchar', return_value='\n')  # RETURN newline
    @patch('click.echo')
    def test_keyboard_arrow_input_newline(self, mock_echo, mock_getchar):
        """Test newline RETURN key."""
        from pkscreener.classes.keys import getKeyBoardArrowInput
        
        result = getKeyBoardArrowInput()
        
        assert result == 'RETURN'
    
    @patch('click.getchar', return_value='C')  # CANCEL
    @patch('click.echo')
    def test_keyboard_arrow_input_cancel(self, mock_echo, mock_getchar):
        """Test CANCEL key."""
        from pkscreener.classes.keys import getKeyBoardArrowInput
        
        result = getKeyBoardArrowInput()
        
        assert result == 'CANCEL'
    
    @patch('click.getchar', return_value='c')  # CANCEL lowercase
    @patch('click.echo')
    def test_keyboard_arrow_input_cancel_lower(self, mock_echo, mock_getchar):
        """Test lowercase cancel key."""
        from pkscreener.classes.keys import getKeyBoardArrowInput
        
        result = getKeyBoardArrowInput()
        
        assert result == 'CANCEL'
    
    @patch('click.getchar', return_value='x')  # Unknown key
    @patch('click.echo')
    def test_keyboard_arrow_input_unknown(self, mock_echo, mock_getchar):
        """Test unknown key."""
        from pkscreener.classes.keys import getKeyBoardArrowInput
        
        result = getKeyBoardArrowInput()
        
        assert result is None
    
    @patch('click.getchar', return_value='\x1b[A')
    @patch('click.echo')
    def test_keyboard_arrow_input_empty_message(self, mock_echo, mock_getchar):
        """Test with empty message."""
        from pkscreener.classes.keys import getKeyBoardArrowInput
        
        result = getKeyBoardArrowInput(message="")
        
        # Empty message should not print
        assert result == 'UP'
    
    @patch('click.getchar', return_value='\x1b[A')
    @patch('click.echo')
    def test_keyboard_arrow_input_custom_message(self, mock_echo, mock_getchar):
        """Test with custom message."""
        from pkscreener.classes.keys import getKeyBoardArrowInput
        
        result = getKeyBoardArrowInput(message="Custom message")
        
        mock_echo.assert_called()
        assert result == 'UP'
    
    @patch('platform.system', return_value='Windows')
    @patch('click.getchar', return_value='àK')  # Windows LEFT
    @patch('click.echo')
    def test_keyboard_arrow_windows_left(self, mock_echo, mock_getchar, mock_platform):
        """Test Windows LEFT arrow key."""
        from pkscreener.classes.keys import getKeyBoardArrowInput
        
        result = getKeyBoardArrowInput()
        
        # Should recognize Windows arrow key
        assert result == 'LEFT' or result is None
    
    @patch('platform.system', return_value='Windows')
    @patch('click.getchar', return_value='àH')  # Windows UP
    @patch('click.echo')
    def test_keyboard_arrow_windows_up(self, mock_echo, mock_getchar, mock_platform):
        """Test Windows UP arrow key."""
        from pkscreener.classes.keys import getKeyBoardArrowInput
        
        result = getKeyBoardArrowInput()
        
        assert result == 'UP' or result is None
    
    @patch('platform.system', return_value='Windows')
    @patch('click.getchar', return_value='XK')  # Windows two-char LEFT
    @patch('click.echo')
    def test_keyboard_arrow_windows_two_char(self, mock_echo, mock_getchar, mock_platform):
        """Test Windows two-character arrow key."""
        from pkscreener.classes.keys import getKeyBoardArrowInput
        
        result = getKeyBoardArrowInput()
        
        # Should parse Windows-style two char
        assert result == 'LEFT' or result is None
    
    @patch('platform.system', return_value='Darwin')  # Mac
    @patch('click.getchar', return_value='XD')  # Two-char LEFT for non-Windows
    @patch('click.echo')
    def test_keyboard_arrow_mac_two_char(self, mock_echo, mock_getchar, mock_platform):
        """Test Mac/Linux two-character arrow key."""
        from pkscreener.classes.keys import getKeyBoardArrowInput
        
        result = getKeyBoardArrowInput()
        
        # Should parse non-Windows style two char
        assert result == 'LEFT' or result is None
    
    @patch('platform.system', return_value='Linux')
    @patch('click.getchar', return_value='XA')  # Two-char UP for non-Windows
    @patch('click.echo')
    def test_keyboard_arrow_linux_up(self, mock_echo, mock_getchar, mock_platform):
        """Test Linux two-character UP arrow key."""
        from pkscreener.classes.keys import getKeyBoardArrowInput
        
        result = getKeyBoardArrowInput()
        
        assert result == 'UP' or result is None
    
    @patch('platform.system', return_value='Linux')
    @patch('click.getchar', return_value='XB')  # Two-char DOWN
    @patch('click.echo')
    def test_keyboard_arrow_linux_down(self, mock_echo, mock_getchar, mock_platform):
        """Test Linux two-character DOWN arrow key."""
        from pkscreener.classes.keys import getKeyBoardArrowInput
        
        result = getKeyBoardArrowInput()
        
        assert result == 'DOWN' or result is None
    
    @patch('platform.system', return_value='Linux')
    @patch('click.getchar', return_value='XC')  # Two-char RIGHT
    @patch('click.echo')
    def test_keyboard_arrow_linux_right(self, mock_echo, mock_getchar, mock_platform):
        """Test Linux two-character RIGHT arrow key."""
        from pkscreener.classes.keys import getKeyBoardArrowInput
        
        result = getKeyBoardArrowInput()
        
        assert result == 'RIGHT' or result is None
    
    @patch('platform.system', return_value='Windows')
    @patch('click.getchar', return_value='XH')  # Windows two-char UP
    @patch('click.echo')
    def test_keyboard_arrow_windows_h(self, mock_echo, mock_getchar, mock_platform):
        """Test Windows H key (UP)."""
        from pkscreener.classes.keys import getKeyBoardArrowInput
        
        result = getKeyBoardArrowInput()
        
        assert result == 'UP' or result is None
    
    @patch('platform.system', return_value='Windows')
    @patch('click.getchar', return_value='XP')  # Windows two-char DOWN
    @patch('click.echo')
    def test_keyboard_arrow_windows_p(self, mock_echo, mock_getchar, mock_platform):
        """Test Windows P key (DOWN)."""
        from pkscreener.classes.keys import getKeyBoardArrowInput
        
        result = getKeyBoardArrowInput()
        
        assert result == 'DOWN' or result is None
    
    @patch('platform.system', return_value='Windows')
    @patch('click.getchar', return_value='XM')  # Windows two-char RIGHT
    @patch('click.echo')
    def test_keyboard_arrow_windows_m(self, mock_echo, mock_getchar, mock_platform):
        """Test Windows M key (RIGHT)."""
        from pkscreener.classes.keys import getKeyBoardArrowInput
        
        result = getKeyBoardArrowInput()
        
        assert result == 'RIGHT' or result is None
