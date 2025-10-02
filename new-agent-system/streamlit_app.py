"""
Streamlit Web Interface for Multi-Agent Booking Extraction System
Provides user-friendly interface for processing emails and table images
"""

import streamlit as st
import pandas as pd
import os
import tempfile
from PIL import Image
import logging
from datetime import datetime
import time

# Import the multi-agent system
from main import BookingExtractionSystem

# Configure logging for Streamlit
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="Multi-Agent Booking Extraction System",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .agent-status {
        padding: 10px;
        border-radius: 5px;
        margin: 5px 0;
        font-weight: bold;
    }
    .agent-running {
        background-color: #fff3cd;
        color: #856404;
        border: 1px solid #ffeaa7;
    }
    .agent-completed {
        background-color: #d4edda;
        color: #155724;
        border: 1px solid #c3e6cb;
    }
    .processing-info {
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        border-radius: 5px;
        padding: 15px;
        margin: 10px 0;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 5px;
        padding: 15px;
        margin: 10px 0;
        color: #155724;
    }
</style>
""", unsafe_allow_html=True)

def extract_company_from_email(email: str) -> str:
    """Extract company name from email address"""
    if not email or '@' not in email:
        return "NA"
    
    try:
        domain = email.split('@')[1].lower()
        # Remove common email providers
        if domain in ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 'rediffmail.com']:
            return "NA"
        
        # Extract company name from domain
        company = domain.split('.')[0]
        # Capitalize first letter
        company = company.capitalize()
        return company
    except:
        return "NA"

def display_agent_progress(agent_name: str, status: str = "running"):
    """Display agent processing progress"""
    agent_display_names = {
        'corporate_booker': '🏢 Agent 1: Corporate & Booker Details',
        'passenger_details': '👤 Agent 2: Passenger Information', 
        'location_time': '📍 Agent 3: Location & Time Details',
        'duty_vehicle': '🚗 Agent 4: Duty Type & Vehicle',
        'flight_details': '✈️ Agent 5: Flight Details',
        'special_requirements': '📝 Agent 6: Special Requirements & Remarks'
    }
    
    display_name = agent_display_names.get(agent_name, agent_name)
    
    if status == "running":
        st.markdown(f'<div class="agent-status agent-running">🔄 {display_name} - Processing...</div>', unsafe_allow_html=True)
    elif status == "completed":
        st.markdown(f'<div class="agent-status agent-completed">✅ {display_name} - Completed</div>', unsafe_allow_html=True)

def simulate_agent_processing(system, email_content=None, image_path=None, sender_email=""):
    """Simulate agent processing with progress updates"""
    
    # Create placeholder for agent progress
    progress_placeholder = st.empty()
    
    # Start processing
    with progress_placeholder.container():
        st.markdown('<div class="processing-info">🚀 <strong>Starting Multi-Agent Processing...</strong></div>', unsafe_allow_html=True)
        
        if email_content:
            st.info("📧 Processing unstructured email content through 6 specialized agents")
        else:
            st.info("🖼️ Processing table image through AWS Textract and 6 specialized agents")
    
    time.sleep(1)
    
    # Simulate agent processing steps
    agent_sequence = [
        'corporate_booker',
        'passenger_details', 
        'location_time',
        'duty_vehicle',
        'flight_details',
        'special_requirements'
    ]
    
    completed_agents = []
    
    for i, agent in enumerate(agent_sequence):
        # Update progress display
        with progress_placeholder.container():
            st.markdown('<div class="processing-info">🔄 <strong>Multi-Agent Processing in Progress...</strong></div>', unsafe_allow_html=True)
            
            # Show completed agents
            for completed_agent in completed_agents:
                display_agent_progress(completed_agent, "completed")
            
            # Show current agent
            display_agent_progress(agent, "running")
            
            # Show remaining agents
            for remaining_agent in agent_sequence[i+1:]:
                st.markdown(f'⏳ {remaining_agent.replace("_", " ").title()} - Waiting...')
        
        # Simulate processing time
        time.sleep(2)
        completed_agents.append(agent)
    
    # Show all completed
    with progress_placeholder.container():
        st.markdown('<div class="success-box">✅ <strong>All Agents Completed Successfully!</strong></div>', unsafe_allow_html=True)
        for agent in completed_agents:
            display_agent_progress(agent, "completed")
    
    time.sleep(1)
    
    # Actually process the data
    if email_content:
        result_df = system.process_email(email_content, sender_email)
    else:
        result_df = system.process_table_image(image_path)
    
    return result_df

def main():
    """Main Streamlit application"""
    
    # Header
    st.markdown('<h1 class="main-header">🚗 Multi-Agent Booking Extraction System</h1>', unsafe_allow_html=True)
    
    st.markdown("""
    <div style="text-align: center; margin-bottom: 2rem;">
        <p><strong>Intelligent AI-powered system for extracting structured booking data from unstructured emails and table screenshots</strong></p>
        <p>🤖 Powered by 6 specialized AI agents using GPT-4o-mini</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Check for API key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        st.error("⚠️ OpenAI API Key not found! Please set the OPENAI_API_KEY environment variable.")
        st.info("💡 Set your API key using: `export OPENAI_API_KEY='your-key-here'`")
        st.stop()
    
    # Initialize system
    try:
        with st.spinner("🔄 Initializing multi-agent system..."):
            system = BookingExtractionSystem(api_key)
        st.success("✅ System initialized with 6 specialized agents!")
    except Exception as e:
        st.error(f"❌ System initialization failed: {e}")
        st.stop()
    
    # Sidebar for configuration
    st.sidebar.header("📧 Email Configuration")
    sender_email = st.sidebar.text_input(
        "Sender Email (Optional)", 
        placeholder="sarah@medtronic.com",
        help="Extract company name from sender email (e.g., sarah@medtronic.com → Medtronic)"
    )
    
    if sender_email:
        company_name = extract_company_from_email(sender_email)
        st.sidebar.info(f"📊 Extracted Company: **{company_name}**")
    
    st.sidebar.markdown("---")
    st.sidebar.header("ℹ️ System Info")
    st.sidebar.info("""
    **Agents Available:**
    - 🏢 Corporate & Booker Details
    - 👤 Passenger Information  
    - 📍 Location & Time Details
    - 🚗 Duty Type & Vehicle
    - ✈️ Flight Details
    - 📝 Special Requirements
    """)
    
    # Main interface
    st.header("📥 Input Selection")
    
    # Input method selection
    input_method = st.radio(
        "Choose your input method:",
        ["📧 Unstructured Email Content", "🖼️ Table Image Upload"],
        horizontal=True
    )
    
    # Input sections
    col1, col2 = st.columns([2, 1])
    
    with col1:
        if input_method == "📧 Unstructured Email Content":
            st.subheader("📧 Email Content Input")
            
            email_content = st.text_area(
                "Paste your email content here:",
                height=300,
                placeholder="""Subject: Car Service Request

Hi,

We need car service for Ms. Priya Sharma (VIP guest) from TechCorp.
Flight: AI 405 arriving at Mumbai airport on Jan 15 at 2:30 PM
Pickup from Terminal 2, drop at Hotel Taj
Vehicle: SUV preferred

Special requirements:
- Driver should speak English
- VIP treatment required

Thanks,
Sarah""",
                help="Paste the complete email content including subject, body, and any special instructions"
            )
            
            process_button = st.button("🚀 Process Email", type="primary")
            
            if process_button and email_content.strip():
                st.header("🔄 Processing Results")
                
                try:
                    # Process with agent simulation
                    result_df = simulate_agent_processing(
                        system, 
                        email_content=email_content, 
                        sender_email=sender_email
                    )
                    
                    if not result_df.empty:
                        st.header("📊 Extracted Booking Data")
                        st.success(f"✅ Successfully extracted **{len(result_df)}** booking(s)")
                        
                        # Display the DataFrame with proper formatting
                        st.dataframe(
                            result_df,
                            width='stretch',
                            height=min(400, len(result_df) * 50 + 100)
                        )
                        
                        # Download button
                        csv = result_df.to_csv(index=False)
                        st.download_button(
                            label="📥 Download Results as CSV",
                            data=csv,
                            file_name=f"booking_extraction_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv"
                        )
                        
                        # Show summary statistics
                        with st.expander("📈 Extraction Summary"):
                            col_a, col_b, col_c = st.columns(3)
                            with col_a:
                                st.metric("Total Bookings", len(result_df))
                            with col_b:
                                non_na_fields = (result_df != "NA").sum().sum()
                                total_fields = len(result_df) * len(result_df.columns)
                                st.metric("Fields Extracted", f"{non_na_fields}/{total_fields}")
                            with col_c:
                                extraction_rate = (non_na_fields / total_fields) * 100
                                st.metric("Extraction Rate", f"{extraction_rate:.1f}%")
                    
                    else:
                        st.warning("⚠️ No booking data could be extracted from the email content.")
                
                except Exception as e:
                    st.error(f"❌ Processing failed: {str(e)}")
                    logger.error(f"Email processing error: {e}")
            
            elif process_button:
                st.warning("⚠️ Please enter email content to process.")
        
        else:  # Table Image Upload
            st.subheader("🖼️ Table Image Upload")
            
            uploaded_file = st.file_uploader(
                "Upload your booking table image:",
                type=['png', 'jpg', 'jpeg', 'pdf'],
                help="Upload clear images of booking tables. Supports PNG, JPG, JPEG, and PDF formats."
            )
            
            if uploaded_file is not None:
                # Display uploaded image
                if uploaded_file.type.startswith('image'):
                    image = Image.open(uploaded_file)
                    st.image(image, caption="Uploaded Table Image", width='stretch')
                else:
                    st.info(f"📄 Uploaded PDF: {uploaded_file.name}")
                
                process_button = st.button("🚀 Process Table", type="primary")
                
                if process_button:
                    st.header("🔄 Processing Results")
                    
                    try:
                        # Save uploaded file temporarily with proper binary mode
                        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}", mode='wb') as tmp_file:
                            # Reset uploaded file position and read bytes
                            uploaded_file.seek(0)
                            file_bytes = uploaded_file.getvalue()  # Use getvalue() for Streamlit UploadedFile
                            tmp_file.write(file_bytes)
                            temp_path = tmp_file.name
                            
                            # Debug: Log file size to verify it's saved correctly
                            logger.info(f"Saved uploaded file to {temp_path}, original size: {len(file_bytes)} bytes")
                        
                        # Verify the saved file size
                        saved_file_size = os.path.getsize(temp_path)
                        logger.info(f"Verified saved file size: {saved_file_size} bytes")
                        
                        if saved_file_size < 100:
                            st.error(f"❌ File save error: Saved file is only {saved_file_size} bytes (likely corrupted)")
                            os.unlink(temp_path)  # Clean up corrupted file
                            return
                        
                        # Process with agent simulation
                        result_df = simulate_agent_processing(
                            system, 
                            image_path=temp_path, 
                            sender_email=sender_email
                        )
                        
                        # Clean up temporary file
                        os.unlink(temp_path)
                        
                        if not result_df.empty:
                            st.header("📊 Extracted Booking Data")
                            st.success(f"✅ Successfully extracted **{len(result_df)}** booking(s) from table")
                            
                            # Display the DataFrame
                            st.dataframe(
                                result_df,
                                width='stretch',
                                height=min(400, len(result_df) * 50 + 100)
                            )
                            
                            # Download button
                            csv = result_df.to_csv(index=False)
                            st.download_button(
                                label="📥 Download Results as CSV",
                                data=csv,
                                file_name=f"table_extraction_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                mime="text/csv"
                            )
                            
                            # Show summary
                            with st.expander("📈 Extraction Summary"):
                                col_a, col_b, col_c = st.columns(3)
                                with col_a:
                                    st.metric("Total Bookings", len(result_df))
                                with col_b:
                                    non_na_fields = (result_df != "NA").sum().sum()
                                    total_fields = len(result_df) * len(result_df.columns)
                                    st.metric("Fields Extracted", f"{non_na_fields}/{total_fields}")
                                with col_c:
                                    extraction_rate = (non_na_fields / total_fields) * 100
                                    st.metric("Extraction Rate", f"{extraction_rate:.1f}%")
                        
                        else:
                            st.warning("⚠️ No booking data could be extracted from the table image.")
                    
                    except Exception as e:
                        st.error(f"❌ Table processing failed: {str(e)}")
                        logger.error(f"Table processing error: {e}")
    
    with col2:
        st.subheader("📋 Expected Output Format")
        
        # Show sample output structure
        sample_columns = [
            "Customer", "Booked By Name", "Passenger Name", 
            "From (Service Location)", "To", "Vehicle Group",
            "Duty Type", "Start Date", "Rep. Time", "Flight/Train Number",
            "Remarks", "Labels"
        ]
        
        sample_data = {
            "Field": sample_columns[:5] + ["..."] + sample_columns[-2:],
            "Example": [
                "TechCorp", "Sarah Johnson", "Ms. Priya Sharma",
                "Mumbai", "Mumbai", "...",
                "Driver should speak English", "LadyGuest, VIP"
            ]
        }
        
        st.table(pd.DataFrame(sample_data))
        
        st.info("""
        **📊 Output Features:**
        - Fixed 20-column structure
        - Multiple booking support
        - NA for missing fields
        - Standardized formatting
        - CSV download ready
        """)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666;">
        <p><strong>Multi-Agent Booking Extraction System</strong></p>
        <p>Built with ❤️ using GPT-4o-mini and AWS Textract</p>
        <p>🤖 6 Specialized Agents | 📊 20-Column Output | ⚡ Real-time Processing</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()