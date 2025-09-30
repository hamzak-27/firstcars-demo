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
    
    # Show concise duty type reasoning if available (DEBUG INFORMATION)
    if hasattr(booking, 'duty_type_reasoning') and booking.duty_type_reasoning:
        reasoning_text = booking.duty_type_reasoning
        
        # Extract key information
        corporate_type = "P2P"  # Default
        keywords_found = []
        final_result = booking.duty_type or "Unknown"
        
        # Parse reasoning for key info
        lines = reasoning_text.split("\n")
        for line in lines:
            if "Category: G2G" in line:
                corporate_type = "G2G"
            elif "Category: P2P" in line:
                corporate_type = "P2P"
            elif "Keywords found:" in line:
                keywords_part = line.split("Keywords found:")[-1].strip()
                if keywords_part:
                    keywords_found = [kw.strip() for kw in keywords_part.split(",")]
            elif "OUTSTATION DETECTED" in line:
                keywords_found.append("outstation travel")
            elif "MAJOR CITY ROUTE" in line:
                keywords_found.append("major cities")
        
        # Show concise debug info
        with st.expander("🎯 Duty Type Debug", expanded=False):
            st.write(f"🏁 **Result:** `{final_result}` ({corporate_type} category)")
            if keywords_found:
                st.write(f"🔍 **Keywords:** {', '.join(keywords_found[:3])}{'...' if len(keywords_found) > 3 else ''}")
            else:
                st.write(f"🔍 **Keywords:** No specific keywords detected (used default)")
    
    elif booking.duty_type:
        # If duty type exists but no reasoning, show minimal note
        with st.expander("🎯 Duty Type Debug", expanded=False):
            st.write(f"🏁 **Result:** `{booking.duty_type}` (no reasoning available)")

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
    
    # API Key Configuration Section
    st.subheader("🔑 API Key Configuration")
    
    # Check for API key (from secrets or environment)
    api_key = None
    try:
        # Try Streamlit secrets first (for deployment)
        api_key = st.secrets["OPENAI_API_KEY"]
        api_key_source = "Streamlit Secrets"
    except (KeyError, FileNotFoundError):
        # Fallback to environment variable (for local development)
        api_key = os.getenv('OPENAI_API_KEY')
        api_key_source = "Environment Variable" if api_key else None
    
    # Provide UI option to enter API key
    col_key1, col_key2 = st.columns([2, 1])
    
    with col_key1:
        if api_key:
            st.success(f"✅ OpenAI API key found in {api_key_source}")
            use_existing_key = st.checkbox("Use existing API key", value=True, key="use_existing_api_key")
            if not use_existing_key:
                api_key = st.text_input(
                    "Enter OpenAI API key:",
                    type="password",
                    help="Enter your OpenAI API key for AI-powered extraction",
                    key="manual_api_key"
                )
        else:
            st.warning("⚠️ No OpenAI API key found in secrets or environment")
            
            # Offer options
            key_option = st.radio(
                "Choose your preferred option:",
                [
                    "Continue with basic extraction (no AI)",
                    "Enter API key manually", 
                    "Set up API key in environment"
                ],
                key="api_key_option"
            )
            
            if key_option == "Enter API key manually":
                api_key = st.text_input(
                    "Enter OpenAI API key:",
                    type="password",
                    help="Enter your OpenAI API key for AI-powered extraction",
                    key="manual_api_key"
                )
            elif key_option == "Set up API key in environment":
                with st.expander("📝 How to set up API key", expanded=False):
                    st.markdown("""
                    **For local development:**
                    1. Create a `.env` file in your project directory
                    2. Add: `OPENAI_API_KEY=your_api_key_here`
                    3. Restart the application
                    
                    **For Streamlit Cloud deployment:**
                    1. Go to your app settings in Streamlit Cloud
                    2. Add `OPENAI_API_KEY` in the secrets section
                    3. Redeploy your application
                    """)
    
    with col_key2:
        if api_key:
            st.info("🤖 AI-powered extraction enabled")
        else:
            st.info("📝 Basic extraction mode")
    
    # Set the API key in environment for the agents to use
    if api_key:
        os.environ['OPENAI_API_KEY'] = api_key
    
    st.markdown("---")
    
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
    
    # Initialize Enhanced Form processor
    enhanced_form_processor = None
    try:
        from enhanced_form_processor import EnhancedFormProcessor
        enhanced_form_processor = EnhancedFormProcessor(openai_api_key=api_key)
        if hasattr(enhanced_form_processor, 'textract_available') and enhanced_form_processor.textract_available:
            st.success("📋 Enhanced Form Processing is available! (FORMS + TABLES extraction with Textract)")
        else:
            st.warning("⚠️ Enhanced form processor available but AWS not configured")
            enhanced_form_processor = None
    except ImportError as e:
        st.warning(f"⚠️ Enhanced form processing not available: Missing dependencies")
    except Exception as e:
        st.warning(f"⚠️ Enhanced form processor initialization failed: {str(e)}")
    
    # Initialize Multi-Booking processor
    multi_booking_processor = None
    try:
        from enhanced_multi_booking_processor import EnhancedMultiBookingProcessor
        multi_booking_processor = EnhancedMultiBookingProcessor(aws_region='ap-south-1', openai_api_key=api_key)
        if hasattr(multi_booking_processor, 'textract_available') and multi_booking_processor.textract_available:
            st.success("📊 Multi-Booking Table Processing is available! (Complex table layouts with multiple bookings)")
        else:
            st.warning("⚠️ Multi-booking processor available but AWS not configured")
            multi_booking_processor = None
    except ImportError as e:
        st.warning(f"⚠️ Multi-booking processing not available: Missing dependencies")
    except Exception as e:
        st.warning(f"⚠️ Multi-booking processor initialization failed: {str(e)}")
    
    # Create tabs based on available processors
    tabs_list = ["Email Processing", "Classification"]
    if document_processor:
        tabs_list.append("Document Processing (S3+Textract)")
    if docx_processor:
        tabs_list.append("Word Document Processing")
    if flight_processor:
        tabs_list.append("Flight Details Processing")
    if enhanced_form_processor:
        tabs_list.append("Enhanced Form Processing")
    if multi_booking_processor:
        tabs_list.append("Multi-Booking Tables")
    
    if len(tabs_list) > 1:
        tabs = st.tabs(tabs_list)
        tab1 = tabs[0]  # Email Processing
        tab_classification = tabs[1]  # Classification (always second tab)
        
        # Assign remaining tabs based on availability
        tab_idx = 2
        tab2 = tabs[tab_idx] if document_processor else None  # Document Processing
        if document_processor:
            tab_idx += 1
        
        tab3 = tabs[tab_idx] if docx_processor else None  # Word Document Processing  
        if docx_processor:
            tab_idx += 1
            
        tab4 = tabs[tab_idx] if flight_processor else None  # Flight Details Processing
        if flight_processor:
            tab_idx += 1
        
        tab5 = tabs[tab_idx] if enhanced_form_processor else None  # Enhanced Form Processing
        if enhanced_form_processor:
            tab_idx += 1
        
        tab6 = tabs[tab_idx] if multi_booking_processor else None  # Multi-Booking Tables
    else:
        # Single email processing interface
        tab1 = st.container()
        tab_classification = None
        tab2 = None
        tab3 = None
        tab4 = None
        tab5 = None
        tab6 = None

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
    
    # Classification Tab
    if tab_classification:
        with tab_classification:
            st.subheader("🎯 Booking Classification")
            st.markdown("**Predict how many bookings will be created from your content**")
            st.info("📊 This agent analyzes text, images, or PDFs to predict single vs multiple bookings based on your business rules.")
            
            # Initialize classification agent
            try:
                from booking_classification_agent import BookingClassificationAgent
                # Check for OpenAI API key
                openai_api_key = os.getenv('OPENAI_API_KEY')
                classifier = BookingClassificationAgent(openai_api_key=openai_api_key)
                
                # Show classification agent status
                if classifier.ai_available:
                    st.success("🤖 AI-powered classification enabled (OpenAI GPT-4o-mini)")
                else:
                    st.warning("⚠️ Using fallback pattern matching (no OpenAI API key found)")
                    
            except ImportError:
                st.error("❌ Classification agent not available")
                st.stop()
            
            # Create sub-tabs for different input types
            class_tabs = st.tabs(["📝 Text Classification", "🖼️ Image Classification", "📄 PDF Classification"])
            
            # Text Classification Tab
            with class_tabs[0]:
                st.subheader("📝 Text Content Classification")
                
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    st.markdown("**📋 Paste Your Content**")
                    text_content = st.text_area(
                        "Enter text content to classify:",
                        height=300,
                        placeholder="Example:\n\nNeed cab for outstation trip from Delhi to Gurgaon for 3 days.\nOR\nNeed 2 drops today - one at 9 AM to airport and another at 6 PM to hotel.",
                        key="text_classification_input"
                    )
                    
                    col_btn1, col_btn2 = st.columns(2)
                    with col_btn1:
                        classify_text_btn = st.button("🎯 Classify Text", type="primary", use_container_width=True, key="classify_text")
                    with col_btn2:
                        clear_text_btn = st.button("🗑️ Clear", use_container_width=True, key="clear_text_classification")
                
                with col2:
                    st.markdown("**📊 Classification Result**")
                    
                    # Initialize session state for text classification
                    if 'text_classification_result' not in st.session_state:
                        st.session_state.text_classification_result = None
                    if 'text_classification_done' not in st.session_state:
                        st.session_state.text_classification_done = False
                    
                    # Clear functionality
                    if clear_text_btn:
                        st.session_state.text_classification_result = None
                        st.session_state.text_classification_done = False
                        st.rerun()
                    
                    # Classify text
                    if classify_text_btn and text_content.strip():
                        with st.spinner("🤖 Analyzing text content..."):
                            try:
                                result = classifier.classify_text_content(text_content.strip())
                                st.session_state.text_classification_result = result
                                st.session_state.text_classification_done = True
                            except Exception as e:
                                st.error(f"❌ Classification failed: {str(e)}")
                                st.session_state.text_classification_result = None
                                st.session_state.text_classification_done = False
                    
                    elif classify_text_btn and not text_content.strip():
                        st.warning("⚠️ Please enter some text content first.")
                    
                    # Display classification results
                    if st.session_state.text_classification_done and st.session_state.text_classification_result:
                        result = st.session_state.text_classification_result
                        
                        # Main result display
                        col_res1, col_res2, col_res3 = st.columns(3)
                        with col_res1:
                            st.metric("📊 Predicted Bookings", result.predicted_booking_count)
                        with col_res2:
                            booking_icon = "🔀" if result.booking_type == "multiple" else "📋"
                            st.metric(f"{booking_icon} Type", result.booking_type.title())
                        with col_res3:
                            confidence_color = "🟢" if result.confidence_score > 0.8 else "🟡" if result.confidence_score > 0.6 else "🔴"
                            st.metric(f"{confidence_color} Confidence", f"{result.confidence_score:.1%}")
                        
                        # Reasoning
                        st.markdown("**🧠 Analysis Reasoning:**")
                        st.info(result.reasoning)
                        
                        # Additional details in expandable section
                        with st.expander("🔍 Detailed Analysis", expanded=False):
                            if result.duty_type_indicators:
                                st.write(f"**🚗 Duty Type Indicators:** {', '.join(result.duty_type_indicators)}")
                            if result.date_patterns:
                                st.write(f"**📅 Date Patterns:** {', '.join(result.date_patterns)}")
                            if result.detected_patterns:
                                st.write("**🔍 Detected Patterns:**")
                                for pattern in result.detected_patterns:
                                    st.write(f"• {pattern}")
                            if result.additional_info:
                                st.write(f"**ℹ️ Additional Info:** {result.additional_info}")
                    
                    elif not st.session_state.text_classification_done:
                        st.info("👈 Enter text content and click 'Classify Text' to see predictions here.")
            
            # Image Classification Tab
            with class_tabs[1]:
                st.subheader("🖼️ Image Content Classification")
                
                if not document_processor:
                    st.warning("⚠️ Image classification requires Document Processing (S3+Textract) to be available.")
                else:
                    uploaded_image = st.file_uploader(
                        "Choose an image file:",
                        type=['jpg', 'jpeg', 'png', 'gif'],
                        help="Upload images containing booking information (screenshots, forms, tables)",
                        key="image_classification_uploader"
                    )
                    
                    if uploaded_image is not None:
                        # Display image info
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("📄 File Name", uploaded_image.name)
                        with col2:
                            st.metric("📊 File Size", f"{uploaded_image.size / 1024:.1f} KB")
                        with col3:
                            st.metric("🔖 File Type", uploaded_image.type)
                        
                        # Show image preview
                        st.image(uploaded_image, caption="Uploaded Image", use_column_width=True)
                        
                        # Classify button
                        if st.button("🎯 Classify Image", type="primary", key="classify_image"):
                            # Validate file
                            is_valid, validation_message = document_processor.validate_file(
                                uploaded_image.name, 
                                uploaded_image.size
                            )
                            
                            if not is_valid:
                                st.error(f"❌ {validation_message}")
                            else:
                                with st.spinner("🤖 Processing image with S3 + Textract + Classification..."):
                                    try:
                                        # Get file content
                                        file_content = uploaded_image.read()
                                        file_type = uploaded_image.name.split('.')[-1].lower()
                                        
                                        # Check if multi-booking processor is available for table detection
                                        if multi_booking_processor:
                                            # Use multi-booking processor for better table detection
                                            result = multi_booking_processor.process_multi_booking_document(
                                                file_content, uploaded_image.name, file_type
                                            )
                                            
                                            # Classify based on actual extraction results
                                            classification_result = classifier.classify_from_extraction_result(result)
                                            
                                            # Display results
                                            st.success(f"✅ Image classification completed!")
                                            
                                            # Show classification results
                                            col_res1, col_res2, col_res3 = st.columns(3)
                                            with col_res1:
                                                st.metric("📊 Predicted Bookings", classification_result.predicted_booking_count)
                                            with col_res2:
                                                booking_icon = "🔀" if classification_result.booking_type == "multiple" else "📋"
                                                st.metric(f"{booking_icon} Type", classification_result.booking_type.title())
                                            with col_res3:
                                                confidence_color = "🟢" if classification_result.confidence_score > 0.8 else "🟡" if classification_result.confidence_score > 0.6 else "🔴"
                                                st.metric(f"{confidence_color} Confidence", f"{classification_result.confidence_score:.1%}")
                                            
                                            st.info(f"**🧠 Analysis:** {classification_result.reasoning}")
                                            
                                            # Show DataFrame if multiple bookings detected
                                            if result.total_bookings_found > 1:
                                                from streamlit_multi_booking_app import bookings_to_dataframe
                                                df = bookings_to_dataframe(result.bookings)
                                                st.subheader(f"📊 Detected Bookings ({len(df)} rows)")
                                                st.dataframe(df, use_container_width=True)
                                            
                                            # Show detailed analysis
                                            with st.expander("🔍 Detailed Analysis", expanded=False):
                                                st.write(f"**📋 Actual Bookings Found:** {result.total_bookings_found}")
                                                if classification_result.additional_info:
                                                    st.write(f"**ℹ️ Additional Info:** {classification_result.additional_info}")
                                                if result.processing_notes:
                                                    st.write(f"**🔧 Processing Notes:** {result.processing_notes}")
                                        
                                        else:
                                            # Fallback to regular document processing
                                            result = document_processor.process_document(
                                                file_content, uploaded_image.name, file_type
                                            )
                                            
                                            # Classify based on extraction results
                                            classification_result = classifier.classify_from_extraction_result(result)
                                            
                                            # Display results
                                            st.success(f"✅ Image classification completed!")
                                            
                                            col_res1, col_res2, col_res3 = st.columns(3)
                                            with col_res1:
                                                st.metric("📊 Predicted Bookings", classification_result.predicted_booking_count)
                                            with col_res2:
                                                booking_icon = "🔀" if classification_result.booking_type == "multiple" else "📋"
                                                st.metric(f"{booking_icon} Type", classification_result.booking_type.title())
                                            with col_res3:
                                                confidence_color = "🟢" if classification_result.confidence_score > 0.8 else "🟡" if classification_result.confidence_score > 0.6 else "🔴"
                                                st.metric(f"{confidence_color} Confidence", f"{classification_result.confidence_score:.1%}")
                                            
                                            st.info(f"**🧠 Analysis:** {classification_result.reasoning}")
                                    
                                    except Exception as e:
                                        st.error(f"❌ Image classification failed: {str(e)}")
                    else:
                        st.info("📤 Please upload an image file to begin classification.")
            
            # PDF Classification Tab
            with class_tabs[2]:
                st.subheader("📄 PDF Content Classification")
                
                if not document_processor:
                    st.warning("⚠️ PDF classification requires Document Processing (S3+Textract) to be available.")
                else:
                    uploaded_pdf = st.file_uploader(
                        "Choose a PDF file:",
                        type=['pdf'],
                        help="Upload PDF files containing booking information (forms, tables, email screenshots)",
                        key="pdf_classification_uploader"
                    )
                    
                    if uploaded_pdf is not None:
                        # Display PDF info
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("📄 File Name", uploaded_pdf.name)
                        with col2:
                            st.metric("📊 File Size", f"{uploaded_pdf.size / 1024:.1f} KB")
                        with col3:
                            st.metric("🔖 File Type", uploaded_pdf.type)
                        
                        # Classify button
                        if st.button("🎯 Classify PDF", type="primary", key="classify_pdf"):
                            # Validate file
                            is_valid, validation_message = document_processor.validate_file(
                                uploaded_pdf.name, 
                                uploaded_pdf.size
                            )
                            
                            if not is_valid:
                                st.error(f"❌ {validation_message}")
                            else:
                                with st.spinner("🤖 Processing PDF with S3 + Textract + Classification..."):
                                    try:
                                        # Get file content
                                        file_content = uploaded_pdf.read()
                                        file_type = 'pdf'
                                        
                                        # Check if multi-booking processor is available for table detection
                                        if multi_booking_processor:
                                            # Use multi-booking processor for better table detection
                                            result = multi_booking_processor.process_multi_booking_document(
                                                file_content, uploaded_pdf.name, file_type
                                            )
                                            
                                            # Classify based on actual extraction results
                                            classification_result = classifier.classify_from_extraction_result(result)
                                            
                                            # Display results
                                            st.success(f"✅ PDF classification completed!")
                                            
                                            # Show classification results
                                            col_res1, col_res2, col_res3 = st.columns(3)
                                            with col_res1:
                                                st.metric("📊 Predicted Bookings", classification_result.predicted_booking_count)
                                            with col_res2:
                                                booking_icon = "🔀" if classification_result.booking_type == "multiple" else "📋"
                                                st.metric(f"{booking_icon} Type", classification_result.booking_type.title())
                                            with col_res3:
                                                confidence_color = "🟢" if classification_result.confidence_score > 0.8 else "🟡" if classification_result.confidence_score > 0.6 else "🔴"
                                                st.metric(f"{confidence_color} Confidence", f"{classification_result.confidence_score:.1%}")
                                            
                                            st.info(f"**🧠 Analysis:** {classification_result.reasoning}")
                                            
                                            # Show DataFrame if multiple bookings detected
                                            if result.total_bookings_found > 1:
                                                from streamlit_multi_booking_app import bookings_to_dataframe
                                                df = bookings_to_dataframe(result.bookings)
                                                st.subheader(f"📊 Detected Bookings ({len(df)} rows)")
                                                st.dataframe(df, use_container_width=True)
                                            
                                            # Show detailed analysis
                                            with st.expander("🔍 Detailed Analysis", expanded=False):
                                                st.write(f"**📋 Actual Bookings Found:** {result.total_bookings_found}")
                                                if classification_result.additional_info:
                                                    st.write(f"**ℹ️ Additional Info:** {classification_result.additional_info}")
                                                if result.processing_notes:
                                                    st.write(f"**🔧 Processing Notes:** {result.processing_notes}")
                                        
                                        else:
                                            # Fallback to regular document processing
                                            result = document_processor.process_document(
                                                file_content, uploaded_pdf.name, file_type
                                            )
                                            
                                            # Classify based on extraction results
                                            classification_result = classifier.classify_from_extraction_result(result)
                                            
                                            # Display results
                                            st.success(f"✅ PDF classification completed!")
                                            
                                            col_res1, col_res2, col_res3 = st.columns(3)
                                            with col_res1:
                                                st.metric("📊 Predicted Bookings", classification_result.predicted_booking_count)
                                            with col_res2:
                                                booking_icon = "🔀" if classification_result.booking_type == "multiple" else "📋"
                                                st.metric(f"{booking_icon} Type", classification_result.booking_type.title())
                                            with col_res3:
                                                confidence_color = "🟢" if classification_result.confidence_score > 0.8 else "🟡" if classification_result.confidence_score > 0.6 else "🔴"
                                                st.metric(f"{confidence_color} Confidence", f"{classification_result.confidence_score:.1%}")
                                            
                                            st.info(f"**🧠 Analysis:** {classification_result.reasoning}")
                                    
                                    except Exception as e:
                                        st.error(f"❌ PDF classification failed: {str(e)}")
                    else:
                        st.info("📤 Please upload a PDF file to begin classification.")
            
            # Business Rules Information
            st.markdown("---")
            st.subheader("📋 Classification Business Rules")
            
            col_rules1, col_rules2 = st.columns(2)
            
            with col_rules1:
                st.markdown("""
                **📋 Single Booking Scenarios:**
                - ✅ 8/80 or outstation package for consecutive days
                - ✅ Single 4/40 drop in a day
                - ✅ Same car type for entire duration
                - ✅ Continuous multi-day travel
                """)
            
            with col_rules2:
                st.markdown("""
                **🔀 Multiple Booking Scenarios:**
                - ✅ Two or more drops in same day
                - ✅ 8/80 for alternate (non-consecutive) days
                - ✅ Different car types on different days
                - ✅ Tables with multiple rows/columns
                """)
    
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

    # Tab 5: Enhanced Form Processing (if available)
    if tab5 and enhanced_form_processor:
        with tab5:
            st.subheader("📋 Enhanced Form Processing")
            st.info("🚀 This processor uses AWS Textract's FORMS feature to extract key-value pairs from structured documents like travel requisition forms.")
            
            # File uploader for forms
            uploaded_form = st.file_uploader(
                "Choose a form image (JPG, PNG, GIF) or PDF:",
                type=['jpg', 'jpeg', 'png', 'gif', 'pdf'],
                key="form_uploader"
            )
            
            if uploaded_form is not None:
                # Display file info
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("📄 File Name", uploaded_form.name)
                with col2:
                    st.metric("📊 File Size", f"{uploaded_form.size / 1024:.1f} KB")
                with col3:
                    st.metric("🔖 File Type", uploaded_form.type)
                
                # Process button
                if st.button("🔍 Extract Form Data", type="primary", key="form_extract"):
                    # Validate file
                    is_valid, validation_message = enhanced_form_processor.validate_file(
                        uploaded_form.name, 
                        uploaded_form.size
                    )
                    
                    if not is_valid:
                        st.error(f"❌ {validation_message}")
                    else:
                        with st.spinner("🤖 Processing form with enhanced Textract + AI..."):
                            try:
                                # Get file content
                                file_content = uploaded_form.read()
                                file_type = uploaded_form.name.split('.')[-1].lower()
                                
                                # Process with enhanced form processor
                                result = enhanced_form_processor.process_document(
                                    file_content, 
                                    uploaded_form.name, 
                                    file_type
                                )
                                
                                # Display enhanced results
                                st.success(f"✅ Enhanced form processing completed!")
                                
                                # Enhanced extraction details
                                col1, col2, col3, col4 = st.columns(4)
                                with col1:
                                    st.metric("📋 Bookings Found", result.total_bookings_found)
                                with col2:
                                    st.metric("🎯 Confidence", f"{result.confidence_score:.1%}")
                                with col3:
                                    st.metric("⚙️ Method", result.extraction_method)
                                with col4:
                                    st.metric("🕒 Processing", "Enhanced")
                                
                                # Display structured data extraction details
                                if result.processing_notes:
                                    st.info(f"📝 {result.processing_notes}")
                                
                                # Display bookings
                                if result.total_bookings_found > 0:
                                    st.subheader("📊 Extracted Booking Information")
                                    for i, booking in enumerate(result.bookings):
                                        display_single_booking(booking, i)
                                        
                                        # Show structured data if available in additional_info
                                        if booking.additional_info and "Structured Data:" in booking.additional_info:
                                            with st.expander(f"🔍 View Structured Data for Booking {i+1}", expanded=False):
                                                # Extract and format the structured data
                                                import json
                                                try:
                                                    # Find the JSON part in additional_info
                                                    info_parts = booking.additional_info.split("Structured Data: ")
                                                    if len(info_parts) > 1:
                                                        json_str = info_parts[1].strip()
                                                        structured_data = json.loads(json_str)
                                                        
                                                        # Display key-value pairs
                                                        if structured_data.get('key_value_pairs'):
                                                            st.write("**📋 Form Fields:**")
                                                            for kv in structured_data['key_value_pairs']:
                                                                st.write(f"• **{kv['key']}**: {kv['value']}")
                                                        
                                                        # Display tables
                                                        if structured_data.get('tables'):
                                                            for j, table in enumerate(structured_data['tables']):
                                                                st.write(f"**📊 Table {j+1} ({table['type']})**")
                                                                if table['type'] == 'form_table' and table.get('key_value_pairs'):
                                                                    for kv in table['key_value_pairs']:
                                                                        st.write(f"• **{kv['key']}**: {kv['value']}")
                                                except json.JSONDecodeError:
                                                    st.text(booking.additional_info)
                                    
                                    # Save to Google Sheets option
                                    if sheets_success:
                                        if st.button("💾 Save to Google Sheets", key="form_save_sheets"):
                                            success, result_info = save_extraction_results_to_sheets(result)
                                            if success:
                                                total_saved, bookings_processed = result_info
                                                st.success(f"✅ Successfully saved {bookings_processed} booking(s) to Google Sheets! Total rows: {total_saved}")
                                                st.balloons()
                                            else:
                                                st.error(f"❌ Failed to save to Google Sheets: {result_info}")
                                    
                                else:
                                    st.warning("⚠️ No booking information could be extracted from this form.")
                                    
                                    # Show raw extracted text for debugging
                                    if hasattr(result, 'bookings') and result.bookings:
                                        first_booking = result.bookings[0]
                                        if first_booking.additional_info:
                                            with st.expander("🔍 View Raw Extracted Content", expanded=False):
                                                st.text(first_booking.additional_info)
                            
                            except Exception as e:
                                st.error(f"❌ Enhanced form processing failed: {str(e)}")
                                import traceback
                                st.text(traceback.format_exc())
            
            else:
                st.info("📤 Please upload a form document to begin enhanced processing.")
                
                # Show processing comparison
                st.subheader("🔄 Enhanced vs Standard Processing")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("""
                    **🚀 Enhanced Form Processing:**
                    - ✅ Uses Textract FORMS feature for key-value extraction
                    - ✅ Proper table structure preservation
                    - ✅ Maps field labels to values correctly
                    - ✅ Handles form-like tables (2-column key-value pairs)
                    - ✅ Better accuracy for structured documents
                    """)
                
                with col2:
                    st.markdown("""
                    **📄 Standard Processing:**
                    - ⚠️ Uses only TABLES feature
                    - ⚠️ May lose key-value relationships
                    - ⚠️ Sequential text extraction
                    - ⚠️ Headers might be captured instead of values
                    - ⚠️ Less accurate for forms
                    """)

    # Tab 6: Multi-Booking Table Processing (if available)
    if tab6 and multi_booking_processor:
        with tab6:
            st.subheader("📊 Multi-Booking Table Extraction")
            st.info("🚀 Extract multiple bookings from complex table layouts (vertical/horizontal formats) with DataFrame display.")
            
            # Import the multi-booking tab functionality
            try:
                from streamlit_multi_booking_app import (
                    bookings_to_dataframe, 
                    display_extraction_summary,
                    display_detailed_bookings
                )
                
                # File uploader for multi-booking tables
                uploaded_multi_file = st.file_uploader(
                    "Choose a file with multiple bookings (PDF, JPG, PNG, GIF):",
                    type=['pdf', 'jpg', 'jpeg', 'png', 'gif'],
                    help="Upload images or PDFs containing tables with multiple booking information",
                    key="multi_booking_tab_uploader"
                )
                
                if uploaded_multi_file is not None:
                    # Display file info
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("📄 File Name", uploaded_multi_file.name)
                    with col2:
                        st.metric("📊 File Size", f"{uploaded_multi_file.size / 1024:.1f} KB")
                    with col3:
                        st.metric("🔖 File Type", uploaded_multi_file.type)
                    
                    # Process button
                    if st.button("🔍 Extract All Bookings from Table", type="primary", key="multi_extract_tab"):
                        # Validate file
                        is_valid, validation_message = multi_booking_processor.validate_file(
                            uploaded_multi_file.name, 
                            uploaded_multi_file.size
                        )
                        
                        if not is_valid:
                            st.error(f"❌ {validation_message}")
                        else:
                            with st.spinner("🤖 Extracting multiple bookings from table..."):
                                try:
                                    from datetime import datetime
                                    start_time = datetime.now()
                                    
                                    # Get file content
                                    file_content = uploaded_multi_file.read()
                                    file_type = uploaded_multi_file.name.split('.')[-1].lower()
                                    
                                    # Process with multi-booking processor
                                    result = multi_booking_processor.process_multi_booking_document(
                                        file_content, 
                                        uploaded_multi_file.name, 
                                        file_type
                                    )
                                    
                                    processing_time = (datetime.now() - start_time).total_seconds()
                                    
                                    # Display results
                                    st.success(f"✅ Multi-booking extraction completed!")
                                    
                                    # Summary metrics
                                    display_extraction_summary(result, processing_time)
                                    
                                    if result.total_bookings_found > 0:
                                        # Convert to DataFrame and display
                                        df = bookings_to_dataframe(result.bookings)
                                        
                                        st.subheader("📊 Extracted Bookings DataFrame")
                                        st.markdown("**Dynamic table showing all extracted bookings:**")
                                        
                                        # Display the DataFrame with enhanced formatting
                                        st.dataframe(
                                            df,
                                            use_container_width=True,
                                            height=min(600, (len(df) + 1) * 35),
                                            column_config={
                                                "Booking #": st.column_config.NumberColumn("Booking #", width="small"),
                                                "Passenger Name": st.column_config.TextColumn("Passenger Name", width="medium"),
                                                "Phone Number": st.column_config.TextColumn("Phone Number", width="medium"),
                                                "Company": st.column_config.TextColumn("Company", width="medium"),
                                                "Travel Date": st.column_config.TextColumn("Travel Date", width="medium"),
                                                "Vehicle Type": st.column_config.TextColumn("Vehicle Type", width="medium"),
                                                "Duty Type": st.column_config.TextColumn("Duty Type", width="medium"),
                                                "Confidence": st.column_config.TextColumn("Confidence", width="small"),
                                            }
                                        )
                                        
                                        # Download options
                                        st.subheader("💾 Download Extracted Data")
                                        
                                        col1, col2, col3 = st.columns(3)
                                        
                                        with col1:
                                            # CSV download
                                            csv = df.to_csv(index=False)
                                            st.download_button(
                                                label="📥 Download CSV",
                                                data=csv,
                                                file_name=f"multi_bookings_{uploaded_multi_file.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                                mime="text/csv"
                                            )
                                        
                                        with col2:
                                            # Excel download
                                            import io
                                            buffer = io.BytesIO()
                                            df.to_excel(buffer, index=False, engine='openpyxl')
                                            excel_data = buffer.getvalue()
                                            
                                            st.download_button(
                                                label="📊 Download Excel",
                                                data=excel_data,
                                                file_name=f"multi_bookings_{uploaded_multi_file.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                                            )
                                        
                                        with col3:
                                            # JSON download
                                            import json
                                            json_data = []
                                            for booking in result.bookings:
                                                json_data.append({
                                                    'passenger_name': booking.passenger_name,
                                                    'passenger_phone': booking.passenger_phone,
                                                    'corporate': booking.corporate,
                                                    'start_date': booking.start_date,
                                                    'reporting_time': booking.reporting_time,
                                                    'vehicle_group': booking.vehicle_group,
                                                    'from_location': booking.from_location,
                                                    'to_location': booking.to_location,
                                                    'reporting_address': booking.reporting_address,
                                                    'drop_address': booking.drop_address,
                                                    'flight_train_number': booking.flight_train_number,
                                                    'duty_type': booking.duty_type,
                                                    'remarks': booking.remarks,
                                                    'confidence_score': booking.confidence_score
                                                })
                                            
                                            json_str = json.dumps(json_data, indent=2)
                                            st.download_button(
                                                label="📄 Download JSON",
                                                data=json_str,
                                                file_name=f"multi_bookings_{uploaded_multi_file.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                                                mime="application/json"
                                            )
                                        
                                        # Detailed bookings view
                                        display_detailed_bookings(result.bookings)
                                        
                                        # Save to Google Sheets option
                                        if sheets_success:
                                            st.subheader("☁️ Google Sheets Integration")
                                            if st.button("💾 Save All Bookings to Google Sheets", key="multi_tab_save_sheets"):
                                                success, result_info = save_extraction_results_to_sheets(result)
                                                if success:
                                                    total_saved, bookings_processed = result_info
                                                    st.success(f"✅ Successfully saved {bookings_processed} booking(s) to Google Sheets! Total rows: {total_saved}")
                                                    st.balloons()
                                                else:
                                                    st.error(f"❌ Failed to save to Google Sheets: {result_info}")
                                    
                                    else:
                                        st.warning("⚠️ No bookings could be extracted from this table.")
                                        
                                        # Show debug information
                                        with st.expander("🔍 Debug Information", expanded=False):
                                            st.text(f"Method: {result.extraction_method}")
                                            st.text(f"Notes: {result.processing_notes}")
                                
                                except Exception as e:
                                    st.error(f"❌ Multi-booking extraction failed: {str(e)}")
                                    import traceback
                                    with st.expander("🔍 Error Details", expanded=False):
                                        st.text(traceback.format_exc())
                
                else:
                    st.info("📤 Please upload a document containing multiple bookings in table format.")
                    
                    # Show supported formats
                    st.subheader("📋 Supported Multi-Booking Table Formats")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("""
                        **📋 Vertical Layout (Key-Value):**
                        - Date & City / Car → Travel dates
                        - Pick up – Time → Reporting times  
                        - Global Leaders → Passenger names
                        - Pick up Address → Source locations
                        - Drop address → Destinations
                        """)
                    
                    with col2:
                        st.markdown("""
                        **📊 Horizontal Layout (Columns):**
                        - Cab 1, Cab 2, Cab 3... → Individual bookings
                        - Field Names → Row headers
                        - Each column = One complete booking
                        - Handles 4+ bookings in single table
                        """)
                    
                    # Features comparison
                    st.subheader("🆚 Multi-Booking vs Single Booking")
                    
                    feature_col1, feature_col2 = st.columns(2)
                    
                    with feature_col1:
                        st.markdown("""
                        **📊 Multi-Booking Processing:**
                        - ✅ Extracts multiple bookings per document
                        - ✅ Handles complex table layouts
                        - ✅ Dynamic DataFrame display
                        - ✅ Bulk download options (CSV/Excel/JSON)
                        - ✅ Perfect for team travel schedules
                        """)
                    
                    with feature_col2:
                        st.markdown("""
                        **📋 Single Booking Processing:**
                        - ✅ Extracts one booking per document
                        - ✅ Simple form processing
                        - ✅ Detailed individual analysis
                        - ✅ Perfect for individual travel requests
                        - ✅ Enhanced duty type detection
                        """)
            
            except ImportError as e:
                st.error(f"❌ Could not load multi-booking functionality: {str(e)}")
                st.info("Please ensure all required dependencies are installed.")

if __name__ == "__main__":
    main()
