#!/usr/bin/env python3
"""
FirstCars Demo Tool - Streamlit Frontend
A user-friendly interface for Car Rental Email Processing with Multiple Booking Detection
"""

import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta
import json
import logging
from typing import List, Tuple, Optional

# Configure logging
logger = logging.getLogger(__name__)

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    st.error("python-dotenv not installed. Install with: pip install python-dotenv")

# Import our processors
from unified_email_processor import UnifiedEmailProcessor
from structured_email_agent import StructuredExtractionResult
from car_rental_ai_agent import BookingExtraction
from google_sheets_integration import sheets_manager

# Import simple document processor (using your exact approach)
try:
    from simple_document_processor import SimpleDocumentProcessor
    DOCUMENT_PROCESSOR_AVAILABLE = True
except ImportError as e:
    DOCUMENT_PROCESSOR_AVAILABLE = False
    DOCUMENT_PROCESSOR_ERROR = str(e)

# Google Sheets configuration
GOOGLE_SHEETS_URL = "https://docs.google.com/spreadsheets/d/1zz1xkvI0-XCkU23eBfSW9jSLK--UfCU94iT-poEkf_E/edit#gid=0"

def test_google_sheets_connection():
    """Test Google Sheets connection and show status"""
    success, message = sheets_manager.test_connection()
    return success, message

def create_multiple_bookings_if_needed(booking):
    """Create multiple booking entries if the request spans multiple dates or is a date range"""
    if not booking.start_date:
        return [booking]  # Return single booking if start date is missing
    
    try:
        start_date = datetime.strptime(booking.start_date, '%Y-%m-%d')
        
        # If no end date, treat as single booking
        if not booking.end_date:
            return [booking]
        
        end_date = datetime.strptime(booking.end_date, '%Y-%m-%d')
        
        # If same date, return single booking
        if start_date == end_date:
            return [booking]
        
        # Create multiple bookings for each date
        bookings = []
        current_date = start_date
        day_counter = 1
        
        while current_date <= end_date:
            # Create a copy of the original booking for each date
            new_booking = BookingExtraction(
                corporate=booking.corporate,
                booked_by_name=booking.booked_by_name,
                booked_by_phone=booking.booked_by_phone,
                booked_by_email=booking.booked_by_email,
                passenger_name=booking.passenger_name,
                passenger_phone=booking.passenger_phone,
                passenger_email=booking.passenger_email,
                from_location=booking.from_location,
                to_location=booking.to_location,
                vehicle_group=booking.vehicle_group,
                duty_type=booking.duty_type,
                start_date=current_date.strftime('%Y-%m-%d'),
                end_date=current_date.strftime('%Y-%m-%d'),  # Each booking is single day
                reporting_time=booking.reporting_time,
                start_from_garage=booking.start_from_garage,
                reporting_address=booking.reporting_address,
                drop_address=booking.drop_address,
                flight_train_number=booking.flight_train_number,
                dispatch_center=booking.dispatch_center,
                bill_to=booking.bill_to,
                price=booking.price,
                remarks=f"{booking.remarks or ''} (Day {day_counter} of multi-day booking)".strip(),
                labels=booking.labels,
                confidence_score=booking.confidence_score,
                extraction_reasoning=booking.extraction_reasoning,
                additional_info=booking.additional_info
            )
            
            bookings.append(new_booking)
            current_date += timedelta(days=1)
            day_counter += 1
        
        return bookings
        
    except (ValueError, AttributeError) as e:
        # If date parsing fails, return original booking
        logger.warning(f"Date parsing failed for booking: {str(e)}")
        return [booking]

def save_to_google_sheets(booking_data):
    """Save booking data to Google Sheets"""
    try:
        # Check if this booking spans multiple dates
        bookings_to_save = create_multiple_bookings_if_needed(booking_data)
        
        # Save to Google Sheets
        success, message, total_rows = sheets_manager.append_booking_data(bookings_to_save)
        
        if success:
            return True, (total_rows, len(bookings_to_save))
        else:
            return False, message
            
    except Exception as e:
        return False, f"Failed to save to Google Sheets: {str(e)}"

def display_single_booking(booking: BookingExtraction, booking_number: int = None):
    """Display a single booking in a clean format"""
    if booking_number:
        st.subheader(f"📋 Booking #{booking_number}")
    else:
        st.subheader("📋 Extracted Information")
    
    # Group fields logically
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**👤 Passenger Details**")
        if booking.passenger_name:
            st.write(f"**Name:** {booking.passenger_name}")
        if booking.passenger_phone:
            st.write(f"**Phone:** {booking.passenger_phone}")
        if booking.passenger_email:
            st.write(f"**Email:** {booking.passenger_email}")
        if booking.corporate:
            st.write(f"**Corporate:** {booking.corporate}")
        
        st.markdown("**📅 Trip Details**")
        if booking.start_date:
            st.write(f"**Date:** {booking.start_date}")
        if booking.end_date and booking.end_date != booking.start_date:
            st.write(f"**End Date:** {booking.end_date}")
        if booking.reporting_time:
            st.write(f"**Pickup Time:** {booking.reporting_time}")
        if booking.vehicle_group:
            st.write(f"**Vehicle:** {booking.vehicle_group}")
    
    with col2:
        st.markdown("**📍 Location Details**")
        if booking.from_location:
            st.write(f"**From:** {booking.from_location}")
        if booking.to_location:
            st.write(f"**To:** {booking.to_location}")
        if booking.reporting_address:
            st.write(f"**Pickup Address:** {booking.reporting_address}")
        if booking.drop_address:
            st.write(f"**Drop Address:** {booking.drop_address}")
        
        st.markdown("**ℹ️ Additional Information**")
        if booking.flight_train_number:
            st.write(f"**Flight/Train:** {booking.flight_train_number}")
        if booking.duty_type:
            st.write(f"**Duty Type:** {booking.duty_type}")
        if booking.price:
            st.write(f"**Price:** {booking.price}")
        if booking.remarks:
            st.write(f"**Remarks:** {booking.remarks}")
    
    # Show additional info if available
    if booking.additional_info:
        with st.expander("📄 Additional Info"):
            st.text_area("Additional information extracted:", booking.additional_info, height=100, disabled=True)

def display_extraction_results(result: StructuredExtractionResult):
    """Display structured extraction results"""
    if not result or not result.bookings:
        st.error("❌ No bookings found in the processed content")
        return
    
    # Show processing summary
    st.metric("📊 Bookings Found", result.total_bookings_found)
    
    # Display each booking
    if len(result.bookings) == 1:
        display_single_booking(result.bookings[0])
    else:
        for i, booking in enumerate(result.bookings, 1):
            with st.expander(f"Booking #{i} - {booking.passenger_name or 'Unknown Passenger'}", expanded=(i == 1)):
                display_single_booking(booking, i)

def save_extraction_results_to_sheets(result: StructuredExtractionResult):
    """Save extraction results to Google Sheets"""
    try:
        all_bookings_to_save = []
        
        # Process each booking for multi-date handling
        for booking in result.bookings:
            bookings_to_save = create_multiple_bookings_if_needed(booking)
            all_bookings_to_save.extend(bookings_to_save)
        
        # Save to Google Sheets
        success, message, total_rows = sheets_manager.append_booking_data(all_bookings_to_save)
        
        if success:
            return True, (total_rows, len(all_bookings_to_save))
        else:
            return False, message
            
    except Exception as e:
        return False, f"Failed to save to Google Sheets: {str(e)}"


def main():
    """Main Streamlit application"""
    
    # Page configuration
    st.set_page_config(
        page_title="FirstCars Demo Tool",
        page_icon="🚗",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # Header
    st.title("🚗 FirstCars Demo Tool")
    st.markdown("**Intelligent Car Rental Booking Extraction from Email Content**")
    st.markdown("🎆 **Enhanced Features:** Multiple booking detection, relative date parsing (tomorrow, next Monday), smart city/vehicle mapping")
    st.markdown("---")
    
    # Test Google Sheets connection
    with st.spinner("Connecting to Google Sheets..."):
        sheets_success, sheets_message = test_google_sheets_connection()
    
    if sheets_success:
        st.success(f"✅ {sheets_message}")
        # Initialize headers in Google Sheets if needed
        sheets_manager.initialize_headers()
    else:
        st.error(f"❌ Google Sheets connection failed: {sheets_message}")
        st.info("📝 Please ensure Google Service Account credentials are configured in Streamlit secrets.")
    
    # Check for API key (from secrets or environment)
    api_key = None
    try:
        # Try Streamlit secrets first (for deployment)
        api_key = st.secrets["OPENAI_API_KEY"]
    except (KeyError, FileNotFoundError):
        # Fallback to environment variable (for local development)
        api_key = os.getenv('OPENAI_API_KEY')
    
    if not api_key:
        st.error("❌ OpenAI API key not found. Please configure it in Streamlit secrets or .env file.")
        st.info("📝 For local development: Add OPENAI_API_KEY to your .env file")
        st.info("☁️ For deployment: Configure OPENAI_API_KEY in Streamlit Cloud secrets")
        st.stop()
    
    # Set the API key in environment for the agent to use
    os.environ['OPENAI_API_KEY'] = api_key
    
    # Initialize processors
    unified_processor = UnifiedEmailProcessor(api_key)
    
    # Initialize document processor if available
    document_processor = None
    if DOCUMENT_PROCESSOR_AVAILABLE:
        try:
            document_processor = SimpleDocumentProcessor(openai_api_key=api_key)
            if hasattr(document_processor, 'aws_available') and document_processor.aws_available:
                st.success("🚀 Document Processing with S3 + Textract + AI is available! (Using your exact approach)")
            else:
                st.warning("⚠️ Document processor available but AWS not configured")
                document_processor = None
        except Exception as e:
            st.error(f"❌ Document processor initialization failed: {str(e)}")
            document_processor = None
    else:
        st.warning(f"⚠️ Document processing not available: {globals().get('DOCUMENT_PROCESSOR_ERROR', 'Unknown error')}")
    
    # Create tabs if document processor is available
    if document_processor:
        tab1, tab2 = st.tabs(["Email Processing", "Document Processing"])
    else:
        # Single email processing interface
        tab1 = st.container()

    # Tab 1: Email Processing
    with tab1:
        st.subheader("📧 Email Processing")
        
        # Main layout
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("📧 Email Content")
            email_content = st.text_area(
                "Paste your email content here:",
                height=400,
                placeholder="Dear Team,\n\nKindly arrange a cab...\n\nRegards,\nJohn"
            )
            
            # Action buttons
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                extract_btn = st.button("🔍 Extract Data", type="primary", use_container_width=True, key="email_extract")
            with col_btn2:
                clear_btn = st.button("🗑️ Clear", use_container_width=True, key="email_clear")
        
        with col2:
            st.subheader("📊 Results")
            
            # Initialize session state
            if 'extraction_result' not in st.session_state:
                st.session_state.extraction_result = None
            if 'extraction_done' not in st.session_state:
                st.session_state.extraction_done = False
            
            # Clear functionality
            if clear_btn:
                st.session_state.extraction_result = None
                st.session_state.extraction_done = False
                st.rerun()
            
            # Extract data
            if extract_btn and email_content.strip():
                with st.spinner("🤖 Processing email with AI..."):
                    try:
                        result = unified_processor.process_email(email_content.strip())
                        st.session_state.extraction_result = result
                        st.session_state.extraction_done = True
                    except Exception as e:
                        st.error(f"❌ Extraction failed: {str(e)}")
                        st.session_state.extraction_result = None
                        st.session_state.extraction_done = False
            
            elif extract_btn and not email_content.strip():
                st.warning("⚠️ Please enter email content first.")
            
            # Display results
            if st.session_state.extraction_done and st.session_state.extraction_result:
                display_extraction_results(st.session_state.extraction_result)
                
                st.markdown("---")
                if st.button("💾 Save to Google Sheets", type="secondary", use_container_width=True, key="email_save"):
                    if not sheets_success:
                        st.error("❌ Cannot save: Google Sheets connection failed. Please check your credentials.")
                    else:
                        with st.spinner("Saving to Google Sheets..."):
                            success, result_info = save_extraction_results_to_sheets(st.session_state.extraction_result)
                        if success:
                            total_records, bookings_added = result_info
                            if bookings_added > 1:
                                st.success(f"✅ Saved {bookings_added} bookings successfully! Total records: {total_records}")
                            else:
                                st.success(f"✅ Saved successfully! Total records: {total_records}")
                        else:
                            st.error(f"❌ Save failed: {result_info}")
            
            elif not st.session_state.extraction_done:
                st.info("👈 Enter email content and click 'Extract Data' to see results here.")
    
    # Tab 2: Document Processing (only if document processor is available)
    if document_processor:
        with tab2:
            st.subheader("🖼️ Document Processing")
            st.markdown("**Upload booking documents (PDFs, Word docs, or email screenshots) for intelligent extraction**")
            
            uploaded_files = st.file_uploader(
                "Choose files to upload:",
                type=document_processor.get_supported_file_types(),
                accept_multiple_files=True,
                help="Supported formats: PDF, Word documents (.docx/.doc), Images (.jpg/.png/.gif) including email screenshots"
            )
            
            if uploaded_files:
                # Validate files
                valid_files = []
                for uploaded_file in uploaded_files:
                    is_valid, error_msg = document_processor.validate_file(uploaded_file.name, len(uploaded_file.getvalue()))
                    
                    if is_valid:
                        valid_files.append((uploaded_file.getvalue(), uploaded_file.name))
                        st.success(f"✅ {uploaded_file.name} - Ready for processing")
                    else:
                        st.error(f"❌ {uploaded_file.name}: {error_msg}")
                
                if valid_files:
                    if st.button("🔍 Process Documents", type="primary", use_container_width=True, key="doc_process"):
                        with st.spinner(f"📷 Processing {len(valid_files)} document(s) with S3 + Textract + AI..."):
                            try:
                                results = document_processor.process_multiple_documents(valid_files)
                                st.session_state.doc_results = results
                                st.session_state.doc_processing_done = True
                            except Exception as e:
                                st.error(f"❌ Document processing failed: {str(e)}")
                                st.session_state.doc_results = None
                                st.session_state.doc_processing_done = False
            
            # Display document processing results
            if st.session_state.get('doc_processing_done') and st.session_state.get('doc_results'):
                st.markdown("### 📊 Processing Results")
                
                total_bookings = sum(len(r.bookings) for r in st.session_state.doc_results)
                st.info(f"📊 Found {total_bookings} total booking(s) from {len(st.session_state.doc_results)} document(s)")
                
                for i, result in enumerate(st.session_state.doc_results, 1):
                    with st.expander(f"Document {i} Results ({len(result.bookings)} booking(s))", expanded=(i == 1)):
                        st.markdown(f"**Processing Method:** {result.extraction_method}")
                        if result.processing_notes:
                            st.markdown(f"**Notes:** {result.processing_notes}")
                        
                        display_extraction_results(result)
                
                # Save all documents button
                st.markdown("---")
                if st.button("💾 Save All Documents to Google Sheets", type="secondary", use_container_width=True, key="doc_save_all"):
                    if not sheets_success:
                        st.error("❌ Cannot save: Google Sheets connection failed. Please check your credentials.")
                    else:
                        with st.spinner("Saving all document results to Google Sheets..."):
                            # Combine all bookings from all documents
                            all_bookings = []
                            for result in st.session_state.doc_results:
                                all_bookings.extend(result.bookings)
                            
                            if all_bookings:
                                # Create combined result
                                combined_result = StructuredExtractionResult(
                                    bookings=all_bookings,
                                    total_bookings_found=len(all_bookings),
                                    extraction_method="document_batch_processing",
                                    confidence_score=0.8,
                                    processing_notes=f"Batch processing of {len(st.session_state.doc_results)} documents"
                                )
                                
                                success, result_info = save_extraction_results_to_sheets(combined_result)
                                
                                if success:
                                    total_records, bookings_added = result_info
                                    st.success(f"✅ Saved {bookings_added} bookings from {len(st.session_state.doc_results)} documents! Total records: {total_records}")
                                else:
                                    st.error(f"❌ Save failed: {result_info}")
                            else:
                                st.warning("⚠️ No bookings to save")

    # Footer with Google Sheets info
    st.markdown("---")
    col_info1, col_info2, col_info3 = st.columns(3)
    
    # Get Google Sheets information
    if sheets_success:
        sheet_info = sheets_manager.get_sheet_info()
        if sheet_info:
            with col_info1:
                st.metric("📁 Total Records", sheet_info["total_rows"])
            
            with col_info2:
                st.metric("📈 Sheet Title", sheet_info["sheet_title"])
            
            with col_info3:
                st.markdown(f"**📝 Worksheet:** {sheet_info['worksheet_title']}")
            
            # Link to open Google Sheets
            st.markdown(f"### 🔗 [Open Google Sheets]({GOOGLE_SHEETS_URL})")
        else:
            st.warning("⚠️ Could not retrieve Google Sheets information")
    else:
        with col_info2:
            st.error("❌ Google Sheets not connected")

if __name__ == "__main__":
    main()
