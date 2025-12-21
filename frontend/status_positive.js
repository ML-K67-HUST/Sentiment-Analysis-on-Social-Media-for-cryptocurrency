// Mock function to simulate getting data from an API
// Replace this with your actual data fetching logic
async function fetchPositiveRate() {
    try {
        const response = await fetch('http://localhost:8000/chart/');
        const dataChart = await response.json();

        // Filter valid scores
        const validData = dataChart.filter(item =>
            item.bitcoin_index_score !== null &&
            item.bitcoin_index_score !== undefined
        );

        if (validData.length === 0) {
            return { rate: 50.0, trend: true };
        }

        // Get last 6 elements (1 hour window)
        const lastElements = validData.slice(-6);

        // Calculate average
        const sum = lastElements.reduce((acc, curr) => acc + curr.bitcoin_index_score, 0);
        const avg = sum / lastElements.length;

        return {
            rate: avg,
            trend: avg >= 50
        };
    } catch (e) {
        console.error("Error calculating rate:", e);
        return { rate: 50.0, trend: true };
    }
}

async function updatePositiveRate() {
    try {
        const data = await fetchPositiveRate();

        const rateElement = document.querySelector('.rate');
        const statusText = document.querySelector('.pst-status-text');
        const trendIcon = document.querySelector('.trend');

        // Update rate
        rateElement.textContent = `${data.rate.toFixed(2)}%`;

        // Update trend and colors dynamically
        if (data.trend) {
            rateElement.className = 'rate up';
            statusText.className = 'pst-status-text up';
            statusText.textContent = 'Positive';
            trendIcon.src = 'style/assets/trending_up_24dp_E8EAED_FILL0_wght400_GRAD0_opsz24.svg';
        } else {
            rateElement.className = 'rate down';
            statusText.className = 'pst-status-text down';
            statusText.textContent = 'Negative';
            trendIcon.src = 'style/assets/trending_down_24dp_E8EAED_FILL0_wght400_GRAD0_opsz24.svg';
        }

    } catch (error) {
        console.error('Error fetching positive rate:', error);
    }
}

// Update immediately and then every minute
updatePositiveRate();
setInterval(updatePositiveRate, 60000);