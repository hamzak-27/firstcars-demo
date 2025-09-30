#!/usr/bin/env python3
"""
Test script to verify Gemini API is working with updated safety settings
"""

import os
import logging
from gemini_model_utils import create_gemini_model

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_gemini_api():
    """Test Gemini API with the car rental booking content"""
    
    # Your API key from environment or hardcode for testing
    api_key = os.getenv('GEMINI_API_KEY') or 'AIzaSyAId73p8fsv1U0z2_jQ0yOLdcVJsVsOmeg'
    
    print(f"🧪 Testing Gemini API with key: {api_key[:10]}...{api_key[-4:]}")
    
    try:
        # Create model using updated utility
        model, model_name = create_gemini_model(api_key)
        
        if not model:
            print(f"❌ Failed to create Gemini model: {model_name}")
            return False
        
        print(f"✅ Successfully created model: {model_name}")
        
        # Test with simple booking content
        test_content = """
        Kindly confirm a cab:
        
        Location: Chennai
        Job: Outstation. (chennai to bangalore to chennai)
        Date: Saturday, October 04, 2025 
        Time: 4am
        Pickup address: 9B2, DABC Mithilam Apartments, Nolambur, Chennai
        Type of car: Suzuki Dzire
        
        Regards,
        Ganesan K
        """
        
        prompt = f"""
        Analyze this car rental booking request and extract key information in JSON format:
        
        Content: {test_content}
        
        Please respond with:
        {{
            "passenger_name": "extracted name",
            "pickup_location": "extracted location",
            "destination": "extracted destination",  
            "booking_type": "single or multiple",
            "vehicle_requested": "vehicle type"
        }}
        """
        
        print("🔄 Testing API call...")
        response = model.generate_content(prompt)
        
        if response and hasattr(response, 'text') and response.text:
            print(f"✅ API call successful!")
            print(f"📝 Response: {response.text[:200]}...")
            return True
        else:
            print(f"❌ API call failed - no response text")
            if hasattr(response, 'prompt_feedback'):
                print(f"Prompt feedback: {response.prompt_feedback}")
            if hasattr(response, 'candidates'):
                print(f"Candidates: {response.candidates}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing Gemini API: {str(e)}")
        return False

def test_classification():
    """Test the classification agent specifically"""
    
    try:
        from booking_classification_agent import BookingClassificationAgent
        
        print("\n🎯 Testing Classification Agent...")
        
        api_key = os.getenv('GEMINI_API_KEY') or 'AIzaSyAId73p8fsv1U0z2_jQ0yOLdcVJsVsOmeg'
        classifier = BookingClassificationAgent(api_key)
        
        if not classifier.ai_available:
            print("❌ Classification agent AI not available")
            return False
        
        test_content = """
        Need a cab for Chennai to Bangalore outstation trip.
        Date: October 4th, 2025
        Time: 4 AM
        Vehicle: Dzire
        """
        
        print("🔄 Testing classification...")
        result = classifier.classify_text_content(test_content)
        
        print(f"✅ Classification successful!")
        print(f"📊 Predicted bookings: {result.predicted_booking_count}")
        print(f"📋 Booking type: {result.booking_type}")
        print(f"🎯 Confidence: {result.confidence_score}")
        print(f"💭 Reasoning: {result.reasoning[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing classification agent: {str(e)}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Gemini API with Safety Settings Fix")
    print("=" * 50)
    
    # Test basic API
    api_test = test_gemini_api()
    
    # Test classification agent
    classification_test = test_classification()
    
    print("\n" + "=" * 50)
    if api_test and classification_test:
        print("🎉 All tests passed! Gemini API is working correctly.")
        print("Your app should now work without safety filter blocks.")
    else:
        print("❌ Some tests failed. Check the errors above.")
        if not api_test:
            print("  - Basic API test failed")
        if not classification_test:
            print("  - Classification agent test failed")