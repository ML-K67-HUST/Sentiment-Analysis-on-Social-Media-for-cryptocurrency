"""
Consumer Monitoring API
Provides real-time stats for LLM and NLP consumers
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from database.mongodb import MongoManager
from datetime import datetime
import time

app = FastAPI(title="Consumer Monitoring API")

mongo = MongoManager('blog-data')


@app.get("/api/consumer-stats")
async def get_consumer_stats():
    """Get stats for all consumers"""
    try:
        metrics = list(mongo.find(
            collection_name='consumer_metrics',
            filter={}
        ))
        
        # Calculate uptime and add human-readable timestamps
        for metric in metrics:
            if metric.get('started_at'):
                uptime_seconds = int(time.time()) - metric['started_at']
                metric['uptime_formatted'] = format_duration(uptime_seconds)
            
            if metric.get('last_processed_at'):
                metric['last_processed_ago'] = format_time_ago(metric['last_processed_at'])
            
            if metric.get('last_error_at'):
                metric['last_error_ago'] = format_time_ago(metric['last_error_at'])
            
            # Calculate success rate
            total = metric['total_processed'] + metric['total_errors']
            if total > 0:
                metric['success_rate'] = round((metric['total_processed'] / total) * 100, 2)
            else:
                metric['success_rate'] = 0
        
        return {
            "status": "success",
            "timestamp": int(time.time()),
            "consumers": metrics
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/data-stats")
async def get_data_stats():
    """Get data statistics from MongoDB"""
    try:
        stats = {
            "cmc_news": mongo.count_documents('cmc_news', {}),
            "cmc_sentiment_data": mongo.count_documents('cmc_sentiment_data', {}),
            "article_features": mongo.count_documents('article_features', {}),
            "aggregated_features_30min": mongo.count_documents('aggregated_features_30min', {}),
        }
        
        # Get latest records
        latest_news = mongo.find_one('cmc_news', filter={}, sort=('crawled_at', -1))
        latest_sentiment = mongo.find_one('cmc_sentiment_data', filter={}, sort=('timestamp', -1))
        latest_nlp = mongo.find_one('article_features', filter={}, sort=('processed_at', -1))
        latest_agg = mongo.find_one('aggregated_features_30min', filter={}, sort=('window_start', -1))
        
        stats['latest'] = {
            'news': latest_news.get('crawled_at') if latest_news else None,
            'sentiment': latest_sentiment.get('timestamp') if latest_sentiment else None,
            'nlp': latest_nlp.get('processed_at') if latest_nlp else None,
            'aggregation': latest_agg.get('window_start') if latest_agg else None
        }
        
        return {
            "status": "success",
            "stats": stats
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """Simple monitoring dashboard"""
    return """
<!DOCTYPE html>
<html>
<head>
    <title>Consumer Monitoring Dashboard</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        
        h1 {
            color: white;
            text-align: center;
            margin-bottom: 30px;
            font-size: 2.5em;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }
        
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .card {
            background: white;
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            transition: transform 0.3s ease;
        }
        
        .card:hover {
            transform: translateY(-5px);
        }
        
        .card h2 {
            color: #667eea;
            margin-bottom: 20px;
            font-size: 1.5em;
            border-bottom: 3px solid #667eea;
            padding-bottom: 10px;
        }
        
        .metric {
            margin: 15px 0;
            padding: 10px;
            background: #f8f9fa;
            border-radius: 8px;
        }
        
        .metric-label {
            font-size: 0.9em;
            color: #6c757d;
            margin-bottom: 5px;
        }
        
        .metric-value {
            font-size: 1.8em;
            font-weight: bold;
            color: #333;
        }
        
        .status {
            display: inline-block;
            padding: 5px 15px;
            border-radius: 20px;
            font-weight: bold;
            font-size: 0.9em;
        }
        
        .status-running {
            background: #d4edda;
            color: #155724;
        }
        
        .status-stopped {
            background: #f8d7da;
            color: #721c24;
        }
        
        .status-error {
            background: #fff3cd;
            color: #856404;
        }
        
        .success-rate {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .progress-bar {
            flex: 1;
            height: 25px;
            background: #e9ecef;
            border-radius: 15px;
            overflow: hidden;
        }
        
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #667eea, #764ba2);
            transition: width 0.5s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
            font-size: 0.9em;
        }
        
        .error-box {
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 15px;
            margin-top: 15px;
            border-radius: 5px;
        }
        
        .error-box strong {
            color: #856404;
        }
        
        .refresh-btn {
            background: white;
            color: #667eea;
            border: none;
            padding: 12px 30px;
            border-radius: 25px;
            font-size: 1em;
            font-weight: bold;
            cursor: pointer;
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
            transition: all 0.3s ease;
            display: block;
            margin: 0 auto;
        }
        
        .refresh-btn:hover {
            transform: scale(1.05);
            box-shadow: 0 8px 20px rgba(0,0,0,0.3);
        }
        
        .timestamp {
            text-align: center;
            color: white;
            margin-top: 20px;
            font-size: 0.9em;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔍 Consumer Monitoring Dashboard</h1>
        
        <div id="consumers" class="grid"></div>
        
        <div class="card">
            <h2>📊 Data Statistics</h2>
            <div id="data-stats"></div>
        </div>
        
        <button class="refresh-btn" onclick="loadData()">🔄 Refresh</button>
        <p class="timestamp" id="last-update"></p>
    </div>
    
    <script>
        async function loadData() {
            try {
                // Load consumer stats
                const consumerRes = await fetch('/api/consumer-stats');
                const consumerData = await consumerRes.json();
                
                const consumersDiv = document.getElementById('consumers');
                consumersDiv.innerHTML = '';
                
                consumerData.consumers.forEach(consumer => {
                    const statusClass = `status-${consumer.status}`;
                    
                    consumersDiv.innerHTML += `
                        <div class="card">
                            <h2>${consumer.consumer_name}</h2>
                            <div class="metric">
                                <div class="metric-label">Status</div>
                                <span class="status ${statusClass}">${consumer.status.toUpperCase()}</span>
                            </div>
                            <div class="metric">
                                <div class="metric-label">Total Processed</div>
                                <div class="metric-value">${consumer.total_processed.toLocaleString()}</div>
                            </div>
                            <div class="metric">
                                <div class="metric-label">Total Errors</div>
                                <div class="metric-value" style="color: ${consumer.total_errors > 0 ? '#dc3545' : '#28a745'}">${consumer.total_errors.toLocaleString()}</div>
                            </div>
                            <div class="metric">
                                <div class="metric-label">Success Rate</div>
                                <div class="success-rate">
                                    <div class="progress-bar">
                                        <div class="progress-fill" style="width: ${consumer.success_rate}%">
                                            ${consumer.success_rate}%
                                        </div>
                                    </div>
                                </div>
                            </div>
                            ${consumer.uptime_formatted ? `
                            <div class="metric">
                                <div class="metric-label">Uptime</div>
                                <div style="font-size: 1.2em; color: #667eea; font-weight: bold;">${consumer.uptime_formatted}</div>
                            </div>
                            ` : ''}
                            ${consumer.last_processed_ago ? `
                            <div class="metric">
                                <div class="metric-label">Last Processed</div>
                                <div style="font-size: 1.1em; color: #6c757d;">${consumer.last_processed_ago}</div>
                            </div>
                            ` : ''}
                            ${consumer.last_error_message ? `
                            <div class="error-box">
                                <strong>Last Error:</strong><br>
                                ${consumer.last_error_message}
                            </div>
                            ` : ''}
                        </div>
                    `;
                });
                
                // Load data stats
                const dataRes = await fetch('/api/data-stats');
                const dataStats = await dataRes.json();
                
                const dataStatsDiv = document.getElementById('data-stats');
                dataStatsDiv.innerHTML = `
                    <div class="metric">
                        <div class="metric-label">News Articles</div>
                        <div class="metric-value">${dataStats.stats.cmc_news.toLocaleString()}</div>
                    </div>
                    <div class="metric">
                        <div class="metric-label">LLM Sentiments</div>
                        <div class="metric-value">${dataStats.stats.cmc_sentiment_data.toLocaleString()}</div>
                    </div>
                    <div class="metric">
                        <div class="metric-label">NLP Features</div>
                        <div class="metric-value">${dataStats.stats.article_features.toLocaleString()}</div>
                    </div>
                    <div class="metric">
                        <div class="metric-label">Aggregated (30min)</div>
                        <div class="metric-value">${dataStats.stats.aggregated_features_30min.toLocaleString()}</div>
                    </div>
                `;
                
                document.getElementById('last-update').textContent = 
                    `Last updated: ${new Date().toLocaleString()}`;
                    
            } catch (error) {
                console.error('Error loading data:', error);
                alert('Failed to load data: ' + error.message);
            }
        }
        
        // Load data on page load
        loadData();
        
        // Auto-refresh every 10 seconds
        setInterval(loadData, 10000);
    </script>
</body>
</html>
    """


def format_duration(seconds):
    """Format seconds into human-readable duration"""
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        return f"{seconds // 60}m {seconds % 60}s"
    elif seconds < 86400:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}h {minutes}m"
    else:
        days = seconds // 86400
        hours = (seconds % 86400) // 3600
        return f"{days}d {hours}h"


def format_time_ago(timestamp):
    """Format timestamp as 'X ago'"""
    now = int(time.time())
    diff = now - timestamp
    
    if diff < 60:
        return f"{diff}s ago"
    elif diff < 3600:
        return f"{diff // 60}m ago"
    elif diff < 86400:
        return f"{diff // 3600}h ago"
    else:
        return f"{diff // 86400}d ago"


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
