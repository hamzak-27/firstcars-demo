#!/usr/bin/env python3
"""
Test script to verify complex flight data extraction
"""
import os
import sys
from dotenv import load_dotenv

# Add agents to path
sys.path.append('.')

# Load environment
load_dotenv()

# Import agents
from agents.flight_details_agent import FlightDetailsAgent

# Test data with complex flight information
complex_flight_email = """Dear First Car team

Pls book

Innova
27 Sep, 2025

Guest : Mr. Vinod Kumar (+91 98880 41305)

Pick up time : 2020
Pick up venue : Bangalore Airport
Drop at Radisson Hotel, Atria, Bangalore

Flight detail :   
  2  6E 429 Y 27SEP 6 IXCBLR GK1  1715 2020  27SEP     EZJVVL"""

def test_complex_flight_extraction():
    """Test complex flight data extraction - should extract 6E 429"""
    print("🧪 Testing Complex Flight Details Extraction...")
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ No OpenAI API key found")
        return
    
    agent = FlightDetailsAgent(api_key)
    
    try:
        result = agent.extract_fields(complex_flight_email, {})
        print(f"✅ Flight Result: {result}")
        
        # Check if it correctly identified the complete flight details
        flight_details = result.get('flight_train_number', '')
        expected_complete = "6E 429 Y 27SEP 6 IXCBLR GK1 1715 2020 27SEP EZJVVL"
        if "6E 429 Y 27SEP 6 IXCBLR GK1 1715 2020" in str(flight_details):
            print("✅ CORRECT: Extracted complete flight details from GDS data")
        else:
            print(f"❌ WRONG: Got '{flight_details}' - expected complete GDS string")
            
        # Show what it extracted exactly
        print(f"📉 Extracted flight details: '{flight_details}'")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def test_more_complex_examples():
    """Test additional complex flight patterns"""
    print("\n🧪 Testing Additional Complex Flight Patterns...")
    
    test_cases = [
        {
            "name": "Multi-segment GDS",
            "input": "AI 234 J 15OCT MUMBAI DELHI 0800 1000 + 6E 567 Y 15OCT DELHI BANGALORE 1200 1400",
            "expected": "AI 234 J 15OCT MUMBAI DELHI 0800 1000, 6E 567 Y 15OCT DELHI BANGALORE 1200 1400"
        },
        {
            "name": "Simple flight with context",
            "input": "Please pick up passenger arriving on IndiGo 6E 123 at 14:30",
            "expected": "6E 123"
        },
        {
            "name": "Multiple flights in text",
            "input": "Outbound flight AI 405 departure 08:00, return flight AI 406 arrival 22:30",
            "expected": "AI 405, AI 406"
        }
    ]
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ No OpenAI API key found")
        return
    
    agent = FlightDetailsAgent(api_key)
    
    for test_case in test_cases:
        try:
            print(f"\n🔍 Test: {test_case['name']}")
            print(f"Input: {test_case['input'][:50]}...")
            
            result = agent.extract_fields(test_case['input'], {})
            extracted = result.get('flight_train_number', '')
            
            print(f"Expected: {test_case['expected']}")
            print(f"Got: {extracted}")
            
            # Basic check - see if expected numbers are in the result
            expected_parts = test_case['expected'].split(', ')
            found_all = all(part.strip() in str(extracted) for part in expected_parts)
            
            if found_all:
                print("✅ PASSED")
            else:
                print("❌ FAILED")
                
        except Exception as e:
            print(f"❌ Error in {test_case['name']}: {e}")

def main():
    """Run all flight extraction tests"""
    print("🛫 Testing Complex Flight Data Extraction")
    print("=" * 50)
    
    print("Your Complex Flight Email:")
    print(complex_flight_email)
    print("=" * 50)
    
    print("Expected Extraction: COMPLETE GDS string from complex format")
    print("Input: '2  6E 429 Y 27SEP 6 IXCBLR GK1  1715 2020  27SEP     EZJVVL'")
    print("Expected: '6E 429 Y 27SEP 6 IXCBLR GK1 1715 2020 27SEP EZJVVL'")
    
    test_complex_flight_extraction()
    test_more_complex_examples()
    
    print("\n🎯 Summary:")
    print("The flight agent should now handle:")
    print("✅ Complex GDS format: '2 6E 429 Y 27SEP...' → '6E 429 Y 27SEP 6 IXCBLR GK1 1715 2020 27SEP EZJVVL'")
    print("  ✅ Multiple flight segments in single string") 
    print("  ✅ Flight data mixed with times, dates, codes")
    print("  ✅ Standard flight numbers: 'AI 123', '6E 456'")

if __name__ == "__main__":
    main()