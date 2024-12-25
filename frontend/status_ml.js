async function fetchMLPrediction() {
    try {
        const response = await fetch("http://localhost:8002/predict", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            redirect: "follow"
        });

        if (!response.ok) {
            throw new Error(`Error: ${response.status} - ${response.statusText}`);
        }
        
        const data = await response.json();
        console.log('Fetched prediction : ', data.prediction)
        return data.prediction; 
    } catch (error) {
        console.error("Failed to fetch prediction:", error);
        throw error;
    }
}

async function updateMLPrediction() {
    try {
        console.log("Trying to get ML PREDICTION");
        const data = await fetchMLPrediction();
        console.log("Fetched prediction");
        const predictElement = document.querySelector('.predict');
        
        predictElement.textContent = `${data.toFixed(2)}%`;
        
        if (data > 0) {
            predictElement.className = 'predict up';
        } else {
            predictElement.className = 'predict down';
        }

    } catch (error) {
        console.error('Error fetching positive rate:', error);
    }
}
updateMLPrediction()