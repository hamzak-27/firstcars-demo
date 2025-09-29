#!/usr/bin/env python3
"""
Quick debug script to see what Textract is actually extracting
"""

import boto3
import json
import logging
import glob
from enhanced_multi_booking_processor import EnhancedMultiBookingProcessor

# Set up logging to see everything
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def debug_textract_extraction():
    """Debug what Textract actually extracts from your images"""
    
    print("🔍 DEBUGGING TEXTRACT EXTRACTION")
    print("="*50)
    
    # Find any image files
    image_files = glob.glob('*.png') + glob.glob('*.jpg') + glob.glob('*.jpeg')
    
    if not image_files:
        print("❌ No image files found!")
        print("Please put your table image (Screenshot 2025-09-16 004941.png) in this directory")
        return
    
    print(f"📁 Found images: {image_files}")
    
    # Create the processor
    processor = EnhancedMultiBookingProcessor()
    
    for image_file in image_files[:1]:  # Test first image
        print(f"\n🔍 ANALYZING: {image_file}")
        print("-"*50)
        
        try:
            # Read the image
            with open(image_file, 'rb') as f:
                file_content = f.read()
            
            print(f"📄 Image size: {len(file_content)} bytes")
            
            # Extract structured data using the same method as your app
            extracted_data = processor._extract_structured_data(file_content, image_file)
            
            if not extracted_data:
                print("❌ No data extracted!")
                continue
            
            print(f"\n📊 EXTRACTED DATA OVERVIEW:")
            print(f"   Key-value pairs: {len(extracted_data.get('key_value_pairs', []))}")
            print(f"   Tables: {len(extracted_data.get('tables', []))}")
            print(f"   Raw text length: {len(extracted_data.get('raw_text', ''))}")
            
            # Analyze tables in detail
            tables = extracted_data.get('tables', [])
            print(f"\n📋 TABLE ANALYSIS:")
            
            for i, table in enumerate(tables, 1):
                print(f"\n   TABLE {i}:")
                print(f"   - Type: {table.get('type', 'unknown')}")
                print(f"   - Row count: {table.get('row_count', 0)}")
                print(f"   - Column count: {table.get('column_count', 0)}")
                print(f"   - Headers: {table.get('headers', [])}")
                
                # Show first few rows
                rows = table.get('rows', [])
                print(f"   - Rows preview:")
                for j, row in enumerate(rows[:5]):
                    print(f"     Row {j}: {row}")
                if len(rows) > 5:
                    print(f"     ... and {len(rows)-5} more rows")
                
                # Show key-value pairs if it's a form table
                if table.get('type') == 'form_table':
                    kv_pairs = table.get('key_value_pairs', [])
                    print(f"   - Key-value pairs ({len(kv_pairs)}):")
                    for kv in kv_pairs[:10]:
                        print(f"     '{kv.get('key', '')}' = '{kv.get('value', '')}'")
            
            # Show key-value pairs
            kv_pairs = extracted_data.get('key_value_pairs', [])
            if kv_pairs:
                print(f"\n🔑 KEY-VALUE PAIRS ({len(kv_pairs)}):")
                for kv in kv_pairs[:10]:
                    print(f"   '{kv.get('key', '')}' = '{kv.get('value', '')}'")
            
            # Show raw text sample
            raw_text = extracted_data.get('raw_text', '')
            if raw_text:
                print(f"\n📝 RAW TEXT SAMPLE:")
                sample = raw_text[:300] + "..." if len(raw_text) > 300 else raw_text
                print(f"   {sample}")
            
            # Now test the booking extraction
            print(f"\n🎯 TESTING BOOKING EXTRACTION:")
            bookings = processor._extract_multiple_bookings_from_tables(extracted_data)
            print(f"   Bookings extracted: {len(bookings)}")
            
            for i, booking in enumerate(bookings, 1):
                print(f"\n   BOOKING {i}:")
                print(f"   - Passenger: {booking.passenger_name}")
                print(f"   - Phone: {booking.passenger_phone}")
                print(f"   - Company: {booking.corporate}")
                print(f"   - Date: {booking.start_date}")
                print(f"   - Time: {booking.reporting_time}")
                print(f"   - Vehicle: {booking.vehicle_group}")
                print(f"   - From: {booking.from_location}")
                print(f"   - Pickup Address: {booking.reporting_address}")
                print(f"   - Drop Address: {booking.drop_address}")
                print(f"   - Extraction Method: {booking.extraction_method}")
            
            # Save debug data
            debug_file = f"debug_{image_file.replace('.', '_')}.json"
            with open(debug_file, 'w') as f:
                json.dump(extracted_data, f, indent=2)
            print(f"\n💾 Debug data saved to: {debug_file}")
            
            print(f"\n" + "="*50)
            
        except Exception as e:
            print(f"❌ ERROR processing {image_file}: {e}")
            import traceback
            traceback.print_exc()

def analyze_table_structure():
    """Analyze why table structure detection might be failing"""
    
    print("\n🔬 ANALYZING TABLE STRUCTURE DETECTION")
    print("="*50)
    
    # Test with mock data that should work
    mock_table_data = {
        'type': 'regular_table',
        'headers': ['Cab Booking Format', 'Cab 1', 'Cab 2', 'Cab 3', 'Cab 4'],
        'rows': [
            ['Cab Booking Format', 'Cab 1', 'Cab 2', 'Cab 3', 'Cab 4'],
            ['Name of Employee', 'Jayasheel Bhansali', 'Jayasheel Bhansali', 'Jayasheel Bhansali', 'Jayasheel Bhansali'],
            ['Contact Number', '7001682596', '7001682596', '7001682596', '7001682596'],
            ['City', 'Bangalore', 'Bangalore', 'Mumbai', 'Mumbai']
        ],
        'row_count': 4,
        'column_count': 5
    }
    
    mock_extracted_data = {
        'tables': [mock_table_data],
        'key_value_pairs': [],
        'raw_text': 'Mock table data'
    }
    
    processor = EnhancedMultiBookingProcessor()
    
    print("🧪 Testing with PERFECT mock table data...")
    bookings = processor._extract_multiple_bookings_from_tables(mock_extracted_data)
    print(f"   Result: {len(bookings)} bookings extracted")
    
    if len(bookings) == 4:
        print("✅ Mock data works perfectly - the issue is with Textract parsing!")
        print("🎯 PROBLEM: Textract is not returning the table in the expected format")
    else:
        print("❌ Even mock data fails - there's a logic error in extraction")
    
    for i, booking in enumerate(bookings, 1):
        print(f"   Mock Booking {i}: {booking.passenger_name} - {booking.start_date}")

if __name__ == "__main__":
    debug_textract_extraction()
    analyze_table_structure()