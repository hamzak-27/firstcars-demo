#!/usr/bin/env python3
"""
Enhanced Textract debugging script to analyze FORMS and TABLES extraction
"""

import json
import logging
import os
import glob
import boto3
from enhanced_multi_booking_processor import EnhancedMultiBookingProcessor
from enhanced_form_processor import EnhancedFormProcessor

# Set up logging to see all details
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_mock_textract_data():
    """Create mock Textract data that simulates what should be extracted from your table image"""
    return {
        'tables': [{
            'type': 'regular_table',
            'headers': ['Cab Booking Format', 'Cab 1', 'Cab 2', 'Cab 3', 'Cab 4'],
            'rows': [
                ['Cab Booking Format', 'Cab 1', 'Cab 2', 'Cab 3', 'Cab 4'],
                ['Name of Employee', 'Jayasheel Bhansali', 'Jayasheel Bhansali', 'Jayasheel Bhansali', 'Jayasheel Bhansali'],
                ['Contact Number', '7001682596', '7001682596', '7001682596', '7001682596'],
                ['City', 'Bangalore', 'Bangalore', 'Mumbai', 'Mumbai'],
                ['Date of Travel', '19-Sep-25', '20 Sep 2025 & 21 Sep 2025', '21-Sep-25', '22 Sep 2025 to 25 Sep 2025'],
                ['Pick-up Time', '8:30 PM', '10:00 AM', '7:30 PM', '8:00 AM'],
                ['Cab Type', 'CRYSTA', 'CRYSTA', 'CRYSTA', 'CRYSTA'],
                ['Pick-up Address', 'Bangalore Airport T-2', 'ITC Windsor Bangalore', 'Mumbai Airport Terminal 2', 'JW Marriott Mumbai Sahar'],
                ['Drop at', 'ITC Windsor Bangalore', 'Full Day', 'JW Marriott Mumbai Sahar', 'Office .Silver Utopia,Cardinal gracious Road, chakala andheri east...... FULL DAY .'],
                ['Flight details', 'AI-2641', 'NA', 'AI 2854', 'NA'],
                ['Company Name', 'LTPL (Lendingkart Technologies Private Limited)', 'LTPL (Lendingkart Technologies Private Limited)', 'LTPL (Lendingkart Technologies Private Limited)', 'LTPL (Lendingkart Technologies Private Limited)']
            ]
        }],
        'key_value_pairs': [],
        'raw_text': 'Mock text for debugging table extraction logic'
    }

def analyze_raw_textract_response(file_content: bytes, filename: str):
    """Analyze raw Textract response to understand parsing structure"""
    
    print(f"\n🔍 ANALYZING RAW TEXTRACT RESPONSE FOR: {filename}")
    print("="*80)
    
    try:
        # Initialize Textract client
        textract_client = boto3.client('textract')
        
        # Call Textract with FORMS and TABLES (same as the system uses)
        response = textract_client.analyze_document(
            Document={'Bytes': file_content},
            FeatureTypes=['FORMS', 'TABLES']
        )
        
        print(f"✅ Textract API call successful!")
        
        # Analyze the raw response structure
        blocks = response.get('Blocks', [])
        print(f"📊 Total blocks returned: {len(blocks)}")
        
        # Categorize blocks by type
        block_types = {}
        for block in blocks:
            block_type = block.get('BlockType')
            if block_type not in block_types:
                block_types[block_type] = 0
            block_types[block_type] += 1
        
        print(f"\n📋 BLOCK TYPE BREAKDOWN:")
        for block_type, count in block_types.items():
            print(f"   {block_type}: {count} blocks")
        
        # Analyze specific block types in detail
        analyze_line_blocks(blocks)
        analyze_key_value_blocks(blocks)
        analyze_table_blocks(blocks)
        
        return response
        
    except Exception as e:
        print(f"❌ Textract API call failed: {e}")
        return None

def analyze_line_blocks(blocks):
    """Analyze LINE blocks to see raw text detection"""
    
    print(f"\n📝 LINE BLOCKS ANALYSIS (Raw text detection):")
    print("-"*50)
    
    line_blocks = [b for b in blocks if b.get('BlockType') == 'LINE']
    print(f"Found {len(line_blocks)} LINE blocks")
    
    # Show first 20 lines to see what text was detected
    for i, block in enumerate(line_blocks[:20]):
        text = block.get('Text', '')
        confidence = block.get('Confidence', 0)
        print(f"   Line {i+1:2d}: {text} (confidence: {confidence:.1f}%)")
    
    if len(line_blocks) > 20:
        print(f"   ... and {len(line_blocks)-20} more lines")
    
    # Look for multi-booking indicators in line text
    multi_booking_indicators = ['cab 1', 'cab 2', 'cab 3', 'cab 4', 'jayasheel', 'crysta', 'lendingkart']
    found_indicators = []
    
    for block in line_blocks:
        text = block.get('Text', '').lower()
        for indicator in multi_booking_indicators:
            if indicator in text and indicator not in found_indicators:
                found_indicators.append(indicator)
    
    print(f"\n🎯 Multi-booking indicators found in text: {found_indicators}")
    
def analyze_key_value_blocks(blocks):
    """Analyze KEY_VALUE_SET blocks (FORMS feature)"""
    
    print(f"\n🔑 KEY_VALUE_SET BLOCKS ANALYSIS (FORMS feature):")
    print("-"*50)
    
    kv_blocks = [b for b in blocks if b.get('BlockType') == 'KEY_VALUE_SET']
    print(f"Found {len(kv_blocks)} KEY_VALUE_SET blocks")
    
    # Separate keys and values
    key_blocks = [b for b in kv_blocks if b.get('EntityTypes') and 'KEY' in b['EntityTypes']]
    value_blocks = [b for b in kv_blocks if b.get('EntityTypes') and 'VALUE' in b['EntityTypes']]
    
    print(f"   Keys: {len(key_blocks)}, Values: {len(value_blocks)}")
    
    # Build block map for text extraction
    block_map = {block['Id']: block for block in blocks}
    
    # Extract key-value pairs
    kv_pairs = []
    for key_block in key_blocks[:15]:  # Show first 15 pairs
        key_text = extract_text_from_block(key_block, block_map)
        
        # Find corresponding value
        value_text = ""
        for relationship in key_block.get('Relationships', []):
            if relationship['Type'] == 'VALUE':
                for value_id in relationship['Ids']:
                    if value_id in block_map:
                        value_block = block_map[value_id]
                        value_text = extract_text_from_block(value_block, block_map)
                        break
        
        if key_text:
            kv_pairs.append((key_text.strip(), value_text.strip()))
            print(f"   '{key_text.strip()}' → '{value_text.strip()}'")
    
    if len(key_blocks) > 15:
        print(f"   ... and {len(key_blocks)-15} more key-value pairs")
    
    return kv_pairs

def analyze_table_blocks(blocks):
    """Analyze TABLE blocks (TABLES feature) - this is crucial for multi-booking"""
    
    print(f"\n📊 TABLE BLOCKS ANALYSIS (TABLES feature):")
    print("-"*50)
    
    table_blocks = [b for b in blocks if b.get('BlockType') == 'TABLE']
    print(f"Found {len(table_blocks)} TABLE blocks")
    
    if not table_blocks:
        print("❌ NO TABLES DETECTED - This is likely why multi-booking extraction is failing!")
        print("   Textract is not recognizing your table structure.")
        return []
    
    block_map = {block['Id']: block for block in blocks}
    extracted_tables = []
    
    for i, table_block in enumerate(table_blocks):
        print(f"\n=== TABLE {i+1} ===")
        
        # Find all cells in the table
        cells = []
        for relationship in table_block.get('Relationships', []):
            if relationship['Type'] == 'CHILD':
                for cell_id in relationship['Ids']:
                    if cell_id in block_map and block_map[cell_id]['BlockType'] == 'CELL':
                        cells.append(block_map[cell_id])
        
        print(f"Total cells found: {len(cells)}")
        
        # Organize cells by row and column
        cells.sort(key=lambda x: (x.get('RowIndex', 0), x.get('ColumnIndex', 0)))
        
        # Build table structure
        table_data = {}
        max_row = 0
        max_col = 0
        
        for cell in cells:
            row_idx = cell.get('RowIndex', 0)
            col_idx = cell.get('ColumnIndex', 0)
            cell_text = extract_text_from_block(cell, block_map)
            
            if row_idx not in table_data:
                table_data[row_idx] = {}
            
            table_data[row_idx][col_idx] = cell_text.strip()
            max_row = max(max_row, row_idx)
            max_col = max(max_col, col_idx)
        
        print(f"Table dimensions: {max_row + 1} rows x {max_col + 1} columns")
        
        # Display the table structure
        print(f"\nTable content:")
        for row in range(max_row + 1):
            row_data = []
            for col in range(max_col + 1):
                cell_content = table_data.get(row, {}).get(col, '')
                # Truncate long content for display
                if len(cell_content) > 30:
                    cell_content = cell_content[:27] + '...'
                row_data.append(cell_content)
            print(f"   Row {row}: {row_data}")
        
        # Check for multi-booking patterns
        multi_booking_patterns = ['cab 1', 'cab 2', 'cab 3', 'cab 4']
        patterns_found = []
        
        for row in table_data.values():
            for cell_content in row.values():
                cell_lower = cell_content.lower()
                for pattern in multi_booking_patterns:
                    if pattern in cell_lower and pattern not in patterns_found:
                        patterns_found.append(pattern)
        
        print(f"\n🎯 Multi-booking patterns in table: {patterns_found}")
        
        # Check if this looks like a multi-booking table
        if len(patterns_found) >= 2:  # At least 2 cab columns
            print("✅ This table appears to contain multi-booking data!")
        else:
            print("⚠️  This table may not be recognized as multi-booking format")
        
        extracted_tables.append(table_data)
    
    return extracted_tables

def extract_text_from_block(block, block_map):
    """Helper function to extract text from a block"""
    text = ""
    
    if 'Text' in block:
        return block['Text']
    
    # If no direct text, look for child WORD blocks
    for relationship in block.get('Relationships', []):
        if relationship['Type'] == 'CHILD':
            for child_id in relationship['Ids']:
                if child_id in block_map:
                    child_block = block_map[child_id]
                    if child_block['BlockType'] == 'WORD':
                        if text:
                            text += ' '
                        text += child_block.get('Text', '')
    
    return text

def debug_textract_extraction():
    """Debug what Textract actually extracts from your image"""
    
    print(f"🧪 ENHANCED TEXTRACT DEBUGGING SCRIPT")
    print(f"This script analyzes exactly what AWS Textract extracts from your images.")
    print(f"It uses the same FORMS + TABLES analysis as your system.")
    print(f"Target image: multi-bookings images\\Screenshot 2025-09-16 004941.png\n")
    
    # Check AWS credentials first
    try:
        import boto3
        session = boto3.Session()
        credentials = session.get_credentials()
        if credentials is None:
            print(f"❌ AWS credentials not found!")
            print(f"Please configure AWS credentials using one of these methods:")
            print(f"   1. AWS CLI: aws configure")
            print(f"   2. Environment variables: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY")
            print(f"   3. IAM role (if running on EC2)")
            return
        else:
            print(f"✅ AWS credentials found")
            # Test Textract service availability
            try:
                textract_client = boto3.client('textract')
                # This is a simple check - we don't actually call the service yet
                print(f"✅ Textract client initialized successfully")
            except Exception as e:
                print(f"❌ Error initializing Textract client: {e}")
                return
    except Exception as e:
        print(f"❌ Error checking AWS setup: {e}")
        return
    
    # Create processor
    processor = EnhancedMultiBookingProcessor()
    
    # Use the specific multi-booking image
    test_image_path = r"multi-bookings images\Screenshot 2025-09-16 004941.png"
    
    extracted_data = None
    raw_response = None
    
    # Check if the specific image exists
    if os.path.exists(test_image_path):
        print(f"📁 Found target image: {test_image_path}")
        
        try:
            # Read the actual image file
            with open(test_image_path, 'rb') as f:
                file_content = f.read()
            
            # Validate it's actually an image file
            if len(file_content) < 100:
                print(f"❌ Image file seems too small ({len(file_content)} bytes) - may be corrupted")
                return
            
            # Check for common image headers
            header = file_content[:10]
            is_png = header.startswith(b'\x89PNG')
            is_jpg = header.startswith(b'\xff\xd8\xff')
            
            if not (is_png or is_jpg):
                print(f"⚠️  Warning: File may not be a valid image (header: {header.hex()})")
            else:
                image_type = "PNG" if is_png else "JPEG"
                print(f"✅ Valid {image_type} image detected")
            
            print(f"📁 Processing actual image: {test_image_path} ({len(file_content)} bytes)")
            print(f"📝 This is the multi-booking table image that should contain 4 cab bookings")
            
            # First, analyze the raw Textract response
            raw_response = analyze_raw_textract_response(file_content, test_image_path)
            
            if raw_response:
                # Then, extract structured data using the system's method
                extracted_data = processor._extract_structured_data(file_content, test_image_path)
                print("\n✅ System's structured data extraction completed!")
            else:
                print("\n❌ Raw Textract analysis failed - cannot proceed with system analysis")
                return
            
        except FileNotFoundError:
            print(f"❌ Image file not found: {test_image_path}")
            print("Please make sure the file exists in the correct location.")
            return
        except Exception as e:
            print(f"❌ Error reading image file: {e}")
            import traceback
            traceback.print_exc()
            return
    else:
        # Also check for any other multi-booking images as fallback
        fallback_patterns = [
            r"multi-bookings images\*.png",
            r"multi-bookings images\*.jpg", 
            r"multi-bookings images\*.jpeg",
            "*.png", "*.jpg", "*.jpeg"  # Current directory as last resort
        ]
        
        found_image = None
        for pattern in fallback_patterns:
            matches = glob.glob(pattern)
            if matches:
                found_image = matches[0]
                print(f"📁 Target image not found, using fallback: {found_image}")
                break
        
        if found_image:
            try:
                with open(found_image, 'rb') as f:
                    file_content = f.read()
                print(f"📁 Processing fallback image: {found_image} ({len(file_content)} bytes)")
                raw_response = analyze_raw_textract_response(file_content, found_image)
                if raw_response:
                    extracted_data = processor._extract_structured_data(file_content, found_image)
            except Exception as e:
                print(f"❌ Error processing fallback image: {e}")
                return
        else:
            print(f"❌ No image files found!")
            print(f"Please make sure the image exists at: {test_image_path}")
            print(f"Or place some image files in the current directory.")
            return
    
    if not extracted_data:
        print("❌ No data available for analysis")
        return
    
    print(f"\n📊 SYSTEM'S STRUCTURED DATA EXTRACTION RESULTS:")
    print("="*80)
    
    kv_pairs = extracted_data.get('key_value_pairs', [])
    tables = extracted_data.get('tables', [])
    raw_text = extracted_data.get('raw_text', '')
    
    print(f"Key-value pairs extracted: {len(kv_pairs)}")
    print(f"Tables extracted: {len(tables)}")
    print(f"Raw text length: {len(raw_text)} characters")
    
    # Show some key-value pairs
    if kv_pairs:
        print(f"\n🔑 SAMPLE KEY-VALUE PAIRS (first 10):")
        for i, kv in enumerate(kv_pairs[:10]):
            print(f"   {i+1:2d}. '{kv.get('key', '')}' → '{kv.get('value', '')}'")
        if len(kv_pairs) > 10:
            print(f"   ... and {len(kv_pairs)-10} more pairs")
    
    # Analyze tables in detail
    if tables:
        print(f"\n📊 SYSTEM'S TABLE EXTRACTION RESULTS:")
        for i, table in enumerate(tables):
            print(f"\n=== TABLE {i+1} ===")
            print(f"Type: {table.get('type', 'unknown')}")
            print(f"Headers: {table.get('headers', [])}")
            print(f"Rows: {len(table.get('rows', []))}")
            print(f"Columns: {table.get('column_count', 'unknown')}")
            
            # Show table structure
            rows = table.get('rows', [])
            if rows:
                print(f"\nTable structure:")
                for j, row in enumerate(rows[:8]):  # Show first 8 rows
                    print(f"   Row {j:2d}: {row}")
                
                if len(rows) > 8:
                    print(f"   ... and {len(rows)-8} more rows")
            
            # Check for multi-booking indicators
            table_text = str(table).lower()
            multi_indicators = ['cab 1', 'cab 2', 'cab 3', 'cab 4']
            found_in_table = [ind for ind in multi_indicators if ind in table_text]
            print(f"Multi-booking indicators in table: {found_in_table}")
    else:
        print(f"\n⚠️  NO TABLES EXTRACTED BY SYSTEM - This explains the multi-booking issue!")
    
    # Show sample raw text
    if raw_text:
        print(f"\n📝 SAMPLE RAW TEXT (first 500 characters):")
        print(f"   {raw_text[:500]}{'...' if len(raw_text) > 500 else ''}")
        
        # Check for multi-booking patterns in raw text
        raw_lower = raw_text.lower()
        multi_indicators = ['cab 1', 'cab 2', 'cab 3', 'cab 4', 'jayasheel', 'crysta', 'lendingkart']
        found_in_raw = [ind for ind in multi_indicators if ind in raw_lower]
        print(f"Multi-booking indicators in raw text: {found_in_raw}")
    
    # Test the booking extraction
    print(f"\n🔍 TESTING MULTI-BOOKING EXTRACTION LOGIC:")
    print("-"*60)
    
    try:
        # Apply Textract corrections
        print(f"1. Applying Textract corrections...")
        corrected_data = processor._apply_textract_corrections(extracted_data)
        
        corrected_tables = corrected_data.get('tables', [])
        if len(corrected_tables) > len(tables):
            print(f"   ✅ Corrections added {len(corrected_tables) - len(tables)} reconstructed tables")
        else:
            print(f"   ⚠️  No table reconstruction was needed")
        
        # Extract bookings
        print(f"2. Extracting bookings from tables...")
        bookings = processor._extract_multiple_bookings_from_tables(corrected_data)
        print(f"   Result: {len(bookings)} bookings extracted")
        
        if len(bookings) == 0:
            print(f"\n❌ PROBLEM IDENTIFIED: No bookings found!")
            print(f"This is why your multi-booking extraction is not working.")
            print(f"\nPossible causes:")
            print(f"   1. Textract is not detecting tables properly")
            print(f"   2. Table structure is not recognized as multi-booking format")
            print(f"   3. Column headers are not being identified correctly")
            
            # Debug the horizontal table processing specifically
            print(f"\n🔧 DEBUGGING TABLE PROCESSING LOGIC:")
            for i, table in enumerate(corrected_tables):
                print(f"\n--- Testing table {i+1} ---")
                print(f"Table type: {table.get('type', 'unknown')}")
                print(f"Headers: {table.get('headers', [])}")
                
                if table.get('type') == 'regular_table':
                    print(f"Processing as horizontal table...")
                    test_bookings = processor._extract_from_horizontal_table(table)
                    print(f"Result: {len(test_bookings)} bookings from horizontal table")
                    
                    if len(test_bookings) == 0:
                        print(f"   ❌ Horizontal table processing failed")
                        print(f"   Debug: Headers detected = {table.get('headers', [])}")
                        
                        # Check if headers contain booking columns
                        headers = table.get('headers', [])
                        booking_cols = []
                        for j, header in enumerate(headers):
                            header_lower = (header or '').lower()
                            if any(pattern in header_lower for pattern in ['cab', 'booking']):
                                booking_cols.append(f"Column {j}: '{header}'")
                        
                        print(f"   Debug: Booking columns found = {booking_cols}")
                        
                        if not booking_cols:
                            print(f"   ❌ Issue: No 'cab' or 'booking' columns detected in headers")
                    else:
                        print(f"   ✅ Horizontal table processing successful!")
                        
                elif table.get('type') == 'form_table':
                    print(f"Processing as vertical table...")
                    test_bookings = processor._extract_from_vertical_table(table)
                    print(f"Result: {len(test_bookings)} bookings from vertical table")
                else:
                    print(f"   ⚠️  Unknown table type, skipping")
            
        else:
            print(f"\n✅ SUCCESS: Found {len(bookings)} bookings!")
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
                print(f"Confidence: {booking.confidence_score:.2f}")
    
    except Exception as e:
        print(f"❌ Booking extraction failed with error: {e}")
        import traceback
        print(f"Full error traceback:")
        traceback.print_exc()
    
    # Final analysis and recommendations
    print(f"\n📝 ANALYSIS SUMMARY AND RECOMMENDATIONS:")
    print("="*80)
    
    if raw_response:
        raw_table_blocks = [b for b in raw_response.get('Blocks', []) if b.get('BlockType') == 'TABLE']
        print(f"Raw Textract detected {len(raw_table_blocks)} table(s)")
    else:
        raw_table_blocks = []
    
    system_tables = len(tables)
    corrected_tables = len(corrected_data.get('tables', [])) if 'corrected_data' in locals() else 0
    final_bookings = len(bookings) if 'bookings' in locals() else 0
    
    print(f"System extracted {system_tables} table(s) from raw Textract data")
    print(f"After corrections: {corrected_tables} table(s)")
    print(f"Final bookings extracted: {final_bookings}")
    
    if final_bookings == 0:
        print(f"\n❌ ROOT CAUSE ANALYSIS:")
        if len(raw_table_blocks) == 0:
            print(f"   ➡️  Textract is not detecting any tables in your image")
            print(f"   ➡️  This could be due to image quality, table formatting, or layout issues")
            print(f"   ➡️  RECOMMENDATION: Check image resolution, contrast, and table boundaries")
        elif system_tables == 0:
            print(f"   ➡️  Textract detected tables but system failed to extract them")
            print(f"   ➡️  This is a bug in the table extraction logic")
            print(f"   ➡️  RECOMMENDATION: Debug _extract_enhanced_tables method")
        elif corrected_tables > 0 and final_bookings == 0:
            print(f"   ➡️  Tables were extracted but no bookings found")
            print(f"   ➡️  This suggests table structure is not recognized as multi-booking")
            print(f"   ➡️  RECOMMENDATION: Check column header detection logic")
    elif final_bookings < 4:
        print(f"\n⚠️  PARTIAL SUCCESS:")
        print(f"   ➡️  Found {final_bookings} booking(s) but expected 4")
        print(f"   ➡️  Some bookings may be missing or merged")
        print(f"   ➡️  RECOMMENDATION: Check horizontal table processing logic")
    else:
        print(f"\n✅ EXTRACTION WORKING CORRECTLY!")
        print(f"   ➡️  All {final_bookings} bookings were successfully extracted")
    
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

if __name__ == "__main__":
    debug_textract_extraction()