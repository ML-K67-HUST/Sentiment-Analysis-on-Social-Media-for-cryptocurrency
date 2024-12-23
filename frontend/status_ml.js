async function fetchMLPrediction() {
    
}

async function updateMLPrediction() {
    try {
        const data = await fetchMLPrediction();
        
        const predictElement = document.querySelector('.predict');
        
        predictElement.textContent = `${data.rate.toFixed(2)}%`;
        
        predictElement.className = 'predict up';

    } catch (error) {
        console.error('Error fetching positive rate:', error);
    }
}