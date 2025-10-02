"""
Agent 5: Special Requirements Agent
Extracts driver details, cancellation info, and rate negotiations
"""

from agents.base_agent import BaseAgent
from typing import List
import logging

logger = logging.getLogger(__name__)

class SpecialRequirementsAgent(BaseAgent):
    """
    Specialized agent for extracting special requirements and additional details
    """
    
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        """Initialize the special requirements agent"""
        super().__init__(api_key, model)
    
    def get_target_fields(self) -> List[str]:
        """Fields this agent extracts"""
        return [
            'rate',
            'rate_unit',
            'driver_name',
            'driver_phone',
            'driver_license',
            'cancellation_type',
            'cancellation_time',
            'cancellation_reason',
            'remarks',
            'labels'
        ]
    
    def build_extraction_prompt(self) -> str:
        """Build specialized prompt for special requirements extraction"""
        
        return f"""You are a specialized AI agent for extracting SPECIAL REQUIREMENTS and ADDITIONAL DETAILS from car rental requests.

**YOUR RESPONSIBILITY:**
Extract only these 10 fields:
1. rate - Quoted price/fare (numeric only)
2. rate_unit - Unit of pricing (per km, per hour, total, etc.)
3. driver_name - Driver's full name if mentioned
4. driver_phone - Driver's contact number
5. driver_license - Driver's license number if specified
6. cancellation_type - Type of cancellation if booking is cancelled
7. cancellation_time - When cancellation occurred
8. cancellation_reason - Reason for cancellation
9. remarks - ALL extra information that doesn't fit into other fields
10. labels - Specific passenger labels (LadyGuest, VIP only)

**RATE EXTRACTION LOGIC:**

**RATE PATTERNS TO LOOK FOR:**
- "Rs. 1500", "₹2000", "1200/-", "$50"
- "1800 total", "2500 for the trip"
- "40 per km", "100/hour"
- "Negotiated at 1600", "Final rate 1750"

**RATE UNIT IDENTIFICATION:**
- **per_km**: "per km", "/km", "per kilometer"
- **per_hour**: "per hour", "/hour", "hourly rate"
- **total**: "total", "lump sum", "package rate", "fixed"
- **per_trip**: "per trip", "one way", "for the journey"
- **per_day**: "per day", "/day", "daily rate"

**DRIVER DETAILS LOGIC:**

**DRIVER NAME PATTERNS:**
- "Driver: Ramesh Kumar"
- "Mr. Suresh will be driving"
- "Assigned driver - Rajesh"
- "Your driver is Prakash"

**DRIVER PHONE PATTERNS:**
- Mobile numbers: 10-digit Indian numbers
- "Driver contact: 9876543210"
- "Call driver at +91-9988776655"

**DRIVER LICENSE PATTERNS:**
- "DL: MH123456789012"
- "License No: KA1234567890123"
- Any alphanumeric license format

**CANCELLATION LOGIC:**

**CANCELLATION TYPES:**
- **client_initiated**: Customer/client cancelled
- **company_initiated**: Company cancelled
- **no_show**: Passenger didn't show up
- **breakdown**: Vehicle breakdown/technical issue
- **weather**: Weather-related cancellation
- **other**: Any other reason

**CANCELLATION TIME PATTERNS:**
- Look for timestamps, dates, or relative times
- "Cancelled at 2:30 PM", "Cancelled 1 hour before"
- "Booking cancelled on 15th Jan"

**CANCELLATION REASONS:**
- Direct quotes: "Flight delayed", "Meeting cancelled"
- Inferred reasons: "Emergency", "Change of plans"
- Technical: "Vehicle not available", "Driver unavailable"

**TABLE PROCESSING:**
- Look for "Rate", "Fare", "Amount" rows/columns
- Check for "Driver", "Assigned to" fields
- Look for "Status", "Cancelled", "Remarks" columns
- Extract driver details from contact columns

**EMAIL PROCESSING:**
- Scan entire email for rate negotiations
- Look for driver assignment notifications
- Check for cancellation communications
- Extract special instructions or requirements

**REMARKS EXTRACTION LOGIC:**

**CRITICAL: NO INFORMATION SHOULD BE OMITTED**
- Extract ALL extra information provided by the booker that doesn't fit into other fields
- Include driver details, special instructions, preferences, requirements
- **SPECIAL FOCUS**: Capture vague instructions like "As per instructions", "As per guest requirements", "As per client needs"
- Copy and paste exact text without summarizing or changing
- Examples of remarks content:
  - "Please ensure AC is working properly"
  - "Driver should speak English"
  - "Passenger has mobility issues"
  - "Need child seat"
  - "Prefer experienced driver for outstation trip"
  - "Contact passenger 30 minutes before pickup"
  - "Vehicle should be clean and well-maintained"
  - **"As per guest instructions & meetings"** 
  - **"As per instructions"**
  - **"As per client requirements"**
  - **"Usage: As per Ashish's Instructions & meetings"**
  - Any other special instructions or requirements

**LABELS EXTRACTION LOGIC:**

**ONLY 3 LABELS ARE USED:**
1. **LadyGuest** - Use ONLY if "Ms" or "Mrs" is mentioned in passenger information
2. **VIP** - Use ONLY if booker explicitly specifies passenger is VIP
3. **MD's Guest** - Ignore for now (not to be extracted)

**LABEL RULES:**
- Check passenger names for "Ms." "Mrs." titles
- Look for explicit VIP mentions: "VIP guest", "VIP passenger", "VIP treatment"
- Multiple labels can be applied (comma-separated)
- If no labels apply, return null

**SPECIAL INSTRUCTIONS:**
- Rates should be numeric only (remove currency symbols)
- Phone numbers should include country code if available
- Preserve exact cancellation reasons as quoted
- Handle multiple drivers if mentioned (use primary/main driver)
- REMARKS: Include ALL information - nothing should be omitted
- LABELS: Only use LadyGuest (for Ms/Mrs) and VIP (if explicitly mentioned)

{self.get_standard_field_instructions()}

**OUTPUT FORMAT:**
Return ONLY a JSON object with these exact fields:
{{
    "rate": "Numeric value only or null",
    "rate_unit": "per_km/per_hour/total/per_trip/per_day or null",
    "driver_name": "Full driver name or null",
    "driver_phone": "Phone number or null",
    "driver_license": "License number or null",
    "cancellation_type": "client_initiated/company_initiated/no_show/breakdown/weather/other or null",
    "cancellation_time": "Timestamp/date or null",
    "cancellation_reason": "Exact reason text or null",
    "remarks": "ALL extra information from booking - exact text without omissions or null",
    "labels": "LadyGuest, VIP (comma-separated if multiple) or null"
}}

**EXAMPLES:**

Example 1 - Rate negotiation:
rate: "1800"
rate_unit: "total"
driver_name: null
driver_phone: null

Example 2 - Driver assignment:
rate: null
rate_unit: null
driver_name: "Ramesh Kumar"
driver_phone: "9876543210"
driver_license: "MH123456789012"

Example 3 - Cancellation:
rate: null
rate_unit: null
cancellation_type: "client_initiated"
cancellation_time: "2024-01-15 14:30"
cancellation_reason: "Flight got delayed by 4 hours"

**IMPORTANT:**
- Extract only when explicitly mentioned
- Don't infer rates from standard packages
- Preserve exact wording for reasons
- Handle multiple phone numbers (use primary)
- Default all fields to null if not found"""
    
    def process_booking_data(self, booking_data: dict, shared_context: dict) -> dict:
        """Process booking data with enhanced context from previous agents"""
        
        # Add any special processing for rates, drivers, and cancellations
        # This could include validation against previous agent results
        result = super().process_booking_data(booking_data, shared_context)
        
        # Log special requirements found
        extracted = result.get('extracted_fields', {})
        if extracted.get('rate'):
            logger.info(f"Rate found: {extracted['rate']} {extracted.get('rate_unit', '')}")
        if extracted.get('driver_name'):
            logger.info(f"Driver assigned: {extracted['driver_name']}")
        if extracted.get('cancellation_type'):
            logger.info(f"Cancellation detected: {extracted['cancellation_type']}")
            
        return result