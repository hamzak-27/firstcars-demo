#!/usr/bin/env python3
"""
Test script for multi-booking extraction
"""

import os
import logging
from enhanced_multi_booking_processor import EnhancedMultiBookingProcessor

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_table_extraction():
    """Test multi-booking extraction with simulated table data"""
    
    # Create processor
    processor = EnhancedMultiBookingProcessor()
    
    # Simulate extracted table data (like what Textract would return)
    extracted_data = {
        'tables': [{
            'type': 'regular_table',
            'headers': ['Cab Booking Format', 'Cab 1', 'Cab 2', 'Cab 3', 'Cab 4'],
            'rows': [
                ['Cab Booking Format', 'Cab 1', 'Cab 2', 'Cab 3', 'Cab 4'],  # Header row
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
        }]
    }
    
    # Extract bookings
    logger.info("Testing multi-booking extraction...")
    bookings = processor._extract_multiple_bookings_from_tables(extracted_data)
    
    logger.info(f"Extraction completed. Found {len(bookings)} bookings")
    
    # Print results
    for i, booking in enumerate(bookings, 1):
        logger.info(f"\n=== Booking {i} ===")
        logger.info(f"Passenger: {booking.passenger_name}")
        logger.info(f"Phone: {booking.passenger_phone}")
        logger.info(f"Company: {booking.corporate}")
        logger.info(f"City: {booking.from_location}")
        logger.info(f"Date: {booking.start_date}")
        logger.info(f"Time: {booking.reporting_time}")
        logger.info(f"Vehicle: {booking.vehicle_group}")
        logger.info(f"Pickup: {booking.reporting_address}")
        logger.info(f"Drop: {booking.drop_address}")
        logger.info(f"Flight: {booking.flight_train_number}")
        logger.info(f"Confidence: {booking.confidence_score}")
    
    return len(bookings)

if __name__ == "__main__":
    try:
        booking_count = test_table_extraction()
        if booking_count >= 4:
            print(f"\n✅ SUCCESS: Found {booking_count} bookings as expected!")
        else:
            print(f"\n❌ ISSUE: Only found {booking_count} bookings, expected 4")
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()