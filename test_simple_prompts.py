#!/usr/bin/env python3
"""
Test simplified prompts to bypass Gemini safety filters
"""

import logging
import os
from booking_classification_agent import BookingClassificationAgent

# Configure logging
logging.basicConfig(level=logging.INFO)

def test_simple_prompts():
    """Test if simplified prompts bypass safety filters."""
    
    print("🎯 Testing Simplified Prompts")
    print("=" * 40)
    
    # Check for API key
    api_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_AI_API_KEY')
    
    if not api_key:
        print("⚠️ **NO API KEY FOUND**")
        print("   Set GEMINI_API_KEY or GOOGLE_AI_API_KEY to test")
        return False
    
    print(f"✅ **API KEY FOUND**: Testing simple prompts...")
    
    # Test with simple Chennai to Bangalore content
    simple_content = """
    Dear Team,
    
    Please arrange cab for Chennai to Bangalore to Chennai trip.
    Date: Tomorrow 
    Time: 5 AM
    Passenger: Rajesh Kumar
    Phone: 9876543210
    
    Thanks
    """
    
    print("📧 **Test Content**: Simple Chennai→Bangalore→Chennai")
    print()
    
    try:
        classifier = BookingClassificationAgent()
        if classifier.ai_available:
            print("   ✅ AI Classification: ENABLED")
            print("   🔄 Testing simplified prompt...")
            
            result = classifier.classify_text_content(simple_content)
            
            print(f"   📊 Result: {result.booking_type} booking ({result.predicted_booking_count} count)")
            print(f"   🎯 Confidence: {result.confidence_score * 100:.1f}%")
            print(f"   💭 Reasoning: {result.reasoning}")
            
            if result.booking_type == 'single':
                print("   ✅ **SUCCESS**: Simple prompt worked! Safety filters bypassed!")
                print("   ✅ Correctly identified Chennai→Bangalore→Chennai as single booking")
                return True
            else:
                print("   ⚠️ **UNEXPECTED RESULT**: Should be single booking")
                return False
                
        else:
            print("   ⚠️ AI Classification: DISABLED")
            return False
    
    except Exception as e:
        if "finish_reason=2" in str(e) or "SAFETY" in str(e):
            print(f"   ❌ **SAFETY FILTER STILL BLOCKING**: {e}")
            print("   🔄 Even simple prompts are being blocked")
            return False
        else:
            print(f"   ❌ **OTHER ERROR**: {e}")
            return False

def test_direct_api():
    """Test direct API call with minimal prompt"""
    print("\n🧪 **Direct API Test with Minimal Prompt**")
    print("-" * 45)
    
    api_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_AI_API_KEY')
    if not api_key:
        print("   ⚠️ No API key for direct test")
        return False
    
    try:
        import google.generativeai as genai
        
        genai.configure(api_key=api_key)
        
        # Create model with no safety settings
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        # Minimal prompt
        minimal_prompt = """Is this one trip or multiple trips?
        
"Please book car from Chennai to Bangalore and back to Chennai tomorrow at 5am"

Answer: one trip or multiple trips?"""
        
        print(f"   📝 Minimal prompt: {minimal_prompt[:100]}...")
        
        response = model.generate_content(
            minimal_prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.1,
                max_output_tokens=50
            )
        )
        
        if response and hasattr(response, 'text') and response.text:
            print(f"   ✅ **SUCCESS**: Direct API worked!")
            print(f"   💬 Response: {response.text.strip()}")
            return True
        else:
            print("   ❌ No response from direct API")
            return False
            
    except Exception as e:
        if "finish_reason=2" in str(e):
            print(f"   ❌ **SAFETY FILTER**: Even minimal prompt blocked")
            return False
        else:
            print(f"   ❌ **API ERROR**: {e}")
            return False

if __name__ == "__main__":
    success1 = test_simple_prompts()
    success2 = test_direct_api()
    
    if success1 or success2:
        print("\n🎉 **SIMPLIFIED PROMPTS WORKING!**")
        if success1:
            print("✅ Classification agent with simple prompts: SUCCESS")
        if success2:
            print("✅ Direct API with minimal prompt: SUCCESS")
        print("🚀 Safety filters can be bypassed with simpler prompts!")
    else:
        print("\n❌ **SAFETY FILTERS STILL ACTIVE**")
        print("🛡️ Even minimal prompts are being blocked")
        print("💡 Consider using different model or contacting Google AI support")
        exit(1)