let lastPrice = 0;

async function updateBitcoinPrice() {
try {
    console.log("Updated BTC")
    const response = await fetch('https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd&include_24hr_change=true');
    const data = await response.json();
    
    const currentPrice = data.bitcoin.usd;
    const priceChange = data.bitcoin.usd_24h_change;
    
    const priceElement = document.querySelector('.price');
    const statusText = document.querySelector('.status-text');
    const statusIcon = document.querySelector('.status-icon');
    
    // Update price
    priceElement.textContent = `$${currentPrice.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
    
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