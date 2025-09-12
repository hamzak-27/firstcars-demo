"""
Flight Document Processor using S3 + Textract + Flight AI Agent
Specifically designed for extracting flight details from screenshots and PDFs
"""

import os
import logging
import boto3
import uuid
from typing import Dict, List, Optional, Any, Tuple, Union
from botocore.exceptions import ClientError, NoCredentialsError

# Import our flight AI agent
from flight_details_agent import FlightDetailsAIAgent, FlightExtractionResult, FlightExtraction

logger = logging.getLogger(__name__)

class FlightDocumentProcessor:
    """Flight document processor using S3 + Textract + Flight AI approach"""
    
    def __init__(self, 
                 aws_region: str = 'ap-south-1',
                 aws_access_key_id: str = None,
                 aws_secret_access_key: str = None,
                 s3_bucket: str = 'aws-textract-bucket3',
                 openai_api_key: str = None):
        """
        Initialize flight document processor with AWS and OpenAI configuration
        """
        self.aws_region = aws_region
        self.s3_bucket = s3_bucket
        # Use provided AWS credentials or environment variables
        self.aws_access_key_id = aws_access_key_id or os.getenv('AWS_ACCESS_KEY_ID')
        self.aws_secret_access_key = aws_secret_access_key or os.getenv('AWS_SECRET_ACCESS_KEY')
        self.openai_api_key = openai_api_key or os.getenv('OPENAI_API_KEY')
        
        # Initialize Flight AI agent
        self.flight_agent = FlightDetailsAIAgent(self.openai_api_key)
        
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
            logger.info(f"AWS Textract and S3 initialized for flight processing in region: {aws_region}")
        except Exception as e:
            logger.error(f"AWS initialization failed for flight processor: {str(e)}")
            self.aws_available = False

    def process_flight_document(self, file_content: bytes, filename: str, file_type: str = None) -> FlightExtractionResult:
        """
        Process a flight document using S3 + Textract + Flight AI approach
        
        Args:
            file_content: Raw file bytes
            filename: Original filename
            file_type: File type (optional)
            
        Returns:
            FlightExtractionResult with extracted flight data
        """
        logger.info(f"Processing flight document: {filename}")
        
        if not self.aws_available:
            return self._create_error_result("AWS not available for flight processing", filename)
        
        try:
            # Step 1: Upload to S3
            s3_uri = self._upload_to_s3(file_content, filename)
            
            if not s3_uri:
                return self._create_error_result("Failed to upload flight document to S3", filename)
            
            # Step 2: Extract text using Textract
            extracted_text = self._extract_text_from_s3(s3_uri)
            
            if not extracted_text:
                return self._create_error_result("Could not extract text from flight document", filename)
            
            logger.info(f"Extracted {len(extracted_text)} characters from flight document {filename}")
            
            # Step 3: Process with Flight AI agent
            result = self._process_with_flight_ai(extracted_text, filename, s3_uri)
            
            # Step 4: Add metadata
            result.extraction_method = f"s3_textract_flight_ai ({file_type or self._detect_file_type(filename)})"
            result.processing_notes = f"Flight S3+Textract+AI processing: {filename}. Text length: {len(extracted_text)} chars."
            
            # Step 5: Add extracted content to additional_info for each flight
            for flight in result.flights:
                document_info = f"Flight Document: {filename}\\nS3 URI: {s3_uri}\\nExtracted: {extracted_text[:800]}{'...' if len(extracted_text) > 800 else ''}"
                
                if flight.additional_info:
                    flight.additional_info = f"{flight.additional_info}\\n\\n{document_info}"
                else:
                    flight.additional_info = document_info
            
            logger.info(f"Flight document processing completed: {filename}, found {len(result.flights)} flight(s)")
            return result
            
        except Exception as e:
            logger.error(f"Flight document processing failed for {filename}: {str(e)}")
            return self._create_error_result(str(e), filename)
    
    def _upload_to_s3(self, file_content: bytes, filename: str) -> Optional[str]:
        """Upload flight document to S3"""
        try:
            # Generate unique key with flight prefix
            unique_id = str(uuid.uuid4())[:8]
            key = f"flights/{unique_id}_{filename}"
            
            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.s3_bucket,
                Key=key,
                Body=file_content
            )
            
            s3_uri = f"s3://{self.s3_bucket}/{key}"
            logger.info(f"Flight document uploaded to S3: {s3_uri}")
            return s3_uri
            
        except Exception as e:
            logger.error(f"S3 upload failed for flight document: {str(e)}")
            return None
    
    def _extract_text_from_s3(self, s3_uri: str) -> str:
        """Extract text from S3 flight document using Textract"""
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
            logger.info(f"Textract extraction successful for flight document. Text length: {len(full_text)}")
            return full_text
            
        except Exception as e:
            logger.error(f"Textract extraction failed for flight document: {str(e)}")
            return ""
    
    def _process_with_flight_ai(self, extracted_text: str, filename: str, s3_uri: str) -> FlightExtractionResult:
        """Process extracted text with Flight AI agent"""
        
        # Create enhanced context for flight documents
        flight_document_context = f"""
FLIGHT DOCUMENT ANALYSIS CONTEXT:
Source: {filename} (Flight Document - Screenshot/PDF)
Processing Method: AWS Textract OCR + Flight AI Processing  
Document Type: Flight Ticket, Boarding Pass, Flight Itinerary, or Flight Confirmation
S3 Location: {s3_uri}

EXTRACTED CONTENT FROM TEXTRACT:
{extracted_text}

PROCESSING INSTRUCTION:
This content was extracted from a flight-related document using AWS Textract OCR.
The document contains flight information such as:
- Flight numbers and airline details
- Departure and arrival airports with times
- Passenger information and booking references
- Gate, terminal, and seat information
- Flight status and additional travel details

Extract ALL flight information from this document.
Handle multiple flights if this is a multi-leg journey or round-trip itinerary.
Normalize airport codes to standard IATA format.
Convert times to 24-hour format and dates to YYYY-MM-DD format.
"""
        
        # Process with Flight AI agent
        result = self.flight_agent.extract_flight_details(flight_document_context)
        return result
    
    def _detect_file_type(self, filename: str) -> str:
        """Detect file type from filename"""
        if not filename:
            return 'unknown'
        
        extension = filename.split('.')[-1].lower() if '.' in filename else 'unknown'
        return extension
    
    def _create_error_result(self, error_message: str, filename: str = "") -> FlightExtractionResult:
        """Create error result for failed flight processing"""
        error_flight = FlightExtraction(
            remarks=f"Flight processing failed: {error_message}",
            additional_info=f"Failed to process flight document: {filename}",
            confidence_score=0.0
        )
        
        return FlightExtractionResult(
            flights=[error_flight],
            total_flights_found=0,
            extraction_method="flight_s3_textract_error",
            confidence_score=0.0,
            processing_notes=f"Flight processing error for {filename}: {error_message}"
        )
    
    def process_multiple_flight_documents(self, documents: List[Tuple[bytes, str]]) -> List[FlightExtractionResult]:
        """Process multiple flight documents"""
        results = []
        for file_content, filename in documents:
            result = self.process_flight_document(file_content, filename)
            results.append(result)
        return results
    
    def get_supported_file_types(self) -> List[str]:
        """Get list of supported file types for flight documents"""
        return ['pdf', 'jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff']
    
    def validate_file(self, filename: str, file_size: int, max_size: int = 10 * 1024 * 1024) -> Tuple[bool, str]:
        """Validate uploaded flight document"""
        if not filename:
            return False, "No filename provided"
        
        # Check file extension
        file_type = self._detect_file_type(filename)
        if file_type not in self.get_supported_file_types():
            return False, f"Unsupported file type: {file_type}. Supported: {', '.join(self.get_supported_file_types())}"
        
        # Check file size
        if file_size > max_size:
            return False, f"File too large: {file_size / (1024*1024):.1f}MB (max: {max_size / (1024*1024):.1f}MB)"
        
        return True, "Flight document is valid"

# Test function
def test_flight_processor():
    """Test the flight document processor"""
    try:
        processor = FlightDocumentProcessor()
        
        if not processor.aws_available:
            print("AWS not available for testing")
            return
        
        # This would require an actual flight document file
        print("Flight Document Processor initialized successfully")
        print(f"Supported file types: {processor.get_supported_file_types()}")
        
    except Exception as e:
        print(f"Flight processor test failed: {str(e)}")

if __name__ == "__main__":
    test_flight_processor()
