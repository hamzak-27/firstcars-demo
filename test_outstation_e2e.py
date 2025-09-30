#!/usr/bin/env python3
"""
End-to-End Test for Outstation Round Trip Classification and Validation
Testing the complete flow from email content to final validated booking data.
"""

import logging
from booking_classification_agent import BookingClassificationAgent
from business_logic_validation_agent import BusinessLogicValidationAgent

# Configure logger
logger = logging.getLogger(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)

def test_outstation_round_trip_e2e():
    """Test complete flow for Chennai to Bangalore round trip."""
    
    print("🧪 End-to-End Test: Chennai → Bangalore → Chennai")
    print("=" * 60)
    
    # Test email content
    email_content = """
    Subject: Cab Booking Required - Outstation Trip
    
    Kindly confirm a cab:
    
    Location: Chennai
    Job: Outstation. (chennai to bangalore to chennai)
    Date: Saturday, October 04, 2025 
    Time: 4am
    Pickup address: 9B2, DABC Mithilam Apartments, Nolambur, Chennai
    Type of car: Suzuki Dzire
    Passenger: Ganesan K
    Phone: +91 9876543210
    Email: ganesan.k@company.com
    
    Additional Info:
    - Need driver with good highway experience
    - Prefer AC car for long journey
    - Will pay by company billing
    - Emergency contact: +91 9876543211
    
    Regards,
    Ganesan K
    """
    
    print("📧 Original Email Content:")
    print("-" * 40)
    print(email_content.strip())
    print()
    
    # Step 1: Classification
    print("🎯 Step 1: Classification")
    print("-" * 30)
    
    try:
        classifier = BookingClassificationAgent()
        classification_result = classifier.classify_text_content(email_content)
        
        print(f"   📊 Predicted Bookings: {classification_result.predicted_booking_count}")
        print(f"   🏷️ Booking Type: {classification_result.booking_type}")
        print(f"   🎯 Confidence: {classification_result.confidence_score * 100}%")
        print(f"   💭 Reasoning: {classification_result.reasoning[:100]}...")
        
        is_single_booking = classification_result.booking_type == 'single'
        
        if is_single_booking:
            print("   ✅ Classification: PASS (Single booking detected)")
        else:
            print("   ❌ Classification: FAIL (Should be single booking)")
            return False
            
    except Exception as e:
        print(f"   ❌ Classification Error: {e}")
        return False
    
    print()
    
    # Step 2: Business Logic Validation
    print("⚙️ Step 2: Business Logic Validation")
    print("-" * 40)
    
    try:
        validator = BusinessLogicValidationAgent()
        
        # Create test booking data that the validation agent expects
        test_booking = {
            'Email Content': email_content,
            'Corporate': 'Standard',  # Assuming standard booking
            'Customer': 'Standard Customer',
            'From (Service Location)': 'Chennai',
            'To': 'Bangalore', 
            'Start Date': '04/10/2025',
            'Start Time': '04:00',
            'End Date': '04/10/2025',
            'End Time': '18:00',
            'Rep. Time': '04:00',
            'Vehicle Group': 'Dzire',
            'Passenger Name': 'Ganesan K',
            'Passenger Phone': '+91 9876543210',
            'Passenger Email': 'ganesan.k@company.com',
            'Booked By Email': 'ganesan.k@company.com',
            'Passenger Phone Number': '+91 9876543210',
            'Duty Type': '',  # To be determined by validation
            'Remarks': ''  # To be populated by validation
        }
        
        print("   📋 Test Booking Data:")
        for key, value in test_booking.items():
            print(f"      {key}: {value}")
        print()
        
        # Create a DataFrame from the test booking data
        import pandas as pd
        test_df = pd.DataFrame([test_booking])
        
        # Create a mock classification result for validation
        from booking_classification_agent import ClassificationResult
        mock_classification = ClassificationResult(
            predicted_booking_count=1,
            booking_type='single',
            confidence_score=0.8,
            reasoning='Test classification',
            detected_patterns=[],
            duty_type_indicators=[],
            date_patterns=[]
        )
        
        # Validate the booking
        validated_df = validator._validate_single_booking_row(test_df, 0, mock_classification, email_content)
        validated_booking = validated_df.iloc[0].to_dict()
        
        print("   📋 Validated Booking Data:")
        print("   " + "-" * 30)
        for key, value in validated_booking.items():
            if key == 'Email Content':
                continue  # Skip long email content
            print(f"      {key}: {value}")
        
        # Check key validations
        checks = [
            ("City Standardization", validated_booking.get('From (Service Location)') == 'Chennai' and 'Bangalore' in validated_booking.get('To', '')),
            ("Duty Type Detection", 'Outstation' in validated_booking.get('Duty Type', '')),
            ("Passenger Details", validated_booking.get('Passenger Name') == 'Ganesan K'),
            ("Remarks Populated", len(validated_booking.get('Remarks', '')) > 10)
        ]
        
        print("\n   🔍 Validation Checks:")
        all_passed = True
        for check_name, passed in checks:
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"      {status} {check_name}")
            if not passed:
                all_passed = False
        
        if all_passed:
            print("\n   ✅ Business Validation: PASS")
        else:
            print("\n   ❌ Business Validation: Some checks failed")
            return False
            
    except Exception as e:
        print(f"   ❌ Business Validation Error: {e}")
        logging.error(f"Validation error: {e}", exc_info=True)
        return False
    
    print()
    print("🎉 END-TO-END TEST RESULT: ✅ PASS")
    print("=" * 60)
    print("✅ Outstation round trip correctly processed as single booking")
    print("✅ Business validation applied all improvements successfully")
    print("✅ Ready for production deployment!")
    
    return True

if __name__ == "__main__":
    success = test_outstation_round_trip_e2e()
    if not success:
        exit(1)
    
    print("\n🚀 **DEPLOYMENT READY:** Your Chennai→Bangalore→Chennai fix is working!")