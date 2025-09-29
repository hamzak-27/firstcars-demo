#!/usr/bin/env python3
"""
Diagnostic script to test the complete multi-booking flow and identify remaining issues
"""

import logging
import traceback
import os
from pathlib import Path

# Set up logging to capture all details
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_extraction_router_integration():
    """Test the extraction router with multi-booking content"""
    
    print("🧪 TESTING EXTRACTION ROUTER INTEGRATION")
    print("="*70)
    
    try:
        # Import the extraction router
        from extraction_router import ExtractionRouter
        from gemma_classification_agent import ClassificationResult, BookingType, DutyType
        
        print("✅ Successfully imported ExtractionRouter")
        
        # Initialize router
        router = ExtractionRouter(api_key="test-key")
        print("✅ ExtractionRouter initialized")
        
        # Test with pre-processed Textract content (simulates file upload flow)
        test_content = """
        TABLE EXTRACTION RESULTS (4 bookings found):

        Booking 1:
        - Passenger: Jayasheel Bhansali (7001682596)
        - Company: LTPL (Lendingkart Technologies Private Limited)
        - Date: 19-Sep-25
        - Time: 8:30 PM
        - Vehicle: CRYSTA
        - From: Bangalore Airport T-2
        - To: ITC Windsor Bangalore
        - Flight: AI-2641

        Booking 2:
        - Passenger: Jayasheel Bhansali (7001682596)
        - Company: LTPL (Lendingkart Technologies Private Limited)
        - Date: 20 Sep 2025 & 21 Sep 2025
        - Time: 10:00 AM
        - Vehicle: CRYSTA
        - From: ITC Windsor Bangalore
        - To: Full Day

        Original processing method: enhanced_multi_booking_extraction
        """
        
        # Create classification result
        classification = ClassificationResult(
            booking_type=BookingType.MULTIPLE,
            booking_count=4,
            confidence_score=0.9,
            reasoning="Multiple bookings detected in table format",
            detected_duty_type=DutyType.P2P,
            cost_inr=0.0,
            processing_time=0.1
        )
        
        print("🔄 Testing extraction routing with pre-processed content...")
        
        # Test the routing
        result = router.route_and_extract(test_content, classification)
        
        print(f"✅ Routing completed!")
        print(f"   - Success: {result.success}")
        print(f"   - Method: {result.extraction_method}")
        print(f"   - Booking count: {result.booking_count}")
        print(f"   - DataFrame shape: {result.bookings_dataframe.shape if result.bookings_dataframe is not None else 'None'}")
        
        if result.success and result.bookings_dataframe is not None and not result.bookings_dataframe.empty:
            print(f"   - Sample data: {result.bookings_dataframe.iloc[0]['Passenger Name'] if 'Passenger Name' in result.bookings_dataframe.columns else 'N/A'}")
            return True
        else:
            print(f"   - Error: {result.error_message}")
            return False
            
    except Exception as e:
        print(f"❌ ExtractionRouter test failed: {e}")
        traceback.print_exc()
        return False

def test_enhanced_multi_booking_processor():
    """Test the EnhancedMultiBookingProcessor directly"""
    
    print("\n🔬 TESTING ENHANCED MULTI-BOOKING PROCESSOR")
    print("="*70)
    
    try:
        from enhanced_multi_booking_processor import EnhancedMultiBookingProcessor
        
        print("✅ Successfully imported EnhancedMultiBookingProcessor")
        
        # Initialize processor
        processor = EnhancedMultiBookingProcessor(gemini_api_key="test-key")
        print("✅ EnhancedMultiBookingProcessor initialized")
        
        # Check if image file exists
        image_path = "multi-bookings images\\Screenshot 2025-09-16 004941.png"
        if os.path.exists(image_path):
            print(f"✅ Found test image: {image_path}")
            
            with open(image_path, 'rb') as f:
                file_content = f.read()
            
            print(f"🔄 Processing image ({len(file_content)} bytes)...")
            
            # Process the image
            result = processor.process_document(file_content, image_path)
            
            print(f"✅ Processing completed!")
            print(f"   - Method: {result.extraction_method}")
            print(f"   - Booking count: {result.total_bookings_found}")
            print(f"   - Processing notes: {result.processing_notes}")
            
            if result.bookings:
                print(f"   - Sample booking: {result.bookings[0].passenger_name} - {result.bookings[0].start_date}")
                return True
            else:
                print(f"   - No bookings found")
                return False
                
        else:
            print(f"❌ Test image not found: {image_path}")
            return False
            
    except Exception as e:
        print(f"❌ EnhancedMultiBookingProcessor test failed: {e}")
        traceback.print_exc()
        return False

def test_complete_orchestrator():
    """Test the complete orchestrator"""
    
    print("\n🎼 TESTING COMPLETE ORCHESTRATOR")
    print("="*70)
    
    try:
        from complete_multi_agent_orchestrator import CompleteMultiAgentOrchestrator
        
        print("✅ Successfully imported CompleteMultiAgentOrchestrator")
        
        # Initialize orchestrator
        orchestrator = CompleteMultiAgentOrchestrator(api_key="test-key")
        print("✅ CompleteMultiAgentOrchestrator initialized")
        
        # Test with simulated file upload content (what the app would send)
        test_content = """[File: Screenshot 2025-09-16 004941.png, Method: enhanced_multi_booking_textract]

TABLE EXTRACTION RESULTS (4 bookings found):

Booking 1:
- Passenger: Jayasheel Bhansali (7001682596)
- Company: LTPL (Lendingkart Technologies Private Limited)
- Date: 19-Sep-25
- Time: 8:30 PM
- Vehicle: CRYSTA
- From: Bangalore Airport T-2
- To: ITC Windsor Bangalore
- Flight: AI-2641

Booking 2:
- Passenger: Jayasheel Bhansali (7001682596)
- Company: LTPL (Lendingkart Technologies Private Limited)
- Date: 20 Sep 2025 & 21 Sep 2025
- Time: 10:00 AM
- Vehicle: CRYSTA
- From: ITC Windsor Bangalore
- To: Full Day

Original processing method: enhanced_multi_booking_extraction (unknown)"""
        
        print(f"🔄 Processing content through complete pipeline...")
        
        # Process through orchestrator
        result = orchestrator.process_content(test_content, source_type="file_upload_png")
        
        print(f"✅ Orchestrator processing completed!")
        print(f"   - Success: {result['success']}")
        print(f"   - Booking count: {result['booking_count']}")
        print(f"   - Total cost: ₹{result['total_cost_inr']:.4f}")
        print(f"   - Processing time: {result['total_processing_time']:.2f}s")
        print(f"   - Agents used: {', '.join(result['metadata']['agents_used'])}")
        
        if result['final_dataframe'] is not None and not result['final_dataframe'].empty:
            print(f"   - DataFrame shape: {result['final_dataframe'].shape}")
            print(f"   - Sample passenger: {result['final_dataframe'].iloc[0]['Passenger Name'] if 'Passenger Name' in result['final_dataframe'].columns else 'N/A'}")
            return True
        else:
            print(f"   - No final DataFrame produced")
            return False
            
    except Exception as e:
        print(f"❌ CompleteMultiAgentOrchestrator test failed: {e}")
        traceback.print_exc()
        return False

def test_app_file_processing():
    """Test the app's file processing function"""
    
    print("\n📱 TESTING APP FILE PROCESSING FUNCTION")
    print("="*70)
    
    try:
        # Import what the app uses
        from enhanced_multi_booking_processor import EnhancedMultiBookingProcessor
        
        # Simulate file upload processing (what the app does)
        image_path = "multi-bookings images\\Screenshot 2025-09-16 004941.png"
        
        if not os.path.exists(image_path):
            print(f"❌ Test image not found: {image_path}")
            return False
        
        print(f"✅ Found test image: {image_path}")
        
        # Read file like the app does
        with open(image_path, 'rb') as f:
            file_content = f.read()
        
        print(f"🔄 Processing with EnhancedMultiBookingProcessor (as app does)...")
        
        # Process like the app does (line 286-289 in car_rental_app.py)
        multi_processor = EnhancedMultiBookingProcessor()
        table_result = multi_processor.process_multi_booking_document(file_content, "Screenshot 2025-09-16 004941.png", "png")
        
        print(f"✅ Table processing completed: {table_result.extraction_method}")
        
        if table_result.bookings:
            print(f"📊 Found {len(table_result.bookings)} booking(s) in table")
            
            # Convert to text format like the app does (lines 296-312)
            booking_summaries = []
            for i, booking in enumerate(table_result.bookings, 1):
                summary = f"Booking {i}:\n"
                summary += f"- Passenger: {booking.passenger_name or 'N/A'} ({booking.passenger_phone or 'N/A'})\n"
                summary += f"- Company: {booking.corporate or 'N/A'}\n"
                summary += f"- Date: {booking.start_date or 'N/A'}\n"
                summary += f"- Time: {booking.reporting_time or 'N/A'}\n"
                summary += f"- Vehicle: {booking.vehicle_group or 'N/A'}\n"
                summary += f"- From: {booking.from_location or booking.reporting_address or 'N/A'}\n"
                summary += f"- To: {booking.to_location or booking.drop_address or 'N/A'}\n"
                summary += f"- Flight: {booking.flight_train_number or 'N/A'}\n"
                booking_summaries.append(summary)
            
            content = f"TABLE EXTRACTION RESULTS ({len(table_result.bookings)} bookings found):\n\n" + "\n".join(booking_summaries)
            content += f"\n\nOriginal processing method: {table_result.extraction_method}"
            
            print(f"✅ Converted to text format ({len(content)} chars)")
            print(f"📝 Content preview: {content[:200]}...")
            
            return True
        else:
            print(f"❌ No bookings found in table")
            return False
            
    except Exception as e:
        print(f"❌ App file processing test failed: {e}")
        traceback.print_exc()
        return False

def main():
    """Run all diagnostic tests"""
    
    print("🚀 MULTI-BOOKING FLOW DIAGNOSTIC")
    print("="*80)
    print("This will test the complete multi-booking flow and identify any remaining issues\n")
    
    # Test results
    results = []
    
    # Test 1: Enhanced Multi-Booking Processor
    results.append(("Enhanced Multi-Booking Processor", test_enhanced_multi_booking_processor()))
    
    # Test 2: App File Processing Function  
    results.append(("App File Processing", test_app_file_processing()))
    
    # Test 3: Extraction Router Integration
    results.append(("Extraction Router Integration", test_extraction_router_integration()))
    
    # Test 4: Complete Orchestrator
    results.append(("Complete Orchestrator", test_complete_orchestrator()))
    
    # Summary
    print("\n" + "="*80)
    print("📊 DIAGNOSTIC SUMMARY")
    print("="*80)
    
    passed = 0
    failed = 0
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print(f"\nResults: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! Multi-booking flow should work correctly.")
    else:
        print("⚠️  Some tests failed. Check the error details above.")
        
        # Recommendations
        print("\n🔧 RECOMMENDED FIXES:")
        
        for test_name, result in results:
            if not result:
                if "Enhanced Multi-Booking Processor" in test_name:
                    print("   - Check Textract configuration and image file path")
                elif "Extraction Router" in test_name:
                    print("   - Fix extraction router integration and content parsing")
                elif "Complete Orchestrator" in test_name:
                    print("   - Debug orchestrator agent initialization")
                elif "App File Processing" in test_name:
                    print("   - Check file processing logic in car_rental_app.py")

if __name__ == "__main__":
    main()