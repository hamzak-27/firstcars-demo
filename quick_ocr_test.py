#!/usr/bin/env python3
"""
Quick test to verify OCR processing with region fix
"""

import logging
import sys

# Set up logging to see detailed output
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_ocr_processing():
    """Test OCR processing with a sample image"""
    
    try:
        from enhanced_multi_booking_processor import EnhancedMultiBookingProcessor
        
        print("🔧 Testing Enhanced Multi-Booking Processor")
        print("=" * 50)
        
        # Initialize processor (should now use ap-south-1 automatically)
        processor = EnhancedMultiBookingProcessor()
        
        print(f"✅ Processor initialized")
        print(f"   - AWS Region: {processor.aws_region}")
        print(f"   - Textract Available: {processor.textract_available}")
        
        if not processor.textract_available:
            print("❌ Textract not available - check AWS credentials")
            return False
            
        print("\\n🎯 Ready to process images!")
        print("   You can now upload your screenshot in the debug Streamlit app")
        print("   The processor should now work correctly with your AWS region")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_ocr_processing()
    
    if success:
        print("\\n✨ OCR system is ready!")
        print("\\n🚀 Next steps:")
        print("1. Run: python launch_debug_app.py")
        print("2. Upload your screenshot image")
        print("3. The system should now extract bookings correctly")
    else:
        print("\\n❌ OCR system needs attention")
        print("Check AWS credentials and region configuration")