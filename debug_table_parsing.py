#!/usr/bin/env python3
"""
Debug Table Parsing - Check why multi-booking processor isn't finding bookings in tables
"""

import os
import json

def debug_table_parsing():
    """Debug the table parsing issue"""
    
    print("🔍 Debug: Multi-Booking Table Parsing")
    print("=" * 50)
    
    # Set credentials
    gemini_api_key = "AIzaSyAId73p8fsv1U0z2_jQ0yOLdcVJsVsOmeg"
    os.environ['GEMINI_API_KEY'] = gemini_api_key
    
    aws_credentials = {
        'AWS_DEFAULT_REGION': 'ap-south-1',
        'AWS_ACCESS_KEY_ID': 'AKIAYLZZKLOTYIXDAARY',
        'AWS_SECRET_ACCESS_KEY': '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',
        'S3_BUCKET_NAME': 'aws-textract-bucket3'
    }
    
    for key, value in aws_credentials.items():
        os.environ[key] = value
    
    print("✅ Credentials configured")
    
    # Test the enhanced multi-booking processor directly
    try:
        from enhanced_multi_booking_processor import EnhancedMultiBookingProcessor
        
        processor = EnhancedMultiBookingProcessor()
        print(f"✅ Multi-Booking Processor initialized")
        print(f"   Textract available: {processor.textract_available}")
        
        # Test with a sample image (you'll need to provide the path to your image)
        # For now, let's test the parsing logic with some sample extracted data
        
        # Sample extracted data that might come from Textract
        sample_extracted_data = {
            'key_value_pairs': [
                {'key': 'Date & City / Car', 'value': '2024-09-26 Mumbai'},
                {'key': 'Pick up – Time', 'value': '09:00 AM'},
                {'key': 'Global Leaders', 'value': 'John Doe'},
                {'key': 'Pick up Address', 'value': 'Mumbai Office'},
                {'key': 'Drop Address', 'value': 'Mumbai Airport'},
            ],
            'tables': [
                {
                    'type': 'regular_table',
                    'headers': ['Field', 'Cab 1', 'Cab 2'],
                    'rows': [
                        ['Field', 'Cab 1', 'Cab 2'],
                        ['Name of Employee', 'John Doe', 'Jane Smith'],
                        ['Contact Number', '9876543210', '9876543211'],
                        ['Date of Travel', '2024-09-26', '2024-09-27'],
                        ['Pick-up Time', '09:00', '14:00'],
                        ['Cab Type', 'Dzire', 'Innova'],
                    ]
                }
            ],
            'raw_text': 'Booking details for multiple cabs...'
        }
        
        print("\n🔍 Testing table extraction...")
        
        # Test the table extraction method directly
        bookings = processor._extract_multiple_bookings_from_tables(sample_extracted_data)
        
        print(f"📊 Bookings found: {len(bookings)}")
        
        if bookings:
            for i, booking in enumerate(bookings, 1):
                print(f"\nBooking {i}:")
                print(f"  Passenger: {booking.passenger_name}")
                print(f"  Phone: {booking.passenger_phone}")
                print(f"  Date: {booking.start_date}")
                print(f"  Vehicle: {booking.vehicle_group}")
                print(f"  From: {booking.from_location}")
                print(f"  To: {booking.to_location}")
        else:
            print("❌ No bookings extracted from tables")
            
            # Debug the field mapping
            print("\n🔧 Debug: Field Mappings")
            print("Available field mappings:")
            for field, mappings in processor.field_mappings.items():
                print(f"  '{field}' -> {mappings}")
            
            # Test horizontal table extraction specifically
            print("\n🔧 Debug: Horizontal Table Extraction")
            if sample_extracted_data['tables']:
                table = sample_extracted_data['tables'][0]
                print(f"Table headers: {table['headers']}")
                print(f"Table rows: {len(table['rows'])} rows")
                
                # Test the horizontal table extraction method
                horizontal_bookings = processor._extract_from_horizontal_table(table)
                print(f"Horizontal extraction result: {len(horizontal_bookings)} bookings")
                
                if horizontal_bookings:
                    for i, booking in enumerate(horizontal_bookings, 1):
                        booking_dict = booking.__dict__
                        filled_fields = {k: v for k, v in booking_dict.items() if v}
                        print(f"  Booking {i} fields: {filled_fields}")
        
    except Exception as e:
        print(f"❌ Debug failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 50)
    print("🔍 Debug Complete")

if __name__ == "__main__":
    debug_table_parsing()