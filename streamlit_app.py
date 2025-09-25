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

def display_single_flight(flight, flight_number: int = None):
    """Display a single flight in a clean format"""
    import time
    # Generate a truly unique key for flight displays
    flight_unique_key = f"flight_{flight_number if flight_number is not None else 'single'}_{int(time.time() * 1000000)}"
    
    if flight_number:
        st.subheader(f"✈️ Flight #{flight_number}")
    else:
        st.subheader("✈️ Flight Information")
    
    # Group fields logically
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**📋 Flight Details**")
        if flight.flight_number:
            st.write(f"**Flight:** {flight.flight_number}")
        if flight.airline:
            st.write(f"**Airline:** {flight.airline}")
        if flight.aircraft_type:
            st.write(f"**Aircraft:** {flight.aircraft_type}")
        if flight.flight_duration:
            st.write(f"**Duration:** {flight.flight_duration}")
        if flight.status:
            st.write(f"**Status:** {flight.status}")
        
        st.markdown("**👤 Passenger Info**")
        if flight.passenger_name:
            st.write(f"**Passenger:** {flight.passenger_name}")
        if flight.booking_reference:
            st.write(f"**PNR/Booking:** {flight.booking_reference}")
        if flight.seat_number:
            st.write(f"**Seat:** {flight.seat_number}")
    
    with col2:
        st.markdown("**🛫 Departure**")
        if flight.departure_airport:
            st.write(f"**Airport:** {flight.departure_airport}")
        if flight.departure_city:
            st.write(f"**City:** {flight.departure_city}")
        if flight.departure_date:
            st.write(f"**Date:** {flight.departure_date}")
        if flight.departure_time:
            st.write(f"**Time:** {flight.departure_time}")
        
        st.markdown("**🛬 Arrival**")
        if flight.arrival_airport:
            st.write(f"**Airport:** {flight.arrival_airport}")
        if flight.arrival_city:
            st.write(f"**City:** {flight.arrival_city}")
        if flight.arrival_date:
            st.write(f"**Date:** {flight.arrival_date}")
        if flight.arrival_time:
            st.write(f"**Time:** {flight.arrival_time}")
    
    # Additional information in expandable sections
    if any([flight.gate, flight.terminal, flight.baggage_info, flight.meal_info, flight.ticket_type, flight.price]):
        with st.expander("📝 Additional Details"):
            if flight.gate:
                st.write(f"**Gate:** {flight.gate}")
            if flight.terminal:
                st.write(f"**Terminal:** {flight.terminal}")
            if flight.baggage_info:
                st.write(f"**Baggage:** {flight.baggage_info}")
            if flight.meal_info:
                st.write(f"**Meal:** {flight.meal_info}")
            if flight.ticket_type:
                st.write(f"**Class:** {flight.ticket_type}")
            if flight.price:
                st.write(f"**Price:** {flight.price}")
    
    # Show remarks and additional info if available
    if flight.remarks:
        st.write(f"**📋 Remarks:** {flight.remarks}")
    
    if flight.additional_info:
        with st.expander("📄 Additional Info"):
            st.text_area("Additional flight information:", flight.additional_info, height=100, disabled=True, key=f"flight_additional_{flight_unique_key}")

def display_flight_results(result):
    """Display flight extraction results"""
    if not result or not result.flights:
        st.error("❌ No flights found in the processed document")
        return
    
    # Show processing summary
    st.metric("📊 Flights Found", result.total_flights_found)
    
    # Display each flight
    if len(result.flights) == 1:
        display_single_flight(result.flights[0])
    else:
        for i, flight in enumerate(result.flights, 1):
            with st.expander(f"Flight #{i} - {flight.flight_number or 'Unknown Flight'}", expanded=(i == 1)):
                display_single_flight(flight, i)

def display_single_booking(booking: BookingExtraction, booking_number: int = None):
    """Display a single booking with ALL 20 fields from AI field list.csv"""
    import time
    # Generate a truly unique key based on booking_number and timestamp
    unique_key = f"{booking_number if booking_number is not None else 'single'}_{int(time.time() * 1000000)}"
    
    if booking_number:
        st.subheader(f"📋 Booking #{booking_number}")
    else:
        st.subheader("📋 Extracted Information")
    
    # Helper function to display field with fallback to NA
    def display_field(label, value, icon=""):
        display_value = value if value and str(value).strip() and str(value).strip().lower() not in ['none', 'null'] else "NA"
        st.write(f"**{icon} {label}:** {display_value}")
    
    # Display all 20 fields as per AI field list.csv in organized sections
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**🏢 Corporate & Booking Information**")
        display_field("Customer", booking.corporate, "🏢")
        display_field("Booked By Name", booking.booked_by_name, "📝")
        display_field("Booked By Phone Number", booking.booked_by_phone, "📞")
        display_field("Booked By Email", booking.booked_by_email, "📧")
        
        st.markdown("**👤 Passenger Information**")
        display_field("Passenger Name", booking.passenger_name, "👤")
        display_field("Passenger Phone Number", booking.passenger_phone, "📱")
        display_field("Passenger Email", booking.passenger_email, "✉️")
        
        st.markdown("**🚗 Vehicle & Service Details**")
        display_field("Vehicle Group", booking.vehicle_group, "🚗")
        display_field("Duty Type", booking.duty_type, "📋")
        display_field("Flight/Train Number", booking.flight_train_number, "✈️")
    
    with col2:
        st.markdown("**📍 Location Information**")
        display_field("From (Service Location)", booking.from_location, "📍")
        display_field("To", booking.to_location, "🎯")
        display_field("Reporting Address", booking.reporting_address, "📍")
        display_field("Drop Address", booking.drop_address, "🚩")
        
        st.markdown("**📅 Date & Time Information**")
        display_field("Start Date", booking.start_date, "📅")
        display_field("End Date", booking.end_date, "📅")
        display_field("Rep. Time", booking.reporting_time, "⏰")
        
        st.markdown("**🔧 Additional Details**")
        display_field("Dispatch Center", booking.dispatch_center, "🚛")
        display_field("Labels", booking.labels, "🏷️")
    
    # Remarks section (full width)
    st.markdown("**📝 Remarks & Special Instructions**")
    remarks_value = booking.remarks if booking.remarks and str(booking.remarks).strip() and str(booking.remarks).strip().lower() not in ['none', 'null'] else "NA"
    st.text_area("Remarks:", value=remarks_value, height=100, disabled=True, key=f"remarks_{unique_key}")
    
    # Show confidence and processing info
    if hasattr(booking, 'confidence_score') and booking.confidence_score:
        confidence_color = "🟢" if booking.confidence_score > 0.8 else "🟡" if booking.confidence_score > 0.6 else "🔴"
        st.caption(f"{confidence_color} Confidence Score: {booking.confidence_score:.2f}")
    
    # Show additional info if available
    if booking.additional_info and str(booking.additional_info).strip() and str(booking.additional_info).strip().lower() not in ['none', 'null', 'na']:
        with st.expander("📄 Additional Information"):
            st.text_area("Additional information extracted:", booking.additional_info, height=100, disabled=True, key=f"additional_{unique_key}")
    
    # Show duty type reasoning if available (DEBUG INFORMATION)
    if hasattr(booking, 'duty_type_reasoning') and booking.duty_type_reasoning:
        with st.expander("🎯 Duty Type Analysis (Debug)", expanded=False):
            st.markdown("**🔍 Why was this duty type assigned?**")
            st.text_area(
                "Detailed reasoning for duty type determination:", 
                booking.duty_type_reasoning, 
                height=400, 
                disabled=True, 
                key=f"duty_reasoning_{unique_key}"
            )
            
            # Add a summary box with key points
            reasoning_text = booking.duty_type_reasoning
            final_result = ""
            corporate_detected = ""
            package_type = ""
            
            if "FINAL DETERMINATION:" in reasoning_text:
                lines = reasoning_text.split("\n")
                for line in lines:
                    if "Final Result:" in line:
                        final_result = line.split("Final Result:")[-1].strip()
                    elif "CORPORATE DETECTED:" in line:
                        corporate_detected = "Yes"
                    elif "NO CORPORATE DETECTED:" in line:
                        corporate_detected = "No"
                    elif "Package Type:" in line:
                        package_type = line.split("Package Type:")[-1].strip()
            
            # Show summary metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Corporate Detected", corporate_detected or "Unknown")
            with col2:
                st.metric("Package Type", package_type or "Unknown")
            with col3:
                st.metric("Final Duty Type", final_result or booking.duty_type or "Unknown")
            
            # Show color-coded status
            if final_result:
                if "G-" in final_result:
                    st.success(f"🟢 G2G Corporate: {final_result}")
                elif "P-" in final_result:
                    st.info(f"🔵 P2P Corporate: {final_result}")
                else:
                    st.warning(f"🟡 Unknown Format: {final_result}")
    
    elif booking.duty_type:
        # If duty type exists but no reasoning, show a note
        with st.expander("🎯 Duty Type Analysis (Debug)", expanded=False):
            st.warning("⚠️ Duty type was assigned but no detailed reasoning is available.")
            st.info(f"**Current Duty Type:** {booking.duty_type}")
            st.caption("This might be from an older extraction or fallback method.")

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
    st.title("🚗 Demo Tool")
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
    
    # Initialize DOCX processor
    docx_processor = None
    try:
        from docx_document_processor import DocxDocumentProcessor
        docx_processor = DocxDocumentProcessor(openai_api_key=api_key)
        st.success("📄 Word Document Processing is available!")
    except ImportError as e:
        st.warning(f"⚠️ Word document processing not available: python-docx not installed")
    except Exception as e:
        st.warning(f"⚠️ Word document processor initialization failed: {str(e)}")
    
    # Initialize Flight processor
    flight_processor = None
    try:
        from flight_document_processor import FlightDocumentProcessor
        flight_processor = FlightDocumentProcessor(openai_api_key=api_key)
        if hasattr(flight_processor, 'aws_available') and flight_processor.aws_available:
            st.success("✈️ Flight Details Processing is available! (S3 + Textract + Flight AI)")
        else:
            st.warning("⚠️ Flight processor available but AWS not configured")
            flight_processor = None
    except ImportError as e:
        st.warning(f"⚠️ Flight processing not available: Missing dependencies")
    except Exception as e:
        st.warning(f"⚠️ Flight processor initialization failed: {str(e)}")
    
    # Create tabs based on available processors
    tabs_list = ["Email Processing"]
    if document_processor:
        tabs_list.append("Document Processing (S3+Textract)")
    if docx_processor:
        tabs_list.append("Word Document Processing")
    if flight_processor:
        tabs_list.append("Flight Details Processing")
    
    if len(tabs_list) > 1:
        tabs = st.tabs(tabs_list)
        tab1 = tabs[0]  # Email Processing
        
        # Assign tabs based on availability
        tab_idx = 1
        tab2 = tabs[tab_idx] if document_processor else None  # Document Processing
        if document_processor:
            tab_idx += 1
        
        tab3 = tabs[tab_idx] if docx_processor else None  # Word Document Processing  
        if docx_processor:
            tab_idx += 1
            
        tab4 = tabs[tab_idx] if flight_processor else None  # Flight Details Processing
    else:
        # Single email processing interface
        tab1 = st.container()
        tab2 = None
        tab3 = None
        tab4 = None

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
    
    # Tab 2: Document Processing (S3+Textract) if available
    if document_processor and tab2:
        with tab2:
            st.subheader("🖼️ Document Processing (S3 + Textract)")
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

    # Tab 3: Word Document Processing (.docx files)
    if docx_processor and tab3:
        with tab3:
            st.subheader("📄 Word Document Processing")
            st.markdown("**Upload .docx or .doc files for intelligent booking extraction**")
            
            docx_files = st.file_uploader(
                "Choose Word files to upload:",
                type=['docx', 'doc'],
                accept_multiple_files=True,
                help="Supported formats: Microsoft Word documents (.docx recommended, .doc supported via Textract if configured)",
                key="docx_uploader"
            )
            
            if docx_files:
                # Validate files
                valid_docx_files = []
                valid_doc_files = []
                for uploaded_file in docx_files:
                    name_lower = uploaded_file.name.lower()
                    size = len(uploaded_file.getvalue())
                    if name_lower.endswith('.docx'):
                        is_valid, error_msg = docx_processor.validate_file(uploaded_file.name, size)
                        if is_valid:
                            valid_docx_files.append((uploaded_file.getvalue(), uploaded_file.name))
                            st.success(f"✅ {uploaded_file.name} - Ready for DOCX processing")
                        else:
                            st.error(f"❌ {uploaded_file.name}: {error_msg}")
                    elif name_lower.endswith('.doc'):
                        if document_processor:
                            is_valid, error_msg = document_processor.validate_file(uploaded_file.name, size)
                            if is_valid:
                                valid_doc_files.append((uploaded_file.getvalue(), uploaded_file.name))
                                st.success(f"✅ {uploaded_file.name} - Ready for DOC processing (Textract)")
                            else:
                                st.error(f"❌ {uploaded_file.name}: {error_msg}")
                        else:
                            st.error(f"❌ {uploaded_file.name}: .doc support requires Document Processing (S3 + Textract) to be configured")
                    else:
                        st.error(f"❌ {uploaded_file.name}: Unsupported Word file type")
                
                if valid_docx_files or valid_doc_files:
                    if st.button("🔍 Process Word Documents", type="primary", use_container_width=True, key="docx_process"):
                        total_to_process = len(valid_docx_files) + len(valid_doc_files)
                        spinner_msg = f"📄 Processing {total_to_process} Word document(s)"
                        with st.spinner(spinner_msg + "..."):
                            try:
                                all_results = []
                                # Process DOCX with python-docx processor
                                for file_content, filename in valid_docx_files:
                                    result = docx_processor.process_document(file_content, filename)
                                    all_results.append(result)
                                # Process DOC via Textract if available
                                if valid_doc_files and document_processor:
                                    for file_content, filename in valid_doc_files:
                                        result = document_processor.process_document(file_content, filename, file_type='doc')
                                        all_results.append(result)
                                
                                st.session_state.docx_results = all_results
                                st.session_state.docx_processing_done = True
                            except Exception as e:
                                st.error(f"❌ Word document processing failed: {str(e)}")
                                st.session_state.docx_results = None
                                st.session_state.docx_processing_done = False
            
            # Display Word document processing results
            if st.session_state.get('docx_processing_done') and st.session_state.get('docx_results'):
                st.markdown("### 📊 Word Document Processing Results")
                
                total_bookings = sum(len(r.bookings) for r in st.session_state.docx_results)
                st.info(f"📊 Found {total_bookings} total booking(s) from {len(st.session_state.docx_results)} Word document(s)")
                
                for i, result in enumerate(st.session_state.docx_results, 1):
                    with st.expander(f"Document {i} Results ({len(result.bookings)} booking(s))", expanded=(i == 1)):
                        st.markdown(f"**Processing Method:** {result.extraction_method}")
                        if result.processing_notes:
                            st.markdown(f"**Notes:** {result.processing_notes}")
                        
                        display_extraction_results(result)
                
                # Save all Word documents button
                st.markdown("---")
                if st.button("💾 Save All Word Documents to Google Sheets", type="secondary", use_container_width=True, key="docx_save_all"):
                    if not sheets_success:
                        st.error("❌ Cannot save: Google Sheets connection failed. Please check your credentials.")
                    else:
                        with st.spinner("Saving all Word document results to Google Sheets..."):
                            # Combine all bookings from all Word documents
                            all_docx_bookings = []
                            for result in st.session_state.docx_results:
                                all_docx_bookings.extend(result.bookings)
                            
                            if all_docx_bookings:
                                # Create combined result
                                combined_docx_result = StructuredExtractionResult(
                                    bookings=all_docx_bookings,
                                    total_bookings_found=len(all_docx_bookings),
                                    extraction_method="docx_batch_processing",
                                    confidence_score=0.8,
                                    processing_notes=f"Batch processing of {len(st.session_state.docx_results)} Word documents"
                                )
                                
                                success, result_info = save_extraction_results_to_sheets(combined_docx_result)
                                
                                if success:
                                    total_records, bookings_added = result_info
                                    st.success(f"✅ Saved {bookings_added} bookings from {len(st.session_state.docx_results)} Word documents! Total records: {total_records}")
                                else:
                                    st.error(f"❌ Save failed: {result_info}")
                            else:
                                st.warning("⚠️ No bookings to save")

    # Tab 4: Flight Details Processing (.pdf/.jpg/.png files for flight documents)
    if flight_processor and tab4:
        with tab4:
            st.subheader("✈️ Flight Details Processing")
            st.markdown("**Upload flight documents (PDFs, screenshots) for intelligent flight information extraction**")
            
            flight_files = st.file_uploader(
                "Choose flight documents to upload:",
                type=flight_processor.get_supported_file_types(),
                accept_multiple_files=True,
                help="Supported formats: PDF, Images (.jpg/.png/.gif) - Flight tickets, boarding passes, itineraries",
                key="flight_uploader"
            )
            
            if flight_files:
                # Validate files
                valid_flight_files = []
                for uploaded_file in flight_files:
                    is_valid, error_msg = flight_processor.validate_file(uploaded_file.name, len(uploaded_file.getvalue()))
                    
                    if is_valid:
                        valid_flight_files.append((uploaded_file.getvalue(), uploaded_file.name))
                        st.success(f"✅ {uploaded_file.name} - Ready for flight processing")
                    else:
                        st.error(f"❌ {uploaded_file.name}: {error_msg}")
                
                if valid_flight_files:
                    if st.button("✈️ Process Flight Documents", type="primary", use_container_width=True, key="flight_process"):
                        with st.spinner(f"✈️ Processing {len(valid_flight_files)} flight document(s) with S3 + Textract + Flight AI..."):
                            try:
                                flight_results = flight_processor.process_multiple_flight_documents(valid_flight_files)
                                st.session_state.flight_results = flight_results
                                st.session_state.flight_processing_done = True
                            except Exception as e:
                                st.error(f"❌ Flight document processing failed: {str(e)}")
                                st.session_state.flight_results = None
                                st.session_state.flight_processing_done = False
            
            # Display flight processing results
            if st.session_state.get('flight_processing_done') and st.session_state.get('flight_results'):
                st.markdown("### 📊 Flight Processing Results")
                
                total_flights = sum(len(r.flights) for r in st.session_state.flight_results)
                st.info(f"✈️ Found {total_flights} total flight(s) from {len(st.session_state.flight_results)} document(s)")
                
                for i, result in enumerate(st.session_state.flight_results, 1):
                    with st.expander(f"Document {i} Results ({len(result.flights)} flight(s))", expanded=(i == 1)):
                        st.markdown(f"**Processing Method:** {result.extraction_method}")
                        if result.processing_notes:
                            st.markdown(f"**Notes:** {result.processing_notes}")
                        
                        display_flight_results(result)
                
                # Note: Flight details don't need Google Sheets integration for now
                # Could be added later if needed for flight tracking

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
