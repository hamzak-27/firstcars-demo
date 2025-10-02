"""
Agent 1: Corporate and Booker Details Agent
Extracts company information and booker details with CSV validation
"""

from agents.base_agent import BaseAgent
from typing import List
import pandas as pd
import logging
import os

logger = logging.getLogger(__name__)

class CorporateBookerAgent(BaseAgent):
    """
    Specialized agent for extracting corporate and booker information
    """
    
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        """Initialize agent and load corporate CSV data"""
        super().__init__(api_key, model)
        self.corporate_df = self._load_corporate_csv()
    
    def _load_corporate_csv(self) -> pd.DataFrame:
        """Load Corporate (1).csv file for company validation"""
        try:
            csv_path = "../Corporate (1).csv"  # Relative to new-agent-system directory
            if os.path.exists(csv_path):
                df = pd.read_csv(csv_path)
                logger.info(f"Loaded corporate CSV with {len(df)} companies")
                return df
            else:
                logger.warning(f"Corporate CSV not found at {csv_path}")
                return pd.DataFrame()
        except Exception as e:
            logger.error(f"Error loading corporate CSV: {e}")
            return pd.DataFrame()
    
    def get_target_fields(self) -> List[str]:
        """Fields this agent extracts"""
        return [
            'corporate_name',
            'booker_name', 
            'booker_phone',
            'booker_email'
        ]
    
    def build_extraction_prompt(self) -> str:
        """Build specialized prompt for corporate and booker extraction"""
        
        # Create corporate lookup table from CSV for the prompt
        corporate_lookup = ""
        if not self.corporate_df.empty:
            # Get sample companies for the prompt (first 20)
            sample_companies = self.corporate_df.head(20)
            corporate_lookup = "\n**CORPORATE DATABASE SAMPLE:**\n"
            for _, row in sample_companies.iterrows():
                corp_name = row.get('Corporate', '')
                booker_involved = row.get('Booker involved or direct', '')
                corporate_lookup += f"- {corp_name}: Booker {booker_involved}\n"
            corporate_lookup += f"... and {len(self.corporate_df) - 20} more companies in database\n"
        
        return f"""You are a specialized AI agent for extracting CORPORATE and BOOKER information from car rental requests.

**YOUR RESPONSIBILITY:**
Extract only these 4 fields:
1. corporate_name - Company/organization name
2. booker_name - Person making the booking (if involved)
3. booker_phone - Booker's contact number
4. booker_email - Booker's email address

**CRITICAL SELF-BOOKING DETECTION:**
⚠️ **ANALYZE EMAIL LANGUAGE CAREFULLY:**
- If email says "book a cab for me", "I need a car", "my requirement", "pickup me" → SELF-BOOKING
- If email says "book for Mr. X", "passenger will be Y", "guest needs car" → THIRD-PARTY BOOKING
- Self-booking means: sender = passenger, extract sender details as both booker AND passenger info
- Third-party booking: sender = booker, passenger is someone else mentioned in email

**CRITICAL BUSINESS LOGIC:**

**STEP 1: CORPORATE IDENTIFICATION**
- Look for company names, organization names, corporate signatures
- Check email domains for corporate identification (@company.com patterns)
- Look for letterheads, corporate footers, company stamps
- Check email sender data (if provided separately)
- Examples: "Microsoft", "TCS", "Infosys", "LTPL (Lendingkart Technologies)"
- **PRIORITY**: If sender email provided, extract company from domain first

**SELF-BOOKING SCENARIO EXAMPLE:**
```
Email from: ganesan.k@medtronic.com
Content: "Kindly confirm a cab for me for the following requirement...
Regards, Ganesan K"

→ ANALYSIS:
1. Corporate: "Medtronic" (extracted from email domain)
2. Self-booking detected ("for me", "my requirement")
3. Sender/Booker/Passenger: Ganesan K (same person)
4. Check Medtronic in corporate database for booker involvement
5. If booker involved → extract Ganesan's details as booker
6. If direct → set booker fields to null (direct booking)
```

{corporate_lookup}

**STEP 2: BOOKER EXTRACTION LOGIC**
⚠️ **CONDITIONAL EXTRACTION:** Extract booker details ONLY if:
1. Company is found in the corporate database AND
2. The company's "Booker involved or direct" column says "involved"

If company not in database OR says "direct": Set all booker fields to null

**BOOKER IDENTIFICATION (when applicable):**
- Person who is making/coordinating the booking request
- May be different from the passenger
- Look for signatures, "Regards", "From", "Booked by"
- Travel coordinators, admins, assistants
- Check email sender information

**TABLE PROCESSING:**
- **Form Tables**: Look for Field-Value pairs in booking forms
- Key fields: "Company Name", "Name & Contact Number of booker", "Email ID of booker"
- Extract company from "Company Name" field value
- Extract booker details from corresponding form fields
- **Multi-column Tables**: Look for "Company", "Booked By", "Corporate" columns
- Extract company from appropriate cell based on booking number

**FORM DATA EXAMPLES:**

**Example 1 - Medtronic Form:**
```
Field: "Company Name" → Value: "India Medtronic Pvt. Ltd."
Field: "Name & Contact Number of booker" → Value: "Hiba Mohammed"
Field: "Email ID of booker" → Value: "hiba.mohammed@medtronic.com"

→ EXTRACT:
- Corporate: "Medtronic" (normalized from "India Medtronic Pvt. Ltd.")
- Booker Name: "Hiba Mohammed"
- Booker Email: "hiba.mohammed@medtronic.com"
```

**Example 2 - Booker vs Passenger Form:**
```
Field: "Name of the booker / requester" → Value: "MR. Sujoy Baidya-9870419192"
Field: "Booker's Landline and Mobile No. (Must)" → Value: "022-66591333"
Field: "Name of the user" → Value: "Mr. Rahul Waghmare"
Field: "User's Contact no" → Value: "7506403838"

→ EXTRACT:
- Booker Name: "MR. Sujoy Baidya" (from "Name of the booker / requester" field)
- Booker Phone: "9870419192, 02266591333" (extract from booker name and landline fields)
- NOTE: "Name of the user" and "User's Contact no" are PASSENGER details (other agent's job)
```

**EMAIL PROCESSING:**
- Extract company from email signatures, headers, domain
- Extract booker from sender info, signatures
- Check if email sender data is provided separately

**FALLBACK RULES:**
- If company name not found anywhere: corporate = "NA"
- If company found but not in database: extract booker anyway (assume involved)
- If company requires booker but no booker details found: set booker fields to null

{self.get_standard_field_instructions()}

**OUTPUT FORMAT:**
Return ONLY a JSON object with these exact fields:
{{
    "corporate_name": "Company name or NA",
    "booker_name": "Booker name or null (based on company rules)", 
    "booker_phone": "Booker phone (10 digits) or null (based on company rules)",
    "booker_email": "Booker email or null (based on company rules)"
}}

**EXAMPLES:**

Example 1 - Company requires booker:
Corporate: "TCS" (found in DB, Booker involved)
→ Extract all booker details

Example 2 - Company is direct:  
Corporate: "ABC Corp" (found in DB, Booker direct)
→ Set all booker fields to null

Example 3 - Company not found:
Corporate: "Unknown Company" (not in database)
→ Extract booker details anyway (assume involved)

**IMPORTANT:**
- Focus ONLY on company and booker details
- Do NOT extract passenger information (that's for another agent)
- Apply the conditional booker logic strictly
- Use null for missing information
- Ensure phone numbers are 10 digits only"""
    
    def extract_fields(self, content: str, context: dict) -> dict:
        """Override to add post-processing with CSV lookup"""
        
        # First get the raw extraction
        raw_result = super().extract_fields(content, context)
        
        # Apply CSV validation logic
        return self._apply_corporate_validation(raw_result)
    
    def _apply_corporate_validation(self, raw_result: dict) -> dict:
        """Apply corporate CSV validation to determine if booker extraction is needed"""
        
        corporate_name = raw_result.get('corporate_name', '')
        
        if not corporate_name or corporate_name == 'NA':
            return raw_result
        
        if self.corporate_df.empty:
            # No CSV data, assume booker involved
            logger.warning("No corporate CSV data available, assuming booker involved")
            return raw_result
        
        # Search for company in CSV (case-insensitive partial matching)
        company_row = None
        corporate_lower = corporate_name.lower()
        
        for _, row in self.corporate_df.iterrows():
            csv_company = str(row.get('Corporate', '')).lower()
            if csv_company and (corporate_lower in csv_company or csv_company in corporate_lower):
                company_row = row
                break
        
        if company_row is not None:
            booker_status = str(company_row.get('Booker involved or direct', '')).lower()
            logger.info(f"Found company '{corporate_name}' in CSV with booker status: {booker_status}")
            
            if 'direct' in booker_status:
                # Company is direct, clear all booker fields
                raw_result['booker_name'] = None
                raw_result['booker_phone'] = None  
                raw_result['booker_email'] = None
                logger.info(f"Company '{corporate_name}' is direct - cleared booker fields")
            # If 'involved', keep the extracted booker details
        else:
            # Company not found in CSV, assume booker involved (keep extracted data)
            logger.info(f"Company '{corporate_name}' not found in CSV - assuming booker involved")
        
        return raw_result
