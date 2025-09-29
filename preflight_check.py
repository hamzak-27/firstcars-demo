#!/usr/bin/env python3
"""
Pre-flight check script to verify all components are working
"""

import os
import boto3
from botocore.exceptions import ClientError
from pathlib import Path

def check_aws_credentials():
    """Check if AWS credentials are working"""
    try:
        client = boto3.client('textract', region_name='ap-south-1')
        client.get_document_analysis(JobId='test-job-id')
        return False  # Should not reach here
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'InvalidJobIdException':
            return True  # Credentials work, just invalid job ID
        else:
            return False
    except Exception:
        return False

def check_processors():
    """Check if document processors are available"""
    try:
        from enhanced_multi_booking_processor import EnhancedMultiBookingProcessor
        processor = EnhancedMultiBookingProcessor()
        return processor.textract_available
    except ImportError:
        return False
    except Exception:
        return False

def check_orchestrator():
    """Check if multi-agent orchestrator is working"""
    try:
        from complete_multi_agent_orchestrator import CompleteMultiAgentOrchestrator
        orchestrator = CompleteMultiAgentOrchestrator(api_key='test-key')
        return orchestrator is not None
    except ImportError:
        return False
    except Exception:
        return False

def check_csv_files():
    """Check if CSV mapping files are available"""
    files_to_check = [
        'Corporate (1).csv',
        'City(1).xlsx - Sheet1.csv', 
        'Car.xlsx - Sheet1.csv'
    ]
    
    missing_files = []
    for file in files_to_check:
        if not os.path.exists(file):
            missing_files.append(file)
    
    return len(missing_files) == 0, missing_files

def main():
    """Run all pre-flight checks"""
    print("🚗 Car Rental Multi-Agent System - Pre-flight Check")
    print("=" * 60)
    
    all_good = True
    
    # Check AWS credentials
    print("🔐 Checking AWS credentials...")
    if check_aws_credentials():
        print("   ✅ AWS Textract credentials working")
    else:
        print("   ❌ AWS Textract credentials not working")
        all_good = False
    
    # Check processors
    print("🔧 Checking document processors...")
    if check_processors():
        print("   ✅ Enhanced Multi-Booking Processor ready")
    else:
        print("   ❌ Document processor not available")
        all_good = False
    
    # Check orchestrator
    print("🤖 Checking multi-agent orchestrator...")
    if check_orchestrator():
        print("   ✅ Multi-agent orchestrator ready")
    else:
        print("   ❌ Multi-agent orchestrator not available")
        all_good = False
    
    # Check CSV files
    print("📋 Checking CSV mapping files...")
    csv_ok, missing_files = check_csv_files()
    if csv_ok:
        print("   ✅ All CSV mapping files found")
    else:
        print(f"   ❌ Missing CSV files: {', '.join(missing_files)}")
        all_good = False
    
    print("\n" + "=" * 60)
    
    if all_good:
        print("🎉 ALL SYSTEMS GO! Ready to process your table images!")
        print()
        print("🚀 To start the app, run:")
        print("   python launch_app.py")
        print()
        print("📸 Your system can now:")
        print("   - Extract bookings from table images using AWS Textract")
        print("   - Process multiple booking formats")
        print("   - Apply corporate mappings and business rules")
        print("   - Export results to CSV/Excel/JSON")
    else:
        print("⚠️  Some issues found. Please resolve them before proceeding.")
        print("   Check the error messages above for details.")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()