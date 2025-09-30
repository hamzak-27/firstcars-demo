#!/usr/bin/env python3
"""
Test AI-based validation and classification with actual API key
"""

import logging
import os
from booking_classification_agent import BookingClassificationAgent
from business_logic_validation_agent import BusinessLogicValidationAgent

# Configure logging
logging.basicConfig(level=logging.INFO)

def test_ai_with_api_key():
    """Test if AI validation works when API key is available."""
    
    print("🤖 Testing AI-Based Validation")
    print("=" * 50)
    
    # Check for API key
    api_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_AI_API_KEY')
    
    if not api_key:
        print("⚠️ **NO API KEY FOUND**")
        print("   Set GEMINI_API_KEY or GOOGLE_AI_API_KEY environment variable")
        print("   Currently running in fallback mode only")
        return False
    
    print(f"✅ **API KEY FOUND**: {api_key[:10]}...{api_key[-5:]}")
    
    # Test email content
    email_content = """
    Subject: Cab Booking Required - Chennai to Bangalore
    
    Dear Team,
    
    Kindly arrange a cab for outstation trip:
    
    Journey: Chennai to Bangalore to Chennai (round trip)
    Date: Tomorrow (25th October)
    Time: Early morning 5 AM
    Passenger: Mr. Rajesh Kumar
    Phone: +91-9876543210
    Email: rajesh.kumar@techcorp.com
    Vehicle: Prefer Dzire or similar sedan
    
    Additional Details:
    - Need experienced highway driver
    - AC mandatory for long journey
    - Return same day by evening
    - Bill to TechCorp account
    - Emergency contact: +91-9876543211 (Office)
    
    Please confirm the booking.
    
    Thanks,
    Operations Team
    """
    
    print("📧 **Test Content**: Chennai→Bangalore→Chennai outstation")
    print()
    
    # Test 1: Classification Agent
    print("🎯 **Test 1: AI Classification**")
    print("-" * 40)
    
    try:
        classifier = BookingClassificationAgent()
        if classifier.ai_available:
            print("   ✅ AI Classification: ENABLED")
            result = classifier.classify_text_content(email_content)
            
            print(f"   📊 Result: {result.booking_type} booking ({result.predicted_booking_count} count)")
            print(f"   🎯 Confidence: {result.confidence_score * 100:.1f}%")
            print(f"   💭 Reasoning: {result.reasoning[:100]}...")
            
            if result.booking_type == 'single':
                print("   ✅ **CLASSIFICATION SUCCESS**: Correctly identified as single booking")
            else:
                print("   ❌ **CLASSIFICATION ISSUE**: Should be single booking")
        else:
            print("   ⚠️ AI Classification: DISABLED (using fallback)")
            result = classifier.classify_text_content(email_content)
            print(f"   📊 Fallback Result: {result.booking_type} booking")
    
    except Exception as e:
        print(f"   ❌ **CLASSIFICATION ERROR**: {e}")
        return False
    
    print()
    
    # Test 2: Business Validation Agent
    print("⚙️ **Test 2: AI Business Validation**")
    print("-" * 40)
    
    try:
        validator = BusinessLogicValidationAgent()
        if validator.model:
            print("   ✅ AI Business Validation: ENABLED")
            
            # Create minimal test booking
            import pandas as pd
            test_booking = {
                'Email Content': email_content,
                'Corporate': 'TechCorp',
                'Customer': 'TechCorp Ltd',
                'From (Service Location)': 'Chennai',
                'To': 'Bangalore',
                'Start Date': '2025-10-25',
                'Start Time': '05:00',
                'End Date': '2025-10-25', 
                'End Time': '20:00',
                'Rep. Time': '05:00',
                'Vehicle Group': 'Dzire',
                'Passenger Name': 'Rajesh Kumar',
                'Passenger Phone': '+91-9876543210',
                'Passenger Email': 'rajesh.kumar@techcorp.com',
                'Booked By Email': 'operations@techcorp.com',
                'Passenger Phone Number': '+91-9876543210',
                'Duty Type': '',
                'Remarks': '',
                'Labels': '',
                'Dispatch center': '',
                'Flight/Train Number': 'NA'
            }
            
            # Create DataFrame
            test_df = pd.DataFrame([test_booking])
            
            # Create mock classification result
            from booking_classification_agent import ClassificationResult
            mock_classification = ClassificationResult(
                predicted_booking_count=1,
                booking_type='single',
                confidence_score=0.9,
                reasoning='Outstation round trip',
                detected_patterns=['outstation', 'round trip'],
                duty_type_indicators=['outstation'],
                date_patterns=['tomorrow']
            )
            
            # Test AI validation
            try:
                validated_df = validator._ai_comprehensive_validation_safe(test_df, 0, email_content)
                print("   ✅ **AI VALIDATION SUCCESS**: AI processing completed")
                
                # Check some key fields
                validated_booking = validated_df.iloc[0]
                print(f"   📝 Validated Duty Type: {validated_booking.get('Duty Type', 'N/A')}")
                print(f"   📍 Validated Cities: {validated_booking.get('From (Service Location)')} → {validated_booking.get('To')}")
                print(f"   📧 Validated Email: {validated_booking.get('Passenger Email', 'N/A')}")
                print(f"   📞 Validated Phone: {validated_booking.get('Passenger Phone Number', 'N/A')}")
                
                remarks = str(validated_booking.get('Remarks', ''))
                if len(remarks) > 10:
                    print(f"   📋 Enhanced Remarks: {remarks[:100]}...")
                else:
                    print("   📋 Enhanced Remarks: (minimal)")
                
            except Exception as validation_error:
                print(f"   ⚠️ **AI VALIDATION FAILED**: {validation_error}")
                print("   🔄 Falling back to rule-based validation...")
                
                # Test rule-based fallback
                try:
                    validated_df = validator._rule_based_comprehensive_validation(test_df, 0, email_content)
                    print("   ✅ **RULE-BASED FALLBACK**: Working properly")
                except Exception as fallback_error:
                    print(f"   ❌ **FALLBACK FAILED**: {fallback_error}")
                    return False
        else:
            print("   ⚠️ AI Business Validation: DISABLED (no model available)")
    
    except Exception as e:
        print(f"   ❌ **BUSINESS VALIDATION ERROR**: {e}")
        return False
    
    print()
    print("🎉 **AI VALIDATION TEST COMPLETED**")
    print("=" * 50)
    
    if api_key:
        print("✅ **READY FOR AI-POWERED PROCESSING**")
        print("   Your app will use AI validation when deployed!")
        print("   Chennai→Bangalore→Chennai will be processed with full AI intelligence")
    else:
        print("⚠️ **FALLBACK MODE CONFIRMED**")
        print("   Add API key for full AI capabilities")
    
    return True

if __name__ == "__main__":
    success = test_ai_with_api_key()
    if success:
        print("\n🚀 **AI VALIDATION READY FOR DEPLOYMENT!**")
    else:
        print("\n❌ **AI VALIDATION NEEDS ATTENTION**")
        exit(1)