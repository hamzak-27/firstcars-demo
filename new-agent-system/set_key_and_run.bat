@echo off
echo 🔑 Multi-Agent Booking Extraction System - API Key Setup
echo ================================================================
echo.
echo Please enter your OpenAI API Key:
set /p OPENAI_API_KEY="API Key: "
echo.
echo ✅ API Key set for this session!
echo 🚀 Starting Streamlit application...
echo.
python run_streamlit.py
pause