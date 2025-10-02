#!/usr/bin/env python3
"""
Test script to verify the passenger vs booker detection and round trip fixes
"""
import os
import sys
import pandas as pd
from dotenv import load_dotenv

# Add agents to path
sys.path.append('.')

# Load environment
load_dotenv()

# Import agents
from agents.passenger_details_agent import PassengerDetailsAgent
from agents.location_time_agent import LocationTimeAgent
from agents.corporate_booker_agent import CorporateBookerAgent

# Test data simulating your booking table
test_booking_data = {
    "Name of the booker / requester": "MR. Sujoy Baidya-9870419192",
    "Booker's Landline and Mobile No. (Must)": "022-66591333",
    "Remarks": "",
    "Name of the user": "Mr. Rahul Waghmare", 
    "User's Contact no": "7506403838",
    "Car type": "Dezire",
    "Date / from - to": "Sep' 11, 2025f at 8:00 am",
    "Reporting place": "Add: Airoli bus depot, near railway station, Navi Mumbai - 400708",
    "Reporting time": "8:00 am",
    "Type of duty [Apt / Local / Outstation]": "Travel to Aurangabad and same day back.",
    "Billing Location (MUST)": "Asset Reconstruction Company (India) Limited (Arcil)\nThe Ruby, 10th Floor\n29, Senapati Bapat Marg\nDadar (West)\nMumbai – 400 028",
    "Billing Instructions – Credit Card / Bill To Company (BTC)": "BILLING TO-ARCIL-MUMBAI"
}

def test_passenger_extraction():
    """Test passenger details extraction - should get Rahul, not Sujoy"""
    print("🧪 Testing Passenger Details Agent...")
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ No OpenAI API key found")
        return
    
    agent = PassengerDetailsAgent(api_key)
    
    # Convert dict to string representation for the agent
    content = "\n".join([f"{k}: {v}" for k, v in test_booking_data.items()])
    
    try:
        result = agent.extract_fields(content, {})
        print(f"✅ Passenger Result: {result}")
        
        # Check if it correctly identified the passenger
        if result.get('passenger_name') == "Mr. Rahul Waghmare":
            print("✅ CORRECT: Identified Rahul Waghmare as passenger")
        else:
            print(f"❌ WRONG: Got '{result.get('passenger_name')}' instead of 'Mr. Rahul Waghmare'")
            
        if result.get('passenger_phone') == "7506403838":
            print("✅ CORRECT: Got passenger phone 7506403838")
        else:
            print(f"❌ WRONG: Got passenger phone '{result.get('passenger_phone')}' instead of '7506403838'")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def test_corporate_extraction():
    """Test corporate/booker details extraction - should get Sujoy as booker"""
    print("\n🧪 Testing Corporate Booker Agent...")
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ No OpenAI API key found")
        return
    
    agent = CorporateBookerAgent(api_key)
    
    # Convert dict to string representation for the agent
    content = "\n".join([f"{k}: {v}" for k, v in test_booking_data.items()])
    
    try:
        result = agent.extract_fields(content, {})
        print(f"✅ Corporate Result: {result}")
        
        # Check if it correctly identified the booker
        if "Sujoy Baidya" in str(result.get('booker_name', '')):
            print("✅ CORRECT: Identified Sujoy Baidya as booker")
        else:
            print(f"❌ WRONG: Got '{result.get('booker_name')}' instead of 'Sujoy Baidya'")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def test_location_extraction():
    """Test location extraction - should show round trip correctly"""
    print("\n🧪 Testing Location Time Agent...")
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ No OpenAI API key found")
        return
    
    agent = LocationTimeAgent(api_key)
    
    # Convert dict to string representation for the agent
    content = "\n".join([f"{k}: {v}" for k, v in test_booking_data.items()])
    
    try:
        result = agent.extract_fields(content, {})
        print(f"✅ Location Result: {result}")
        
        # Check if it correctly identified the round trip
        if result.get('from_location') == "Mumbai" or result.get('from_location') == "Navi Mumbai":
            print("✅ CORRECT: From location is Mumbai/Navi Mumbai")
        else:
            print(f"❌ WRONG: Got from_location '{result.get('from_location')}'")
            
        if result.get('to_location') == "Mumbai" or result.get('to_location') == "Navi Mumbai":
            print("✅ CORRECT: To location is Mumbai (round trip - same as from)")
        else:
            print(f"❌ WRONG: Got to_location '{result.get('to_location')}' instead of 'Mumbai' (round trip should have same from/to)")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    """Run all tests"""
    print("🎯 Testing Passenger vs Booker Detection & Round Trip Logic")
    print("=" * 60)
    print("Test Data:")
    for k, v in test_booking_data.items():
        if len(str(v)) > 50:
            print(f"  {k}: {str(v)[:47]}...")
        else:
            print(f"  {k}: {v}")
    print("=" * 60)
    
    test_passenger_extraction()
    test_corporate_extraction() 
    test_location_extraction()
    
    print("\n🎯 Summary:")
    print("Expected Results:")
    print("  ✅ Passenger: Mr. Rahul Waghmare (7506403838)")
    print("  ✅ Booker: MR. Sujoy Baidya (9870419192)")
    print("  ✅ From: Mumbai/Navi Mumbai")
    print("  ✅ To: Mumbai/Navi Mumbai (round trip - same base city!)")

if __name__ == "__main__":
    main()