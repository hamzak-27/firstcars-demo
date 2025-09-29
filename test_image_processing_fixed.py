#!/usr/bin/env python3
"""
Test Fixed Image Processing - Debug the table extraction with your image
"""

import os
import json

def test_image_processing():
    """Test image processing with debugging"""
    
    print("🔍 Testing Fixed Image Processing")
    print("=" * 60)
    
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
    
    # Test the fixed multi-booking processor
    try:
        from enhanced_multi_booking_processor import EnhancedMultiBookingProcessor
        
        processor = EnhancedMultiBookingProcessor()
        print(f"✅ Multi-Booking Processor initialized")
        print(f"   Textract available: {processor.textract_available}")
        
        # Simulate the data from your form image
        print("\n📋 Simulating Form Data Extraction...")
        
        # Based on your image, here's what Textract likely extracted
        simulated_extracted_data = {
            'key_value_pairs': [
                {'key': 'NAME OF THE GUEST', 'value': 'Nakul Ayhad'},
                {'key': 'MOBILE NUMBER', 'value': '9152026571'},
                {'key': 'RENTAL CITY / PICK UP CITY', 'value': 'New Delhi'},
                {'key': 'CAR TYPE', 'value': 'Sedan'},
                {'key': 'DATE OF REQUIREMENT', 'value': '12th September 2025'},
                {'key': 'REPORTING TIME', 'value': 'Flight Ticket Attached'},
                {'key': 'REPORTING ADDRESS', 'value': 'Delhi Airport'},
                {'key': 'FLIGHT DETAILS', 'value': 'Flight Ticket Attached'},
                {'key': 'USAGE (Drop/Disposal/Outstation)', 'value': 'Disposal / Outstation'},
                {'key': 'Billing Mode (BTC)', 'value': 'BTC'},
                {'key': 'SPECIAL INSTRUCTIONS(if any)', 'value': ''},
                {'key': 'Purpose of Travel', 'value': 'ACMA AGM'},
                {'key': 'COMPANY NAME', 'value': 'Horizon Industrial Parks Pvt Ltd'},
                {'key': 'BILLING ENTITY NAME', 'value': 'Horizon Industrial Parks Pvt Ltd'}
            ],
            'tables': [],  # Single form, no tables
            'raw_text': 'TRAVEL REQUISITION FORM NAME OF THE GUEST Nakul Ayhad MOBILE NUMBER 9152026571 RENTAL CITY / PICK UP CITY New Delhi CAR TYPE Sedan DATE OF REQUIREMENT 12th September 2025 REPORTING TIME Flight Ticket Attached REPORTING ADDRESS Delhi Airport FLIGHT DETAILS Flight Ticket Attached USAGE (Drop/Disposal/Outstation) Disposal / Outstation Billing Mode (BTC) BTC SPECIAL INSTRUCTIONS(if any) Purpose of Travel ACMA AGM COMPANY NAME Horizon Industrial Parks Pvt Ltd BILLING ENTITY NAME Horizon Industrial Parks Pvt Ltd'
        }
        
        print("📊 Testing enhanced table extraction...")
        
        # Test the table extraction method directly
        bookings = processor._extract_multiple_bookings_from_tables(simulated_extracted_data)
        
        print(f"📋 Bookings found from tables: {len(bookings)}")
        
        if bookings:
            for i, booking in enumerate(bookings, 1):
                print(f"\nBooking {i} from tables:")
                print(f"  Passenger: {booking.passenger_name}")
                print(f"  Phone: {booking.passenger_phone}")
                print(f"  Company: {booking.corporate}")
                print(f"  Date: {booking.start_date}")
                print(f"  Vehicle: {booking.vehicle_group}")
                print(f"  From: {booking.from_location}")
                print(f"  Duty Type: {booking.duty_type}")
        else:
            print("❌ No bookings extracted from tables, testing fallback processing...")
            
            # Test the fallback processing (key-value pairs)
            kv_pairs = simulated_extracted_data['key_value_pairs']
            booking = processor._create_booking_from_kv_pairs(kv_pairs)
            
            if booking:
                print("\n✅ Fallback extraction successful:")
                print(f"  Passenger: {booking.passenger_name}")
                print(f"  Phone: {booking.passenger_phone}")
                print(f"  Company: {booking.corporate}")
                print(f"  Date: {booking.start_date}")
                print(f"  Vehicle: {booking.vehicle_group}")
                print(f"  From: {booking.from_location}")
                print(f"  Duty Type: {booking.duty_type}")
                
        # Test the complete processing pipeline
        print("\n🔄 Testing Complete Processing Pipeline...")
        try:
            from complete_multi_agent_orchestrator import CompleteMultiAgentOrchestrator
            
            orchestrator = CompleteMultiAgentOrchestrator(api_key=gemini_api_key)
            
            # Create realistic content from your form
            form_content = """
            [File: Screenshot 2025-09-11 120940.png, Method: enhanced_multi_booking_textract]

            TABLE EXTRACTION RESULTS (1 bookings found):

            Booking 1:
            - Passenger: Nakul Ayhad (9152026571)
            - Company: Horizon Industrial Parks Pvt Ltd
            - Date: 12th September 2025
            - Time: Flight Ticket Attached
            - Vehicle: Sedan
            - From: New Delhi
            - To: Delhi Airport
            - Flight: Flight Ticket Attached
            - Remarks: Purpose: ACMA AGM, Usage: Disposal/Outstation, Billing: BTC

            Original processing method: enhanced_multi_booking_extraction (png)
            """
            
            print("Starting AI processing of extracted form data...")
            result = orchestrator.process_content(form_content, "file_upload_png")
            
            if result['success']:
                print(f"\n✅ AI PROCESSING SUCCESS:")
                print(f"   Bookings: {result['booking_count']}")
                print(f"   Cost: ₹{result['total_cost_inr']:.4f}")
                print(f"   Time: {result['total_processing_time']:.2f}s")
                
                # Show the final DataFrame
                if 'final_dataframe' in result:
                    df = result['final_dataframe']
                    if not df.empty:
                        first_booking = df.iloc[0]
                        print(f"\n📋 FINAL EXTRACTED DATA:")
                        print(f"   Customer: {first_booking.get('Customer', 'N/A')}")
                        print(f"   Passenger: {first_booking.get('Passenger Name', 'N/A')}")
                        print(f"   Phone: {first_booking.get('Passenger Phone Number', 'N/A')}")
                        print(f"   Vehicle: {first_booking.get('Vehicle Group', 'N/A')}")
                        print(f"   Duty Type: {first_booking.get('Duty Type', 'N/A')}")
                        print(f"   Date: {first_booking.get('Start Date', 'N/A')}")
                        print(f"   From: {first_booking.get('From (Service Location)', 'N/A')}")
                        print(f"   To: {first_booking.get('To', 'N/A')}")
                        print(f"   Labels: {first_booking.get('Labels', 'N/A')}")
                        print(f"   Remarks: {str(first_booking.get('Remarks', 'N/A'))[:100]}...")
                        
                        # Convert to JSON format like your example
                        booking_json = {
                            "Customer": first_booking.get('Customer', ''),
                            "Booked By Name": first_booking.get('Booked By Name', ''),
                            "Booked By Phone Number": first_booking.get('Booked By Phone Number', ''),
                            "Booked By Email": first_booking.get('Booked By Email', ''),
                            "Passenger Name": first_booking.get('Passenger Name', ''),
                            "Passenger Phone Number": first_booking.get('Passenger Phone Number', ''),
                            "Passenger Email": first_booking.get('Passenger Email', ''),
                            "From (Service Location)": first_booking.get('From (Service Location)', ''),
                            "To": first_booking.get('To', ''),
                            "Vehicle Group": first_booking.get('Vehicle Group', ''),
                            "Duty Type": first_booking.get('Duty Type', ''),
                            "Start Date": first_booking.get('Start Date', ''),
                            "End Date": first_booking.get('End Date', ''),
                            "Rep. Time": first_booking.get('Rep. Time', ''),
                            "Reporting Address": first_booking.get('Reporting Address', ''),
                            "Drop Address": first_booking.get('Drop Address', ''),
                            "Flight/Train Number": first_booking.get('Flight/Train Number', ''),
                            "Dispatch center": first_booking.get('Dispatch center', ''),
                            "Remarks": first_booking.get('Remarks', ''),
                            "Labels": first_booking.get('Labels', '')
                        }
                        
                        print(f"\n📄 JSON OUTPUT:")
                        print(json.dumps([booking_json], indent=2))
                        
            else:
                print(f"❌ AI processing failed: {result.get('error_message')}")
                
        except Exception as e:
            print(f"❌ Pipeline test failed: {e}")
            import traceback
            traceback.print_exc()
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("🔍 Test Complete")
    
    print("\n💡 EXPECTED IMPROVEMENTS:")
    print("- Table parsing errors should be fixed")
    print("- Field mapping should work correctly") 
    print("- AI should receive better structured data")
    print("- Final results should be much more accurate")

if __name__ == "__main__":
    test_image_processing()