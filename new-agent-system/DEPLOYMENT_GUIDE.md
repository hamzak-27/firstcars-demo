# 🚀 **Streamlit Cloud Deployment Guide**

## 📋 **Pre-Deployment Checklist**

### ✅ **Code Security - COMPLETED**
- [x] Removed hardcoded API keys from all files
- [x] Updated `processors/textract_processor.py` to use environment variables
- [x] Created `.gitignore` to prevent sensitive files from being committed
- [x] All credentials now sourced from environment variables

### ✅ **Files Ready for Deployment**
- [x] `streamlit_app.py` - Main Streamlit application (entry point)
- [x] `requirements.txt` - All dependencies specified
- [x] `.streamlit/config.toml` - Streamlit configuration
- [x] `.gitignore` - Prevents committing sensitive data

---

## 🔐 **Environment Variables Setup**

### **Required Environment Variables:**

#### **1. OpenAI API Key**
```
OPENAI_API_KEY=your-openai-api-key-here
```

#### **2. AWS Credentials**
```
AWS_ACCESS_KEY_ID=your-aws-access-key-id
AWS_SECRET_ACCESS_KEY=your-aws-secret-access-key
AWS_REGION=ap-south-1
AWS_S3_BUCKET=aws-textract-bucket3
```

---

## 🌐 **Streamlit Cloud Deployment Steps**

### **Step 1: Prepare GitHub Repository**

1. **Commit your code to GitHub:**
   ```bash
   git add .
   git commit -m "Prepare for Streamlit Cloud deployment - environment variables configured"
   git push origin main
   ```

2. **Verify `.env` is NOT committed:**
   ```bash
   git status
   # Should show .env as ignored
   ```

### **Step 2: Deploy to Streamlit Cloud**

1. **Go to [share.streamlit.io](https://share.streamlit.io)**

2. **Connect your GitHub repository**
   - Repository: `your-username/firstcars-demo` 
   - Branch: `main`
   - Main file path: `new-agent-system/streamlit_app.py`

3. **Set Environment Variables in Streamlit Cloud:**
   - In your Streamlit Cloud dashboard, go to **App Settings**
   - Navigate to **Secrets** section
   - Add the following in TOML format:

```toml
OPENAI_API_KEY = "your-openai-api-key-here"
AWS_ACCESS_KEY_ID = "your-aws-access-key-id"
AWS_SECRET_ACCESS_KEY = "your-aws-secret-access-key"
AWS_REGION = "ap-south-1"
AWS_S3_BUCKET = "aws-textract-bucket3"
```

### **Step 3: Deployment Configuration**

#### **App URL will be:**
```
https://your-app-name.streamlit.app/
```

#### **Streamlit Cloud Settings:**
- **Python version**: 3.9+ (automatic)
- **Main file**: `new-agent-system/streamlit_app.py`
- **Requirements**: Auto-detected from `requirements.txt`

---

## 🔧 **Local Development Setup**

### **For Local Testing:**

1. **Create `.env` file locally:**
   ```bash
   OPENAI_API_KEY=your-openai-api-key-here
   AWS_ACCESS_KEY_ID=your-aws-access-key-id
   AWS_SECRET_ACCESS_KEY=your-aws-secret-access-key
   AWS_REGION=ap-south-1
   AWS_S3_BUCKET=aws-textract-bucket3
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run locally:**
   ```bash
   streamlit run streamlit_app.py
   ```

---

## 🎯 **Environment Variables in Code**

### **Current Implementation:**

#### **Main App (streamlit_app.py):**
```python
# Check for API key
api_key = os.getenv('OPENAI_API_KEY')
if not api_key:
    st.error("⚠️ OpenAI API Key not found!")
    st.stop()
```

#### **Textract Processor (processors/textract_processor.py):**
```python
# Get AWS credentials from environment variables
aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
aws_region = os.getenv('AWS_REGION', 'ap-south-1')
```

#### **All Agents:**
```python
# All agents receive API key as constructor parameter
def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
    self.api_key = api_key  # No hardcoding
```

---

## ⚡ **Quick Deployment Commands**

```bash
# 1. Ensure .env is in .gitignore
echo ".env" >> .gitignore

# 2. Commit deployment-ready code
git add .
git commit -m "Deploy to Streamlit Cloud with environment variables"
git push origin main

# 3. Go to share.streamlit.io and deploy!
```

---

## 🔍 **Verification Checklist**

### **Before Deployment:**
- [ ] No hardcoded API keys in any `.py` files
- [ ] `.env` file is in `.gitignore`
- [ ] All environment variables are set in Streamlit Cloud secrets
- [ ] `requirements.txt` contains all necessary dependencies
- [ ] `streamlit_app.py` is the main entry point

### **After Deployment:**
- [ ] App loads without credential errors
- [ ] Email processing works (OpenAI API connected)
- [ ] Image processing works (AWS Textract connected)
- [ ] No sensitive data exposed in logs or interface

---

## 🚨 **Security Best Practices**

### ✅ **What's Secured:**
1. **API Keys**: Stored in Streamlit Cloud secrets (encrypted)
2. **AWS Credentials**: Environment variables only
3. **No Hardcoding**: All sensitive data external
4. **Git Safety**: `.gitignore` prevents accidental commits

### ⚠️ **Remember:**
- Never commit `.env` files
- Rotate API keys periodically
- Use least-privilege AWS IAM policies
- Monitor usage and costs

---

## 🎉 **Deployment Complete!**

Your Multi-Agent Booking Extraction System is now ready for Streamlit Cloud deployment with:

- ✅ **Secure credential management**
- ✅ **Production-ready configuration**
- ✅ **No hardcoded secrets**
- ✅ **Complete functionality**

**Access your deployed app at:** `https://your-app-name.streamlit.app/`

🚀 **Ready to process emails and table images in the cloud!**