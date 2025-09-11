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
    passenger_name: Optional[str] = None
    passenger_phone: Optional[str] = None
    passenger_email: Optional[str] = None
    from_location: Optional[str] = None
    to_location: Optional[str] = None
    vehicle_group: Optional[str] = None
    duty_type: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    reporting_time: Optional[str] = None
    start_from_garage: Optional[str] = None
    reporting_address: Optional[str] = None
    drop_address: Optional[str] = None
    flight_train_number: Optional[str] = None
    dispatch_center: Optional[str] = None
    bill_to: Optional[str] = None
    price: Optional[str] = None
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
            self.from_location or "",
            self.to_location or "",
            self.vehicle_group or "",
            self.duty_type or "",
            self.start_date or "",
            self.end_date or "",
            self.reporting_time or "",
            self.start_from_garage or "",
            self.reporting_address or "",
            self.drop_address or "",
            self.flight_train_number or "",
            self.dispatch_center or "",
            self.bill_to or "",
            self.price or "",
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
        
        # Vehicle type standardization mapping
        self.vehicle_mappings = {
            'swift': 'Swift Dzire',
            'dzire': 'Swift Dzire',
            'desire': 'Swift Dzire',
            'innova': 'Toyota Innova',
            'crysta': 'Toyota Innova Crysta',
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
        
        # Load city and vehicle mappings
        self.city_mappings = self._load_city_mappings()
        self.vehicle_mappings_csv = self._load_vehicle_mappings()
    
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
            bookings = self._process_multiple_extractions(extraction_result)
            
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
        
        system_prompt = f"""You are an expert AI agent specialized in extracting car rental booking information from unstructured emails. You must identify ALL separate bookings mentioned in the email content.

IMPORTANT RULES:
1. Analyze the email for MULTIPLE bookings - each booking should be a separate record
2. Different dates = different bookings (even same passenger)
3. Different passengers = different bookings (even same date)
4. Different pickup/drop locations = different bookings
5. Handle relative dates like "tomorrow", "next Monday", "today" using current date: {current_date_str} ({current_day_name})
6. Normalize vehicle names and locations using provided mappings
7. Convert all dates to YYYY-MM-DD format
8. Convert times to HH:MM 24-hour format

DATE CONVERSION REFERENCE (Today is {current_date_str}, {current_day_name}):
- "today" = {current_date_str}
- "tomorrow" = {(current_date + timedelta(days=1)).strftime('%Y-%m-%d')}
- "day after tomorrow" = {(current_date + timedelta(days=2)).strftime('%Y-%m-%d')}
- "next Monday" = next occurrence of that weekday
- "this Friday" = this week's Friday if not past, otherwise next week

VEHICLE STANDARDIZATION:
- Dzire/Desire → Swift Dzire
- Crysta → Toyota Innova Crysta
- Etios → Toyota Etios
- Innova → Toyota Innova
- AC Cab → AC Sedan
- Tempo Traveller → Tempo Traveller"""
        
        user_prompt = f"""
Please analyze this car rental email and extract ALL separate bookings. Look carefully for:
- Multiple dates mentioned
- Multiple passengers
- Multiple trips/routes
- Different pickup times
- Round trips vs one-way trips

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
            "passenger_name": "passenger name or null",
            "passenger_phone": "passenger phone (10 digits) or null",
            "passenger_email": "passenger email or null",
            "from_location": "source location or null",
            "to_location": "destination location or null", 
            "vehicle_group": "standardized vehicle name or null",
            "duty_type": "duty type or null",
            "start_date": "YYYY-MM-DD format (convert relative dates) or null",
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
    
    def _process_multiple_extractions(self, raw_data: Dict) -> List[BookingExtraction]:
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
                    normalized_time = self._normalize_time(value)
                    processed[field] = self._round_time_to_15_minutes(normalized_time)
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
        
        # Pattern 2: "27/08/2025", "27-08-2025"
        pattern2 = r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})'
        match = re.search(pattern2, date_str)
        if match:
            day, month, year = match.groups()
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
    
    def _map_city_name(self, location: str) -> str:
        """Map location/address to standardized city name"""
        if not location:
            return None
            
        location_lower = location.lower().strip()
        
        # Check for exact match first
        if location_lower in self.city_mappings:
            return self.city_mappings[location_lower]
        
        # Check for partial matches
        for city_variant, standard_city in self.city_mappings.items():
            if city_variant in location_lower or location_lower in city_variant:
                return standard_city
        
        # If no match found, return original location
        return location
    
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
        """Round time to nearest 15-minute interval (8:00, 8:15, 8:30, 8:45)"""
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
            
            # Round minute to nearest 15-minute interval
            if minute <= 7:        # 0-7 → :00
                rounded_minute = 0
            elif minute <= 22:     # 8-22 → :15
                rounded_minute = 15
            elif minute <= 37:     # 23-37 → :30
                rounded_minute = 30
            elif minute <= 52:     # 38-52 → :45
                rounded_minute = 45
            else:                  # 53-59 → next hour :00
                rounded_minute = 0
                hour += 1
                if hour >= 24:
                    hour = 0
            
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
