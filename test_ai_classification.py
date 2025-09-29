#!/usr/bin/env python3
"""
Test AI-powered classification with sample multiple booking content
"""

import os
from gemma_classification_agent import GemmaClassificationAgent

def test_with_api_key():
    """Test classification with API key (if available)"""
    
    # Sample multiple booking content that should be detected as MULTIPLE
    sample_content = """
    Dear Team,
    
    Please arrange two cars for the following:
    
    First car:
    - Passenger: John Smith (9876543210)
    - Date: 25th December 2024
    - Time: 9:00 AM
    - From: Delhi Office
    - To: Airport
    - Vehicle: Dzire
    
    Second car:
    - Passenger: Mary Wilson (9876543211)
    - Date: 26th December 2024  
    - Time: 10:00 AM
    - From: Mumbai Office
    - To: Hotel
    - Vehicle: Innova
    
    Please arrange both bookings.
    
    Thanks,
    Travel Team
    """
    
    print("🧪 Testing AI-powered classification...")
    print("Content to classify:")
    print("-" * 50)
    print(sample_content.strip())
    print("-" * 50)
    
    # Check for API key
    api_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_AI_API_KEY')
    if not api_key:
        print("❌ No API key found in environment variables")
        print("Please set GEMINI_API_KEY or test with the Streamlit app")
        return
    
    try:
        # Initialize agent with API key
        agent = GemmaClassificationAgent(api_key=api_key)
        
        # Classify the content
        result = agent.classify_content(sample_content, "email")
        
        print("🎯 CLASSIFICATION RESULTS:")
        print(f"Booking Type: {result.booking_type.value}")
        print(f"Booking Count: {result.booking_count}")
        print(f"Confidence: {result.confidence_score:.1%}")
        print(f"Duty Type: {result.detected_duty_type.value}")
        print(f"Cost: ₹{result.cost_inr:.4f}")
        print(f"Processing Time: {result.processing_time:.2f}s")
        print(f"Reasoning: {result.reasoning}")
        
        # Check if it correctly identified multiple bookings
        if result.booking_type.value == "multiple" and result.booking_count >= 2:
            print("✅ PASS: Correctly identified as multiple bookings!")
        else:
            print("❌ FAIL: Should have identified as multiple bookings")
            print("This suggests the AI prompt or business rules need adjustment")
        
        # Show detected patterns
        print("\n📋 DETECTED PATTERNS:")
        print(f"Multi-day continuous: {result.is_multi_day_continuous}")
        print(f"Alternate days: {result.is_alternate_days}")
        print(f"Vehicle changes: {result.has_vehicle_changes}")
        print(f"Multiple drops per day: {result.has_multiple_drops_per_day}")
        print(f"Detected dates: {result.detected_dates}")
        print(f"Detected vehicles: {result.detected_vehicles}")
        print(f"Detected drops: {result.detected_drops}")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_with_api_key()