const verticalLinePlugin = {
    id: 'verticalLinePlugin',
    afterDraw: (chart) => {
        if (chart.tooltip && chart.tooltip._active && chart.tooltip._active.length) {
            const ctx = chart.ctx;
            const activePoint = chart.tooltip._active[0];
            ctx.save();
            ctx.beginPath();
            ctx.moveTo(activePoint.element.x, chart.chartArea.top);
            ctx.lineTo(activePoint.element.x, chart.chartArea.bottom);
            ctx.lineWidth = 1; // Make the line thinner/subtle
            ctx.strokeStyle = '#adb5bd'; // Use a gray color instead of white for better aesthetics
            ctx.setLineDash([5, 5]); // Dashed line for better style
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

            // Determine appropriate time unit based on data range
            // Determine appropriate time unit based on selected option
            let timeUnit = 'day';
            let displayFormat = 'MMM dd';

            // Get selected option directly from DOM or passed argument
            // But here we rely on the filteredData scope. 
            // Better to rely on the 'time span' of data.
            const startTime = new Date(filteredData[0].timestamp).getTime();
            const endTime = new Date(filteredData[filteredData.length - 1].timestamp).getTime();
            const durationHours = (endTime - startTime) / (1000 * 60 * 60);

            if (durationHours <= 24.5) { // Last Data (allow some buffer)
                timeUnit = 'hour';
                displayFormat = 'MMM dd HH:mm';
            } else {
                timeUnit = 'day';
                displayFormat = 'MMM dd';
            }

            const chartData = {
                datasets: [
                    {
                        label: 'BTC price',
                        data: filteredData.map(entry => ({
                            x: entry.timestamp,
                            y: entry.price ? Math.round(entry.price * 100) / 100 : null
                        })),
                        borderColor: 'rgb(255, 0, 0)',
                        backgroundColor: 'rgba(75, 192, 192, 0.2)',
                        fill: false,
                        yAxisID: 'y',
                        pointRadius: 0,
                        borderWidth: 3,
                        spanGaps: true
                    },
                    {
                        label: 'Positive rate',
                        data: filteredData.map(entry => {
                            let val = entry.bitcoin_index_score;
                            // Safety clamp: ensure value is within 0-100 range
                            if (val !== null) {
                                if (val > 100) val = 100;
                                if (val < 0) val = 0;
                            }
                            return {
                                x: entry.timestamp,
                                y: val !== null ? Math.round(val * 100) / 100 : null
                            }
                        }),
                        borderColor: 'rgb(0, 255, 200)',
                        backgroundColor: 'rgba(153, 102, 255, 0.2)',
                        fill: false,
                        yAxisID: 'y1',
                        pointRadius: 0,
                        borderWidth: 3,
                        spanGaps: false
                    },
                ],
            };

            const chartOptions = {
                responsive: true,
                maintainAspectRatio: false, // Allow chart to fill container
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            boxWidth: 10,
                            boxHeight: 1,
                            padding: 15,
                            font: {
                                size: 14 // Decreased font size for better fit
                            },
                            color: '#adb5bd'
                        },
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                        displayColors: false,
                        titleFont: {
                            size: 14
                        },
                        bodyFont: {
                            size: 14
                        },
                        callbacks: {
                            label: function (context) {
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
                            unit: timeUnit,
                            tooltipFormat: 'MMM dd, yyyy HH:mm',
                            displayFormats: {
                                hour: 'MMM dd HH:mm',
                                day: 'MMM dd',
                                week: 'MMM dd',
                                month: 'MMM yyyy'
                            },
                        },
                        grid: {
                            display: false,
                        },
                        ticks: {
                            autoSkip: true,  // Auto-adjust labels based on available space
                            maxTicksLimit: 8,  // Limit number of ticks for readability
                            maxRotation: 0,
                            minRotation: 0,
                            font: {
                                size: 12
                            },
                            color: '#adb5bd'
                        },
                    },
                    y: {
                        type: 'linear',
                        position: 'right',
                        ticks: {
                            font: {
                                size: 12 // Reduced font size
                            },
                            color: '#adb5bd',
                            callback: function (value) {
                                return Number((value / 1000).toFixed(2)) + 'k';
                            },
                        },
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        min: 0,   // Explicitly set min
                        max: 100, // Explicitly set max
                        grid: {
                            drawOnChartArea: false,
                        },
                        ticks: {
                            font: {
                                size: 12 // Reduced font size
                            },
                            color: '#adb5bd',
                            callback: function (value) {
                                return Number(value.toFixed(0)) + '%';
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