# 🚀 Quick Start Guide - Car Rental Multi-Agent System

## ⚡ Quick Setup (5 minutes)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Get Gemini API Key
1. Visit: https://makersuite.google.com/app/apikey
2. Sign in with Google account
3. Click "Create API Key"
4. Copy the generated key

### 3. Run the App
```bash
streamlit run car_rental_app.py
```

### 4. Configure API Key
- Open the app in your browser (usually http://localhost:8501)
- In the sidebar: select "Enter manually"
- Paste your API key in the password field
- Start processing!

## 🎯 Testing the System

### Sample Inputs Available
The app includes 3 ready-to-use samples:
1. **Single Booking** - Simple airport drop request
2. **Multiple Bookings** - Team travel with 2 bookings  
3. **Table Format** - Structured form data

### What You'll See
✅ **Classification Results** - Single vs Multiple booking detection  
✅ **Extraction Results** - Structured data extraction  
✅ **Validation Results** - Business rules applied  
✅ **Final DataFrame** - 20-column standardized format  
✅ **Download Options** - CSV, JSON, Excel export  

## 🔧 Key Features Added

### Enhanced Single Booking Agent
- **Table Detection** ✨ NEW
- Intelligent field mapping from key:value pairs  
- Support for structured data formats
- Higher confidence scoring for table data

### Complete Multi-Agent Pipeline
1. **Classification** → Gemini AI determines booking type
2. **Extraction** → Routes to appropriate specialist agent  
3. **Validation** → Applies business rules & standardization
4. **Output** → Clean 20-column DataFrame

### Smart Fallback System
- Rule-based extraction when API unavailable
- Graceful degradation with detailed error reporting
- Test mode for offline development

## 💰 API Costs

Typical cost per booking: **₹0.01 - ₹0.05**
- Input: ₹0.05 per 1K tokens
- Output: ₹0.15 per 1K tokens  
- Cost tracking built into app

## 🚨 Troubleshooting

**"Failed to import required modules"**
→ Run: `pip install -r requirements.txt`

**"No API key found"**  
→ Configure key in sidebar or set environment variable

**"Processing failed"**
→ Try "Test mode" to isolate API issues

**Low confidence results**
→ Use provided sample inputs to test system

## 📂 File Support

**Text Input**: Direct email/text pasting  
**File Upload**: Currently supports .txt files  
*Note: OCR for PDF/images requires additional setup*

## 🔄 Alternative Setup (Using Environment Variables)

**Windows PowerShell:**
```powershell
$env:GEMINI_API_KEY="your-api-key-here"
streamlit run car_rental_app.py
```

**Windows Command Prompt:**
```cmd
set GEMINI_API_KEY=your-api-key-here
streamlit run car_rental_app.py
```

**macOS/Linux:**
```bash
export GEMINI_API_KEY="your-api-key-here"
streamlit run car_rental_app.py
```

## 📊 System Architecture

```
Input Text/File
       ↓
Classification Agent (Gemma AI)
       ↓
Extraction Router
       ↓
┌─────────────────────┬─────────────────────┐
│  Single Booking     │  Multiple Booking   │
│  Agent (Enhanced)   │  Agent              │
│  + Table Detection  │  + Complex Parsing  │
└─────────────────────┴─────────────────────┘
       ↓
Business Logic Validation Agent
       ↓
Standardized 20-Column DataFrame
```

## 🎉 Ready to Go!

The system is now fully functional with:
- ✅ Enhanced table detection
- ✅ Multi-agent coordination  
- ✅ Business rule validation
- ✅ Professional Streamlit interface
- ✅ Export capabilities
- ✅ Cost tracking
- ✅ Error handling

**Start the app and begin testing with the provided samples!**

---

*For detailed technical documentation, see README.md*