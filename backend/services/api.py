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

app = FastAPI(title="Coinmarketcap_articles_retrieve")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or ["*"] to allow all
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Allow all headers
)

mongo_client = MongoManager('blog-data')


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
    Kept for backwards compatibility.
    """
    try:
        # Redirect to TradingView ideas
        return get_tradingview_ideas()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/tradingview_ideas/")
async def get_tradingview():
    """
    Get TradingView cryptocurrency trading ideas.
    Replaces Twitter/X data source with TradingView analysis.
    """
    try:
        return get_tradingview_ideas()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/cmc_news/")
async def get_cmc():
    try:
        return get_cmc_news()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/chart/")
async def get_chart():
    try:
        return get_chart_data()
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
        mongo_client = MongoManager('blog-data')
        
        # Get latest 30-min aggregation 
        latest_aggregation = mongo_client.find_one(
            collection_name='aggregated_features_30min',
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
            response = await client.post(
                "http://backend-ml-api:8002/predict",
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
                "model_type": "30min_aggregated"
            }
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)