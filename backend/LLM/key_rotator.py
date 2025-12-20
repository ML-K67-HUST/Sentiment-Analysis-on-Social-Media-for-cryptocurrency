"""
API Key Rotation Manager for Gemini
Manages multiple API keys with round-robin selection and auto-failover
"""
import time
import threading
from typing import List, Optional


class GeminiKeyRotator:
    """
    Manages multiple Gemini API keys with intelligent rotation.
    
    Features:
    - Round-robin selection for load balancing
    - Health tracking per key
    - Automatic cooldown for rate-limited/failed keys
    - Thread-safe operations
    """
    
    def __init__(self, keys: List[str]):
        """
        Initialize the key rotator.
        
        Args:
            keys: List of Gemini API keys
        """
        if not keys:
            raise ValueError("At least one API key is required")
        
        self.keys = keys
        self.current_idx = 0
        self.lock = threading.Lock()
        
        # Health tracking: {key: {"failures": int, "cooldown_until": timestamp}}
        self.health = {
            key: {"failures": 0, "cooldown_until": 0}
            for key in keys
        }
    
    def get_next_key(self) -> Optional[str]:
        """
        Get the next healthy API key using round-robin selection.
        
        Returns:
            str: A healthy API key, or None if all keys are in cooldown
        """
        with self.lock:
            now = time.time()
            attempts = 0
            max_attempts = len(self.keys) * 2  # Try twice through all keys
            
            while attempts < max_attempts:
                key = self.keys[self.current_idx]
                key_health = self.health[key]
                
                # Check if key is healthy (not in cooldown)
                if key_health["cooldown_until"] <= now:
                    # Move to next key for next call (round-robin)
                    self.current_idx = (self.current_idx + 1) % len(self.keys)
                    return key
                
                # Key in cooldown, try next
                self.current_idx = (self.current_idx + 1) % len(self.keys)
                attempts += 1
            
            # All keys are in cooldown - return first key anyway and log warning
            print("⚠️  All API keys in cooldown! Using first key anyway...")
            return self.keys[0]
    
    def mark_rate_limit(self, key: str):
        """
        Mark a key as rate-limited (429/RESOURCE_EXHAUSTED).
        Applies 60-second cooldown.
        
        Args:
            key: The API key that hit rate limit
        """
        with self.lock:
            if key in self.health:
                cooldown_seconds = 60
                self.health[key]["cooldown_until"] = time.time() + cooldown_seconds
                print(f"🔄 Key ...{key[-8:]} rate limited → {cooldown_seconds}s cooldown")
    
    def mark_failed(self, key: str):
        """
        Mark a key as failed. Applies exponential backoff cooldown.
        
        Args:
            key: The API key that failed
        """
        with self.lock:
            if key in self.health:
                self.health[key]["failures"] += 1
                failures = self.health[key]["failures"]
                
                # Exponential backoff: 5s, 30s, 5min, 15min
                cooldown_map = {1: 5, 2: 30, 3: 300, 4: 900}
                cooldown_seconds = cooldown_map.get(failures, 900)  # Max 15min
                
                self.health[key]["cooldown_until"] = time.time() + cooldown_seconds
                print(f"❌ Key ...{key[-8:]} failed (×{failures}) → {cooldown_seconds}s cooldown")
    
    def mark_success(self, key: str):
        """
        Mark a key as successful. Resets failure count.
        
        Args:
            key: The API key that succeeded
        """
        with self.lock:
            if key in self.health:
                # Reset failures on success
                if self.health[key]["failures"] > 0:
                    print(f"✅ Key ...{key[-8:]} recovered")
                self.health[key]["failures"] = 0
                self.health[key]["cooldown_until"] = 0
    
    def get_stats(self) -> dict:
        """
        Get current health statistics for all keys.
        
        Returns:
            dict: Health stats for each key
        """
        with self.lock:
            now = time.time()
            return {
                key: {
                    "failures": health["failures"],
                    "cooldown_remaining": max(0, int(health["cooldown_until"] - now)),
                    "status": "cooldown" if health["cooldown_until"] > now else "healthy"
                }
                for key, health in self.health.items()
            }
