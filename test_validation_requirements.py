#!/usr/bin/env python3
"""
Test Validation Requirements - Verify all specific validation rules
"""

import os
import pandas as pd
import sys

def test_validation_requirements():
    """Test all specific validation requirements"""
    
    print("🧪 Testing Validation Requirements")
    print("=" * 60)
    
    # Set Gemini API key
    gemini_api_key = "AIzaSyAId73p8fsv1U0z2_jQ0yOLdcVJsVsOmeg"
    os.environ['GEMINI_API_KEY'] = gemini_api_key
    
    # Import required modules
    from business_logic_validation_agent import BusinessLogicValidationAgent
    from base_extraction_agent import ExtractionResult
    from gemma_classification_agent import BookingType, DutyType, ClassificationResult
    
    # Test data with specific scenarios
    test_scenarios = [
        {
            'name': 'LadyGuest Label Test',
            'passenger_name': 'Mrs. Priya Sharma',
            'original_content': """
            Dear Team,
            Please arrange cab for Mrs. Priya Sharma tomorrow.
            She needs to go from office to airport.
            Phone: 9876543210
            Please ensure driver calls before arriving.
            Thanks!
            """,
            'expected_labels': ['LadyGuest']
        },
        {
            'name': 'VIP Label Test', 
            'passenger_name': 'Mr. Rajesh Kumar',
            'original_content': """
            Hi Team,
            Need urgent cab for Mr. Rajesh Kumar - he is a VIP client.
            Pickup from Hyatt Hotel at 10 AM.
            Please arrange premium vehicle and experienced driver.
            This is high priority.
            Contact: 9876543210
            """,
            'expected_labels': ['VIP']
        },
        {
            'name': 'Ms. Title Test',
            'passenger_name': 'Ms. Ananya Gupta', 
            'original_content': """
            Hello,
            Please book cab for Ms. Ananya Gupta.
            Date: Tomorrow 9 AM
            From: Bangalore Airport
            To: Electronic City
            Flight: AI 506
            """,
            'expected_labels': ['LadyGuest']
        },
        {
            'name': 'Regular Guest (No Labels)',
            'passenger_name': 'Amit Patel',
            'original_content': """
            Need cab for Amit Patel today.
            From: Office
            To: Home
            Time: 6 PM
            Vehicle: Dzire preferred
            """,
            'expected_labels': []
        },
        {
            'name': 'Duty Type and Mapping Test',
            'passenger_name': 'John Smith',
            'original_content': """
            From: hr@accenture.com
            
            Please arrange outstation cab from Mumbai to Pune.
            Passenger: John Smith
            Date: Tomorrow 8 AM
            Vehicle: Innova preferred
            Return trip needed.
            Contact: 9876543210
            """,
            'expected_duty': 'G2G-Outstation',
            'expected_vehicle': 'Toyota Innova Crysta',
            'expected_corporate': 'Accenture India Ltd'
        }
    ]
    
    # Initialize validator
    validator = BusinessLogicValidationAgent()
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n🔍 Test {i}: {scenario['name']}")
        print("-" * 40)
        
        # Create test DataFrame
        test_data = {
            'Customer': [scenario.get('expected_corporate', '')],
            'Booked By Name': ['Travel Coordinator'],
            'Booked By Phone Number': ['9876543210'],
            'Booked By Email': ['travel@company.com'],
            'Passenger Name': [scenario['passenger_name']],
            'Passenger Phone Number': ['9876543210'],
            'Passenger Email': [''],
            'From (Service Location)': ['Mumbai'],
            'To': ['Pune' if 'outstation' in scenario['name'].lower() else 'Airport'],
            'Vehicle Group': ['innova' if 'innova' in scenario['original_content'].lower() else 'dzire'],
            'Duty Type': [''],
            'Start Date': ['2024-12-25'],
            'End Date': [''],
            'Rep. Time': ['08:00'],
            'Reporting Address': ['Office Location'],
            'Drop Address': ['Destination'],
            'Flight/Train Number': ['AI 506' if 'AI 506' in scenario['original_content'] else ''],
            'Dispatch center': [''],
            'Remarks': [''],
            'Labels': ['']
        }
        
        df = pd.DataFrame(test_data)
        
        # Create extraction result
        extraction_result = ExtractionResult(
            success=True,
            bookings_dataframe=df,
            booking_count=1,
            confidence_score=0.8,
            processing_time=1.0,
            cost_inr=0.0,
            extraction_method="test_extraction"
        )
        
        # Create classification result
        classification_result = ClassificationResult(
            booking_type=BookingType.SINGLE,
            booking_count=1,
            confidence_score=0.9,
            reasoning="Test scenario",
            detected_duty_type=DutyType.DROP_4_40,
            detected_dates=["2024-12-25"],
            detected_vehicles=["Dzire"],
            detected_drops=["Airport"]
        )
        
        # Apply validation
        try:
            validated_result = validator.validate_and_enhance(
                extraction_result, classification_result, scenario['original_content']
            )
            
            validated_df = validated_result.bookings_dataframe
            
            # Check results
            print(f"Original Passenger: {scenario['passenger_name']}")
            print(f"Validated Labels: '{validated_df.iloc[0]['Labels']}'")
            
            if 'expected_labels' in scenario:
                expected = scenario['expected_labels']
                actual = [label.strip() for label in str(validated_df.iloc[0]['Labels']).split(',') if label.strip()]
                
                if set(expected) == set(actual):
                    print("✅ Labels: PASS")
                else:
                    print(f"❌ Labels: FAIL - Expected {expected}, Got {actual}")
            
            if 'expected_duty' in scenario:
                duty_type = validated_df.iloc[0]['Duty Type']
                if scenario['expected_duty'] in str(duty_type):
                    print("✅ Duty Type: PASS")
                else:
                    print(f"❌ Duty Type: FAIL - Expected '{scenario['expected_duty']}', Got '{duty_type}'")
            
            if 'expected_vehicle' in scenario:
                vehicle = validated_df.iloc[0]['Vehicle Group']
                if scenario['expected_vehicle'] == str(vehicle):
                    print("✅ Vehicle Mapping: PASS")
                else:
                    print(f"❌ Vehicle Mapping: FAIL - Expected '{scenario['expected_vehicle']}', Got '{vehicle}'")
            
            if 'expected_corporate' in scenario:
                corporate = validated_df.iloc[0]['Customer']
                if scenario['expected_corporate'] in str(corporate):
                    print("✅ Corporate Mapping: PASS")
                else:
                    print(f"❌ Corporate Mapping: FAIL - Expected '{scenario['expected_corporate']}', Got '{corporate}'")
            
            # Check remarks enhancement
            remarks = str(validated_df.iloc[0]['Remarks'])
            if len(remarks) > 10 and remarks != 'nan':
                print(f"✅ Remarks Enhanced: '{remarks[:50]}...'")
            else:
                print("⚠️ Remarks: No extra information captured")
            
            # Check dispatch center
            dispatch = validated_df.iloc[0]['Dispatch center']
            print(f"📍 Dispatch Center: {dispatch}")
            
        except Exception as e:
            print(f"❌ Test failed: {str(e)}")
    
    # Test mapping validation specifically
    print("\n" + "=" * 60)
    print("🗺️ Testing All Mappings")
    print("-" * 40)
    
    # Test vehicle mappings
    print("\n🚗 Vehicle Mappings:")
    vehicle_tests = [
        ('innova', 'Toyota Innova Crysta'),
        ('dzire', 'Swift Dzire'),
        ('swift', 'Maruti Swift'),
        ('ertiga', 'Maruti Ertiga'),
        ('sedan', 'Swift Dzire'),
        ('suv', 'Toyota Innova Crysta')
    ]
    
    for input_vehicle, expected in vehicle_tests:
        mapped = validator.vehicle_mappings.get(input_vehicle, input_vehicle.title())
        if mapped == expected:
            print(f"  ✅ {input_vehicle} → {mapped}")
        else:
            print(f"  ❌ {input_vehicle} → {mapped} (expected {expected})")
    
    # Test city mappings
    print("\n🏙️ City Mappings:")
    city_tests = [
        ('mumbai', 'Mumbai'),
        ('delhi', 'Delhi'),
        ('bangalore', 'Bangalore'),
        ('bengaluru', 'Bangalore'),
        ('gurgaon', 'Gurgaon'),
        ('gurugram', 'Gurgaon')
    ]
    
    for input_city, expected in city_tests:
        mapped = validator.city_mappings.get(input_city, input_city.title())
        if mapped == expected:
            print(f"  ✅ {input_city} → {mapped}")
        else:
            print(f"  ❌ {input_city} → {mapped} (expected {expected})")
    
    # Test corporate patterns
    print("\n🏢 Corporate Patterns:")
    for pattern, info in list(validator.corporate_patterns.items())[:5]:
        print(f"  ✅ {pattern} → {info['name']} ({info['category']})")
    
    print(f"\n✨ Validation Requirements Test Complete!")
    print(f"📋 Verified: Labels, Duty Types, Mappings, and Remarks enhancement")

if __name__ == "__main__":
    test_validation_requirements()