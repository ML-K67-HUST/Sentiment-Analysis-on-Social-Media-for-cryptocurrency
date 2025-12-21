let lastPrice = 0;

async function updateBitcoinPrice() {
    try {
        const response = await fetch('http://localhost:8000/chart/');
        const data = await response.json();

        if (!data || data.length === 0) return;

        // Get latest price
        const currentData = data[data.length - 1];
        const currentPrice = currentData.price;

        // Calculate 24h change
        // Find data point approx 24h ago (86400 seconds)
        // Data is ascending by timestamp
        const now = new Date(currentData.timestamp).getTime();
        const oneDayAgo = now - (24 * 60 * 60 * 1000);

        // Find closest point to oneDayAgo
        const closePoint = data.find(item => new Date(item.timestamp).getTime() >= oneDayAgo);
        const oldPrice = closePoint ? closePoint.price : currentPrice;

        const priceChange = ((currentPrice - oldPrice) / oldPrice) * 100;

        const priceElement = document.querySelector('.price');
        const statusText = document.querySelector('.status-text');
        const statusIcon = document.querySelector('.status-icon');

        // Update price
        priceElement.textContent = `$${currentPrice.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

        // Update percentage
        statusText.textContent = `${priceChange.toFixed(3)}%`;

        // Update colors and arrow direction
        if (priceChange >= 0) {
            statusText.className = 'status-text up';
            priceElement.className = 'price up';
            statusIcon.src = 'style/assets/arrow_drop_up_24dp_E8EAED_FILL0_wght400_GRAD0_opsz24.svg';
        } else {
            statusText.className = 'status-text down';
            priceElement.className = 'price down';
            statusIcon.src = 'style/assets/arrow_drop_down_24dp_E8EAED_FILL0_wght400_GRAD0_opsz24.svg';
        }

        lastPrice = currentPrice;
    } catch (error) {
        console.error('Error fetching Bitcoin price:', error);
    }
}

// Update immediately and then every minute
updateBitcoinPrice();
setInterval(updateBitcoinPrice, 60000);