#!/usr/bin/env python3
"""
Debug why multiple booking classification doesn't result in multiple extracted bookings
"""

import os
import sys
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s - %(name)s - %(message)s')
logger = logging.getLogger(__name__)

def test_full_pipeline_with_multiple_bookings():
    """Test the full pipeline with a multiple booking example"""
    
    # Sample content that should definitely be classified as multiple bookings
    test_content = """
    Dear Team,
    
    Please arrange two separate car bookings:
    
    First car:
    - Passenger: John Smith (9876543210)
    - Date: 25th December 2024
    - Time: 9:00 AM
    - From: Delhi Office, Connaught Place
    - To: Delhi Airport Terminal 3
    - Vehicle: Dzire
    - This is for airport drop service
    
    Second car:
    - Passenger: Mary Wilson (9876543211)
    - Date: 26th December 2024
    - Time: 10:00 AM
    - From: Mumbai Office, BKC
    - To: Mumbai Airport Terminal 2
    - Vehicle: Innova Crysta
    - This is also for airport drop service
    
    Both are separate bookings for different passengers on different days.
    
    Corporate: TechCorp India
    
    Thanks,
    Travel Coordinator
    """
    
    print("🧪 DEBUGGING MULTIPLE BOOKING PIPELINE")
    print("=" * 70)
    print("Test Content:")
    print(test_content.strip())
    print("=" * 70)
    
    try:
        # Step 1: Test Classification Agent
        print("\n📊 STEP 1: CLASSIFICATION")
        print("-" * 40)
        
        from gemma_classification_agent import GemmaClassificationAgent
        
        # Use environment variable for API key
        api_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_AI_API_KEY')
        if not api_key:
            print("⚠️  No API key found - will test rule-based fallback")
            api_key = "test-key"  # This will trigger fallback mode
        
        classifier = GemmaClassificationAgent(api_key=api_key)
        classification_result = classifier.classify_content(test_content, "email")
        
        print(f"Classification Result:")
        print(f"  - Booking Type: {classification_result.booking_type.value}")
        print(f"  - Booking Count: {classification_result.booking_count}")
        print(f"  - Confidence: {classification_result.confidence_score:.1%}")
        print(f"  - Reasoning: {classification_result.reasoning}")
        
        if classification_result.booking_type.value != "multiple":
            print("❌ PROBLEM: Classification should be MULTIPLE but got SINGLE!")
            print("This explains why only 1 booking is found.")
            
            # Check if using AI or fallback
            if "Rule-based" in classification_result.reasoning:
                print("💡 SOLUTION: The rule-based fallback doesn't detect multiple bookings properly.")
                print("   You need to configure a valid Gemini API key for AI-powered classification.")
                
                # Let's enhance the rule-based detection for this specific case
                print("\n🔧 Testing enhanced rule-based detection...")
                
                content_lower = test_content.lower()
                enhanced_indicators = [
                    'first car', 'second car', 'third car', 'fourth car',
                    'car 1', 'car 2', 'car 3', 'car 4',
                    'booking 1', 'booking 2', 'booking 3', 'booking 4',
                    'separate bookings', 'both are separate', 'different passengers',
                    'arrange two', 'arrange 2', 'two separate', '2 separate'
                ]
                
                detected = [indicator for indicator in enhanced_indicators if indicator in content_lower]
                print(f"Enhanced indicators found: {detected}")
                
                if detected:
                    print("✅ Enhanced rule-based detection would work!")
                    print("   The current rule-based logic needs to be updated with these patterns.")
                
            else:
                print("💡 The AI classification might need prompt refinement.")
                
            return
        
        print("✅ Classification correctly identified MULTIPLE bookings")
        
        # Step 2: Test Extraction Router
        print(f"\n📋 STEP 2: EXTRACTION ROUTING")
        print("-" * 40)
        
        from extraction_router import ExtractionRouter
        router = ExtractionRouter(api_key=api_key)
        
        extraction_result = router.route_and_extract(test_content, classification_result)
        
        print(f"Extraction Result:")
        print(f"  - Success: {extraction_result.success}")
        print(f"  - Booking Count: {extraction_result.booking_count}")
        print(f"  - DataFrame Shape: {extraction_result.bookings_dataframe.shape}")
        print(f"  - Extraction Method: {extraction_result.extraction_method}")
        print(f"  - Confidence: {extraction_result.confidence_score:.1%}")
        
        if extraction_result.booking_count < 2:
            print("❌ PROBLEM: Extraction should find 2+ bookings but found fewer!")
            print("This is where the pipeline is losing the multiple bookings.")
            
            if extraction_result.metadata:
                agent_used = extraction_result.metadata.get('agent_selected', 'Unknown')
                print(f"   Agent used: {agent_used}")
                
                if agent_used == "MultipleBookingExtractionAgent":
                    print("💡 The MultipleBookingExtractionAgent isn't extracting multiple bookings from text.")
                    print("   It might be designed for table data, not structured text.")
                elif agent_used == "SingleBookingExtractionAgent":
                    print("💡 The router incorrectly sent it to SingleBookingExtractionAgent!")
                    print("   This is a routing logic problem.")
            
            # Show the DataFrame content
            if not extraction_result.bookings_dataframe.empty:
                print("\nExtracted DataFrame:")
                print(extraction_result.bookings_dataframe[['Passenger Name', 'Start Date', 'Vehicle Group']].to_string())
            
            return
        
        print("✅ Extraction correctly found multiple bookings")
        
        # Step 3: Test Full Orchestrator
        print(f"\n🤖 STEP 3: FULL ORCHESTRATOR")
        print("-" * 40)
        
        from complete_multi_agent_orchestrator import CompleteMultiAgentOrchestrator
        orchestrator = CompleteMultiAgentOrchestrator(api_key=api_key)
        
        final_result = orchestrator.process_content(test_content, "email")
        
        print(f"Final Result:")
        print(f"  - Success: {final_result['success']}")
        print(f"  - Final Booking Count: {final_result['booking_count']}")
        print(f"  - Confidence: {final_result['confidence_score']:.1%}")
        print(f"  - Total Cost: ₹{final_result['total_cost_inr']:.4f}")
        
        if final_result['booking_count'] < 2:
            print("❌ PROBLEM: Final result should have 2+ bookings!")
            
            # Check each pipeline stage
            for stage, info in final_result['pipeline_stages'].items():
                print(f"\n{stage.upper()} Stage:")
                if 'booking_count' in info:
                    print(f"  - Booking Count: {info['booking_count']}")
                if 'agent' in info:
                    print(f"  - Agent: {info['agent']}")
        else:
            print("✅ Full pipeline correctly processed multiple bookings!")
            
            # Show final DataFrame
            if final_result['final_dataframe'] is not None and not final_result['final_dataframe'].empty:
                print(f"\nFinal DataFrame ({final_result['final_dataframe'].shape}):")
                display_cols = ['Passenger Name', 'Start Date', 'Vehicle Group', 'Reporting Address', 'Drop Address']
                available_cols = [col for col in display_cols if col in final_result['final_dataframe'].columns]
                if available_cols:
                    print(final_result['final_dataframe'][available_cols].to_string())
        
    except Exception as e:
        print(f"❌ Pipeline test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Set API key if provided as command line argument
    if len(sys.argv) > 1:
        os.environ['GEMINI_API_KEY'] = sys.argv[1]
        print(f"Using provided API key: {sys.argv[1][:20]}...")
    
    test_full_pipeline_with_multiple_bookings()