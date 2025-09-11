"""
Enhanced Document Processor with S3 Upload and LangChain Integration
Handles PDF, Word, and image documents using AWS Textract + LangChain + AI
"""

import os
import logging
import boto3
import json
import tempfile
import uuid
from typing import Dict, List, Optional, Any, Tuple, Union
from botocore.exceptions import ClientError, NoCredentialsError
from io import BytesIO

# Import LangChain components
try:
    from langchain_community.document_loaders import AmazonTextractPDFLoader
    from langchain_community.vectorstores import FAISS
    from langchain_openai import OpenAIEmbeddings
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain.chains.question_answering import load_qa_chain
    from langchain_openai import OpenAI
    LANGCHAIN_AVAILABLE = True
except ImportError as e:
    LANGCHAIN_AVAILABLE = False
    _LANGCHAIN_ERROR = str(e)

# Import our AI agents
from unified_email_processor import UnifiedEmailProcessor
from structured_email_agent import StructuredExtractionResult
from car_rental_ai_agent import BookingExtraction

logger = logging.getLogger(__name__)

class DocumentProcessorV2:
    """Enhanced document processor using S3 + Textract + LangChain + AI"""
    
    def __init__(self, 
                 aws_region: str = 'ap-south-1',
                 aws_access_key_id: str = None,
                 aws_secret_access_key: str = None,
                 s3_bucket: str = 'aws-textract-bucket3',
                 openai_api_key: str = None):
        """
        Initialize enhanced document processor
        
        Args:
            aws_region: AWS region for Textract
            aws_access_key_id: AWS access key
            aws_secret_access_key: AWS secret key
            s3_bucket: S3 bucket for file uploads
            openai_api_key: OpenAI API key for AI processing
        """
        self.aws_region = aws_region
        self.s3_bucket = s3_bucket
        self.openai_api_key = openai_api_key or os.getenv('OPENAI_API_KEY')
        self.email_processor = UnifiedEmailProcessor(openai_api_key)
        
        # Use provided AWS credentials or environment variables
        self.aws_access_key_id = aws_access_key_id or os.getenv('AWS_ACCESS_KEY_ID')
        self.aws_secret_access_key = aws_secret_access_key or os.getenv('AWS_SECRET_ACCESS_KEY')
        
        # Initialize AWS clients
        try:
            self.textract_client = boto3.client(
                'textract',
                region_name=aws_region,
                aws_access_key_id=self.aws_access_key_id,
                aws_secret_access_key=self.aws_secret_access_key
            )
            self.s3_client = boto3.client(
                's3',
                region_name=aws_region,
                aws_access_key_id=self.aws_access_key_id,
                aws_secret_access_key=self.aws_secret_access_key
            )
            self.aws_available = True
            logger.info(f"AWS Textract and S3 initialized for region: {aws_region}")
        except Exception as e:
            logger.error(f"AWS initialization failed: {str(e)}")
            self.aws_available = False
        
        # Initialize LangChain components
        self.langchain_available = LANGCHAIN_AVAILABLE and self.aws_available
        
        if self.langchain_available:
            try:
                self.embeddings = OpenAIEmbeddings(openai_api_key=self.openai_api_key)
                self.llm = OpenAI(openai_api_key=self.openai_api_key)
                self.qa_chain = load_qa_chain(self.llm, chain_type="stuff")
                logger.info("LangChain components initialized successfully")
            except Exception as e:
                logger.warning(f"LangChain initialization failed: {str(e)}")
                self.langchain_available = False
        else:
            if not LANGCHAIN_AVAILABLE:
                logger.warning(f"LangChain not available: {globals().get('_LANGCHAIN_ERROR', 'Unknown import error')}")

    def process_document(self, file_content: bytes, filename: str, file_type: str = None) -> StructuredExtractionResult:
        """
        Process a document using S3 + Textract + LangChain + AI approach
        
        Args:
            file_content: File content as bytes
            filename: Original filename
            file_type: File type hint
            
        Returns:
            StructuredExtractionResult with extracted bookings
        """
        logger.info(f"Processing document with enhanced pipeline: {filename}")
        
        if not self.langchain_available:
            return self._create_error_result("Enhanced processing not available - LangChain or AWS not configured", filename)
        
        try:
            # Step 1: Upload to S3
            s3_uri = self._upload_to_s3(file_content, filename)
            
            if not s3_uri:
                return self._create_error_result("Failed to upload document to S3", filename)
            
            # Step 2: Extract text using LangChain + Textract
            extracted_text = self._extract_with_langchain_textract(s3_uri)
            
            if not extracted_text:
                return self._create_error_result("Could not extract text from document", filename)
            
            logger.info(f"Extracted {len(extracted_text)} characters from {filename}")
            
            # Step 3: Use enhanced AI processing with LangChain
            result = self._process_with_langchain_ai(extracted_text, filename)
            
            # Step 4: Add metadata
            result.extraction_method = f"s3_textract_langchain_ai ({file_type or self._detect_file_type(filename)})"
            result.processing_notes = f"Enhanced S3+Textract+LangChain processing: {filename}. Text length: {len(extracted_text)} chars."
            
            # Step 5: Add extracted text to additional_info
            for booking in result.bookings:
                document_info = f"Document: {filename}\\nS3 URI: {s3_uri}\\nExtracted content: {extracted_text[:1000]}{'...' if len(extracted_text) > 1000 else ''}"
                
                if booking.additional_info:
                    booking.additional_info = f"{booking.additional_info}\\n\\n{document_info}"
                else:
                    booking.additional_info = document_info
            
            logger.info(f"Enhanced document processing completed: {filename}, found {len(result.bookings)} booking(s)")
            
            # Step 6: Cleanup S3 file (optional - comment out if you want to keep files)
            # self._cleanup_s3_file(s3_uri)
            
            return result
            
        except Exception as e:
            logger.error(f"Enhanced document processing failed for {filename}: {str(e)}")
            return self._create_error_result(str(e), filename)
    
    def _upload_to_s3(self, file_content: bytes, filename: str) -> Optional[str]:
        """Upload file to S3 for Textract processing"""
        try:
            # Generate unique key to avoid conflicts
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
    
    def _extract_with_langchain_textract(self, s3_uri: str) -> str:
        """Extract text using LangChain AmazonTextractPDFLoader"""
        try:
            loader = AmazonTextractPDFLoader(s3_uri, client=self.textract_client)
            documents = loader.load()
            
            # Combine all document content
            extracted_text = "\\n\\n".join([doc.page_content for doc in documents])
            
            logger.info(f"LangChain Textract extraction successful. Text length: {len(extracted_text)}")
            return extracted_text
            
        except Exception as e:
            logger.error(f"LangChain Textract extraction failed: {str(e)}")
            return ""
    
    def _process_with_langchain_ai(self, extracted_text: str, filename: str) -> StructuredExtractionResult:
        """Process extracted text using LangChain AI with enhanced prompting"""
        try:
            # Split text into chunks for better processing
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1024,
                chunk_overlap=100,
                length_function=len,
            )
            texts = text_splitter.split_text(extracted_text)
            
            # Create vector store
            docsearch = FAISS.from_texts(texts, self.embeddings)
            
            # Enhanced booking extraction query for documents
            booking_query = f"""
            Extract comprehensive car rental booking information from this document: {filename}

            This document may contain:
            - Reservation forms with structured fields
            - Table-based booking data
            - Travel requisition forms
            - Corporate booking requests
            
            Extract ALL the following information if available:
            
            COMPANY & BOOKING INFO:
            - Corporate/Company name
            - Booked by (person making booking) with phone and email
            - Billing entity name
            
            PASSENGER INFO:
            - Passenger/User name
            - Passenger phone number  
            - Passenger email address
            
            TRIP DETAILS:
            - Pick up city/location
            - Drop/destination location  
            - Reporting/pickup address (full address)
            - Drop address (if different)
            - Date of requirement/travel date
            - Reporting time/pickup time
            - Flight details (if airport pickup/drop)
            
            VEHICLE & SERVICE:
            - Car type/vehicle type requested
            - Type of duty (Drop/Pickup/Local/Outstation/Day trip)
            - Special instructions
            
            BILLING:
            - Payment mode (BTC/Credit Card/Company Card)
            - Billing instructions
            
            Look for multiple bookings if this document contains table data with multiple rows.
            Each row in a table typically represents a separate booking.
            
            Format your response with clear field labels and extracted values.
            If multiple bookings are found, clearly separate them.
            """
            
            # Search relevant chunks
            docs = docsearch.similarity_search(booking_query, k=8)
            
            # Use QA chain to extract booking info
            ai_result = self.qa_chain.run(input_documents=docs, question=booking_query)
            
            logger.info(f"LangChain AI analysis completed for {filename}")
            
            # Create enhanced text with AI analysis for our email processor
            enhanced_text = f"""
DOCUMENT ANALYSIS CONTEXT:
Source: {filename}
Processing Method: S3 + AWS Textract + LangChain + OpenAI
Document Type: Booking/Reservation Form or Table

ORIGINAL EXTRACTED CONTENT:
{extracted_text}

AI ANALYSIS RESULT:
{ai_result}

PROCESSING INSTRUCTION FOR FINAL EXTRACTION:
The above content was extracted from a booking document and analyzed by AI.
Extract structured booking information, looking for multiple bookings if present.
Use the AI analysis to guide extraction but also verify against the original content.
"""
            
            # Process with our unified email processor
            result = self.email_processor.process_email(enhanced_text)
            
            return result
            
        except Exception as e:
            logger.error(f"LangChain AI processing failed: {str(e)}")
            # Fallback to direct email processor
            enhanced_text = f"DOCUMENT: {filename}\\n\\n{extracted_text}"
            return self.email_processor.process_email(enhanced_text)
    
    def _cleanup_s3_file(self, s3_uri: str):
        """Clean up temporary S3 file"""
        try:
            # Parse S3 URI to get bucket and key
            s3_parts = s3_uri.replace('s3://', '').split('/', 1)
            if len(s3_parts) == 2:
                bucket, key = s3_parts
                self.s3_client.delete_object(Bucket=bucket, Key=key)
                logger.info(f"Cleaned up S3 file: {s3_uri}")
        except Exception as e:
            logger.warning(f"Failed to cleanup S3 file {s3_uri}: {str(e)}")
    
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
            extraction_method="s3_textract_langchain_error",
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

# For backward compatibility
DocumentProcessor = DocumentProcessorV2
