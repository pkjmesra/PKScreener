from importlib.util import find_spec

Imports = {
    "scipy": find_spec("scipy") is not None,
    "sklearn": find_spec("sklearn") is not None,
    "talib": find_spec("talib") is not None,
    "pandas_ta": find_spec("pandas_ta") is not None,
    "tensorflow": find_spec("tensorflow") is not None,
    "keras": find_spec("keras") is not None,
    "yfinance": find_spec("yfinance") is not None,
}
