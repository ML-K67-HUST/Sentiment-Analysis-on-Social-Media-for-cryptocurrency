from fastapi import FastAPI, HTTPException
from typing import Union
from fastapi.middleware.cors import CORSMiddleware
from .cmc_api import get_cmc_news
from .twitter_api import get_tweet_news
from .chart_api import get_chart_data
from database.mongodb import MongoManager

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
    try:
        # return [
        #     {
        #         "timestamp": "2 hours ago",
        #         "title": "X Platform News Example",
        #         "description": "@userid",
        #         "link": 'https://www.facebook.com/profile.php?id=100093414754735&mibextid=wwXIfr&rdid=3OxRRw3Ij0tQJJsi&share_url=https%3A%2F%2Fwww.facebook.com%2Fshare%2FjaF8Q932p8hajft7%2F%3Fmibextid%3DwwXIfr',
        #         "sentiments": [
        #             {
        #                 "type": "Positive",
        #                 "content": "Positive sentiment from X..."
        #             }
        #         ]
        #     },
        # ]
        return get_tweet_news()
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)