# API Reference

Welcome to the PKScreener API Reference. This documentation is automatically generated from the source code.

**Last Generated:** 2026-04-29 13:13:12

## Core Modules

- [`MainApplication`](api/API_MainApplication.md) `7 classes` `1 function`
- [`globals`](api/API_globals.md) `72 functions`
- [`pkscreenerbot`](api/API_pkscreenerbot.md) `1 class` `43 functions`
- [`pkscreenercli`](api/API_pkscreenercli.md) `5 classes` `3 functions`

## Classes & Modules

- [`ArtTexts`](api/API_classes_ArtTexts.md) `1 function`
- [`AssetsManager`](api/API_classes_AssetsManager.md) `1 class`
- [`Barometer`](api/API_classes_Barometer.md) `1 function`
- [`BotHandlers`](api/API_classes_bot_BotHandlers.md) `7 classes`
- [`CandlePatterns`](api/API_classes_CandlePatterns.md) `1 class`
- [`Changelog`](api/API_classes_Changelog.md) `1 function`
- [`ConfigManager`](api/API_classes_ConfigManager.md) `1 class`
- [`ConsoleMenuUtility`](api/API_classes_ConsoleMenuUtility.md) `1 class`
- [`ConsoleUtility`](api/API_classes_ConsoleUtility.md) `1 class`
- [`CoreFunctions`](api/API_classes_CoreFunctions.md) `6 functions`
- [`DataLoader`](api/API_classes_DataLoader.md) `1 class` `1 function`
- [`ExecuteOptionHandlers`](api/API_classes_ExecuteOptionHandlers.md) `17 functions`
- [`Fetcher`](api/API_classes_Fetcher.md) `1 class`
- [`GlobalStore`](api/API_classes_GlobalStore.md) `1 class` `1 function`
- [`ImageUtility`](api/API_classes_ImageUtility.md) `1 class`
- [`MainLogic`](api/API_classes_MainLogic.md) `2 classes` `6 functions`
- [`MarketMonitor`](api/API_classes_MarketMonitor.md) `1 class`
- [`MarketStatus`](api/API_classes_MarketStatus.md) `1 class`
- [`MenuManager`](api/API_classes_MenuManager.md) `6 classes`
- [`MenuNavigation`](api/API_classes_MenuNavigation.md) `1 class` `1 function`
- [`MenuOptions`](api/API_classes_MenuOptions.md) `3 classes`
- [`NotificationService`](api/API_classes_NotificationService.md) `1 class` `4 functions`
- [`OtaUpdater`](api/API_classes_OtaUpdater.md) `1 class`
- [`OutputFunctions`](api/API_classes_OutputFunctions.md) `19 functions`
- [`PKAnalytics`](api/API_classes_PKAnalytics.md) `1 class`
- [`PKCliRunner`](api/API_classes_cli_PKCliRunner.md) `3 classes`
- [`PKDataService`](api/API_classes_PKDataService.md) `1 class`
- [`PKDemoHandler`](api/API_classes_PKDemoHandler.md) `1 class`
- [`PKMarketOpenCloseAnalyser`](api/API_classes_PKMarketOpenCloseAnalyser.md) `3 classes`
- [`PKPremiumHandler`](api/API_classes_PKPremiumHandler.md) `1 class`
- [`PKScanRunner`](api/API_classes_PKScanRunner.md) `1 class`
- [`PKScheduledTaskProgress`](api/API_classes_PKScheduledTaskProgress.md) `1 class`
- [`PKScheduler`](api/API_classes_PKScheduler.md) `1 class` `1 function`
- [`PKScreenerMain`](api/API_classes_PKScreenerMain.md) `1 class` `1 function`
- [`PKSpreadsheets`](api/API_classes_PKSpreadsheets.md) `1 class`
- [`PKTask`](api/API_classes_PKTask.md) `1 class`
- [`PKUserRegistration`](api/API_classes_PKUserRegistration.md) `2 classes`
- [`Pktalib`](api/API_classes_Pktalib.md) `1 class`
- [`Portfolio`](api/API_classes_Portfolio.md) `3 classes`
- [`PortfolioXRay`](api/API_classes_PortfolioXRay.md) `69 functions`
- [`ResultsLabeler`](api/API_classes_ResultsLabeler.md) `1 class` `1 function`
- [`ResultsManager`](api/API_classes_ResultsManager.md) `1 class`
- [`ScreeningStatistics`](api/API_classes_ScreeningStatistics.md) `8 classes`
- [`StockScreener`](api/API_classes_StockScreener.md) `1 class`
- [`TelegramNotifier`](api/API_classes_TelegramNotifier.md) `1 class`
- [`UserMenuChoicesHandler`](api/API_classes_UserMenuChoicesHandler.md) `1 class`
- [`Utility`](api/API_classes_Utility.md) `1 class` `1 function`
- [`WorkflowManager`](api/API_classes_WorkflowManager.md) `2 functions`
- [`keys`](api/API_classes_keys.md) `1 function`
- [`signals`](api/API_classes_screening_signals.md) `3 classes`

---

## File Structure

The API documentation mirrors the source code structure:

```
pkscreener/
├── __init__.py
├── globals.py
├── pkscreenercli.py
├── pkscreenerbot.py
├── MainApplication.py
├── classes/
│   ├── StockScreener.py
│   ├── ScreeningStatistics.py
│   ├── Fetcher.py
│   ├── CandlePatterns.py
│   ├── Pktalib.py
│   ├── bot/
│   │   └── BotHandlers.py
│   ├── cli/
│   │   └── ...
│   ├── Exchange/
│   │   └── ...
│   └── screening/
│       └── ...
└── ...
```
