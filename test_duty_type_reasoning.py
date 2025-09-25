#!/usr/bin/env python3
"""
Test script to verify duty type reasoning functionality
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the current directory to path
sys.path.append('.')

def test_duty_type_reasoning():
    """Test duty type reasoning with sample emails"""
    
    try:
        from car_rental_ai_agent import CarRentalAIAgent
        print("✅ Successfully imported CarRentalAIAgent")
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
        agent = CarRentalAIAgent()
        print("✅ Agent initialized successfully")
        print(f"   Corporate mappings loaded: {len(agent.corporate_mappings)} companies")
    except Exception as e:
        print(f"❌ Agent initialization failed: {e}")
        return
    
    # Test samples
    test_samples = [
        {
            "name": "RELIANCE Corporate - Airport Transfer (should be P-04HR 40KMS)",
            "content": """
From: booking@reliance.com

Subject: Car Booking Request

Please book a car for airport transfer:
- Employee: Vikram Singh
- Contact: 8765432109  
- Date: tomorrow
- Pickup: Bandra, Mumbai
- Drop: Mumbai Airport
- Time: 4:30 AM
- Vehicle: Dzire

This is for Reliance corporate booking.
            """.strip()
        },
        {
            "name": "Local Disposal (should be P-08HR 80KMS)",
            "content": """
Dear Team,

Please arrange a car for local use:
- Passenger: John Smith (9876543210)
- Date: 25th December 2024
- Pickup: Andheri West, Mumbai at 9:00 AM
- Usage: At disposal for whole day
- Vehicle: Innova

Thanks!
            """.strip()
        },
        {
            "name": "Outstation Trip Mumbai to Pune (should be P-Outstation 250KMS)",
            "content": """
Car needed for outstation trip:
- Passenger: Rajesh Patel (9123456789)
- Route: Mumbai to Pune
- Date: Tomorrow
- Pickup: 6:00 AM from Andheri
- Vehicle: Innova

Business trip to Pune.
            """.strip()
        }
    ]
    
    print("\n" + "="*80)
    print("TESTING DUTY TYPE REASONING SYSTEM")
    print("="*80)
    
    for i, sample in enumerate(test_samples, 1):
        print(f"\n🧪 Test {i}: {sample['name']}")
        print("="*60)
        
        try:
            # Process with agent
            booking = agent.extract_booking_data(sample['content'])
            
            # Display key results
            print(f"📊 EXTRACTED RESULTS:")
            print(f"   Corporate: {booking.corporate}")
            print(f"   Corporate Duty Type: {booking.corporate_duty_type}")
            print(f"   Duty Type: {booking.duty_type}")
            print(f"   From: {booking.from_location}")
            print(f"   To: {booking.to_location}")
            print(f"   Confidence: {booking.confidence_score or 0:.1%}")
            
            # Show reasoning if available
            if hasattr(booking, 'duty_type_reasoning') and booking.duty_type_reasoning:
                print(f"\n🎯 DUTY TYPE REASONING:")
                print("-" * 40)
                print(booking.duty_type_reasoning)
                print("-" * 40)
            else:
                print(f"\n❌ NO REASONING AVAILABLE")
                print("   duty_type_reasoning field is missing or empty")
            
        except Exception as e:
            print(f"❌ Test failed with error: {str(e)}")
            import traceback
            traceback.print_exc()
        
        print("\n" + "-"*60)
    
    print(f"\n✅ Duty type reasoning test completed!")

if __name__ == "__main__":
    test_duty_type_reasoning()