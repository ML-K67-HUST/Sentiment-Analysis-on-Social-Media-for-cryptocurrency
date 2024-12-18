const verticalLinePlugin = {
    id: 'verticalLinePlugin',
    afterDraw: (chart) => {
        if (chart.tooltip._active && chart.tooltip._active.length) {
            const ctx = chart.ctx;
            const activePoint = chart.tooltip._active[0];
            ctx.save();
            ctx.beginPath();
            ctx.moveTo(activePoint.element.x, chart.chartArea.top);
            ctx.lineTo(activePoint.element.x, chart.chartArea.bottom);
            ctx.lineWidth = 2;
            ctx.strokeStyle = 'white';
            ctx.stroke();
            ctx.restore();
        }
    }
};

Chart.register(verticalLinePlugin);

// Fetch and process data
async function createChart() {
    try {
        const response = await fetch('data_chart.json');
        const dataChart = await response.json();

        const sortedData = [...dataChart].sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));
        
        const latestTimestamp = new Date(sortedData[sortedData.length - 1].timestamp);
        const threeDaysAgo = new Date(latestTimestamp);
        threeDaysAgo.setDate(threeDaysAgo.getDate() - 3);
        
        const filteredData = sortedData.filter(entry => new Date(entry.timestamp) >= threeDaysAgo);

        const ctx = document.getElementById('bitcoinChart');
        
        new Chart(ctx, {
            type: 'line',
            data: {
                datasets: [
                    {
                        label: 'BTC price',
                        data: filteredData.map(entry => ({ 
                            x: entry.timestamp, 
                            y: Math.round(entry.price * 100) / 100 
                        })),
                        borderColor: 'rgb(255, 0, 0)',
                        backgroundColor: 'rgba(75, 192, 192, 0.2)',
                        fill: false,
                        yAxisID: 'y',
                        pointRadius: 0,
                        borderWidth: 1,
                    },
                    {
                        label: 'Positive rate',
                        data: filteredData.map(entry => ({ 
                            x: entry.timestamp, 
                            y: Math.round(entry.bitcoin_index_score * 10000) / 100 
                        })),
                        borderColor: 'rgb(0, 255, 200)',
                        backgroundColor: 'rgba(153, 102, 255, 0.2)',
                        fill: false,
                        yAxisID: 'y1',
                        pointRadius: 0,
                        borderWidth: 1,
                    },
                ],
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            boxWidth: 10,
                            boxHeight: 1,
                            padding: 15,
                            font: {
                                size: 24  // Increased legend font size
                            },
                            color: '#adb5bd'
                        },
                    },
                    title: {
                        display: false,
                        text: 'Bitcoin Price and Index Score Over Time',
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                        displayColors: false,
                        titleFont: {
                            size: 20  // Increased tooltip title font size
                        },
                        bodyFont: {
                            size: 20  // Increased tooltip body font size
                        },
                        callbacks: {
                            label: function(context) {
                                let label = context.dataset.label || '';
                                if (label) {
                                    label += ': ';
                                }
                                if (context.parsed.y !== null) {
                                    let formattedValue = '';
                                    if (label.includes('price')) {
                                        formattedValue = Number((context.parsed.y / 1000).toFixed(2)) + 'k USD';
                                    } else if (label.includes('rate')) {
                                        formattedValue = Number(context.parsed.y.toFixed(2)) + '%';
                                    }
                                    label += formattedValue;
                                }
                                return label;
                            },
                        },
                    },
                },
                interaction: {
                    mode: 'index',
                    intersect: false,
                },
                scales: {
                    x: {
                        type: 'time',
                        time: {
                            unit: 'day',
                            tooltipFormat: 'MMM dd, yyyy',
                            displayFormats: {
                                day: 'MMM dd',
                            },
                        },
                        grid: {
                            display: false,
                        },
                        title: {
                            display: false,
                            text: 'Date',
                        },
                        ticks: {
                            autoSkip: false,
                            maxRotation: 0,
                            minRotation: 0,
                            font: {
                                size: 20  // Increased x-axis font size
                            },
                            color: '#adb5bd'
                        },
                    },
                    y: {
                        type: 'linear',
                        position: 'right',
                        title: {
                            display: false,
                            text: 'Price (USD)',
                        },
                        grid: {
                            display: false,
                        },
                        ticks: {
                            font: {
                                size: 20  // Increased x-axis font size
                            },
                            color: '#adb5bd',
                            callback: function(value) {
                                return Number((value / 1000).toFixed(2)) + 'k';
                            },
                        },
                    },
                    y1: {
                        type: 'linear',
                        position: 'left',
                        grid: {
                            drawOnChartArea: false,
                            display: false,
                        },
                        title: {
                            display: false,
                            text: 'Index Score (%)',
                        },
                        ticks: {
                            font: {
                                size: 20  // Increased x-axis font size
                            },
                            color: '#adb5bd',
                            callback: function(value) {
                                return Number(value.toFixed(2)) + '%';
                            },
                        },
                    },
                },
            }
        });
    } catch (error) {
        console.error('Error loading or processing data:', error);
    }
}
// Initialize the chart when the page loads
document.addEventListener('DOMContentLoaded', createChart);
