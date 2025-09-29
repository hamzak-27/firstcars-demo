#!/usr/bin/env python3
"""
Debug script to analyze Textract table extraction
"""

import json
import logging
from enhanced_multi_booking_processor import EnhancedMultiBookingProcessor

# Set up logging to see all details
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def debug_textract_extraction():
    """Debug what Textract actually extracts from your image"""
    
    # Create processor
    processor = EnhancedMultiBookingProcessor()
    
    # Check for any image files in the current directory
    import os
    import glob
    
    image_files = glob.glob('*.png') + glob.glob('*.jpg') + glob.glob('*.jpeg')
    
    if image_files:
        test_image_path = image_files[0]
        print(f"📁 Found image file: {test_image_path}")
        
        # Read the image
        with open(test_image_path, 'rb') as f:
            file_content = f.read()
        
        print(f"📁 Processing image: {test_image_path} ({len(file_content)} bytes)")
        
        # Extract structured data using Textract
        try:
            extracted_data = processor._extract_structured_data(file_content, test_image_path)
        except Exception as e:
            print(f"❌ Textract failed: {e}")
            print("Falling back to mock data for debugging...")
            extracted_data = create_mock_textract_data()
    else:
        print("📁 No image files found in current directory")
        print("Using mock Textract data to test table extraction logic...")
        extracted_data = create_mock_textract_data()
        
        if not extracted_data:
            print("❌ No data extracted from Textract")
            return
        
        print(f"\n📊 TEXTRACT EXTRACTION RESULTS:")
        print(f"Key-value pairs: {len(extracted_data.get('key_value_pairs', []))}")
        print(f"Tables found: {len(extracted_data.get('tables', []))}")
        print(f"Raw text length: {len(extracted_data.get('raw_text', ''))}")
        
        # Analyze tables in detail
        tables = extracted_data.get('tables', [])
        for i, table in enumerate(tables):
            print(f"\n=== TABLE {i+1} ===")
            print(f"Type: {table.get('type', 'unknown')}")
            print(f"Headers: {table.get('headers', [])}")
            print(f"Rows: {len(table.get('rows', []))}")
            
            # Show first few rows for debugging
            rows = table.get('rows', [])
            for j, row in enumerate(rows[:5]):  # Show first 5 rows
                print(f"Row {j}: {row}")
            
            if len(rows) > 5:
                print(f"... and {len(rows)-5} more rows")
        
        # Test the booking extraction
        print(f"\n🔍 TESTING BOOKING EXTRACTION:")
        bookings = processor._extract_multiple_bookings_from_tables(extracted_data)
        print(f"Bookings extracted: {len(bookings)}")
        
        for i, booking in enumerate(bookings, 1):
            print(f"\n--- Booking {i} ---")
            print(f"Passenger: {booking.passenger_name}")
            print(f"Phone: {booking.passenger_phone}")
            print(f"Company: {booking.corporate}")
            print(f"Date: {booking.start_date}")
            print(f"Time: {booking.reporting_time}")
            print(f"Vehicle: {booking.vehicle_group}")
            print(f"Pickup: {booking.reporting_address}")
            print(f"Drop: {booking.drop_address}")
        
        # Save debug data to file
        debug_file = "textract_debug_output.json"
        with open(debug_file, 'w') as f:
            # Convert to serializable format
            debug_data = {
                'tables': extracted_data.get('tables', []),
                'key_value_pairs': extracted_data.get('key_value_pairs', []),
                'raw_text': extracted_data.get('raw_text', '')[:1000]  # First 1000 chars
            }
            json.dump(debug_data, f, indent=2)
        
        print(f"\n💾 Debug data saved to: {debug_file}")
        
    except Exception as e:
        print(f"❌ Error during Textract processing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_textract_extraction()