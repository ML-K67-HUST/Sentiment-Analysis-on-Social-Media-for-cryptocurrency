import {Line} from 'react-chartjs-2'
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend,
    TimeScale,
} from 'chart.js'
import 'chartjs-adapter-date-fns';
import dataChart from '../assets/data_chart.json'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, TimeScale, {
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
    },
});

export const LineGraph = () => {

    const sortedData = [...dataChart].sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));

    // Determine the date 3 days ago from the latest timestamp
    const latestTimestamp = new Date(sortedData[sortedData.length - 1].timestamp);
    const threeDaysAgo = new Date(latestTimestamp);
    threeDaysAgo.setDate(threeDaysAgo.getDate() - 3);

    // Filter the data to include only the last 3 days
    const filteredData = sortedData.filter(entry => new Date(entry.timestamp) >= threeDaysAgo);

    const data = {
        datasets: [
            {
                label: 'Bitcoin Price',
                data: filteredData.map(entry => ({ 
                    x: entry.timestamp, 
                    y: Math.round(entry.price * 100) / 100 
                })),
                borderColor: 'rgb(255, 0, 0)',
                backgroundColor: 'rgba(75, 192, 192, 0.2)',
                fill: false,
                yAxisID: 'y',
                pointRadius: 0,
                borderWidth: 1, // Reduced line thickness
            },
            {
                label: 'Bitcoin Index Score',
                data: filteredData.map(entry => ({ 
                    x: entry.timestamp, 
                    y: Math.round(entry.bitcoin_index_score * 10000) / 100 
                })),
                borderColor: 'rgb(0, 255, 200)',
                backgroundColor: 'rgba(153, 102, 255, 0.2)',
                fill: false,
                yAxisID: 'y1',
                pointRadius: 0,
                borderWidth: 1, // Reduced line thickness
            },
        ],
    }

    const options = {
        responsive: true,
        plugins: {
            legend: {
                position: 'bottom',
                labels: {
                    boxWidth: 10, // Reduced box width
                    boxHeight: 1, // Reduced box height
                    padding: 15, // Optional: Adjust padding as needed
                }, 
            },
            title: {
                display: false,
                text: 'Bitcoin Price and Index Score Over Time',
            },
            tooltip: {
                mode: 'index',
                intersect: false,
                displayColors: false, // Disable color boxes in tooltips
                callbacks: {
                    label: function(context) {
                        let label = context.dataset.label || '';
                        if (label) {
                            label += ': ';
                        }
                        if (context.parsed.y !== null) {
                            let formattedValue = '';
                            if (label.includes('Price')) {
                                formattedValue = Number((context.parsed.y / 1000).toFixed(2)) + 'k USD';
                            } else if (label.includes('Score')) {
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
                title: {
                    display: false,
                    text: 'Date',
                },
                ticks: {
                    autoSkip: false,
                    maxRotation: 0,
                    minRotation: 0,
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
                    callback: function(value) {
                        return Number(value.toFixed(2)) + '%';
                    },
                },
            },
        },
    }

    return <Line width={1000} height={400} options={options} data={data}></Line>
}







