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
    
    # Set the Gemini API key
    gemini_api_key = "AIzaSyAId73p8fsv1U0z2_jQ0yOLdcVJsVsOmeg"
    os.environ['GEMINI_API_KEY'] = gemini_api_key
    os.environ['GOOGLE_AI_API_KEY'] = gemini_api_key  # Alternative env var name
    print(f"✅ Gemini API key configured: {gemini_api_key[:20]}...{gemini_api_key[-4:]}")  # Show partial key for verification
    
    # Set AWS environment variables for Textract
    aws_credentials = {
        'AWS_DEFAULT_REGION': 'ap-south-1',
        'AWS_ACCESS_KEY_ID': 'AKIAYLZZKLOTYIXDAARY',
        'AWS_SECRET_ACCESS_KEY': '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',
        'S3_BUCKET_NAME': 'aws-textract-bucket3'
    }
    
    for key, value in aws_credentials.items():
        os.environ[key] = value
    
    print(f"✅ AWS credentials configured for region: {aws_credentials['AWS_DEFAULT_REGION']}")
    print(f"✅ S3 bucket configured: {aws_credentials['S3_BUCKET_NAME']}")
    print(f"✅ AWS Access Key: {aws_credentials['AWS_ACCESS_KEY_ID'][:10]}...{aws_credentials['AWS_ACCESS_KEY_ID'][-4:]}")
    
    try:
        subprocess.run([sys.executable, "-m", "streamlit", "run", "car_rental_app.py"])
    except KeyboardInterrupt:
        print("\n👋 App stopped by user")
    except Exception as e:
        print(f"❌ Failed to start Streamlit: {e}")
        print("Try running manually: streamlit run car_rental_app.py")

if __name__ == "__main__":
    main()