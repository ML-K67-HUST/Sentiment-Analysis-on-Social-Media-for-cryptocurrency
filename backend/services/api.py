from fastapi import FastAPI, HTTPException
from typing import Union
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI(title="Coinmarketcap_articles_retrieve")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or ["*"] to allow all
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Allow all headers
)

@app.get("/",)
async def health_check():
    try:
        return {'message':'ok'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@app.get("/x_news/")
async def get_x():
    try:
        return [
            {
                "timestamp": "2 hours ago",
                "title": "X Platform News Example",
                "description": "@userid",
                "link": 'https://www.facebook.com/profile.php?id=100093414754735&mibextid=wwXIfr&rdid=3OxRRw3Ij0tQJJsi&share_url=https%3A%2F%2Fwww.facebook.com%2Fshare%2FjaF8Q932p8hajft7%2F%3Fmibextid%3DwwXIfr',
                "sentiments": [
                    {
                        "type": "Positive",
                        "content": "Positive sentiment from X..."
                    }
                ]
            },
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/cmc_news/")
async def get_cmc():
    try:
        return [
        {
            "timestamp": "1 hours ago",
            "title": "Bitcoin Drops, But Forecasts Predict $118,000 Before 2025",
            "description": "The world of cryptocurrencies is in turmoil...",
            "link": 'https://www.facebook.com/profile.php?id=100093414754735&mibextid=wwXIfr&rdid=3OxRRw3Ij0tQJJsi&share_url=https%3A%2F%2Fwww.facebook.com%2Fshare%2FjaF8Q932p8hajft7%2F%3Fmibextid%3DwwXIfr',
            "sentiments": [
                {
                    "type": "Positive",
                    "content": "the article presents a reasonable and wellsubstantiated case..."
                },
                {
                    "type": "Negative",
                    "content": "the article also presents concerns about..."
                }
            ]
        },
        {
            "timestamp": "1 hours ago",
            "title": "Bitcoin Drops, But Forecasts Predict $118,000 Before 2025",
            "description": "The world of cryptocurrencies is in turmoil...",
            "link": 'https://www.facebook.com/profile.php?id=100093414754735&mibextid=wwXIfr&rdid=3OxRRw3Ij0tQJJsi&share_url=https%3A%2F%2Fwww.facebook.com%2Fshare%2FjaF8Q932p8hajft7%2F%3Fmibextid%3DwwXIfr',
            "sentiments": [
                {
                    "type": "Negative",
                    "content": "the article also presents concerns about..."
                }
            ]
        },
        {
            "timestamp": "1 hours ago",
            "title": "Bitcoin Drops, But Forecasts Predict $118,000 Before 2025",
            "description": "The world of cryptocurrencies is in turmoil...",
            "link": 'https://www.facebook.com/profile.php?id=100093414754735&mibextid=wwXIfr&rdid=3OxRRw3Ij0tQJJsi&share_url=https%3A%2F%2Fwww.facebook.com%2Fshare%2FjaF8Q932p8hajft7%2F%3Fmibextid%3DwwXIfr',
            "sentiments": [
                {
                    "type": "Positive",
                    "content": "the article presents a reasonable and wellsubstantiated case..."
                }
            ]
        },
        {
            "timestamp": "1 hours ago",
            "title": "Bitcoin Drops, But Forecasts Predict $118,000 Before 2025",
            "description": "The world of cryptocurrencies is in turmoil...",
            "link": 'https://www.facebook.com/profile.php?id=100093414754735&mibextid=wwXIfr&rdid=3OxRRw3Ij0tQJJsi&share_url=https%3A%2F%2Fwww.facebook.com%2Fshare%2FjaF8Q932p8hajft7%2F%3Fmibextid%3DwwXIfr',
            "sentiments": [
                {
                    "type": "Positive",
                    "content": "the article presents a reasonable and wellsubstantiated case..."
                },
                {
                    "type": "Negative",
                    "content": "the article also presents concerns about..."
                }
            ]
        },
    ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)