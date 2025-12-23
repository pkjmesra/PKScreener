"""
    The MIT License (MIT)

    Copyright (c) 2023 pkjmesra

    Tests for PKDataService.py to achieve 90%+ coverage.
"""

import pytest
from unittest.mock import patch, MagicMock
import json
import warnings
warnings.filterwarnings("ignore")


class TestPKDataServiceCoverage:
    """Comprehensive tests for PKDataService."""
    
    def test_pkdataservice_init(self):
        """Test PKDataService can be instantiated."""
        from pkscreener.classes.PKDataService import PKDataService
        
        service = PKDataService()
        assert service is not None
    
    def test_get_symbols_empty_list(self):
        """Test getSymbolsAndSectorInfo with empty list."""
        from pkscreener.classes.PKDataService import PKDataService
        
        service = PKDataService()
        config = MagicMock()
        config.longTimeout = 1
        
        result, left_out = service.getSymbolsAndSectorInfo(config, [])
        
        assert result == []
        assert left_out == []
    
    @patch('pkscreener.classes.PKDataService.PKScheduler.scheduleTasks')
    @patch('PKNSETools.PKCompanyGeneral.initialize')
    @patch('PKNSETools.PKCompanyGeneral.download')
    def test_get_symbols_with_stocks(self, mock_download, mock_init, mock_schedule):
        """Test getSymbolsAndSectorInfo with stock codes."""
        from pkscreener.classes.PKDataService import PKDataService
        from pkscreener.classes.PKTask import PKTask
        
        service = PKDataService()
        config = MagicMock()
        config.longTimeout = 1
        
        # Mock the task result
        def side_effect(tasksList, **kwargs):
            for task in tasksList:
                task.result = json.dumps({"info": {"symbol": task.userData, "sector": "IT"}})
        
        mock_schedule.side_effect = side_effect
        
        result, left_out = service.getSymbolsAndSectorInfo(config, ["SBIN", "INFY"])
        
        assert isinstance(result, list)
        assert isinstance(left_out, list)
    
    @patch('pkscreener.classes.PKDataService.PKScheduler.scheduleTasks')
    @patch('PKNSETools.PKCompanyGeneral.initialize')
    @patch('PKNSETools.PKCompanyGeneral.download')
    def test_get_symbols_with_none_result(self, mock_download, mock_init, mock_schedule):
        """Test getSymbolsAndSectorInfo when task result is None."""
        from pkscreener.classes.PKDataService import PKDataService
        
        service = PKDataService()
        config = MagicMock()
        config.longTimeout = 1
        
        # Task results are None
        def side_effect(tasksList, **kwargs):
            for task in tasksList:
                task.result = None
        
        mock_schedule.side_effect = side_effect
        
        result, left_out = service.getSymbolsAndSectorInfo(config, ["SBIN"])
        
        assert result == []
        assert left_out == ["SBIN"]
    
    @patch('pkscreener.classes.PKDataService.PKScheduler.scheduleTasks')
    @patch('PKNSETools.PKCompanyGeneral.initialize')
    def test_get_symbols_with_invalid_json(self, mock_init, mock_schedule):
        """Test getSymbolsAndSectorInfo with invalid JSON result."""
        from pkscreener.classes.PKDataService import PKDataService
        
        service = PKDataService()
        config = MagicMock()
        config.longTimeout = 1
        
        def side_effect(tasksList, **kwargs):
            for task in tasksList:
                task.result = json.dumps({"other_key": "value"})  # No "info" key
        
        mock_schedule.side_effect = side_effect
        
        result, left_out = service.getSymbolsAndSectorInfo(config, ["SBIN"])
        
        assert result == []
        assert left_out == ["SBIN"]
    
    @patch('pkscreener.classes.PKDataService.PKScheduler.scheduleTasks')
    @patch('PKNSETools.PKCompanyGeneral.initialize')
    def test_get_symbols_partial_success(self, mock_init, mock_schedule):
        """Test getSymbolsAndSectorInfo with partial success."""
        from pkscreener.classes.PKDataService import PKDataService
        
        service = PKDataService()
        config = MagicMock()
        config.longTimeout = 1
        
        def side_effect(tasksList, **kwargs):
            for i, task in enumerate(tasksList):
                if i == 0:
                    task.result = json.dumps({"info": {"symbol": task.userData}})
                else:
                    task.result = None
        
        mock_schedule.side_effect = side_effect
        
        result, left_out = service.getSymbolsAndSectorInfo(config, ["SBIN", "INFY"])
        
        assert len(result) == 1
        assert "INFY" in left_out
