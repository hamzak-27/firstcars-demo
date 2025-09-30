#!/usr/bin/env python3
"""
Gemini Model Discovery and Management Utilities
Automatically discovers available models and provides fallback options
"""

import logging
import os
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)

try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    logger.warning("Google Generative AI not available")

class GeminiModelManager:
    """Manages Gemini model discovery and fallback"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_AI_API_KEY')
        self.available_models = []
        self.configured = False
        
        if GENAI_AVAILABLE and self.api_key and self.api_key != "test-key":
            self._discover_models()
    
    def _discover_models(self) -> None:
        """Discover available models that support generateContent"""
        try:
            genai.configure(api_key=self.api_key)
            models = genai.list_models()
            
            self.available_models = []
            for model in models:
                if 'generateContent' in model.supported_generation_methods:
                    self.available_models.append(model.name)
            
            self.configured = True
            logger.info(f"Discovered {len(self.available_models)} available Gemini models")
            
            if self.available_models:
                logger.info(f"Available models: {', '.join(self.available_models[:3])}...")
            
        except Exception as e:
            logger.warning(f"Failed to discover Gemini models: {e}")
            self.configured = False
            self.available_models = []
    
    def get_best_model(self, preferred_models: List[str] = None) -> Optional[str]:
        """Get the best available model from preferred list or fallback"""
        
        if not self.configured or not self.available_models:
            logger.warning("No models available - API key may be invalid or not configured")
            return None
        
        # Default preferred models (in order of preference)
        if preferred_models is None:
            preferred_models = [
                "models/gemini-2.5-flash",
                "models/gemini-2.5-pro",
                "models/gemini-2.0-flash",
                "models/gemini-flash-latest",
                "models/gemini-pro-latest",
                "models/gemini-1.5-flash",
                "models/gemini-1.5-pro", 
                "gemini-pro",  # Fallback without models/ prefix
                "gemini-1.5-flash",
                "gemini-1.5-pro"
            ]
        
        # Try preferred models in order
        for preferred in preferred_models:
            if preferred in self.available_models:
                logger.info(f"Selected preferred model: {preferred}")
                return preferred
        
        # If no preferred models available, use the first available
        if self.available_models:
            fallback = self.available_models[0]
            logger.info(f"Using fallback model: {fallback}")
            return fallback
        
        return None
    
    def create_model(self, model_name: Optional[str] = None) -> Tuple[Optional[object], str]:
        """Create a GenerativeModel instance with the best available model"""
        
        if not GENAI_AVAILABLE:
            return None, "Google Generative AI not available"
        
        if not self.api_key or self.api_key == "test-key":
            return None, "No valid API key configured"
        
        # Get the best model to use
        if model_name is None:
            model_name = self.get_best_model()
        
        if not model_name:
            return None, "No compatible models available"
        
        try:
            if not self.configured:
                genai.configure(api_key=self.api_key)
            
            # Configure safety settings to bypass blocks
            safety_settings = {
                genai.types.HarmCategory.HARM_CATEGORY_HATE_SPEECH: genai.types.HarmBlockThreshold.BLOCK_NONE,
                genai.types.HarmCategory.HARM_CATEGORY_HARASSMENT: genai.types.HarmBlockThreshold.BLOCK_NONE,
                genai.types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: genai.types.HarmBlockThreshold.BLOCK_NONE,
                genai.types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: genai.types.HarmBlockThreshold.BLOCK_NONE,
            }
            
            model = genai.GenerativeModel(
                model_name,
                safety_settings=safety_settings
            )
            return model, model_name
            
        except Exception as e:
            error_msg = f"Failed to create model '{model_name}': {e}"
            logger.error(error_msg)
            
            # Try fallback models
            if model_name != self.get_best_model():
                fallback_model = self.get_best_model()
                if fallback_model and fallback_model != model_name:
                    try:
                        # Configure safety settings for fallback too
                        safety_settings = {
                            genai.types.HarmCategory.HARM_CATEGORY_HATE_SPEECH: genai.types.HarmBlockThreshold.BLOCK_NONE,
                            genai.types.HarmCategory.HARM_CATEGORY_HARASSMENT: genai.types.HarmBlockThreshold.BLOCK_NONE,
                            genai.types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: genai.types.HarmBlockThreshold.BLOCK_NONE,
                            genai.types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: genai.types.HarmBlockThreshold.BLOCK_NONE,
                        }
                        model = genai.GenerativeModel(fallback_model, safety_settings=safety_settings)
                        logger.info(f"Successfully created fallback model: {fallback_model}")
                        return model, fallback_model
                    except Exception as fallback_error:
                        logger.error(f"Fallback model also failed: {fallback_error}")
            
            return None, error_msg
    
    def get_model_info(self) -> dict:
        """Get information about available models"""
        return {
            "api_configured": self.configured,
            "available_models": self.available_models,
            "total_models": len(self.available_models),
            "recommended_model": self.get_best_model(),
            "api_key_present": bool(self.api_key and self.api_key != "test-key")
        }

# Global instance for easy access
_model_manager = None

def get_model_manager(api_key: Optional[str] = None) -> GeminiModelManager:
    """Get or create the global model manager"""
    global _model_manager
    if _model_manager is None or (api_key and api_key != getattr(_model_manager, 'api_key', None)):
        _model_manager = GeminiModelManager(api_key)
    return _model_manager

def create_gemini_model(api_key: Optional[str] = None, preferred_model: Optional[str] = None) -> Tuple[Optional[object], str]:
    """Convenience function to create a Gemini model with automatic fallback"""
    manager = get_model_manager(api_key)
    return manager.create_model(preferred_model)

def list_available_models(api_key: Optional[str] = None) -> List[str]:
    """List all available Gemini models"""
    manager = get_model_manager(api_key)
    return manager.available_models

# Test function
def test_model_discovery():
    """Test the model discovery functionality"""
    print("🔍 Testing Gemini Model Discovery...")
    print("=" * 50)
    
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("⚠️ No API key found - set GEMINI_API_KEY environment variable")
        print("Testing with test key (will show fallback behavior)...")
        api_key = "test-key"
    
    manager = GeminiModelManager(api_key)
    info = manager.get_model_info()
    
    print(f"API Configured: {info['api_configured']}")
    print(f"API Key Present: {info['api_key_present']}")
    print(f"Total Available Models: {info['total_models']}")
    print(f"Recommended Model: {info['recommended_model']}")
    
    if info['available_models']:
        print(f"\nAvailable Models:")
        for i, model in enumerate(info['available_models'], 1):
            print(f"  {i}. {model}")
    
    # Test model creation
    print(f"\n🧪 Testing Model Creation...")
    model, model_name = manager.create_model()
    
    if model:
        print(f"✅ Successfully created model: {model_name}")
    else:
        print(f"❌ Failed to create model: {model_name}")
    
    print(f"\n✨ Model discovery test complete!")

if __name__ == "__main__":
    test_model_discovery()