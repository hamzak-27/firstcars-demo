"""
Test script for the Enhanced Form Processor
Demonstrates the improvements in table and form extraction
"""

import os
import sys
import logging
from pathlib import Path

# Add the current directory to the Python path
sys.path.append(str(Path(__file__).parent))

from enhanced_form_processor import EnhancedFormProcessor

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_enhanced_form_processor():
    """Test the enhanced form processor with sample forms"""
    
    # Initialize the processor
    processor = EnhancedFormProcessor()
    
    if not processor.textract_available:
        logger.warning("AWS Textract not available. Please configure AWS credentials.")
        return
    
    # Test with a sample file (you would replace this with your actual file path)
    test_files = [
        # Add paths to your sample form images here
        # "path/to/your/travel_form_1.jpg",
        # "path/to/your/travel_form_2.png",
    ]
    
    if not test_files:
        logger.info("No test files specified. Please add file paths to the test_files list.")
        return
    
    for file_path in test_files:
        if not os.path.exists(file_path):
            logger.warning(f"File not found: {file_path}")
            continue
        
        try:
            logger.info(f"Processing file: {file_path}")
            
            # Read the file
            with open(file_path, 'rb') as f:
                file_content = f.read()
            
            filename = os.path.basename(file_path)
            file_type = filename.split('.')[-1].lower()
            
            # Process with enhanced form processor
            result = processor.process_document(file_content, filename, file_type)
            
            # Display results
            logger.info(f"Results for {filename}:")
            logger.info(f"  Extraction method: {result.extraction_method}")
            logger.info(f"  Total bookings found: {result.total_bookings_found}")
            logger.info(f"  Confidence score: {result.confidence_score}")
            logger.info(f"  Processing notes: {result.processing_notes}")
            
            for i, booking in enumerate(result.bookings):
                logger.info(f"  Booking {i+1}:")
                logger.info(f"    Guest name: {booking.guest_name}")
                logger.info(f"    Mobile number: {booking.mobile_number}")
                logger.info(f"    Pickup city: {booking.pickup_city}")
                logger.info(f"    Car type: {booking.car_type}")
                logger.info(f"    Date: {booking.date_of_requirement}")
                logger.info(f"    Company: {booking.company_name}")
                logger.info(f"    Confidence: {booking.confidence_score}")
                if booking.additional_info:
                    logger.info(f"    Additional info: {booking.additional_info[:200]}...")
                logger.info("")
            
        except Exception as e:
            logger.error(f"Error processing {file_path}: {str(e)}")

def compare_processors():
    """Compare the old and new processors side by side"""
    
    from document_processor import DocumentProcessor  # Your old processor
    
    old_processor = DocumentProcessor()
    new_processor = EnhancedFormProcessor()
    
    # Test file path - replace with your actual file
    test_file = "path/to/your/test_form.jpg"
    
    if not os.path.exists(test_file):
        logger.warning(f"Test file not found: {test_file}")
        return
    
    with open(test_file, 'rb') as f:
        file_content = f.read()
    
    filename = os.path.basename(test_file)
    file_type = filename.split('.')[-1].lower()
    
    # Process with both processors
    logger.info("=== OLD PROCESSOR RESULTS ===")
    old_result = old_processor.process_document(file_content, filename, file_type)
    display_result(old_result, "Old Processor")
    
    logger.info("\\n=== NEW ENHANCED PROCESSOR RESULTS ===")
    new_result = new_processor.process_document(file_content, filename, file_type)
    display_result(new_result, "Enhanced Processor")

def display_result(result, processor_name):
    """Display processing results"""
    logger.info(f"{processor_name} Results:")
    logger.info(f"  Method: {result.extraction_method}")
    logger.info(f"  Bookings: {result.total_bookings_found}")
    logger.info(f"  Confidence: {result.confidence_score}")
    
    for i, booking in enumerate(result.bookings):
        logger.info(f"  Booking {i+1}: {booking.guest_name} | {booking.mobile_number} | {booking.pickup_city}")

if __name__ == "__main__":
    logger.info("Testing Enhanced Form Processor...")
    
    # You can run either test
    test_enhanced_form_processor()
    
    # Uncomment to compare old vs new processors
    # compare_processors()