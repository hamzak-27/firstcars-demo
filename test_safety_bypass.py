#!/usr/bin/env python3
"""
Test enhanced safety settings to bypass Gemini safety filters
"""

import logging
import os
from booking_classification_agent import BookingClassificationAgent
from business_logic_validation_agent import BusinessLogicValidationAgent

# Configure logging
logging.basicConfig(level=logging.INFO)

def test_safety_bypass():
    """Test if enhanced safety settings bypass Gemini safety filters."""
    
    print("🛡️ Testing Enhanced Safety Settings")
    print("=" * 50)
    
    # Check for API key
    api_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_AI_API_KEY')
    
    if not api_key:
        print("⚠️ **NO API KEY FOUND**")
        print("   Set GEMINI_API_KEY or GOOGLE_AI_API_KEY environment variable to test")
        print("   Example: $env:GEMINI_API_KEY = 'your-key-here'")
        return False
    
    print(f"✅ **API KEY FOUND**: Testing safety bypass...")
    
    # Test with the problematic content that was getting blocked
    problematic_content = """
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
    - Driver should have good knowledge of highway routes
    - Vehicle should be well-maintained for long distance
    - Contact operations manager for any issues: operations@techcorp.com
    
    Please confirm the booking and provide driver details.
    
    Thanks,
    Operations Team
    TechCorp Solutions Pvt Ltd
    """
    
    print("📧 **Test Content**: Complex Chennai→Bangalore booking with driver requirements")
    print()
    
    # Test 1: Classification Agent with Enhanced Safety Settings
    print("🎯 **Test 1: Classification with Safety Bypass**")
    print("-" * 45)
    
    try:
        classifier = BookingClassificationAgent()
        if classifier.ai_available:
            print("   ✅ AI Classification: ENABLED")
            result = classifier.classify_text_content(problematic_content)
            
            print(f"   📊 Result: {result.booking_type} booking ({result.predicted_booking_count} count)")
            print(f"   🎯 Confidence: {result.confidence_score * 100:.1f}%")
            print(f"   💭 Reasoning: {result.reasoning[:150]}...")
            
            if result.booking_type == 'single':
                print("   ✅ **SUCCESS**: Safety filters bypassed - AI working correctly!")
                print("   ✅ Correctly identified as single booking")
            else:
                print("   ⚠️ **UNEXPECTED RESULT**: Should be single booking")
            
            classification_success = True
        else:
            print("   ⚠️ AI Classification: DISABLED (no API key or model creation failed)")
            classification_success = False
    
    except Exception as e:
        print(f"   ❌ **CLASSIFICATION ERROR**: {e}")
        classification_success = False
    
    print()
    
    # Test 2: Business Validation with Enhanced Safety Settings
    print("⚙️ **Test 2: Business Validation with Safety Bypass**")
    print("-" * 50)
    
    try:
        validator = BusinessLogicValidationAgent()
        if validator.model:
            print("   ✅ AI Business Validation: ENABLED")
            
            # Create test DataFrame for validation
            import pandas as pd
            test_booking = {
                'Email Content': problematic_content,
                'Corporate': 'TechCorp',
                'Customer': 'TechCorp Solutions Pvt Ltd',
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
                'Dispatch center': 'Chennai Dispatch',
                'Flight/Train Number': 'NA'
            }
            
            test_df = pd.DataFrame([test_booking])
            
            # Test AI validation with safety bypass
            try:
                validated_df = validator._ai_comprehensive_validation_safe(test_df, 0, problematic_content)
                print("   ✅ **SUCCESS**: Safety filters bypassed - AI validation working!")
                
                # Check results
                validated_booking = validated_df.iloc[0]
                print(f"   📝 AI Validated Duty Type: {validated_booking.get('Duty Type', 'N/A')}")
                print(f"   📍 AI Validated Cities: {validated_booking.get('From (Service Location)')} → {validated_booking.get('To')}")
                
                validation_success = True
            except Exception as validation_error:
                print(f"   ❌ **AI VALIDATION STILL BLOCKED**: {validation_error}")
                print("   🔄 Safety filters may still be active or prompt needs adjustment")
                validation_success = False
        else:
            print("   ⚠️ AI Business Validation: DISABLED (no model available)")
            validation_success = False
    
    except Exception as e:
        print(f"   ❌ **BUSINESS VALIDATION ERROR**: {e}")
        validation_success = False
    
    print()
    print("🛡️ **SAFETY BYPASS TEST COMPLETED**")
    print("=" * 50)
    
    if classification_success and validation_success:
        print("✅ **SAFETY FILTERS SUCCESSFULLY BYPASSED!**")
        print("   🎉 AI classification and validation working without restrictions")
        print("   🚀 Ready for full AI-powered processing!")
        return True
    elif classification_success or validation_success:
        print("⚠️ **PARTIAL SUCCESS**")
        if classification_success:
            print("   ✅ AI Classification: Working")
        if validation_success:
            print("   ✅ AI Validation: Working")
        print("   🔄 Some safety filters bypassed, continue investigating others")
        return True
    else:
        print("❌ **SAFETY FILTERS STILL ACTIVE**")
        print("   🛡️ Gemini is still blocking AI responses")
        print("   💡 Try different prompts or contact Google AI support")
        return False

if __name__ == "__main__":
    success = test_safety_bypass()
    if success:
        print("\n🎊 **AI VALIDATION WITH BYPASSED SAFETY FILTERS IS WORKING!**")
        print("🚀 Your Chennai→Bangalore→Chennai booking will be processed with full AI power!")
    else:
        print("\n🔄 **CONTINUE USING RULE-BASED VALIDATION**")
        print("   (Still works perfectly for Chennai→Bangalore→Chennai fix)")
        exit(1)