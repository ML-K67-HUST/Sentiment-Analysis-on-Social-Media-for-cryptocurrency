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
            ctx.lineWidth = 5;
            ctx.strokeStyle = 'white';
            ctx.stroke();
            ctx.restore();
        }
    }
};

Chart.register(verticalLinePlugin);

async function createChart() {
    try {
        const response = await fetch('http://localhost:8000/chart/');
        const dataChart = await response.json();

        const sortedData = [...dataChart].sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));

        let chartInstance;

        function filterData(selectedValue) {
            const currentDate = new Date(sortedData[sortedData.length - 1].timestamp);
            let startDate;

            switch (selectedValue) {
                case 'option-1': // Last day
                    startDate = new Date(currentDate);
                    startDate.setDate(startDate.getDate() - 1);
                    break;
                case 'option-2': // Three days ago
                    startDate = new Date(currentDate);
                    startDate.setDate(startDate.getDate() - 3);
                    break;
                case 'option-3': // One week ago
                    startDate = new Date(currentDate);
                    startDate.setDate(startDate.getDate() - 7);
                    break;
                case 'option-4': // One month ago
                    startDate = new Date(currentDate);
                    startDate.setMonth(startDate.getMonth() - 1);
                    break;
                default:
                    console.error('Invalid selection');
                    return [];
            }

            return sortedData.filter(entry => new Date(entry.timestamp) >= startDate);
        }

        function updateChart(filteredData) {
            const ctx = document.getElementById('bitcoinChart').getContext('2d');

            const chartData = {
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
                        borderWidth: 3,
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
                        borderWidth: 3,
                    },
                ],
            };

            const chartOptions = {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            boxWidth: 10,
                            boxHeight: 1,
                            padding: 15,
                            font: {
                                size: 24 // Increased legend font size
                            },
                            color: '#adb5bd'
                        },
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                        displayColors: false,
                        titleFont: {
                            size: 20 
                        },
                        bodyFont: {
                            size: 20
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
                        ticks: {
                            autoSkip: false,
                            maxRotation: 0,
                            minRotation: 0,
                            font: {
                                size: 20 // Increased x-axis font size
                            },
                            color: '#adb5bd'
                        },
                    },
                    y: {
                        type: 'linear',
                        position: 'right',
                        ticks: {
                            font: {
                                size: 20 // Increased y-axis font size
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
                        },
                        ticks: {
                            font: {
                                size: 20 // Increased y1-axis font size
                            },
                            color: '#adb5bd',
                            callback: function(value) {
                                return Number(value.toFixed(2)) + '%';
                            },
                        },
                    },
                },
            };

            // If the chart already exists, update it; otherwise, create a new one
            if (chartInstance) {
                chartInstance.data = chartData;
                chartInstance.options = chartOptions;
                chartInstance.update();
            } else {
                chartInstance = new Chart(ctx, {
                    type: 'line',
                    data: chartData,
                    options: chartOptions,
                });
            }
        }

        const initialFilteredData = filterData('option-1');
        updateChart(initialFilteredData);

        document.getElementById('options').addEventListener('change', (event) => {
            const selectedValue = event.target.value;
            const filteredData = filterData(selectedValue);
            updateChart(filteredData);
        });

    } catch (error) {
        console.error('Error loading or processing data:', error);
    }
}

document.addEventListener('DOMContentLoaded', createChart);