#!/usr/bin/env python3
"""
Debug script to test image processing and identify why bookings aren't being detected
"""

import logging
import os
import sys

# Set up detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_image_processing(image_path: str):
    """Test image processing with detailed logging"""
    
    try:
        # Step 1: Test EnhancedMultiBookingProcessor
        logger.info("=" * 60)
        logger.info("TESTING ENHANCED MULTI-BOOKING PROCESSOR")
        logger.info("=" * 60)
        
        from enhanced_multi_booking_processor import EnhancedMultiBookingProcessor
        processor = EnhancedMultiBookingProcessor()
        
        # Read image
        with open(image_path, 'rb') as f:
            image_content = f.read()
        
        logger.info(f"Image file size: {len(image_content)} bytes")
        
        # Process image
        result = processor.process_multi_booking_document(
            image_content, 
            os.path.basename(image_path), 
            image_path.split('.')[-1].lower()
        )
        
        logger.info(f"Processing result: {result}")
        logger.info(f"Number of bookings found: {len(result.bookings) if result.bookings else 0}")
        logger.info(f"Processing notes: {result.processing_notes}")
        logger.info(f"Extraction method: {result.extraction_method}")
        
        if result.bookings:
            for i, booking in enumerate(result.bookings, 1):
                logger.info(f"Booking {i}:")
                logger.info(f"  - Passenger: {booking.passenger_name}")
                logger.info(f"  - Phone: {booking.passenger_phone}")
                logger.info(f"  - Date: {booking.start_date}")
                logger.info(f"  - Time: {booking.reporting_time}")
                logger.info(f"  - From: {booking.from_location or booking.reporting_address}")
                logger.info(f"  - To: {booking.to_location or booking.drop_address}")
                logger.info(f"  - Vehicle: {booking.vehicle_group}")
                logger.info(f"  - Corporate: {booking.corporate}")
        
        # Step 2: Test the complete orchestrator pipeline
        logger.info("=" * 60)
        logger.info("TESTING COMPLETE MULTI-AGENT ORCHESTRATOR")
        logger.info("=" * 60)
        
        from complete_multi_agent_orchestrator import CompleteMultiAgentOrchestrator
        
        # Set up API key
        api_key = os.getenv('GEMINI_API_KEY', 'test-key')
        orchestrator = CompleteMultiAgentOrchestrator(api_key=api_key)
        
        # Convert the result to text format for the orchestrator
        if result.bookings:
            booking_summaries = []
            for i, booking in enumerate(result.bookings, 1):
                summary = f"Booking {i}:\n"
                summary += f"- Passenger: {booking.passenger_name or 'N/A'} ({booking.passenger_phone or 'N/A'})\n"
                summary += f"- Company: {booking.corporate or 'N/A'}\n"
                summary += f"- Date: {booking.start_date or 'N/A'}\n"
                summary += f"- Time: {booking.reporting_time or 'N/A'}\n"
                summary += f"- Vehicle: {booking.vehicle_group or 'N/A'}\n"
                summary += f"- From: {booking.from_location or booking.reporting_address or 'N/A'}\n"
                summary += f"- To: {booking.to_location or booking.drop_address or 'N/A'}\n"
                summary += f"- Flight: {booking.flight_train_number or 'N/A'}\n"
                if booking.remarks:
                    summary += f"- Remarks: {booking.remarks}\n"
                booking_summaries.append(summary)
            
            content = f"TABLE EXTRACTION RESULTS ({len(result.bookings)} bookings found):\n\n" + "\n".join(booking_summaries)
            content += f"\n\nOriginal processing method: {result.extraction_method}"
        else:
            content = f"Table processed but no bookings found. Processing notes: {result.processing_notes or 'None'}"
        
        logger.info(f"Content being sent to orchestrator:")
        logger.info("-" * 40)
        logger.info(content)
        logger.info("-" * 40)
        
        # Process through orchestrator
        orchestrator_result = orchestrator.process_content(
            content=content,
            source_type="file_upload_debug"
        )
        
        logger.info(f"Orchestrator result: {orchestrator_result}")
        logger.info(f"Final booking count: {orchestrator_result.get('booking_count', 0)}")
        
        if orchestrator_result.get('final_dataframe') is not None:
            df = orchestrator_result['final_dataframe']
            logger.info(f"Final DataFrame shape: {df.shape}")
            logger.info(f"Final DataFrame columns: {list(df.columns)}")
            if not df.empty:
                logger.info("Final DataFrame preview:")
                logger.info(df.head().to_string())
        
        return result, orchestrator_result
        
    except Exception as e:
        logger.error(f"Error in test_image_processing: {e}", exc_info=True)
        return None, None

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python debug_image_processing.py <path_to_image>")
        print("Example: python debug_image_processing.py test_image.png")
        sys.exit(1)
    
    image_path = sys.argv[1]
    
    if not os.path.exists(image_path):
        print(f"Error: Image file not found: {image_path}")
        sys.exit(1)
    
    print(f"Testing image processing for: {image_path}")
    test_image_processing(image_path)