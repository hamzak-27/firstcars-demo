"""
Practical Enhanced Document and Image Processor
Uses AWS Textract with enhanced AI prompting for better OCR + AI extraction
"""

import os
import logging
import boto3
import json
import tempfile
from typing import Dict, List, Optional, Any, Tuple, Union
from botocore.exceptions import ClientError, NoCredentialsError
from io import BytesIO

# Import our AI agents
from unified_email_processor import UnifiedEmailProcessor
from structured_email_agent import StructuredExtractionResult

logger = logging.getLogger(__name__)

class PracticalDocumentProcessor:
    """Enhanced document processor using AWS Textract + enhanced AI prompting"""
    
    def __init__(self, aws_region: str = 'us-east-1', openai_api_key: str = None):
        """
        Initialize practical document processor
        
        Args:
            aws_region: AWS region for Textract
            openai_api_key: OpenAI API key for AI processing
        """
        self.aws_region = aws_region
        self.openai_api_key = openai_api_key or os.getenv('OPENAI_API_KEY')
        self.email_processor = UnifiedEmailProcessor(openai_api_key)
        
        # Initialize AWS Textract client
        try:
            self.textract_client = boto3.client('textract', region_name=aws_region)
            self.textract_available = True
            logger.info(f"AWS Textract initialized for region: {aws_region}")
        except (NoCredentialsError, ClientError) as e:
            logger.warning(f"AWS Textract not available: {str(e)}")
            self.textract_available = False

    def process_document(self, file_content: bytes, filename: str, file_type: str = None) -> StructuredExtractionResult:
        """
        Process a document using enhanced Textract + AI approach
        
        Args:
            file_content: File content as bytes
            filename: Original filename
            file_type: File type hint
            
        Returns:
            StructuredExtractionResult with extracted bookings
        """
        logger.info(f"Processing document with enhanced OCR: {filename}")
        
        try:
            # Step 1: Extract text using AWS Textract
            extracted_text = self._extract_text_with_textract(file_content, filename, file_type)
            
            if not extracted_text:
                return self._create_error_result("Could not extract text from document", filename)
            
            logger.info(f"Extracted {len(extracted_text)} characters from {filename}")
            
            # Step 2: Use enhanced AI processing with better prompting
            result = self._process_with_enhanced_prompts(extracted_text, filename)
            
            # Step 3: Add metadata
            result.extraction_method = f"enhanced_textract_ai ({file_type or self._detect_file_type(filename)})"
            result.processing_notes = f"Enhanced OCR processing: {filename}. Text length: {len(extracted_text)} chars."
            
            # Step 4: Add extracted text to additional_info
            for booking in result.bookings:
                document_info = f"Document: {filename}\\nOCR extracted: {extracted_text[:800]}{'...' if len(extracted_text) > 800 else ''}"
                
                if booking.additional_info:
                    booking.additional_info = f"{booking.additional_info}\\n\\n{document_info}"
                else:
                    booking.additional_info = document_info
            
            logger.info(f"Enhanced document processing completed: {filename}, found {len(result.bookings)} booking(s)")
            return result
            
        except Exception as e:
            logger.error(f"Enhanced document processing failed for {filename}: {str(e)}")
            return self._create_error_result(str(e), filename)
    
    def _extract_text_with_textract(self, file_content: bytes, filename: str, file_type: str = None) -> str:
        """Extract text using AWS Textract with enhanced parsing"""
        
        if not self.textract_available:
            return self._fallback_text_extraction(file_content, filename, file_type)
        
        try:
            # Detect file type if not provided
            if not file_type:
                file_type = self._detect_file_type(filename)
            
            file_type = file_type.lower()
            
            # Use appropriate Textract method based on file type
            if file_type in ['jpg', 'jpeg', 'png', 'gif']:
                # For images (including screenshots), use analyze_document for better table detection
                response = self._textract_analyze_document(file_content)
            elif file_type in ['pdf']:
                # For PDFs, use analyze_document for structure
                response = self._textract_analyze_document(file_content)
            else:
                # For other documents, try detect_document_text
                response = self._textract_detect_text(file_content)
            
            # Enhanced text parsing
            extracted_text = self._enhanced_parse_textract_response(response)
            return extracted_text
            
        except Exception as e:
            logger.error(f"AWS Textract failed for {filename}: {str(e)}")
            return self._fallback_text_extraction(file_content, filename, file_type)
    
    def _textract_detect_text(self, file_content: bytes) -> dict:
        """Use Textract detect_document_text for basic OCR"""
        return self.textract_client.detect_document_text(
            Document={'Bytes': file_content}
        )
    
    def _textract_analyze_document(self, file_content: bytes) -> dict:
        """Use Textract analyze_document for structured analysis"""
        return self.textract_client.analyze_document(
            Document={'Bytes': file_content},
            FeatureTypes=['TABLES', 'FORMS', 'LAYOUT']
        )
    
    def _enhanced_parse_textract_response(self, response: dict) -> str:
        """Enhanced parsing of Textract response with better structure detection"""
        text_blocks = []
        table_blocks = []
        form_blocks = []
        
        # Create a map of block IDs to blocks
        block_map = {block['Id']: block for block in response.get('Blocks', [])}
        
        for block in response.get('Blocks', []):
            if block['BlockType'] == 'LINE':
                text_blocks.append({
                    'text': block.get('Text', ''),
                    'confidence': block.get('Confidence', 0),
                    'geometry': block.get('Geometry', {})
                })
            elif block['BlockType'] == 'TABLE':
                table_info = self._extract_enhanced_table(block, block_map)
                if table_info:
                    table_blocks.append(table_info)
            elif block['BlockType'] == 'KEY_VALUE_SET':
                form_info = self._extract_form_data(block, block_map)
                if form_info:
                    form_blocks.append(form_info)
        
        # Combine all content with enhanced formatting
        all_content = []
        
        if text_blocks:
            all_content.append("=== EXTRACTED TEXT ===")
            # Sort by reading order if possible
            text_blocks.sort(key=lambda x: x.get('geometry', {}).get('BoundingBox', {}).get('Top', 0))
            all_content.extend([block['text'] for block in text_blocks])
        
        if table_blocks:
            all_content.append("\\n=== EXTRACTED TABLES ===")
            all_content.extend(table_blocks)
        
        if form_blocks:
            all_content.append("\\n=== EXTRACTED FORM DATA ===")
            all_content.extend(form_blocks)
        
        return '\\n'.join(all_content)
    
    def _extract_enhanced_table(self, table_block: dict, block_map: dict) -> str:
        """Extract table with enhanced formatting for better AI processing"""
        try:
            cells = []
            relationships = table_block.get('Relationships', [])
            
            for relationship in relationships:
                if relationship['Type'] == 'CHILD':
                    for cell_id in relationship['Ids']:
                        if cell_id in block_map:
                            cell_block = block_map[cell_id]
                            if cell_block['BlockType'] == 'CELL':
                                cells.append(cell_block)
            
            if not cells:
                return ""
            
            # Organize cells by row and column
            table_data = {}
            max_row = 0
            max_col = 0
            
            for cell in cells:
                row_idx = cell.get('RowIndex', 1) - 1  # Convert to 0-based
                col_idx = cell.get('ColumnIndex', 1) - 1
                max_row = max(max_row, row_idx)
                max_col = max(max_col, col_idx)
                
                cell_text = self._extract_cell_text(cell, block_map)
                if row_idx not in table_data:
                    table_data[row_idx] = {}
                table_data[row_idx][col_idx] = cell_text or ""
            
            # Format as enhanced table
            table_lines = ["📊 TABLE DETECTED:"]
            
            for row_idx in range(max_row + 1):
                row_cells = []
                for col_idx in range(max_col + 1):
                    cell_value = table_data.get(row_idx, {}).get(col_idx, "")
                    row_cells.append(cell_value)
                
                if any(cell.strip() for cell in row_cells):  # Only add non-empty rows
                    if row_idx == 0:  # First row is likely headers
                        table_lines.append("HEADERS: " + " | ".join(row_cells))
                        table_lines.append("-" * 50)
                    else:
                        table_lines.append("DATA ROW: " + " | ".join(row_cells))
            
            return "\\n".join(table_lines)
            
        except Exception as e:
            logger.warning(f"Error extracting enhanced table: {str(e)}")
            return ""
    
    def _extract_form_data(self, form_block: dict, block_map: dict) -> str:
        """Extract form key-value pairs"""
        try:
            if form_block.get('EntityTypes') and 'KEY' in form_block.get('EntityTypes', []):
                # This is a key block
                key_text = self._extract_text_from_block(form_block, block_map)
                
                # Find corresponding value
                relationships = form_block.get('Relationships', [])
                for relationship in relationships:
                    if relationship['Type'] == 'VALUE':
                        for value_id in relationship['Ids']:
                            if value_id in block_map:
                                value_block = block_map[value_id]
                                value_text = self._extract_text_from_block(value_block, block_map)
                                return f"{key_text}: {value_text}"
            
            return ""
            
        except Exception as e:
            logger.warning(f"Error extracting form data: {str(e)}")
            return ""
    
    def _extract_text_from_block(self, block: dict, block_map: dict) -> str:
        """Extract text from any Textract block"""
        text_parts = []
        relationships = block.get('Relationships', [])
        
        for relationship in relationships:
            if relationship['Type'] == 'CHILD':
                for child_id in relationship['Ids']:
                    if child_id in block_map:
                        child_block = block_map[child_id]
                        if child_block['BlockType'] == 'WORD':
                            text_parts.append(child_block.get('Text', ''))
        
        return ' '.join(text_parts)
    
    def _extract_cell_text(self, cell_block: dict, block_map: dict) -> str:
        """Extract text from a table cell"""
        return self._extract_text_from_block(cell_block, block_map)
    
    def _process_with_enhanced_prompts(self, extracted_text: str, filename: str) -> StructuredExtractionResult:
        """Process extracted text with enhanced prompts for better booking detection"""
        
        # Add context about the document type for better processing
        enhanced_text = f"""
DOCUMENT PROCESSING CONTEXT:
- Source: {filename}
- Content extracted via AWS Textract OCR
- May contain tables, forms, or structured data
- Look for multiple bookings in table format

EXTRACTED CONTENT:
{extracted_text}

PROCESSING INSTRUCTION:
This content was extracted from a document that may contain structured booking information.
Pay special attention to:
1. Table data with multiple rows (each row may be a separate booking)
2. Form fields with booking information
3. Multiple passenger names, dates, or locations
4. Structured layouts typical of booking confirmations or requests
"""
        
        # Process with our unified email processor (which handles both structured and unstructured)
        result = self.email_processor.process_email(enhanced_text)
        
        return result
    
    def _fallback_text_extraction(self, file_content: bytes, filename: str, file_type: str = None) -> str:
        """Fallback text extraction when AWS Textract is not available"""
        logger.info(f"Using fallback text extraction for {filename}")
        
        if not file_type:
            file_type = self._detect_file_type(filename)
        
        file_type = file_type.lower()
        
        # For images, we can't do much without OCR
        if file_type in ['jpg', 'jpeg', 'png', 'gif']:
            return f"Image file: {filename} (OCR not available - AWS Textract required for image processing)"
        
        # For PDFs, try basic text extraction
        if file_type == 'pdf':
            try:
                import PyPDF2
                with tempfile.NamedTemporaryFile() as temp_file:
                    temp_file.write(file_content)
                    temp_file.flush()
                    
                    with open(temp_file.name, 'rb') as pdf_file:
                        pdf_reader = PyPDF2.PdfReader(pdf_file)
                        text_content = []
                        
                        for page in pdf_reader.pages:
                            text_content.append(page.extract_text())
                        
                        return '\\n'.join(text_content)
            except Exception as e:
                logger.warning(f"PDF extraction failed: {str(e)}")
        
        # For Word documents
        if file_type in ['docx']:
            try:
                from docx import Document
                with tempfile.NamedTemporaryFile() as temp_file:
                    temp_file.write(file_content)
                    temp_file.flush()
                    
                    doc = Document(temp_file.name)
                    paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]
                    
                    return '\\n'.join(paragraphs)
            except Exception as e:
                logger.warning(f"Word document extraction failed: {str(e)}")
        
        return f"Could not extract text from {filename} (file type: {file_type})"
    
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
            extraction_method="enhanced_processing_error",
            confidence_score=0.0,
            processing_notes=f"Enhanced processing error for {filename}: {error_message}"
        )
    
    # Multi-document processing methods
    def process_multiple_documents(self, documents: List[Tuple[bytes, str]]) -> List[StructuredExtractionResult]:
        """Process multiple documents"""
        results = []
        
        for file_content, filename in documents:
            result = self.process_document(file_content, filename)
            results.append(result)
        
        return results
    
    def combine_email_and_documents(
        self, 
        email_content: str, 
        documents: List[Tuple[bytes, str]] = None,
        sender_email: str = None
    ) -> StructuredExtractionResult:
        """Process email content along with attached documents"""
        logger.info("Processing email with document attachments")
        
        # Step 1: Process email content
        email_result = self.email_processor.process_email(email_content, sender_email)
        
        # Step 2: Process documents if provided
        document_results = []
        if documents:
            document_results = self.process_multiple_documents(documents)
        
        # Step 3: Combine results intelligently
        all_bookings = list(email_result.bookings)
        combined_notes = [email_result.processing_notes]
        
        # Add document information to email bookings
        for doc_result in document_results:
            combined_notes.append(doc_result.processing_notes)
            
            # Add document-specific bookings if they contain substantial data
            for doc_booking in doc_result.bookings:
                if doc_booking.passenger_name or doc_booking.from_location or doc_booking.start_date:
                    # This looks like a real booking from the document
                    all_bookings.append(doc_booking)
                elif doc_booking.additional_info and "OCR extracted:" in doc_booking.additional_info:
                    # Add OCR content to first email booking if it exists
                    if all_bookings and all_bookings[0]:
                        existing_info = all_bookings[0].additional_info or ""
                        doc_info = doc_booking.additional_info or ""
                        
                        if existing_info and doc_info:
                            all_bookings[0].additional_info = f"{existing_info}\\n\\n{doc_info}"
                        elif doc_info:
                            all_bookings[0].additional_info = doc_info
        
        # Create combined result
        combined_result = StructuredExtractionResult(
            bookings=all_bookings,
            total_bookings_found=len(all_bookings),
            extraction_method="email_plus_documents_enhanced",
            confidence_score=sum(r.confidence_score for r in [email_result] + document_results) / max(len(document_results) + 1, 1),
            processing_notes="\\n".join(combined_notes)
        )
        
        logger.info(f"Combined enhanced processing completed. Total bookings: {len(all_bookings)}")
        return combined_result
    
    def get_supported_file_types(self) -> List[str]:
        """Get list of supported file types"""
        return ['pdf', 'docx', 'doc', 'jpg', 'jpeg', 'png', 'gif']
    
    def validate_file(self, filename: str, file_size: int, max_size: int = 10 * 1024 * 1024) -> Tuple[bool, str]:
        """Validate uploaded file"""
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

# For backward compatibility, create an alias
DocumentProcessor = PracticalDocumentProcessor
