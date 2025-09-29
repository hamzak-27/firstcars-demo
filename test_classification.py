#!/usr/bin/env python3
"""
Test script for the new AI-powered BookingClassificationAgent
This demonstrates that the new agent correctly identifies multiple bookings
"""

import os
from booking_classification_agent import BookingClassificationAgent

def test_your_sample_email():
    """Test with your exact sample email that was failing"""
    
    sample_email = """
Kindly arrange two small cars as per details given below.

First car
Contact personnel     : Mr. Imamul Ansari
Mobile No.                     :  9920849115
Venue                               : Twin Towers CHS, Swatantrya Veer Savarkar Marg, Prabhadevi, Mumbai
Time & Date                   : 28.09.2025 @ 06.00 AM (Sunday)

Second car
Contact personnel     : Ms. K.C.Mini
Mobile No.                     : 9445205499
Venue                               : Godrej Prime, Sahakarnagar, Shell Colony, Chembur
Time & Date                   : 28.09.2025 @ 05.30 AM (Sunday)
"""
    
    print("🧪 TESTING NEW AI-POWERED CLASSIFICATION AGENT")
    print("="*60)
    
    # Test with your sample
    print("📝 Testing with your sample email:")
    print(sample_email.strip())
    print("\n" + "-"*60)
    
    # Initialize agent
    print("\n🔧 Initializing BookingClassificationAgent...")
    gemini_api_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_AI_API_KEY')
    
    if gemini_api_key:
        print("✅ Gemini API key found - will use AI classification")
    else:
        print("⚠️ No Gemini API key found - will use fallback pattern matching")
    
    classifier = BookingClassificationAgent(gemini_api_key=gemini_api_key)
    
    print(f"🤖 AI Available: {classifier.ai_available}")
    
    # Classify the content
    print("\n🎯 Classifying the content...")
    try:
        result = classifier.classify_text_content(sample_email)
        
        print("\n📊 CLASSIFICATION RESULTS:")
        print(f"   Predicted Booking Count: {result.predicted_booking_count}")
        print(f"   Booking Type: {result.booking_type}")
        print(f"   Confidence Score: {result.confidence_score:.2f}")
        print(f"   Reasoning: {result.reasoning}")
        
        if result.detected_patterns:
            print(f"   Detected Patterns: {result.detected_patterns}")
        
        if result.additional_info:
            print(f"   Additional Info: {result.additional_info}")
        
        # Check if result is correct
        if result.booking_type == "multiple" and result.predicted_booking_count == 2:
            print("\n✅ SUCCESS: Correctly identified as MULTIPLE bookings (2 cars)")
        else:
            print("\n❌ FAILED: Should be MULTIPLE bookings with count=2")
            
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

def test_other_scenarios():
    """Test other scenarios to validate the logic"""
    
    print("\n\n🧪 TESTING OTHER SCENARIOS")
    print("="*60)
    
    classifier = BookingClassificationAgent()
    
    scenarios = [
        {
            "name": "Single 4/40 drop",
            "content": "Need a cab for airport drop tomorrow at 8 AM. Passenger: John Doe.",
            "expected": "single"
        },
        {
            "name": "8/80 outstation consecutive days",  
            "content": "Need 8/80 package from Mumbai to Pune for 3 consecutive days starting Monday.",
            "expected": "single"
        },
        {
            "name": "Multiple drops same day",
            "content": "Need 2 drops today: one at 9 AM to airport, another at 6 PM to hotel.",
            "expected": "multiple"
        },
        {
            "name": "8/80 alternate days",
            "content": "Need 8/80 on Monday, then Wednesday, then Friday - alternate days.",
            "expected": "multiple"
        }
    ]
    
    for scenario in scenarios:
        print(f"\n📝 Testing: {scenario['name']}")
        print(f"   Content: {scenario['content']}")
        
        try:
            result = classifier.classify_text_content(scenario['content'])
            print(f"   Result: {result.booking_type} ({result.predicted_booking_count} bookings)")
            print(f"   Expected: {scenario['expected']}")
            
            if result.booking_type == scenario['expected']:
                print("   ✅ CORRECT")
            else:
                print("   ❌ INCORRECT")
                
        except Exception as e:
            print(f"   ❌ ERROR: {str(e)}")

if __name__ == "__main__":
    test_your_sample_email()
    test_other_scenarios()
    
    print("\n\n🏁 TESTING COMPLETED")
    print("="*60)
    print("📝 Notes:")
    print("1. If using Gemini AI, results should be highly accurate")
    print("2. Fallback pattern matching should still handle basic cases")
    print("3. Your sample email should now correctly show 2 MULTIPLE bookings")