# 🤖 AI Validation Setup Guide

Your car rental booking app is now ready for AI-powered validation! Here's how to enable it:

## 🔑 Step 1: Get Gemini API Key

1. **Go to Google AI Studio**: https://aistudio.google.com/
2. **Sign in** with your Google account
3. **Get API Key** → Create new API key
4. **Copy** the generated API key (starts with `AIza...`)

## 💻 Step 2: Set Environment Variable

### For Streamlit Cloud Deployment:
1. Go to your **Streamlit Cloud** app settings
2. Click **"Secrets"** tab  
3. Add this to your secrets:
   ```toml
   GEMINI_API_KEY = "your-api-key-here"
   ```

### For Local Testing:
**Windows (PowerShell):**
```powershell
$env:GEMINI_API_KEY = "your-api-key-here"
python test_ai_validation.py
```

**Windows (Command Prompt):**
```cmd
set GEMINI_API_KEY=your-api-key-here
python test_ai_validation.py
```

**Linux/Mac:**
```bash
export GEMINI_API_KEY="your-api-key-here"
python test_ai_validation.py
```

## 🧪 Step 3: Test AI Validation

Run the test to verify everything works:
```bash
python test_ai_validation.py
```

You should see:
```
✅ **API KEY FOUND**: AIzaSyD...
✅ AI Classification: ENABLED
✅ AI Business Validation: ENABLED
🚀 **AI VALIDATION READY FOR DEPLOYMENT!**
```

## 🎯 What AI Validation Provides

### **1. Smart Classification**
- **Outstation Detection**: Chennai→Bangalore→Chennai correctly identified as single booking
- **Multiple Booking Detection**: "First car", "Second car" patterns  
- **Context Understanding**: Business rules applied intelligently

### **2. Enhanced Business Logic**
- **City Standardization**: Mumbai/Bombay → Mumbai
- **G2G/P2P Detection**: Corporate vs personal bookings
- **Date Intelligence**: "Tomorrow", "next Monday" handling
- **Duty Type Logic**: 04HR 40KMS, 08HR 80KMS, Outstation packages

### **3. Comprehensive Remarks**
- **Extract ALL Extra Info**: Driver details, special instructions, payment notes
- **No Information Loss**: Everything from email captured
- **Clean Formatting**: No system messages, only booking details

## 🔄 Fallback Behavior

**Without API Key**: Uses rule-based validation (still works well)
**With API Key**: Uses AI + rule-based fallback for maximum accuracy

## 🚀 Deployment

Once you add the API key to Streamlit Cloud secrets:
1. Your app will **automatically redeploy**
2. AI validation will be **enabled**  
3. Chennai→Bangalore→Chennai bookings will be processed with **full AI intelligence**

## 💡 Cost Estimate

Gemini 2.5 Flash is very cost-effective:
- **Input**: $0.075 per 1M tokens
- **Output**: $0.30 per 1M tokens  
- **Estimated cost**: <$0.01 per booking validation

## ✅ Verification

After setup, test with a Chennai→Bangalore→Chennai booking to confirm:
- ✅ Classified as **single booking**
- ✅ Duty type: **G2G-Outstation 250KMS** or **P2P-Outstation 250KMS**
- ✅ Enhanced remarks with all extra details
- ✅ Proper city standardization

---

**Need Help?** Run `python test_ai_validation.py` to diagnose any issues!