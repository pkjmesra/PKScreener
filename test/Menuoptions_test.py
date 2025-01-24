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
import unittest
from unittest.mock import patch, MagicMock

from pkscreener.classes.MenuOptions import menu, menus, level0MenuDict, Pin_MenuDict, CANDLESTICK_DICT, MenuRenderStyle

class TestMenu:
    def test_create(self):
        m = menu()
        m.create("1", "Test Menu", level=1, isException=False, parent=None)
        assert m.menuKey == "1"
        assert m.menuText == "Test Menu"
        assert m.level == 1
        assert m.isException == False
        assert m.parent == None

    def test_keyTextLabel(self):
        m = menu()
        m.menuKey = "1"
        m.menuText = "Test Menu"
        assert m.keyTextLabel() == "1 > Test Menu"

    def test_commandTextKey(self):
        m = menu()
        m.menuKey = "1"
        m.parent = None
        assert m.commandTextKey() == "/1"
        p = menu()
        p.menuKey = "P"
        m.parent = p
        assert m.commandTextKey() == "/P_1"

    def test_commandTextLabel(self):
        m = menu()
        m.menuText = "Child Menu"
        m.parent = None
        assert m.commandTextLabel() == "Child Menu"
        p = menu()
        p.menuText = "P"
        m.parent = p
        assert m.commandTextLabel() == "P > Child Menu"

    def test_render(self):
        m = menu()
        m.menuKey = "1"
        m.menuText = "Test Menu"
        m.isException = False
        m.hasLeftSibling = False
        assert m.render() == "\n     1 > Test Menu"

    def test_renderSpecial(self):
        m = menu()
        m.menuKey = "T"
        m.level = 0
        assert "Toggle between long-term (Default)" in m.renderSpecial("T")
        m.menuText = "Random"
        m.level = 1
        assert m.renderSpecial("T") == "~"
        assert m.renderSpecial("Whatever") == "~"
        m.level = 0
        assert m.renderSpecial("AnythingOtherThanT") == "~"

class TestMenus:
    def test_fromDictionary(self):
        m = menus()
        rawDictionary = {
            "1": "Menu 1",
            "2": "Menu 2",
            "3": "Menu 3"
        }
        m.fromDictionary(rawDictionary)
        assert len(m.menuDict) == 3
        assert m.find("1").menuText.strip() == "Menu 1"
        assert m.find("2").menuText.strip() == "Menu 2"
        assert m.find("3").menuText.strip() == "Menu 3"

    def test_render(self):
        m = menus()
        rawDictionary = {
            "1": "Menu 1",
            "2": "Menu 2",
            "3": "Menu 3"
        }
        m.fromDictionary(rawDictionary)
        assert m.render().replace(" ","") == f"\n1>Menu1\n2>Menu2\n3>Menu3"

    def test_find_existing_key(self):
        m = menus()
        rawDictionary = {
            "1": "Menu 1",
            "2": "Menu 2",
            "3": "Menu 3"
        }
        m.fromDictionary(rawDictionary)
        assert m.find("1").menuText.strip() == "Menu 1"

    def test_find_nonexistent_key(self):
        m = menus()
        rawDictionary = {
            "1": "Menu 1",
            "2": "Menu 2",
            "3": "Menu 3"
        }
        m.fromDictionary(rawDictionary)
        assert m.find("4") is None
        assert m.find() is None

    def test_renderLevel0Menus(self):
        m = menus()
        rawDictionary = {
            "1": "Menu 1",
            "2": "Menu 2",
            "3": "Menu 3"
        }
        m.fromDictionary(rawDictionary)
        assert len(m.renderForMenu().split("\n")) >= len(level0MenuDict.keys())

    def test_renderForMenu_Lorenzian(self):
        m = menus()
        m.renderForMenu()
        m1 = m.find("X")
        m1.level = 3
        m1.menuKey = "7"
        m1.parent = menu()
        m1.parent.menuKey = "6"
        list_menus = m.renderForMenu(selectedMenu=m1, asList=True)
        assert len(list_menus) == 4
        assert list_menus[0].menuText.strip() == "Buy"
        assert list_menus[1].menuText.strip() == "Sell"
        assert list_menus[2].menuText.strip() == "Any/All"
    
    def test_renderLevel_X(self):
        m = menus()
        m1 = menu()
        assert m.renderForMenu() is not None
        assert m.renderForMenu(selectedMenu=menu(parent=m1,level=0)) is not None
        assert m.renderForMenu(selectedMenu=menu(parent=m1,level=1)) is not None
        keys = ["6","7","21","22","30","32","33","40"]
        for key in keys:
            assert m.renderForMenu(selectedMenu=menu(parent=m1,level=2,menuKey=key)) is not None
        assert m.renderForMenu(selectedMenu=menu(parent=menu(menuKey="6"),level=3,menuKey="7")) is not None
        assert m.renderForMenu(selectedMenu=menu(parent=menu(menuKey="6"),level=3,menuKey="10")) is not None
        assert m.renderForMenu(selectedMenu=menu(parent=menu(menuKey="7"),level=3,menuKey="3")) is not None
        assert m.renderForMenu(selectedMenu=menu(parent=menu(menuKey="7"),level=3,menuKey="6")) is not None
        assert m.renderForMenu(selectedMenu=menu(parent=menu(menuKey="7"),level=3,menuKey="9")) is not None
        assert m.renderForMenu(selectedMenu=menu(parent=menu(menuKey="40"),level=3,menuKey="1")) is not None
        assert m.renderForMenu(selectedMenu=menu(parent=menu(menuKey="40"),level=3,menuKey="2")) is not None

class TestAllMenus(unittest.TestCase):

    @patch('PKDevTools.classes.PKDateUtilities')
    @patch('pkscreener.classes.MenuOptions.menus')
    def test_all_menus_positive(self, mock_menus, mock_PKDateUtilities):
        # Setup mock data
        mock_PKDateUtilities.isTradingTime.return_value = True
        mock_menu_instance = MagicMock()
        mock_menus.return_value = mock_menu_instance
        
        # Mocking the behavior of renderForMenu
        mock_menu_instance.renderForMenu.side_effect = [
            [menu(), menu()],  # First call
            None,                  # Second call (indicating no child menus)
            [menu()],     # Third call
            None,                  # Fourth call
            [menu()],     # Fifth call
            None,                  # Sixth call
            [menu()],     # Seventh call
            None                   # Eighth call
        ]
        
        runOptions, runKeyOptions = menus.allMenus()
        
        # Assertions to validate the output
        self.assertIsInstance(runOptions, list)
        self.assertIsInstance(runKeyOptions, dict)
        self.assertGreater(len(runOptions), 0)
        self.assertGreater(len(runKeyOptions), 0)

    @patch('PKDevTools.classes.PKDateUtilities')
    @patch('pkscreener.classes.MenuOptions.menus')
    def test_all_menus_negative(self, mock_menus, mock_PKDateUtilities):
        # Setup mock data
        mock_PKDateUtilities.isTradingTime.return_value = False
        mock_menu_instance = MagicMock()
        mock_menus.return_value = mock_menu_instance
        
        # Mocking the behavior of renderForMenu to return empty lists
        mock_menu_instance.renderForMenu.return_value = []
        
        runOptions, runKeyOptions = menus.allMenus()
        
        # Assertions to validate the output
        self.assertEqual(runOptions, [])
        self.assertEqual(runKeyOptions, {})

    @patch('PKDevTools.classes.PKDateUtilities')
    def test_all_menus_edge_case(self, mock_PKDateUtilities):
        # Edge case: No options available
        mock_PKDateUtilities.isTradingTime.return_value = False
        
        runOptions, runKeyOptions = menus.allMenus(topLevel="NonExistent", index=99)
        
        # Assertions to validate the output
        self.assertEqual(runOptions, [])
        self.assertEqual(runKeyOptions, {})

class TestMenuRendering(unittest.TestCase):
    # @patch('pkscreener.classes.MenuOptions.Pin_MenuDict') 
    @patch('pkscreener.classes.MenuOptions.menus.renderMenuFromDictionary')  # Mocking the renderMenuFromDictionary method
    def test_renderPinnedMenu_positive(self, mock_render):
        m = menus()
        # Arrange
        mock_render.return_value = "Rendered Menu"
        substitutes = ["Sub1", "Sub2"]
        skip = ["Skip1"]

        # Act
        result = m.renderPinnedMenu(substitutes=substitutes, skip=skip)

        # Assert
        self.assertEqual(result, "Rendered Menu")
        mock_render.assert_called_once_with(
            dict=Pin_MenuDict,
            exceptionKeys=["M"],
            coloredValues=(["M"]),
            defaultMenu="M",
            substitutes=substitutes,
            skip=skip
        )

    # @patch('pkscreener.classes.MenuOptions.Pin_MenuDict')
    @patch('pkscreener.classes.MenuOptions.menus.renderMenuFromDictionary')
    def test_renderPinnedMenu_negative(self, mock_render):
        m = menus()
        # Arrange
        mock_render.side_effect = Exception("Error rendering menu")
        substitutes = []
        skip = []

        # Act & Assert
        with self.assertRaises(Exception) as context:
            m.renderPinnedMenu(substitutes=substitutes, skip=skip)
        self.assertEqual(str(context.exception), "Error rendering menu")

    # @patch('pkscreener.classes.MenuOptions.CANDLESTICK_DICT')
    @patch('pkscreener.classes.MenuOptions.menus.renderMenuFromDictionary')
    def test_renderCandleStickPatterns_positive(self, mock_render):
        m = menus()
        # Arrange
        mock_render.return_value = "Rendered Candlestick Patterns"
        skip = ["SkipPattern"]

        # Act
        result = m.renderCandleStickPatterns(skip=skip)

        # Assert
        self.assertEqual(result, "Rendered Candlestick Patterns")
        mock_render.assert_called_once_with(
            dict=CANDLESTICK_DICT,
            exceptionKeys=["0", "M"],
            coloredValues=(["0"]),
            defaultMenu="0",
            renderStyle=MenuRenderStyle.TWO_PER_ROW,
            optionText="  [+] Would you like to filter by a specific Candlestick pattern? Select filter:",
            skip=skip
        )

    # @patch('pkscreener.classes.MenuOptions.CANDLESTICK_DICT')
    @patch('pkscreener.classes.MenuOptions.menus.renderMenuFromDictionary')
    def test_renderCandleStickPatterns_negative(self, mock_render):
        m = menus()
        # Arrange
        mock_render.side_effect = Exception("Error rendering candlestick patterns")
        skip = []

        # Act & Assert
        with self.assertRaises(Exception) as context:
            m.renderCandleStickPatterns(skip=skip)
        self.assertEqual(str(context.exception), "Error rendering candlestick patterns")
