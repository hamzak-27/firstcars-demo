"""
Streamlit Multi-Booking Table Extraction App
Extracts multiple bookings from table images/PDFs and displays in DataFrame format
"""

import streamlit as st
import pandas as pd
import os
import json
import logging
from typing import List, Dict, Any
from datetime import datetime
import traceback

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def initialize_multi_booking_processor():
    """Initialize the multi-booking processor"""
    try:
        from enhanced_multi_booking_processor import EnhancedMultiBookingProcessor
        
        # Get API key
        api_key = None
        try:
            api_key = st.secrets["OPENAI_API_KEY"]
        except (KeyError, FileNotFoundError):
            api_key = os.getenv('OPENAI_API_KEY')
        
        if not api_key:
            st.error("❌ OpenAI API key not found. Please configure it in Streamlit secrets or .env file.")
            return None
        
        processor = EnhancedMultiBookingProcessor(openai_api_key=api_key)
        
        if not processor.textract_available:
            st.warning("⚠️ AWS Textract not available. Please configure AWS credentials.")
            return None
        
        return processor
    
    except ImportError as e:
        st.error(f"❌ Could not import multi-booking processor: {str(e)}")
        return None
    except Exception as e:
        st.error(f"❌ Failed to initialize multi-booking processor: {str(e)}")
        return None

def bookings_to_dataframe(bookings: List) -> pd.DataFrame:
    """Convert booking extractions to pandas DataFrame"""
    if not bookings:
        return pd.DataFrame()
    
    # Define the columns we want to display
    columns = [
        'Booking #',
        'Passenger Name',
        'Phone Number',
        'Company',
        'Travel Date',
        'Pickup Time',
        'Vehicle Type',
        'From Location',
        'To Location', 
        'Pickup Address',
        'Drop Address',
        'Flight Details',
        'Duty Type',
        'Remarks',
        'Confidence'
    ]
    
    # Extract data from bookings
    data = []
    for i, booking in enumerate(bookings, 1):
        row = {
            'Booking #': i,
            'Passenger Name': booking.passenger_name or '',
            'Phone Number': booking.passenger_phone or '',
            'Company': booking.corporate or '',
            'Travel Date': booking.start_date or '',
            'Pickup Time': booking.reporting_time or '',
            'Vehicle Type': booking.vehicle_group or '',
            'From Location': booking.from_location or '',
            'To Location': booking.to_location or '',
            'Pickup Address': booking.reporting_address or '',
            'Drop Address': booking.drop_address or '',
            'Flight Details': booking.flight_train_number or '',
            'Duty Type': booking.duty_type or '',
            'Remarks': booking.remarks or '',
            'Confidence': f"{booking.confidence_score:.1%}" if booking.confidence_score else '0%'
        }
        data.append(row)
    
    return pd.DataFrame(data, columns=columns)

def display_extraction_summary(result, processing_time: float):
    """Display extraction summary with metrics"""
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="📊 Bookings Found", 
            value=result.total_bookings_found,
            help="Total number of bookings extracted from the document"
        )
    
    with col2:
        st.metric(
            label="🎯 Confidence", 
            value=f"{result.confidence_score:.1%}",
            help="Overall confidence in the extraction accuracy"
        )
    
    with col3:
        st.metric(
            label="⚙️ Method", 
            value="Multi-Booking",
            help="Extraction method used for this document"
        )
    
    with col4:
        st.metric(
            label="⏱️ Processing Time", 
            value=f"{processing_time:.1f}s",
            help="Time taken to process the document"
        )

def display_detailed_bookings(bookings: List):
    """Display detailed booking information in expandable sections"""
    
    st.subheader("📋 Detailed Booking Information")
    
    for i, booking in enumerate(bookings, 1):
        with st.expander(f"🚗 Booking {i}: {booking.passenger_name or 'Unknown Passenger'}", expanded=False):
            
            # Basic Information
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**👤 Passenger Details:**")
                st.write(f"• Name: {booking.passenger_name or 'Not specified'}")
                st.write(f"• Phone: {booking.passenger_phone or 'Not specified'}")
                st.write(f"• Email: {booking.passenger_email or 'Not specified'}")
                
                st.write("**🏢 Company Information:**")
                st.write(f"• Company: {booking.corporate or 'Not specified'}")
                
            with col2:
                st.write("**📅 Travel Details:**")
                st.write(f"• Date: {booking.start_date or 'Not specified'}")
                st.write(f"• End Date: {booking.end_date or 'Same day'}")
                st.write(f"• Pickup Time: {booking.reporting_time or 'Not specified'}")
                
                st.write("**🚗 Vehicle & Service:**")
                st.write(f"• Vehicle: {booking.vehicle_group or 'Not specified'}")
                st.write(f"• Duty Type: {booking.duty_type or 'Not specified'}")
            
            # Location Information
            st.write("**📍 Location Details:**")
            location_col1, location_col2 = st.columns(2)
            
            with location_col1:
                st.write(f"• From: {booking.from_location or 'Not specified'}")
                st.write(f"• Pickup Address: {booking.reporting_address or 'Not specified'}")
            
            with location_col2:
                st.write(f"• To: {booking.to_location or 'Not specified'}")
                st.write(f"• Drop Address: {booking.drop_address or 'Not specified'}")
            
            # Additional Information
            if booking.flight_train_number:
                st.write(f"✈️ **Flight Details:** {booking.flight_train_number}")
            
            if booking.remarks:
                st.write(f"💬 **Remarks:** {booking.remarks}")
            
            # Confidence and Analysis
            st.write(f"📊 **Confidence Score:** {booking.confidence_score:.1%}")
            
            # Show duty type reasoning if available
            if hasattr(booking, 'duty_type_reasoning') and booking.duty_type_reasoning:
                with st.expander("🔍 Duty Type Analysis", expanded=False):
                    st.text(booking.duty_type_reasoning)

def save_to_sheets_button(result, sheets_manager):
    """Display save to sheets button and handle saving"""
    
    if st.button("💾 Save All Bookings to Google Sheets", key="multi_save_sheets"):
        try:
            # Import the save function
            from streamlit_app import save_extraction_results_to_sheets
            
            success, result_info = save_extraction_results_to_sheets(result)
            if success:
                total_saved, bookings_processed = result_info
                st.success(f"✅ Successfully saved {bookings_processed} booking(s) to Google Sheets! Total rows: {total_saved}")
                st.balloons()
            else:
                st.error(f"❌ Failed to save to Google Sheets: {result_info}")
                
        except Exception as e:
            st.error(f"❌ Error saving to sheets: {str(e)}")

def create_multi_booking_tab():
    """Create the multi-booking extraction tab"""
    
    st.header("📊 Multi-Booking Table Extraction")
    st.markdown("**Extract multiple bookings from complex table layouts (vertical/horizontal formats)**")
    
    # Information section
    with st.expander("ℹ️ How Multi-Booking Extraction Works", expanded=False):
        st.markdown("""
        **This tool handles complex table formats with multiple bookings:**
        
        **📋 Vertical Layout (Key-Value Format):**
        - Date & City / Car → Travel dates and duty type
        - Pick up – Time → Reporting times  
        - Global Leaders → Passenger names
        - Pick up Address → Source locations
        - Drop address → Destination locations
        
        **📊 Horizontal Layout (Column Format):**
        - Cab 1, Cab 2, Cab 3... → Separate bookings per column
        - Field Names → Row headers (Name, Phone, Date, etc.)
        - Each column represents one complete booking
        
        **🚀 Enhanced Features:**
        - ✅ Intelligent field mapping
        - ✅ Enhanced duty type detection 
        - ✅ Vehicle type normalization
        - ✅ Corporate company detection
        - ✅ Confidence scoring per booking
        """)
    
    # Initialize processor
    processor = initialize_multi_booking_processor()
    
    if not processor:
        st.stop()
    
    # File uploader
    st.subheader("📤 Upload Multi-Booking Document")
    uploaded_file = st.file_uploader(
        "Choose a file with multiple bookings (PDF, JPG, PNG, GIF):",
        type=['pdf', 'jpg', 'jpeg', 'png', 'gif'],
        help="Upload images or PDFs containing tables with multiple booking information",
        key="multi_booking_uploader"
    )
    
    if uploaded_file is not None:
        # Display file information
        col1, col2, col3 = st.columns(3)
        with col1:
            st.info(f"📄 **File:** {uploaded_file.name}")
        with col2:
            st.info(f"📊 **Size:** {uploaded_file.size / 1024:.1f} KB")
        with col3:
            st.info(f"🔖 **Type:** {uploaded_file.type}")
        
        # Process button
        if st.button("🔍 Extract All Bookings", type="primary", key="extract_multi_bookings"):
            
            # Validate file
            is_valid, validation_message = processor.validate_file(
                uploaded_file.name, 
                uploaded_file.size
            )
            
            if not is_valid:
                st.error(f"❌ {validation_message}")
                return
            
            # Processing
            with st.spinner("🤖 Extracting multiple bookings from document..."):
                try:
                    start_time = datetime.now()
                    
                    # Get file content
                    file_content = uploaded_file.read()
                    file_type = uploaded_file.name.split('.')[-1].lower()
                    
                    # Process with multi-booking processor
                    result = processor.process_multi_booking_document(
                        file_content, 
                        uploaded_file.name, 
                        file_type
                    )
                    
                    processing_time = (datetime.now() - start_time).total_seconds()
                    
                    # Display results
                    st.success("✅ Multi-booking extraction completed!")
                    
                    # Summary metrics
                    display_extraction_summary(result, processing_time)
                    
                    if result.total_bookings_found > 0:
                        # Convert to DataFrame
                        df = bookings_to_dataframe(result.bookings)
                        
                        # Display DataFrame
                        st.subheader("📊 Extracted Bookings Table")
                        st.markdown("**Dynamic table showing all extracted bookings:**")
                        
                        # Configure DataFrame display
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
                        st.subheader("💾 Download Options")
                        
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            # CSV download
                            csv = df.to_csv(index=False)
                            st.download_button(
                                label="📥 Download CSV",
                                data=csv,
                                file_name=f"multi_bookings_{uploaded_file.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
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
                                file_name=f"multi_bookings_{uploaded_file.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                            )
                        
                        with col3:
                            # JSON download
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
                                file_name=f"multi_bookings_{uploaded_file.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                                mime="application/json"
                            )
                        
                        # Detailed view
                        display_detailed_bookings(result.bookings)
                        
                        # Save to Google Sheets (if available)
                        try:
                            from streamlit_app import sheets_manager
                            if sheets_manager:
                                st.subheader("☁️ Google Sheets Integration")
                                save_to_sheets_button(result, sheets_manager)
                        except ImportError:
                            pass
                        
                        # Processing notes
                        if result.processing_notes:
                            with st.expander("🔍 Processing Details", expanded=False):
                                st.text(result.processing_notes)
                                st.text(f"Extraction method: {result.extraction_method}")
                    
                    else:
                        st.warning("⚠️ No bookings could be extracted from this document.")
                        
                        # Show debug information
                        with st.expander("🔍 Debug Information", expanded=True):
                            st.text("Processing details:")
                            st.text(f"Method: {result.extraction_method}")
                            st.text(f"Notes: {result.processing_notes}")
                            
                            # Show raw extracted content if available
                            if hasattr(result, 'bookings') and result.bookings:
                                first_booking = result.bookings[0]
                                if hasattr(first_booking, 'additional_info') and first_booking.additional_info:
                                    st.text("Raw extracted content:")
                                    st.text(first_booking.additional_info[:1000] + "..." if len(first_booking.additional_info) > 1000 else first_booking.additional_info)
                
                except Exception as e:
                    st.error(f"❌ Multi-booking extraction failed: {str(e)}")
                    
                    # Show detailed error for debugging
                    with st.expander("🔍 Error Details", expanded=False):
                        st.text(traceback.format_exc())
    
    else:
        st.info("📤 Please upload a document containing multiple bookings to begin extraction.")
        
        # Show example formats
        st.subheader("📋 Supported Table Formats")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            **📋 Vertical Layout Example:**
            ```
            Date & City / Car    | Sep 16, Tuesday
            Pick up – Time       | 9:15am  
            Global Leaders       | Carol Perez
            Pick up Address      | Gate 2
            Drop address         | Electronic city
            Comments             | Wait till meeting...
            ```
            """)
        
        with col2:
            st.markdown("""
            **📊 Horizontal Layout Example:**
            ```
            Field Names      | Cab 1    | Cab 2    | Cab 3
            Name of Employee | John Doe | Jane Doe | Bob Smith
            Contact Number   | 1234567  | 7654321  | 9876543
            Date of Travel   | 19-Sep   | 20-Sep   | 21-Sep
            City             | Mumbai   | Delhi    | Bangalore
            ```
            """)

if __name__ == "__main__":
    st.set_page_config(
        page_title="Multi-Booking Extractor",
        page_icon="📊",
        layout="wide"
    )
    
    create_multi_booking_tab()