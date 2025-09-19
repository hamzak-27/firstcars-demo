"""
Car Rental AI Agent - Standalone Version
Extracts structured booking data from unstructured emails using GPT-4o with chain-of-thought reasoning
"""

import os
import json
import re
import csv
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
import openai
from openai import OpenAI

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("Warning: python-dotenv not installed. Install with: pip install python-dotenv")
    print("Using system environment variables only.")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class BookingExtraction:
    """Data structure for extracted booking information"""
    corporate: Optional[str] = None
    booked_by_name: Optional[str] = None
    booked_by_phone: Optional[str] = None
    booked_by_email: Optional[str] = None
    passenger_name: Optional[str] = None  # Primary passenger name
    passenger_phone: Optional[str] = None  # Primary passenger phone
    passenger_email: Optional[str] = None  # Primary passenger email
    additional_passengers: Optional[str] = None  # Other passenger names (comma-separated)
    multiple_pickup_locations: Optional[str] = None  # Multiple pickup addresses (comma-separated)
    from_location: Optional[str] = None
    to_location: Optional[str] = None
    # Multiple drop locations
    drop1: Optional[str] = None  # Primary drop location
    drop2: Optional[str] = None  # Second drop location
    drop3: Optional[str] = None  # Third drop location
    drop4: Optional[str] = None  # Fourth drop location
    drop5: Optional[str] = None  # Fifth drop location
    vehicle_group: Optional[str] = None
    duty_type: Optional[str] = None
    # Corporate features
    corporate_duty_type: Optional[str] = None  # G2G or P2P based on corporate mapping
    recommended_package: Optional[str] = None  # Recommended package (G-04HR 40KMS, etc.)
    approval_required: Optional[str] = None  # Yes/No based on corporate CSV
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    reporting_time: Optional[str] = None
    start_from_garage: Optional[str] = None
    reporting_address: Optional[str] = None
    drop_address: Optional[str] = None  # Keep for backward compatibility
    flight_train_number: Optional[str] = None
    dispatch_center: Optional[str] = None
    bill_to: Optional[str] = None
    # Removed price field as per requirements
    remarks: Optional[str] = None
    labels: Optional[str] = None
    additional_info: Optional[str] = None
    confidence_score: Optional[float] = None
    extraction_reasoning: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)
    
    def to_sheets_row(self) -> List[str]:
        """Convert to list format for Google Sheets"""
        return [
            self.corporate or "",
            self.booked_by_name or "",
            self.booked_by_phone or "",
            self.booked_by_email or "",
            self.passenger_name or "",
            self.passenger_phone or "",
            self.passenger_email or "",
            self.additional_passengers or "",
            self.multiple_pickup_locations or "",
            self.from_location or "",
            self.to_location or "",
            self.drop1 or "",
            self.drop2 or "",
            self.drop3 or "",
            self.drop4 or "",
            self.drop5 or "",
            self.vehicle_group or "",
            self.duty_type or "",
            self.corporate_duty_type or "",
            self.recommended_package or "",
            self.approval_required or "",
            self.start_date or "",
            self.end_date or "",
            self.reporting_time or "",
            self.start_from_garage or "",
            self.reporting_address or "",
            self.drop_address or "",  # Keep for backward compatibility
            self.flight_train_number or "",
            self.dispatch_center or "",
            self.bill_to or "",
            self.remarks or "",
            self.labels or "",
            self.additional_info or ""
        ]
    
    def get_missing_critical_fields(self) -> List[str]:
        """Return list of missing critical fields"""
        critical_fields = {
            'passenger_name': 'Passenger Name',
            'passenger_phone': 'Passenger Phone',
            'start_date': 'Start Date',
            'reporting_time': 'Reporting Time',
            'reporting_address': 'Reporting Address',
            'vehicle_group': 'Vehicle Type'
        }
        
        missing = []
        for field, display_name in critical_fields.items():
            value = getattr(self, field)
            if not value or (isinstance(value, str) and value.strip() == ""):
                missing.append(display_name)
        return missing

class CarRentalAIAgent:
    """AI Agent for extracting car rental booking data from unstructured emails"""
    
    def __init__(self, openai_api_key: str = None):
        """Initialize the AI agent"""
        self.openai_api_key = openai_api_key or os.getenv('OPENAI_API_KEY')
        if not self.openai_api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY environment variable or pass it directly.")
        
        self.client = OpenAI(api_key=self.openai_api_key)
        
        # Vehicle type standardization mapping with business rules
        self.vehicle_mappings = {
            'swift': 'Swift Dzire',
            'dzire': 'Swift Dzire',
            'desire': 'Swift Dzire',
            'innova': 'Innova Crysta',  # Business rule: Toyota Innova -> Innova Crysta
            'toyota innova': 'Innova Crysta',  # Business rule: Toyota Innova -> Innova Crysta
            'crysta': 'Innova Crysta',
            'innova crysta': 'Innova Crysta',
            'toyota innova crysta': 'Innova Crysta',
            'etios': 'Toyota Etios',
            'sedan': 'Sedan',
            'suv': 'SUV',
            'hatchback': 'Hatchback',
            'ac cab': 'AC Sedan',
            'tempo traveller': 'Tempo Traveller',
            'traveller': 'Tempo Traveller'
        }
        
        # Month mappings for date parsing
        self.month_mappings = {
            'january': '01', 'jan': '01',
            'february': '02', 'feb': '02',
            'march': '03', 'mar': '03',
            'april': '04', 'apr': '04',
            'may': '05', 'june': '06', 'jun': '06',
            'july': '07', 'jul': '07',
            'august': '08', 'aug': '08',
            'september': '09', 'sep': '09', 'sept': '09',
            'october': '10', 'oct': '10',
            'november': '11', 'nov': '11',
            'december': '12', 'dec': '12'
        }
        
        # Load city, vehicle, and corporate mappings
        self.city_mappings = self._load_city_mappings()
        self.vehicle_mappings_csv = self._load_vehicle_mappings()
        self.corporate_mappings = self._load_corporate_mappings()
        
        # Comprehensive suburb-to-city mapping for major Indian cities
        self.suburb_city_mappings = {
            # Mumbai suburbs
            'jogeshwari': 'Mumbai',
            'andheri': 'Mumbai',
            'bandra': 'Mumbai',
            'kurla': 'Mumbai',
            'powai': 'Mumbai',
            'goregaon': 'Mumbai',
            'malad': 'Mumbai',
            'borivali': 'Mumbai',
            'kandivali': 'Mumbai',
            'dahisar': 'Mumbai',
            'chembur': 'Mumbai',
            'ghatkopar': 'Mumbai',
            'vikhroli': 'Mumbai',
            'kanjurmarg': 'Mumbai',
            'mulund': 'Mumbai',
            'thane': 'Mumbai',
            'navi mumbai': 'Mumbai',
            'vashi': 'Mumbai',
            'nerul': 'Mumbai',
            'panvel': 'Mumbai',
            'kalyan': 'Mumbai',
            'dombivli': 'Mumbai',
            'bhiwandi': 'Mumbai',
            'ulhasnagar': 'Mumbai',
            
            # Delhi suburbs
            'gurgaon': 'Delhi',
            'gurugram': 'Delhi',
            'noida': 'Delhi',
            'greater noida': 'Delhi',
            'faridabad': 'Delhi',
            'ghaziabad': 'Delhi',
            'dwarka': 'Delhi',
            'rohini': 'Delhi',
            'janakpuri': 'Delhi',
            'lajpat nagar': 'Delhi',
            'karol bagh': 'Delhi',
            'connaught place': 'Delhi',
            'cp': 'Delhi',
            'saket': 'Delhi',
            'vasant kunj': 'Delhi',
            'vasant vihar': 'Delhi',
            'defence colony': 'Delhi',
            'greater kailash': 'Delhi',
            'south extension': 'Delhi',
            'laxmi nagar': 'Delhi',
            'pitampura': 'Delhi',
            'preet vihar': 'Delhi',
            
            # Bangalore suburbs
            'whitefield': 'Bangalore',
            'electronic city': 'Bangalore',
            'koramangala': 'Bangalore',
            'indiranagar': 'Bangalore',
            'jayanagar': 'Bangalore',
            'btm layout': 'Bangalore',
            'hsr layout': 'Bangalore',
            'marathahalli': 'Bangalore',
            'sarjapur': 'Bangalore',
            'hebbal': 'Bangalore',
            'yelahanka': 'Bangalore',
            'banashankari': 'Bangalore',
            'rajajinagar': 'Bangalore',
            'malleshwaram': 'Bangalore',
            'jp nagar': 'Bangalore',
            'basavanagudi': 'Bangalore',
            'vijayanagar': 'Bangalore',
            
            # Chennai suburbs  
            'ambattur': 'Chennai',
            'tambaram': 'Chennai',
            'chrompet': 'Chennai',
            'adyar': 'Chennai',
            'velachery': 'Chennai',
            'porur': 'Chennai',
            'anna nagar': 'Chennai',
            't nagar': 'Chennai',
            'nungambakkam': 'Chennai',
            'mylapore': 'Chennai',
            'guindy': 'Chennai',
            'omr': 'Chennai',
            'ecr': 'Chennai',
            'thoraipakkam': 'Chennai',
            'perungudi': 'Chennai',
            'sholinganallur': 'Chennai',
            'pallikaranai': 'Chennai',
            
            # Hyderabad suburbs
            'hitech city': 'Hyderabad',
            'gachibowli': 'Hyderabad',
            'madhapur': 'Hyderabad',
            'kondapur': 'Hyderabad',
            'jubilee hills': 'Hyderabad',
            'banjara hills': 'Hyderabad',
            'secunderabad': 'Hyderabad',
            'miyapur': 'Hyderabad',
            'kukatpally': 'Hyderabad',
            'ameerpet': 'Hyderabad',
            'begumpet': 'Hyderabad',
            'somajiguda': 'Hyderabad',
            'abids': 'Hyderabad',
            'koti': 'Hyderabad',
            'dilsukhnagar': 'Hyderabad',
            'lb nagar': 'Hyderabad',
            
            # Pune suburbs
            'hinjewadi': 'Pune',
            'wakad': 'Pune',
            'baner': 'Pune',
            'aundh': 'Pune',
            'kharadi': 'Pune',
            'viman nagar': 'Pune',
            'koregaon park': 'Pune',
            'camp': 'Pune',
            'shivajinagar': 'Pune',
            'deccan': 'Pune',
            'kothrud': 'Pune',
            'warje': 'Pune',
            'karve nagar': 'Pune',
            'magarpatta': 'Pune',
            'hadapsar': 'Pune',
            
            # Kolkata suburbs
            'salt lake': 'Kolkata',
            'park street': 'Kolkata',
            'ballygunge': 'Kolkata',
            'howrah': 'Kolkata',
            'dumdum': 'Kolkata',
            'behala': 'Kolkata',
            'tollygunge': 'Kolkata',
            'jadavpur': 'Kolkata',
            'gariahat': 'Kolkata',
            'esplanade': 'Kolkata',
            'sealdah': 'Kolkata',
            
            # Ahmedabad suburbs
            'sg highway': 'Ahmedabad',
            'bopal': 'Ahmedabad',
            'satellite': 'Ahmedabad',
            'vastrapur': 'Ahmedabad',
            'naranpura': 'Ahmedabad',
            'ellis bridge': 'Ahmedabad',
            'cg road': 'Ahmedabad',
            'paldi': 'Ahmedabad',
            'navrangpura': 'Ahmedabad',
            'maninagar': 'Ahmedabad',
            
            # Other major cities
            'kochi': 'Cochin',
            'ernakulam': 'Cochin',
            'chembumukku': 'Cochin',
            'mather berrywoods': 'Cochin',
            'kadavanthra': 'Cochin',
            'edapally': 'Cochin',
            'mg road': 'Cochin'
        }
    
    def _normalize_time_to_15min_intervals(self, time_str: str) -> str:
        """
        Normalize time to 15-minute intervals based on enhanced business rules:
        - 0-7 minutes → round down (7:10 → 7:00, 7:07 → 7:00)
        - 8-22 minutes → round to :15 (7:15 → 7:15, 7:10 → 7:00)
        - 23-37 minutes → round to :30 (7:30 → 7:30, 7:25 → 7:15)
        - 38-52 minutes → round to :45 (7:45 → 7:45, 7:43 → 7:30)
        - 53-59 minutes → round down to :45 (7:53 → 7:45)
        """
        if not time_str:
            return time_str
            
        try:
            # Parse time string (handle various formats)
            import re
            time_match = re.search(r'(\d{1,2})[:.](\d{2})', time_str)
            if not time_match:
                return time_str
                
            hour = int(time_match.group(1))
            minute = int(time_match.group(2))
            
            # Enhanced 15-minute interval logic based on requirements
            if minute <= 7:        # 0-7 → :00 (7:10 → 7:00, 7:07 → 7:00)
                normalized_minute = 0
            elif minute <= 22:     # 8-22 → :15 or :00 (7:10 → 7:00, 7:15 → 7:15)
                if minute <= 10:   # Special case: 7:10 → 7:00
                    normalized_minute = 0
                else:
                    normalized_minute = 15
            elif minute <= 37:     # 23-37 → :30 or :15
                if minute <= 25:   # 25 and below → :15
                    normalized_minute = 15
                else:
                    normalized_minute = 30
            elif minute <= 52:     # 38-52 → :45 or :30
                if minute <= 43:   # 43 and below (like 7:43) → :30
                    normalized_minute = 30
                else:
                    normalized_minute = 45
            else:                  # 53-59 → :45 (7:53 → 7:45)
                normalized_minute = 45
                
            # Format as HH:MM
            return f"{hour:02d}:{normalized_minute:02d}"
            
        except Exception as e:
            logger.warning(f"Could not normalize time '{time_str}': {e}")
            return time_str
    
    def _apply_business_rules(self, booking: BookingExtraction, email_content: str = "") -> BookingExtraction:
        """
        Apply enhanced business rules to extracted booking data
        """
        # Rule 1: Default vehicle to 'Dzire' if not specified
        if not booking.vehicle_group or booking.vehicle_group.strip() == "":
            booking.vehicle_group = "Dzire"
        
        # Rule 2: Round trip drop city logic (Bangalore to Mysore and back to Bangalore = drop Bangalore)
        if booking.from_location and booking.to_location:
            from_loc = booking.from_location.lower()
            to_loc = booking.to_location.lower()
            
            # Look for round trip patterns in additional_info or remarks
            combined_text = f"{booking.additional_info or ''} {booking.remarks or ''}".lower()
            
            if "back to" in combined_text or "return to" in combined_text:
                # Extract the return destination
                back_match = re.search(r'(?:back to|return to)\s+([^\s,\.]+)', combined_text)
                if back_match:
                    return_city = back_match.group(1).strip()
                    # If return city matches origin, set final drop as origin city
                    if return_city in from_loc or from_loc in return_city:
                        booking.drop1 = booking.from_location  # Final drop is origin
                        if booking.to_location != booking.from_location:
                            # If there's an intermediate stop, keep it in to_location
                            pass
        
        # Rule 3: Intra-city logic - if mentioned as intra-city, from and to should be same
        combined_text = f"{booking.additional_info or ''} {booking.remarks or ''} {booking.duty_type or ''}".lower()
        intra_city_keywords = ['intra-city', 'within city', 'same city', 'local use', 'city trip']
        if any(keyword in combined_text for keyword in intra_city_keywords):
            if booking.from_location and not booking.to_location:
                booking.to_location = booking.from_location
            elif booking.to_location and not booking.from_location:
                booking.from_location = booking.to_location
        
        # Rule 4: Time precision with 15-minute intervals
        if booking.reporting_time:
            booking.reporting_time = self._normalize_time_to_15min_intervals(booking.reporting_time)
        
        # Rule 5: Filter special instructions (remove greetings, signatures)
        if booking.remarks:
            booking.remarks = self._filter_relevant_instructions(booking.remarks)
        
        # Rule 6: Apply corporate logic
        booking = self._apply_corporate_logic(booking, email_content)
        
        return booking
    
    def _filter_relevant_instructions(self, remarks: str) -> str:
        """Filter out irrelevant content from remarks, keeping only booking-related instructions"""
        if not remarks:
            return remarks
            
        lines = remarks.split('\n')
        relevant_lines = []
        
        # Keywords to exclude (greetings, signatures, etc.)
        exclude_keywords = [
            'regards', 'best regards', 'warm regards', 'kind regards',
            'hello', 'hi', 'dear', 'thanks', 'thank you', 'sincerely',
            'yours', 'faithfully', 'cheers', 'have a', 'good day',
            'please let me know', 'feel free', 'contact me'
        ]
        
        # Keywords to include (booking-related)
        include_keywords = [
            'driver', 'car', 'vehicle', 'pickup', 'drop', 'time', 'address',
            'clean', 'neat', 'punctual', 'contact', 'mobile', 'phone',
            'special', 'requirement', 'instruction', 'note', 'important',
            'guest', 'passenger', 'luggage', 'baggage', 'route', 'toll'
        ]
        
        for line in lines:
            line_lower = line.lower().strip()
            if not line_lower:
                continue
                
            # Skip lines that are just greetings/signatures
            if any(exclude in line_lower for exclude in exclude_keywords) and \
               not any(include in line_lower for include in include_keywords):
                continue
                
            # Skip very short lines that are likely greetings
            if len(line_lower) < 10 and not any(include in line_lower for include in include_keywords):
                continue
                
            relevant_lines.append(line.strip())
        
        return '\n'.join(relevant_lines).strip()
    
    def extract_booking_data(self, email_content: str, sender_email: str = None) -> BookingExtraction:
        """
        Main method to extract booking data from email content (single booking - for backward compatibility)
        
        Args:
            email_content: Raw email text content
            sender_email: Sender's email address (optional)
            
        Returns:
            BookingExtraction object with extracted data and confidence score
        """
        logger.info("Starting single booking data extraction")
        
        try:
            # Use the new multi-booking method and return the first booking
            multiple_results = self.extract_multiple_bookings(email_content, sender_email)
            
            if multiple_results and len(multiple_results) > 0:
                return multiple_results[0]
            else:
                # Return empty extraction
                return BookingExtraction(
                    remarks="No bookings found",
                    confidence_score=0.0
                )
            
        except Exception as e:
            logger.error(f"Extraction failed: {str(e)}")
            # Return empty extraction with error information
            return BookingExtraction(
                remarks=f"Extraction failed: {str(e)}",
                confidence_score=0.0
            )
    
    def extract_multiple_bookings(self, email_content: str, sender_email: str = None) -> List[BookingExtraction]:
        """
        Enhanced method to extract multiple booking data from email content
        
        Args:
            email_content: Raw email text content
            sender_email: Sender's email address (optional)
            
        Returns:
            List of BookingExtraction objects with extracted data
        """
        logger.info("Starting multiple booking data extraction")
        
        try:
            # Use GPT-4o with enhanced reasoning for multiple bookings
            extraction_result = self._extract_multiple_with_reasoning(email_content, sender_email)
            
            # Process multiple bookings
            bookings = self._process_multiple_extractions(extraction_result, email_content)
            
            logger.info(f"Multiple extraction completed. Found {len(bookings)} booking(s)")
            return bookings
            
        except Exception as e:
            logger.error(f"Multiple extraction failed: {str(e)}")
            # Return empty list
            return []
    
    def _extract_multiple_with_reasoning(self, email_content: str, sender_email: str = None) -> Dict:
        """Use GPT-4o to extract multiple bookings from unstructured email content"""
        
        # Get current date for relative date processing
        current_date = datetime.now()
        current_date_str = current_date.strftime('%Y-%m-%d')
        current_day_name = current_date.strftime('%A')
        
        system_prompt = f"""You are an expert AI agent specialized in extracting car rental booking information from unstructured emails. You must identify ALL separate bookings and extract comprehensive details with ZERO data loss.

CRITICAL BUSINESS RULES:
1. MULTIPLE BOOKINGS ANALYSIS: 
   - Analyze for multiple SEPARATE bookings (different dates/times/passengers/routes)
   - Each unique DATE requires a separate booking (17th & 18th Sept = 2 bookings)
   - Different pickup/drop times on same day = separate bookings if different passengers
   - Round trips with overnight stay = 2 separate bookings (outbound + return)
   - Multi-day requirements = separate booking per day
   - Example: "Car for 17th & 18th Sept" = 2 bookings, not 1

2. COMPREHENSIVE DATA EXTRACTION (ZERO LOSS POLICY):
   - Extract EVERY piece of information from the email
   - If data doesn't fit standard fields, put it in 'remarks' or 'additional_info'
   - Driver names, contact numbers, special preferences, cleanliness requirements
   - VIP instructions, billing details, payment methods, corporate contacts
   - Vehicle preferences, alternate contact numbers, emergency contacts
   - Route variations, timing flexibility, special equipment needs

3. MULTIPLE DROP LOCATIONS:
   - Extract ALL drop locations separately as drop1, drop2, drop3, drop4, drop5
   - Example: "Pick from A, drop at B, then C, finally D" = drop1: B, drop2: C, drop3: D
   - For round trips: "Mumbai to Pune and back to Mumbai" = drop1: Mumbai (final destination)

4. ENHANCED BUSINESS LOGIC:
   - VEHICLE DEFAULT: If no vehicle mentioned, DO NOT extract any vehicle (system will default to 'Dzire')
   - ROUND TRIP LOGIC: "Bangalore to Mysore and back to Bangalore" = drop1 should be Bangalore
   - CITY NAMES ONLY: from_location and to_location must contain ONLY city names, not full addresses
   - INTRA-CITY: If mentioned as "intra-city", "within city", "local use" - from and to should be same city
   - NO PRICE EXTRACTION: Do NOT extract any price/cost information

5. MULTIPLE PASSENGERS CLARIFICATION:
   - Multiple passenger names = ONE booking with multiple people, NOT separate bookings
   - Put primary passenger in 'passenger_name', others in 'additional_passengers'
   - Example: "John and Mary traveling" = passenger_name: John, additional_passengers: Mary

6. SPECIAL INSTRUCTIONS FILTERING:
   - Extract ONLY booking-related instructions in remarks
   - EXCLUDE: greetings (hello, hi), signatures (regards, thanks), pleasantries
   - INCLUDE: driver instructions, vehicle requirements, timing notes, special needs

7. CORPORATE COMPANY DETECTION:
   - Identify company names from email signatures, domains, or content
   - Look for corporate entities that might be in our database
   - Extract company names accurately for corporate duty type mapping

8. STANDARDIZATION RULES:
   - Vehicle names: Toyota Innova/Innova → Innova Crysta (MANDATORY)
   - City names: Suburb → City (Jogeshwari → Mumbai, Andheri → Mumbai)
   - Time precision: Extract exact times (7:43, 7:10, 7:53) - no rounding
   - Phone numbers: Clean format (10 digits)
   - Addresses: Full addresses in reporting_address/drop_address, cities only in from/to_location

CRITICAL DATE FORMAT:
- Input dates are in DD/MM/YYYY format (e.g., 27/08/2025 = 27th August 2025)
- Convert to YYYY-MM-DD (e.g., 27/08/2025 → 2025-08-27)
- DO NOT interpret as MM/DD/YYYY or YYYY/MM/DD

DATE CONVERSION REFERENCE (Today is {current_date_str}, {current_day_name}):
- "today" = {current_date_str}
- "tomorrow" = {(current_date + timedelta(days=1)).strftime('%Y-%m-%d')}
- "day after tomorrow" = {(current_date + timedelta(days=2)).strftime('%Y-%m-%d')}
- "next Monday" = next occurrence of that weekday

VEHICLE STANDARDIZATION (MANDATORY):
- Dzire/Desire → Swift Dzire
- Toyota Innova/Innova → Innova Crysta (BUSINESS RULE)
- Crysta → Innova Crysta
- Etios → Toyota Etios
- AC Cab → AC Sedan
- Tempo Traveller → Tempo Traveller

REMARKS EXTRACTION:
- Include ALL special instructions
- Extract driver name/contact if mentioned (e.g., "need driver XYZ - 9876543210")
- Include cleanliness requirements, timing instructions, special needs
- Capture payment instructions, billing details
- Note any VIP/special guest requirements"""
        
        user_prompt = f"""
Please analyze this car rental email and extract ALL separate bookings with comprehensive analysis. 

STEP 1 - MULTIPLE BOOKING ANALYSIS:
Look carefully for these indicators requiring SEPARATE bookings:
- Multiple DATES mentioned (17th Sept + 18th Sept = 2 bookings)
- Different pickup/drop TIMES on same day with different passengers
- Round trips with overnight stays (outbound + return legs)
- Multi-day trips (each day = separate booking)
- Different passengers traveling on different days
- Separate outbound and return journeys

STEP 2 - COMPREHENSIVE DATA EXTRACTION:
Extract EVERY detail from the email - nothing should be lost:
- All names, numbers, addresses, instructions
- Driver preferences, special requirements, VIP needs
- Corporate information, billing details, payment methods
- Vehicle specifications, cleanliness requirements
- Alternate contacts, emergency numbers, backup arrangements
- Route variations, timing flexibility, special equipment
- If information doesn't fit standard fields, put in 'remarks' or 'additional_info'

STEP 3 - SMART CITY MAPPING:
- Extract only CITY names for from_location and to_location
- Map suburbs to cities (Jogeshwari → Mumbai, Andheri → Mumbai)
- Full addresses go in reporting_address and drop_address

EMAIL CONTENT:
{email_content}

SENDER EMAIL: {sender_email or 'Not provided'}

CURRENT DATE: {current_date_str} ({current_day_name})

Please provide your analysis in this EXACT JSON format:
{{
    "analysis": "Step-by-step analysis explaining how many separate bookings you identified and why",
    "bookings_count": 2,
    "bookings": [
        {{
            "booking_number": 1,
            "corporate": "company name or null",
            "booked_by_name": "booker name or null",
            "booked_by_phone": "booker phone or null", 
            "booked_by_email": "booker email or null",
            "passenger_name": "primary passenger name or null",
            "passenger_phone": "primary passenger phone (10 digits) or null",
            "passenger_email": "primary passenger email or null",
            "additional_passengers": "other passenger names (comma-separated) or null",
            "multiple_pickup_locations": "multiple pickup addresses (comma-separated) or null",
            "from_location": "source CITY NAME ONLY or null",
            "to_location": "destination CITY NAME ONLY or null",
            "drop1": "first drop CITY NAME or null",
            "drop2": "second drop CITY NAME or null",
            "drop3": "third drop CITY NAME or null",
            "drop4": "fourth drop CITY NAME or null",
            "drop5": "fifth drop CITY NAME or null", 
            "vehicle_group": "standardized vehicle name or null (leave null if not mentioned - system will default to Dzire)",
            "duty_type": "duty type or null",
            "start_date": "YYYY-MM-DD format (e.g., 27/08/2025 → 2025-08-27, convert relative dates) or null",
            "end_date": "YYYY-MM-DD format (e.g., 27/08/2025 → 2025-08-27) or null",
            "reporting_time": "HH:MM format or null",
            "start_from_garage": "garage info or null",
            "reporting_address": "complete pickup address or null",
            "drop_address": "complete drop address or null",
            "flight_train_number": "flight/train number or null",
            "dispatch_center": "dispatch info or null",
            "bill_to": "billing entity or null",
            "remarks": "ONLY booking-related special instructions/notes (exclude greetings, signatures) or null",
            "labels": "any labels or null",
            "additional_info": "any other relevant information or null"
        }}
        // ... additional bookings if found
    ],
    "confidence_score": 0.85,
    "processing_notes": "Notes about extraction process and any assumptions made"
}}

Return ONLY valid JSON, no additional text."""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                max_tokens=4000
            )
            
            # Extract and parse JSON response
            ai_response = response.choices[0].message.content.strip()
            json_data = self._parse_json_response(ai_response)
            
            return json_data
            
        except Exception as e:
            logger.error(f"Multiple booking GPT-4o extraction failed: {str(e)}")
            raise
    
    def _extract_with_chain_of_thought(self, email_content: str, sender_email: str = None) -> Dict:
        """Use GPT-4o with chain-of-thought reasoning for extraction (legacy method)"""
        
        # Create comprehensive prompt with examples and reasoning
        system_prompt = """You are an expert AI agent specialized in extracting car rental booking information from unstructured emails. You must think step-by-step and provide detailed reasoning for your extractions.

IMPORTANT RULES:
1. Always think step-by-step before extracting data
2. Normalize vehicle names (e.g., "Dzire" → "Swift Dzire", "Crysta" → "Toyota Innova Crysta")
3. Convert dates to YYYY-MM-DD format
4. Convert times to HH:MM 24-hour format
5. Clean phone numbers to 10 digits (remove +91, spaces, hyphens)
6. Use null for genuinely missing information
7. Assign confidence scores based on data completeness and clarity

VEHICLE STANDARDIZATION:
- Dzire/Desire → Swift Dzire
- Crysta → Toyota Innova Crysta  
- Etios → Toyota Etios
- Innova → Toyota Innova
- AC Cab → AC Sedan
- Tempo Traveller → Tempo Traveller

FIELD DEFINITIONS:
- Corporate: Company/organization name
- Booked By: Person making the booking request
- Passenger: Person who will actually travel
- From/To: Source and destination cities/locations
- Reporting Address: Complete pickup address
- Drop Address: Complete drop-off address
- Remarks: Special instructions, requirements, notes"""

        user_prompt = f"""
Please analyze this car rental booking email and extract the required information step-by-step.

EMAIL CONTENT:
{email_content}

SENDER EMAIL: {sender_email or 'Not provided'}

EXTRACTION PROCESS:
1. First, identify all entities (names, dates, times, locations, vehicles, contact info)
2. Then, determine relationships and context
3. Map entities to the required fields
4. Normalize and format the data
5. Assess confidence based on completeness and clarity

Please provide your analysis in this EXACT JSON format:
{{
    "reasoning": "Your step-by-step analysis of the email content",
    "extracted_entities": {{
        "names": ["list of names found"],
        "phones": ["list of phone numbers"],
        "emails": ["list of emails"],
        "dates": ["list of dates"],
        "times": ["list of times"],
        "locations": ["list of locations"],
        "vehicles": ["list of vehicles mentioned"]
    }},
    "extraction": {{
        "corporate": "company name or null",
        "booked_by_name": "booker name or null",
        "booked_by_phone": "booker phone or null", 
        "booked_by_email": "booker email or null",
        "passenger_name": "passenger name or null",
        "passenger_phone": "passenger phone (10 digits) or null",
        "passenger_email": "passenger email or null",
        "from_location": "source location or null",
        "to_location": "destination location or null", 
        "vehicle_group": "standardized vehicle name or null",
        "start_date": "YYYY-MM-DD format or null",
        "end_date": "YYYY-MM-DD format or null",
        "reporting_time": "HH:MM format or null",
        "start_from_garage": "garage info or null",
        "reporting_address": "complete pickup address or null",
        "drop_address": "complete drop address or null",
        "flight_train_number": "flight/train number or null",
        "dispatch_center": "dispatch info or null",
        "bill_to": "billing entity or null",
        "price": "price info or null",
        "remarks": "special instructions/notes or null",
        "labels": "any labels or null",
        "additional_info": "any other relevant information not captured above or null"
    }},
    "confidence_score": 0.85
}}

Return ONLY valid JSON, no additional text."""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                max_tokens=2000
            )
            
            # Extract and parse JSON response
            ai_response = response.choices[0].message.content.strip()
            json_data = self._parse_json_response(ai_response)
            
            return json_data
            
        except Exception as e:
            logger.error(f"GPT-4o extraction failed: {str(e)}")
            raise
    
    def _parse_json_response(self, response: str) -> Dict:
        """Parse JSON from AI response, handling various formats"""
        try:
            # Remove code block markers if present
            response = re.sub(r'```json\s*', '', response)
            response = re.sub(r'```\s*$', '', response)
            
            # Find JSON object boundaries
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                raise ValueError("No JSON object found in response")
            
            json_str = response[json_start:json_end]
            parsed_data = json.loads(json_str)
            
            return parsed_data
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing failed: {str(e)}")
            logger.error(f"Response was: {response[:500]}...")
            raise ValueError(f"Invalid JSON in AI response: {str(e)}")
    
    def _process_multiple_extractions(self, raw_data: Dict, email_content: str = "") -> List[BookingExtraction]:
        """Process multiple extraction results into BookingExtraction objects"""
        
        bookings = []
        
        if 'bookings' not in raw_data:
            logger.warning("No 'bookings' key found in extraction result")
            return bookings
        
        for i, booking_data in enumerate(raw_data['bookings']):
            try:
                # Remove booking_number if present
                booking_data.pop('booking_number', None)
                
                # Process each field with validation and normalization
                processed_data = self._post_process_single_booking(booking_data)
                
                # Add metadata from the overall extraction
                processed_data['confidence_score'] = raw_data.get('confidence_score', 0.5)
                processed_data['extraction_reasoning'] = raw_data.get('analysis', '')
                
                # Create BookingExtraction object
                booking = BookingExtraction(**processed_data)
                
                # Apply business rules
                booking = self._apply_business_rules(booking, email_content)
                
                bookings.append(booking)
                
            except Exception as e:
                logger.warning(f"Failed to process booking {i+1}: {str(e)}")
                continue
        
        return bookings
    
    def _post_process_single_booking(self, booking_data: Dict) -> Dict:
        """Post-process a single booking's data"""
        processed = {}
        
        # Process each field with validation and normalization
        for field, value in booking_data.items():
            if value is None or (isinstance(value, str) and value.lower() in ['null', 'none', 'not provided', '']):
                processed[field] = None
            elif isinstance(value, str):
                value = value.strip()
                
                # Field-specific processing
                if field == 'vehicle_group':
                    processed[field] = self._map_vehicle_type(value)
                elif field in ['from_location', 'to_location']:
                    processed[field] = self._map_city_name(value)
                elif field in ['booked_by_phone', 'passenger_phone']:
                    processed[field] = self._clean_phone_number(value)
                elif field in ['start_date', 'end_date']:
                    processed[field] = self._normalize_date_with_relative(value)
                elif field == 'reporting_time':
                    # Use new business rule time normalization (15-minute intervals)
                    normalized_time = self._normalize_time(value)
                    processed[field] = self._normalize_time_to_15min_intervals(normalized_time)
                else:
                    processed[field] = value if value else None
            else:
                processed[field] = value
        
        # Auto-fill end_date if not provided (assume same day for single trips)
        if processed.get('start_date') and not processed.get('end_date'):
            remarks = processed.get('remarks') or ''
            if 'round trip' not in remarks.lower():
                processed['end_date'] = processed['start_date']
        
        return processed
    
    def _post_process_extraction(self, raw_data: Dict) -> Dict:
        """Post-process and validate extracted data"""
        
        if 'extraction' not in raw_data:
            raise ValueError("Missing 'extraction' key in AI response")
        
        extraction = raw_data['extraction']
        processed = {}
        
        # Process each field with validation and normalization
        for field, value in extraction.items():
            if value is None or (isinstance(value, str) and value.lower() in ['null', 'none', 'not provided', '']):
                processed[field] = None
            elif isinstance(value, str):
                value = value.strip()
                
                # Field-specific processing
                if field == 'vehicle_group':
                    processed[field] = self._map_vehicle_type(value)
                elif field in ['from_location', 'to_location']:
                    processed[field] = self._map_city_name(value)
                elif field in ['booked_by_phone', 'passenger_phone']:
                    processed[field] = self._clean_phone_number(value)
                elif field in ['start_date', 'end_date']:
                    processed[field] = self._normalize_date(value)
                elif field == 'reporting_time':
                    normalized_time = self._normalize_time(value)
                    processed[field] = self._round_time_to_15_minutes(normalized_time)
                else:
                    processed[field] = value if value else None
            else:
                processed[field] = value
        
        # Add metadata
        processed['confidence_score'] = raw_data.get('confidence_score', 0.5)
        processed['extraction_reasoning'] = raw_data.get('reasoning', '')
        
        # Auto-fill end_date if not provided (assume same day for single trips)
        if processed.get('start_date') and not processed.get('end_date'):
            remarks = processed.get('remarks') or ''
            if 'round trip' not in remarks.lower():
                processed['end_date'] = processed['start_date']
        
        return processed
    
    def _normalize_vehicle_type(self, vehicle: str) -> str:
        """Normalize vehicle type names"""
        if not vehicle:
            return None
            
        vehicle_lower = vehicle.lower().strip()
        
        # Check for exact matches first
        if vehicle_lower in self.vehicle_mappings:
            return self.vehicle_mappings[vehicle_lower]
        
        # Check for partial matches
        for pattern, standard in self.vehicle_mappings.items():
            if pattern in vehicle_lower:
                return standard
        
        # Return capitalized original if no match
        return vehicle.title()
    
    def _clean_phone_number(self, phone: str) -> str:
        """Clean and standardize phone numbers"""
        if not phone:
            return None
            
        # Remove all non-digits
        digits = re.sub(r'\D', '', phone)
        
        # Handle Indian numbers
        if digits.startswith('91') and len(digits) == 12:
            return digits[2:]  # Remove country code
        elif len(digits) == 10 and digits[0] in '6789':
            return digits
        elif len(digits) == 11 and digits[0] == '0':
            return digits[1:]  # Remove leading zero
        
        # Return original if can't standardize
        return phone
    
    def _normalize_date_with_relative(self, date_str: str) -> str:
        """Convert various date formats including relative dates to YYYY-MM-DD"""
        if not date_str:
            return None
            
        date_str = date_str.strip().lower()
        current_date = datetime.now()
        current_year = current_date.year
        
        # Handle relative dates first
        if 'today' in date_str:
            return current_date.strftime('%Y-%m-%d')
        elif 'tomorrow' in date_str:
            tomorrow = current_date + timedelta(days=1)
            return tomorrow.strftime('%Y-%m-%d')
        elif 'day after tomorrow' in date_str:
            day_after = current_date + timedelta(days=2)
            return day_after.strftime('%Y-%m-%d')
        elif 'yesterday' in date_str:
            yesterday = current_date - timedelta(days=1)
            return yesterday.strftime('%Y-%m-%d')
        
        # Handle "next [weekday]" or "this [weekday]"
        weekdays = {
            'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
            'friday': 4, 'saturday': 5, 'sunday': 6
        }
        
        for day_name, day_num in weekdays.items():
            if f'next {day_name}' in date_str:
                days_ahead = (day_num - current_date.weekday() + 7) % 7
                if days_ahead == 0:  # Today is the target day, so next week
                    days_ahead = 7
                target_date = current_date + timedelta(days=days_ahead)
                return target_date.strftime('%Y-%m-%d')
            elif f'this {day_name}' in date_str:
                days_ahead = (day_num - current_date.weekday()) % 7
                if days_ahead == 0:  # Today is the target day
                    target_date = current_date
                else:
                    target_date = current_date + timedelta(days=days_ahead)
                return target_date.strftime('%Y-%m-%d')
        
        # Handle "in X days"
        days_pattern = r'in (\d+) days?'
        match = re.search(days_pattern, date_str)
        if match:
            days_count = int(match.group(1))
            target_date = current_date + timedelta(days=days_count)
            return target_date.strftime('%Y-%m-%d')
        
        # Handle "after X days"
        after_days_pattern = r'after (\d+) days?'
        match = re.search(after_days_pattern, date_str)
        if match:
            days_count = int(match.group(1))
            target_date = current_date + timedelta(days=days_count)
            return target_date.strftime('%Y-%m-%d')
        
        # Fall back to original date parsing logic
        return self._normalize_date(date_str)
    
    def _normalize_date(self, date_str: str) -> str:
        """Convert various date formats to YYYY-MM-DD (legacy method)"""
        if not date_str:
            return None
            
        date_str = date_str.strip().lower()
        current_year = datetime.now().year
        
        # Pattern 1: "27th Aug", "29th August", "26th Aug 2025"
        pattern1 = r'(\d{1,2})(?:st|nd|rd|th)?\s+(\w+)(?:\s+(\d{4}))?'
        match = re.search(pattern1, date_str)
        if match:
            day, month_name, year = match.groups()
            year = year or str(current_year)
            
            if month_name in self.month_mappings:
                month = self.month_mappings[month_name]
                return f"{year}-{month}-{day.zfill(2)}"
        
        # Pattern 2: "27/08/2025", "27-08-2025" (DD/MM/YYYY format)
        pattern2 = r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})'
        match = re.search(pattern2, date_str)
        if match:
            day, month, year = match.groups()
            # CRITICAL FIX: DD/MM/YYYY format - day comes first, then month
            return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
        
        # Pattern 3: "2025-08-27" (already formatted)
        pattern3 = r'(\d{4})-(\d{1,2})-(\d{1,2})'
        match = re.search(pattern3, date_str)
        if match:
            year, month, day = match.groups()
            return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
        
        # Return original if can't parse
        logger.warning(f"Could not parse date: {date_str}")
        return date_str
    
    def _normalize_time(self, time_str: str) -> str:
        """Convert various time formats to HH:MM (24-hour)"""
        if not time_str:
            return None
            
        time_str = time_str.strip().lower()
        
        # Remove common suffixes
        time_str = re.sub(r'\s*(hrs?|hours?)\s*', '', time_str)
        
        # Pattern 1: "7.30am", "5.30 AM", "12.30pm"
        pattern1 = r'(\d{1,2})[\.:,](\d{2})\s*(am|pm)?'
        match = re.search(pattern1, time_str)
        if match:
            hour, minute, ampm = match.groups()
            hour = int(hour)
            
            if ampm:
                if ampm == 'pm' and hour != 12:
                    hour += 12
                elif ampm == 'am' and hour == 12:
                    hour = 0
            
            return f"{hour:02d}:{minute}"
        
        # Pattern 2: "1700 Hrs", "0530"
        pattern2 = r'(\d{4})'
        match = re.search(pattern2, time_str)
        if match:
            time_digits = match.group(1)
            hour = int(time_digits[:2])
            minute = int(time_digits[2:])
            return f"{hour:02d}:{minute:02d}"
        
        # Pattern 3: Already in HH:MM format
        pattern3 = r'(\d{1,2}):(\d{2})'
        match = re.search(pattern3, time_str)
        if match:
            hour, minute = match.groups()
            return f"{int(hour):02d}:{minute}"
        
        # Return original if can't parse
        logger.warning(f"Could not parse time: {time_str}")
        return time_str
    
    def _load_city_mappings(self) -> Dict[str, str]:
        """Load city mappings from CSV file"""
        city_mappings = {}
        try:
            with open('City(1).xlsx - Sheet1.csv', 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    city_name = row.get('City name (As per mail)', '').strip()
                    dispatch_center = row.get('Dispatch Centre (To be entered in Indecab)', '').strip()
                    if city_name and dispatch_center and dispatch_center != 'NA':
                        city_mappings[city_name.lower()] = dispatch_center
            logger.info(f"Loaded {len(city_mappings)} city mappings")
        except Exception as e:
            logger.warning(f"Failed to load city mappings: {str(e)}")
        return city_mappings
    
    def _load_vehicle_mappings(self) -> Dict[str, str]:
        """Load vehicle mappings from CSV file"""
        vehicle_mappings = {}
        try:
            with open('Car.xlsx - Sheet1.csv', 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    car_name = row.get('Car name (As per mail)', '').strip()
                    vehicle_group = row.get('Vehicle Group (To be entered in Indecab)', '').strip()
                    if car_name and vehicle_group and vehicle_group != 'NA':
                        vehicle_mappings[car_name.lower()] = vehicle_group
            logger.info(f"Loaded {len(vehicle_mappings)} vehicle mappings")
        except Exception as e:
            logger.warning(f"Failed to load vehicle mappings: {str(e)}")
        return vehicle_mappings
    
    def _load_corporate_mappings(self) -> Dict[str, Dict[str, str]]:
        """Load corporate mappings from Corporate (1).csv file"""
        corporate_mappings = {}
        try:
            with open('Corporate (1).csv', 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    corporate_name = row.get('Corporate', '').strip()
                    approval_reqd = row.get('Approval Reqd (Yes or No)', '').strip()
                    duty_type = row.get('Duty Type (G2G or P2P)', '').strip()
                    
                    if corporate_name and duty_type:
                        corporate_mappings[corporate_name.lower()] = {
                            'approval_required': approval_reqd,
                            'duty_type': duty_type,
                            'original_name': corporate_name
                        }
            logger.info(f"Loaded {len(corporate_mappings)} corporate mappings")
        except Exception as e:
            logger.warning(f"Failed to load corporate mappings: {str(e)}")
        return corporate_mappings
    
    def _detect_corporate_company(self, email_content: str) -> Optional[Dict[str, str]]:
        """Detect corporate company from email content"""
        if not self.corporate_mappings:
            return None
            
        email_lower = email_content.lower()
        
        # Try exact matches first
        for corp_key, corp_info in self.corporate_mappings.items():
            if corp_key in email_lower:
                return corp_info
        
        # Try partial matches for common variations
        for corp_key, corp_info in self.corporate_mappings.items():
            corp_words = corp_key.split()
            if len(corp_words) > 1:
                # Check if major words from company name appear in email
                matches = sum(1 for word in corp_words if len(word) > 3 and word in email_lower)
                if matches >= len(corp_words) * 0.7:  # 70% word match threshold
                    return corp_info
        
        return None
    
    def _recommend_package(self, booking: BookingExtraction) -> str:
        """Recommend appropriate package based on booking details and duty type"""
        duty_type_prefix = "G-" if booking.corporate_duty_type == "G2G" else "P-"
        
        # Determine package based on booking context
        remarks_lower = (booking.remarks or "").lower()
        additional_info_lower = (booking.additional_info or "").lower()
        duty_lower = (booking.duty_type or "").lower()
        
        combined_text = f"{remarks_lower} {additional_info_lower} {duty_lower}"
        
        # Check for 4HR patterns (Drop/Airport)
        drop_keywords = ['drop', 'airport transfer', 'airport pickup', 'pickup from airport', 'drop to airport']
        if any(keyword in combined_text for keyword in drop_keywords):
            return f"{duty_type_prefix}04HR 40KMS"
        
        # Check for outstation patterns
        from_city = (booking.from_location or "").lower()
        to_city = (booking.to_location or "").lower()
        
        major_cities = ['mumbai', 'pune', 'hyderabad', 'chennai', 'delhi', 'ahmedabad', 'bangalore']
        
        # Check if it's outstation travel
        if from_city and to_city and from_city != to_city:
            if any(city in from_city or city in to_city for city in ['kolkata'] + [c for c in major_cities]):
                if 'kolkata' in from_city or 'kolkata' in to_city:
                    return f"{duty_type_prefix}Outstation 300KMS"
                else:
                    return f"{duty_type_prefix}Outstation 250KMS"
        
        # Check for 8HR patterns (Local use/At disposal)
        local_keywords = ['at disposal', 'local use', 'city trip', 'whole day use', 'visit', 'as per guest', 'local']
        if any(keyword in combined_text for keyword in local_keywords):
            return f"{duty_type_prefix}08HR 80KMS"
        
        # Default to 8HR 80KMS when unclear
        return f"{duty_type_prefix}08HR 80KMS"
    
    def _apply_corporate_logic(self, booking: BookingExtraction, email_content: str) -> BookingExtraction:
        """Apply corporate mapping and package recommendation logic"""
        # Detect corporate company
        corporate_info = self._detect_corporate_company(email_content)
        
        if corporate_info:
            # Set corporate duty type and approval requirements
            if corporate_info['approval_required'].lower() in ['no', 'n']:
                booking.corporate_duty_type = corporate_info['duty_type']
                booking.approval_required = "No"
                # Recommend package based on duty type and booking context
                booking.recommended_package = self._recommend_package(booking)
            else:
                booking.approval_required = "Yes"
                booking.corporate_duty_type = None  # Don't auto-assign if approval needed
                booking.recommended_package = "Approval Required"
            
            # Update corporate name if detected
            if not booking.corporate:
                booking.corporate = corporate_info['original_name']
        
        return booking
    
    def _map_city_name(self, location: str) -> str:
        """Map location/address to standardized city name with suburb mapping"""
        if not location:
            return None
            
        location_lower = location.lower().strip()
        
        # First, check suburb-to-city mappings for comprehensive coverage
        for suburb, city in self.suburb_city_mappings.items():
            if suburb in location_lower:
                logger.info(f"Mapped suburb '{suburb}' to city '{city}' from location '{location}'")
                return city
        
        # Check for exact match in CSV city mappings
        if location_lower in self.city_mappings:
            return self.city_mappings[location_lower]
        
        # Check for partial matches in CSV city mappings
        for city_variant, standard_city in self.city_mappings.items():
            if city_variant in location_lower or location_lower in city_variant:
                return standard_city
        
        # Extract city from common address patterns
        city_patterns = [
            r'(?:^|[\s,])([A-Za-z\s]+)\s+airport(?:$|[\s,])',  # "Delhi Airport", "Mumbai Airport"
            r'(?:^|[\s,])([A-Za-z\s]+)\s+railway\s+station(?:$|[\s,])',  # "Chennai Railway Station"
            r'(?:^|[\s,])([A-Za-z\s]+)\s+bus\s+stand(?:$|[\s,])',  # "Bangalore Bus Stand"
        ]
        
        for pattern in city_patterns:
            match = re.search(pattern, location_lower)
            if match:
                extracted_city = match.group(1).strip().title()
                # Check if extracted city is in our suburb mappings
                if extracted_city.lower() in self.suburb_city_mappings:
                    return self.suburb_city_mappings[extracted_city.lower()]
                logger.info(f"Extracted city '{extracted_city}' from address pattern in '{location}'")
                return extracted_city
        
        # If no match found, return original location but capitalize properly
        return location.title() if location else location
    
    def _map_vehicle_type(self, vehicle: str) -> str:
        """Map vehicle name to standardized vehicle group using CSV data"""
        if not vehicle:
            return None
            
        vehicle_lower = vehicle.lower().strip()
        
        # Check CSV mappings first
        if vehicle_lower in self.vehicle_mappings_csv:
            return self.vehicle_mappings_csv[vehicle_lower]
        
        # Check for partial matches in CSV data
        for car_name, vehicle_group in self.vehicle_mappings_csv.items():
            if car_name in vehicle_lower or vehicle_lower in car_name:
                return vehicle_group
        
        # Fallback to original hardcoded mappings
        if vehicle_lower in self.vehicle_mappings:
            return self.vehicle_mappings[vehicle_lower]
        
        for pattern, standard in self.vehicle_mappings.items():
            if pattern in vehicle_lower:
                return standard
        
        # Return original if no match
        return vehicle
    
    def _round_time_to_15_minutes(self, time_str: str) -> str:
        """Round time to 15-minute intervals using enhanced business rules"""
        if not time_str:
            return None
            
        try:
            # Parse time string to get hour and minute
            if ':' in time_str:
                hour_str, minute_str = time_str.split(':')[:2]
                hour = int(hour_str)
                minute = int(minute_str)
            else:
                # Handle cases like "830" or "8"
                if len(time_str) <= 2:
                    hour = int(time_str)
                    minute = 0
                else:
                    hour = int(time_str[:-2])
                    minute = int(time_str[-2:])
            
            # Use the enhanced 15-minute interval logic
            if minute <= 7:        # 0-7 → :00
                rounded_minute = 0
            elif minute <= 22:     # 8-22 → :15 or :00
                if minute <= 10:   # Special case: 7:10 → 7:00
                    rounded_minute = 0
                else:
                    rounded_minute = 15
            elif minute <= 37:     # 23-37 → :30 or :15
                if minute <= 25:   # 25 and below → :15
                    rounded_minute = 15
                else:
                    rounded_minute = 30
            elif minute <= 52:     # 38-52 → :45 or :30
                if minute <= 43:   # 43 and below (like 7:43) → :30
                    rounded_minute = 30
                else:
                    rounded_minute = 45
            else:                  # 53-59 → :45
                rounded_minute = 45
            
            return f"{hour:02d}:{rounded_minute:02d}"
            
        except (ValueError, IndexError) as e:
            logger.warning(f"Could not round time '{time_str}': {str(e)}")
            return time_str
    
    def validate_extraction(self, booking: BookingExtraction) -> Dict[str, Any]:
        """Validate extracted booking data and provide feedback"""
        validation_result = {
            'is_valid': True,
            'missing_critical': booking.get_missing_critical_fields(),
            'quality_score': 0.0,
            'warnings': []
        }
        
        # Calculate quality score based on filled fields
        total_fields = len(asdict(booking)) - 2  # Exclude confidence_score and extraction_reasoning
        filled_fields = sum(1 for field, value in asdict(booking).items() 
                          if value and field not in ['confidence_score', 'extraction_reasoning'])
        
        validation_result['quality_score'] = filled_fields / total_fields
        validation_result['is_valid'] = len(validation_result['missing_critical']) == 0
        
        # Add warnings for common issues
        if not booking.passenger_phone or len(booking.passenger_phone or '') != 10:
            validation_result['warnings'].append("Invalid or missing passenger phone number")
        
        if booking.start_date and booking.end_date:
            try:
                start = datetime.strptime(booking.start_date, '%Y-%m-%d')
                end = datetime.strptime(booking.end_date, '%Y-%m-%d')
                if end < start:
                    validation_result['warnings'].append("End date is before start date")
            except ValueError:
                validation_result['warnings'].append("Invalid date format")
        
        return validation_result
    
    def extract_multiple_emails(self, email_list: List[str]) -> List[Tuple[BookingExtraction, Dict]]:
        """Process multiple emails and return results with validation"""
        results = []
        
        for i, email_content in enumerate(email_list):
            logger.info(f"Processing email {i+1}/{len(email_list)}")
            
            try:
                # Extract booking data
                booking = self.extract_booking_data(email_content)
                
                # Validate extraction
                validation = self.validate_extraction(booking)
                
                results.append((booking, validation))
                
            except Exception as e:
                logger.error(f"Failed to process email {i+1}: {str(e)}")
                # Add error result
                error_booking = BookingExtraction(
                    remarks=f"Processing failed: {str(e)}",
                    confidence_score=0.0
                )
                error_validation = {'is_valid': False, 'quality_score': 0.0, 'warnings': [str(e)]}
                results.append((error_booking, error_validation))
        
        return results

def test_agent_with_samples():
    """Test the agent with the sample emails"""
    
    # Sample emails for testing
    sample_emails = [
        """Car needed 
Pickup - Hyderabad airport 
Time- 12.30 pm
Flight- Delhi- Hyderabad  AI 2859
Local use""",
        
        """Dear Team,
Kindly arrange a cab on 27th Aug,
Name -Nasimsha Nasarulla
Date-27th Aug, Wednesday 
Location - Mather Berrywoods, Chembumukku,Cochin
Time- 7.30am
Cab Type-Dzire
Duty- Local Disposal 
mob- 7358593915""",
        
        """Hi,
Please book a cab as below mentioned requirement.
Name- Muthuseenivasan
Location: Chennai
Mobile No- 8939881561
Designation- AM, CAS
Email ID- muthu.seenivasan@medtronic.com
Trip type- Drop to Chennai Airport 
Trip date: 26th  Aug 2025
Car Type-  Etios
Reporting Time- 5.30 AM
Reporting Address- Nandi Gardens, B2, Plot No 18,19&20, Masilamanieswarar Street, Venkateshwara Nagar, Ambattur OT, Chennai -600053.
Comments: Car should be neat & Clean, Driver should be in location on time"""
    ]
    
    # Initialize agent (requires OPENAI_API_KEY environment variable)
    try:
        agent = CarRentalAIAgent()
        
        print("=" * 80)
        print("TESTING CAR RENTAL AI AGENT")
        print("=" * 80)
        
        # Process all sample emails
        results = agent.extract_multiple_emails(sample_emails)
        
        for i, (booking, validation) in enumerate(results, 1):
            print(f"\n{'='*50}")
            print(f"EMAIL {i} RESULTS")
            print(f"{'='*50}")
            
            print(f"\nEXTRACTED DATA:")
            print(json.dumps(booking.to_dict(), indent=2, default=str))
            
            print(f"\nVALIDATION:")
            print(f"Valid: {validation['is_valid']}")
            print(f"Quality Score: {validation['quality_score']:.1%}")
            print(f"Missing Critical: {validation.get('missing_critical', [])}")
            if validation.get('warnings'):
                print(f"Warnings: {validation['warnings']}")
            
            print(f"\nSHEETS ROW FORMAT:")
            print(booking.to_sheets_row())
        
        # Summary statistics
        total_emails = len(results)
        valid_emails = sum(1 for _, v in results if v['is_valid'])
        avg_quality = sum(v['quality_score'] for _, v in results) / total_emails
        avg_confidence = sum(b.confidence_score or 0 for b, _ in results) / total_emails
        
        print(f"\n{'='*50}")
        print("SUMMARY STATISTICS")
        print(f"{'='*50}")
        print(f"Total Emails: {total_emails}")
        print(f"Valid Extractions: {valid_emails}/{total_emails} ({valid_emails/total_emails:.1%})")
        print(f"Average Quality Score: {avg_quality:.1%}")
        print(f"Average Confidence: {avg_confidence:.1%}")
        
    except Exception as e:
        print(f"Test failed: {str(e)}")
        print("Make sure to set OPENAI_API_KEY environment variable")

if __name__ == "__main__":
    # Run tests
    test_agent_with_samples()
