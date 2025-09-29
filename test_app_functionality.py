#!/usr/bin/env python3
"""
Test App Functionality - Verify all components are working
"""

import os

def test_functionality():
    """Test that all the key functionality is available"""
    
    print("🧪 Testing App Functionality")
    print("=" * 50)
    
    # Set Gemini API key
    gemini_api_key = "AIzaSyAId73p8fsv1U0z2_jQ0yOLdcVJsVsOmeg"
    os.environ['GEMINI_API_KEY'] = gemini_api_key
    
    print(f"✅ Gemini API Key set: {gemini_api_key[:20]}...{gemini_api_key[-4:]}")
    
    # Test 1: Enhanced Multi-Booking Processor
    print("\n📊 Testing Enhanced Multi-Booking Processor...")
    try:
        from enhanced_multi_booking_processor import EnhancedMultiBookingProcessor
        multi_processor = EnhancedMultiBookingProcessor()
        if hasattr(multi_processor, 'textract_available') and multi_processor.textract_available:
            print("✅ Multi-Booking Table Processor: Available with Textract")
        else:
            print("⚠️ Multi-Booking Table Processor: Available but no Textract")
    except ImportError as e:
        print(f"❌ Multi-Booking Table Processor: Not available - {e}")
    
    # Test 2: Enhanced Form Processor  
    print("\n📋 Testing Enhanced Form Processor...")
    try:
        from enhanced_form_processor import EnhancedFormProcessor
        form_processor = EnhancedFormProcessor()
        if hasattr(form_processor, 'textract_available') and form_processor.textract_available:
            print("✅ Enhanced Form Processor: Available with Textract")
        else:
            print("⚠️ Enhanced Form Processor: Available but no Textract")
    except ImportError as e:
        print(f"❌ Enhanced Form Processor: Not available - {e}")
    
    # Test 3: Complete Multi-Agent Orchestrator
    print("\n🤖 Testing Complete Multi-Agent Orchestrator...")
    try:
        from complete_multi_agent_orchestrator import CompleteMultiAgentOrchestrator
        orchestrator = CompleteMultiAgentOrchestrator(api_key=gemini_api_key)
        
        if orchestrator.classification_agent:
            print("✅ Classification Agent: Available")
        else:
            print("❌ Classification Agent: Not available")
            
        if orchestrator.extraction_router:
            print("✅ Extraction Router: Available")
        else:
            print("❌ Extraction Router: Not available")
            
        if orchestrator.validation_agent:
            print("✅ Validation Agent: Available")
        else:
            print("❌ Validation Agent: Not available")
    except Exception as e:
        print(f"❌ Multi-Agent Orchestrator: Failed - {e}")
    
    # Test 4: AWS Textract availability
    print("\n☁️ Testing AWS Textract...")
    try:
        import boto3
        client = boto3.client('textract', region_name='ap-south-1')
        print("✅ AWS Textract: Client available")
    except Exception as e:
        print(f"⚠️ AWS Textract: {e}")
    
    # Test 5: Test a simple processing flow
    print("\n🔄 Testing Simple Processing Flow...")
    try:
        test_content = """
        From: booking@company.com
        
        Need cab for airport pickup.
        Passenger: John Doe
        Phone: 9876543210
        Date: Tomorrow
        Time: 8:00 AM
        From: Home
        To: Airport
        """
        
        result = orchestrator.process_content(test_content, "text_input")
        
        if result['success']:
            print(f"✅ Processing Flow: Success - {result['booking_count']} booking(s) found")
            print(f"   Cost: ₹{result['total_cost_inr']:.4f}")
            print(f"   Time: {result['total_processing_time']:.2f}s")
        else:
            print(f"❌ Processing Flow: Failed - {result.get('error_message', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Processing Flow: Exception - {e}")
    
    print("\n" + "=" * 50)
    print("✨ Functionality Test Complete!")

if __name__ == "__main__":
    test_functionality()