#!/usr/bin/env python3
"""
Final Integration Test for Multi-Booking Pipeline
Tests the complete flow from image upload through the full app pipeline
"""

import os
import sys
import logging
import tempfile

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_complete_pipeline():
    """Test the complete multi-booking pipeline end-to-end"""
    
    print("🧪 FINAL INTEGRATION TEST - COMPLETE MULTI-BOOKING PIPELINE")
    print("=" * 80)
    
    # Test 1: Enhanced Multi-Booking Processor Direct Test
    print("\n📊 TEST 1: Enhanced Multi-Booking Processor (Direct)")
    print("-" * 50)
    
    try:
        from enhanced_multi_booking_processor import EnhancedMultiBookingProcessor
        
        # Find the test image
        test_image = "multi-bookings images/Screenshot 2025-09-16 004941.png"
        if not os.path.exists(test_image):
            print(f"❌ Test image not found: {test_image}")
            return False
        
        processor = EnhancedMultiBookingProcessor()
        bookings = processor.process_document(test_image)
        
        print(f"✅ Processor extracted {len(bookings)} bookings")
        for i, booking in enumerate(bookings, 1):
            print(f"   Booking {i}: {booking.get('Passenger Name', 'N/A')} - {booking.get('Date', 'N/A')}")
        
    except Exception as e:
        print(f"❌ Processor test failed: {e}")
        return False
    
    # Test 2: App File Processing Function
    print("\n🎯 TEST 2: App File Processing Function")
    print("-" * 50)
    
    try:
        # Read the test image
        with open(test_image, 'rb') as f:
            file_content = f.read()
        
        # Create a mock uploaded file object
        class MockUploadedFile:
            def __init__(self, content, name):
                self.content = content
                self.name = name
                
            def getvalue(self):
                return self.content
            
            def read(self):
                return self.content
        
        mock_file = MockUploadedFile(file_content, "test_table.png")
        
        # Import and initialize the orchestrator
        from complete_multi_agent_orchestrator import CompleteMultiAgentOrchestrator
        
        # Use dummy API key since we're testing preprocessed content
        orchestrator = CompleteMultiAgentOrchestrator(api_key="dummy_key_for_test")
        
        # Simulate the app's file processing
        from enhanced_multi_booking_processor import EnhancedMultiBookingProcessor
        multi_processor = EnhancedMultiBookingProcessor()
        
        # Save file temporarily for processing (like the app does)
        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_file:
            tmp_file.write(file_content)
            temp_path = tmp_file.name
        
        try:
            # Process the image
            bookings = multi_processor.process_document(temp_path)
            
            # Format like the app does
            booking_summaries = []
            for i, booking in enumerate(bookings, 1):
                summary = f"Booking {i}:\\n"
                summary += f"- Passenger: {booking.get('Passenger Name', 'N/A')} ({booking.get('Phone', 'N/A')})\\n"
                summary += f"- Company: {booking.get('Corporate', 'N/A')}\\n"
                summary += f"- Date: {booking.get('Date', 'N/A')}\\n"
                summary += f"- Time: {booking.get('Time', 'N/A')}\\n"
                summary += f"- Vehicle: {booking.get('Vehicle', 'N/A')}\\n"
                summary += f"- From: {booking.get('From', 'N/A')}\\n"
                summary += f"- To: {booking.get('To', 'N/A')}\\n"
                summary += f"- Flight: {booking.get('Flight', 'N/A')}\\n"
                booking_summaries.append(summary)
            
            content = f"TABLE EXTRACTION RESULTS ({len(bookings)} bookings found):\\n\\n" + "\\n".join(booking_summaries)
            content += f"\\n\\nOriginal processing method: Enhanced Multi-Booking Textract"
            
            print(f"✅ App processing created content with {len(bookings)} bookings")
            
        finally:
            # Clean up
            if os.path.exists(temp_path):
                os.unlink(temp_path)
        
    except Exception as e:
        print(f"❌ App processing test failed: {e}")
        return False
    
    # Test 3: Full Orchestrator Pipeline
    print("\n🚀 TEST 3: Full Orchestrator Pipeline")
    print("-" * 50)
    
    try:
        # Process through orchestrator (this should detect preprocessed content)
        result = orchestrator.process_content(
            content=content,
            source_type="file_upload_png"
        )
        
        if result['success']:
            print(f"✅ Orchestrator success: {result['booking_count']} bookings")
            print(f"   Processing time: {result['total_processing_time']:.2f}s")
            print(f"   Cost: ₹{result['total_cost_inr']:.4f}")
            
            if result['final_dataframe'] is not None and not result['final_dataframe'].empty:
                print(f"   DataFrame shape: {result['final_dataframe'].shape}")
                print(f"   DataFrame columns: {list(result['final_dataframe'].columns)}")
            else:
                print("   ⚠️ DataFrame is empty")
        else:
            print(f"❌ Orchestrator failed: {result.get('error_message', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Orchestrator test failed: {e}")
        return False
    
    # Test 4: Extraction Router Direct Test
    print("\n🔄 TEST 4: Extraction Router Direct Test")
    print("-" * 50)
    
    try:
        from extraction_router import ExtractionRouter
        from gemma_classification_agent import BookingType, DutyType
        
        # Create mock classification
        class MockClassification:
            def __init__(self):
                self.booking_type = BookingType.MULTIPLE
                self.booking_count = len(bookings)
                self.confidence_score = 0.95
                self.detected_duty_type = DutyType.POINT_TO_POINT
        
        router = ExtractionRouter(api_key="dummy_key")
        mock_classification = MockClassification()
        
        extraction_result = router.route_and_extract(content, mock_classification)
        
        if extraction_result.success:
            print(f"✅ Router success: {extraction_result.booking_count} bookings")
            print(f"   Method: {extraction_result.extraction_method}")
            if not extraction_result.bookings_dataframe.empty:
                print(f"   DataFrame shape: {extraction_result.bookings_dataframe.shape}")
            else:
                print("   ⚠️ DataFrame is empty")
        else:
            print(f"❌ Router failed: {extraction_result.error_message}")
            return False
        
    except Exception as e:
        print(f"❌ Router test failed: {e}")
        return False
    
    print("\n🎉 ALL TESTS PASSED! Multi-booking pipeline is working correctly.")
    print("=" * 80)
    return True

if __name__ == "__main__":
    success = test_complete_pipeline()
    sys.exit(0 if success else 1)