from fastapi import FastAPI, HTTPException
from typing import Union
from fastapi.middleware.cors import CORSMiddleware
from .cmc_api import get_cmc_news
from .twitter_api import get_tweet_news
from .tradingview_api import get_tradingview_ideas
from .chart_api import get_chart_data
from database.mongodb import MongoManager
import httpx
import time
from datetime import datetime, timedelta
from cachetools import TTLCache
import asyncio

app = FastAPI(title="Coinmarketcap_articles_retrieve")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or ["*"] to allow all
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Allow all headers
)

# --- Caching Setup ---
# Cache for 60 seconds, max 100 items
cache = TTLCache(maxsize=100, ttl=60)

# --- Database Connection Reuse ---
mongo_manager = None

def get_db():
    global mongo_manager
    if mongo_manager is None:
        mongo_manager = MongoManager('blog-data')
    return mongo_manager

@app.on_event("startup")
async def startup_event():
    get_db()

@app.get("/",)
async def health_check():
    try:
        return {'message':'ok'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@app.get("/x_news/")
async def get_x():
    """
    DEPRECATED: Use /tradingview_ideas/ instead.
    """
    return await get_tradingview()


@app.get("/tradingview_ideas/")
async def get_tradingview():
    """
    Get TradingView cryptocurrency trading ideas with caching.
    """
    cache_key = "tradingview_ideas"
    if cache_key in cache:
        return cache[cache_key]
        
    try:
        # Run synchronous function in thread pool
        data = await asyncio.to_thread(get_tradingview_ideas)
        cache[cache_key] = data
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/cmc_news/")
async def get_cmc():
    """
    Get CMC news with caching.
    """
    cache_key = "cmc_news"
    if cache_key in cache:
        return cache[cache_key]

    try:
        data = await asyncio.to_thread(get_cmc_news)
        cache[cache_key] = data
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/chart/")
async def get_chart():
    """
    Get Chart data with caching.
    """
    cache_key = "chart_data"
    if cache_key in cache:
        return cache[cache_key]

    try:
        data = await asyncio.to_thread(get_chart_data)
        cache[cache_key] = data
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ml_predict/")
async def get_ml_prediction():
    """
    Get ML prediction based on latest 30-min aggregated features
    
    Returns:
        prediction: Price movement prediction (percentage)
        window_info: Information about the aggregation window
        num_articles: Number of articles in the window
        llm_sentiment: Aggregated LLM sentiment
        timestamp: Current timestamp
    """
    try:
        # Reuse connection
        mongo_client = get_db()
        
        # Get latest 10-min aggregation 
        latest_aggregation = mongo_client.find_one(
            collection_name='aggregated_features_10min',
            filter={'aggregation_status': 'complete'},
            sort=("window_start", -1)
        )
        
        if not latest_aggregation:
            raise HTTPException(
                status_code=404, 
                detail="No aggregated data available. Please wait for initial data collection."
            )
        
        # Extract features from aggregation
        nlp_agg = latest_aggregation.get('nlp_features_agg', {})
        
        # Prepare input for ML API (17 features)
        ml_input = {
            "num_articles": latest_aggregation.get('num_articles', 0),
            "llm_sentiment_avg": latest_aggregation.get('llm_sentiment_avg', 0.0),
            "llm_confidence_avg": latest_aggregation.get('llm_confidence_avg', 0.0),
            # NLP features
            "avg_positive_word_ratio": nlp_agg.get('avg_positive_word_ratio', 0.0),
            "avg_negative_word_ratio": nlp_agg.get('avg_negative_word_ratio', 0.0),
            "avg_neutral_word_ratio": nlp_agg.get('avg_neutral_word_ratio', 0.0),
            "avg_compound_score": nlp_agg.get('avg_compound_score', 0.0),
            "total_avg_sentence_length": nlp_agg.get('total_avg_sentence_length', 0.0),
            "total_word_count": nlp_agg.get('total_word_count', 0),
            "avg_unique_word_ratio": nlp_agg.get('avg_unique_word_ratio', 0.0),
            "total_exclamation_count": nlp_agg.get('total_exclamation_count', 0),
            "total_question_count": nlp_agg.get('total_question_count', 0),
            "total_btc_mention_count": nlp_agg.get('total_btc_mention_count', 0),
            "total_price_keyword_count": nlp_agg.get('total_price_keyword_count', 0),
            "avg_technical_term_ratio": nlp_agg.get('avg_technical_term_ratio', 0.0),
            "total_ne_person_count": nlp_agg.get('total_ne_person_count', 0),
            "total_ne_org_count": nlp_agg.get('total_ne_org_count', 0)
        }
        
        # Call ML API
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    "http://backend-ml-api:8002/predict",
                    json=ml_input
                )
            except httpx.ConnectError:
                # Fallback to localhost for local development
                print("⚠️ Cloud not connect to backend-ml-api, trying localhost...")
                response = await client.post(
                    "http://localhost:8002/predict",
                    json=ml_input
                )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"ML API error: {response.text}"
                )
            
            ml_result = response.json()
            prediction = ml_result.get('prediction', 0)
            
            return {
                "prediction": float(prediction) * 100,  # Convert to percentage
                "window_info": {
                    "start": latest_aggregation.get('window_datetime'),
                    "num_articles": latest_aggregation.get('num_articles', 0),
                    "llm_sentiment": latest_aggregation.get('llm_sentiment_avg', 0.0),
                    "llm_confidence": latest_aggregation.get('llm_confidence_avg', 0.0)
                },
                "timestamp": int(time.time()),
                "model_type": "10min_aggregated",
                "last_train_time": ml_result.get('last_train_time')
            }
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)