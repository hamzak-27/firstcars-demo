#!/usr/bin/env python3
"""
Enhanced Car Rental Multi-Agent System with Debug Logging
"""

import streamlit as st
import pandas as pd
import json
import time
import os
import logging
import tempfile
from typing import Dict, List, Any, Optional
from io import BytesIO

# Enhanced logging configuration
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create a custom Streamlit log handler
class StreamlitLogHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.logs = []
    
    def emit(self, record):
        log_entry = self.format(record)
        self.logs.append(log_entry)
        if len(self.logs) > 100:  # Keep last 100 logs
            self.logs = self.logs[-100:]

# Create streamlit log handler
st_log_handler = StreamlitLogHandler()
st_log_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(st_log_handler)

# Import our agents with error handling
try:
    from complete_multi_agent_orchestrator import CompleteMultiAgentOrchestrator
    from enhanced_multi_booking_processor import EnhancedMultiBookingProcessor
    logger.info("✅ All required modules imported successfully")
except ImportError as e:
    st.error(f"Failed to import required modules: {e}")
    logger.error(f"Import error: {e}")
    st.stop()

# Page configuration
st.set_page_config(
    page_title="Car Rental Multi-Agent System (Debug)", 
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded"
)

def initialize_session_state():
    """Initialize session state variables"""
    if 'processing_results' not in st.session_state:
        st.session_state.processing_results = None
    if 'orchestrator' not in st.session_state:
        st.session_state.orchestrator = None
    if 'api_key_configured' not in st.session_state:
        st.session_state.api_key_configured = False
    if 'debug_logs' not in st.session_state:
        st.session_state.debug_logs = []

def setup_api_key():
    """Setup and validate API key"""
    st.sidebar.markdown("### 🔑 API Configuration")
    
    api_method = st.sidebar.radio(
        "Choose API key method:",
        ["Use test mode (fallback only)", "Enter manually", "Use environment variable"]
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
    
    else:  # Test mode
        api_key = "test-key"
        os.environ['GEMINI_API_KEY'] = api_key
        st.sidebar.info("🧪 Test mode: Will use fallback extraction only")
        st.session_state.api_key_configured = True
    
    return api_key

def initialize_orchestrator(api_key: str):
    """Initialize the multi-agent orchestrator"""
    try:
        orchestrator = CompleteMultiAgentOrchestrator(api_key=api_key)
        st.session_state.orchestrator = orchestrator
        logger.info("✅ Orchestrator initialized successfully")
        return orchestrator
    except Exception as e:
        st.error(f"Failed to initialize orchestrator: {e}")
        logger.error(f"Orchestrator initialization failed: {e}")
        return None

def process_image_with_debug(uploaded_file):
    """Process image with detailed debugging"""
    
    logger.info(f"🖼️ Starting image processing for: {uploaded_file.name}")
    
    try:
        # Read file content
        file_content = uploaded_file.read()
        file_type = uploaded_file.name.split('.')[-1].lower() if '.' in uploaded_file.name else 'unknown'
        
        logger.info(f"File size: {len(file_content)} bytes")
        logger.info(f"File type: {file_type}")
        
        # Step 1: Process with EnhancedMultiBookingProcessor
        st.write("### 🔍 Step 1: OCR and Table Processing")
        
        processor = EnhancedMultiBookingProcessor()
        
        with st.spinner("Processing image with AWS Textract..."):
            table_result = processor.process_multi_booking_document(file_content, uploaded_file.name, file_type)
        
        logger.info(f"Table processing result: {table_result}")
        logger.info(f"Bookings found: {len(table_result.bookings) if table_result.bookings else 0}")
        logger.info(f"Processing method: {table_result.extraction_method}")
        logger.info(f"Processing notes: {table_result.processing_notes}")
        
        # Display OCR results
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**OCR Processing Results:**")
            st.write(f"- Extraction Method: {table_result.extraction_method}")
            st.write(f"- Bookings Found: {len(table_result.bookings) if table_result.bookings else 0}")
            st.write(f"- Processing Notes: {table_result.processing_notes or 'None'}")
        
        with col2:
            if table_result.bookings:
                st.write("**Detected Bookings:**")
                for i, booking in enumerate(table_result.bookings, 1):
                    with st.expander(f"Booking {i}", expanded=True):
                        st.write(f"**Passenger:** {booking.passenger_name or 'N/A'}")
                        st.write(f"**Phone:** {booking.passenger_phone or 'N/A'}")
                        st.write(f"**Date:** {booking.start_date or 'N/A'}")
                        st.write(f"**Time:** {booking.reporting_time or 'N/A'}")
                        st.write(f"**From:** {booking.from_location or booking.reporting_address or 'N/A'}")
                        st.write(f"**To:** {booking.to_location or booking.drop_address or 'N/A'}")
                        st.write(f"**Vehicle:** {booking.vehicle_group or 'N/A'}")
                        st.write(f"**Corporate:** {booking.corporate or 'N/A'}")
            else:
                st.warning("No bookings detected in OCR processing")
        
        # Step 2: Convert to text format for multi-agent processing
        st.write("### 🤖 Step 2: Multi-Agent Processing")
        
        if table_result.bookings:
            booking_summaries = []
            for i, booking in enumerate(table_result.bookings, 1):
                summary = f"Booking {i}:\\n"
                summary += f"- Passenger: {booking.passenger_name or 'N/A'} ({booking.passenger_phone or 'N/A'})\\n"
                summary += f"- Company: {booking.corporate or 'N/A'}\\n"
                summary += f"- Date: {booking.start_date or 'N/A'}\\n"
                summary += f"- Time: {booking.reporting_time or 'N/A'}\\n"
                summary += f"- Vehicle: {booking.vehicle_group or 'N/A'}\\n"
                summary += f"- From: {booking.from_location or booking.reporting_address or 'N/A'}\\n"
                summary += f"- To: {booking.to_location or booking.drop_address or 'N/A'}\\n"
                summary += f"- Flight: {booking.flight_train_number or 'N/A'}\\n"
                if booking.remarks:
                    summary += f"- Remarks: {booking.remarks}\\n"
                booking_summaries.append(summary)
            
            content = f"TABLE EXTRACTION RESULTS ({len(table_result.bookings)} bookings found):\\n\\n" + "\\n".join(booking_summaries)
            content += f"\\n\\nOriginal processing method: {table_result.extraction_method}"
        else:
            content = f"Table processed but no bookings found. Processing notes: {table_result.processing_notes or 'None'}"
        
        # Show the text being sent to multi-agent system
        with st.expander("📝 Text Content Sent to Multi-Agent System", expanded=False):
            st.code(content, language="text")
        
        logger.info(f"Text content length: {len(content)} characters")
        logger.info(f"Content preview: {content[:500]}...")
        
        # Step 3: Process through orchestrator
        with st.spinner("Processing through multi-agent system..."):
            orchestrator = st.session_state.orchestrator
            content_with_info = f"[File: {uploaded_file.name}, Method: enhanced_multi_booking_textract]\\n\\n{content}"
            
            result = orchestrator.process_content(
                content=content_with_info,
                source_type=f"file_upload_{file_type}"
            )
        
        logger.info(f"Orchestrator result: {result}")
        logger.info(f"Final booking count: {result.get('booking_count', 0)}")
        
        # Display final results
        st.write("### 📊 Final Results")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("OCR Bookings Found", len(table_result.bookings) if table_result.bookings else 0)
        with col2:
            st.metric("Final Processed Bookings", result.get('booking_count', 0))
        with col3:
            success = result.get('success', False)
            st.metric("Processing Success", "✅ Yes" if success else "❌ No")
        
        if result.get('final_dataframe') is not None and not result['final_dataframe'].empty:
            st.write("**Final Booking Data:**")
            st.dataframe(result['final_dataframe'], use_container_width=True)
        else:
            st.warning("⚠️ No final booking data produced by multi-agent system")
            
            # Debug information
            with st.expander("🔧 Debug Information", expanded=True):
                st.write("**Pipeline Stages:**")
                if result.get('pipeline_stages'):
                    for stage, info in result['pipeline_stages'].items():
                        st.write(f"- **{stage}**: {info.get('status', 'Unknown')}")
                        if 'error' in info:
                            st.error(f"  Error: {info['error']}")
                
                st.write("**Error Messages:**")
                if result.get('error_message'):
                    st.error(result['error_message'])
                else:
                    st.info("No error messages recorded")
        
        # Store results
        st.session_state.processing_results = {
            'result': result,
            'processing_time': 0,
            'input_type': 'file',
            'filename': uploaded_file.name,
            'file_size': len(file_content),
            'ocr_result': table_result
        }
        
        return True
        
    except Exception as e:
        st.error(f"❌ Processing failed: {str(e)}")
        logger.error(f"Processing error: {e}", exc_info=True)
        return False

def main():
    """Main application function"""
    
    initialize_session_state()
    
    st.title("🔧 Car Rental Multi-Agent System (Debug Mode)")
    st.markdown("Enhanced version with detailed logging for debugging image processing issues")
    
    # Setup API key
    api_key = setup_api_key()
    
    if not st.session_state.api_key_configured:
        st.warning("⚠️ Please configure your API key in the sidebar to continue")
        return
    
    # Initialize orchestrator
    if not st.session_state.orchestrator:
        orchestrator = initialize_orchestrator(api_key)
        if not orchestrator:
            return
    
    # Status display
    st.write("### 🚀 System Status")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Orchestrator", "✅ Ready")
    with col2:
        try:
            from enhanced_multi_booking_processor import EnhancedMultiBookingProcessor
            st.metric("OCR Processor", "✅ Ready")
        except:
            st.metric("OCR Processor", "❌ Error")
    with col3:
        st.metric("AWS Textract", "✅ Ready" if os.getenv('AWS_ACCESS_KEY_ID') or os.path.exists(os.path.expanduser('~/.aws/credentials')) else "⚠️ Check Config")
    
    # File upload
    st.write("### 📎 Upload Table Image")
    
    uploaded_file = st.file_uploader(
        "Choose an image file with booking table",
        type=['jpg', 'jpeg', 'png', 'gif'],
        help="Upload an image containing a table with booking information"
    )
    
    if uploaded_file:
        # Display image preview
        st.write("**Image Preview:**")
        st.image(uploaded_file, caption=f"Uploaded: {uploaded_file.name}", use_column_width=True)
        
        if st.button("🚀 Process Image", type="primary", use_container_width=True):
            success = process_image_with_debug(uploaded_file)
            if success:
                st.success("✅ Processing completed!")
    
    # Display logs
    if st.checkbox("Show Debug Logs"):
        st.write("### 📝 Debug Logs")
        if st_log_handler.logs:
            logs_text = "\\n".join(st_log_handler.logs[-50:])  # Show last 50 logs
            st.text_area("Recent Logs", logs_text, height=300)
        else:
            st.info("No logs available")
    
    # Clear logs button
    if st.button("🗑️ Clear Logs"):
        st_log_handler.logs = []
        st.success("Logs cleared!")

if __name__ == "__main__":
    main()