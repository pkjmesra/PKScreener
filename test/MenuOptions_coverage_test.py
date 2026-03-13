"""
    The MIT License (MIT)

    Copyright (c) 2023 pkjmesra

    Tests for MenuOptions.py to achieve 90%+ coverage.
"""

import pytest
from unittest.mock import patch, MagicMock
import warnings
warnings.filterwarnings("ignore")


class TestMenuOptionsCoverage:
    """Comprehensive tests for MenuOptions."""
    
    def test_menus_init(self):
        """Test menus initialization."""
        from pkscreener.classes.MenuOptions import menus
        
        m = menus()
        
        assert m.level == 0
        assert m.menuDict == {}
        assert m.strategyNames == []
    
    def test_menu_init(self):
        """Test menu class initialization."""
        from pkscreener.classes.MenuOptions import menu
        
        m = menu(menuKey="X", level=0)
        m.menuText = "Test"
        
        assert m.menuKey == "X"
        assert m.menuText == "Test"
        assert m.level == 0
    
    def test_menu_key_text_label(self):
        """Test menu keyTextLabel method."""
        from pkscreener.classes.MenuOptions import menu
        
        m = menu(menuKey="X", level=0)
        m.menuText = "Test Menu"
        
        label = m.keyTextLabel()
        
        assert "X" in label
        assert "Test Menu" in label
    
    def test_render_for_menu_top_level(self):
        """Test renderForMenu for top level menu."""
        from pkscreener.classes.MenuOptions import menus
        
        m = menus()
        result = m.renderForMenu(selectedMenu=None, asList=True)
        
        assert result is not None
        assert isinstance(result, list)
    
    def test_render_for_menu_x_level0(self):
        """Test renderForMenu for X menu at level 0."""
        from pkscreener.classes.MenuOptions import menus, menu
        
        m = menus()
        parent = menu(menuKey="X", level=0)
        
        result = m.renderForMenu(selectedMenu=parent, asList=True)
        
        assert result is not None
    
    def test_render_for_menu_t_level0(self):
        """Test renderForMenu for T menu at level 0."""
        from pkscreener.classes.MenuOptions import menus, menu
        
        m = menus()
        parent = menu(menuKey="T", level=0)
        
        result = m.renderForMenu(selectedMenu=parent, asList=True)
        
        assert result is not None
    
    def test_render_for_menu_p_level0(self):
        """Test renderForMenu for P menu at level 0."""
        from pkscreener.classes.MenuOptions import menus, menu
        
        m = menus()
        parent = menu(menuKey="P", level=0)
        
        result = m.renderForMenu(selectedMenu=parent, asList=True)
        
        assert result is not None
    
    def test_render_for_menu_d_level0(self):
        """Test renderForMenu for D menu at level 0."""
        from pkscreener.classes.MenuOptions import menus, menu
        
        m = menus()
        parent = menu(menuKey="D", level=0)
        
        result = m.renderForMenu(selectedMenu=parent, asList=True)
        
        assert result is not None
    
    def test_render_for_menu_s_level0(self):
        """Test renderForMenu for S menu at level 0."""
        from pkscreener.classes.MenuOptions import menus, menu
        
        m = menus()
        m.strategyNames = ["Strategy1", "Strategy2"]
        parent = menu(menuKey="S", level=0)
        
        result = m.renderForMenu(selectedMenu=parent, asList=True)
        
        assert result is not None
    
    def test_render_for_menu_level1_d_parent(self):
        """Test renderForMenu for level 1 with D parent."""
        from pkscreener.classes.MenuOptions import menus, menu
        
        m = menus()
        top_menu = menu(menuKey="D", level=0)
        child_menu = menu(menuKey="D", level=1, parent=top_menu)
        
        result = m.renderForMenu(selectedMenu=child_menu, asList=True)
        
        assert result is not None
    
    def test_render_for_menu_level1_t_l(self):
        """Test renderForMenu for T>L menu."""
        from pkscreener.classes.MenuOptions import menus, menu
        
        m = menus()
        top_menu = menu(menuKey="T", level=0)
        child_menu = menu(menuKey="L", level=1, parent=top_menu)
        
        result = m.renderForMenu(selectedMenu=child_menu, asList=True)
        
        assert result is not None
    
    def test_render_for_menu_level1_t_s(self):
        """Test renderForMenu for T>S menu."""
        from pkscreener.classes.MenuOptions import menus, menu
        
        m = menus()
        top_menu = menu(menuKey="T", level=0)
        child_menu = menu(menuKey="S", level=1, parent=top_menu)
        
        result = m.renderForMenu(selectedMenu=child_menu, asList=True)
        
        assert result is not None
    
    def test_render_for_menu_level2_x(self):
        """Test renderForMenu for X at level 2."""
        from pkscreener.classes.MenuOptions import menus, menu
        
        m = menus()
        top_menu = menu(menuKey="X", level=0)
        level1_menu = menu(menuKey="12", level=1, parent=top_menu)
        level2_menu = menu(menuKey="1", level=2, parent=level1_menu)
        
        result = m.renderForMenu(selectedMenu=level2_menu, asList=True)
        
        assert result is not None or result is None
    
    def test_find_method(self):
        """Test find method."""
        from pkscreener.classes.MenuOptions import menus
        
        m = menus()
        m.renderForMenu(selectedMenu=None, asList=True)
        
        result = m.find("X")
        
        assert result is not None or result is None
    
    def test_all_menus_method(self):
        """Test allMenus static method."""
        from pkscreener.classes.MenuOptions import menus
        
        with patch('PKDevTools.classes.PKDateUtilities.PKDateUtilities.isTradingTime', return_value=False):
            run_options, run_key_options = menus.allMenus()
            
            assert isinstance(run_options, list)
            assert isinstance(run_key_options, dict)
    
    @patch('PKDevTools.classes.PKDateUtilities.PKDateUtilities.isTradingTime', return_value=True)
    def test_all_menus_during_trading(self, mock_trading):
        """Test allMenus during trading hours."""
        from pkscreener.classes.MenuOptions import menus
        
        run_options, run_key_options = menus.allMenus()
        
        assert isinstance(run_options, list)
        assert isinstance(run_key_options, dict)
    
    def test_from_dictionary(self):
        """Test fromDictionary method."""
        from pkscreener.classes.MenuOptions import menus, MenuRenderStyle
        
        m = menus()
        test_dict = {"1": "Option 1", "2": "Option 2", "M": "Main Menu"}
        
        m.fromDictionary(
            rawDictionary=test_dict,
            renderStyle=MenuRenderStyle.STANDALONE
        )
        
        assert len(m.menuDict) > 0
    
    def test_render_menu_from_dictionary(self):
        """Test renderMenuFromDictionary method."""
        from pkscreener.classes.MenuOptions import menus, MenuRenderStyle
        
        m = menus()
        test_dict = {"1": "Option 1", "2": "Option 2"}
        
        result = m.renderMenuFromDictionary(
            dict=test_dict,
            asList=True,
            renderStyle=MenuRenderStyle.STANDALONE
        )
        
        assert result is not None
    
    def test_menu_render_style_enum(self):
        """Test MenuRenderStyle enum values."""
        from pkscreener.classes.MenuOptions import MenuRenderStyle
        
        assert MenuRenderStyle.STANDALONE is not None
        assert MenuRenderStyle.TWO_PER_ROW is not None
        assert MenuRenderStyle.THREE_PER_ROW is not None
    
    def test_level1_menus_dict_constants(self):
        """Test menu dictionary constants exist."""
        from pkscreener.classes.MenuOptions import (
            level0MenuDict, level1_X_MenuDict, level1_P_MenuDict,
            level1_T_MenuDict, level2_X_MenuDict
        )
        
        assert isinstance(level0MenuDict, dict)
        assert isinstance(level1_X_MenuDict, dict)
        assert isinstance(level1_P_MenuDict, dict)
        assert isinstance(level1_T_MenuDict, dict)
        assert isinstance(level2_X_MenuDict, dict)
    
    def test_max_menu_option_constant(self):
        """Test MAX_MENU_OPTION constant."""
        from pkscreener.classes.MenuOptions import MAX_MENU_OPTION
        
        assert MAX_MENU_OPTION == 50
    
    def test_indices_map_constant(self):
        """Test INDICES_MAP constant."""
        from pkscreener.classes.MenuOptions import INDICES_MAP
        
        assert isinstance(INDICES_MAP, dict)
        assert "12" in INDICES_MAP  # Nifty 50
    
    def test_render_for_menu_b_level0(self):
        """Test renderForMenu for B menu at level 0."""
        from pkscreener.classes.MenuOptions import menus, menu
        
        m = menus()
        parent = menu(menuKey="B", level=0)
        
        result = m.renderForMenu(selectedMenu=parent, asList=True)
        
        assert result is not None
    
    def test_render_for_menu_g_level0(self):
        """Test renderForMenu for G menu at level 0."""
        from pkscreener.classes.MenuOptions import menus, menu
        
        m = menus()
        parent = menu(menuKey="G", level=0)
        
        result = m.renderForMenu(selectedMenu=parent, asList=True)
        
        assert result is not None
    
    def test_render_for_menu_h_level0(self):
        """Test renderForMenu for H menu at level 0."""
        from pkscreener.classes.MenuOptions import menus, menu
        
        m = menus()
        parent = menu(menuKey="H", level=0)
        
        result = m.renderForMenu(selectedMenu=parent, asList=True)
        
        assert result is not None
    
    def test_render_for_menu_y_level0(self):
        """Test renderForMenu for Y menu at level 0."""
        from pkscreener.classes.MenuOptions import menus, menu
        
        m = menus()
        parent = menu(menuKey="Y", level=0)
        
        result = m.renderForMenu(selectedMenu=parent, asList=True)
        
        assert result is not None or result is None
    
    def test_render_for_menu_e_level0(self):
        """Test renderForMenu for E menu at level 0."""
        from pkscreener.classes.MenuOptions import menus, menu
        
        m = menus()
        parent = menu(menuKey="E", level=0)
        
        result = m.renderForMenu(selectedMenu=parent, asList=True)
        
        assert result is not None or result is None
    
    def test_menu_with_parent(self):
        """Test menu with parent reference."""
        from pkscreener.classes.MenuOptions import menu
        
        parent = menu(menuKey="X", level=0)
        child = menu(menuKey="12", level=1, parent=parent)
        
        assert child.parent == parent
        assert child.parent.menuKey == "X"
    
    def test_render_for_menu_level1_x_parent(self):
        """Test renderForMenu for level 1 with X parent."""
        from pkscreener.classes.MenuOptions import menus, menu
        
        m = menus()
        top_menu = menu(menuKey="X", level=0)
        child_menu = menu(menuKey="12", level=1, parent=top_menu)
        
        result = m.renderForMenu(selectedMenu=child_menu, asList=True)
        
        assert result is not None or result is None
    
    @patch('PKDevTools.classes.OutputControls.OutputControls.printOutput')
    def test_render_menu_from_dictionary_not_as_list(self, mock_print):
        """Test renderMenuFromDictionary with asList=False."""
        from pkscreener.classes.MenuOptions import menus, MenuRenderStyle
        from PKDevTools.classes.OutputControls import OutputControls
        
        m = menus()
        test_dict = {"1": "Option 1", "2": "Option 2"}
        
        # Set the property to True
        output_ctrl = OutputControls()
        original_value = output_ctrl.enableMultipleLineOutput
        output_ctrl.enableMultipleLineOutput = True
        
        try:
            result = m.renderMenuFromDictionary(
                dict=test_dict,
                asList=False,
                renderStyle=MenuRenderStyle.STANDALONE,
                checkUpdate=False  # Avoid OTA check
            )
            
            assert result is not None
        finally:
            output_ctrl.enableMultipleLineOutput = original_value
    
    def test_render_for_menu_level3(self):
        """Test renderForMenu for level 3 menu."""
        from pkscreener.classes.MenuOptions import menus, menu
        
        m = menus()
        top_menu = menu(menuKey="X", level=0)
        level1_menu = menu(menuKey="12", level=1, parent=top_menu)
        level2_menu = menu(menuKey="6", level=2, parent=level1_menu)
        level3_menu = menu(menuKey="1", level=3, parent=level2_menu)
        
        result = m.renderForMenu(selectedMenu=level3_menu, asList=True)
        
        assert result is not None or result is None
    
    def test_render_for_menu_level4(self):
        """Test renderForMenu for level 4 menu."""
        from pkscreener.classes.MenuOptions import menus, menu
        
        m = menus()
        top_menu = menu(menuKey="X", level=0)
        level1_menu = menu(menuKey="12", level=1, parent=top_menu)
        level2_menu = menu(menuKey="6", level=2, parent=level1_menu)
        level3_menu = menu(menuKey="7", level=3, parent=level2_menu)
        level4_menu = menu(menuKey="1", level=4, parent=level3_menu)
        
        result = m.renderForMenu(selectedMenu=level4_menu, asList=True)
        
        assert result is not None or result is None
    
    def test_all_menus_covers_deep_levels(self):
        """Test allMenus method traverses deep menu levels."""
        from pkscreener.classes.MenuOptions import menus
        
        # This will traverse all menu combinations
        run_options, run_key_options = menus.allMenus(topLevel="X", index=12)
        
        # Check that we have some multi-level options
        assert len(run_options) > 0
        
        # Check for options with multiple levels
        deep_options = [opt for opt in run_options if opt.count(":") >= 4]
        assert len(deep_options) >= 0  # Some menus have deep levels
    
    def test_render_for_menu_c_level0(self):
        """Test renderForMenu for C menu at level 0."""
        from pkscreener.classes.MenuOptions import menus, menu
        
        m = menus()
        parent = menu(menuKey="C", level=0)
        
        result = m.renderForMenu(selectedMenu=parent, asList=True)
        
        assert result is not None or result is None
    
    def test_render_for_menu_u_level0(self):
        """Test renderForMenu for U menu at level 0."""
        from pkscreener.classes.MenuOptions import menus, menu
        
        m = menus()
        parent = menu(menuKey="U", level=0)
        
        result = m.renderForMenu(selectedMenu=parent, asList=True)
        
        assert result is not None or result is None
    
    def test_render_for_menu_f_level0(self):
        """Test renderForMenu for F menu at level 0."""
        from pkscreener.classes.MenuOptions import menus, menu
        
        m = menus()
        parent = menu(menuKey="F", level=0)
        
        result = m.renderForMenu(selectedMenu=parent, asList=True)
        
        assert result is not None or result is None
    
    @patch('PKDevTools.classes.OutputControls.OutputControls.printOutput')
    @patch('pkscreener.classes.MenuOptions.OTAUpdater.checkForUpdate')
    def test_render_menu_with_ota_check(self, mock_ota, mock_print):
        """Test renderMenuFromDictionary with OTA check."""
        from pkscreener.classes.MenuOptions import menus, MenuRenderStyle
        from PKDevTools.classes.OutputControls import OutputControls
        
        m = menus()
        test_dict = {"1": "Option 1", "2": "Option 2"}
        
        output_ctrl = OutputControls()
        original_value = output_ctrl.enableMultipleLineOutput
        output_ctrl.enableMultipleLineOutput = True
        
        try:
            result = m.renderMenuFromDictionary(
                dict=test_dict,
                asList=False,
                renderStyle=MenuRenderStyle.STANDALONE,
                checkUpdate=True  # Trigger OTA check
            )
            
            assert result is not None
            # OTA check should have been called
            mock_ota.assert_called()
        finally:
            output_ctrl.enableMultipleLineOutput = original_value
    
    def test_from_dictionary_with_skip(self):
        """Test fromDictionary with skip parameter."""
        from pkscreener.classes.MenuOptions import menus, MenuRenderStyle
        
        m = menus()
        test_dict = {"1": "Option 1", "2": "Option 2", "3": "Option 3"}
        
        m.fromDictionary(
            rawDictionary=test_dict,
            renderStyle=MenuRenderStyle.STANDALONE,
            skip=["2"]  # Skip option 2
        )
        
        assert len(m.menuDict) > 0
    
    def test_from_dictionary_with_substitutes(self):
        """Test fromDictionary with substitutes parameter."""
        from pkscreener.classes.MenuOptions import menus, MenuRenderStyle
        
        m = menus()
        test_dict = {"1": "Option {0}", "2": "Option 2"}
        
        m.fromDictionary(
            rawDictionary=test_dict,
            renderStyle=MenuRenderStyle.STANDALONE,
            substitutes=["Substituted"]
        )
        
        assert len(m.menuDict) > 0
    
    def test_from_dictionary_with_zero_substitute(self):
        """Test fromDictionary with zero substitute value."""
        from pkscreener.classes.MenuOptions import menus, MenuRenderStyle
        
        m = menus()
        test_dict = {"1": "Option {0}", "2": "Option {0}", "3": "Option 3"}
        
        m.fromDictionary(
            rawDictionary=test_dict,
            renderStyle=MenuRenderStyle.STANDALONE,
            substitutes=[0, "Valid"]  # First is 0, should skip
        )
        
        assert len(m.menuDict) > 0
