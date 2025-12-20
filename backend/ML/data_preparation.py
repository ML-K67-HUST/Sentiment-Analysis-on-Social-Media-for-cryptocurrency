"""
Data Preparation for ML Models
Load labeled sentiment data from MongoDB and prepare for training
"""
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from database.mongodb import MongoManager


def load_labeled_data(collection_name='cmc_news', limit=None):
    """
    Load labeled sentiment data from MongoDB
    
    Args:
        collection_name: MongoDB collection name
        limit: Maximum number of documents to load
        
    Returns:
        DataFrame with text and sentiment labels
    """
    print(f"\n📊 Loading labeled data from MongoDB...")
    
    mongo = MongoManager('blog-data')
    
    # Query only documents with sentiment labels
    filter_query = {
        'sentiment': {'$exists': True, '$ne': None}
    }
    
    # Load data
    articles = list(mongo.find(
        collection_name=collection_name,
        filter=filter_query,
        limit=limit if limit else 10000
    ))
    
    print(f"   ✅ Loaded {len(articles)} labeled articles")
    
    if len(articles) == 0:
        raise ValueError("No labeled data found! Please label some data first.")
    
    # Create DataFrame
    data = []
    for article in articles:
        # Combine title and content for full text
        title = article.get('title', '')
        content = article.get('content', '')
        text = f"{title}. {content}"
        
        sentiment = article.get('sentiment', 'neutral')
        
        data.append({
            'text': text,
            'sentiment': sentiment,
            'title': title,
            'timestamp': article.get('timestamp', 0)
        })
    
    df = pd.DataFrame(data)
    
    # Show distribution
    print(f"\n📊 Sentiment Distribution:")
    sentiment_counts = df['sentiment'].value_counts()
    for sentiment, count in sentiment_counts.items():
        percentage = (count / len(df)) * 100
        print(f"   {sentiment.capitalize()}: {count} ({percentage:.1f}%)")
    
    return df


def prepare_train_test_split(df, test_size=0.3, random_state=42):
    """
    Split data into train and test sets with stratification
    
    Args:
        df: DataFrame with 'text' and 'sentiment' columns
        test_size: Proportion of test set (default: 0.3)
        random_state: Random seed for reproducibility
        
    Returns:
        X_train, X_test, y_train, y_test
    """
    print(f"\n🔀 Splitting data: {int((1-test_size)*100)}% train, {int(test_size*100)}% test...")
    
    X = df['text'].values
    y = df['sentiment'].values
    
    # Stratified split to maintain class distribution
    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=test_size,
        random_state=random_state,
        stratify=y  # Important for imbalanced data
    )
    
    print(f"   Training set: {len(X_train)} samples")
    print(f"   Test set: {len(X_test)} samples")
    
    return X_train, X_test, y_train, y_test


def get_class_weights(y):
    """
    Calculate class weights for imbalanced data
    
    Args:
        y: Array of labels
        
    Returns:
        Dictionary of class weights
    """
    from sklearn.utils.class_weight import compute_class_weight
    
    classes = np.unique(y)
    class_weights = compute_class_weight(
        class_weight='balanced',
        classes=classes,
        y=y
    )
    
    class_weight_dict = dict(zip(classes, class_weights))
    
    print(f"\n⚖️  Class Weights (to handle imbalance):")
    for label, weight in class_weight_dict.items():
        print(f"   {label}: {weight:.2f}")
    
    return class_weight_dict


if __name__ == "__main__":
    # Test data loading
    df = load_labeled_data()
    print(f"\n✅ Data loaded successfully!")
    print(f"\nSample text:")
    print(df['text'].iloc[0][:200] + "...")
    
    # Test split
    X_train, X_test, y_train, y_test = prepare_train_test_split(df)
    print(f"\n✅ Data split successfully!")
    
    # Calculate class weights
    class_weights = get_class_weights(y_train)

