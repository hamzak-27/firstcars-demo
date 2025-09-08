# 🚗 FirstCars Demo Tool

An AI-powered car rental booking extraction system that converts unstructured email content into structured data using GPT-4o.

## ✨ Features

- **AI-Powered Extraction**: Uses OpenAI GPT-4o with chain-of-thought reasoning
- **Clean Web Interface**: Built with Streamlit for easy testing
- **Excel Integration**: Automatically saves results to Excel with proper column mapping
- **Multi-Day Bookings**: Automatically creates separate entries for multi-day requests
- **Smart Data Processing**: Handles phone numbers, dates, times, and vehicle standardization
- **Real-time Processing**: Instant feedback and validation

## 🚀 Live Demo

**Deployed App**: [FirstCars Demo Tool](https://your-app-url.streamlit.app) *(will be updated after deployment)*

## 📸 Screenshots

### Main Interface
- Left panel: Email content input
- Right panel: Extracted results display
- Bottom: Excel file management

## 🛠️ Local Development Setup

### Prerequisites
- Python 3.8+
- OpenAI API key

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/firstcars-demo.git
   cd firstcars-demo
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   Create a `.env` file in the project root:
   ```env
   OPENAI_API_KEY=your-openai-api-key-here
   ```

4. **Run the application**
   ```bash
   streamlit run streamlit_app.py
   ```

5. **Open your browser**
   Navigate to `http://localhost:8501`

## 🔧 Usage

### Processing Emails

1. **Paste Email Content**: Copy and paste the raw email content in the left text area
2. **Extract Data**: Click "🔍 Extract Data" to process with AI
3. **Review Results**: Check the extracted information on the right panel
4. **Save to Excel**: Click "💾 Save to Excel" to store the results

### Multi-Day Bookings

The system automatically detects multi-day bookings and creates separate Excel rows for each day:

**Example Input:**
```
Please arrange a cab at 09:45 pm on 05-09-25 & 06-09-25.
```

**Result:** Creates 2 separate bookings (one for each date)

### Excel Output

Results are saved to `booking_extractions.xlsx` with columns:
- Corporate, Passenger Details, Trip Information
- Locations, Vehicle Type, Flight/Train Details
- Remarks and Additional Information

## 🌐 Deployment

### Streamlit Cloud Deployment

1. **Push to GitHub** (see instructions below)

2. **Deploy on Streamlit Cloud**:
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Connect your GitHub account
   - Select your repository
   - Choose `streamlit_app.py` as the main file

3. **Configure Secrets**:
   - In Streamlit Cloud dashboard, go to "Settings" > "Secrets"
   - Add your OpenAI API key:
     ```toml
     OPENAI_API_KEY = "sk-proj-your-api-key-here"
     ```

## 📋 Project Structure

```
firstcars-demo/
├── streamlit_app.py              # Main Streamlit application
├── car_rental_ai_agent.py        # Core AI agent logic
├── example_usage.py              # CLI usage examples
├── test_new_samples.py           # Test script for email samples
├── requirements.txt              # Python dependencies
├── .env                          # Environment variables (local)
├── .gitignore                    # Git ignore rules
├── .streamlit/
│   ├── config.toml              # Streamlit configuration
│   └── secrets.toml             # Streamlit secrets (template)
├── booking_extractions.xlsx     # Generated Excel file
└── README.md                    # This file
```

## 🧪 Testing

### Test with Sample Emails

The system has been tested with various email formats:

```python
# Run test script
python test_new_samples.py
```

### Sample Email Formats Supported

- **Basic Requests**: Simple cab booking emails
- **Corporate Bookings**: Company-related bookings with full details
- **Airport Transfers**: Flight-based pickup/drop requests
- **Multi-day Bookings**: Requests spanning multiple dates
- **Local Disposals**: City-based local usage requests

## 💰 Cost Analysis

**Estimated Cost per Email**: ~$0.014

**Volume Estimates**:
- 100 emails/month: ~$1.40
- 500 emails/month: ~$7.00
- 1000 emails/month: ~$14.00

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | OpenAI API key for GPT-4o | Yes |

### Customization

- **Vehicle Mappings**: Edit `vehicle_mappings` in `car_rental_ai_agent.py`
- **Date Formats**: Modify `month_mappings` for additional date formats
- **Excel Columns**: Update `EXCEL_COLUMNS` in `streamlit_app.py`

## 📊 Data Fields Extracted

- **Passenger Information**: Name, phone, email
- **Corporate Details**: Company name, booked by information
- **Trip Details**: Start/end dates, times, vehicle type
- **Locations**: From/to locations, pickup/drop addresses
- **Additional**: Flight numbers, duty type, remarks, pricing

## 🐛 Troubleshooting

### Common Issues

1. **Excel Permission Error**: Close Excel file before saving
2. **API Key Error**: Ensure OPENAI_API_KEY is properly set
3. **Date Parsing**: Check date formats match expected patterns

### Error Handling

- Automatic retry mechanism for Excel file conflicts
- Graceful fallback for failed extractions
- Comprehensive error messages and logging

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- OpenAI for GPT-4o API
- Streamlit for the web framework
- pandas for data manipulation

## 📞 Support

For questions or issues, please open a GitHub issue or contact the development team.

---

**Built with ❤️ for FirstCars**
