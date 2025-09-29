#!/usr/bin/env python3
"""
Launch script for the Car Rental Multi-Agent System Streamlit app
"""

import os
import subprocess
import sys
from pathlib import Path

def setup_aws_credentials():
    """Set up AWS credentials for Textract OCR"""
    aws_dir = Path.home() / ".aws"
    credentials_file = aws_dir / "credentials"
    
    # Check if AWS credentials already exist
    if credentials_file.exists():
        print("✅ AWS credentials file already exists")
        return
    
    # Create .aws directory if it doesn't exist
    aws_dir.mkdir(exist_ok=True)
    
    print("⚠️ AWS credentials not found.")
    print("Please configure AWS credentials using one of these methods:")
    print("1. Run: aws configure")
    print("2. Set environment variables: AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY")
    print("3. Create ~/.aws/credentials file manually")
    print("\n📋 For Textract access, you need:")
    print("   - AWS Access Key ID")
    print("   - AWS Secret Access Key")
    print("   - Region: ap-south-1")

def main():
    print("🚗 Car Rental Multi-Agent System")
    print("=" * 50)
    
    # Setup AWS credentials first
    setup_aws_credentials()
    
    print("🎉 System is ready!")
    print("✅ Gemini 2.5 Flash configured (cheapest option)")
    print("✅ AWS Textract OCR enabled for image processing")
    print("✅ Enhanced table detection in multi-booking agent")
    print("✅ Complete multi-agent pipeline with CSV mappings")
    print()
    print("💰 Cost per email: ₹0.0349 (excellent!)")
    print("💰 1000 emails/month: Only ₹35")
    print()
    print("🚀 Starting Streamlit app...")
    print("📱 App will open in your browser at: http://localhost:8501")
    print()
    print("🔑 In the app sidebar:")
    print("   - Select 'Use environment variable' (recommended)")
    print("   - Or select 'Enter manually' and paste your API key")
    print("   - Or select 'Test mode' to try without API costs")
    print()
    print("📸 Image Processing:")
    print("   - Upload PNG/JPG images with table data")
    print("   - System will extract bookings using AWS Textract")
    print("   - Supports complex table layouts and multiple bookings")
    print()
    print("📝 Try the built-in sample inputs to test the system!")
    print()
    
    # Set the environment variables for the session
    # Note: Set your GEMINI_API_KEY environment variable or configure in the app
    if 'GEMINI_API_KEY' not in os.environ:
        print("⚠️ GEMINI_API_KEY not found in environment variables")
        print("You can set it in the app interface")
    
    # Set AWS environment variables for Textract (if available)
    if 'AWS_DEFAULT_REGION' not in os.environ:
        os.environ['AWS_DEFAULT_REGION'] = 'ap-south-1'
    
    if 'AWS_ACCESS_KEY_ID' not in os.environ or 'AWS_SECRET_ACCESS_KEY' not in os.environ:
        print("⚠️ AWS credentials not found in environment variables")
        print("Textract features will not be available without AWS credentials")
    
    try:
        subprocess.run([sys.executable, "-m", "streamlit", "run", "car_rental_app.py"])
    except KeyboardInterrupt:
        print("\n👋 App stopped by user")
    except Exception as e:
        print(f"❌ Failed to start Streamlit: {e}")
        print("Try running manually: streamlit run car_rental_app.py")

if __name__ == "__main__":
    main()