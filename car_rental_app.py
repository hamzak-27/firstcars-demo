#!/usr/bin/env python3
"""
Car Rental Multi-Agent System - Streamlit App
Interactive testing interface for the complete booking extraction and validation system
"""

import streamlit as st
import pandas as pd
import json
import time
import os
import logging
from typing import Dict, List, Any, Optional
import tempfile
from io import BytesIO

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import our agents
try:
    from complete_multi_agent_orchestrator import CompleteMultiAgentOrchestrator
    from gemma_classification_agent import GemmaClassificationAgent, BookingType, DutyType
    from single_booking_extraction_agent import SingleBookingExtractionAgent
    from multiple_booking_extraction_agent import MultipleBookingExtractionAgent
    from business_logic_validation_agent import BusinessLogicValidationAgent
    from extraction_router import ExtractionRouter
except ImportError as e:
    st.error(f"Failed to import required modules: {e}")
    st.stop()

# Page configuration
st.set_page_config(
    page_title="Car Rental Multi-Agent System", 
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #FF6B6B, #4ECDC4);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .agent-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #007bff;
        margin: 1rem 0;
    }
    
    .success-card {
        background: #d4edda;
        border-color: #28a745;
        color: #155724;
    }
    
    .error-card {
        background: #f8d7da;
        border-color: #dc3545;
        color: #721c24;
    }
    
    .warning-card {
        background: #fff3cd;
        border-color: #ffc107;
        color: #856404;
    }
    
    .metric-container {
        display: flex;
        justify-content: space-around;
        margin: 1rem 0;
    }
    
    .stExpander > div:first-child > div {
        background-color: #e9ecef;
    }
</style>
""", unsafe_allow_html=True)

def initialize_session_state():
    """Initialize session state variables"""
    if 'processing_results' not in st.session_state:
        st.session_state.processing_results = None
    if 'orchestrator' not in st.session_state:
        st.session_state.orchestrator = None
    if 'api_key_configured' not in st.session_state:
        st.session_state.api_key_configured = False

def setup_api_key():
    """Setup and validate API key"""
    st.sidebar.markdown("### 🔑 API Configuration")
    
    # API key input methods
    api_method = st.sidebar.radio(
        "Choose API key method:",
        ["Enter manually", "Use environment variable", "Use test mode (fallback only)"]
    )
    
    api_key = None
    
    if api_method == "Enter manually":
        api_key = st.sidebar.text_input(
            "Enter your Gemini API Key:",
            type="password",
            help="Get your API key from https://makersuite.google.com/app/apikey"
        )
        if api_key:
            os.environ['GEMINI_API_KEY'] = api_key
            st.sidebar.success("✅ API key configured!")
            st.session_state.api_key_configured = True
        else:
            st.sidebar.warning("⚠️ Please enter your API key")
            
    elif api_method == "Use environment variable":
        api_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_AI_API_KEY')
        if api_key:
            st.sidebar.success("✅ Found API key in environment")
            st.session_state.api_key_configured = True
        else:
            st.sidebar.error("❌ No API key found in environment variables")
            st.sidebar.info("Set GEMINI_API_KEY or GOOGLE_AI_API_KEY environment variable")
    
    else:  # Test mode
        api_key = "test-key"
        os.environ['GEMINI_API_KEY'] = api_key
        st.sidebar.info("🧪 Test mode: Will use fallback extraction only")
        st.session_state.api_key_configured = True
    
    return api_key

def initialize_orchestrator(api_key: str):
    """Initialize the multi-agent orchestrator"""
    try:
        if api_key and api_key != "test-key":
            st.info(f"🤖 Initializing AI agents with Gemini API: {api_key[:20]}...{api_key[-4:]}")
        else:
            st.warning("⚠️ Initializing in test mode - limited functionality")
            
        orchestrator = CompleteMultiAgentOrchestrator(
            api_key=api_key
        )
        st.session_state.orchestrator = orchestrator
        
        # Test the API connection
        if api_key and api_key != "test-key":
            st.success("✅ AI agents initialized successfully with Gemini API!")
        
        return orchestrator
    except Exception as e:
        st.error(f"Failed to initialize orchestrator: {e}")
        return None

def display_main_header():
    """Display the main application header"""
    st.markdown("""
    <div class="main-header">
        <h1>🚗 Car Rental Multi-Agent System</h1>
        <p>AI-powered booking extraction, classification, and validation</p>
    </div>
    """, unsafe_allow_html=True)

def display_system_status(orchestrator):
    """Display system status and agent information"""
    st.markdown("### 🔧 System Status")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Classification Agent",
            "Ready ✅" if orchestrator.classification_agent else "Error ❌"
        )
    
    with col2:
        st.metric(
            "Extraction Router", 
            "Ready ✅" if orchestrator.extraction_router else "Error ❌"
        )
    
    with col3:
        st.metric(
            "Validation Agent",
            "Ready ✅" if orchestrator.validation_agent else "Error ❌"
        )
    
    with col4:
        api_status = "Connected ✅" if st.session_state.api_key_configured else "Not configured ⚠️"
        st.metric("API Status", api_status)

def process_text_input(orchestrator, content: str, sender_email: str = None):
    """Process text input through the multi-agent system"""
    
    st.info("🚀 Starting multi-agent AI processing pipeline...")
    with st.spinner("🔄 Processing with AI agents..."):
        start_time = time.time()
        
        try:
            # Process through orchestrator
            st.info("🤖 Running through Classification → Extraction → Validation pipeline")
            result = orchestrator.process_content(
                content=content,
                source_type="text_input"
            )
            
            # Show processing success
            if result.get('success'):
                st.success(f"✅ AI processing completed! Found {result.get('booking_count', 0)} booking(s)")
            else:
                st.error(f"❌ AI processing failed: {result.get('error_message', 'Unknown error')}")
            
            processing_time = time.time() - start_time
            
            # Store results
            st.session_state.processing_results = {
                'result': result,
                'processing_time': processing_time,
                'input_type': 'text',
                'input_length': len(content)
            }
            
            return True
            
        except Exception as e:
            st.error(f"Processing failed: {e}")
            logger.error(f"Processing error: {e}")
            return False

def process_file_upload(orchestrator, uploaded_file, sender_email: str = None):
    """Process uploaded file through the multi-agent system"""
    
    with st.spinner(f"🔄 Processing file: {uploaded_file.name}..."):
        start_time = time.time()
        
        try:
            # Read file content
            file_content = uploaded_file.read()
            
            # Process through document processors based on file type
            file_type = uploaded_file.name.split('.')[-1].lower() if '.' in uploaded_file.name else 'unknown'
            
            # Try to use document processors for OCR/text extraction
            content = None
            processing_method = "unknown"
            
            try:
                if file_type == 'txt':
                    content = file_content.decode('utf-8')
                    processing_method = "text_file"
                elif file_type in ['pdf', 'docx', 'doc']:
                    # Try document processing
                    try:
                        from practical_document_processor import PracticalDocumentProcessor
                        doc_processor = PracticalDocumentProcessor()
                        doc_result = doc_processor.process_document(file_content, uploaded_file.name, file_type)
                        if doc_result.bookings and doc_result.bookings[0].additional_info:
                            # Extract OCR text from additional_info
                            additional_info = doc_result.bookings[0].additional_info
                            if "OCR extracted:" in additional_info:
                                content = additional_info.split("OCR extracted:")[-1].strip()
                                processing_method = "textract_ocr"
                            else:
                                content = additional_info
                                processing_method = "document_extraction"
                        else:
                            content = f"Document processed but no readable content found: {uploaded_file.name}"
                            processing_method = "document_fallback"
                    except ImportError:
                        content = f"Document processing not available for {uploaded_file.name}"
                        processing_method = "no_document_processor"
                elif file_type in ['jpg', 'jpeg', 'png', 'gif']:
                    # Use EnhancedMultiBookingProcessor for table images (handles your exact formats)
                    st.info(f"🔄 Processing image with Multi-Booking Table Processor...")
                    try:
                        from enhanced_multi_booking_processor import EnhancedMultiBookingProcessor
                        # Initialize with Gemini API key from orchestrator
                        api_key = getattr(orchestrator, 'api_key', None)
                        multi_processor = EnhancedMultiBookingProcessor(gemini_api_key=api_key)
                        
                        # Process with the multi-booking table processor
                        # Save file temporarily for processing
                        import tempfile
                        import os
                        
                        with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{file_type}') as tmp_file:
                            tmp_file.write(file_content)
                            temp_path = tmp_file.name
                        
                        try:
                            # Process the image using the correct method
                            bookings = multi_processor.process_document(temp_path)
                            
                            # Create result object similar to what orchestrator expects
                            class TableResult:
                                def __init__(self, bookings, method):
                                    self.bookings = []
                                    self.extraction_method = method
                                    self.processing_notes = f"Processed {len(bookings)} bookings"
                                    
                                    # Convert dict bookings to booking objects
                                    for booking_dict in bookings:
                                        booking_obj = type('Booking', (), booking_dict)
                                        # Map common fields
                                        booking_obj.passenger_name = booking_dict.get('Passenger Name', '')
                                        booking_obj.passenger_phone = booking_dict.get('Phone', '')
                                        booking_obj.corporate = booking_dict.get('Corporate', '')
                                        booking_obj.start_date = booking_dict.get('Date', '')
                                        booking_obj.reporting_time = booking_dict.get('Time', '')
                                        booking_obj.vehicle_group = booking_dict.get('Vehicle', '')
                                        booking_obj.from_location = booking_dict.get('From', '')
                                        booking_obj.to_location = booking_dict.get('To', '')
                                        booking_obj.reporting_address = booking_dict.get('Pickup', '')
                                        booking_obj.drop_address = booking_dict.get('Drop', '')
                                        booking_obj.flight_train_number = booking_dict.get('Flight', '')
                                        booking_obj.remarks = booking_dict.get('Remarks', '')
                                        self.bookings.append(booking_obj)
                            
                            table_result = TableResult(bookings, "Enhanced Multi-Booking Textract")
                        finally:
                            # Clean up temporary file
                            if os.path.exists(temp_path):
                                os.unlink(temp_path)
                        
                        st.success(f"✅ Table processing completed: {table_result.extraction_method}")
                        
                        if table_result.bookings:
                            st.info(f"📊 Found {len(table_result.bookings)} booking(s) in table - Using AI for further processing")
                            # Convert the structured bookings back to text for the multi-agent pipeline
                            booking_summaries = []
                            for i, booking in enumerate(table_result.bookings, 1):
                                summary = f"Booking {i}:\n"
                                summary += f"- Passenger: {booking.passenger_name or 'N/A'} ({booking.passenger_phone or 'N/A'})\n"
                                summary += f"- Company: {booking.corporate or 'N/A'}\n"
                                summary += f"- Date: {booking.start_date or 'N/A'}\n"
                                summary += f"- Time: {booking.reporting_time or 'N/A'}\n"
                                summary += f"- Vehicle: {booking.vehicle_group or 'N/A'}\n"
                                summary += f"- From: {booking.from_location or booking.reporting_address or 'N/A'}\n"
                                summary += f"- To: {booking.to_location or booking.drop_address or 'N/A'}\n"
                                summary += f"- Flight: {booking.flight_train_number or 'N/A'}\n"
                                if booking.remarks:
                                    summary += f"- Remarks: {booking.remarks}\n"
                                booking_summaries.append(summary)
                            
                            content = f"TABLE EXTRACTION RESULTS ({len(table_result.bookings)} bookings found):\n\n" + "\n".join(booking_summaries)
                            content += f"\n\nOriginal processing method: {table_result.extraction_method}"
                            processing_method = "enhanced_multi_booking_textract"
                        else:
                            st.warning(f"⚠️ No bookings found in table - This might be a single booking form")
                            content = f"Table processed but no bookings found: {uploaded_file.name}\nProcessing notes: {table_result.processing_notes or 'None'}"
                            processing_method = "table_no_bookings"
                    except ImportError:
                        # Fallback to enhanced form processor
                        st.info(f"🔄 Falling back to Enhanced Form Processor for single booking...")
                        try:
                            from enhanced_form_processor import EnhancedFormProcessor
                            form_processor = EnhancedFormProcessor()
                            form_result = form_processor.process_document(file_content, uploaded_file.name, file_type)
                            
                            st.success(f"✅ Form processing completed: {form_result.extraction_method}")
                            if form_result.bookings and form_result.bookings[0].additional_info:
                                st.info(f"📝 Found single booking - Using AI for further processing")
                                content = form_result.bookings[0].additional_info
                                processing_method = "enhanced_form_textract"
                            else:
                                content = f"Image processed but no readable content found: {uploaded_file.name}"
                                processing_method = "image_fallback"
                        except ImportError:
                            content = f"Table processing not available for image: {uploaded_file.name}\nNote: Install AWS Textract dependencies for table processing"
                            processing_method = "no_table_processing"
                else:
                    content = f"Unsupported file type: {uploaded_file.name} ({file_type})"
                    processing_method = "unsupported"
                    
            except Exception as ocr_error:
                content = f"Error processing file {uploaded_file.name}: {str(ocr_error)}"
                processing_method = "processing_error"
            
            if not content:
                content = f"Could not extract content from {uploaded_file.name}"
                processing_method = "extraction_failed"
            
            # Add processing info to content for the user
            content_with_info = f"[File: {uploaded_file.name}, Method: {processing_method}]\n\n{content}"
            
            # Process through orchestrator
            result = orchestrator.process_content(
                content=content_with_info,
                source_type=f"file_upload_{file_type}"
            )
            
            processing_time = time.time() - start_time
            
            # Store results
            st.session_state.processing_results = {
                'result': result,
                'processing_time': processing_time,
                'input_type': 'file',
                'filename': uploaded_file.name,
                'file_size': len(file_content)
            }
            
            return True
            
        except Exception as e:
            st.error(f"File processing failed: {e}")
            logger.error(f"File processing error: {e}")
            return False

def display_results():
    """Display processing results"""
    
    if not st.session_state.processing_results:
        return
    
    results = st.session_state.processing_results
    result = results['result']
    
    st.markdown("## 📊 Processing Results")
    
    # Overall metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Success", "✅ Yes" if result['success'] else "❌ No")
    
    with col2:
        st.metric("Bookings Found", result['booking_count'])
    
    with col3:
        st.metric("Processing Time", f"{result['total_processing_time']:.2f}s")
    
    with col4:
        st.metric("Total Cost", f"₹{result['total_cost_inr']:.4f}")
    
    # Pipeline Stages Results
    if result.get('pipeline_stages'):
        with st.expander("🔍 Pipeline Stages", expanded=True):
            stages = result['pipeline_stages']
            
            for stage_name, stage_info in stages.items():
                st.write(f"### {stage_name.title()} Stage")
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Agent:** {stage_info.get('agent', 'Unknown')}")
                    if 'booking_type' in stage_info:
                        st.write(f"**Booking Type:** {stage_info['booking_type']}")
                    if 'booking_count' in stage_info:
                        st.write(f"**Booking Count:** {stage_info['booking_count']}")
                    if 'confidence' in stage_info:
                        st.write(f"**Confidence:** {stage_info['confidence']:.1%}")
                
                with col2:
                    st.write(f"**Processing Time:** {stage_info.get('processing_time', 0):.2f}s")
                    st.write(f"**Cost:** ₹{stage_info.get('cost_inr', 0):.4f}")
                    if 'duty_type' in stage_info:
                        st.write(f"**Duty Type:** {stage_info['duty_type']}")
                    if 'extraction_method' in stage_info:
                        st.write(f"**Method:** {stage_info['extraction_method']}")
                
                st.write("---")
    
    # Final DataFrame
    if result.get('final_dataframe') is not None and not result['final_dataframe'].empty:
        with st.expander("📋 Final Booking Data", expanded=True):
            st.dataframe(result['final_dataframe'], use_container_width=True)
            
            # Download options
            col1, col2, col3 = st.columns(3)
            
            with col1:
                csv_data = result['final_dataframe'].to_csv(index=False)
                st.download_button(
                    "📥 Download CSV",
                    csv_data,
                    file_name=f"bookings_{int(time.time())}.csv",
                    mime="text/csv"
                )
            
            with col2:
                json_data = result['final_dataframe'].to_json(orient='records', indent=2)
                st.download_button(
                    "📥 Download JSON",
                    json_data,
                    file_name=f"bookings_{int(time.time())}.json",
                    mime="application/json"
                )
            
            with col3:
                excel_buffer = BytesIO()
                result['final_dataframe'].to_excel(excel_buffer, index=False)
                excel_data = excel_buffer.getvalue()
                st.download_button(
                    "📥 Download Excel",
                    excel_data,
                    file_name=f"bookings_{int(time.time())}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
    
    # Metadata and Error Information
    if result.get('error_message'):
        st.error(f"❌ **Error:** {result['error_message']}")
    
    if result.get('metadata'):
        with st.expander("📊 System Metadata"):
            metadata = result['metadata']
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Source Type:** {metadata.get('source_type', 'Unknown')}")
                st.write(f"**Content Length:** {metadata.get('content_length', 0)} chars")
                st.write(f"**Pipeline Version:** {metadata.get('pipeline_version', 'Unknown')}")
            
            with col2:
                st.write(f"**Pipeline Success:** {metadata.get('pipeline_success', False)}")
                st.write(f"**Total Agents Used:** {metadata.get('total_agents_used', 0)}")
                if metadata.get('agents_used'):
                    st.write(f"**Agents:** {', '.join(metadata['agents_used'])}")

def display_sample_inputs():
    """Display sample inputs for testing"""
    
    with st.expander("📝 Sample Test Inputs"):
        
        tab1, tab2, tab3 = st.tabs(["Single Booking", "Multiple Bookings", "Table Format"])
        
        with tab1:
            sample_single = """
Dear Team,

Please arrange a cab for Mr. Rajesh Kumar (9876543210) tomorrow.

Details:
- Date: 25th December 2024
- Time: 10:30 AM
- From: Andheri Office, Mumbai
- To: Mumbai International Airport
- Vehicle: Innova Crysta preferred
- Corporate: Accenture India Ltd
- Purpose: Airport drop service

Thanks,
Travel Coordinator
            """
            st.code(sample_single, language="text")
            if st.button("Use Single Booking Sample", key="sample_single"):
                st.session_state.sample_text = sample_single
        
        with tab2:
            sample_multiple = """
Multiple car bookings required:

Booking 1:
- Passenger: John Smith (9876543210)
- Date: 25th December 2024
- Time: 9:00 AM
- From: Delhi Office
- To: Gurgaon
- Vehicle: Dzire

Booking 2:
- Passenger: Mary Wilson (9876543211)  
- Date: 26th December 2024
- Time: 10:00 AM
- From: Mumbai Office
- To: Mumbai Airport
- Vehicle: Innova

Corporate: TechCorp India
            """
            st.code(sample_multiple, language="text")
            if st.button("Use Multiple Booking Sample", key="sample_multiple"):
                st.session_state.sample_text = sample_multiple
        
        with tab3:
            sample_table = """
Employee Name: John Smith
Contact Number: 9876543210
Date of Travel: 25-12-2024
Pick-up Time: 09:00 AM
City: Mumbai
Cab Type: Innova Crysta
Pick-up Address: Andheri Office, Mumbai
Drop At: Mumbai Airport Terminal 2
Flight Details: AI-131 (10:45 AM)
Company Name: TechCorp India
            """
            st.code(sample_table, language="text")
            if st.button("Use Table Format Sample", key="sample_table"):
                st.session_state.sample_text = sample_table

def main():
    """Main application"""
    
    # Set AWS credentials first
    aws_credentials = {
        'AWS_DEFAULT_REGION': 'ap-south-1',
        'AWS_ACCESS_KEY_ID': 'AKIAYLZZKLOTYIXDAARY', 
        'AWS_SECRET_ACCESS_KEY': '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',
        'S3_BUCKET_NAME': 'aws-textract-bucket3'
    }
    
    for key, value in aws_credentials.items():
        os.environ[key] = value
    
    # Initialize session state
    initialize_session_state()
    
    # Display main header
    display_main_header()
    
    # Setup API key
    api_key = setup_api_key()
    
    if not st.session_state.api_key_configured:
        st.warning("⚠️ Please configure your API key in the sidebar to continue")
        st.markdown("""
        ### How to get your Gemini API Key:
        1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
        2. Sign in with your Google account
        3. Click "Create API Key"
        4. Copy the key and paste it in the sidebar
        """)
        return
    
    # Initialize orchestrator
    if not st.session_state.orchestrator:
        orchestrator = initialize_orchestrator(api_key)
        if not orchestrator:
            return
    else:
        orchestrator = st.session_state.orchestrator
    
    # Display system status
    display_system_status(orchestrator)
    
    # Display document processing capabilities
    with st.expander("📄 Document Processing Status"):
        doc_processors = []
        
        # Check for document processors
        try:
            from practical_document_processor import PracticalDocumentProcessor
            doc_processors.append("✅ Textract Document Processor (PDF, DOCX)")
        except ImportError:
            doc_processors.append("❌ Textract Document Processor not available")
        
        try:
            from enhanced_form_processor import EnhancedFormProcessor
            doc_processors.append("✅ Enhanced Form Processor (Images, Tables)")
        except ImportError:
            doc_processors.append("❌ Enhanced Form Processor not available")
        
        try:
            from simple_document_processor import SimpleDocumentProcessor  
            doc_processors.append("✅ Simple Document Processor (Fallback OCR)")
        except ImportError:
            doc_processors.append("❌ Simple Document Processor not available")
        
        try:
            from enhanced_multi_booking_processor import EnhancedMultiBookingProcessor
            doc_processors.append("✅ Enhanced Multi-Booking Processor (Table Images - Your Formats)")
        except ImportError:
            doc_processors.append("❌ Enhanced Multi-Booking Processor not available")
        
        for processor in doc_processors:
            st.write(processor)
    
    # Main interface
    st.markdown("## 📝 Input Methods")
    
    input_method = st.radio(
        "Choose input method:",
        ["Text Input", "File Upload"],
        horizontal=True
    )
    
    # Sender email (optional)
    sender_email = st.text_input(
        "Sender Email (optional):",
        placeholder="sender@company.com",
        help="Email of the person who made the booking request"
    )
    
    # Text input method
    if input_method == "Text Input":
        st.markdown("### 📄 Text Input")
        
        # Check for sample text from session state
        initial_text = getattr(st.session_state, 'sample_text', '')
        
        text_content = st.text_area(
            "Enter booking request text:",
            value=initial_text,
            height=300,
            placeholder="Paste your booking email or text here..."
        )
        
        # Clear sample text after using it
        if initial_text:
            st.session_state.sample_text = ''
        
        if st.button("🚀 Process Text", type="primary", use_container_width=True):
            if text_content.strip():
                success = process_text_input(orchestrator, text_content, sender_email)
                if success:
                    st.success("✅ Processing completed!")
                    st.rerun()
            else:
                st.error("Please enter some text to process")
    
    # File upload method
    else:
        st.markdown("### 📎 File Upload")
        
        st.info("🔄 **File Processing Pipeline:** OCR Extraction → AI Classification → AI Extraction → AI Validation")
        
        with st.expander("📝 What happens to different file types", expanded=False):
            st.markdown("""
            **📊 Table Images (JPG/PNG):**
            1. 🔄 Multi-Booking Table Processor (for complex tables)
            2. 🔄 Enhanced Form Processor (fallback for single bookings) 
            3. 🤖 Gemini AI processes extracted text through full pipeline
            
            **📄 Documents (PDF/DOCX):**
            1. 🔄 Document processors with AWS Textract OCR
            2. 🤖 Gemini AI processes extracted text through full pipeline
            
            **📝 Text Files (TXT):**
            1. 🤖 Direct Gemini AI processing through full pipeline
            """)
        
        uploaded_file = st.file_uploader(
            "Choose a file",
            type=['txt', 'pdf', 'docx', 'doc', 'jpg', 'jpeg', 'png', 'gif'],
            help="Supported formats: TXT, PDF, Word documents, Images (JPG, PNG, GIF) - Uses AWS Textract for OCR when available"
        )
        
        if uploaded_file and st.button("🚀 Process File", type="primary", use_container_width=True):
            success = process_file_upload(orchestrator, uploaded_file, sender_email)
            if success:
                st.success("✅ File processing completed!")
                st.rerun()
    
    # Display sample inputs
    display_sample_inputs()
    
    # Display results if available
    if st.session_state.processing_results:
        display_results()
    
    # Clear results button
    if st.session_state.processing_results:
        if st.button("🗑️ Clear Results"):
            st.session_state.processing_results = None
            st.rerun()

if __name__ == "__main__":
    main()