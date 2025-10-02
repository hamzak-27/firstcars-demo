"""
End-to-End Test for Enhanced Booking Form Processing System
Tests the complete pipeline with realistic form data
"""

import os
import pandas as pd
from core.multi_agent_orchestrator import MultiAgentOrchestrator

def test_form_processing_pipeline():
    """Test the complete form processing pipeline"""
    
    print("🧪 END-TO-END BOOKING FORM PROCESSING TEST")
    print("=" * 60)
    
    # Check if OpenAI API key is available
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("⚠️  No OPENAI_API_KEY found - using mock orchestrator")
        test_data_flow_only()
        return
    
    try:
        # Initialize the orchestrator with real API key
        orchestrator = MultiAgentOrchestrator(api_key, model="gpt-4o-mini")
        print("✅ Orchestrator initialized with 6 agents")
        
        # Test with actual image processing (will use mock data from Textract processor)
        print("\n📁 Testing Table Image Processing:")
        result_df = orchestrator.process_table_data("mock_booking_form.png")
        
        if not result_df.empty:
            print(f"✅ Processing successful! Extracted {len(result_df)} booking(s)")
            print("\n📊 RESULTS:")
            print(result_df.to_string(index=False))
            
            # Save results
            output_file = "test_e2e_results.csv"
            result_df.to_csv(output_file, index=False)
            print(f"\n💾 Results saved to: {output_file}")
            
            # Analyze results
            analyze_extraction_results(result_df)
            
        else:
            print("❌ No data extracted - check logs for errors")
    
    except Exception as e:
        print(f"❌ Error in E2E test: {e}")
        test_data_flow_only()

def test_data_flow_only():
    """Test just the data flow without actual API calls"""
    
    print("\n🔧 TESTING DATA FLOW (Mock Mode):")
    print("-" * 50)
    
    # Create mock form data
    form_df = pd.DataFrame({
        'Field': [
            'Company Name',
            'Name & Contact Number of booker', 
            'Email ID of booker',
            'City in which car is required',
            'Name of the User',
            'Mobile No. of the User',
            'Email ID of user',
            'Date of Requirement',
            'Car Type (Indigo/Dzire/Fiesta)',
            'Reporting Address',
            'Reporting Time',
            'Type of duty'
        ],
        'Value': [
            'India Medtronic Pvt. Ltd.',
            'Hiba Mohammed',
            'hiba.mohammed@medtronic.com',
            'Chennai',
            'Hiba Mohammed', 
            '8281011554, 9319154943',
            'hiba.mohammed@medtronic.com',
            '01-10-25, 11:00 AM',
            'Dzire',
            'H.No 33/432B Thattekadu Rd Near Villa Exotica Bavasons Homes, Maradu Nettoor, kochi 682040',
            '01-10-25, 11:00 AM',
            'Local full day'
        ]
    })
    
    print("✅ Mock form DataFrame created")
    print(f"Form shape: {form_df.shape}")
    
    # Test orchestrator initialization
    try:
        orchestrator = MultiAgentOrchestrator('fake-key')
        print("✅ Orchestrator initialized")
        
        # Test DataFrame structure analysis
        analysis = orchestrator._analyze_dataframe_structure(form_df)
        print("✅ DataFrame structure analysis:")
        for key, value in analysis.items():
            print(f"   {key}: {value}")
        
        # Test DataFrame slicing
        slice_df = orchestrator._extract_booking_table_slice(form_df, 0)
        print("✅ DataFrame slicing works:")
        print(f"   Original: {form_df.shape}")
        print(f"   Slice: {slice_df.shape}")
        
        # Test booking data preparation
        booking_data = orchestrator._prepare_booking_data(
            df=form_df,
            booking_idx=0,
            source_data={'raw_df': form_df, 'image_path': 'mock.png'},
            data_type='table'
        )
        print("✅ Booking data preparation:")
        print(f"   Source type: {booking_data['source_type']}")
        print(f"   Table data type: {type(booking_data['table_data'])}")
        print(f"   Table shape: {booking_data['table_data'].shape if hasattr(booking_data['table_data'], 'shape') else 'N/A'}")
        
        print("\n✅ All data flow tests passed!")
        
    except Exception as e:
        print(f"❌ Data flow test error: {e}")

def analyze_extraction_results(df: pd.DataFrame):
    """Analyze the quality of extraction results"""
    
    print("\n📈 EXTRACTION ANALYSIS:")
    print("-" * 50)
    
    # Check key fields
    key_fields = [
        'Customer', 
        'Passenger Name',
        'From (Service Location)',
        'Vehicle Group',
        'Duty Type',
        'Rep. Time'
    ]
    
    filled_count = 0
    for field in key_fields:
        if field in df.columns:
            value = df[field].iloc[0] if len(df) > 0 else 'N/A'
            status = "✅" if value and value != 'NA' else "❌"
            print(f"{status} {field}: {value}")
            if value and value != 'NA':
                filled_count += 1
        else:
            print(f"❌ {field}: Column not found")
    
    completion_rate = (filled_count / len(key_fields)) * 100
    print(f"\n📊 Extraction Completion Rate: {completion_rate:.1f}%")
    
    # Expected vs Actual comparison
    expected_values = {
        'Customer': 'Medtronic',
        'Passenger Name': 'Hiba Mohammed',
        'From (Service Location)': 'Chennai',
        'Vehicle Group': 'Maruti Dzire',
        'Duty Type': '08HR 80KMS',
        'Rep. Time': '11:00'
    }
    
    print("\n🎯 EXPECTED vs ACTUAL:")
    for field, expected in expected_values.items():
        if field in df.columns and len(df) > 0:
            actual = df[field].iloc[0]
            match = "✅" if expected.lower() in str(actual).lower() else "⚠️"
            print(f"{match} {field}:")
            print(f"   Expected: {expected}")
            print(f"   Actual: {actual}")
        else:
            print(f"❌ {field}: Not extracted")

def main():
    """Run all tests"""
    
    print("🚀 Enhanced Booking Form Processing System")
    print("Multi-Agent Pipeline Test")
    print("=" * 60)
    
    # Run the comprehensive test
    test_form_processing_pipeline()
    
    print("\n" + "=" * 60)
    print("TEST COMPLETED")
    print("=" * 60)
    
    print("\n📋 NEXT STEPS:")
    print("1. Check test_e2e_results.csv for detailed output")
    print("2. Run 'python run_streamlit.py' to test with UI")
    print("3. Upload your booking form image to verify results")
    print("\n💡 If extraction rate is low, agents may need prompt tuning")

if __name__ == "__main__":
    main()