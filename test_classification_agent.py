#!/usr/bin/env python3
"""
Simple test script for the Booking Classification Agent
Tests the basic functionality before running the full Streamlit app
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the current directory to path so we can import our modules
sys.path.append('.')

def test_classification_agent():
    """Test the classification agent with sample data"""
    
    try:
        from multi_agent_system.agents.classification_agent import BookingClassificationAgent
        from multi_agent_system.models.shared_models import BookingType, UsageType
        print("✅ Successfully imported classification agent")
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return
    
    # Check API key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ No OpenAI API key found. Please set OPENAI_API_KEY environment variable.")
        return
    
    print(f"✅ API Key found: {api_key[:8]}...{api_key[-4:]}")
    
    # Initialize agent
    try:
        agent = BookingClassificationAgent()
        print("✅ Agent initialized successfully")
    except Exception as e:
        print(f"❌ Agent initialization failed: {e}")
        return
    
    # Test samples
    test_samples = [
        {
            "name": "Single Booking - Multiple Passengers",
            "content": """
Dear Team,

Please arrange a car for office visit tomorrow:
- Passengers: John Smith, Mary Wilson, Peter Kumar
- Date: 25th December 2024
- Pickup: Andheri West, Mumbai at 9:00 AM
- Drop: BKC, Mumbai
- Vehicle: Innova
- Duration: 4 hours local use

Thanks!
Manager
            """.strip(),
            "expected_type": "single",
            "expected_count": 1
        },
        {
            "name": "Multiple Bookings - Local Multiple Days", 
            "content": """
Hi,

Need cars for local Bangalore trips:
- Date 1: 26th Dec - Koramangala to Electronic City (for John - 9876543210)
- Date 2: 27th Dec - Whitefield to MG Road (for Sarah - 9876543211) 
- Date 3: 28th Dec - Indiranagar to Hebbal (for Mike - 9876543212)

All local disposal, separate bookings please.

Thanks
            """.strip(),
            "expected_type": "multiple",
            "expected_count": 3
        }
    ]
    
    print("\n" + "="*60)
    print("TESTING CLASSIFICATION AGENT")
    print("="*60)
    
    total_cost = 0.0
    
    for i, sample in enumerate(test_samples, 1):
        print(f"\n🧪 Test {i}: {sample['name']}")
        print("-" * 40)
        
        input_data = {
            'email_content': sample['content'],
            'sender_email': 'test@example.com'
        }
        
        try:
            # Process classification
            result = agent.process(input_data)
            classification_result = agent.create_classification_result(result)
            
            # Display results
            print(f"📊 RESULTS:")
            print(f"   Booking Type: {classification_result.booking_type.value.upper()}")
            print(f"   Booking Count: {classification_result.booking_count}")
            print(f"   Usage Type: {classification_result.usage_type.value}")
            print(f"   Confidence: {classification_result.confidence_score:.1%}")
            print(f"   Processing Time: {result.processing_time:.2f}s")
            print(f"   Cost: ${result.cost_estimate:.4f}")
            
            total_cost += result.cost_estimate
            
            # Check if results match expectations
            expected_type = sample['expected_type']
            expected_count = sample['expected_count']
            
            actual_type = classification_result.booking_type.value
            actual_count = classification_result.booking_count
            
            if actual_type == expected_type and actual_count == expected_count:
                print(f"✅ Test PASSED - Type: {actual_type}, Count: {actual_count}")
            else:
                print(f"❌ Test FAILED - Expected: {expected_type}/{expected_count}, Got: {actual_type}/{actual_count}")
            
            # Show detected entities
            if classification_result.detected_dates:
                print(f"📅 Detected Dates: {', '.join(classification_result.detected_dates)}")
            if classification_result.detected_passengers:
                print(f"👤 Detected Passengers: {', '.join(classification_result.detected_passengers)}")
            if classification_result.detected_locations:
                print(f"📍 Detected Locations: {', '.join(classification_result.detected_locations)}")
            
            print(f"🧠 Reasoning: {classification_result.reasoning}")
            
        except Exception as e:
            print(f"❌ Test failed with error: {str(e)}")
            import traceback
            traceback.print_exc()
    
    print(f"\n📊 SUMMARY:")
    print(f"   Total Tests: {len(test_samples)}")
    print(f"   Total Cost: ${total_cost:.4f}")
    print(f"   Average Cost per Test: ${total_cost/len(test_samples):.4f}")
    
    # Show agent performance stats
    stats = agent.get_performance_stats()
    print(f"   Agent Stats:")
    print(f"     Total Calls: {stats['total_calls']}")
    print(f"     Average Time: {stats['average_processing_time']:.2f}s")
    print(f"     Average Cost: ${stats['average_cost']:.4f}")
    
    print("\n✅ Classification agent test completed!")

if __name__ == "__main__":
    test_classification_agent()