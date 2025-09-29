#!/usr/bin/env python3
"""
Standalone Textract Table Extraction Tester
Use this file to test Textract table extraction independently on Google Colab
"""

import boto3
import json
import logging
from typing import Dict, List, Any

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class StandaloneTextractTester:
    """Standalone Textract tester for table extraction"""
    
    def __init__(self, aws_region: str = "ap-south-1"):
        """Initialize Textract client"""
        try:
            self.textract_client = boto3.client('textract', region_name=aws_region)
            logger.info(f"Textract client initialized for region: {aws_region}")
        except Exception as e:
            logger.error(f"Failed to initialize Textract: {e}")
            self.textract_client = None
    
    def analyze_image(self, image_path: str) -> Dict[str, Any]:
        """
        Analyze image using Textract and extract tables
        
        Args:
            image_path: Path to the image file
        
        Returns:
            Dictionary with extracted data
        """
        if not self.textract_client:
            return {"error": "Textract not available"}
        
        try:
            # Read image file
            with open(image_path, 'rb') as image_file:
                image_bytes = image_file.read()
            
            logger.info(f"Analyzing image: {image_path} ({len(image_bytes)} bytes)")
            
            # Call Textract with TABLES and FORMS features
            response = self.textract_client.analyze_document(
                Document={'Bytes': image_bytes},
                FeatureTypes=['TABLES', 'FORMS']
            )
            
            logger.info(f"Textract analysis completed. Total blocks: {len(response.get('Blocks', []))}")
            
            # Extract structured data
            result = {
                'total_blocks': len(response.get('Blocks', [])),
                'tables': self._extract_all_tables(response),
                'key_value_pairs': self._extract_key_value_pairs(response),
                'raw_text': self._extract_raw_text(response),
                'block_analysis': self._analyze_blocks(response)
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing image: {e}")
            return {"error": str(e)}
    
    def _extract_all_tables(self, response: dict) -> List[Dict[str, Any]]:
        """Extract all tables with detailed structure"""
        tables = []
        block_map = {block['Id']: block for block in response.get('Blocks', [])}
        
        for block in response.get('Blocks', []):
            if block['BlockType'] == 'TABLE':
                table_data = self._extract_detailed_table(block, block_map)
                if table_data:
                    tables.append(table_data)
        
        logger.info(f"Found {len(tables)} tables")
        return tables
    
    def _extract_detailed_table(self, table_block: dict, block_map: dict) -> Dict[str, Any]:
        """Extract table with complete details"""
        try:
            # Find all cells
            cells = []
            for relationship in table_block.get('Relationships', []):
                if relationship['Type'] == 'CHILD':
                    for cell_id in relationship['Ids']:
                        if cell_id in block_map and block_map[cell_id]['BlockType'] == 'CELL':
                            cells.append(block_map[cell_id])
            
            if not cells:
                return None
            
            # Organize cells by position
            cells.sort(key=lambda x: (x.get('RowIndex', 0), x.get('ColumnIndex', 0)))
            
            # Build table structure
            table_grid = {}
            max_row = 0
            max_col = 0
            
            for cell in cells:
                row_idx = cell.get('RowIndex', 0)
                col_idx = cell.get('ColumnIndex', 0)
                cell_text = self._get_cell_text(cell, block_map)
                
                if row_idx not in table_grid:
                    table_grid[row_idx] = {}
                
                table_grid[row_idx][col_idx] = cell_text.strip()
                max_row = max(max_row, row_idx)
                max_col = max(max_col, col_idx)
            
            # Convert to readable format
            headers = []
            rows = []
            
            # Extract headers (first row)
            if 0 in table_grid:
                headers = [table_grid[0].get(col, '') for col in range(max_col + 1)]
            
            # Extract all rows
            for row_idx in range(max_row + 1):
                if row_idx in table_grid:
                    row_data = [table_grid[row_idx].get(col, '') for col in range(max_col + 1)]
                    rows.append(row_data)
            
            # Determine table type
            table_type = 'form_table' if max_col <= 1 else 'regular_table'
            
            logger.info(f"Extracted table: {len(rows)} rows x {max_col + 1} columns, type: {table_type}")
            logger.info(f"Headers: {headers}")
            
            return {
                'type': table_type,
                'headers': headers,
                'rows': rows,
                'row_count': len(rows),
                'column_count': max_col + 1,
                'confidence': table_block.get('Confidence', 0.0),
                'raw_cells': len(cells)
            }
            
        except Exception as e:
            logger.error(f"Error extracting table: {e}")
            return None
    
    def _get_cell_text(self, cell_block: dict, block_map: dict) -> str:
        """Extract text from a cell"""
        text_parts = []
        
        for relationship in cell_block.get('Relationships', []):
            if relationship['Type'] == 'CHILD':
                for child_id in relationship['Ids']:
                    if child_id in block_map:
                        child_block = block_map[child_id]
                        if child_block['BlockType'] == 'WORD':
                            text_parts.append(child_block.get('Text', ''))
        
        return ' '.join(text_parts)
    
    def _extract_key_value_pairs(self, response: dict) -> List[Dict[str, str]]:
        """Extract key-value pairs from FORMS"""
        kv_pairs = []
        block_map = {block['Id']: block for block in response.get('Blocks', [])}
        
        for block in response.get('Blocks', []):
            if block['BlockType'] == 'KEY_VALUE_SET' and block.get('EntityTypes') and 'KEY' in block['EntityTypes']:
                key_text = self._get_cell_text(block, block_map)
                
                # Find corresponding value
                value_text = ""
                for relationship in block.get('Relationships', []):
                    if relationship['Type'] == 'VALUE':
                        for value_id in relationship['Ids']:
                            if value_id in block_map:
                                value_block = block_map[value_id]
                                value_text = self._get_cell_text(value_block, block_map)
                                break
                
                if key_text:
                    kv_pairs.append({
                        'key': key_text.strip(),
                        'value': value_text.strip(),
                        'confidence': block.get('Confidence', 0.0)
                    })
        
        logger.info(f"Found {len(kv_pairs)} key-value pairs")
        return kv_pairs
    
    def _extract_raw_text(self, response: dict) -> str:
        """Extract all raw text"""
        text_blocks = []
        
        for block in response.get('Blocks', []):
            if block['BlockType'] == 'LINE':
                text_blocks.append(block.get('Text', ''))
        
        raw_text = '\n'.join(text_blocks)
        logger.info(f"Raw text length: {len(raw_text)} characters")
        return raw_text
    
    def _analyze_blocks(self, response: dict) -> Dict[str, int]:
        """Analyze block types"""
        block_counts = {}
        
        for block in response.get('Blocks', []):
            block_type = block['BlockType']
            block_counts[block_type] = block_counts.get(block_type, 0) + 1
        
        return block_counts
    
    def print_analysis_results(self, results: Dict[str, Any]):
        """Print detailed analysis results"""
        print("="*80)
        print("TEXTRACT ANALYSIS RESULTS")
        print("="*80)
        
        if 'error' in results:
            print(f"❌ ERROR: {results['error']}")
            return
        
        print(f"📊 OVERVIEW:")
        print(f"   Total blocks: {results['total_blocks']}")
        print(f"   Tables found: {len(results['tables'])}")
        print(f"   Key-value pairs: {len(results['key_value_pairs'])}")
        print(f"   Raw text length: {len(results['raw_text'])}")
        
        print(f"\n📋 BLOCK TYPES:")
        for block_type, count in results['block_analysis'].items():
            print(f"   {block_type}: {count}")
        
        print(f"\n📊 TABLES ANALYSIS:")
        for i, table in enumerate(results['tables'], 1):
            print(f"\n   TABLE {i}:")
            print(f"   - Type: {table['type']}")
            print(f"   - Dimensions: {table['row_count']} rows x {table['column_count']} columns")
            print(f"   - Confidence: {table['confidence']:.1f}%")
            print(f"   - Headers: {table['headers']}")
            print(f"   - Sample rows:")
            for j, row in enumerate(table['rows'][:3]):  # Show first 3 rows
                print(f"     Row {j}: {row}")
            if len(table['rows']) > 3:
                print(f"     ... and {len(table['rows'])-3} more rows")
        
        print(f"\n🔑 KEY-VALUE PAIRS:")
        for i, kv in enumerate(results['key_value_pairs'][:5], 1):  # Show first 5
            print(f"   {i}. '{kv['key']}' = '{kv['value']}'")
        if len(results['key_value_pairs']) > 5:
            print(f"   ... and {len(results['key_value_pairs'])-5} more pairs")
        
        print(f"\n📝 SAMPLE RAW TEXT:")
        sample_text = results['raw_text'][:200] + "..." if len(results['raw_text']) > 200 else results['raw_text']
        print(f"   {sample_text}")
        
        print("="*80)


def main():
    """Main function for testing"""
    print("🧪 STANDALONE TEXTRACT TABLE EXTRACTION TESTER")
    print("="*60)
    
    # Instructions for Google Colab
    print("\n📋 GOOGLE COLAB SETUP INSTRUCTIONS:")
    print("1. Install dependencies:")
    print("   !pip install boto3")
    print("\n2. Configure AWS credentials:")
    print("   import os")
    print("   os.environ['AWS_ACCESS_KEY_ID'] = 'your_access_key'")
    print("   os.environ['AWS_SECRET_ACCESS_KEY'] = 'your_secret_key'")
    print("\n3. Upload your table image to Colab")
    print("\n4. Run this tester:")
    print("   tester = StandaloneTextractTester()")
    print("   results = tester.analyze_image('your_image.png')")
    print("   tester.print_analysis_results(results)")
    
    print("\n" + "="*60)
    
    # Initialize tester
    tester = StandaloneTextractTester()
    
    # Check if we can find any image files locally
    import glob
    image_files = glob.glob('*.png') + glob.glob('*.jpg') + glob.glob('*.jpeg')
    
    if image_files:
        print(f"\n📁 Found local image files: {image_files}")
        
        # Test with first image found
        image_file = image_files[0]
        print(f"\n🔍 Testing with: {image_file}")
        
        results = tester.analyze_image(image_file)
        tester.print_analysis_results(results)
        
        # Save results to JSON for further analysis
        output_file = f"textract_analysis_{image_file.replace('.', '_')}.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n💾 Results saved to: {output_file}")
        
    else:
        print("\n❌ No image files found in current directory")
        print("Upload your table image and run:")
        print("   tester = StandaloneTextractTester()")
        print("   results = tester.analyze_image('your_image.png')")
        print("   tester.print_analysis_results(results)")


if __name__ == "__main__":
    main()