#!/usr/bin/env python3
"""
Test Form Integration
Test that the new FormExtractionUtils is properly integrated into the extraction pipeline
"""

import logging
from enhanced_multi_booking_processor import EnhancedMultiBookingProcessor
from form_extraction_utils import FormExtractionUtils

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_form_integration():
    """Test form extraction integration"""
    
    print("🧪 Testing Form Extraction Integration")
    print("=" * 50)
    
    # Sample form content (like the Medtronic form)
    sample_form_text = """
    Company Name | India Medtronic Pvt. Ltd.
    Is the booking for IMPL employee or SPR (Doctor) | IMPL Employee
    Name & Contact Number of booker | Hiba Mohammed
    Email ID of booker | hiba.mohammed@medtronic.com
    City in which car is required | Chengannur
    Name of the User | Hiba Mohammed
    Mobile No. of the User | 8281011554, 9319154943
    Email ID of user | hiba.mohammed@medtronic.com
    Date of Requirement – From date & To date for multi day | 01-10-25, 11:00 AM
    1Car Type (Indigo/Dzire/Fiesta) | Dzire
    Reporting | H.No 33/432B Thattekadu Rd Near Villa Exotica Bavasons Homes, Maradu Nettoor, kochi 682040
    Reporting Time | 01-10-25, 11:00 AM
    Type of duty (Only Drop / Local full day | chengannur
    """
    
    # Test 1: Form detection
    print("\n1. Testing form detection...")
    processor = EnhancedMultiBookingProcessor()
    
    is_form = processor._is_form_document(sample_form_text)
    print(f"   Form detected: {is_form} ✅" if is_form else f"   Form detected: {is_form} ❌")
    
    # Test 2: Direct form extraction
    print("\n2. Testing form data extraction...")
    try:
        form_utils = FormExtractionUtils()
        form_data = form_utils.extract_form_data(sample_form_text)
        
        print(f"   Extracted {len(form_data)} form fields:")
        for field, value in form_data.items():
            print(f"     {field}: {value}")
        
        if len(form_data) >= 5:
            print("   ✅ Form extraction working correctly")
        else:
            print("   ❌ Form extraction extracted too few fields")
    except Exception as e:
        print(f"   ❌ Form extraction failed: {e}")
    
    # Test 3: Integrated pipeline test (mock)
    print("\n3. Testing integrated pipeline...")
    try:
        # Create mock extracted_data (simulating Textract output)
        mock_extracted_data = {
            'raw_text': sample_form_text,
            'tables': [],
            'key_value_pairs': []
        }
        
        # Test form extraction from pipeline
        form_booking = processor._extract_single_booking_from_form(mock_extracted_data)
        
        if form_booking:
            print("   ✅ Pipeline integration working!")
            print(f"     Passenger: {form_booking.passenger_name}")
            print(f"     Company: {form_booking.customer}") 
            print(f"     Phone: {form_booking.passenger_phone}")
            print(f"     Vehicle: {form_booking.vehicle_group}")
            print(f"     Extraction Method: {form_booking.extraction_method}")
        else:
            print("   ❌ Pipeline integration failed")
            
    except Exception as e:
        print(f"   ❌ Pipeline test failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 4: Business logic validation check
    print("\n4. Testing business logic validation...")
    try:
        from business_logic_validation_agent import BusinessLogicValidationAgent
        from base_extraction_agent import ExtractionResult
        from openai_classification_agent import ClassificationResult, BookingType, DutyType
        import pandas as pd
        
        # Create mock data for validation test
        sample_data = {
            'Customer': ['India Medtronic Pvt. Ltd.'],
            'Booked By Name': ['Hiba Mohammed'],
            'Booked By Email': ['hiba.mohammed@medtronic.com'],
            'Passenger Name': ['Hiba Mohammed'],
            'Passenger Phone Number': ['8281011554'],
            'Passenger Email': ['hiba.mohammed@medtronic.com'],
            'From (Service Location)': ['Chengannur'],
            'To': ['Chengannur'],
            'Vehicle Group': ['Dzire'],
            'Duty Type': ['Local full day'],
            'Start Date': ['2025-10-01'],
            'End Date': ['2025-10-01'],
            'Rep. Time': ['11:00'],
            'Reporting Address': ['H.No 33/432B Thattekadu Rd'],
            'Drop Address': [''],
            'Flight/Train Number': [''],
            'Dispatch center': [''],
            'Remarks': [''],
            'Labels': ['']
        }
        
        df = pd.DataFrame(sample_data)
        
        extraction_result = ExtractionResult(
            success=True,
            bookings_dataframe=df,
            booking_count=1,
            confidence_score=0.85,
            processing_time=1.0,
            cost_inr=0.0,
            extraction_method="form_extraction"
        )
        
        classification_result = ClassificationResult(
            booking_type=BookingType.SINGLE,
            booking_count=1,
            confidence_score=0.9,
            reasoning="Single form booking",
            detected_duty_type=DutyType.DISPOSAL_8_80,
            detected_dates=["2025-10-01"],
            detected_vehicles=["Dzire"],
            detected_drops=["Local"]
        )
        
        # Test validation
        validator = BusinessLogicValidationAgent()
        validated_result = validator.validate_and_enhance(extraction_result, classification_result, sample_form_text)
        
        if validated_result.success:
            print("   ✅ Business logic validation working!")
            validated_df = validated_result.bookings_dataframe
            
            # Check key validations
            duty_type = validated_df.iloc[0]['Duty Type']
            corporate_col = validated_df.iloc[0].get('Corporate', 'NA')
            time_col = validated_df.iloc[0]['Rep. Time']
            
            print(f"     Final Duty Type: {duty_type}")
            print(f"     Corporate Column: {corporate_col}")
            print(f"     Reporting Time: {time_col}")
            print(f"     Method: {validated_result.extraction_method}")
            
            # Check if validation rules were applied
            checks = []
            if 'G2G' in duty_type:  # Should be G2G for Medtronic
                checks.append("✅ G2G classification correct")
            else:
                checks.append("❌ G2G classification failed")
                
            if corporate_col == 'NA':
                checks.append("✅ Corporate column set to NA")
            else:
                checks.append("❌ Corporate column not set to NA")
            
            if ':' in time_col and len(time_col) == 5:  # HH:MM format
                checks.append("✅ Time format correct")
            else:
                checks.append("❌ Time format incorrect")
            
            for check in checks:
                print(f"     {check}")
        else:
            print(f"   ❌ Business logic validation failed: {validated_result.error_message}")
            
    except Exception as e:
        print(f"   ❌ Business logic validation test failed: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"\n🎯 Integration Test Complete!")
    print("=" * 50)

if __name__ == "__main__":
    test_form_integration()