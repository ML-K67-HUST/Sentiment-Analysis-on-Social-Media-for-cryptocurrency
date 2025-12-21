"""
Sentiment Analysis Agent using LLM (Gemini or Together AI).
Classifies cryptocurrency articles based on predefined policies.
"""
import json
import os
import sys

# Add parent directory to path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import config

# Import LLM clients based on provider
if config.LLM_PROVIDER == "gemini":
    from google import genai
    from google.genai import types
else:
    from openai import OpenAI


def infer_policy(text: str) -> dict:
    """
    Analyze text and classify it according to predefined policies.
    Supports both Gemini and Together AI as LLM providers.
    
    Args:
        text: The article content to analyze
        
    Returns:
        dict: Classification results with metrics for each policy
        
    Raises:
        ValueError: If required API key is not configured
    """
    # Removed verbose logging for cleaner output
    
    if config.LLM_PROVIDER == "gemini":
        return _infer_policy_gemini(text)
    else:
        return _infer_policy_together(text)


def _get_system_prompt() -> str:
    """Get the system prompt for sentiment analysis."""
    return """
You are an expert cryptocurrency market analyst with 10 years of experience in sentiment analysis.
Your task is to analyze cryptocurrency news articles and determine their overall sentiment towards the market.

Analyze the article and classify it into one of these four categories:
- "Bitcoin Reporting": The article provides factual, balanced, and objective information about Bitcoin. Bitcoin must be mentioned in the article.
- "Bitcoin Price Manipulation": The article contains claims about Bitcoin's price going up or down without credible evidence or reasoning.
- "Bitcoin Positive Speculation": The article presents a reasonable and well-substantiated case for why Bitcoin's price may increase.
- "Bitcoin Negative Speculation": The article presents a reasonable and well-substantiated case for why Bitcoin's price may decrease.

Return ONLY a valid JSON object with this exact structure (no markdown, no code blocks, no extra text):
{
  "sentiment": "Bitcoin Reporting" or "Bitcoin Price Manipulation" or "Bitcoin Positive Speculation" or "Bitcoin Negative Speculation",
  "confidence": 0.85,
  "reasoning": "Brief explanation of why this sentiment was chosen based on the article content"
}

Be concise and accurate. The confidence should be between 0.0 and 1.0.
"""



def _infer_policy_gemini(text: str) -> dict:
    """
    Analyze text using Google Gemini API with automatic key rotation.
    
    Args:
        text: The article content to analyze
        
    Returns:
        dict: Classification results
    """
    if not config.GEMINI_API_KEYS:
        raise ValueError(
            "GEMINI_API_KEY or GEMINI_API_KEYS not configured. \n"
            "Single key: GEMINI_API_KEY=your_key\n"
            "Multiple keys: GEMINI_API_KEYS=key1,key2,key3\n"
            "Get your free API key at: https://makersuite.google.com/app/apikey"
        )
    
    # Initialize key rotator (singleton pattern)
    if not hasattr(_infer_policy_gemini, '_rotator'):
        from .key_rotator import GeminiKeyRotator
        _infer_policy_gemini._rotator = GeminiKeyRotator(config.GEMINI_API_KEYS)
        print(f"🔑 Initialized KeyRotator with {len(config.GEMINI_API_KEYS)} API keys")
    
    rotator = _infer_policy_gemini._rotator
    
    # Prepare prompt
    prompt = f"{_get_system_prompt()}\n\nArticle to analyze:\n{text}"
    
    MAX_RETRIES = 3
    # Try all available keys
    max_attempts = len(config.GEMINI_API_KEYS)
    target_model = 'gemini-2.5-flash'
    print(f"🤖 Using model: {target_model}")
    
    for attempt in range(max_attempts):
        current_key = rotator.get_next_key()
        if not current_key:
            # All keys in cooldown
            break
        
        try:
            # Create client with current key
            client = genai.Client(api_key=current_key)
            
            # Generate response
            response = client.models.generate_content(
                model=target_model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.2,
                    top_p=0.8,
                    top_k=40,
                    max_output_tokens=2048,
                )
            )
            
            # Success! Mark key as healthy
            rotator.mark_success(current_key)
            
            # Parse JSON response
            content = response.text.strip()
            content = content.strip("```json").strip("```").strip()
            
            return json.loads(content)
            
        except json.JSONDecodeError as e:
            # JSON parse error - not a key issue, fail silently
            return {}
            
        except Exception as e:
            error_str = str(e)
            print(f"⚠️ DEBUG - Error detected for key ...{current_key[-6:]}: {error_str}")
            
            # Check if rate limit error
            if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str or "quota" in error_str.lower():
                rotator.mark_rate_limit(current_key)
                # Continue to next key immediately
                continue
            
            # Other error - mark as failed and try next key
            rotator.mark_failed(current_key)
            
            # Re-raise critical errors
            if "INVALID_ARGUMENT" in error_str or "API_KEY" in error_str:
                raise
            
            # Continue to next key for other errors
            continue
    
    # All keys exhausted
    raise Exception("ALL_KEYS_EXHAUSTED")


def _infer_policy_together(text: str) -> dict:
    """
    Analyze text using Together AI (Meta-Llama).
    
    Args:
        text: The article content to analyze
        
    Returns:
        dict: Classification results
    """
    if not config.TOGETHER_API_KEY:
        raise ValueError(
            "TOGETHER_API_KEY not configured. "
            "Please set it in your .env file."
        )
    
    client = OpenAI(
        api_key=config.TOGETHER_API_KEY,
        base_url='https://api.together.xyz/v1',
    )
    chat = [
        {
            "role": "system",
            "content": _get_system_prompt()
        },
        {
            "role": "user",
            "content": text
        }
    ]
    model = "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo"
    
    try:
        chat_response = client.chat.completions.create(
            model=model,
            messages=chat,
            top_p=0.2,
            stream=False,
        )
        
        content = chat_response.choices[0].message.content.strip("```").strip("json")
        return json.loads(content)
        
    except json.JSONDecodeError as e:
        print(f'❌ JSON LOAD FAILED: {e}')
        print('Response content:')
        print(chat_response.choices[0].message.content)
        print("Cannot parse the above response as JSON")
        return {}
        
    except Exception as e:
        print(f'❌ Error calling LLM API: {e}')
        return {}


def infer_sentiment(metric: dict) -> float:
    """
    Calculate sentiment score from policy classification metrics.
    
    Args:
        metric: Dictionary containing policy classification results
        
    Returns:
        float: Sentiment score (0-100)
    """
    if not metric:
        return 0.0
        
    # Weights for each policy type
    WEIGHTS = {
        "positive": 1.0,
        "manipulation": 0.1,
        "reporting": 0.2,
        "negative": -1.0,
    }
    
    # CASE 1: New Gemini Format (Single sentiment)
    if "sentiment" in metric:
        sentiment_text = metric.get("sentiment", "").lower()
        confidence = metric.get("confidence", 1.0)
        
        score = 0.0
        if "positive" in sentiment_text:
            score = WEIGHTS["positive"]
        elif "negative" in sentiment_text:
            score = WEIGHTS["negative"]
        elif "manipulation" in sentiment_text:
            score = WEIGHTS["manipulation"]
        elif "reporting" in sentiment_text:
            score = WEIGHTS["reporting"]
            
        # Weighted by confidence? The old logic didn't seem to verify confidence weight in loop, 
        # but let's just return the raw score scaled to 0-100 as per docstring
        return round(score * 100, 2)

    # CASE 2: Old Format (Metrics list)
    if "metrics" in metric:
        sentiment_score = 0.0
        
        for policy_result in metric["metrics"]:
            policy_name = policy_result.get("policy", "").lower()
            classification = int(policy_result.get("classification", 0))
            
            for keyword, weight in WEIGHTS.items():
                if keyword in policy_name:
                    sentiment_score += classification * weight
                    break
        
        # Normalize and convert to percentage
        return round(sentiment_score, 4) * 100
        
    return 0.0