"""
Test script for the structured email agent with sample table data
"""

import os
from structured_email_agent import StructuredEmailAgent

# Sample structured email (based on your screenshot examples)
sample_structured_email = """
Corporate Name: SAI
Booked By & Contact Number: Ms.Renuka -9840824232
Email ID of booker: renuka@sparkcapital.in
City in which car is required: Chennai
Name of the User: SRIRAM M
Mobile No. of the User: 9787835841
Date of Requirement: 10-09-2025
Car Type: Dzire
Rept Address: Office Adyar,Chennai
Reporting Time / Flight Details (If airport pick up): 15:30HRS
Type of duty (Drop / Pickup / Local/Outstation): Apt Drop
Billing Instructions: BTC
Special Instructions (If any): Cab should be neat & Clean, On time reporting

---

Pick Up City: Coimbatore
Pick Up address: Coimbatore Airport
Pick Up Date: 11-09-2025
Pick Up Time: 07:10hrs
Company name: Yes Bank Ltd
Customer name: Mr. Ashish Kapahi /AKE2869002
Customer contact no: 9902599667/8790811122
Cab type: Innova
Trip details (Usage): As per Ashish's Instructions & meetings
Flight details (For Airport pickup): Indigo - 857
Destination: As per instructions
Special Instructions: Please send a good and clean car with good driver
PAYMENT MODE: Company Card

---

Name of the booker / requester: MR. Sujoy Baidya-9870419192,
Booker's Landline and Mobile No. (Must): 022-66591333
Remarks:
Name of the user: Mr. Rahul Waghmare
User's Contact no: 7506403838
Car type: Dezire
Date / from - to: Sep' 11, 2025/ at 8:00 am
Reporting place: Add: Airoli bus depot, near railway station, Navi Mumbai - 400708
Reporting time: 8:00 am
Type of duty (Apt / Local / Outstation): Travel to Aurangabad and same day back.
Billing Location (MUST): Asset Reconstruction Company (India) Limited (Arcil) The Ruby, 10th Floor 29, Senapati Bapat Marg Dadar (West) Mumbai – 400 028
Billing Instructions – Credit Card / Bill To Company (BTC): BILLING TO-ARCIL-MUMBAI
"""

# Another sample - more table-like format
sample_table_email = """
TRAVEL REQUISITION FORM

NAME OF THE GUEST: Nakul Ayhad
MOBILE NUMBER: 9152026571
RENTAL CITY / PICK UP CITY: New Delhi
CAR TYPE: Sedan
DATE OF REQUIREMENT: 12th September 2025
REPORTING TIME: Flight Ticket Attached
REPORTING ADDRESS: Delhi Airport
FLIGHT DETAILS: Flight Ticket Attached
USAGE (Drop/Disposal/Outstation): Disposal / Outstation
Billing Mode (BTC): BTC
SPECIAL INSTRUCTIONS(if any):
Purpose of Travel: ACMA AGM
COMPANY NAME: Horizon Industrial Parks Pvt Ltd
BILLING ENTITY NAME: Horizon Industrial Parks Pvt Ltd

---

Reservation cum Authorisation Form

Corporate Name (Billing Entity Name): Olive VARS Hospitality LLP
Booked By : Name (With Salutation) & Contact Number: Megha S +91 8147218940
Email ID of booker: megha.s@oliveliving.com
City in which car is required: Hyderabad
Name of the User (Guest Name With Salutation): Siddarth Reddy
Mobile No. of the User (Guest Mobile Number): +91 99800 32808
Email ID of user: Siddarth Reddy siddarth@oliveliving.com
Date of Requirement: 11/09/2025 – 1 day Use
Car Type: Innova Crysta
Reporting Place Address: Park Hyatt Hotel and Residences, Hyderabad
Reporting Time / Flight Details (if airport pick up or airport drop): (Reporting Time – 10:00 AM)
Type of duty (Drop / Pickup / Local Disposal / Outstation): Full Day
Billing Instructions (Bill To Company): Bill To Company
Special Instructions (If any): The driver should know English Clean Car
"""

def test_structured_agent():
    """Test the structured email agent"""
    print("🧪 Testing Structured Email AI Agent")
    print("=" * 50)
    
    # Check if OpenAI key is available
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ OPENAI_API_KEY not found in environment variables")
        print("Please set your OpenAI API key and try again.")
        return
    
    try:
        # Initialize agent
        print("🔧 Initializing structured email agent...")
        agent = StructuredEmailAgent()
        
        print("\n📧 TEST 1: Multiple structured bookings")
        print("-" * 40)
        
        # Test structured extraction
        result = agent.extract_structured_bookings(sample_structured_email)
        
        print(f"Found {result.total_bookings_found} booking(s)")
        print(f"Confidence: {result.confidence_score:.2f}")
        print(f"Method: {result.extraction_method}")
        
        # Display each booking
        for i, booking in enumerate(result.bookings, 1):
            print(f"\n📋 BOOKING {i}:")
            print(f"  Passenger: {booking.passenger_name}")
            print(f"  Phone: {booking.passenger_phone}")
            print(f"  From: {booking.from_location}")
            print(f"  To: {booking.to_location}")
            print(f"  Vehicle: {booking.vehicle_group}")
            print(f"  Date: {booking.start_date}")
            print(f"  Time: {booking.reporting_time}")
            print(f"  Corporate: {booking.corporate}")
        
        print(f"\n📝 Processing Notes: {result.processing_notes}")
        
        print("\n" + "=" * 50)
        print("\n📧 TEST 2: Form-based structured data")
        print("-" * 40)
        
        # Test with more structured form data
        result2 = agent.extract_structured_bookings(sample_table_email)
        
        print(f"Found {result2.total_bookings_found} booking(s)")
        print(f"Confidence: {result2.confidence_score:.2f}")
        
        for i, booking in enumerate(result2.bookings, 1):
            print(f"\n📋 BOOKING {i}:")
            print(f"  Passenger: {booking.passenger_name}")
            print(f"  Corporate: {booking.corporate}")
            print(f"  From: {booking.from_location} → To: {booking.to_location}")
            print(f"  Vehicle: {booking.vehicle_group}")
            print(f"  Date: {booking.start_date}, Time: {booking.reporting_time}")
        
        print("\n" + "=" * 50)
        print("\n🧠 TEST 3: Intelligent email type detection")
        print("-" * 40)
        
        # Test intelligent processing
        unstructured_email = """
        Hi team,
        
        Please book a cab for John Smith (9876543210) from Mumbai Airport to Hotel on 15th Sept at 8:30 AM. 
        Need an Innova for this trip.
        
        Thanks
        """
        
        result3 = agent.process_email_intelligently(unstructured_email)
        print(f"Email type detection result:")
        print(f"  Bookings found: {result3.total_bookings_found}")
        print(f"  Method: {result3.extraction_method}")
        print(f"  Notes: {result3.processing_notes}")
        
        print("\n✅ All tests completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False
    
    return True

def test_email_type_detection():
    """Test the email type detection logic"""
    print("\n🔍 Testing Email Type Detection")
    print("-" * 30)
    
    agent = StructuredEmailAgent()
    
    test_cases = [
        ("Simple unstructured", "Hi, please book a cab for John from airport to hotel tomorrow at 9 AM."),
        ("Structured form", "Corporate Name: ABC Corp\nPassenger Name: John Smith\nReporting Time: 09:00"),
        ("Table format", "| Name | Phone | Destination |\n| John | 9876543210 | Airport |"),
        ("HTML table", "<table><tr><td>Name</td><td>John</td></tr></table>"),
        ("Reservation form", "Reservation cum Authorization Form\nCorporate Name: XYZ\nBooked By: Manager")
    ]
    
    for test_name, content in test_cases:
        email_type = agent.detect_email_type(content)
        print(f"  {test_name}: {email_type}")

if __name__ == "__main__":
    test_structured_agent()
    test_email_type_detection()
