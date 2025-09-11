"""
Test script for the updated car rental AI agent with city/vehicle mappings and time rounding
"""

import os
from car_rental_ai_agent import CarRentalAIAgent

# Sample email for testing
sample_email = """
Subject: Cab Booking Request - Urgent

Dear Team,

Please arrange cab for client meeting tomorrow.

Details:
- Passenger: John Smith
- Phone: +91-9876543210
- From: Mumbai Airport Terminal 1
- To: Business Hotel Andheri
- Date: 15th September 2025
- Time: 8:35 AM
- Vehicle: Innova Crysta
- Flight: AI 101

Please ensure the car is clean.

Thanks,
Manager
"""

def test_updated_agent():
    """Test the updated agent with new features"""
    print("🧪 Testing Updated Car Rental AI Agent")
    print("=" * 50)
    
    # Check if OpenAI key is available
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ OPENAI_API_KEY not found in environment variables")
        print("Please set your OpenAI API key and try again.")
        return
    
    try:
        # Initialize agent
        print("🔧 Initializing AI agent...")
        agent = CarRentalAIAgent()
        
        # Test extraction
        print("🤖 Extracting booking data...")
        result = agent.extract_booking_data(sample_email)
        
        # Display results
        print("\n📊 EXTRACTION RESULTS:")
        print("=" * 30)
        
        print(f"Passenger Name: {result.passenger_name}")
        print(f"Phone: {result.passenger_phone}")
        print(f"From (mapped): {result.from_location}")
        print(f"To (mapped): {result.to_location}")
        print(f"Vehicle (mapped): {result.vehicle_group}")
        print(f"Date: {result.start_date}")
        print(f"Time (rounded): {result.reporting_time}")
        print(f"Additional Info: {result.additional_info}")
        print(f"Confidence: {result.confidence_score:.2f}")
        
        print("\n✅ Test completed successfully!")
        
        # Test time rounding specifically
        print("\n⏰ TESTING TIME ROUNDING:")
        print("=" * 30)
        
        test_times = ["8:35", "8:43", "8:45", "8:52", "7:07", "9:22"]
        for time_str in test_times:
            rounded = agent._round_time_to_15_minutes(time_str)
            print(f"{time_str} → {rounded}")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    test_updated_agent()
