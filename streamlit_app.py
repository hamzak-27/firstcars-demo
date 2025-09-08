#!/usr/bin/env python3
"""
FirstCars Demo Tool - Streamlit Frontend
A user-friendly interface for the Car Rental AI Agent
"""

import streamlit as st
import pandas as pd
import os
from datetime import datetime
import json

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    st.error("python-dotenv not installed. Install with: pip install python-dotenv")

from car_rental_ai_agent import CarRentalAIAgent, BookingExtraction
from google_sheets_integration import sheets_manager
from datetime import datetime, timedelta

# Google Sheets configuration
GOOGLE_SHEETS_URL = "https://docs.google.com/spreadsheets/d/1zz1xkvI0-XCkU23eBfSW9jSLK--UfCU94iT-poEkf_E/edit#gid=0"

def test_google_sheets_connection():
    """Test Google Sheets connection and show status"""
    success, message = sheets_manager.test_connection()
    return success, message

def create_multiple_bookings_if_needed(booking):
    """Create multiple booking entries if the request spans multiple dates"""
    if not booking.start_date or not booking.end_date:
        return [booking]  # Return single booking if dates are missing
    
    try:
        start_date = datetime.strptime(booking.start_date, '%Y-%m-%d')
        end_date = datetime.strptime(booking.end_date, '%Y-%m-%d')
        
        # If same date, return single booking
        if start_date == end_date:
            return [booking]
        
        # Create multiple bookings for each date
        bookings = []
        current_date = start_date
        
        while current_date <= end_date:
            # Create a copy of the original booking
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
                end_date=current_date.strftime('%Y-%m-%d'),  # Single day booking
                reporting_time=booking.reporting_time,
                drop_time=booking.drop_time,
                start_from_garage=booking.start_from_garage,
                reporting_address=booking.reporting_address,
                drop_address=booking.drop_address,
                flight_train_number=booking.flight_train_number,
                dispatch_center=booking.dispatch_center,
                bill_to=booking.bill_to,
                price=booking.price,
                remarks=booking.remarks,
                labels=booking.labels,
                confidence_score=booking.confidence_score,
                extraction_reasoning=booking.extraction_reasoning
            )
            
            bookings.append(new_booking)
            current_date += timedelta(days=1)
        
        return bookings
        
    except (ValueError, AttributeError):
        # If date parsing fails, return original booking
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

def display_extracted_data(booking):
    """Display extracted data in a clean format"""
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
        if booking.drop_time:
            st.write(f"**Drop Time:** {booking.drop_time}")
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
            extract_btn = st.button("🔍 Extract Data", type="primary", use_container_width=True)
        with col_btn2:
            clear_btn = st.button("🗑️ Clear", use_container_width=True)
    
    with col2:
        st.subheader("📊 Results")
        
        # Initialize session state
        if 'booking_data' not in st.session_state:
            st.session_state.booking_data = None
        if 'extraction_done' not in st.session_state:
            st.session_state.extraction_done = False
        
        # Clear functionality
        if clear_btn:
            st.session_state.booking_data = None
            st.session_state.extraction_done = False
            st.rerun()
        
        # Extract data
        if extract_btn and email_content.strip():
            with st.spinner("🤖 Processing email with AI..."):
                try:
                    agent = CarRentalAIAgent()
                    booking = agent.extract_booking_data(email_content.strip())
                    st.session_state.booking_data = booking
                    st.session_state.extraction_done = True
                except Exception as e:
                    st.error(f"❌ Extraction failed: {str(e)}")
                    st.session_state.booking_data = None
                    st.session_state.extraction_done = False
        
        elif extract_btn and not email_content.strip():
            st.warning("⚠️ Please enter email content first.")
        
        # Display results
        if st.session_state.extraction_done and st.session_state.booking_data:
            display_extracted_data(st.session_state.booking_data)
            
            # Check if this will create multiple bookings
            multiple_bookings = create_multiple_bookings_if_needed(st.session_state.booking_data)
            num_bookings = len(multiple_bookings)
            
            # Save to Excel button
            st.markdown("---")
            if num_bookings > 1:
                st.info(f"📅 This booking spans {num_bookings} days and will create {num_bookings} separate Google Sheets rows.")
                button_text = f"💾 Save {num_bookings} Bookings to Google Sheets"
            else:
                button_text = "💾 Save to Google Sheets"
            
            if st.button(button_text, type="secondary", use_container_width=True):
                if not sheets_success:
                    st.error("❌ Cannot save: Google Sheets connection failed. Please check your credentials.")
                else:
                    with st.spinner("Saving to Google Sheets..."):
                        success, result = save_to_google_sheets(st.session_state.booking_data)
                if success:
                    total_records, bookings_added = result
                    if bookings_added > 1:
                        st.success(f"✅ Saved {bookings_added} bookings successfully! Total records: {total_records}")
                    else:
                        st.success(f"✅ Saved successfully! Total records: {total_records}")
                else:
                    st.error(f"❌ Save failed: {result}")
        
        elif not st.session_state.extraction_done:
            st.info("👈 Enter email content and click 'Extract Data' to see results here.")
    
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
