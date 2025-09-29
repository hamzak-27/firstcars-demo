"""
Enhanced Form and Table Processor
Uses AWS Textract FORMS and TABLES features for better structured data extraction
"""

import os
import logging
import boto3
import json
from typing import Dict, List, Optional, Any, Tuple
from botocore.exceptions import ClientError, NoCredentialsError

from unified_email_processor import UnifiedEmailProcessor
from structured_email_agent import StructuredExtractionResult

logger = logging.getLogger(__name__)

class EnhancedFormProcessor:
    """Enhanced processor focusing on form extraction and table structure preservation"""
    
    def __init__(self, aws_region: str = None, openai_api_key: str = None):
        """
        Initialize enhanced form processor
        
        Args:
            aws_region: AWS region for Textract
            openai_api_key: OpenAI API key for AI processing
        """
        # Auto-detect AWS region if not specified
        if aws_region is None:
            session = boto3.Session()
            aws_region = session.region_name or 'us-east-1'
        
        self.aws_region = aws_region
        self.openai_api_key = openai_api_key or os.getenv('OPENAI_API_KEY')
        # Initialize email processor with None if no OpenAI key
        self.email_processor = UnifiedEmailProcessor(openai_api_key)
        
        # Initialize AWS Textract client
        try:
            self.textract_client = boto3.client('textract', region_name=aws_region)
            
            # Test the credentials with a simple call
            try:
                self.textract_client.get_document_analysis(JobId='test-job-id')
            except ClientError as test_error:
                if test_error.response['Error']['Code'] == 'InvalidJobIdException':
                    # This means credentials work, just invalid job ID
                    self.textract_available = True
                    logger.info(f"AWS Textract initialized for region: {aws_region}")
                elif test_error.response['Error']['Code'] == 'UnrecognizedClientException':
                    # Invalid credentials
                    logger.warning(f"AWS Textract credentials invalid: {str(test_error)}")
                    self.textract_available = False
                else:
                    # Other permission issues
                    logger.warning(f"AWS Textract permission issue: {str(test_error)}")
                    self.textract_available = False
                    
        except (NoCredentialsError, ClientError) as e:
            logger.warning(f"AWS Textract not available: {str(e)}")
            self.textract_available = False

    def process_document(self, file_content: bytes, filename: str, file_type: str = None) -> StructuredExtractionResult:
        """
        Process a document with enhanced form and table extraction
        
        Args:
            file_content: File content as bytes
            filename: Original filename
            file_type: File type hint
            
        Returns:
            StructuredExtractionResult with extracted bookings
        """
        logger.info(f"Enhanced form processing document: {filename}")
        
        if not self.textract_available:
            logger.warning("Textract not available, using fallback processing")
            return self._fallback_processing(file_content, filename, file_type)
        
        try:
            # Step 1: Extract structured data using enhanced Textract features
            extracted_data = self._extract_structured_data(file_content, filename)
            
            if not extracted_data:
                return self._create_error_result("Could not extract structured data from document", filename)
            
            # Step 2: Format the extracted data for AI processing
            formatted_text = self._format_extracted_data(extracted_data)
            
            # Step 3: Process with AI agent
            result = self.email_processor.process_email(formatted_text)
            
            # Step 4: Apply enhanced duty type detection (without OpenAI dependency)
            try:
                from enhanced_duty_type_detector import EnhancedDutyTypeDetector
                duty_detector = EnhancedDutyTypeDetector()
                
                # Apply enhanced duty type detection to each booking
                for booking in result.bookings:
                    # Add extracted data for duty type detection
                    if not booking.additional_info:
                        booking.additional_info = ""
                    booking.additional_info += f"\nStructured Data: {json.dumps(extracted_data, indent=2)}"
                    
                    # Create mock result for duty type detection
                    mock_result = StructuredExtractionResult(
                        bookings=[booking],
                        total_bookings_found=1,
                        extraction_method="enhanced_form_processing",
                        confidence_score=0.8,
                        processing_notes=""
                    )
                    
                    # Detect duty type from structured data
                    duty_result = duty_detector.detect_duty_type_from_structured_data(mock_result, formatted_text)
                    if duty_result:
                        booking.duty_type = duty_result['duty_type']
                        booking.duty_type_reasoning = duty_result['reasoning']
                        booking.confidence_score = duty_result['confidence']
                
                logger.info(f"Enhanced duty type detection applied to {filename}")
            except Exception as e:
                logger.warning(f"Enhanced duty type detection failed: {str(e)}, continuing with standard detection")
            
            # Step 5: Add metadata
            result.extraction_method = f"enhanced_form_extraction_with_duty_detection ({file_type or 'unknown'})"
            result.processing_notes = f"Enhanced form processing: {filename}. Structured fields found: {len(extracted_data.get('key_value_pairs', []))}, Enhanced duty type detection applied"
            
            # Step 6: Add extracted data to additional_info
            for booking in result.bookings:
                document_info = f"Document: {filename}\nStructured Data: {json.dumps(extracted_data, indent=2)}"
                
                if booking.additional_info:
                    booking.additional_info = f"{booking.additional_info}\n\n{document_info}"
                else:
                    booking.additional_info = document_info
            
            logger.info(f"Enhanced form processing completed: {filename}")
            return result
            
        except Exception as e:
            logger.error(f"Enhanced form processing failed for {filename}: {str(e)}")
            return self._fallback_processing(file_content, filename, file_type)

    def _extract_structured_data(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """Extract structured data using Textract FORMS and TABLES"""
        try:
            logger.info(f"Starting Textract analysis for {filename} (size: {len(file_content)} bytes)")
            
            # Use analyze_document with both FORMS and TABLES features
            response = self.textract_client.analyze_document(
                Document={'Bytes': file_content},
                FeatureTypes=['FORMS', 'TABLES']
            )
            
            logger.info(f"Textract analysis completed for {filename}")
            
            # Count total blocks
            total_blocks = len(response.get('Blocks', []))
            logger.info(f"Total blocks returned by Textract: {total_blocks}")
            
            # Extract structured data
            extracted_data = {
                'key_value_pairs': self._extract_key_value_pairs(response),
                'tables': self._extract_enhanced_tables(response),
                'raw_text': self._extract_text_blocks(response)
            }
            
            logger.info(f"Extracted {len(extracted_data['key_value_pairs'])} key-value pairs and {len(extracted_data['tables'])} tables from {filename}")
            logger.info(f"Raw text length: {len(extracted_data.get('raw_text', ''))} characters")
            
            # Log some sample data for debugging
            if extracted_data['raw_text']:
                sample_text = extracted_data['raw_text'][:200] + '...' if len(extracted_data['raw_text']) > 200 else extracted_data['raw_text']
                logger.debug(f"Sample extracted text: {sample_text}")
            
            if not any([extracted_data['key_value_pairs'], extracted_data['tables'], extracted_data['raw_text']]):
                logger.warning(f"No structured data extracted from {filename} despite {total_blocks} blocks returned")
            
            return extracted_data
            
        except Exception as e:
            logger.error(f"Structured data extraction failed for {filename}: {str(e)}", exc_info=True)
            return {}

    def _extract_key_value_pairs(self, response: dict) -> List[Dict[str, str]]:
        """Extract key-value pairs from Textract FORMS analysis"""
        key_value_pairs = []
        
        # Create block map for easier lookup
        block_map = {block['Id']: block for block in response.get('Blocks', [])}
        
        for block in response.get('Blocks', []):
            if block['BlockType'] == 'KEY_VALUE_SET':
                # Process key-value sets
                if block.get('EntityTypes') and 'KEY' in block['EntityTypes']:
                    # This is a key block
                    key_text = self._get_text_from_block(block, block_map)
                    
                    # Find corresponding value
                    value_text = ""
                    for relationship in block.get('Relationships', []):
                        if relationship['Type'] == 'VALUE':
                            for value_id in relationship['Ids']:
                                if value_id in block_map:
                                    value_block = block_map[value_id]
                                    value_text = self._get_text_from_block(value_block, block_map)
                                    break
                    
                    if key_text:
                        key_value_pairs.append({
                            'key': key_text.strip(),
                            'value': value_text.strip(),
                            'confidence': block.get('Confidence', 0.0)
                        })
        
        return key_value_pairs

    def _extract_enhanced_tables(self, response: dict) -> List[Dict[str, Any]]:
        """Extract tables with improved structure preservation"""
        tables = []
        block_map = {block['Id']: block for block in response.get('Blocks', [])}
        
        for block in response.get('Blocks', []):
            if block['BlockType'] == 'TABLE':
                table_data = self._extract_table_with_headers(block, block_map)
                if table_data:
                    tables.append(table_data)
        
        return tables

    def _extract_table_with_headers(self, table_block: dict, block_map: dict) -> Dict[str, Any]:
        """Extract table with proper header-to-value mapping"""
        try:
            # Find all cells in the table
            cells = []
            for relationship in table_block.get('Relationships', []):
                if relationship['Type'] == 'CHILD':
                    for cell_id in relationship['Ids']:
                        if cell_id in block_map and block_map[cell_id]['BlockType'] == 'CELL':
                            cells.append(block_map[cell_id])
            
            if not cells:
                return None
            
            # Organize cells by row and column
            cells.sort(key=lambda x: (x.get('RowIndex', 0), x.get('ColumnIndex', 0)))
            
            # Build table structure
            table_rows = {}
            max_col = 0
            
            for cell in cells:
                row_idx = cell.get('RowIndex', 0)
                col_idx = cell.get('ColumnIndex', 0)
                cell_text = self._get_text_from_block(cell, block_map)
                
                if row_idx not in table_rows:
                    table_rows[row_idx] = {}
                
                table_rows[row_idx][col_idx] = cell_text.strip()
                max_col = max(max_col, col_idx)
            
            # Convert to structured format
            if not table_rows:
                return None
            
            # Check if this is a form-like table (2 columns: key-value pairs)
            if max_col == 1:  # 2-column table (indices 0 and 1)
                key_value_pairs = []
                for row_idx in sorted(table_rows.keys()):
                    row = table_rows[row_idx]
                    key = row.get(0, '').strip()
                    value = row.get(1, '').strip()
                    
                    if key:  # Only add if there's a key
                        key_value_pairs.append({
                            'key': key,
                            'value': value,
                            'row_index': row_idx
                        })
                
                return {
                    'type': 'form_table',
                    'key_value_pairs': key_value_pairs,
                    'row_count': len(table_rows),
                    'column_count': max_col + 1
                }
            else:
                # Regular table with potential headers
                rows = []
                headers = None
                
                for row_idx in sorted(table_rows.keys()):
                    row = table_rows[row_idx]
                    row_data = [row.get(col_idx, '') for col_idx in range(max_col + 1)]
                    
                    if row_idx == 0:  # First row might be headers
                        headers = row_data
                    
                    rows.append(row_data)
                
                return {
                    'type': 'regular_table',
                    'headers': headers,
                    'rows': rows,
                    'row_count': len(rows),
                    'column_count': max_col + 1
                }
            
        except Exception as e:
            logger.warning(f"Error extracting table: {str(e)}")
            return None

    def _get_text_from_block(self, block: dict, block_map: dict) -> str:
        """Extract text from a block by following its child relationships"""
        text_parts = []
        
        for relationship in block.get('Relationships', []):
            if relationship['Type'] == 'CHILD':
                for child_id in relationship['Ids']:
                    if child_id in block_map:
                        child_block = block_map[child_id]
                        if child_block['BlockType'] == 'WORD':
                            text_parts.append(child_block.get('Text', ''))
        
        return ' '.join(text_parts)

    def _extract_text_blocks(self, response: dict) -> str:
        """Extract all text blocks for fallback processing"""
        text_blocks = []
        
        for block in response.get('Blocks', []):
            if block['BlockType'] == 'LINE':
                text_blocks.append(block.get('Text', ''))
        
        return '\n'.join(text_blocks)

    def _format_extracted_data(self, extracted_data: Dict[str, Any]) -> str:
        """Format extracted structured data for AI processing"""
        formatted_parts = []
        
        # Add key-value pairs
        if extracted_data.get('key_value_pairs'):
            formatted_parts.append("=== FORM FIELDS ===")
            for kv in extracted_data['key_value_pairs']:
                formatted_parts.append(f"{kv['key']}: {kv['value']}")
        
        # Add form tables
        if extracted_data.get('tables'):
            for i, table in enumerate(extracted_data['tables']):
                if table['type'] == 'form_table':
                    formatted_parts.append(f"\n=== FORM TABLE {i+1} ===")
                    for kv in table['key_value_pairs']:
                        formatted_parts.append(f"{kv['key']}: {kv['value']}")
                else:
                    formatted_parts.append(f"\n=== TABLE {i+1} ===")
                    if table.get('headers'):
                        formatted_parts.append("Headers: " + " | ".join(table['headers']))
                    
                    for j, row in enumerate(table.get('rows', [])):
                        formatted_parts.append(f"Row {j+1}: " + " | ".join(row))
        
        # Add raw text as fallback
        if extracted_data.get('raw_text'):
            formatted_parts.append("\n=== RAW TEXT (FALLBACK) ===")
            formatted_parts.append(extracted_data['raw_text'])
        
        return '\n'.join(formatted_parts)

    def _fallback_processing(self, file_content: bytes, filename: str, file_type: str = None) -> StructuredExtractionResult:
        """Fallback processing when Textract is not available"""
        logger.info(f"Using fallback processing for {filename}")
        
        try:
            # Basic text extraction
            if not file_type:
                file_type = self._detect_file_type(filename)
            
            if file_type.lower() == 'pdf':
                text = self._extract_pdf_text(file_content)
            else:
                text = f"Could not process file type: {file_type}"
            
            if text:
                result = self.email_processor.process_email(text)
                result.extraction_method = f"fallback_basic ({file_type})"
                result.processing_notes = f"Basic processing: {filename}"
                return result
            else:
                return self._create_error_result("Text extraction failed", filename)
                
        except Exception as e:
            logger.error(f"Fallback processing failed: {str(e)}")
            return self._create_error_result(str(e), filename)

    def _extract_pdf_text(self, file_content: bytes) -> str:
        """Basic PDF text extraction using PyPDF2"""
        try:
            import PyPDF2
            import tempfile
            
            with tempfile.NamedTemporaryFile() as temp_file:
                temp_file.write(file_content)
                temp_file.flush()
                
                with open(temp_file.name, 'rb') as pdf_file:
                    pdf_reader = PyPDF2.PdfReader(pdf_file)
                    text_content = []
                    
                    for page in pdf_reader.pages:
                        text_content.append(page.extract_text())
                    
                    return '\n'.join(text_content)
        except Exception as e:
            logger.warning(f"PDF extraction failed: {str(e)}")
            return ""

    def _detect_file_type(self, filename: str) -> str:
        """Detect file type from filename"""
        if not filename:
            return 'unknown'
        
        extension = filename.split('.')[-1].lower() if '.' in filename else 'unknown'
        return extension

    def _create_error_result(self, error_message: str, filename: str = "") -> StructuredExtractionResult:
        """Create error result for failed processing"""
        from car_rental_ai_agent import BookingExtraction
        
        error_booking = BookingExtraction(
            remarks=f"Document processing failed: {error_message}",
            additional_info=f"Failed to process: {filename}",
            confidence_score=0.0
        )
        
        return StructuredExtractionResult(
            bookings=[error_booking],
            total_bookings_found=0,
            extraction_method="enhanced_form_processing_error",
            confidence_score=0.0,
            processing_notes=f"Enhanced form processing error for {filename}: {error_message}"
        )

    def get_supported_file_types(self) -> List[str]:
        """Get list of supported file types"""
        return ['pdf', 'jpg', 'jpeg', 'png', 'gif']

    def validate_file(self, filename: str, file_size: int, max_size: int = 10 * 1024 * 1024) -> Tuple[bool, str]:
        """
        Validate uploaded file
        
        Args:
            filename: Name of the file
            file_size: Size of file in bytes
            max_size: Maximum allowed size in bytes
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not filename:
            return False, "No filename provided"
        
        # Check file extension
        file_type = self._detect_file_type(filename)
        if file_type not in self.get_supported_file_types():
            return False, f"Unsupported file type: {file_type}. Supported: {', '.join(self.get_supported_file_types())}"
        
        # Check file size
        if file_size > max_size:
            return False, f"File too large: {file_size / (1024*1024):.1f}MB (max: {max_size / (1024*1024):.1f}MB)"
        
        return True, "File is valid"