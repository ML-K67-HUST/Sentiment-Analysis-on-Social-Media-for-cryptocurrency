import re
import string
from sklearn.feature_extraction.text import TfidfVectorizer
import nltk

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords', quiet=True)

from nltk.corpus import stopwords


class TextPreprocessor:
    """Text preprocessing for crypto sentiment analysis"""
    
    def __init__(self):
        self.stop_words = set(stopwords.words('english'))
        
        # Keep some sentiment-bearing words that are usually stopwords
        sentiment_words = {'not', 'no', 'nor', 'very', 'more', 'most', 'up', 'down'}
        self.stop_words = self.stop_words - sentiment_words
        
        # Add crypto-specific stopwords
        crypto_stopwords = {'crypto', 'cryptocurrency', 'coin', 'token'}
        # Don't add crypto stopwords as they might be informative
    
    def clean_text(self, text):
        """
        Clean and normalize text
        
        Args:
            text: Raw text string
            
        Returns:
            Cleaned text
        """
        if not isinstance(text, str):
            return ""
        
        # Lowercase
        text = text.lower()
        
        # Remove URLs
        text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
        
        # Remove HTML tags
        text = re.sub(r'<.*?>', '', text)
        
        # Keep important punctuation (! and ?)
        # Remove other punctuation except those
        text = re.sub(r'[^\w\s!?$%+-]', ' ', text)
        
        # Handle multiple spaces
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def preprocess(self, text):
        """
        Full preprocessing pipeline
        
        Args:
            text: Raw text
            
        Returns:
            Preprocessed text ready for TF-IDF
        """
        text = self.clean_text(text)
        
        # Tokenize and remove stopwords
        words = text.split()
        words = [w for w in words if w not in self.stop_words and len(w) > 2]
        
        return ' '.join(words)


class FeatureExtractor:
    """TF-IDF feature extraction"""
    
    def __init__(self, max_features=5000, ngram_range=(1, 2)):
        """
        Initialize TF-IDF vectorizer
        
        Args:
            max_features: Maximum number of features (default: 5000)
            ngram_range: N-gram range, e.g., (1,2) for unigram+bigram
        """
        self.preprocessor = TextPreprocessor()
        
        self.vectorizer = TfidfVectorizer(
            max_features=max_features,
            ngram_range=ngram_range,
            min_df=2,  # Ignore terms that appear in less than 2 documents
            max_df=0.8,  # Ignore terms that appear in more than 80% of documents
            sublinear_tf=True,  # Apply sublinear tf scaling (1 + log(tf))
            preprocessor=self.preprocessor.preprocess,
            strip_accents='unicode',
            analyzer='word',
            token_pattern=r'\w{2,}',  # Words with at least 2 characters
            use_idf=True,
            smooth_idf=True,
            norm='l2'  # L2 normalization
        )
        
        print(f"📊 TF-IDF Vectorizer initialized:")
        print(f"   Max features: {max_features}")
        print(f"   N-gram range: {ngram_range}")
        print(f"   Min document frequency: 2")
        print(f"   Max document frequency: 0.8")
    
    def fit_transform(self, texts):
        """
        Fit vectorizer and transform texts
        
        Args:
            texts: List or array of text strings
            
        Returns:
            Sparse matrix of TF-IDF features
        """
        print(f"\n🔧 Fitting TF-IDF vectorizer on {len(texts)} documents...")
        X = self.vectorizer.fit_transform(texts)
        
        print(f"   ✅ Feature matrix shape: {X.shape}")
        print(f"   (samples, features): ({X.shape[0]}, {X.shape[1]})")
        
        return X
    
    def transform(self, texts):
        """
        Transform texts using fitted vectorizer
        
        Args:
            texts: List or array of text strings
            
        Returns:
            Sparse matrix of TF-IDF features
        """
        return self.vectorizer.transform(texts)
    
    def get_feature_names(self):
        """Get feature names (vocabulary)"""
        return self.vectorizer.get_feature_names_out()
    
    def get_top_features_by_class(self, X, y, top_n=10):
        """
        Get top TF-IDF features for each class
        
        Args:
            X: Feature matrix
            y: Labels
            top_n: Number of top features to return
            
        Returns:
            Dictionary of {class: top_features}
        """
        import numpy as np
        
        feature_names = self.get_feature_names()
        classes = np.unique(y)
        
        top_features = {}
        
        for cls in classes:
            # Get average TF-IDF score for this class
            cls_mask = (y == cls)
            cls_features = X[cls_mask].mean(axis=0).A1  # Convert to 1D array
            
            # Get top N features
            top_indices = cls_features.argsort()[-top_n:][::-1]
            top_words = [(feature_names[i], cls_features[i]) for i in top_indices]
            
            top_features[cls] = top_words
        
        return top_features


if __name__ == "__main__":
    # Test preprocessing
    preprocessor = TextPreprocessor()
    
    sample_text = """
    Bitcoin Surges to New All-Time High! 🚀 
    The crypto market is celebrating as BTC breaks records. 
    Check out https://example.com for more info.
    """
    
    print("Original text:")
    print(sample_text)
    print("\nPreprocessed text:")
    print(preprocessor.preprocess(sample_text))
    
    # Test feature extraction
    texts = [
        "Bitcoin price is rising rapidly! Great news for crypto investors.",
        "Market crash: Bitcoin drops below $50,000. Panic selling continues.",
        "Ethereum network upgrade scheduled for next month. Neutral market sentiment."
    ]
    
    extractor = FeatureExtractor(max_features=100)
    X = extractor.fit_transform(texts)
    
    print(f"\n✅ Feature extraction test passed!")
    print(f"Feature matrix shape: {X.shape}")

