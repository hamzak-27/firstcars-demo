"""
Test script for Enhanced Multi-Booking Table Processor
Demonstrates handling of complex table layouts with multiple bookings
"""

import os
import sys
import logging
from pathlib import Path

# Add the current directory to the Python path
sys.path.append(str(Path(__file__).parent))

from enhanced_multi_booking_processor import EnhancedMultiBookingProcessor

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_multi_booking_processor():
    """Test the enhanced multi-booking processor"""
    
    # Initialize the processor
    processor = EnhancedMultiBookingProcessor()
    
    if not processor.textract_available:
        logger.warning("AWS Textract not available. Please configure AWS credentials.")
        return
    
    logger.info("=== ENHANCED MULTI-BOOKING PROCESSOR TEST ===")
    
    # Test files (replace with your actual multi-booking form files)
    test_files = [
        # Add paths to your multi-booking form images here
        # "path/to/your/vertical_multi_booking.jpg",
        # "path/to/your/horizontal_multi_booking.jpg", 
    ]
    
    if not test_files:
        logger.info("No test files specified. Please add file paths to the test_files list.")
        logger.info("Expected file formats:")
        logger.info("1. Vertical layout: Date & City/Car | Pick up-Time | Global Leaders | etc.")
        logger.info("2. Horizontal layout: Cab 1 | Cab 2 | Cab 3 | Cab 4 columns")
        return
    
    for file_path in test_files:
        if not os.path.exists(file_path):
            logger.warning(f"File not found: {file_path}")
            continue
        
        try:
            logger.info(f"\\n{'='*60}")
            logger.info(f"Processing multi-booking file: {file_path}")
            
            # Read the file
            with open(file_path, 'rb') as f:
                file_content = f.read()
            
            filename = os.path.basename(file_path)
            file_type = filename.split('.')[-1].lower()
            
            # Process with enhanced multi-booking processor
            result = processor.process_multi_booking_document(file_content, filename, file_type)
            
            # Display results
            logger.info(f"\\n📊 MULTI-BOOKING EXTRACTION RESULTS:")
            logger.info(f"  Extraction method: {result.extraction_method}")
            logger.info(f"  Total bookings found: {result.total_bookings_found}")
            logger.info(f"  Overall confidence: {result.confidence_score:.1%}")
            logger.info(f"  Processing notes: {result.processing_notes}")
            
            # Display each booking
            for i, booking in enumerate(result.bookings):
                logger.info(f"\\n  🚗 BOOKING {i+1}:")
                logger.info(f"    Passenger: {booking.passenger_name or 'Not specified'}")
                logger.info(f"    Phone: {booking.passenger_phone or 'Not specified'}")
                logger.info(f"    Travel Date: {booking.start_date or 'Not specified'}")
                logger.info(f"    Pickup Time: {booking.reporting_time or 'Not specified'}")
                logger.info(f"    Vehicle: {booking.vehicle_group or 'Not specified'}")
                logger.info(f"    From: {booking.from_location or booking.reporting_address or 'Not specified'}")
                logger.info(f"    To: {booking.to_location or booking.drop_address or 'Not specified'}")
                logger.info(f"    Company: {booking.corporate or 'Not specified'}")
                logger.info(f"    Flight: {booking.flight_train_number or 'Not specified'}")
                logger.info(f"    Duty Type: {booking.duty_type or 'Not specified'}")
                logger.info(f"    Confidence: {booking.confidence_score:.1%}")
                
                if booking.remarks:
                    logger.info(f"    Remarks: {booking.remarks}")
                
                # Show enhanced duty type reasoning
                if hasattr(booking, 'duty_type_reasoning') and booking.duty_type_reasoning:
                    logger.info(f"\\n    🔍 Duty Type Analysis:")
                    reasoning_lines = booking.duty_type_reasoning.split('\\n')[:5]  # Show first 5 lines
                    for line in reasoning_lines:
                        if line.strip():
                            logger.info(f"    {line}")
            
        except Exception as e:
            logger.error(f"Error processing {file_path}: {str(e)}")
            import traceback
            traceback.print_exc()

def demo_table_structure_analysis():
    """Demonstrate how the processor handles different table structures"""
    
    logger.info("\\n=== TABLE STRUCTURE ANALYSIS DEMO ===")
    
    # Mock data representing your table structures
    logger.info("\\n📋 VERTICAL TABLE LAYOUT (First Image):")
    logger.info("   Date & City / Car    | Sep 16, Tuesday At disposal")
    logger.info("   Pick up – Time       | 9:15am")
    logger.info("   Global Leaders       | Carol Perez, Craig Hazledine")
    logger.info("   Pick up Address      | Cytiva / GE, Gate 2")
    logger.info("   Drop address         | Gmap - Oterra hotel Electronic city")
    logger.info("   Comments            | Wait till meeting gets over...")
    logger.info("   ↓")
    logger.info("   🎯 EXTRACTION LOGIC:")
    logger.info("      - Detects key-value pairs from form structure")
    logger.info("      - Maps 'Global Leaders' → passenger_name")
    logger.info("      - Maps 'Date & City / Car' → start_date + duty_type") 
    logger.info("      - Maps 'Pick up Address' → reporting_address")
    
    logger.info("\\n📊 HORIZONTAL TABLE LAYOUT (Second Image):")
    logger.info("   Field Names    | Cab 1              | Cab 2              | Cab 3")
    logger.info("   Name of Employee| Jayasheel Bhansali | Jayasheel Bhansali | Jayasheel Bhansali")
    logger.info("   Contact Number  | 7001682596         | 7001682596         | 7001682596")
    logger.info("   City           | Bangalore          | Bangalore          | Mumbai")
    logger.info("   Date of Travel | 19-Sep-25          | 20-21 Sep 2025     | 21-Sep-25")
    logger.info("   ↓")
    logger.info("   🎯 EXTRACTION LOGIC:")
    logger.info("      - Detects columns as separate bookings")
    logger.info("      - Maps row headers to field names")
    logger.info("      - Creates one booking per column")
    logger.info("      - Handles multi-date ranges (20-21 Sep)")
    
    logger.info("\\n🚀 ENHANCED FEATURES:")
    logger.info("   ✅ Handles both vertical and horizontal layouts")
    logger.info("   ✅ Maps field names intelligently")
    logger.info("   ✅ Splits combined fields (Date & City)")
    logger.info("   ✅ Normalizes vehicle types (CRYSTA → Toyota Innova Crysta)")
    logger.info("   ✅ Enhanced duty type detection from structured data")
    logger.info("   ✅ Confidence scoring per booking")

def compare_single_vs_multi_booking():
    """Compare single vs multi-booking processing approaches"""
    
    logger.info("\\n=== SINGLE vs MULTI-BOOKING COMPARISON ===")
    
    logger.info("\\n📄 SINGLE BOOKING PROCESSING:")
    logger.info("   - Uses enhanced_form_processor.py")
    logger.info("   - Extracts one booking per document")
    logger.info("   - Good for simple travel requisition forms")
    logger.info("   - Example: Travel request with one passenger, one trip")
    
    logger.info("\\n📊 MULTI-BOOKING PROCESSING:")
    logger.info("   - Uses enhanced_multi_booking_processor.py") 
    logger.info("   - Extracts multiple bookings from tables")
    logger.info("   - Handles complex layouts (vertical/horizontal)")
    logger.info("   - Example: Multiple employees, multiple trips, multiple dates")
    
    logger.info("\\n🎯 WHEN TO USE EACH:")
    logger.info("   📋 Single Booking: Travel requisition forms, expense reports")
    logger.info("   📊 Multi Booking: Team travel schedules, bulk booking requests")
    
    logger.info("\\n💡 INTEGRATION STRATEGY:")
    logger.info("   1. Try multi-booking processor first")
    logger.info("   2. If only 1 booking found → use single booking processor")
    logger.info("   3. If multiple bookings → continue with multi-booking processor")

if __name__ == "__main__":
    logger.info("Testing Enhanced Multi-Booking Table Processor...")
    
    # Test 1: Multi-booking processor
    test_multi_booking_processor()
    
    # Test 2: Table structure analysis demo
    demo_table_structure_analysis()
    
    # Test 3: Comparison between approaches
    compare_single_vs_multi_booking()
    
    logger.info("\\n✅ Enhanced multi-booking processor tests completed!")
    logger.info("\\n💡 KEY FEATURES:")
    logger.info("   1. Handles vertical table layouts (key-value pairs)")
    logger.info("   2. Handles horizontal table layouts (columns as bookings)")
    logger.info("   3. Intelligent field name mapping")
    logger.info("   4. Enhanced duty type detection per booking")
    logger.info("   5. Confidence scoring and validation")
    logger.info("   6. Fallback to single booking extraction")