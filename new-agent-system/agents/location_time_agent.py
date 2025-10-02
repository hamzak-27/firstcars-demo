"""
Agent 3: Location and Time Agent  
Extracts from/to cities, dates, time, and addresses with city mapping validation
"""

from agents.base_agent import BaseAgent
from typing import List
import pandas as pd
import logging
import os

logger = logging.getLogger(__name__)

class LocationTimeAgent(BaseAgent):
    """
    Specialized agent for extracting location and time information
    """
    
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        """Initialize agent and load city mapping CSV data"""
        super().__init__(api_key, model)
        self.city_df = self._load_city_csv()
    
    def _load_city_csv(self) -> pd.DataFrame:
        """Load City(1).xlsx - Sheet1.csv file for city validation"""
        try:
            csv_path = "../City(1).xlsx - Sheet1.csv"  # Relative to new-agent-system directory
            if os.path.exists(csv_path):
                df = pd.read_csv(csv_path)
                logger.info(f"Loaded city CSV with {len(df)} cities")
                return df
            else:
                logger.warning(f"City CSV not found at {csv_path}")
                return pd.DataFrame()
        except Exception as e:
            logger.error(f"Error loading city CSV: {e}")
            return pd.DataFrame()
    
    def get_target_fields(self) -> List[str]:
        """Fields this agent extracts"""
        return [
            'from_location',  # From (Service Location)
            'to_location',    # To
            'start_date',     # Start Date
            'end_date',       # End Date
            'reporting_time', # Rep. Time
            'reporting_address', # Reporting Address (can be multiple, numbered)
            'drop_address',   # Drop Address (only for 4HR40KMS duties)
            'dispatch_center' # Dispatch center based on from_location city mapping
        ]
    
    def build_extraction_prompt(self) -> str:
        """Build specialized prompt for location and time extraction"""
        
        # Create city lookup table from CSV for the prompt
        city_lookup = ""
        if not self.city_df.empty:
            # Get sample cities for the prompt (first 30)
            sample_cities = self.city_df.head(30)
            city_lookup = "\n**CITY MAPPING DATABASE SAMPLE:**\n"
            for _, row in sample_cities.iterrows():
                city_name = row.get('City name (As per mail)', '')
                dispatch_center = row.get('Dispatch Centre (To be entered in Indecab)', '')
                if city_name and dispatch_center:
                    city_lookup += f"- {city_name} → {dispatch_center}\n"
            city_lookup += f"... and {len(self.city_df) - 30} more cities in database\n"
        
        prompt = f"""You are a specialized AI agent for extracting LOCATION and TIME information from car rental requests.

**YOUR RESPONSIBILITY:**
Extract only these 8 fields:
1. from_location - Source city name ONLY
2. to_location - Destination city name ONLY  
3. start_date - Start date in YYYY-MM-DD format
4. end_date - End date in YYYY-MM-DD format
5. reporting_time - Pickup time in HH:MM format (24-hour)
6. reporting_address - Complete pickup address
7. drop_address - Complete drop address
8. dispatch_center - Dispatch center mapped from from_location city

**CRITICAL LOCATION LOGIC:**

**CITY NAME EXTRACTION:**
⚠️ **CITY NAMES ONLY** in from_location and to_location fields
- Extract city name from full addresses using your knowledge
- Example: "123 MG Road, Bangalore Airport T-2" → "Bangalore"
- Example: "Hotel Taj, Mumbai Sahar" → "Mumbai"

{city_lookup}

**DISPATCH CENTER MAPPING:**
⚠️ **AUTOMATIC CITY TO DISPATCH CENTER MAPPING:**
- Use the city mapping database to find dispatch center for from_location
- Example: If from_location is "Mumbai", find corresponding "Dispatch Centre (To be entered in Indecab)" from CSV
- This mapping is done automatically based on from_location city
- If city not found in database, return null for dispatch_center

**ROUND TRIP LOGIC:**
⚠️ **SPECIAL CASE:** For round trips (A to B back to A):
- When duty mentions "and same day back", "and return", etc. this indicates a round trip!
- For round trips, BOTH from_location AND to_location should be the SAME BASE CITY
- Example: "Mumbai to Aurangabad and same day back" → from: "Mumbai", to: "Mumbai"
- Example: "Travel to Aurangabad and same day back" (from Navi Mumbai) → from: "Mumbai", to: "Mumbai"
- For duty types mentioning: "round trip", "return journey", "back to origin", "same day back", "and return" → Set both from/to as the base city

**DATE PROCESSING:**
- Convert to YYYY-MM-DD format
- Handle relative dates: "tomorrow", "next Monday", "15th Oct"
- If only start date given: end_date = start_date
- Multi-day bookings: extract proper date range

**TIME PROCESSING:**
⚠️ **15-MINUTE TIME INTERVALS MANDATORY:**
- Round ALL times to nearest 15-minute intervals
- Valid intervals: :00, :15, :30, :45
- Examples: 2:23 PM → 2:30 PM, 2:37 PM → 2:30 PM, 2:38 PM → 2:45 PM
- If time is exactly between intervals, round up
- Convert to HH:MM 24-hour format AFTER rounding
- Example: "2:37 PM" → round to "2:30 PM" → "14:30"

**ADDRESS PROCESSING:**

⚠️ **MULTIPLE REPORTING ADDRESSES:**
- Extract ALL reporting addresses if multiple pickups mentioned
- Number them sequentially: "1. Address1, 2. Address2, 3. Address3"
- If email contains numberings/detailed instructions, copy and paste EXACTLY without summarizing
- Example: "First pickup at Hotel A, then Hotel B, finally Hotel C" → "1. Hotel A, 2. Hotel B, 3. Hotel C"
- For single address: just put the address without numbering
- Include landmarks, building names, complete details for driver navigation

⚠️ **DROP ADDRESS RULES:**
- **ONLY for DROP duties (4HR40KMS)** - put complete drop address
- **ALL other duty types** (8HR80KMS, Outstation, etc.) → put "NA" or "-"
- If visits/addresses mentioned for local/outstation duties, DO NOT put in drop_address
- Those visit addresses should go to REMARKS column instead

**TABLE PROCESSING:**
- Look for "City", "Date of Travel", "Pick-up Time", "Pick-up Address", "Drop at" rows/columns
- Extract from appropriate cell based on booking number
- Handle complex date formats in tables

**EMAIL PROCESSING:**
- Extract locations from email content
- Parse date/time information from text
- Handle various date formats and relative dates

{self.get_standard_field_instructions()}

**OUTPUT FORMAT:**
Return ONLY a JSON object with these exact fields:
{{
    "from_location": "City name only or null",
    "to_location": "City name only or null", 
    "start_date": "YYYY-MM-DD or null",
    "end_date": "YYYY-MM-DD or null",
    "reporting_time": "HH:MM (15-minute intervals) or null",
    "reporting_address": "Complete pickup address(es) numbered if multiple or null",
    "drop_address": "Complete drop address (only for 4HR40KMS) or NA",
    "dispatch_center": "Mapped dispatch center or null"
}}

**EXAMPLES:**

Example 1 - Simple trip:
from_location: "Mumbai"
to_location: "Pune" 
start_date: "2025-10-15"
reporting_time: "09:00"

Example 2 - Round trip:
from_location: "Mumbai"
to_location: "Mumbai" 
start_date: "2025-10-15"
end_date: "2025-10-15"
(Even though travel is "Mumbai to Aurangabad and same day back")

Example 3 - Local disposal:
from_location: "Delhi"
to_location: "Delhi"
start_date: "2025-10-15"

**IMPORTANT:**
- Focus ONLY on location and time details
- Extract city names ONLY (not full addresses) for from/to fields
- Handle round trips correctly: SAME BASE CITY for both from/to fields
- Round trip example: "Mumbai to Aurangabad and back" → from="Mumbai", to="Mumbai"
- Use proper date/time formats
- Keep complete addresses for reporting/drop fields
- Use null for missing information"""
        
        return prompt
