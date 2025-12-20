"""
NLP Feature Extractor - 14 Compact Features
Extract aggregatable NLP features from news articles.
"""

import re
from typing import Dict
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk import ne_chunk, pos_tag

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('tokenizers/punkt_tab')
except LookupError:
    nltk.download('punkt_tab')
    
try:
    nltk.data.find('sentiment/vader_lexicon.zip')
except LookupError:
    nltk.download('vader_lexicon')

try:
    nltk.data.find('taggers/averaged_perceptron_tagger')
except LookupError:
    nltk.download('averaged_perceptron_tagger')

try:
    nltk.data.find('chunkers/maxent_ne_chunker')
except LookupError:
    nltk.download('maxent_ne_chunker')

try:
    nltk.data.find('corpora/words')
except LookupError:
    nltk.download('words')


class NLPFeatureExtractor:
    """Extract 14 compact NLP features from text"""
    
    def __init__(self):
        self.sia = SentimentIntensityAnalyzer()
        
        # Bitcoin-specific keywords
        self.price_keywords = {
            'surge', 'rally', 'soar', 'jump', 'spike', 'climb', 'rise',
            'drop', 'fall', 'crash', 'plunge', 'decline', 'sink', 'tumble',
            'price', 'value', 'worth', 'cost', 'trading'
        }
        
        self.technical_terms = {
            'blockchain', 'halving', 'mining', 'hash', 'difficulty',
            'wallet', 'exchange', 'ledger', 'node', 'fork', 'protocol',
            'satoshi', 'altcoin', 'defi', 'nft', 'smart contract',
            'consensus', 'proof of work', 'proof of stake'
        }
    
    def extract_features(self, text: str) -> Dict[str, float]:
        """
        Extract 14 NLP features from article text
        
        Returns:
            Dictionary with 14 feature values
        """
        if not text or len(text.strip()) == 0:
            return self._get_zero_features()
        
        # Clean text
        text = text.lower()
        
        # Tokenize
        sentences = sent_tokenize(text)
        words = word_tokenize(text)
        
        # Filter out punctuation for word stats
        words_alpha = [w for w in words if w.isalnum()]
        
        # A. Sentiment Lexicon Features (4)
        vader_scores = self.sia.polarity_scores(text)
        
        # B. Statistical Features (5)
        avg_sentence_length = len(words) / len(sentences) if len(sentences) > 0 else 0
        word_count = len(words_alpha)
        unique_words = len(set(words_alpha))
        unique_word_ratio = unique_words / word_count if word_count > 0 else 0
        exclamation_count = text.count('!')
        question_count = text.count('?')
        
        # C. Bitcoin-Specific Features (3)
        btc_mentions = text.count('bitcoin') + text.count('btc')
        
        price_keyword_count = sum(1 for word in words_alpha 
                                  if word in self.price_keywords)
        
        # Technical terms (handle multi-word terms)
        technical_count = sum(1 for term in self.technical_terms 
                             if term in text)
        technical_term_ratio = technical_count / word_count if word_count > 0 else 0
        
        # D. Named Entity Features (2)
        try:
            tagged = pos_tag(words_alpha[:200])  # Limit to first 200 words for performance
            named_entities = ne_chunk(tagged)
            
            ne_person_count = 0
            ne_org_count = 0
            
            for chunk in named_entities:
                if hasattr(chunk, 'label'):
                    if chunk.label() == 'PERSON':
                        ne_person_count += 1
                    elif chunk.label() == 'ORGANIZATION':
                        ne_org_count += 1
        except Exception as e:
            print(f"NER extraction failed: {e}")
            ne_person_count = 0
            ne_org_count = 0
        
        return {
            # A. Sentiment Lexicon (4)
            'positive_word_ratio': vader_scores['pos'],
            'negative_word_ratio': vader_scores['neg'],
            'neutral_word_ratio': vader_scores['neu'],
            'compound_score': vader_scores['compound'],
            
            # B. Statistical (5)
            'avg_sentence_length': round(avg_sentence_length, 2),
            'word_count': word_count,
            'unique_word_ratio': round(unique_word_ratio, 3),
            'exclamation_count': exclamation_count,
            'question_count': question_count,
            
            # C. Bitcoin-Specific (3)
            'btc_mention_count': btc_mentions,
            'price_keyword_count': price_keyword_count,
            'technical_term_ratio': round(technical_term_ratio, 3),
            
            # D. Named Entities (2)
            'ne_person_count': ne_person_count,
            'ne_org_count': ne_org_count
        }
    
    def _get_zero_features(self) -> Dict[str, float]:
        """Return zero values for all features (for empty text)"""
        return {
            'positive_word_ratio': 0.0,
            'negative_word_ratio': 0.0,
            'neutral_word_ratio': 0.0,
            'compound_score': 0.0,
            'avg_sentence_length': 0.0,
            'word_count': 0,
            'unique_word_ratio': 0.0,
            'exclamation_count': 0,
            'question_count': 0,
            'btc_mention_count': 0,
            'price_keyword_count': 0,
            'technical_term_ratio': 0.0,
            'ne_person_count': 0,
            'ne_org_count': 0
        }


# Test function
if __name__ == "__main__":
    extractor = NLPFeatureExtractor()
    
    test_text = """
    Bitcoin surged to $87,000 today! The rally comes as major institutions 
    continue their blockchain adoption. Mining difficulty has increased, 
    signaling strong network health. CEO Michael Saylor announced more BTC purchases.
    """
    
    features = extractor.extract_features(test_text)
    print("Extracted Features:")
    for name, value in features.items():
        print(f"  {name}: {value}")
