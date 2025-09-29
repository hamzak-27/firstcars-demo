#!/usr/bin/env python3
"""
Test what Textract actually returns from your image
"""

import glob
from enhanced_multi_booking_processor import EnhancedMultiBookingProcessor

def test_textract_output():
    """Test actual Textract output"""
    
    print("🔍 TESTING ACTUAL TEXTRACT OUTPUT")
    print("="*50)
    
    # Find any image files
    image_files = glob.glob('*.png') + glob.glob('*.jpg') + glob.glob('*.jpeg')
    
    if not image_files:
        print("❌ No image files found!")
        print("Put your image file in this directory and run again")
        return
    
    processor = EnhancedMultiBookingProcessor()
    
    for image_file in image_files[:1]:
        print(f"\n📁 Testing: {image_file}")
        
        with open(image_file, 'rb') as f:
            file_content = f.read()
        
        # This is the EXACT same call your Streamlit app makes
        try:
            result = processor.process_multi_booking_document(file_content, image_file, 'png')
            
            print(f"\n📊 RESULTS:")
            print(f"   Extraction method: {result.extraction_method}")
            print(f"   Bookings found: {result.total_bookings_found}")
            print(f"   Confidence: {result.confidence_score}")
            print(f"   Notes: {result.processing_notes}")
            
            print(f"\n📋 BOOKINGS:")
            for i, booking in enumerate(result.bookings, 1):
                print(f"\n   BOOKING {i}:")
                print(f"   - Passenger: {booking.passenger_name}")
                print(f"   - Phone: {booking.passenger_phone}")
                print(f"   - Company: {booking.corporate}")
                print(f"   - Date: {booking.start_date}")
                print(f"   - Time: {booking.reporting_time}")
                print(f"   - Vehicle: {booking.vehicle_group}")
                print(f"   - From: {booking.from_location}")
                print(f"   - Pickup: {booking.reporting_address}")
                print(f"   - Drop: {booking.drop_address}")
                print(f"   - Method: {booking.extraction_method}")
            
            # This is what gets fed to the AI pipeline
            if result.bookings:
                booking_summaries = []
                for i, booking in enumerate(result.bookings, 1):
                    summary = f"Booking {i}:\\n"
                    summary += f"- Passenger: {booking.passenger_name or 'N/A'} ({booking.passenger_phone or 'N/A'})\\n"
                    summary += f"- Company: {booking.corporate or 'N/A'}\\n"
                    summary += f"- Date: {booking.start_date or 'N/A'}\\n"
                    summary += f"- Time: {booking.reporting_time or 'N/A'}\\n"
                    summary += f"- Vehicle: {booking.vehicle_group or 'N/A'}\\n"
                    summary += f"- From: {booking.from_location or booking.reporting_address or 'N/A'}\\n"
                    summary += f"- To: {booking.to_location or booking.drop_address or 'N/A'}\\n"
                    if booking.flight_train_number:
                        summary += f"- Flight: {booking.flight_train_number}\\n"
                    if booking.remarks:
                        summary += f"- Remarks: {booking.remarks}\\n"
                    booking_summaries.append(summary)
                
                ai_content = f"TABLE EXTRACTION RESULTS ({len(result.bookings)} bookings found):\\n\\n" + "\\n".join(booking_summaries)
                ai_content += f"\\n\\nOriginal processing method: {result.extraction_method}"
                
                print(f"\n🤖 AI PIPELINE CONTENT:")
                print("-"*50)
                print(ai_content)
                print("-"*50)
                
                # Check length
                print(f"\n📏 Content length: {len(ai_content)} characters")
                
                if len(result.bookings) >= 4:
                    print("✅ SUCCESS: Found 4+ bookings!")
                elif len(result.bookings) > 1:
                    print(f"⚠️  PARTIAL: Found {len(result.bookings)} bookings, expected 4")
                else:
                    print(f"❌ FAILURE: Only found {len(result.bookings)} booking")
            
        except Exception as e:
            print(f"❌ ERROR: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_textract_output()