#!/usr/bin/env python3
"""
Test script for enhanced classification agent with table detection
"""

import logging
from gemma_classification_agent import GemmaClassificationAgent

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_table_classification():
    """Test classification agent with table/multi-booking scenarios"""
    
    print("🧪 Testing Enhanced Classification Agent with Table Detection...")
    
    # Test cases that simulate your actual multi-booking table data
    test_cases = [
        {
            "name": "Multi-booking Table (Cab 1-4 columns)",
            "content": """
            [File: Screenshot 2025-09-16 004941.png, Method: enhanced_multi_booking_textract]

            TABLE EXTRACTION RESULTS (4 bookings found):

            Booking 1:
            - Passenger: Jayasheel Bhansali (7001682596)
            - Company: LTPL (Lendingkart Technologies Private Limited)
            - Date: 19-Sep-25
            - Time: 8:30 PM
            - Vehicle: CRYSTA
            - From: Bangalore Airport T-2
            - To: ITC Windsor Bangalore
            - Flight: AI-2641

            Booking 2:
            - Passenger: Jayasheel Bhansali (7001682596)
            - Company: LTPL (Lendingkart Technologies Private Limited)
            - Date: 20 Sep 2025 & 21 Sep 2025
            - Time: 10:00 AM
            - Vehicle: CRYSTA
            - From: ITC Windsor Bangalore
            - To: Full Day
            - Flight: N/A

            Booking 3:
            - Passenger: Jayasheel Bhansali (7001682596)
            - Company: LTPL (Lendingkart Technologies Private Limited)
            - Date: 21-Sep-25
            - Time: 7:30 PM
            - Vehicle: CRYSTA
            - From: Mumbai Airport Terminal 2
            - To: JW Marriott Mumbai Sahar
            - Flight: AI 2854

            Booking 4:
            - Passenger: Jayasheel Bhansali (7001682596)
            - Company: LTPL (Lendingkart Technologies Private Limited)
            - Date: 22 Sep 2025 to 25 Sep 2025
            - Time: 8:00 AM
            - Vehicle: CRYSTA
            - From: JW Marriott Mumbai Sahar
            - To: Office .Silver Utopia,Cardinal gracious Road, chakala andheri east...... FULL DAY

            Original processing method: enhanced_multi_booking_extraction
            """,
            "expected": "multiple",
            "expected_count": 4
        },
        {
            "name": "Table Headers (Cab 1, Cab 2, Cab 3, Cab 4)",
            "content": """
            Cab Booking Format | Cab 1 | Cab 2 | Cab 3 | Cab 4
            Name of Employee: Jayasheel Bhansali | Jayasheel Bhansali | Jayasheel Bhansali | Jayasheel Bhansali
            Contact Number: 7001682596 | 7001682596 | 7001682596 | 7001682596
            City: Bangalore | Bangalore | Mumbai | Mumbai
            Date of Travel: 19-Sep-25 | 20 Sep 2025 & 21 Sep 2025 | 21-Sep-25 | 22 Sep 2025 to 25 Sep 2025
            Enhanced multi-booking processing completed: Found 4 bookings from tables.
            """,
            "expected": "multiple",
            "expected_count": 4
        },
        {
            "name": "Regular single booking (control test)",
            "content": """
            Dear Team,
            Please arrange a car for Mr. Rajesh (9876543210) for airport drop.
            Date: 25th December 2024
            Time: 9 AM
            Vehicle: Dzire
            From: Office
            To: Airport
            Flight: AI123
            Thanks!
            """,
            "expected": "single",
            "expected_count": 1
        }
    ]
    
    # Initialize agent (will use rule-based classification since no real API key)
    agent = GemmaClassificationAgent()
    
    print(f"\n📊 Running {len(test_cases)} test cases...\n")
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"Test {i}: {test_case['name']}")
        print(f"Expected: {test_case['expected']} ({test_case['expected_count']} bookings)")
        
        try:
            result = agent.classify_content(test_case['content'], source_type="image_table")
            
            print(f"Result: {result.booking_type.value} ({result.booking_count} booking(s))")
            print(f"Confidence: {result.confidence_score:.1%}")
            print(f"Duty Type: {result.detected_duty_type.value}")
            print(f"Reasoning: {result.reasoning}")
            
            # Check if result matches expectation
            type_match = result.booking_type.value == test_case['expected']
            count_match = result.booking_count == test_case['expected_count']
            
            if type_match and count_match:
                status = "✅ PASS"
            elif type_match:
                status = f"⚠️  PARTIAL (type correct, count expected {test_case['expected_count']}, got {result.booking_count})"
            else:
                status = f"❌ FAIL (expected {test_case['expected']}, got {result.booking_type.value})"
            
            print(f"Status: {status}")
            
        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
        
        print("-" * 80)
    
    print("\n🎯 Summary:")
    print("The enhanced classification agent should now properly detect multi-booking table structures!")
    print("This will fix the issue where table data was being classified as 'single' instead of 'multiple'.")

if __name__ == "__main__":
    test_table_classification()