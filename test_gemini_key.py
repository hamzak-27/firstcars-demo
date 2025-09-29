#!/usr/bin/env python3
"""
Test Gemini API Key Configuration
"""

import os
import logging
from gemini_model_utils import GeminiModelManager, test_model_discovery

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_gemini_api_key():
    """Test if the Gemini API key is properly configured"""
    
    print("🔑 Testing Gemini API Key Configuration")
    print("=" * 50)
    
    # Set the API key
    gemini_api_key = "AIzaSyAId73p8fsv1U0z2_jQ0yOLdcVJsVsOmeg"
    os.environ['GEMINI_API_KEY'] = gemini_api_key
    os.environ['GOOGLE_AI_API_KEY'] = gemini_api_key
    
    print(f"✅ Set Gemini API key: {gemini_api_key[:20]}...{gemini_api_key[-4:]}")
    
    # Test if the key is accessible
    env_key = os.getenv('GEMINI_API_KEY')
    print(f"✅ Retrieved from env: {env_key[:20]}...{env_key[-4:] if env_key else 'None'}")
    
    # Test model manager initialization
    print("\n🔧 Testing Model Manager...")
    try:
        manager = GeminiModelManager(api_key=gemini_api_key)
        info = manager.get_model_info()
        
        print(f"API Configured: {info['api_configured']}")
        print(f"API Key Present: {info['api_key_present']}")
        print(f"Total Available Models: {info['total_models']}")
        print(f"Recommended Model: {info['recommended_model']}")
        
        if info['available_models']:
            print(f"Available Models: {info['available_models'][:3]}")
        
        # Test model creation
        print("\n🧪 Testing Model Creation...")
        model, model_name = manager.create_model()
        
        if model:
            print(f"✅ Successfully created model: {model_name}")
            
            # Test a simple generation
            print("\n📝 Testing Simple Generation...")
            try:
                test_prompt = "Say 'Gemini API is working!' in a friendly way."
                response = model.generate_content(test_prompt)
                print(f"✅ Model response: {response.text[:100]}...")
                
                return True
                
            except Exception as gen_error:
                print(f"❌ Generation test failed: {gen_error}")
                return False
                
        else:
            print(f"❌ Failed to create model: {model_name}")
            return False
            
    except Exception as e:
        print(f"❌ Model manager test failed: {e}")
        return False

def test_agents_with_api_key():
    """Test that agents can use the API key properly"""
    
    print("\n🤖 Testing Agents with API Key")
    print("=" * 50)
    
    gemini_api_key = "AIzaSyAId73p8fsv1U0z2_jQ0yOLdcVJsVsOmeg"
    os.environ['GEMINI_API_KEY'] = gemini_api_key
    
    # Test classification agent
    try:
        from gemma_classification_agent import GemmaClassificationAgent
        
        print("Testing Classification Agent...")
        agent = GemmaClassificationAgent(api_key=gemini_api_key)
        
        test_content = """
        From: booking@carservice.com
        
        Dear Customer,
        
        Your booking is confirmed:
        Passenger: John Doe
        Date: 2024-01-15
        Time: 08:00 AM
        Vehicle: Sedan
        From: Airport
        To: Hotel
        """
        
        result = agent.classify_content(test_content)
        print(f"✅ Classification successful: {result.booking_type.value}")
        print(f"   Confidence: {result.confidence_score:.2f}")
        print(f"   Cost: ₹{result.cost_inr:.4f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Agent test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Comprehensive Gemini API Tests")
    print("=" * 60)
    
    # Test 1: Basic API key configuration
    api_test = test_gemini_api_key()
    
    # Test 2: Agent integration
    agent_test = test_agents_with_api_key()
    
    print("\n" + "=" * 60)
    print("📊 Test Results Summary:")
    print(f"   API Key Test: {'✅ PASS' if api_test else '❌ FAIL'}")
    print(f"   Agent Test: {'✅ PASS' if agent_test else '❌ FAIL'}")
    
    if api_test and agent_test:
        print("\n🎉 All tests passed! Gemini API is properly configured.")
    else:
        print("\n⚠️ Some tests failed. Check the configuration.")