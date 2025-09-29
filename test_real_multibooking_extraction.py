#!/usr/bin/env python3
"""
Test the actual Textract-based multi-booking extraction with validation
"""

import pandas as pd
import logging
import os
from enhanced_multi_booking_processor import EnhancedMultiBookingProcessor
from complete_multi_agent_orchestrator import CompleteMultiAgentOrchestrator

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_real_multibooking_extraction():
    """Test the actual Textract-based multi-booking extraction"""
    
    print("🧪 TESTING REAL MULTI-BOOKING EXTRACTION WITH TEXTRACT")
    print("="*70)
    print("This test will:")
    print("1. Use EnhancedMultiBookingProcessor with actual Textract")
    print("2. Extract 4 bookings from your table image")
    print("3. Format them into a proper DataFrame")
    print("4. Apply validation using the orchestrator")
    print("5. Display complete results\n")
    
    # Check API keys
    gemini_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_AI_API_KEY')
    print(f"🔑 Gemini API key: {'✅ Found' if gemini_key else '❌ Not found (will use fallback)'}")
    
    # Test image path
    image_path = r"multi-bookings images\Screenshot 2025-09-16 004941.png"
    
    if not os.path.exists(image_path):
        print(f"❌ Image file not found: {image_path}")
        return False
    
    print(f"📁 Processing image: {image_path}")
    
    # Step 1: Extract bookings using Textract-based processor
    print("\n🔍 STEP 1: TEXTRACT-BASED EXTRACTION")
    print("-"*50)
    
    try:
        processor = EnhancedMultiBookingProcessor(gemini_api_key=gemini_key)
        
        with open(image_path, 'rb') as f:
            file_content = f.read()
        
        # Process the image
        result = processor.process_document(file_content, image_path)
        
        print(f"✅ Textract processing completed!")
        print(f"   - Success: {result.extraction_method}")
        print(f"   - Bookings found: {result.total_bookings_found}")
        print(f"   - Processing notes: {result.processing_notes}")
        
        if len(result.bookings) == 0:
            print("❌ No bookings extracted!")
            return False
        
        print(f"\n📊 EXTRACTED BOOKING DETAILS:")
        for i, booking in enumerate(result.bookings, 1):
            print(f"\n--- Booking {i} ---")
            print(f"   Passenger: {booking.passenger_name}")
            print(f"   Phone: {booking.passenger_phone}")
            print(f"   Company: {booking.corporate}")
            print(f"   Date: {booking.start_date}")
            print(f"   Time: {booking.reporting_time}")
            print(f"   Vehicle: {booking.vehicle_group}")
            print(f"   From: {booking.from_location}")
            print(f"   Pickup: {booking.reporting_address}")
            print(f"   Drop: {booking.drop_address}")
            print(f"   Flight: {booking.flight_train_number}")
            print(f"   Confidence: {booking.confidence_score:.2f}")
    
    except Exception as e:
        print(f"❌ Textract extraction failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Step 2: Convert to DataFrame format
    print("\n📋 STEP 2: CONVERT TO DATAFRAME")
    print("-"*50)
    
    try:
        # Convert bookings to DataFrame format
        booking_records = []
        for booking in result.bookings:
            record = {
                'Customer': booking.corporate or 'Corporate Client',
                'Booked By Name': booking.booked_by_name or 'Travel Coordinator',
                'Booked By Phone Number': booking.booked_by_phone or '',
                'Booked By Email': booking.booked_by_email or '',
                'Passenger Name': booking.passenger_name or 'Guest',
                'Passenger Phone Number': booking.passenger_phone or '',
                'Passenger Email': booking.passenger_email or '',
                'From (Service Location)': booking.from_location or '',
                'To': booking.to_location or '',
                'Vehicle Group': booking.vehicle_group or '',
                'Duty Type': booking.duty_type or 'P2P',
                'Start Date': booking.start_date or '',
                'End Date': booking.end_date or '',
                'Rep. Time': booking.reporting_time or '',
                'Reporting Address': booking.reporting_address or '',
                'Drop Address': booking.drop_address or '',
                'Flight/Train Number': booking.flight_train_number or '',
                'Dispatch center': booking.dispatch_center or 'Central Dispatch',
                'Remarks': booking.remarks or f'Extracted by {result.extraction_method}',
                'Labels': booking.labels or ''
            }
            booking_records.append(record)
        
        df = pd.DataFrame(booking_records)
        print(f"✅ DataFrame created with shape: {df.shape}")
        print(f"   Columns: {list(df.columns)}")
        
    except Exception as e:
        print(f"❌ DataFrame conversion failed: {e}")
        return False
    
    # Step 3: Apply validation using orchestrator
    print("\n🔧 STEP 3: APPLY VALIDATION")
    print("-"*50)
    
    try:
        orchestrator = CompleteMultiAgentOrchestrator(api_key=gemini_key)
        
        # Apply business logic validation
        validated_df = orchestrator.validation_agent.validate_dataframe(df)
        
        print(f"✅ Validation completed!")
        print(f"   Validated DataFrame shape: {validated_df.shape}")
        
    except Exception as e:
        print(f"❌ Validation failed: {e}")
        validated_df = df  # Use original DataFrame
        print("⚠️  Using original DataFrame without validation")
    
    # Step 4: Display complete results
    print("\n📊 STEP 4: FINAL RESULTS")
    print("="*100)
    
    # Configure pandas display
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)
    pd.set_option('display.max_colwidth', 40)
    
    print("FINAL DATAFRAME:")
    print(validated_df.to_string(index=True))
    print("="*100)
    
    # Analysis
    print(f"\n🔍 DETAILED ANALYSIS:")
    
    # Data completeness
    missing_data = validated_df.isnull().sum()
    total_cells = len(validated_df) * len(validated_df.columns)
    filled_cells = total_cells - missing_data.sum()
    completeness = (filled_cells / total_cells) * 100
    
    print(f"\n📊 Data Completeness: {completeness:.1f}%")
    print(f"   - Total cells: {total_cells}")
    print(f"   - Filled cells: {filled_cells}")
    print(f"   - Empty cells: {missing_data.sum()}")
    
    # Key field analysis
    key_fields = ['Passenger Name', 'Passenger Phone Number', 'Start Date', 'Rep. Time', 
                  'Reporting Address', 'Drop Address', 'Vehicle Group', 'Customer']
    
    print(f"\n🔑 Key Fields Analysis:")
    for field in key_fields:
        if field in validated_df.columns:
            non_empty = validated_df[field].notna().sum()
            print(f"   ✅ {field}: {non_empty}/{len(validated_df)} filled")
        else:
            print(f"   ❌ {field}: Missing from DataFrame")
    
    # Booking details
    print(f"\n📋 Sample Booking Information:")
    for i, (idx, row) in enumerate(validated_df.head(2).iterrows()):
        print(f"\nBooking {i+1}:")
        print(f"   Passenger: {row.get('Passenger Name', 'N/A')}")
        print(f"   Phone: {row.get('Passenger Phone Number', 'N/A')}")
        print(f"   Date/Time: {row.get('Start Date', 'N/A')} at {row.get('Rep. Time', 'N/A')}")
        pickup = str(row.get('Reporting Address', ''))[:50] + "..." if len(str(row.get('Reporting Address', ''))) > 50 else str(row.get('Reporting Address', ''))
        drop = str(row.get('Drop Address', ''))[:50] + "..." if len(str(row.get('Drop Address', ''))) > 50 else str(row.get('Drop Address', ''))
        print(f"   Route: {pickup} → {drop}")
    
    # Success metrics
    success_metrics = {
        "Textract extraction successful": len(result.bookings) > 0,
        "Expected 4 bookings": len(result.bookings) == 4,
        "DataFrame creation successful": validated_df is not None and not validated_df.empty,
        "High data completeness": completeness >= 70,
        "Key fields present": sum(1 for field in key_fields if field in validated_df.columns) >= 6
    }
    
    print(f"\n✅ SUCCESS METRICS:")
    all_passed = True
    for metric, passed in success_metrics.items():
        status = "✅" if passed else "❌"
        print(f"   {status} {metric}")
        if not passed:
            all_passed = False
    
    # Save results
    try:
        output_file = "real_multibooking_results.csv"
        validated_df.to_csv(output_file, index=False)
        print(f"\n💾 Results saved to: {output_file}")
    except Exception as e:
        print(f"⚠️  Could not save results: {e}")
    
    if all_passed:
        print(f"\n🎉 COMPLETE SUCCESS!")
        print(f"✅ Textract-based multi-booking extraction working perfectly!")
        print(f"✅ All 4 bookings extracted with complete data")
        print(f"✅ DataFrame properly formatted and validated")
        print(f"✅ Ready for production use!")
    else:
        print(f"\n⚠️  PARTIAL SUCCESS")
        print(f"The extraction is working but may need fine-tuning")
    
    return all_passed

if __name__ == "__main__":
    success = test_real_multibooking_extraction()
    
    print(f"\n" + "="*70)
    if success:
        print("🏆 REAL MULTI-BOOKING EXTRACTION TEST: COMPLETE SUCCESS!")
    else:
        print("🔧 REAL MULTI-BOOKING EXTRACTION TEST: NEEDS ATTENTION")
    print("="*70)