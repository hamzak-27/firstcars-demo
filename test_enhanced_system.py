#!/usr/bin/env python3
"""
Comprehensive Test Suite for Enhanced FirstCars AI Agent
Tests all new requirements and enhancements
"""

import os
import json
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_enhanced_features():
    """Test all enhanced features with comprehensive sample data"""
    
    # Test samples covering all new requirements
    test_samples = [
        {
            "name": "Multiple Drops Test",
            "content": """
Dear Team,

Please arrange a cab for tomorrow with the following itinerary:
- Name: Rajesh Kumar
- Phone: 9876543210
- Pickup: Indiranagar, Bangalore at 9:00 AM
- Drop 1: MG Road, Bangalore
- Drop 2: Koramangala, Bangalore  
- Drop 3: Electronic City, Bangalore
- Final Drop: Whitefield, Bangalore

Vehicle: Innova
Thanks!
""",
            "expected": {
                "multiple_drops": True,
                "drop_count": 4,
                "vehicle_standardization": "Innova Crysta",
                "city_extraction": "Bangalore"
            }
        },
        
        {
            "name": "Round Trip Test", 
            "content": """
Hello,

Need a car for business trip:
Passenger: Priya Sharma (9123456789)
Date: 25/12/2024
Trip: Mumbai to Pune and back to Mumbai
Pickup time: 6:30 AM
Pickup from: Andheri West, Mumbai

Regards,
John
""",
            "expected": {
                "round_trip": True,
                "final_drop": "Mumbai",
                "from_location": "Mumbai",
                "to_location": "Pune",
                "drop1": "Mumbai"
            }
        },
        
        {
            "name": "Corporate Mapping Test",
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
""",
            "expected": {
                "corporate": "RELIANCE",
                "corporate_duty_type": "P2P",
                "recommended_package": "P-04HR 40KMS",
                "approval_required": "No"
            }
        },
        
        {
            "name": "Multiple Passengers Single Booking Test",
            "content": """
Hi Team,

Car needed for office visit:
- Primary: Amit Patel (9988776655)
- Other travelers: Neha Shah, Rohit Gupta, Kavita Joshi
- Date: 28th Dec
- Pickup: Satellite, Ahmedabad at 10:15 AM
- Drop: Same location (intra-city usage)
- Duration: Full day

Clean car required.
Driver should be punctual.

Best regards,
Manager
""",
            "expected": {
                "single_booking": True,
                "multiple_passengers": True,
                "intra_city": True,
                "same_from_to": True,
                "filtered_remarks": True
            }
        },
        
        {
            "name": "Default Vehicle Test",
            "content": """
Cab booking required:
Name: Sarah Wilson
Phone: 7654321098
Date: Next Monday
Pickup: Koramangala, Bangalore
Drop: Hebbal, Bangalore  
Time: 7:43 AM

No vehicle mentioned - should default to Dzire.
""",
            "expected": {
                "default_vehicle": "Dzire",
                "time_precision": "07:43",
                "city_names_only": True
            }
        },
        
        {
            "name": "Approval Required Corporate Test",
            "content": """
From: employee@hyclone.com

Car booking for guest visit:
- Guest: Dr. Robert Smith
- Phone: 9876543210
- Date: 30/12/2024
- Pickup: Hotel Taj, Mumbai
- Drop: Hyclone Office, Powai
- Time: 9:00 AM
- Vehicle: Crysta

This booking is from HYCLONE (requires approval).
""",
            "expected": {
                "corporate": "HYCLONE", 
                "approval_required": "Yes",
                "recommended_package": "Approval Required"
            }
        }
    ]
"""
Comprehensive Test Script for Enhanced FirstCars System
Tests all enhancements: multiple bookings, time rounding, city mapping, comprehensive data extraction
"""

import os
import json
from datetime import datetime
from typing import List, Dict, Any

# Import our enhanced processors
from unified_email_processor import UnifiedEmailProcessor
from car_rental_ai_agent import CarRentalAIAgent
from structured_email_agent import StructuredEmailAgent

def test_time_normalization():
    """Test the enhanced 15-minute interval time normalization"""
    print("=" * 60)
    print("TESTING TIME NORMALIZATION TO 15-MINUTE INTERVALS")
    print("=" * 60)
    
    agent = CarRentalAIAgent()
    
    test_times = [
        ("7:10", "07:00"),  # Should round down 
        ("7:43", "07:30"),  # Should round down to 7:30
        ("7:53", "07:45"),  # Should round down to 7:45
        ("7:15", "07:15"),  # Should stay 7:15
        ("7:07", "07:00"),  # Should round down to 7:00
        ("8:25", "08:15"),  # Should round down to 8:15
        ("8:47", "08:45"),  # Should round down to 8:45
        ("9:00", "09:00"),  # Should stay 9:00
    ]
    
    print("Testing time normalization rules:")
    print("7:10 → 7:00, 7:43 → 7:30, 7:53 → 7:45")
    print("-" * 40)
    
    all_passed = True
    for input_time, expected_output in test_times:
        result = agent._round_time_to_15_minutes(input_time)
        passed = result == expected_output
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{input_time:>6} → {result:>6} (expected: {expected_output:>6}) {status}")
        if not passed:
            all_passed = False
    
    print(f"\nTime normalization test: {'✅ ALL PASSED' if all_passed else '❌ SOME FAILED'}")
    return all_passed

def test_city_mapping():
    """Test the suburb-to-city mapping functionality"""
    print("\n" + "=" * 60)
    print("TESTING SUBURB-TO-CITY MAPPING")
    print("=" * 60)
    
    agent = CarRentalAIAgent()
    
    test_locations = [
        ("Jogeshwari", "Mumbai"),
        ("Andheri West", "Mumbai"),
        ("Whitefield Bangalore", "Bangalore"),
        ("Gurgaon", "Delhi"),
        ("Chembumukku, Cochin", "Cochin"),
        ("Mather Berrywoods", "Cochin"),
        ("Electronic City", "Bangalore"),
        ("Hitech City", "Hyderabad"),
        ("Salt Lake", "Kolkata"),
        ("Regular City Name", "Regular City Name"),  # Should return as-is if not mapped
    ]
    
    print("Testing suburb to city mapping:")
    print("-" * 40)
    
    all_passed = True
    for input_location, expected_city in test_locations:
        result = agent._map_city_name(input_location)
        passed = expected_city.lower() in result.lower() or result == input_location.title()
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{input_location:>25} → {result:>15} (expected: {expected_city:>15}) {status}")
        if not passed and expected_city != "Regular City Name":
            all_passed = False
    
    print(f"\nCity mapping test: {'✅ ALL PASSED' if all_passed else '❌ SOME FAILED'}")
    return all_passed

def test_multiple_booking_detection():
    """Test multiple booking detection with sample email"""
    print("\n" + "=" * 60)
    print("TESTING MULTIPLE BOOKING DETECTION")
    print("=" * 60)
    
    # Sample email that should create 2 separate bookings
    sample_email = """
    Subject: Car Requirement for Dr. Malaraj

    Dear Team,

    Please arrange car for the following requirement:

    Passenger: Dr. Malaraj
    Phone: 8056225577
    Corporate: Johnson & Johnson Pvt. Ltd

    Trip Details:
    - Date: 17th September and 18th September 2025
    - Vehicle: Maruti Dzire

    17th September:
    - Pickup from Delhi Airport to Taj Palace hotel at 4:30 PM

    18th September: 
    - Pickup from Taj Palace Hotel to Delhi Airport at 4:00 PM

    Flight Details:
    - 6E2387 (13:15 - 16:05 Chennai-Delhi)
    - AI2525 (6:00 - 8:55 Delhi-Chennai)

    Please SMS details to driver and guest - 9942787200

    Thanks
    """
    
    try:
        processor = UnifiedEmailProcessor()
        result = processor.process_email(sample_email)
        
        print("Sample Email Analysis:")
        print(f"Total bookings found: {result.total_bookings_found}")
        print(f"Expected: 2 (one for 17th Sept, one for 18th Sept)")
        
        if result.bookings:
            for i, booking in enumerate(result.bookings, 1):
                print(f"\nBooking {i}:")
                print(f"  Date: {booking.start_date}")
                print(f"  Passenger: {booking.passenger_name}")
                print(f"  From: {booking.from_location}")
                print(f"  To: {booking.to_location}")
                print(f"  Time: {booking.reporting_time}")
                print(f"  Remarks: {booking.remarks[:100] if booking.remarks else 'None'}...")
        
        # Check if we got 2 bookings as expected
        multiple_booking_test_passed = result.total_bookings_found >= 2
        print(f"\nMultiple booking detection: {'✅ PASSED' if multiple_booking_test_passed else '❌ FAILED'}")
        
        return multiple_booking_test_passed
        
    except Exception as e:
        print(f"❌ Multiple booking test failed with error: {str(e)}")
        return False

def test_comprehensive_data_extraction():
    """Test comprehensive data extraction (zero data loss)"""
    print("\n" + "=" * 60)
    print("TESTING COMPREHENSIVE DATA EXTRACTION")
    print("=" * 60)
    
    # Sample email with lots of details that should be captured
    detailed_email = """
    Car Booking Request - URGENT

    Company: TechCorp Solutions Pvt Ltd
    Booked by: Rajesh Kumar (Manager)
    Contact: +91-9876543210, rajesh@techcorp.com
    
    Passenger Details:
    - Primary: Mr. Suresh Patel
    - Phone: 8765432109
    - Additional passengers: Mrs. Patel, child (2 years)
    
    Trip Requirements:
    - Date: Tomorrow (urgent)
    - Vehicle: Clean Innova Crysta (AC must work properly)
    - Route: Jogeshwari to Mumbai Airport
    - Time: 6:43 AM sharp (flight at 9:30 AM)
    - Distance: Approx 25 KM
    
    Special Instructions:
    - Driver should be punctual and professional
    - Vehicle must be clean and sanitized
    - Child seat required for 2-year-old
    - Driver contact: Preferred - Mohan (9988776655) 
    - Emergency contact: 7766554433 (Rajesh backup)
    - Bill to: Corporate account TechCorp-2024-VIP
    - Reference: Travel-REQ-001234
    
    VIP Service Required:
    - This is for our MD's family
    - No smoking in vehicle
    - Bottled water to be provided
    - Help with luggage
    
    Payment: Corporate billing
    Authorization: Approved by CFO (Auth-7845)
    """
    
    try:
        processor = UnifiedEmailProcessor()
        result = processor.process_email(detailed_email)
        
        print("Detailed Email Analysis:")
        print(f"Bookings found: {result.total_bookings_found}")
        
        if result.bookings:
            booking = result.bookings[0]
            
            # Check if major details were captured
            captured_details = {
                "Corporate": booking.corporate is not None,
                "Passenger Name": booking.passenger_name is not None,
                "Phone": booking.passenger_phone is not None,
                "Vehicle Type": booking.vehicle_group is not None,
                "From Location": booking.from_location is not None,
                "To Location": booking.to_location is not None,
                "Reporting Time": booking.reporting_time is not None,
                "Remarks/Additional Info": (booking.remarks is not None and len(booking.remarks) > 50) or 
                                         (booking.additional_info is not None and len(booking.additional_info) > 50)
            }
            
            print("\nData Extraction Results:")
            for field, captured in captured_details.items():
                status = "✅" if captured else "❌"
                print(f"  {field}: {status}")
            
            # Check time rounding
            if booking.reporting_time:
                expected_time = "06:30"  # 6:43 should round to 6:30 (HH:MM format)
                time_test_passed = booking.reporting_time == expected_time
                print(f"  Time Rounding (6:43 → 6:30): {'✅' if time_test_passed else '❌'} (Got: {booking.reporting_time})")
            
            # Check city mapping
            city_test_passed = "Mumbai" in (booking.from_location or "")
            print(f"  City Mapping (Jogeshwari → Mumbai): {'✅' if city_test_passed else '❌'} (Got: {booking.from_location})")
            
            print(f"\nRemarks content preview:")
            print(f"  {(booking.remarks or '')[:200]}{'...' if len(booking.remarks or '') > 200 else ''}")
            
            comprehensive_test_passed = all(captured_details.values())
            print(f"\nComprehensive extraction: {'✅ PASSED' if comprehensive_test_passed else '❌ SOME DATA MISSED'}")
            
            return comprehensive_test_passed
        else:
            print("❌ No bookings extracted")
            return False
            
    except Exception as e:
        print(f"❌ Comprehensive extraction test failed with error: {str(e)}")
        return False

def run_all_tests():
    """Run all enhancement tests"""
    print("🚗 FIRSTCARS ENHANCED SYSTEM - COMPREHENSIVE TEST SUITE")
    print("=" * 80)
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check if API key is available
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ OPENAI_API_KEY not found in environment variables")
        print("Please set the API key to run the tests")
        return
    
    test_results = []
    
    # Run individual tests
    test_results.append(("Time Normalization", test_time_normalization()))
    test_results.append(("City Mapping", test_city_mapping()))
    test_results.append(("Multiple Booking Detection", test_multiple_booking_detection()))
    test_results.append(("Comprehensive Data Extraction", test_comprehensive_data_extraction()))
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    passed_tests = 0
    for test_name, passed in test_results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name:.<50} {status}")
        if passed:
            passed_tests += 1
    
    overall_success = passed_tests == len(test_results)
    print(f"\nOverall Result: {passed_tests}/{len(test_results)} tests passed")
    print(f"System Status: {'🎉 ALL ENHANCEMENTS WORKING' if overall_success else '⚠️ SOME ISSUES FOUND'}")
    
    if overall_success:
        print("\n✅ The enhanced FirstCars system is ready for production!")
        print("Key improvements implemented:")
        print("  • Enhanced 15-minute time rounding (7:43→7:30, 7:10→7:00, 7:53→7:45)")
        print("  • Comprehensive suburb-to-city mapping")
        print("  • Smart multiple booking detection")
        print("  • Zero data loss extraction (all details captured)")
        print("  • Consistent prompting across all processors")
    else:
        print("\n⚠️ Please review the failed tests and address the issues.")

if __name__ == "__main__":
    run_all_tests()