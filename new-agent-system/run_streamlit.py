"""
Launch Script for Multi-Agent Booking Extraction Streamlit App
Easy way to start the web interface
"""

import os
import sys
import subprocess

def main():
    """Launch the Streamlit application"""
    
    print("🚗 Multi-Agent Booking Extraction System")
    print("=" * 50)
    
    # Check if streamlit is installed
    try:
        import streamlit
        print("✅ Streamlit found")
    except ImportError:
        print("❌ Streamlit not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "streamlit"])
        print("✅ Streamlit installed")
    
    # Check for API key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("\n⚠️  OpenAI API Key not found!")
        print("Please set your API key using one of these methods:")
        print("1. export OPENAI_API_KEY='your-key-here'")
        print("2. Create a .env file with OPENAI_API_KEY=your-key")
        print("\nYou can continue anyway and set it in the Streamlit interface.")
        input("Press Enter to continue...")
    else:
        print("✅ OpenAI API Key found")
    
    # Launch Streamlit
    print("\n🚀 Starting Streamlit application...")
    print("📱 The app will open in your web browser automatically")
    print("🌐 URL: http://localhost:8501")
    print("\n💡 To stop the app, press Ctrl+C in this terminal")
    print("=" * 50)
    
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            "streamlit_app.py",
            "--server.headless", "false",
            "--server.runOnSave", "true",
            "--theme.base", "light"
        ])
    except KeyboardInterrupt:
        print("\n\n👋 Streamlit app stopped. Thanks for using the system!")

if __name__ == "__main__":
    main()