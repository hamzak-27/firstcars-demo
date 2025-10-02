# 🚗 Multi-Agent Booking Extraction - Streamlit Web Interface

A user-friendly web interface for the intelligent multi-agent booking extraction system. Process unstructured emails and table images through a beautiful, real-time web application.

## 🌟 Features

### **Core Functionality**
- 📧 **Email Processing**: Paste unstructured email content for extraction
- 🖼️ **Table Image Upload**: Upload booking table screenshots (PNG, JPG, PDF)
- 🤖 **Real-Time Agent Progress**: Live updates showing which agent is currently processing
- 📊 **Interactive Results**: View extracted data in formatted DataFrames
- 📥 **CSV Export**: Download results with timestamped filenames

### **Enhanced User Experience**
- 📱 **Responsive Design**: Works on desktop, tablet, and mobile
- 🎨 **Professional UI**: Clean, intuitive interface with custom styling
- ⚡ **Real-Time Feedback**: Live progress updates and status messages
- 📈 **Extraction Analytics**: Success rates and field coverage statistics
- 🔧 **Configuration Options**: Sender email extraction for company names

## 🚀 Quick Start

### **Option 1: Simple Launch (Windows)**
```bash
# Double-click the batch file
run_app.bat
```

### **Option 2: Python Launch**
```bash
# Run the launch script
python run_streamlit.py
```

### **Option 3: Direct Streamlit**
```bash
# Install Streamlit if not installed
pip install streamlit

# Set your API key
export OPENAI_API_KEY="your-openai-api-key"

# Run the app
streamlit run streamlit_app.py
```

## 📋 Prerequisites

### **Required**
- ✅ Python 3.8+
- ✅ OpenAI API Key
- ✅ All system dependencies (see `requirements.txt`)

### **Optional (for table processing)**
- AWS credentials configured for Textract access

## 🖥️ Interface Guide

### **1. Email Configuration (Sidebar)**
- **Sender Email**: Enter sender email to auto-extract company name
  - Example: `sarah@medtronic.com` → Company: "Medtronic"
  - Helps Agent 1 perform better corporate lookup
  - Optional but recommended for better accuracy

### **2. Input Methods**

#### **📧 Email Processing**
- **Text Area**: Paste complete email content
- **Supports**: Subject lines, body text, signatures
- **Example Format**:
  ```
  Subject: Car Service Request
  
  Hi,
  We need car service for Ms. Priya Sharma (VIP guest)
  Flight: AI 405 arriving at Mumbai airport
  Special requirements: Driver should speak English
  ```

#### **🖼️ Table Image Upload**
- **File Types**: PNG, JPG, JPEG, PDF
- **Requirements**: Clear, readable table structure
- **Best Practices**: 
  - High resolution images
  - Good lighting and contrast
  - Minimal skew or rotation

### **3. Processing Display**

#### **Real-Time Agent Progress**
```
🚀 Starting Multi-Agent Processing...

✅ 🏢 Agent 1: Corporate & Booker Details - Completed
🔄 👤 Agent 2: Passenger Information - Processing...
⏳ Location Time - Waiting...
⏳ Duty Vehicle - Waiting...
⏳ Flight Details - Waiting...
⏳ Special Requirements - Waiting...
```

#### **Results Display**
- **Success Message**: Number of bookings extracted
- **Interactive DataFrame**: Sortable, filterable table
- **Download Button**: CSV export with timestamp
- **Summary Stats**: Extraction rates and field coverage

### **4. Output Format**

**Fixed 20-Column Structure**:
| Customer | Booked By Name | Passenger Name | From | To | Vehicle Group | ... |
|----------|----------------|----------------|------|----|--------------|----|
| TechCorp | Sarah Johnson | Ms. Priya Sharma | Mumbai | Mumbai | Toyota Innova | ... |

**Multiple Booking Support**:
- 3 bookings = 3 rows in DataFrame
- Each booking processed independently
- Consistent column structure maintained

## 🔧 Configuration Options

### **Environment Variables**
```bash
# Required
export OPENAI_API_KEY="your-openai-api-key-here"

# Optional (for table processing)
export AWS_ACCESS_KEY_ID="your-aws-access-key"
export AWS_SECRET_ACCESS_KEY="your-aws-secret-key"
export AWS_DEFAULT_REGION="us-east-1"
```

### **Streamlit Configuration**
The app includes optimized Streamlit settings:
- **Wide Layout**: Full screen utilization
- **Expanded Sidebar**: Always visible configuration
- **Light Theme**: Professional appearance
- **Auto-Reload**: Development-friendly

## 📊 Processing Examples

### **Example 1: VIP Guest Email**

**Input**:
```
Subject: Urgent VIP Car Service

Hi,
Ms. Priya Sharma (VIP guest) from TechCorp
Flight AI 405 arriving Mumbai 2:37 PM
Pickup Terminal 2, drop Hotel Taj
SUV preferred, English-speaking driver
```

**Expected Output**:
- Customer: TechCorp
- Passenger Name: Ms. Priya Sharma  
- Labels: LadyGuest, VIP
- Flight/Train Number: AI 405
- Rep. Time: 14:30 (rounded to 15-min interval)
- Remarks: English-speaking driver

### **Example 2: Multi-Booking Email**

**Input**:
```
3 bookings for tomorrow:
1. Mr. Rajesh - Hotel A to Office at 9:15 AM
2. Ms. Anita (VIP) - Airport pickup AI 204
3. David - Pune to Mumbai, train 12301
```

**Expected Output**:
- **3 rows** in DataFrame
- Different duty types, times, locations
- VIP label only for Ms. Anita
- All flight/train numbers extracted

## ⚡ Performance

### **Processing Times**
- **Email**: 15-30 seconds per booking
- **Table**: 20-45 seconds per booking  
- **Agent Steps**: ~2 seconds per agent (simulated display)

### **Cost Efficiency**
- **GPT-4o-mini**: ~$0.02-0.05 per booking
- **Textract**: ~$0.001 per table image
- **Total**: Very cost-effective for production use

## 🛠️ Troubleshooting

### **Common Issues**

1. **"API Key not found"**
   - Set `OPENAI_API_KEY` environment variable
   - Restart terminal/app after setting

2. **"No bookings extracted"**
   - Check email content clarity
   - Ensure proper formatting
   - Try with sender email for better context

3. **"Table processing failed"**
   - Verify image quality and clarity
   - Check AWS credentials
   - Ensure table has clear structure

4. **"Agent processing error"**
   - Check internet connection
   - Verify API quotas/billing
   - Check system logs for details

### **Debug Mode**
```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📈 Analytics & Monitoring

### **Extraction Metrics**
- **Total Bookings**: Number of bookings processed
- **Fields Extracted**: Non-NA fields vs total fields
- **Extraction Rate**: Percentage of successful extractions

### **Agent Performance**
- Real-time processing status
- Individual agent completion tracking
- Error handling and recovery

## 🚀 Production Deployment

### **Local Development**
```bash
streamlit run streamlit_app.py --server.runOnSave true
```

### **Production Server**
```bash
streamlit run streamlit_app.py --server.headless true --server.port 8501
```

### **Docker Deployment** (Future)
```dockerfile
FROM python:3.9-slim
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
EXPOSE 8501
CMD ["streamlit", "run", "streamlit_app.py"]
```

## 🎯 Best Practices

### **For Email Processing**
- Include complete email content (subject + body)
- Provide sender email when possible
- Ensure clear passenger and booking details
- Include flight/train numbers if available

### **For Table Processing**
- Use high-resolution images
- Ensure good lighting and contrast
- Avoid skewed or rotated images
- Test with sample tables first

### **For Production Use**
- Monitor API usage and costs
- Set up proper error logging
- Regular backup of CSV outputs
- Test with various email formats

## 🤝 Support

For issues or questions:
1. Check this README first
2. Review system logs
3. Test with provided sample data
4. Contact system administrators

---

**🌟 Enjoy using the Multi-Agent Booking Extraction System!**