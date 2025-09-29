#!/usr/bin/env python3
"""
Launch script for the debug version of the car rental app
"""

import subprocess
import sys
import os

def main():
    """Launch the debug Streamlit app"""
    
    # Change to the project directory
    os.chdir(r'C:\Users\ihamz\firstcars-demo')
    
    print("🔧 Starting Car Rental Multi-Agent System (Debug Mode)")
    print("=" * 60)
    print("This debug version will show detailed information about:")
    print("- OCR text extraction from your image")
    print("- Table processing results")
    print("- Multi-agent pipeline processing")
    print("- Detailed error messages and logs")
    print("=" * 60)
    print()
    print("📱 The app will open in your browser shortly...")
    print("🔍 Use 'Show Debug Logs' checkbox to see detailed processing logs")
    print()
    
    # Run the debug Streamlit app
    try:
        result = subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            "debug_car_rental_app.py",
            "--server.port", "8502"  # Use different port to avoid conflicts
        ], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start app: {e}")
        return 1
    except KeyboardInterrupt:
        print("\\n🛑 App stopped by user")
        return 0
    
    return 0

if __name__ == "__main__":
    exit(main())