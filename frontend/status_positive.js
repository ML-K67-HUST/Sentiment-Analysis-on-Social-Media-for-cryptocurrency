// Mock function to simulate getting data from an API
// Replace this with your actual data fetching logic
async function fetchPositiveRate() {
    const response = await fetch('http://localhost:8000/chart/');
    const dataChart = await response.json();
    const lastElement = dataChart[dataChart.length - 1];

    // Access the 'bitcoin_index_score' from the last element
    const bitcoinIndexScore = lastElement.bitcoin_index_score;
    
    return {
        rate: bitcoinIndexScore, // Already a percentage (0-100)
        trend: true // Positive sentiment trend
    };
}

async function updatePositiveRate() {
    try {
        const data = await fetchPositiveRate();
        
        const rateElement = document.querySelector('.rate');
        const statusText = document.querySelector('.pst-status-text');
        const trendIcon = document.querySelector('.trend');
        
        // Update rate
        rateElement.textContent = `${data.rate.toFixed(2)}%`;
        
        // Update trend and colors
        // if (data.trend) {
        //     rateElement.className = 'rate up';
        //     statusText.className = 'pst-status-text up';
        //     statusText.textContent = 'Positive';
        //     trendIcon.src = './style/assets/trending_up_24dp_E8EAED_FILL0_wght400_GRAD0_opsz24.svg';
        // } else {
        //     rateElement.className = 'rate down';
        //     statusText.className = 'pst-status-text down';
        //     statusText.textContent = 'Negative';
        //     trendIcon.src = './style/assets/trending_down_24dp_E8EAED_FILL0_wght400_GRAD0_opsz24.svg';
        // }
        rateElement.className = 'rate up';
        statusText.className = 'pst-status-text up';
        statusText.textContent = 'Positive';
        trendIcon.src = 'style/assets/trending_up_24dp_E8EAED_FILL0_wght400_GRAD0_opsz24.svg';
        
    } catch (error) {
        console.error('Error fetching positive rate:', error);
    }
}

// Update immediately and then every minute
updatePositiveRate();
setInterval(updatePositiveRate, 60000);