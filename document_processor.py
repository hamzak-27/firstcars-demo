"""
Document and Image Processor
Handles PDF, Word documents, and images using AWS Textract OCR + AI extraction
"""

import os
import logging
import boto3
import json
from typing import Dict, List, Optional, Any, Tuple, Union
from botocore.exceptions import ClientError, NoCredentialsError
from io import BytesIO
import tempfile

# Import our AI agents
from unified_email_processor import UnifiedEmailProcessor
from structured_email_agent import StructuredExtractionResult

logger = logging.getLogger(__name__)

class DocumentProcessor:
    """Processes documents and images using AWS Textract + AI extraction"""
    
    def __init__(self, aws_region: str = 'us-east-1', openai_api_key: str = None):
        """
        Initialize document processor
        
        Args:
            aws_region: AWS region for Textract
            openai_api_key: OpenAI API key for AI processing
        """
        self.aws_region = aws_region
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
        Process a document (PDF, Word, image) and extract booking information
        
        Args:
            file_content: File content as bytes
            filename: Original filename
            file_type: File type hint (pdf, docx, image, etc.)
            
        Returns:
            StructuredExtractionResult with extracted bookings
        """
        logger.info(f"Processing document: {filename}")
        
        try:
            # Step 1: Extract text using AWS Textract
            extracted_text = self._extract_text_from_document(file_content, filename, file_type)
            
            if not extracted_text:
                return self._create_error_result("Could not extract text from document", filename)
            
            # Step 2: Use AI to extract booking information from text
            result = self.email_processor.process_email(extracted_text)
            
            # Step 3: Add document processing metadata
            result.extraction_method = f"document_textract_ai ({file_type or 'unknown'})"
            result.processing_notes = f"Processed document: {filename}. Original text length: {len(extracted_text)} characters."
            
            # Step 4: Add extracted text to additional_info for all bookings
            for booking in result.bookings:
                additional_info = booking.additional_info or ""
                document_info = f"Document: {filename}\nExtracted content: {extracted_text[:500]}{'...' if len(extracted_text) > 500 else ''}"
                
                if additional_info:
                    booking.additional_info = f"{additional_info}\n\n{document_info}"
                else:
                    booking.additional_info = document_info
            
            logger.info(f"Document processing completed: {filename}")
            return result
            
        except Exception as e:
            logger.error(f"Document processing failed for {filename}: {str(e)}")
            return self._create_error_result(str(e), filename)
    
    def _extract_text_from_document(self, file_content: bytes, filename: str, file_type: str = None) -> str:
        """Extract text from document using AWS Textract"""
        
        if not self.textract_available:
            return self._fallback_text_extraction(file_content, filename, file_type)
        
        try:
            # Detect file type if not provided
            if not file_type:
                file_type = self._detect_file_type(filename)
            
            file_type = file_type.lower()
            
            # Use appropriate Textract method based on file type
            if file_type in ['jpg', 'jpeg', 'png', 'gif']:
                # For images, use detect_document_text for simple OCR
                response = self._textract_detect_text(file_content)
            elif file_type in ['pdf', 'docx', 'doc']:
                # For documents, use analyze_document for better structure detection
                response = self._textract_analyze_document(file_content)
            else:
                logger.warning(f"Unsupported file type: {file_type}, trying basic OCR")
                response = self._textract_detect_text(file_content)
            
            # Extract text from Textract response
            extracted_text = self._parse_textract_response(response)
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
            FeatureTypes=['TABLES', 'FORMS']
        )
    
    def _parse_textract_response(self, response: dict) -> str:
        """Parse Textract response and extract text content"""
        text_blocks = []
        table_blocks = []
        
        for block in response.get('Blocks', []):
            if block['BlockType'] == 'LINE':
                text_blocks.append(block.get('Text', ''))
            elif block['BlockType'] == 'TABLE':
                # For tables, we'll extract them separately
                table_info = self._extract_table_from_block(block, response.get('Blocks', []))
                if table_info:
                    table_blocks.append(table_info)
        
        # Combine text and tables
        all_content = []
        
        if text_blocks:
            all_content.append("EXTRACTED TEXT:")
            all_content.extend(text_blocks)
        
        if table_blocks:
            all_content.append("\nEXTRACTED TABLES:")
            all_content.extend(table_blocks)
        
        return '\n'.join(all_content)
    
    def _extract_table_from_block(self, table_block: dict, all_blocks: List[dict]) -> str:
        """Extract table content from Textract table block"""
        try:
            # Create a map of block IDs to blocks
            block_map = {block['Id']: block for block in all_blocks}
            
            # Find cells in this table
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
            
            # Organize cells into table format
            table_text = ["TABLE:"]
            cells.sort(key=lambda x: (x.get('RowIndex', 0), x.get('ColumnIndex', 0)))
            
            current_row = -1
            row_text = []
            
            for cell in cells:
                row_index = cell.get('RowIndex', 0)
                
                if row_index != current_row:
                    if row_text:
                        table_text.append(" | ".join(row_text))
                    row_text = []
                    current_row = row_index
                
                # Extract text from cell
                cell_text = self._extract_cell_text(cell, block_map)
                row_text.append(cell_text or "")
            
            # Add last row
            if row_text:
                table_text.append(" | ".join(row_text))
            
            return "\n".join(table_text)
            
        except Exception as e:
            logger.warning(f"Error extracting table: {str(e)}")
            return ""
    
    def _extract_cell_text(self, cell_block: dict, block_map: dict) -> str:
        """Extract text from a table cell"""
        text_parts = []
        relationships = cell_block.get('Relationships', [])
        
        for relationship in relationships:
            if relationship['Type'] == 'CHILD':
                for child_id in relationship['Ids']:
                    if child_id in block_map:
                        child_block = block_map[child_id]
                        if child_block['BlockType'] == 'WORD':
                            text_parts.append(child_block.get('Text', ''))
        
        return ' '.join(text_parts)
    
    def _fallback_text_extraction(self, file_content: bytes, filename: str, file_type: str = None) -> str:
        """Fallback text extraction when AWS Textract is not available"""
        logger.info(f"Using fallback text extraction for {filename}")
        
        if not file_type:
            file_type = self._detect_file_type(filename)
        
        file_type = file_type.lower()
        
        # For images, we can't do much without OCR
        if file_type in ['jpg', 'jpeg', 'png', 'gif']:
            return f"Image file: {filename} (OCR not available - AWS Textract required)"
        
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
                        
                        return '\n'.join(text_content)
            except Exception as e:
                logger.warning(f"PDF extraction failed: {str(e)}")
        
        # For Word documents
        if file_type in ['docx', 'doc']:
            try:
                from docx import Document
                with tempfile.NamedTemporaryFile() as temp_file:
                    temp_file.write(file_content)
                    temp_file.flush()
                    
                    doc = Document(temp_file.name)
                    paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]
                    
                    return '\n'.join(paragraphs)
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
            extraction_method="document_processing_error",
            confidence_score=0.0,
            processing_notes=f"Error processing {filename}: {error_message}"
        )
    
    def process_multiple_documents(self, documents: List[Tuple[bytes, str]]) -> List[StructuredExtractionResult]:
        """
        Process multiple documents
        
        Args:
            documents: List of (file_content, filename) tuples
            
        Returns:
            List of StructuredExtractionResult objects
        """
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
        """
        Process email content along with attached documents
        
        Args:
            email_content: Email text content
            documents: List of (file_content, filename) tuples
            sender_email: Sender email address
            
        Returns:
            Combined StructuredExtractionResult
        """
        logger.info("Processing email with document attachments")
        
        # Step 1: Process email content
        email_result = self.email_processor.process_email(email_content, sender_email)
        
        # Step 2: Process documents if provided
        document_results = []
        if documents:
            document_results = self.process_multiple_documents(documents)
        
        # Step 3: Combine results
        all_bookings = list(email_result.bookings)
        combined_notes = [email_result.processing_notes]
        
        # Add document information to email bookings
        for doc_result in document_results:
            combined_notes.append(doc_result.processing_notes)
            
            # Add document-specific bookings if found
            for doc_booking in doc_result.bookings:
                if doc_booking.passenger_name:  # Only add if it seems to contain real data
                    all_bookings.append(doc_booking)
                else:
                    # Add document info to first email booking's additional_info
                    if all_bookings:
                        existing_info = all_bookings[0].additional_info or ""
                        doc_info = doc_booking.additional_info or ""
                        
                        if existing_info and doc_info:
                            all_bookings[0].additional_info = f"{existing_info}\n\n{doc_info}"
                        elif doc_info:
                            all_bookings[0].additional_info = doc_info
        
        # Create combined result
        combined_result = StructuredExtractionResult(
            bookings=all_bookings,
            total_bookings_found=len(all_bookings),
            extraction_method="email_plus_documents",
            confidence_score=(email_result.confidence_score + 
                            sum(dr.confidence_score for dr in document_results) / max(len(document_results), 1)) / 2,
            processing_notes="\n".join(combined_notes)
        )
        
        logger.info(f"Combined processing completed. Total bookings: {len(all_bookings)}")
        return combined_result
    
    def get_supported_file_types(self) -> List[str]:
        """Get list of supported file types"""
        return ['pdf', 'docx', 'doc', 'jpg', 'jpeg', 'png', 'gif']
    
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
