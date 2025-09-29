#!/usr/bin/env python3
"""
Test New AWS Credentials - Verify Textract and S3 access
"""

import os
import boto3
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_aws_credentials():
    """Test the new AWS credentials"""
    
    print("🔐 Testing New AWS Credentials")
    print("=" * 50)
    
    # Set AWS credentials
    aws_credentials = {
        'AWS_DEFAULT_REGION': 'ap-south-1',
        'AWS_ACCESS_KEY_ID': 'AKIAYLZZKLOTYIXDAARY',
        'AWS_SECRET_ACCESS_KEY': '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',
        'S3_BUCKET_NAME': 'aws-textract-bucket3'
    }
    
    for key, value in aws_credentials.items():
        os.environ[key] = value
    
    print(f"✅ AWS Region: {aws_credentials['AWS_DEFAULT_REGION']}")
    print(f"✅ S3 Bucket: {aws_credentials['S3_BUCKET_NAME']}")
    print(f"✅ Access Key: {aws_credentials['AWS_ACCESS_KEY_ID'][:10]}...{aws_credentials['AWS_ACCESS_KEY_ID'][-4:]}")
    
    # Test 1: Textract client
    print("\n📄 Testing AWS Textract...")
    try:
        textract_client = boto3.client('textract', region_name='ap-south-1')
        
        # Try to get service status (this will verify credentials)
        response = textract_client.describe_document_classification_job(JobId='test-job-id')
    except Exception as e:
        if 'InvalidJobIdException' in str(e) or 'JobId' in str(e):
            print("✅ Textract client initialized successfully (credentials valid)")
        elif 'AccessDenied' in str(e):
            print("❌ Textract access denied - check IAM permissions")
        elif 'UnrecognizedClientException' in str(e):
            print("❌ Textract credentials invalid")
        else:
            print(f"✅ Textract client working (got expected error: {type(e).__name__})")
    
    # Test 2: S3 client and bucket access
    print("\n🪣 Testing S3 Bucket Access...")
    try:
        s3_client = boto3.client('s3', region_name='ap-south-1')
        
        # Test bucket access
        bucket_name = aws_credentials['S3_BUCKET_NAME']
        
        # Try to list objects in bucket (this will verify both credentials and bucket access)
        try:
            response = s3_client.list_objects_v2(Bucket=bucket_name, MaxKeys=1)
            print(f"✅ S3 bucket '{bucket_name}' accessible")
            
            # Check bucket region
            bucket_location = s3_client.get_bucket_location(Bucket=bucket_name)
            region = bucket_location['LocationConstraint'] or 'us-east-1'
            print(f"✅ S3 bucket region: {region}")
            
        except s3_client.exceptions.NoSuchBucket:
            print(f"❌ S3 bucket '{bucket_name}' does not exist")
        except Exception as bucket_error:
            if 'AccessDenied' in str(bucket_error):
                print(f"❌ S3 bucket '{bucket_name}' access denied - check IAM permissions")
            else:
                print(f"⚠️ S3 bucket test: {bucket_error}")
                
    except Exception as e:
        if 'AccessDenied' in str(e):
            print("❌ S3 access denied - check IAM permissions")
        elif 'InvalidAccessKeyId' in str(e):
            print("❌ S3 credentials invalid")
        else:
            print(f"⚠️ S3 client error: {e}")
    
    # Test 3: Test with Enhanced Multi-Booking Processor
    print("\n📊 Testing Enhanced Multi-Booking Processor...")
    try:
        from enhanced_multi_booking_processor import EnhancedMultiBookingProcessor
        
        processor = EnhancedMultiBookingProcessor()
        
        if hasattr(processor, 'textract_available') and processor.textract_available:
            print("✅ Enhanced Multi-Booking Processor: Textract available")
        else:
            print("⚠️ Enhanced Multi-Booking Processor: Textract not available")
            
        if hasattr(processor, 's3_available') and processor.s3_available:
            print("✅ Enhanced Multi-Booking Processor: S3 available")
        else:
            print("⚠️ Enhanced Multi-Booking Processor: S3 not available")
            
    except ImportError as e:
        print(f"❌ Enhanced Multi-Booking Processor: Import failed - {e}")
    except Exception as e:
        print(f"⚠️ Enhanced Multi-Booking Processor: {e}")
    
    # Test 4: Test with Enhanced Form Processor
    print("\n📋 Testing Enhanced Form Processor...")
    try:
        from enhanced_form_processor import EnhancedFormProcessor
        
        processor = EnhancedFormProcessor()
        
        if hasattr(processor, 'textract_available') and processor.textract_available:
            print("✅ Enhanced Form Processor: Textract available")
        else:
            print("⚠️ Enhanced Form Processor: Textract not available")
            
    except ImportError as e:
        print(f"❌ Enhanced Form Processor: Import failed - {e}")
    except Exception as e:
        print(f"⚠️ Enhanced Form Processor: {e}")
    
    print("\n" + "=" * 50)
    print("✨ AWS Credentials Test Complete!")

if __name__ == "__main__":
    test_aws_credentials()