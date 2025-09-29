#!/usr/bin/env python3
"""
Test vertical layout processing with the table structure from logs
"""

def test_vertical_layout_detection():
    """Test if our vertical layout detection works"""
    
    # Sample table structure from the logs
    sample_table = {
        'type': 'regular_table',
        'headers': ['', 'SR.', 'Date', 'Location', 'Type', 'Reporting Time', 'Car Type', 'Name', 'Contact', 'Pickup Address', 'Drop Address'],
        'rows': [
            ['', 'SR.', 'Date', 'Location', 'Type', 'Reporting Time', 'Car Type', 'Name', 'Contact', 'Pickup Address', 'Drop Address'],
            ['', '1', '17-09-2025', 'Kochi', 'Local', '07:00PM', 'Dzire', 'Shreejit Menon', '9820505442', 'Kochi Airport Terminal 1', 'Vivanta Ernakulam'],
            ['', '2', '18-09-2025', 'Kochi', 'Local', '05:00PM', 'Dzire', 'Shreejit Menon', '9820505442', 'Vivanta Ernakulam', 'Kochi Airport Terminal 1'],
            ['', '2', '18-09-2025', 'Mumbai', 'Local', '10:30PM', 'Dzire', 'Shreejit Menon', '9820505442', 'Chhatrapati Shivaji Airport', 'Rustomjee Ozone Tower']
        ],
        'row_count': 4,
        'column_count': 11
    }
    
    # Test vertical layout detection logic
    headers = sample_table.get('headers', [])
    rows = sample_table.get('rows', [])
    
    vertical_layout_indicators = [
        'date', 'name', 'contact', 'address', 'time', 'location', 
        'pickup', 'drop', 'passenger', 'phone', 'sr.', 'sr'
    ]
    
    header_text = ' '.join(str(h).lower() for h in headers if h)
    has_vertical_indicators = any(indicator in header_text for indicator in vertical_layout_indicators)
    has_horizontal_indicators = any(pattern in header_text for pattern in ['cab 1', 'cab 2', 'cab 3', 'booking 1', 'booking 2'])
    
    # Check if we have multiple data rows (excluding header row)
    data_rows = [row for row in rows[1:] if row and any(str(cell).strip() for cell in row)]
    has_multiple_data_rows = len(data_rows) >= 2
    
    print("🧪 TESTING VERTICAL LAYOUT DETECTION")
    print("=" * 50)
    print(f"Header text: {header_text}")
    print(f"Has vertical indicators: {has_vertical_indicators}")
    print(f"Has horizontal indicators: {has_horizontal_indicators}")
    print(f"Data rows: {len(data_rows)}")
    print(f"Has multiple data rows: {has_multiple_data_rows}")
    
    should_be_vertical = has_vertical_indicators and not has_horizontal_indicators and has_multiple_data_rows
    print(f"\n🎯 DETECTION RESULT: {'VERTICAL' if should_be_vertical else 'HORIZONTAL'} layout")
    
    if should_be_vertical:
        print("✅ SUCCESS: This table should be processed as vertical layout")
        
        # Test header mapping
        print("\n📋 HEADER MAPPING TEST:")
        from enhanced_multi_booking_processor import EnhancedMultiBookingProcessor
        
        processor = EnhancedMultiBookingProcessor()
        
        header_mapping = {}
        for i, header in enumerate(headers):
            if header and str(header).strip():
                mapped_field = processor._map_field_name(str(header).strip())
                if mapped_field:
                    header_mapping[i] = mapped_field
                    print(f"  Column {i} ('{header}') → '{mapped_field}'")
        
        print(f"\n📊 Expected bookings: {len(data_rows)} (one per row)")
        print("Row 1: Kochi Airport → Vivanta Ernakulam (17-09-2025)")
        print("Row 2: Vivanta Ernakulam → Kochi Airport (18-09-2025)")  
        print("Row 3: Mumbai Airport → Rustomjee Tower (18-09-2025)")
        
        return True
    else:
        print("❌ FAILED: This table should be detected as vertical but wasn't")
        return False

if __name__ == "__main__":
    test_vertical_layout_detection()