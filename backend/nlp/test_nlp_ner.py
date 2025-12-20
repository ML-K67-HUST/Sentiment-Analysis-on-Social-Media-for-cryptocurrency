
import nltk
from feature_extractor import NLPFeatureExtractor

def test_ner():
    extractor = NLPFeatureExtractor()
    
    # Test text with known entities
    text = """
    Michael Saylor announced that MicroStrategy has purchased more Bitcoin.
    Elon Musk and Tesla are also watching the crypto market closely.
    Binance CEO Changpeng Zhao commented on the situation.
    The SEC is reviewing the ETF application.
    """
    
    print(f"Testing NER on text:\n{text}")
    print("-" * 50)
    
    features = extractor.extract_features(text)
    
    print(f"Person Count: {features['ne_person_count']}")
    print(f"Org Count:    {features['ne_org_count']}")
    
    if features['ne_person_count'] > 0 or features['ne_org_count'] > 0:
        print("\n✅ NER is working correctly!")
    else:
        print("\n❌ NER failed to detect obvious entities.")

if __name__ == "__main__":
    test_ner()
