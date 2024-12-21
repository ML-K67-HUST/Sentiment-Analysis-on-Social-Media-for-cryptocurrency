import json
from kafka import KafkaConsumer, KafkaProducer
from database.mongodb import MongoManager
from bson.objectid import ObjectId
from LLM.sentiment_agent import infer_policy, infer_sentiment
from data_constructor import construct_unlabeled_dataset
# from database.mongodb import MongoClient
# from data_constructor import construct_unlabeled_dataset
# from LLM.sentiment_agent import infer_sentiment

# mongo_client = MongoClient('blog-data')

kafka_server = ["kafka:9092"]

topic = "coinmarketcap-news"

mongo_client = MongoManager('blog-data')

consumer = KafkaConsumer(
    bootstrap_servers=kafka_server,
    value_deserializer=json.loads,
    auto_offset_reset="latest",
)

consumer.subscribe(topic)

while True:
    data = next(consumer)
    # blog_data = mongo_client.find(data)
    
    # print(data)
    print("NEW ARTICLES FOUND:\n")
    print(data.value)
    
    articles = data.value["hash_ids"]
    for article in articles:
        print(article)
        record = mongo_client.find_one(
            collection_name='cmc_news',
            filter={
                "hash_id":article,
                "symbol":"BTC"
            }
        )
        if not record:
            continue
        print("Query result from db:\n")
        # idd = str(record['_id'])
        title = record['title']
        url = record['url']
        symbol = record['symbol']
        content = record['content']
        timestamp = record['timestamp']
        hash_id = record['hash_id']
        category = record['category']
        
        btc_sentiment = {}
        infered_policy = infer_policy(content)
        if not infered_policy:
            continue
        print('INFERED_POLICY:\n')
        print(infered_policy)
        for policy in infered_policy["metrics"]:
            btc_sentiment[policy['policy']] = {
                "reasoning": policy['reasoning'],
                "result": policy["classification"]
            }
                
        
        
        data_to_store = {
            # "_id" : idd,
            "btc_sentiment" : btc_sentiment,
            "timestamp":timestamp,
            "hash_id":hash_id,
            "source":"cmc_news",
            "symbol":symbol,
            "source_data": [
                {
                # "_id":idd,
                "title":title,
                "url":url,
                "symbol":symbol,
                "content":content,
                "timestamp":timestamp,
                "hash_id":hash_id,
                "category":category
                }
            ]
        }
        
        mongo_client.insert_one(collection_name='cmc_sentiment_data',data=data_to_store)
        print("STORED SENTIMENT DATA:\n")
        print(data_to_store)
        sentiment_score = infer_sentiment(infered_policy)
        unlabeled_data = construct_unlabeled_dataset(sentiment_score)
        
        mongo_client.insert_one(collection_name='cmc_unlabeled_data',data=unlabeled_data)
        print("STORED UNLABELED DATA:\n")
        print(unlabeled_data)
    # print(type(data))
    
    
