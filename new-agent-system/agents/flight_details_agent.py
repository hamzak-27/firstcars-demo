"""
Agent 6: Flight Details Agent
Extracts flight numbers, train numbers, and related travel details
"""

from agents.base_agent import BaseAgent
from typing import List
import logging

logger = logging.getLogger(__name__)

class FlightDetailsAgent(BaseAgent):
    """
    Specialized agent for extracting flight and train details
    """
    
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        """Initialize the flight details agent"""
        super().__init__(api_key, model)
    
    def get_target_fields(self) -> List[str]:
        """Fields this agent extracts"""
        return [
            'flight_train_number'
        ]
    
    def build_extraction_prompt(self) -> str:
        """Build specialized prompt for flight and train details extraction"""
        
        return f"""You are a specialized AI agent for extracting FLIGHT and TRAIN DETAILS from car rental requests.

**YOUR RESPONSIBILITY:**
Extract only this 1 field:
1. flight_train_number - ALL complete flight details and train numbers mentioned

**COMPLETE FLIGHT DETAILS EXTRACTION LOGIC:**

**EXTRACT COMPLETE FLIGHT STRINGS:**
- Standard airline codes: "AI 101", "6E 234", "SG 567", "UK 890"
- Full airline names: "Air India 101", "IndiGo 6E 234", "SpiceJet SG 567"
- International: "Emirates EK 506", "Qatar QR 570", "Singapore SQ 401"
- **COMPLETE GDS/Complex Data**: Extract the ENTIRE flight string as-is
- Complex airline data: "6E 429 Y 27SEP 6 IXCBLR GK1 1715 2020" → "6E 429 Y 27SEP 6 IXCBLR GK1 1715 2020"
- GDS format: "2 6E 429 Y 27SEP 6 IXCBLR GK1 1715 2020 27SEP EZJVVL" → "6E 429 Y 27SEP 6 IXCBLR GK1 1715 2020 27SEP EZJVVL"

**AIRLINE CODE EXAMPLES:**
- Air India: AI, 9W
- IndiGo: 6E  
- SpiceJet: SG
- Vistara: UK
- GoAir: G8
- AirAsia: I5
- Emirates: EK
- Qatar Airways: QR
- Singapore Airlines: SQ
- Thai Airways: TG
- Lufthansa: LH
- British Airways: BA

**TRAIN NUMBER PATTERNS:**
- Express trains: "12301 Rajdhani", "12951 Mumbai Rajdhani"
- Local trains: "Train number 16609", "16609 Bangalore Express"
- Shatabdi: "12049 Shatabdi", "12002 New Delhi Shatabdi"
- With names: "12301 Howrah Rajdhani Express"

**EXTRACTION RULES:**

**MULTIPLE COMPLETE FLIGHT/TRAIN DETAILS:**
- Extract ALL complete flight and train details mentioned in the booking
- For complex/GDS data, extract the ENTIRE string including all codes, times, dates
- Separate multiple entries with commas
- Examples:
  - "Flight AI 101 and return flight AI 102" → "AI 101, AI 102"
  - Complex GDS: "6E 429 Y 27SEP 6 IXCBLR GK1 1715 2020" → "6E 429 Y 27SEP 6 IXCBLR GK1 1715 2020"
  - "Train 12301 and connecting flight AI 405" → "12301, AI 405"

**CONTEXT CLUES:**
- Look for words: "flight", "plane", "aircraft", "train", "railway"
- Arrival/departure context: "arriving on", "departing by", "catching flight"
- Time context: "6 AM flight", "morning train", "evening departure"
- Airport context: "flight from DEL", "plane to BOM"

**FORMAT STANDARDIZATION:**
- For simple flights: Keep airline codes in UPPERCASE: "ai 101" → "AI 101"
- For complex GDS data: **PRESERVE EXACTLY AS FOUND** - do not modify, clean or standardize
- Keep original train number format
- Remove only introductory words: "Flight number AI 101" → "AI 101"
- **CRITICAL**: For complex strings like "6E 429 Y 27SEP 6 IXCBLR GK1 1715 2020", keep the entire string intact

**TABLE PROCESSING:**
- Look for "Flight No", "Flight", "Train No", "Travel Details" columns
- Check "Arrival", "Departure" related fields
- Extract from journey/itinerary sections

**EMAIL PROCESSING:**
- Scan entire email content for flight/train references
- Check subject line for flight numbers
- Look in itinerary sections, travel details, booking confirmations
- Pay attention to arrival/departure information

**COMPLEX FLIGHT DATA PATTERNS - EXTRACT COMPLETE STRINGS:**
- **GDS/Amadeus Format**: "2 6E 429 Y 27SEP 6 IXCBLR GK1 1715 2020 27SEP EZJVVL"
  → Extract: "6E 429 Y 27SEP 6 IXCBLR GK1 1715 2020 27SEP EZJVVL" (ENTIRE string)
- **PNR Data**: Multi-line flight records - extract each complete line
- **Booking Systems**: Complex strings - preserve ALL codes, times, dates, confirmations
- **Key Rule**: Extract from first airline code to last meaningful code/time
- **Airport Codes**: Include IXCBLR, DELBOM etc. in the extracted string
- **Time Stamps**: Include 1715, 2020 etc. in the extracted string

**IMPORTANT PATTERNS:**
- Simple flights: 2-3 letter airline code + 2-4 digits ("AI 101")
- Train numbers: 4-5 digits, sometimes with names ("12301 Rajdhani")
- **Complex GDS data**: Extract COMPLETE string including fare class, times, dates, airport codes
- Multiple segments: Extract each complete segment separately
- Layovers: "via Dubai on EK 506, then EK 508 to Delhi" → "EK 506, EK 508"
- **Complex data rule**: PRESERVE ALL flight information - codes, times, dates, airport codes, everything

{self.get_standard_field_instructions()}

**OUTPUT FORMAT:**
Return ONLY a JSON object with this exact field:
{{
    "flight_train_number": "All flight/train numbers comma-separated or null"
}}

**EXAMPLES:**

Example 1 - Single flight:
flight_train_number: "AI 101"

Example 2 - Multiple flights:
flight_train_number: "6E 234, AI 405, EK 506"

Example 3 - Flight and train:
flight_train_number: "12301, AI 567"

Example 4 - Return journey:
flight_train_number: "SG 234, SG 235"

Example 5 - Complex GDS data (COMPLETE extraction):
Input: "2 6E 429 Y 27SEP 6 IXCBLR GK1 1715 2020 27SEP EZJVVL"
flight_train_number: "6E 429 Y 27SEP 6 IXCBLR GK1 1715 2020 27SEP EZJVVL"

Example 6 - Multiple complex entries (COMPLETE extraction):
Input: "AI 234 J 15OCT MUMBAI DELHI 0800 1000 + 6E 567 Y 15OCT DELHI BANGALORE 1200 1400"
flight_train_number: "AI 234 J 15OCT MUMBAI DELHI 0800 1000, 6E 567 Y 15OCT DELHI BANGALORE 1200 1400"

Example 7 - No travel details:
flight_train_number: null

**IMPORTANT:**
- Extract ALL complete flight and train details mentioned
- For complex GDS data: Include ALL codes, times, dates, airport codes
- Use comma separation for multiple entries
- **DO NOT clean or standardize complex flight strings - preserve exactly as found**
- Include both directions for round trips (complete details for each)
- Return null if no flight/train details found
- Don't include bus, taxi, or other transport numbers"""
    
    def process_booking_data(self, booking_data: dict, shared_context: dict) -> dict:
        """Process booking data with enhanced context from previous agents"""
        
        result = super().process_booking_data(booking_data, shared_context)
        
        # Log flight details found
        extracted = result.get('extracted_fields', {})
        if extracted.get('flight_train_number'):
            logger.info(f"Flight/Train details found: {extracted['flight_train_number']}")
            
        return result