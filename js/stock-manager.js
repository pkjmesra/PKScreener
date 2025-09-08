class StockDataManager {
    constructor() {
        this.storageKey = 'ticks_json_data';
        this.ticksData = this.loadFromStorage();
    }

    loadFromStorage() {
        try {
            const stored = localStorage.getItem(this.storageKey);
            if (stored) {
                return JSON.parse(stored);
            }
        } catch (error) {
            console.error('Error loading from storage:', error);
        }
        
        // Return default structure
        return {
            last_updated: new Date().toISOString(),
            stocks: {}
        };
    }

    saveToStorage() {
        try {
            this.ticksData.last_updated = new Date().toISOString();
            localStorage.setItem(this.storageKey, JSON.stringify(this.ticksData));
            return true;
        } catch (error) {
            console.error('Error saving to storage:', error);
            return false;
        }
    }

    processStockData(symbols, opens, highs, lows, closes, volumes) {
        const symbolArray = symbols.split(',').map(s => s.trim().toUpperCase());
        const openArray = opens.split(',').map(v => parseFloat(v.trim()) || 0);
        const highArray = highs.split(',').map(v => parseFloat(v.trim()) || 0);
        const lowArray = lows.split(',').map(v => parseFloat(v.trim()) || 0);
        const closeArray = closes.split(',').map(v => parseFloat(v.trim()) || 0);
        const volumeArray = volumes.split(',').map(v => parseInt(v.trim()) || 0);

        // Validate array lengths
        const maxLength = Math.max(
            symbolArray.length,
            openArray.length,
            highArray.length,
            lowArray.length,
            closeArray.length,
            volumeArray.length
        );

        for (let i = 0; i < maxLength; i++) {
            const symbol = symbolArray[i] || `UNKNOWN_${i}`;
            const open = openArray[i] || 0;
            const high = highArray[i] || 0;
            const low = lowArray[i] || 0;
            const close = closeArray[i] || 0;
            const volume = volumeArray[i] || 0;

            this.updateStock(symbol, open, high, low, close, volume);
        }

        return this.saveToStorage();
    }

    updateStock(symbol, open, high, low, close, volume) {
        if (!this.ticksData.stocks[symbol]) {
            this.ticksData.stocks[symbol] = {
                symbol: symbol,
                ohlcv: { open: 0, high: 0, low: 0, close: 0, volume: 0 },
                last_updated: new Date().toISOString(),
                update_count: 0
            };
        }

        const stock = this.ticksData.stocks[symbol];
        stock.ohlcv.open = open;
        stock.ohlcv.high = high;
        stock.ohlcv.low = low;
        stock.ohlcv.close = close;
        stock.ohlcv.volume = volume;
        stock.last_updated = new Date().toISOString();
        stock.update_count = (stock.update_count || 0) + 1;
    }

    getData() {
        return this.ticksData;
    }

    clearAllData() {
        this.ticksData = {
            last_updated: new Date().toISOString(),
            stocks: {}
        };
        return this.saveToStorage();
    }

    downloadJson() {
        const dataStr = JSON.stringify(this.ticksData, null, 2);
        const dataBlob = new Blob([dataStr], { type: 'application/json' });
        
        const url = URL.createObjectURL(dataBlob);
        const link = document.createElement('a');
        link.href = url;
        link.download = 'ticks.json';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
    }

    getJsonUrl() {
        return window.location.origin + '/data/ticks.json';
    }
}

// Global instance
const stockManager = new StockDataManager();

function processQueryParams(urlParams) {
    const symbol = urlParams.get('symbol');
    const open = urlParams.get('open');
    const high = urlParams.get('high');
    const low = urlParams.get('low');
    const close = urlParams.get('close');
    const volume = urlParams.get('volume');

    if (symbol && open && high && low && close && volume) {
        const success = stockManager.processStockData(symbol, open, high, low, close, volume);
        
        if (success) {
            showStatus(`✅ Updated ${symbol} data from URL parameters`, true);
            
            // Update URL to remove parameters after processing
            const cleanUrl = window.location.origin + window.location.pathname;
            window.history.replaceState({}, document.title, cleanUrl);
        } else {
            showStatus('❌ Failed to process URL parameters', false);
        }
    }
}

function processManualEntry() {
    const symbols = document.getElementById('symbols').value;
    const open = document.getElementById('open').value;
    const high = document.getElementById('high').value;
    const low = document.getElementById('low').value;
    const close = document.getElementById('close').value;
    const volume = document.getElementById('volume').value;

    if (!symbols || !open || !high || !low || !close || !volume) {
        showStatus('❌ Please fill all fields', false);
        return;
    }

    const success = stockManager.processStockData(symbols, open, high, low, close, volume);
    
    if (success) {
        showStatus('✅ Stock data updated successfully!', true);
        loadTicksData();
        clearForm();
    } else {
        showStatus('❌ Failed to update data', false);
    }
}

function loadTicksData() {
    const data = stockManager.getData();
    const preview = document.getElementById('data-preview');
    preview.textContent = JSON.stringify(data, null, 2);
}

function downloadTicksJson() {
    stockManager.downloadJson();
    showStatus('📥 ticks.json download started', true);
}

function clearAllData() {
    if (confirm('Are you sure you want to clear all stock data?')) {
        stockManager.clearAllData();
        showStatus('🗑️ All data cleared', true);
        loadTicksData();
    }
}

function clearForm() {
    document.getElementById('symbols').value = '';
    document.getElementById('open').value = '';
    document.getElementById('high').value = '';
    document.getElementById('low').value = '';
    document.getElementById('close').value = '';
    document.getElementById('volume').value = '';
}

function showStatus(message, isSuccess = true) {
    const statusDiv = document.getElementById('status');
    statusDiv.textContent = message;
    statusDiv.className = isSuccess ? 'status success' : 'status error';
    statusDiv.style.display = 'block';
    
    setTimeout(() => {
        statusDiv.style.display = 'none';
    }, 5000);
}

function copyJsonUrl() {
    const url = stockManager.getJsonUrl();
    navigator.clipboard.writeText(url).then(() => {
        showStatus('📋 URL copied to clipboard!', true);
    }).catch(() => {
        showStatus('❌ Failed to copy URL', false);
    });
}

function openJsonUrl() {
    const url = stockManager.getJsonUrl();
    window.open(url, '_blank');
}

// Make functions globally available
window.processManualEntry = processManualEntry;
window.downloadTicksJson = downloadTicksJson;
window.clearAllData = clearAllData;
window.clearForm = clearForm;
window.copyJsonUrl = copyJsonUrl;
window.openJsonUrl = openJsonUrl;
