# Car Rental AI Agent - Deployment Guide

## Streamlit Cloud Deployment

### Prerequisites
1. **GitHub Repository**: Your code should be in a GitHub repository (✅ Done)
2. **Streamlit Account**: Sign up at [share.streamlit.io](https://share.streamlit.io)
3. **API Keys**: You'll need:
   - Google Gemini API Key
   - AWS Access Key ID and Secret Access Key (for Textract)

### Step 1: Streamlit Cloud Setup

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Sign in with GitHub
3. Click "New app"
4. Select your repository: `hamzak-27/firstcars-demo`
5. Set main file path: `car_rental_app.py`
6. Click "Deploy!"

### Step 2: Configure Secrets

In your Streamlit Cloud app settings:

1. Go to "Settings" → "Secrets"
2. Add the following secrets:

```toml
# Google Gemini API Key for AI processing
GEMINI_API_KEY = "your_actual_gemini_api_key_here"

# AWS Credentials for Textract document processing
AWS_ACCESS_KEY_ID = "your_actual_aws_access_key_here"
AWS_SECRET_ACCESS_KEY = "your_actual_aws_secret_access_key_here"
AWS_DEFAULT_REGION = "ap-south-1"
```

### Step 3: Getting API Keys

#### Google Gemini API Key
1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Copy the key to your secrets

#### AWS Credentials
1. Go to [AWS IAM Console](https://console.aws.amazon.com/iam/)
2. Create a new user with Textract permissions
3. Generate access keys
4. Add both the Access Key ID and Secret Access Key to secrets

### App Features

✅ **Single Booking Extraction**: Perfect accuracy for individual booking forms
✅ **Multi-Agent AI Pipeline**: Classification → Extraction → Validation
✅ **AWS Textract Integration**: Advanced OCR for document processing
✅ **Business Logic Validation**: Ensures data quality and completeness
✅ **Excel Export**: Download processed bookings as spreadsheets
✅ **Professional UI**: Clean, intuitive Streamlit interface

### App URL
Once deployed, your app will be available at:
`https://[your-app-name].streamlit.app/`

### Support
- **Working**: Single booking extraction, file upload, text input, validation
- **Future**: Multi-booking table extraction (in development)