#!/usr/bin/env python3
"""
Test script to debug AWS Textract processing
"""

import boto3
import json
import sys
import os
from botocore.exceptions import ClientError, NoCredentialsError

def test_textract_with_image(image_path):
    """Test Textract processing with the uploaded image"""
    
    print(f"🔍 Testing Textract with image: {image_path}")
    print("=" * 60)
    
    try:
        # Read the image
        with open(image_path, 'rb') as f:
            image_content = f.read()
        
        print(f"📁 Image size: {len(image_content)} bytes")
        
        # Try different AWS regions
        regions_to_try = ['ap-south-1', 'us-east-1', 'us-west-2']
        
        for region in regions_to_try:
            print(f"\\n🌍 Testing region: {region}")
            
            try:
                # Create Textract client for this region
                client = boto3.client('textract', region_name=region)
                
                # Test with FORMS and TABLES analysis
                response = client.analyze_document(
                    Document={'Bytes': image_content},
                    FeatureTypes=['FORMS', 'TABLES']
                )
                
                print(f"✅ Textract successful in region: {region}")
                
                # Count the blocks
                blocks = response.get('Blocks', [])
                print(f"📊 Total blocks found: {len(blocks)}")
                
                # Count by type
                block_types = {}
                for block in blocks:
                    block_type = block.get('BlockType', 'UNKNOWN')
                    block_types[block_type] = block_types.get(block_type, 0) + 1
                
                print("📋 Block types found:")
                for block_type, count in block_types.items():
                    print(f"  - {block_type}: {count}")
                
                # Extract some sample text
                text_blocks = []
                for block in blocks[:10]:  # Show first 10 blocks
                    if block.get('BlockType') == 'LINE' and block.get('Text'):
                        text_blocks.append(block['Text'])
                
                if text_blocks:
                    print("\\n📝 Sample extracted text:")
                    for i, text in enumerate(text_blocks[:5], 1):
                        print(f"  {i}. {text}")
                else:
                    print("⚠️ No text extracted")
                
                # Check for tables
                table_blocks = [b for b in blocks if b.get('BlockType') == 'TABLE']
                print(f"\\n🏓 Tables found: {len(table_blocks)}")
                
                if table_blocks:
                    for i, table in enumerate(table_blocks, 1):
                        print(f"Table {i}: {table.get('Id', 'Unknown ID')}")
                        
                        # Count cells in this table
                        cell_count = 0
                        for relationship in table.get('Relationships', []):
                            if relationship['Type'] == 'CHILD':
                                cell_count = len(relationship.get('Ids', []))
                        print(f"  - Cells: {cell_count}")
                
                # Check for key-value pairs  
                kv_blocks = [b for b in blocks if b.get('BlockType') == 'KEY_VALUE_SET']
                print(f"\\n🔑 Key-Value pairs found: {len(kv_blocks)}")
                
                return True, region, response
                
            except ClientError as e:
                print(f"❌ Region {region} failed: {e}")
                continue
            except Exception as e:
                print(f"❌ Region {region} error: {e}")
                continue
        
        print("\\n❌ All regions failed!")
        return False, None, None
        
    except Exception as e:
        print(f"❌ Failed to test image: {e}")
        return False, None, None

def analyze_extraction_failure():
    """Analyze why extraction might be failing"""
    print("\\n🔧 TROUBLESHOOTING ANALYSIS")
    print("=" * 60)
    
    # Check common issues
    issues = []
    
    # Check AWS credentials
    try:
        session = boto3.Session()
        credentials = session.get_credentials()
        if not credentials:
            issues.append("❌ AWS credentials not configured")
        else:
            print("✅ AWS credentials are available")
    except:
        issues.append("❌ AWS credentials error")
    
    # Check region configuration
    session = boto3.Session()
    region = session.region_name
    print(f"🌍 Default AWS region: {region or 'Not set'}")
    
    if issues:
        print("\\n⚠️ ISSUES FOUND:")
        for issue in issues:
            print(f"  {issue}")
    else:
        print("\\n✅ Basic AWS setup looks good")
    
    print("\\n💡 POSSIBLE SOLUTIONS:")
    print("1. Try using your region (ap-south-1) instead of us-east-1")
    print("2. Check if image quality/format is suitable for OCR") 
    print("3. Verify Textract service is available in your region")
    print("4. Check image size limits (max 10MB for analyze_document)")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python test_textract.py <path_to_image>")
        print("Example: python test_textract.py 'Screenshot 2025-09-26 131539.png'")
        sys.exit(1)
    
    image_path = sys.argv[1]
    
    if not os.path.exists(image_path):
        print(f"Error: Image file not found: {image_path}")
        sys.exit(1)
    
    success, region, response = test_textract_with_image(image_path)
    
    if not success:
        analyze_extraction_failure()
    else:
        print(f"\\n🎉 Success! Working region: {region}")
        print("\\nTo fix the issue, update your processor to use the working region.")