#!/usr/bin/env python3
"""
Multi-Agent Booking Classifier - Streamlit App
Test interface for the Booking Classification Agent (Agent 1)
"""

import streamlit as st
import os
import json
import time
from datetime import datetime
from typing import Dict, Any, List

# Configure page
st.set_page_config(
    page_title="Multi-Agent Booking Classifier",
    page_icon="🤖", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    st.warning("python-dotenv not installed. Using environment variables only.")

# Import the classification agent
try:
    from multi_agent_system.agents.classification_agent import BookingClassificationAgent
    from multi_agent_system.models.shared_models import BookingType, UsageType
    AGENT_AVAILABLE = True
except ImportError as e:
    AGENT_AVAILABLE = False
    IMPORT_ERROR = str(e)

def initialize_agent():
    """Initialize the classification agent"""
    try:
        openai_api_key = os.getenv('OPENAI_API_KEY')
        if not openai_api_key:
            st.error("⚠️ OpenAI API Key not found. Please set OPENAI_API_KEY environment variable.")
            return None
        
        agent = BookingClassificationAgent(openai_api_key=openai_api_key)
        return agent
    except Exception as e:
        st.error(f"Failed to initialize agent: {str(e)}")
        return None

def display_classification_result(result, classification_obj):
    """Display the classification result in a structured format"""
    
    # Main result
    col1, col2, col3 = st.columns(3)
    
    with col1:
        booking_type_color = "🔴" if classification_obj.booking_type == BookingType.MULTIPLE else "🟢"
        st.metric(
            "Booking Type", 
            f"{booking_type_color} {classification_obj.booking_type.value.upper()}",
            delta=None
        )
    
    with col2:
        st.metric("Booking Count", classification_obj.booking_count)
    
    with col3:
        confidence_color = "🟢" if classification_obj.confidence_score >= 0.8 else "🟡" if classification_obj.confidence_score >= 0.6 else "🔴"
        st.metric(
            "Confidence", 
            f"{confidence_color} {classification_obj.confidence_score:.1%}"
        )
    
    # Usage type and analysis flags
    col4, col5 = st.columns(2)
    
    with col4:
        usage_icons = {
            UsageType.LOCAL: "🏢",
            UsageType.OUTSTATION: "🛣️", 
            UsageType.AIRPORT_TRANSFER: "✈️",
            UsageType.UNKNOWN: "❓"
        }
        icon = usage_icons.get(classification_obj.usage_type, "❓")
        st.info(f"**Usage Type:** {icon} {classification_obj.usage_type.value.title()}")
    
    with col5:
        flags = []
        if classification_obj.has_multiple_dates:
            flags.append("📅 Multiple Dates")
        if classification_obj.has_multiple_passengers:
            flags.append("👥 Multiple Passengers")
        if classification_obj.has_multiple_locations:
            flags.append("📍 Multiple Locations")
        if classification_obj.separate_passenger_bookings:
            flags.append("🔄 Separate Passenger Bookings")
            
        if flags:
            st.info("**Analysis Flags:**\n" + "\n".join([f"• {flag}" for flag in flags]))
    
    # Detected entities
    st.subheader("🔍 Detected Entities")
    
    entity_col1, entity_col2, entity_col3 = st.columns(3)
    
    with entity_col1:
        if classification_obj.detected_dates:
            st.write("**📅 Dates:**")
            for date in classification_obj.detected_dates:
                st.write(f"• {date}")
        else:
            st.write("**📅 Dates:** None detected")
    
    with entity_col2:
        if classification_obj.detected_passengers:
            st.write("**👤 Passengers:**")
            for passenger in classification_obj.detected_passengers:
                st.write(f"• {passenger}")
        else:
            st.write("**👤 Passengers:** None detected")
    
    with entity_col3:
        if classification_obj.detected_locations:
            st.write("**📍 Locations:**")
            for location in classification_obj.detected_locations:
                st.write(f"• {location}")
        else:
            st.write("**📍 Locations:** None detected")
    
    # Processing details
    with st.expander("🔧 Processing Details", expanded=False):
        col_proc1, col_proc2 = st.columns(2)
        
        with col_proc1:
            st.write(f"**Processing Strategy:** {classification_obj.processing_strategy}")
            st.write(f"**Processing Time:** {result.processing_time:.2f} seconds")
            st.write(f"**Cost Estimate:** ${result.cost_estimate:.4f}")
        
        with col_proc2:
            if classification_obj.special_instructions:
                st.write("**Special Instructions:**")
                for key, value in classification_obj.special_instructions.items():
                    st.write(f"• {key}: {value}")
    
    # Reasoning
    st.subheader("🧠 AI Reasoning")
    st.write(classification_obj.reasoning)

def get_test_samples():
    """Get predefined test samples"""
    return {
        "Single Booking - Multiple Passengers": """
Dear Team,

Please arrange a car for office visit tomorrow:
- Passengers: John Smith, Mary Wilson, Peter Kumar
- Date: 25th December 2024
- Pickup: Andheri West, Mumbai at 9:00 AM
- Drop: BKC, Mumbai
- Vehicle: Innova
- Duration: 4 hours local use

Thanks!
Manager
        """.strip(),
        
        "Multiple Bookings - Local Multiple Days": """
Hi,

Need cars for local Bangalore trips:
- Date 1: 26th Dec - Koramangala to Electronic City (for John - 9876543210)
- Date 2: 27th Dec - Whitefield to MG Road (for Sarah - 9876543211) 
- Date 3: 28th Dec - Indiranagar to Hebbal (for Mike - 9876543212)

All local disposal, separate bookings please.

Thanks
        """.strip(),
        
        "Single Booking - Outstation Multiple Days": """
Subject: Outstation Trip Mumbai to Pune

Car needed for business trip:
- Passenger: Rajesh Patel (9123456789)
- Dates: 25th Dec to 28th Dec (4 days)
- Route: Mumbai to Pune and back to Mumbai
- Pickup: 6:00 AM from Andheri
- Vehicle: Innova Crysta
- Stay in Pune for 3 nights

This is a single outstation trip.
        """.strip(),
        
        "Airport Transfer": """
Flight pickup required:

- Passenger: Dr. Smith
- Flight: AI 131 arriving at 10:45 PM
- Date: Tomorrow
- Pickup: Mumbai International Airport 
- Drop: Hotel Taj, Colaba
- Contact: 9988776655

Airport transfer service needed.
        """.strip(),
        
        "Complex - Table Format": """
Car bookings needed:

| Date | Passenger | Route | Contact |
|------|-----------|-------|---------|
| 26-Dec | John Doe | Delhi to Gurgaon | 9876543210 |
| 27-Dec | Mary Smith | Delhi to Noida | 9876543211 |
| 28-Dec | Peter Wilson | Delhi to Faridabad | 9876543212 |

All local Delhi NCR trips, separate bookings for each.
        """.strip(),
        
        "Single Booking - Multiple Drops": """
Hi Team,

Car needed for client visits:
- Passenger: CEO (9123456789)
- Date: Tomorrow
- Route: Hotel → Office 1 → Office 2 → Client Site → Airport
- Pickup: 8:00 AM from Hotel Marriott
- Multiple stops throughout the day
- Vehicle: Mercedes preferred

Single booking with multiple drops.
        """.strip()
    }

def main():
    """Main Streamlit app"""
    
    # Header
    st.title("🤖 Multi-Agent Booking Classifier")
    st.markdown("**Agent 1:** Test interface for booking classification - determines single vs multiple bookings")
    
    if not AGENT_AVAILABLE:
        st.error(f"❌ Classification Agent not available: {IMPORT_ERROR}")
        st.stop()
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Model selection
        model_options = ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo-preview"]
        selected_model = st.selectbox("AI Model", model_options, index=0)
        
        # API key status
        api_key = os.getenv('OPENAI_API_KEY')
        if api_key:
            st.success(f"✅ API Key: {api_key[:8]}...{api_key[-4:]}")
        else:
            st.error("❌ No API Key found")
        
        st.markdown("---")
        st.header("📊 Agent Stats")
        
        # Initialize session state
        if 'classification_stats' not in st.session_state:
            st.session_state.classification_stats = {
                'total_classifications': 0,
                'single_bookings': 0,
                'multiple_bookings': 0,
                'total_cost': 0.0,
                'total_time': 0.0
            }
        
        stats = st.session_state.classification_stats
        st.metric("Total Classifications", stats['total_classifications'])
        st.metric("Single Bookings", stats['single_bookings'])
        st.metric("Multiple Bookings", stats['multiple_bookings'])
        st.metric("Total Cost", f"${stats['total_cost']:.4f}")
        st.metric("Avg Time", f"{stats['total_time'] / max(stats['total_classifications'], 1):.2f}s")
        
        if st.button("Reset Stats"):
            st.session_state.classification_stats = {
                'total_classifications': 0,
                'single_bookings': 0,
                'multiple_bookings': 0,
                'total_cost': 0.0,
                'total_time': 0.0
            }
            st.success("Stats reset!")
    
    # Main content
    tab1, tab2 = st.tabs(["🧪 Test Classification", "📋 Test Samples"])
    
    with tab1:
        st.header("Email Content Analysis")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Input area
            email_content = st.text_area(
                "Email Content", 
                height=300,
                placeholder="Paste email content here for classification..."
            )
            
            sender_email = st.text_input(
                "Sender Email (optional)", 
                placeholder="sender@company.com"
            )
        
        with col2:
            st.subheader("🔍 Quick Actions")
            
            if st.button("🚀 Classify Booking", type="primary", use_container_width=True):
                if not email_content.strip():
                    st.error("Please enter email content")
                else:
                    # Initialize agent
                    agent = initialize_agent()
                    if not agent:
                        st.stop()
                    
                    # Show processing
                    with st.spinner("🤖 Analyzing booking requirements..."):
                        try:
                            start_time = time.time()
                            
                            # Process classification
                            input_data = {
                                'email_content': email_content,
                                'sender_email': sender_email
                            }
                            
                            result = agent.process(input_data)
                            classification_result = agent.create_classification_result(result)
                            
                            processing_time = time.time() - start_time
                            
                            # Update stats
                            stats = st.session_state.classification_stats
                            stats['total_classifications'] += 1
                            stats['total_cost'] += result.cost_estimate
                            stats['total_time'] += processing_time
                            
                            if classification_result.booking_type == BookingType.SINGLE:
                                stats['single_bookings'] += 1
                            else:
                                stats['multiple_bookings'] += 1
                            
                            # Store results in session state
                            st.session_state.last_result = result
                            st.session_state.last_classification = classification_result
                            
                        except Exception as e:
                            st.error(f"Classification failed: {str(e)}")
            
            st.markdown("---")
            
            if st.button("📋 Load Sample", use_container_width=True):
                st.info("Switch to 'Test Samples' tab to select a sample")
            
            if st.button("🗑️ Clear Content", use_container_width=True):
                st.rerun()
        
        # Display results
        if 'last_result' in st.session_state and 'last_classification' in st.session_state:
            st.markdown("---")
            st.header("📊 Classification Results")
            
            display_classification_result(
                st.session_state.last_result, 
                st.session_state.last_classification
            )
    
    with tab2:
        st.header("📋 Test Samples")
        st.markdown("Pre-built test cases to verify classification logic")
        
        test_samples = get_test_samples()
        
        # Sample selection
        sample_name = st.selectbox("Select a test sample:", list(test_samples.keys()))
        
        if sample_name:
            st.subheader(f"📄 {sample_name}")
            
            # Show sample content
            sample_content = test_samples[sample_name]
            st.code(sample_content, language="text")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button(f"🚀 Classify: {sample_name}", type="primary", use_container_width=True):
                    agent = initialize_agent()
                    if not agent:
                        st.stop()
                    
                    with st.spinner(f"🤖 Analyzing {sample_name}..."):
                        try:
                            input_data = {
                                'email_content': sample_content,
                                'sender_email': 'test@example.com'
                            }
                            
                            result = agent.process(input_data)
                            classification_result = agent.create_classification_result(result)
                            
                            # Update stats
                            stats = st.session_state.classification_stats
                            stats['total_classifications'] += 1
                            stats['total_cost'] += result.cost_estimate
                            stats['total_time'] += result.processing_time
                            
                            if classification_result.booking_type == BookingType.SINGLE:
                                stats['single_bookings'] += 1
                            else:
                                stats['multiple_bookings'] += 1
                            
                            st.success("✅ Classification completed!")
                            
                            # Display results
                            display_classification_result(result, classification_result)
                            
                        except Exception as e:
                            st.error(f"Classification failed: {str(e)}")
            
            with col2:
                if st.button("📝 Load in Editor", use_container_width=True):
                    # This would ideally switch tabs and populate content
                    st.info("💡 Copy the content above and paste in the 'Test Classification' tab")
    
    # Footer
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: #666;'>"
        "🤖 Multi-Agent Booking System - Classification Agent v1.0"
        "</div>", 
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()