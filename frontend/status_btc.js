let lastPrice = 0;
let ws;

function connectWebSocket() {
    ws = new WebSocket('wss://stream.binance.com:9443/ws/btcusdt@ticker');

    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        updatePriceDisplay(data);
    };

    ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        fallbackToRESTAPI();
    };

    ws.onclose = () => {
        console.log('WebSocket connection closed. Reconnecting...');
        setTimeout(connectWebSocket, 60000); // Reconnect after 5 seconds
    };
}

function updatePriceDisplay(data) {
    const currentPrice = parseFloat(data.c); // Current price
    const priceChange = parseFloat(data.p); // 24h price change
    const priceChangePercent = parseFloat(data.P); // 24h price change percent

    const priceElement = document.querySelector('.price');
    const statusText = document.querySelector('.status-text');
    const statusIcon = document.querySelector('.status-icon');

    // Update price
    priceElement.textContent = `$${currentPrice.toLocaleString('en-US', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    })}`;

    // Update percentage
    statusText.textContent = `${priceChangePercent.toFixed(3)}%`;

    // Update colors and arrow direction
    if (priceChangePercent >= 0) {
        statusText.className = 'status-text up';
        priceElement.className = 'price up';
        statusIcon.src = './style/assets/arrow_drop_up_24dp_E8EAED_FILL0_wght400_GRAD0_opsz24.svg';
    } else {
        statusText.className = 'status-text down';
        priceElement.className = 'price down';
        statusIcon.src = './style/assets/arrow_drop_down_24dp_E8EAED_FILL0_wght400_GRAD0_opsz24.svg';
    }

    lastPrice = currentPrice;
}

async function fallbackToRESTAPI() {
    try {
        const response = await fetch('https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd&include_24hr_change=true');
        const data = await response.json();
        
        const currentPrice = data.bitcoin.usd;
        const priceChange = data.bitcoin.usd_24h_change;
        
        updatePriceDisplay({
            c: currentPrice,
            P: priceChange
        });
    } catch (error) {
        console.error('Error fetching Bitcoin price:', error);
    }
}

// Start WebSocket connection
connectWebSocket();

// Fallback to REST API if WebSocket fails
window.addEventListener('load', fallbackToRESTAPI);