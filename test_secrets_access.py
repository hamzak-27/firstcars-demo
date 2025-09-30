#!/usr/bin/env python3
"""
Test script to verify that all API keys and secrets are accessible from Streamlit
"""

import streamlit as st
import os
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

def test_openai_key():
    """Test OpenAI API key access"""
    try:
        api_key = st.secrets["OPENAI_API_KEY"]
        if api_key and api_key.startswith("sk-"):
            return True, f"✅ OpenAI API key found and valid format ({api_key[:10]}...{api_key[-4:]})"
        else:
            return False, "❌ OpenAI API key format invalid"
    except KeyError:
        return False, "❌ OPENAI_API_KEY not found in secrets"
    except Exception as e:
        return False, f"❌ Error accessing OpenAI key: {str(e)}"

def test_gemini_key():
    """Test Gemini API key access"""
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
        if api_key and api_key.startswith("AIzaSy"):
            return True, f"✅ Gemini API key found and valid format ({api_key[:10]}...{api_key[-4:]})"
        else:
            return False, "❌ Gemini API key format invalid"
    except KeyError:
        return False, "❌ GEMINI_API_KEY not found in secrets"
    except Exception as e:
        return False, f"❌ Error accessing Gemini key: {str(e)}"

def test_aws_credentials():
    """Test AWS credentials access and functionality"""
    try:
        # Get AWS credentials from secrets
        access_key = st.secrets["AWS_ACCESS_KEY_ID"]
        secret_key = st.secrets["AWS_SECRET_ACCESS_KEY"] 
        region = st.secrets["AWS_DEFAULT_REGION"]
        bucket = st.secrets.get("S3_BUCKET_NAME", "aws-textract-bucket3")
        
        # Set environment variables for boto3
        os.environ['AWS_ACCESS_KEY_ID'] = access_key
        os.environ['AWS_SECRET_ACCESS_KEY'] = secret_key
        os.environ['AWS_DEFAULT_REGION'] = region
        
        # Test Textract client
        textract_client = boto3.client('textract', region_name=region)
        
        # Test credentials with a dummy call
        try:
            textract_client.get_document_analysis(JobId='test-job-id')
        except ClientError as test_error:
            if test_error.response['Error']['Code'] == 'InvalidJobIdException':
                # Credentials work, just invalid job ID
                textract_status = "✅ Textract credentials valid"
            elif test_error.response['Error']['Code'] == 'UnrecognizedClientException':
                textract_status = "❌ Textract credentials invalid"
            else:
                textract_status = f"⚠️ Textract permission issue: {test_error.response['Error']['Code']}"
        
        # Test S3 client
        s3_client = boto3.client('s3', region_name=region)
        try:
            s3_client.head_bucket(Bucket=bucket)
            s3_status = f"✅ S3 bucket '{bucket}' accessible"
        except ClientError as s3_error:
            if s3_error.response['Error']['Code'] == '403':
                s3_status = f"⚠️ S3 bucket '{bucket}' exists but access denied"
            elif s3_error.response['Error']['Code'] == '404':
                s3_status = f"❌ S3 bucket '{bucket}' not found"
            else:
                s3_status = f"❌ S3 error: {s3_error.response['Error']['Code']}"
        
        return True, {
            "credentials": f"✅ AWS credentials found (Access Key: {access_key[:10]}...{access_key[-4:]})",
            "region": f"✅ Region: {region}",
            "textract": textract_status,
            "s3": s3_status
        }
        
    except KeyError as e:
        return False, f"❌ Missing AWS secret: {str(e)}"
    except Exception as e:
        return False, f"❌ AWS error: {str(e)}"

def test_google_sheets():
    """Test Google Sheets credentials access"""
    try:
        credentials_json = st.secrets.get("GOOGLE_SHEETS_CREDENTIALS_JSON")
        if credentials_json:
            return True, "✅ Google Sheets credentials found"
        else:
            return False, "⚠️ Google Sheets credentials not configured (optional)"
    except Exception as e:
        return False, f"❌ Error accessing Google Sheets credentials: {str(e)}"

def main():
    st.set_page_config(
        page_title="Secrets Test",
        page_icon="🔐",
        layout="wide"
    )
    
    st.title("🔐 FirstCars Secrets Configuration Test")
    st.markdown("**Testing all API keys and credentials configuration**")
    st.markdown("---")
    
    # Test OpenAI
    st.subheader("🤖 OpenAI API")
    openai_success, openai_msg = test_openai_key()
    if openai_success:
        st.success(openai_msg)
    else:
        st.error(openai_msg)
    
    # Test Gemini
    st.subheader("🧠 Gemini AI API")
    gemini_success, gemini_msg = test_gemini_key()
    if gemini_success:
        st.success(gemini_msg)
    else:
        st.error(gemini_msg)
    
    # Test AWS
    st.subheader("☁️ AWS Services")
    aws_success, aws_result = test_aws_credentials()
    if aws_success:
        for key, message in aws_result.items():
            if message.startswith("✅"):
                st.success(message)
            elif message.startswith("⚠️"):
                st.warning(message)
            else:
                st.error(message)
    else:
        st.error(aws_result)
    
    # Test Google Sheets
    st.subheader("📊 Google Sheets Integration")
    sheets_success, sheets_msg = test_google_sheets()
    if sheets_success:
        st.success(sheets_msg)
    else:
        st.warning(sheets_msg)
    
    # Summary
    st.markdown("---")
    st.subheader("📋 Configuration Summary")
    
    total_tests = 4
    passed_tests = sum([openai_success, gemini_success, aws_success, sheets_success])
    
    if passed_tests == total_tests:
        st.success(f"🎉 All {total_tests} tests passed! Your app is fully configured.")
    elif passed_tests >= 3:
        st.success(f"✅ {passed_tests}/{total_tests} tests passed. Core functionality available.")
    else:
        st.error(f"❌ Only {passed_tests}/{total_tests} tests passed. Please check your configuration.")
    
    # Next steps
    with st.expander("🚀 Next Steps", expanded=True):
        st.markdown("""
        **If all tests passed:**
        - Your FirstCars app is fully configured
        - All features (OpenAI extraction, Gemini classification, AWS document processing, Google Sheets) are available
        
        **If some tests failed:**
        - OpenAI: Required for main email extraction
        - Gemini: Used for classification features
        - AWS: Required for document/image processing
        - Google Sheets: Optional for data persistence
        
        **Recommended setup for production:**
        1. ✅ OpenAI API key (primary extraction)
        2. ✅ AWS credentials (document processing) 
        3. ✅ Gemini API key (classification features)
        4. ⚠️ Google Sheets (optional but recommended)
        """)

if __name__ == "__main__":
    main()