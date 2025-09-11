"""
Test document extraction with your sample data
"""

from unified_email_processor import UnifiedEmailProcessor

# Your extracted text from the PDF
extracted_text = """
FirstCars

First Cars Reservation Form

Reservation cum Authorization From

Company Name

CYTIVA

Booked By & Contact

SUDHA R & 8867754323

Number

Email ID of booker

Sudharamanathan.r@cytiva.com

Chennai

City in which car is required

Name of the User

Sudha

Mobile No. of the User

9080208949

Email ID of user

Sudharamanathan.r@cytiva.com

Date(s) of Requirement

09Sep2025

Car Type

ANY

Reporting Place Address

Chennai Airport Terminal 4

6AM

Reporting Time / Flight

6.00AM 09Sep2025

Details (If airport pick up)

Type of duty (Drop /

Local/Outstation)

Daytrip

Itinerary (If available)

-

Billing Instructions

BTC

(BTC/Credit Card)

Credit Card no. & Expiry

NA

month/year (If applicable)

Special Instructions (If any)

-
"""

def test_document_extraction():
    """Test extraction with your sample data"""
    print("🚀 Testing document extraction with your sample data...")
    
    try:
        # Initialize processor
        processor = UnifiedEmailProcessor()
        
        # Create enhanced context for document processing
        document_context = f"""
DOCUMENT ANALYSIS CONTEXT:
Source: FirstCars_Reservation_Form.pdf
Processing Method: AWS Textract OCR + AI Processing
Document Type: Booking/Reservation Form

EXTRACTED CONTENT FROM TEXTRACT:
{extracted_text}

PROCESSING INSTRUCTION:
This content was extracted from a FirstCars reservation form document.
Extract structured booking information from this form data.
Map the form fields to standard booking fields.
"""
        
        # Process the document content
        result = processor.process_email(document_context)
        
        print(f"📊 Processing Results:")
        print(f"   - Bookings found: {result.total_bookings_found}")
        print(f"   - Processing method: {result.extraction_method}")
        
        for i, booking in enumerate(result.bookings, 1):
            print(f"\\n📋 Booking #{i}:")
            print(f"   - Company: {booking.corporate}")
            print(f"   - Booked by: {booking.booked_by_name}")
            print(f"   - Booked by phone: {booking.booked_by_phone}")
            print(f"   - Passenger: {booking.passenger_name}")
            print(f"   - Passenger phone: {booking.passenger_phone}")
            print(f"   - Date: {booking.start_date}")
            print(f"   - Time: {booking.reporting_time}")
            print(f"   - From: {booking.from_location}")
            print(f"   - Reporting address: {booking.reporting_address}")
            print(f"   - Vehicle: {booking.vehicle_group}")
            print(f"   - Duty type: {booking.duty_type}")
            print(f"   - Remarks: {booking.remarks}")
        
        print("\\n✅ Test completed successfully!")
        return result
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return None

if __name__ == "__main__":
    test_document_extraction()
