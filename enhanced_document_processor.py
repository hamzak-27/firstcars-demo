"""
Enhanced Document and Image Processor
Uses LangChain with AWS Textract for better OCR + AI extraction of booking information
"""

import os
import logging
import boto3
import json
import tempfile
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
    # Don't log during import, save for later
    _IMPORT_ERROR = str(e)
except Exception as e:
    LANGCHAIN_AVAILABLE = False
    _IMPORT_ERROR = str(e)

# Import our AI agents
from unified_email_processor import UnifiedEmailProcessor
from structured_email_agent import StructuredExtractionResult

logger = logging.getLogger(__name__)

class EnhancedDocumentProcessor:
    """Enhanced document processor using LangChain + Textract for better OCR"""
    
    def __init__(self, aws_region: str = 'us-east-1', openai_api_key: str = None):
        """
        Initialize enhanced document processor
        
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
            self.s3_client = boto3.client('s3', region_name=aws_region)
            self.textract_available = True
            logger.info(f"AWS Textract initialized for region: {aws_region}")
        except (NoCredentialsError, ClientError) as e:
            logger.warning(f"AWS Textract not available: {str(e)}")
            self.textract_available = False
        
        # Initialize LangChain components if available
        self.langchain_available = LANGCHAIN_AVAILABLE and self.textract_available
        
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
            if 'LANGCHAIN_AVAILABLE' in globals() and not LANGCHAIN_AVAILABLE:
                logger.warning(f"LangChain components not available: {globals().get('_IMPORT_ERROR', 'Unknown error')}")

    def process_document(self, file_content: bytes, filename: str, file_type: str = None) -> StructuredExtractionResult:
        """
        Process a document using enhanced LangChain + Textract approach
        
        Args:
            file_content: File content as bytes
            filename: Original filename
            file_type: File type hint
            
        Returns:
            StructuredExtractionResult with extracted bookings
        """
        logger.info(f"Enhanced processing document: {filename}")
        
        if not self.langchain_available:
            logger.warning("Enhanced processing not available, falling back to basic mode")
            return self._fallback_processing(file_content, filename, file_type)
        
        try:
            # Step 1: Upload to temporary S3 bucket for Textract processing
            s3_uri = self._upload_to_s3(file_content, filename)
            
            if not s3_uri:
                return self._fallback_processing(file_content, filename, file_type)
            
            # Step 2: Use LangChain TextractPDFLoader for robust text extraction
            extracted_text = self._extract_with_langchain(s3_uri)
            
            if not extracted_text:
                return self._create_error_result("Could not extract text from document", filename)
            
            # Step 3: Use enhanced AI processing with vector search
            result = self._process_with_enhanced_ai(extracted_text, filename)
            
            # Step 4: Add metadata
            result.extraction_method = f"enhanced_langchain_textract ({file_type or 'unknown'})"
            result.processing_notes = f"Enhanced processing: {filename}. Text length: {len(extracted_text)} chars."
            
            # Step 5: Add extracted text to additional_info
            for booking in result.bookings:
                document_info = f"Document: {filename}\\nEnhanced OCR content: {extracted_text[:1000]}{'...' if len(extracted_text) > 1000 else ''}"
                
                if booking.additional_info:
                    booking.additional_info = f"{booking.additional_info}\\n\\n{document_info}"
                else:
                    booking.additional_info = document_info
            
            logger.info(f"Enhanced document processing completed: {filename}")
            return result
            
        except Exception as e:
            logger.error(f"Enhanced document processing failed for {filename}: {str(e)}")
            return self._fallback_processing(file_content, filename, file_type)
    
    def _upload_to_s3(self, file_content: bytes, filename: str) -> Optional[str]:
        """Upload file to S3 for Textract processing"""
        try:
            # Use a temporary S3 bucket or create one
            bucket_name = os.getenv('TEXTRACT_S3_BUCKET', 'firstcars-textract-temp')
            key = f"temp/{filename}"
            
            # Try to upload to S3
            self.s3_client.put_object(
                Bucket=bucket_name,
                Key=key,
                Body=file_content
            )
            
            s3_uri = f"s3://{bucket_name}/{key}"
            logger.info(f"Uploaded to S3: {s3_uri}")
            return s3_uri
            
        except Exception as e:
            logger.warning(f"S3 upload failed: {str(e)}")
            return None
    
    def _extract_with_langchain(self, s3_uri: str) -> str:
        """Extract text using LangChain TextractPDFLoader"""
        try:
            loader = AmazonTextractPDFLoader(s3_uri, client=self.textract_client)
            documents = loader.load()
            
            # Combine all document content
            extracted_text = "\\n\\n".join([doc.page_content for doc in documents])
            
            logger.info(f"LangChain extraction successful. Text length: {len(extracted_text)}")
            return extracted_text
            
        except Exception as e:
            logger.error(f"LangChain text extraction failed: {str(e)}")
            return ""
    
    def _process_with_enhanced_ai(self, text: str, filename: str) -> StructuredExtractionResult:
        """Process extracted text using enhanced AI with vector search"""
        try:
            # Split text into chunks for better processing
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1024,
                chunk_overlap=100,
                length_function=len,
            )
            texts = text_splitter.split_text(text)
            
            # Create vector store
            docsearch = FAISS.from_texts(texts, self.embeddings)
            
            # Enhanced booking extraction query
            booking_query = """
            Extract all car rental booking information from this document. Look for:
            - Passenger names and contact details
            - Booking dates and times
            - Pickup and drop locations
            - Vehicle types
            - Corporate information
            - Any structured booking data or tables
            
            Extract multiple bookings if present. Format the response as detailed booking information.
            """
            
            # Search relevant chunks
            docs = docsearch.similarity_search(booking_query, k=5)
            
            # Use QA chain to extract booking info
            ai_result = self.qa_chain.run(input_documents=docs, question=booking_query)
            
            # Now process the AI result with our email processor
            result = self.email_processor.process_email(f"{text}\\n\\nAI Analysis: {ai_result}")
            
            logger.info(f"Enhanced AI processing completed for {filename}")
            return result
            
        except Exception as e:
            logger.error(f"Enhanced AI processing failed: {str(e)}")
            # Fallback to regular email processing
            return self.email_processor.process_email(text)
    
    def _fallback_processing(self, file_content: bytes, filename: str, file_type: str = None) -> StructuredExtractionResult:
        """Fallback to basic processing when enhanced features are not available"""
        logger.info(f"Using fallback processing for {filename}")
        
        try:
            # Basic text extraction
            if not file_type:
                file_type = self._detect_file_type(filename)
            
            file_type = file_type.lower()
            
            # For PDFs, try PyPDF2
            if file_type == 'pdf':
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
            extraction_method="enhanced_processing_error",
            confidence_score=0.0,
            processing_notes=f"Enhanced processing error for {filename}: {error_message}"
        )
    
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

# For backward compatibility, create an alias
DocumentProcessor = EnhancedDocumentProcessor
