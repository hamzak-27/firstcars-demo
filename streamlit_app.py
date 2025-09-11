#!/usr/bin/env python3
"""
FirstCars Demo Tool - Streamlit Frontend
A user-friendly interface for the Multi-Modal Car Rental AI Agent
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

# Import our enhanced processors
from unified_email_processor import UnifiedEmailProcessor
from document_processor import DocumentProcessor
from structured_email_agent import StructuredExtractionResult
from car_rental_ai_agent import BookingExtraction
from google_sheets_integration import sheets_manager

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

def validate_uploaded_files(uploaded_files: List) -> List[Tuple[bytes, str]]:
    """Validate and process uploaded files"""
    valid_documents = []
    doc_processor = DocumentProcessor()
    
    for uploaded_file in uploaded_files:
        # Validate file
        is_valid, error_msg = doc_processor.validate_file(uploaded_file.name, len(uploaded_file.getvalue()))
        
        if is_valid:
            valid_documents.append((uploaded_file.getvalue(), uploaded_file.name))
        else:
            st.error(f"❌ {uploaded_file.name}: {error_msg}")
    
    return valid_documents

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
    document_processor = DocumentProcessor(openai_api_key=api_key)

    # Tabs for different workflows
    tab1, tab2, tab3, tab4 = st.tabs(["Email Text", "Email Screenshots", "Documents", "Email + Attachments"])

    # Tab 1: Email processing
    with tab1:
        st.subheader("📧 Process Email Text")
        email_content = st.text_area(
            "Paste your email content here:",
            height=300,
            placeholder="Dear Team,\n\nKindly arrange a cab...\n\nRegards,\nJohn"
        )
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            process_email_btn = st.button("🔍 Extract from Email", type="primary", use_container_width=True, key="process_email")
        with col_btn2:
            clear_email_btn = st.button("🗑️ Clear", use_container_width=True, key="clear_email")
        
        if clear_email_btn:
            st.session_state.pop('email_result', None)
            st.rerun()
        
        if process_email_btn:
            if not email_content.strip():
                st.warning("⚠️ Please enter email content first.")
            else:
                with st.spinner("🤖 Processing email with AI..."):
                    try:
                        result = unified_processor.process_email(email_content.strip())
                        st.session_state.email_result = result
                    except Exception as e:
                        st.error(f"❌ Extraction failed: {str(e)}")
                        st.session_state.email_result = None
        
        # Show results
        if 'email_result' in st.session_state and st.session_state.email_result:
            display_extraction_results(st.session_state.email_result)
            st.markdown("---")
            if st.button("💾 Save to Google Sheets", type="secondary", use_container_width=True, key="save_email"):
                if not sheets_success:
                    st.error("❌ Cannot save: Google Sheets connection failed. Please check your credentials.")
                else:
                    with st.spinner("Saving to Google Sheets..."):
                        success, result_info = save_extraction_results_to_sheets(st.session_state.email_result)
                    if success:
                        total_records, bookings_added = result_info
                        if bookings_added > 1:
                            st.success(f"✅ Saved {bookings_added} bookings successfully! Total records: {total_records}")
                        else:
                            st.success(f"✅ Saved successfully! Total records: {total_records}")
                    else:
                        st.error(f"❌ Save failed: {result_info}")

    # Tab 2: Screenshot processing
    with tab2:
        st.subheader("📷 Process Email Screenshots")
        st.markdown("Upload screenshots of structured emails (with tables) for OCR processing and data extraction.")
        
        uploaded_screenshots = st.file_uploader(
            "Upload email screenshots:",
            type=['jpg', 'jpeg', 'png', 'gif'],
            accept_multiple_files=True,
            key="screenshots"
        )
        
        if uploaded_screenshots:
            # Validate screenshot files
            valid_screenshots = []
            for screenshot in uploaded_screenshots:
                file_size = len(screenshot.getvalue())
                if file_size > 10 * 1024 * 1024:  # 10MB limit
                    st.error(f"❌ {screenshot.name}: File too large (max 10MB)")
                else:
                    valid_screenshots.append((screenshot.getvalue(), screenshot.name))
            
            if valid_screenshots:
                if st.button("🔍 Extract from Screenshots", type="primary", use_container_width=True, key="process_screenshots"):
                    with st.spinner("📷 Processing screenshots with OCR + AI..."):
                        try:
                            # Process screenshots through document processor
                            results = document_processor.process_multiple_documents(valid_screenshots)
                            
                            # For screenshots of structured emails, we want to force structured processing
                            enhanced_results = []
                            for result in results:
                                if result.bookings:
                                    # Try to reprocess with structured agent if we got basic results
                                    for booking in result.bookings:
                                        if booking.additional_info and "EXTRACTED TEXT:" in booking.additional_info:
                                            # Extract the OCR text and reprocess as structured
                                            ocr_text = booking.additional_info.split("EXTRACTED TEXT:")[1].split("\nEXTRACTED TABLES:")[0].strip()
                                            if ocr_text:
                                                # Force structured processing on OCR text
                                                structured_result = unified_processor.process_email_as_structured(ocr_text)
                                                if structured_result.bookings and len(structured_result.bookings) > len(result.bookings):
                                                    enhanced_results.append(structured_result)
                                                    continue
                                enhanced_results.append(result)
                            
                            st.session_state.screenshot_results = enhanced_results
                        except Exception as e:
                            st.error(f"❌ Screenshot processing failed: {str(e)}")
                            st.session_state.screenshot_results = None
        
        if 'screenshot_results' in st.session_state and st.session_state.screenshot_results:
            st.markdown("### Results")
            for i, res in enumerate(st.session_state.screenshot_results, 1):
                with st.expander(f"Screenshot Result #{i}", expanded=(i == 1)):
                    display_extraction_results(res)
            
            st.markdown("---")
            if st.button("💾 Save All to Google Sheets", type="secondary", use_container_width=True, key="save_screenshots"):
                if not sheets_success:
                    st.error("❌ Cannot save: Google Sheets connection failed. Please check your credentials.")
                else:
                    with st.spinner("Saving to Google Sheets..."):
                        # Combine all screenshot bookings
                        combined = StructuredExtractionResult(
                            bookings=[b for r in st.session_state.screenshot_results for b in r.bookings],
                            total_bookings_found=sum(r.total_bookings_found for r in st.session_state.screenshot_results),
                            extraction_method="screenshots_batch",
                            confidence_score=0.8,
                            processing_notes="Batch save from email screenshots"
                        )
                        success, result_info = save_extraction_results_to_sheets(combined)
                    if success:
                        total_records, bookings_added = result_info
                        st.success(f"✅ Saved {bookings_added} bookings successfully! Total records: {total_records}")
                    else:
                        st.error(f"❌ Save failed: {result_info}")

    # Tab 3: Document processing
    with tab3:
        st.subheader("🖼️ Process Documents (PDF/Word/Images)")
        uploaded_files = st.file_uploader(
            "Upload one or more documents:",
            type=document_processor.get_supported_file_types(),
            accept_multiple_files=True
        )
        if uploaded_files:
            valid_docs = validate_uploaded_files(uploaded_files)
            if valid_docs:
                if st.button("🔍 Extract from Documents", type="primary", use_container_width=True, key="process_docs"):
                    with st.spinner("🔎 Extracting from documents..."):
                        try:
                            results = document_processor.process_multiple_documents(valid_docs)
                            st.session_state.doc_results = results
                        except Exception as e:
                            st.error(f"❌ Document processing failed: {str(e)}")
                            st.session_state.doc_results = None
        
        if 'doc_results' in st.session_state and st.session_state.doc_results:
            st.markdown("### Results")
            for i, res in enumerate(st.session_state.doc_results, 1):
                with st.expander(f"Document Result #{i}", expanded=(i == 1)):
                    display_extraction_results(res)
            
            st.markdown("---")
            if st.button("💾 Save All to Google Sheets", type="secondary", use_container_width=True, key="save_docs"):
                if not sheets_success:
                    st.error("❌ Cannot save: Google Sheets connection failed. Please check your credentials.")
                else:
                    with st.spinner("Saving to Google Sheets..."):
                        # Combine all document bookings into a single result-like object
                        combined = StructuredExtractionResult(
                            bookings=[b for r in st.session_state.doc_results for b in r.bookings],
                            total_bookings_found=sum(r.total_bookings_found for r in st.session_state.doc_results),
                            extraction_method="documents_batch",
                            confidence_score=0.8,
                            processing_notes="Batch save from documents"
                        )
                        success, result_info = save_extraction_results_to_sheets(combined)
                    if success:
                        total_records, bookings_added = result_info
                        st.success(f"✅ Saved {bookings_added} bookings successfully! Total records: {total_records}")
                    else:
                        st.error(f"❌ Save failed: {result_info}")

    # Tab 4: Combined processing
    with tab4:
        st.subheader("📧+🖼️ Process Email with Attachments")
        email_content_combined = st.text_area(
            "Paste your email content here:",
            height=200,
            key="combined_email",
            placeholder="Dear Team,\n\nPlease find the attached booking details..."
        )
        uploaded_files_combined = st.file_uploader(
            "Upload attachments:",
            type=document_processor.get_supported_file_types(),
            accept_multiple_files=True,
            key="combined_files"
        )
        if st.button("🤖 Process Email + Attachments", type="primary", use_container_width=True, key="process_combined"):
            if not email_content_combined.strip() and not uploaded_files_combined:
                st.warning("⚠️ Enter email content or upload at least one attachment.")
            else:
                valid_docs = validate_uploaded_files(uploaded_files_combined or [])
                with st.spinner("Processing email and attachments..."):
                    try:
                        result = document_processor.combine_email_and_documents(
                            email_content=email_content_combined.strip(),
                            documents=valid_docs
                        )
                        st.session_state.combined_result = result
                    except Exception as e:
                        st.error(f"❌ Combined processing failed: {str(e)}")
                        st.session_state.combined_result = None
        
        if 'combined_result' in st.session_state and st.session_state.combined_result:
            display_extraction_results(st.session_state.combined_result)
            st.markdown("---")
            if st.button("💾 Save to Google Sheets", type="secondary", use_container_width=True, key="save_combined"):
                if not sheets_success:
                    st.error("❌ Cannot save: Google Sheets connection failed. Please check your credentials.")
                else:
                    with st.spinner("Saving to Google Sheets..."):
                        success, result_info = save_extraction_results_to_sheets(st.session_state.combined_result)
                    if success:
                        total_records, bookings_added = result_info
                        st.success(f"✅ Saved {bookings_added} bookings successfully! Total records: {total_records}")
                    else:
                        st.error(f"❌ Save failed: {result_info}")

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
