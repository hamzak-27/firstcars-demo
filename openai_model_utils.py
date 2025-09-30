#!/usr/bin/env python3
"""
OpenAI Model Discovery and Management Utilities
Replaces gemini_model_utils.py with OpenAI GPT models
"""

import logging
import os
import json
from typing import List, Optional, Tuple, Dict, Any

logger = logging.getLogger(__name__)

try:
    import openai
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI not available - install with: pip install openai")

class OpenAIModelManager:
    """Manages OpenAI model configuration and usage"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        self.client = None
        self.configured = False
        
        # Available models (in order of preference for our use case)
        self.available_models = [
            "gpt-4o-mini",          # Best for our use case - fast, cheap, reliable
            "gpt-3.5-turbo",        # Backup option
            "gpt-4o",               # Overkill but available
            "gpt-4-turbo",          # Also overkill
        ]
        
        if OPENAI_AVAILABLE and self.api_key:
            self._configure_client()
    
    def _configure_client(self) -> None:
        """Configure OpenAI client"""
        try:
            self.client = OpenAI(api_key=self.api_key)
            # Test the connection with a minimal call
            response = self.client.models.list()
            self.configured = True
            logger.info(f"OpenAI client configured successfully")
            
        except Exception as e:
            logger.warning(f"Failed to configure OpenAI client: {e}")
            self.configured = False
            self.client = None
    
    def get_best_model(self, preferred_models: List[str] = None) -> Optional[str]:
        """Get the best available model"""
        
        if not self.configured:
            logger.warning("OpenAI client not configured")
            return None
        
        # Use provided preferences or defaults
        models_to_try = preferred_models or self.available_models
        
        # For our use case, gpt-4o-mini is almost always the best choice
        return models_to_try[0] if models_to_try else "gpt-4o-mini"
    
    def create_completion(self, 
                         messages: List[Dict[str, str]], 
                         model: str = "gpt-4o-mini",
                         temperature: float = 0.1,
                         max_tokens: int = 1000,
                         force_json: bool = False) -> Tuple[Optional[str], Dict[str, Any]]:
        """Create a chat completion and return response with metadata"""
        
        if not self.configured or not self.client:
            raise ValueError("OpenAI client not configured")
        
        try:
            # Check if messages contain 'json' for JSON mode
            messages_text = ' '.join([msg.get('content', '') for msg in messages]).lower()
            use_json_mode = force_json and 'json' in messages_text
            
            completion_params = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            
            if use_json_mode:
                completion_params["response_format"] = {"type": "json_object"}
            
            response = self.client.chat.completions.create(**completion_params)
            
            # Extract response text
            response_text = response.choices[0].message.content
            
            # Extract metadata
            metadata = {
                "model": response.model,
                "input_tokens": response.usage.prompt_tokens,
                "output_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
                "finish_reason": response.choices[0].finish_reason
            }
            
            return response_text, metadata
            
        except Exception as e:
            logger.error(f"OpenAI API call failed: {e}")
            raise
    
    def calculate_cost(self, input_tokens: int, output_tokens: int, model: str = "gpt-4o-mini") -> float:
        """Calculate cost in INR for token usage"""
        
        # GPT-4o-mini pricing (as of 2024)
        pricing = {
            "gpt-4o-mini": {
                "input": 0.15 / 1000000,   # $0.15 per 1M tokens
                "output": 0.60 / 1000000   # $0.60 per 1M tokens
            },
            "gpt-3.5-turbo": {
                "input": 0.50 / 1000000,   # $0.50 per 1M tokens  
                "output": 1.50 / 1000000   # $1.50 per 1M tokens
            },
            "gpt-4o": {
                "input": 5.00 / 1000000,   # $5.00 per 1M tokens
                "output": 15.00 / 1000000  # $15.00 per 1M tokens
            }
        }
        
        # Default to gpt-4o-mini if model not found
        model_pricing = pricing.get(model, pricing["gpt-4o-mini"])
        
        # Calculate cost in USD
        cost_usd = (input_tokens * model_pricing["input"]) + (output_tokens * model_pricing["output"])
        
        # Convert to INR (approximate rate: 1 USD = 83 INR)
        cost_inr = cost_usd * 83
        
        return cost_inr
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about OpenAI configuration"""
        return {
            "api_configured": self.configured,
            "available_models": self.available_models,
            "recommended_model": self.get_best_model(),
            "api_key_present": bool(self.api_key),
            "client_ready": self.client is not None
        }

# Global instance for easy access
_model_manager = None

def get_model_manager(api_key: Optional[str] = None) -> OpenAIModelManager:
    """Get or create the global model manager"""
    global _model_manager
    if _model_manager is None or (api_key and api_key != getattr(_model_manager, 'api_key', None)):
        _model_manager = OpenAIModelManager(api_key)
    return _model_manager

def create_openai_client(api_key: Optional[str] = None, preferred_model: Optional[str] = None) -> Tuple[Optional[OpenAIModelManager], str]:
    """Convenience function to create OpenAI manager"""
    manager = get_model_manager(api_key)
    
    if not manager.configured:
        return None, "OpenAI client not configured - check API key"
    
    model_name = manager.get_best_model([preferred_model] if preferred_model else None)
    return manager, model_name or "gpt-4o-mini"

def create_chat_messages(system_prompt: str, user_content: str) -> List[Dict[str, str]]:
    """Helper to create properly formatted chat messages"""
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content}
    ]

# Test function
def test_openai_connection():
    """Test OpenAI connection and model availability"""
    print("🔍 Testing OpenAI Connection...")
    print("=" * 50)
    
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("⚠️ No OpenAI API key found - set OPENAI_API_KEY environment variable")
        return False
    
    try:
        manager = OpenAIModelManager(api_key)
        info = manager.get_model_info()
        
        print(f"API Configured: {info['api_configured']}")
        print(f"API Key Present: {info['api_key_present']}")
        print(f"Client Ready: {info['client_ready']}")
        print(f"Recommended Model: {info['recommended_model']}")
        
        if info['available_models']:
            print(f"\nAvailable Models:")
            for i, model in enumerate(info['available_models'], 1):
                print(f"  {i}. {model}")
        
        # Test a simple completion
        if manager.configured:
            print(f"\n🧪 Testing simple completion...")
            messages = create_chat_messages(
                "You are a helpful assistant. Respond with valid JSON.",
                "Classify this: 'Book a car from Chennai to Bangalore tomorrow'. Respond with {\"type\": \"single\" or \"multiple\", \"reason\": \"brief explanation\"}"
            )
            
            response, metadata = manager.create_completion(messages, max_tokens=100)
            
            print(f"✅ Test Response: {response[:100]}...")
            print(f"📊 Tokens: {metadata['input_tokens']} input, {metadata['output_tokens']} output")
            print(f"💰 Cost: ₹{manager.calculate_cost(metadata['input_tokens'], metadata['output_tokens']):.4f}")
            
            return True
        else:
            print("❌ Client not configured properly")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    test_openai_connection()