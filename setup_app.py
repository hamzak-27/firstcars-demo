#!/usr/bin/env python3
"""
Quick setup script for the Car Rental Multi-Agent System Streamlit app
"""

import os
import subprocess
import sys

def check_python_version():
    """Check if Python version is 3.8+"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8+ is required. Current version:", sys.version)
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} detected")
    return True

def install_dependencies():
    """Install required dependencies"""
    print("\n🔄 Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def check_api_key():
    """Check for API key configuration"""
    print("\n🔑 Checking API key configuration...")
    
    api_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_AI_API_KEY')
    
    if api_key:
        print("✅ API key found in environment variables")
        return True
    else:
        print("⚠️ No API key found in environment variables")
        print("\nYou can configure your API key in the Streamlit app or set it as an environment variable:")
        print("- Windows: set GEMINI_API_KEY=your-api-key-here")
        print("- macOS/Linux: export GEMINI_API_KEY=your-api-key-here")
        print("\nGet your API key from: https://makersuite.google.com/app/apikey")
        return True  # Not a blocking issue

def start_streamlit():
    """Start the Streamlit application"""
    print("\n🚀 Starting Streamlit application...")
    try:
        subprocess.run([sys.executable, "-m", "streamlit", "run", "car_rental_app.py"])
    except KeyboardInterrupt:
        print("\n👋 Application stopped by user")
    except Exception as e:
        print(f"❌ Failed to start Streamlit: {e}")

def main():
    """Main setup function"""
    print("🚗 Car Rental Multi-Agent System Setup")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        print("\n❌ Setup failed. Please install dependencies manually:")
        print("pip install -r requirements.txt")
        sys.exit(1)
    
    # Check API key
    check_api_key()
    
    # Start the app
    print("\n🎉 Setup completed! Starting the application...")
    print("The app will open in your browser at: http://localhost:8501")
    print("Press Ctrl+C to stop the application")
    
    input("\nPress Enter to continue...")
    start_streamlit()

if __name__ == "__main__":
    main()