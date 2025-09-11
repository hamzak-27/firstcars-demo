"""
Simple Document Processor using your exact S3 + Textract + AI approach
"""

import os
import logging
import boto3
import uuid
from typing import Dict, List, Optional, Any, Tuple, Union
from botocore.exceptions import ClientError, NoCredentialsError

# Import our AI agents
from unified_email_processor import UnifiedEmailProcessor
from structured_email_agent import StructuredExtractionResult
from car_rental_ai_agent import BookingExtraction

logger = logging.getLogger(__name__)

class SimpleDocumentProcessor:
    """Simple document processor using your S3 + Textract + AI approach"""
    
    def __init__(self, 
                 aws_region: str = 'ap-south-1',
                 aws_access_key_id: str = None,
                 aws_secret_access_key: str = None,
                 s3_bucket: str = 'aws-textract-bucket3',
                 openai_api_key: str = None):
        """
        Initialize simple document processor with your exact setup
        """
        self.aws_region = aws_region
        self.s3_bucket = s3_bucket
        # Use provided AWS credentials or environment variables
        self.aws_access_key_id = aws_access_key_id or os.getenv('AWS_ACCESS_KEY_ID')
        self.aws_secret_access_key = aws_secret_access_key or os.getenv('AWS_SECRET_ACCESS_KEY')
        self.openai_api_key = openai_api_key or os.getenv('OPENAI_API_KEY')
        self.email_processor = UnifiedEmailProcessor(openai_api_key)
        
        # Initialize AWS clients with credentials from environment or parameters
        try:
            self.textract_client = boto3.client(
                'textract',
                region_name=self.aws_region,
                aws_access_key_id=self.aws_access_key_id,
                aws_secret_access_key=self.aws_secret_access_key
            )
            self.s3_client = boto3.client(
                's3',
                region_name=self.aws_region,
                aws_access_key_id=self.aws_access_key_id,
                aws_secret_access_key=self.aws_secret_access_key
            )
            self.aws_available = True
            logger.info(f"AWS Textract and S3 initialized for region: {aws_region}")
        except Exception as e:
            logger.error(f"AWS initialization failed: {str(e)}")
            self.aws_available = False

    def process_document(self, file_content: bytes, filename: str, file_type: str = None) -> StructuredExtractionResult:
        """
        Process a document using your S3 + Textract + AI approach
        """
        logger.info(f"Processing document: {filename}")
        
        if not self.aws_available:
            return self._create_error_result("AWS not available", filename)
        
        try:
            # Step 1: Upload to S3
            s3_uri = self._upload_to_s3(file_content, filename)
            
            if not s3_uri:
                return self._create_error_result("Failed to upload to S3", filename)
            
            # Step 2: Extract text using your approach
            extracted_text = self._extract_text_from_s3(s3_uri)
            
            if not extracted_text:
                return self._create_error_result("Could not extract text", filename)
            
            logger.info(f"Extracted {len(extracted_text)} characters from {filename}")
            
            # Step 3: Process with AI using your approach
            result = self._process_with_ai(extracted_text, filename)
            
            # Step 4: Add metadata
            result.extraction_method = f"s3_textract_ai ({file_type or self._detect_file_type(filename)})"
            result.processing_notes = f"S3+Textract+AI processing: {filename}. Text length: {len(extracted_text)} chars."
            
            # Step 5: Add extracted content to additional_info
            for booking in result.bookings:
                document_info = f"Document: {filename}\\nS3 URI: {s3_uri}\\nExtracted: {extracted_text[:800]}{'...' if len(extracted_text) > 800 else ''}"
                
                if booking.additional_info:
                    booking.additional_info = f"{booking.additional_info}\\n\\n{document_info}"
                else:
                    booking.additional_info = document_info
            
            logger.info(f"Document processing completed: {filename}, found {len(result.bookings)} booking(s)")
            return result
            
        except Exception as e:
            logger.error(f"Document processing failed for {filename}: {str(e)}")
            return self._create_error_result(str(e), filename)
    
    def _upload_to_s3(self, file_content: bytes, filename: str) -> Optional[str]:
        """Upload file to S3 using your exact method"""
        try:
            # Generate unique key
            unique_id = str(uuid.uuid4())[:8]
            key = f"temp/{unique_id}_{filename}"
            
            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.s3_bucket,
                Key=key,
                Body=file_content
            )
            
            s3_uri = f"s3://{self.s3_bucket}/{key}"
            logger.info(f"Uploaded to S3: {s3_uri}")
            return s3_uri
            
        except Exception as e:
            logger.error(f"S3 upload failed: {str(e)}")
            return None
    
    def _extract_text_from_s3(self, s3_uri: str) -> str:
        """Extract text from S3 document using direct Textract calls (your approach)"""
        try:
            # Parse S3 URI
            s3_parts = s3_uri.replace('s3://', '').split('/', 1)
            bucket, key = s3_parts
            
            # Call Textract directly
            response = self.textract_client.detect_document_text(
                Document={
                    'S3Object': {
                        'Bucket': bucket,
                        'Name': key
                    }
                }
            )
            
            # Extract text from response
            extracted_text = []
            for block in response.get('Blocks', []):
                if block['BlockType'] == 'LINE':
                    extracted_text.append(block.get('Text', ''))
            
            full_text = '\\n'.join(extracted_text)
            logger.info(f"Textract extraction successful. Text length: {len(full_text)}")
            return full_text
            
        except Exception as e:
            logger.error(f"Textract extraction failed: {str(e)}")
            return ""
    
    def _process_with_ai(self, extracted_text: str, filename: str) -> StructuredExtractionResult:
        """Process extracted text with AI using your approach"""
        
        # Create enhanced context exactly like your approach
        document_context = f"""
DOCUMENT ANALYSIS CONTEXT:
Source: {filename}
Processing Method: AWS Textract OCR + AI Processing  
Document Type: Booking/Reservation Form or Table

EXTRACTED CONTENT FROM TEXTRACT:
{extracted_text}

PROCESSING INSTRUCTION:
This content was extracted from a booking document using AWS Textract.
Extract structured booking information from this document data.
Look for multiple bookings if this is a table with multiple rows.
Map the document fields to standard booking fields.
Handle different document formats: reservation forms, travel requisitions, booking tables.
"""
        
        # Process with our unified email processor
        result = self.email_processor.process_email(document_context)
        return result
    
    def _detect_file_type(self, filename: str) -> str:
        """Detect file type from filename"""
        if not filename:
            return 'unknown'
        
        extension = filename.split('.')[-1].lower() if '.' in filename else 'unknown'
        return extension
    
    def _create_error_result(self, error_message: str, filename: str = "") -> StructuredExtractionResult:
        """Create error result for failed processing"""
        error_booking = BookingExtraction(
            remarks=f"Document processing failed: {error_message}",
            additional_info=f"Failed to process: {filename}",
            confidence_score=0.0
        )
        
        return StructuredExtractionResult(
            bookings=[error_booking],
            total_bookings_found=0,
            extraction_method="s3_textract_error",
            confidence_score=0.0,
            processing_notes=f"Processing error for {filename}: {error_message}"
        )
    
    def process_multiple_documents(self, documents: List[Tuple[bytes, str]]) -> List[StructuredExtractionResult]:
        """Process multiple documents"""
        results = []
        for file_content, filename in documents:
            result = self.process_document(file_content, filename)
            results.append(result)
        return results
    
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
