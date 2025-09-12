"""
Flight Details AI Agent
Extracts flight information from unstructured documents using GPT-4o
"""

import os
import json
import re
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
import openai
from openai import OpenAI

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("Warning: python-dotenv not installed. Using system environment variables only.")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class FlightExtraction:
    """Data structure for extracted flight information"""
    flight_number: Optional[str] = None
    airline: Optional[str] = None
    departure_airport: Optional[str] = None
    departure_city: Optional[str] = None
    departure_date: Optional[str] = None
    departure_time: Optional[str] = None
    arrival_airport: Optional[str] = None
    arrival_city: Optional[str] = None
    arrival_date: Optional[str] = None
    arrival_time: Optional[str] = None
    passenger_name: Optional[str] = None
    booking_reference: Optional[str] = None
    seat_number: Optional[str] = None
    gate: Optional[str] = None
    terminal: Optional[str] = None
    aircraft_type: Optional[str] = None
    flight_duration: Optional[str] = None
    status: Optional[str] = None
    baggage_info: Optional[str] = None
    meal_info: Optional[str] = None
    ticket_type: Optional[str] = None
    price: Optional[str] = None
    remarks: Optional[str] = None
    additional_info: Optional[str] = None
    confidence_score: Optional[float] = None
    extraction_reasoning: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)
    
    def to_sheets_row(self) -> List[str]:
        """Convert to list format for Google Sheets"""
        return [
            self.flight_number or "",
            self.airline or "",
            self.departure_airport or "",
            self.departure_city or "",
            self.departure_date or "",
            self.departure_time or "",
            self.arrival_airport or "",
            self.arrival_city or "",
            self.arrival_date or "",
            self.arrival_time or "",
            self.passenger_name or "",
            self.booking_reference or "",
            self.seat_number or "",
            self.gate or "",
            self.terminal or "",
            self.aircraft_type or "",
            self.flight_duration or "",
            self.status or "",
            self.baggage_info or "",
            self.meal_info or "",
            self.ticket_type or "",
            self.price or "",
            self.remarks or "",
            self.additional_info or ""
        ]
    
    def get_missing_critical_fields(self) -> List[str]:
        """Return list of missing critical flight fields"""
        critical_fields = {
            'flight_number': 'Flight Number',
            'departure_airport': 'Departure Airport',
            'arrival_airport': 'Arrival Airport',
            'departure_date': 'Departure Date',
            'departure_time': 'Departure Time'
        }
        
        missing = []
        for field, display_name in critical_fields.items():
            value = getattr(self, field)
            if not value or (isinstance(value, str) and value.strip() == ""):
                missing.append(display_name)
        return missing

@dataclass
class FlightExtractionResult:
    """Result structure for flight extraction"""
    flights: List[FlightExtraction]
    total_flights_found: int
    extraction_method: str
    confidence_score: float
    processing_notes: str

class FlightDetailsAIAgent:
    """AI Agent for extracting flight details from unstructured documents"""
    
    def __init__(self, openai_api_key: str = None):
        """Initialize the flight details AI agent"""
        self.openai_api_key = openai_api_key or os.getenv('OPENAI_API_KEY')
        if not self.openai_api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY environment variable or pass it directly.")
        
        self.client = OpenAI(api_key=self.openai_api_key)
        
        # Airport code mappings for common airports
        self.airport_mappings = {
            'del': 'DEL - Indira Gandhi International Airport, New Delhi',
            'bom': 'BOM - Chhatrapati Shivaji International Airport, Mumbai',
            'blr': 'BLR - Kempegowda International Airport, Bangalore',
            'maa': 'MAA - Chennai International Airport, Chennai',
            'ccu': 'CCU - Netaji Subhash Chandra Bose International Airport, Kolkata',
            'hyd': 'HYD - Rajiv Gandhi International Airport, Hyderabad',
            'cok': 'COK - Cochin International Airport, Kochi',
            'goa': 'GOI - Goa International Airport, Goa',
            'pnq': 'PNQ - Pune Airport, Pune',
            'amd': 'AMD - Sardar Vallabhbhai Patel International Airport, Ahmedabad'
        }
        
        # Airline mappings
        self.airline_mappings = {
            'ai': 'Air India',
            '6e': 'IndiGo',
            'sg': 'SpiceJet',
            'g8': 'GoAir',
            'uk': 'Vistara',
            '9w': 'Jet Airways',
            'ix': 'Air India Express'
        }
    
    def extract_flight_details(self, document_content: str) -> FlightExtractionResult:
        """
        Extract flight details from document content
        
        Args:
            document_content: Raw document text content
            
        Returns:
            FlightExtractionResult with extracted flight data
        """
        logger.info("Starting flight details extraction")
        
        try:
            # Use GPT-4o with flight-specific reasoning
            extraction_result = self._extract_with_flight_reasoning(document_content)
            
            # Process the extraction results
            flights = self._process_flight_extractions(extraction_result)
            
            result = FlightExtractionResult(
                flights=flights,
                total_flights_found=len(flights),
                extraction_method="flight_textract_ai",
                confidence_score=extraction_result.get('confidence_score', 0.7),
                processing_notes=extraction_result.get('processing_notes', 'Flight details extracted using Textract + AI')
            )
            
            logger.info(f"Flight extraction completed. Found {len(flights)} flight(s)")
            return result
            
        except Exception as e:
            logger.error(f"Flight extraction failed: {str(e)}")
            # Return empty result with error
            error_flight = FlightExtraction(
                remarks=f"Flight extraction failed: {str(e)}",
                confidence_score=0.0
            )
            
            return FlightExtractionResult(
                flights=[error_flight],
                total_flights_found=0,
                extraction_method="flight_extraction_error",
                confidence_score=0.0,
                processing_notes=f"Flight extraction error: {str(e)}"
            )
    
    def _extract_with_flight_reasoning(self, document_content: str) -> Dict:
        """Use GPT-4o to extract flight details with specialized reasoning"""
        
        # Get current date for relative date processing
        current_date = datetime.now()
        current_date_str = current_date.strftime('%Y-%m-%d')
        
        system_prompt = f"""You are an expert AI agent specialized in extracting flight information from unstructured documents including flight tickets, boarding passes, itineraries, and flight confirmation emails.

FLIGHT EXTRACTION RULES:
1. Extract ALL flights mentioned in the document - connecting flights, return flights, etc.
2. Normalize airport codes to IATA format (e.g., DEL, BOM, BLR)
3. Convert dates to YYYY-MM-DD format
4. Convert times to HH:MM 24-hour format
5. Handle relative dates using current date: {current_date_str}
6. Extract passenger names, booking references, seat numbers
7. Capture flight status, gate, terminal information
8. Include baggage and meal information if present

COMMON PATTERNS:
- Flight numbers: AI 2859, 6E 123, SG 456
- Airport codes: DEL, BOM, BLR, MAA, CCU
- Times: 07:30, 7:30 AM, 1930 hrs
- Dates: 12-Sep-25, 12/09/2025, Sep 12 2025
- Booking refs: ABC123, 6E4ABC, ABCDEF

AIRLINE CODES:
- AI/IC = Air India
- 6E = IndiGo  
- SG = SpiceJet
- G8 = GoAir
- UK = Vistara
- IX = Air India Express"""
        
        user_prompt = f"""
Please analyze this flight document and extract ALL flight information:

DOCUMENT CONTENT:
{document_content}

CURRENT DATE: {current_date_str}

Extract flight details in this EXACT JSON format:
{{
    "analysis": "Step-by-step analysis of the flight document",
    "flights_count": 1,
    "flights": [
        {{
            "flight_number": "flight number (e.g., AI 2859) or null",
            "airline": "full airline name or null",
            "departure_airport": "IATA code (e.g., DEL) or null",
            "departure_city": "city name or null", 
            "departure_date": "YYYY-MM-DD format or null",
            "departure_time": "HH:MM format or null",
            "arrival_airport": "IATA code (e.g., BOM) or null",
            "arrival_city": "city name or null",
            "arrival_date": "YYYY-MM-DD format or null", 
            "arrival_time": "HH:MM format or null",
            "passenger_name": "passenger name or null",
            "booking_reference": "booking/PNR reference or null",
            "seat_number": "seat assignment or null",
            "gate": "departure gate or null",
            "terminal": "terminal information or null",
            "aircraft_type": "aircraft model or null",
            "flight_duration": "flight duration or null",
            "status": "flight status (On Time, Delayed, etc.) or null",
            "baggage_info": "baggage allowance/info or null",
            "meal_info": "meal service info or null",
            "ticket_type": "ticket class (Economy, Business) or null",
            "price": "ticket price or null",
            "remarks": "special notes/instructions or null",
            "additional_info": "any other relevant flight info or null"
        }}
    ],
    "confidence_score": 0.85,
    "processing_notes": "Notes about extraction process"
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
                max_tokens=3000
            )
            
            # Extract and parse JSON response
            ai_response = response.choices[0].message.content.strip()
            json_data = self._parse_json_response(ai_response)
            
            return json_data
            
        except Exception as e:
            logger.error(f"Flight GPT-4o extraction failed: {str(e)}")
            raise
    
    def _parse_json_response(self, response: str) -> Dict:
        """Parse JSON from AI response"""
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
    
    def _process_flight_extractions(self, raw_data: Dict) -> List[FlightExtraction]:
        """Process flight extraction results into FlightExtraction objects"""
        
        flights = []
        
        if 'flights' not in raw_data:
            logger.warning("No 'flights' key found in extraction result")
            return flights
        
        for i, flight_data in enumerate(raw_data['flights']):
            try:
                # Process each field with validation and normalization
                processed_data = self._post_process_single_flight(flight_data)
                
                # Add metadata from the overall extraction
                processed_data['confidence_score'] = raw_data.get('confidence_score', 0.5)
                processed_data['extraction_reasoning'] = raw_data.get('analysis', '')
                
                # Create FlightExtraction object
                flight = FlightExtraction(**processed_data)
                flights.append(flight)
                
            except Exception as e:
                logger.warning(f"Failed to process flight {i+1}: {str(e)}")
                continue
        
        return flights
    
    def _post_process_single_flight(self, flight_data: Dict) -> Dict:
        """Post-process a single flight's data"""
        processed = {}
        
        # Process each field with validation and normalization
        for field, value in flight_data.items():
            if value is None or (isinstance(value, str) and value.lower() in ['null', 'none', 'not provided', '']):
                processed[field] = None
            elif isinstance(value, str):
                value = value.strip()
                
                # Field-specific processing
                if field in ['departure_airport', 'arrival_airport']:
                    processed[field] = self._normalize_airport_code(value)
                elif field == 'airline':
                    processed[field] = self._normalize_airline_name(value)
                elif field in ['departure_date', 'arrival_date']:
                    processed[field] = self._normalize_date(value)
                elif field in ['departure_time', 'arrival_time']:
                    processed[field] = self._normalize_time(value)
                else:
                    processed[field] = value if value else None
            else:
                processed[field] = value
        
        return processed
    
    def _normalize_airport_code(self, airport: str) -> str:
        """Normalize airport codes"""
        if not airport:
            return None
        
        airport_lower = airport.lower().strip()
        
        # Check for exact matches
        if airport_lower in self.airport_mappings:
            return self.airport_mappings[airport_lower]
        
        # Extract 3-letter codes
        code_match = re.search(r'\b([A-Z]{3})\b', airport.upper())
        if code_match:
            return code_match.group(1)
        
        return airport.upper()
    
    def _normalize_airline_name(self, airline: str) -> str:
        """Normalize airline names"""
        if not airline:
            return None
        
        airline_lower = airline.lower().strip()
        
        # Check for airline code matches
        for code, name in self.airline_mappings.items():
            if code in airline_lower:
                return name
        
        return airline.title()
    
    def _normalize_date(self, date_str: str) -> str:
        """Convert various date formats to YYYY-MM-DD"""
        if not date_str:
            return None
        
        date_str = date_str.strip().lower()
        current_year = datetime.now().year
        
        # Pattern 1: "12th Sep", "12 September", "12-Sep-25"
        pattern1 = r'(\d{1,2})(?:st|nd|rd|th)?[\s\-]+(sep|sept|september|jan|january|feb|february|mar|march|apr|april|may|jun|june|jul|july|aug|august|oct|october|nov|november|dec|december)(?:[\s\-]+(\d{2,4}))?'
        match = re.search(pattern1, date_str)
        if match:
            day, month_name, year = match.groups()
            year = year or str(current_year)
            if len(year) == 2:
                year = "20" + year
            
            month_mappings = {
                'jan': '01', 'january': '01', 'feb': '02', 'february': '02',
                'mar': '03', 'march': '03', 'apr': '04', 'april': '04',
                'may': '05', 'jun': '06', 'june': '06', 'jul': '07', 'july': '07',
                'aug': '08', 'august': '08', 'sep': '09', 'sept': '09', 'september': '09',
                'oct': '10', 'october': '10', 'nov': '11', 'november': '11',
                'dec': '12', 'december': '12'
            }
            
            if month_name in month_mappings:
                month = month_mappings[month_name]
                return f"{year}-{month}-{day.zfill(2)}"
        
        # Pattern 2: "12/09/2025", "12-09-25"
        pattern2 = r'(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})'
        match = re.search(pattern2, date_str)
        if match:
            day, month, year = match.groups()
            if len(year) == 2:
                year = "20" + year
            return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
        
        # Return original if can't parse
        logger.warning(f"Could not parse date: {date_str}")
        return date_str
    
    def _normalize_time(self, time_str: str) -> str:
        """Convert various time formats to HH:MM (24-hour)"""
        if not time_str:
            return None
        
        time_str = time_str.strip().lower()
        
        # Pattern 1: "7:30 AM/PM", "19:30"
        pattern1 = r'(\d{1,2})[:\.](\d{2})\s*(am|pm)?'
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
        
        # Pattern 2: "1930 hrs", "0730"
        pattern2 = r'(\d{4})\s*hrs?'
        match = re.search(pattern2, time_str)
        if match:
            time_digits = match.group(1)
            hour = int(time_digits[:2])
            minute = int(time_digits[2:])
            return f"{hour:02d}:{minute:02d}"
        
        # Return original if can't parse
        logger.warning(f"Could not parse time: {time_str}")
        return time_str

def test_flight_agent():
    """Test the flight agent with sample data"""
    try:
        agent = FlightDetailsAIAgent()
        
        sample_flight_doc = """
        FLIGHT ITINERARY
        
        Passenger: John Smith
        PNR: ABC123
        
        Flight AI 2859
        Delhi (DEL) to Mumbai (BOM)
        Date: 12-Sep-2025
        Departure: 07:30
        Arrival: 09:45
        Seat: 14A
        Gate: 12
        Terminal: 3
        """
        
        result = agent.extract_flight_details(sample_flight_doc)
        
        print("Flight Extraction Results:")
        print(f"Found {result.total_flights_found} flight(s)")
        
        for i, flight in enumerate(result.flights, 1):
            print(f"\nFlight {i}:")
            print(f"  Flight: {flight.flight_number}")
            print(f"  From: {flight.departure_airport} at {flight.departure_time}")
            print(f"  To: {flight.arrival_airport} at {flight.arrival_time}")
            print(f"  Passenger: {flight.passenger_name}")
            
    except Exception as e:
        print(f"Test failed: {str(e)}")

if __name__ == "__main__":
    test_flight_agent()
