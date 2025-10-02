"""
Agent 4: Duty Type and Vehicle Agent
Determines duty type (G2G/P2P packages) and vehicle group with CSV mappings
"""

from agents.base_agent import BaseAgent
from typing import List
import pandas as pd
import logging
import os

logger = logging.getLogger(__name__)

class DutyVehicleAgent(BaseAgent):
    """
    Specialized agent for extracting duty type and vehicle information
    """
    
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        """Initialize agent and load CSV mapping data"""
        super().__init__(api_key, model)
        self.corporate_df = self._load_corporate_csv()
        self.vehicle_df = self._load_vehicle_csv()
    
    def _load_corporate_csv(self) -> pd.DataFrame:
        """Load Corporate (1).csv file for G2G/P2P determination"""
        try:
            # Use relative path from project root
            csv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Corporate (1).csv")
            if os.path.exists(csv_path):
                df = pd.read_csv(csv_path)
                logger.info(f"✅ Loaded corporate CSV with {len(df)} companies")
                return df
            else:
                logger.warning(f"Corporate CSV not found at {csv_path}")
                return pd.DataFrame()
        except Exception as e:
            logger.error(f"Error loading corporate CSV: {e}")
            return pd.DataFrame()
    
    def _load_vehicle_csv(self) -> pd.DataFrame:
        """Load Car.xlsx - Sheet1.csv file for vehicle mapping"""
        try:
            # Use relative path from project root
            csv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Car.xlsx - Sheet1.csv")
            if os.path.exists(csv_path):
                df = pd.read_csv(csv_path)
                logger.info(f"✅ Loaded vehicle CSV with {len(df)} vehicles")
                return df
            else:
                logger.warning(f"Vehicle CSV not found at {csv_path}")
                return pd.DataFrame()
        except Exception as e:
            logger.error(f"Error loading vehicle CSV: {e}")
            return pd.DataFrame()
    
    def get_target_fields(self) -> List[str]:
        """Fields this agent extracts"""
        return [
            'duty_type',
            'vehicle_group'
        ]
    
    def build_extraction_prompt(self) -> str:
        """Build specialized prompt for duty type and vehicle extraction"""
        
        # Create vehicle lookup table from CSV for the prompt
        vehicle_lookup = ""
        if not self.vehicle_df.empty:
            # Get sample vehicles for the prompt
            sample_vehicles = self.vehicle_df.head(15)
            vehicle_lookup = "\n**VEHICLE MAPPING DATABASE SAMPLE:**\n"
            for _, row in sample_vehicles.iterrows():
                car_name = row.get('Car name (As per mail)', '')
                vehicle_group = row.get('Vehicle Group (To be entered in Indecab)', '')
                if car_name and vehicle_group:
                    vehicle_lookup += f"- {car_name} → {vehicle_group}\n"
            vehicle_lookup += f"... and {len(self.vehicle_df) - 15} more vehicles in database\n"
        
        return f"""You are a specialized AI agent for extracting DUTY TYPE and VEHICLE information from car rental requests.

**YOUR RESPONSIBILITY:**
Extract only these 2 fields:
1. duty_type - Service package type with G2G/P2P prefix
2. vehicle_group - Standardized vehicle name from mapping

**CRITICAL DUTY TYPE LOGIC:**

**STEP 1: DETERMINE G2G vs P2P**
From previous agent results, get the corporate name and determine:
- G2G (Garage to Garage): Pre-approved corporate clients
- P2P (Point to Point): Individual or non-listed corporates
- Check Corporate (1).csv database for company classification

**STEP 2: IDENTIFY SERVICE TYPE**
Analyze the booking content for these patterns:

| Service Type | Keywords | Package |
|--------------|----------|---------|
| **DROP/AIRPORT** | Drop, Airport Transfer, Pickup, One-way | 04HR 40KMS |
| **DISPOSAL** | At disposal, Local use, Visit + drop back, Whole day use, Use as per guest instructions, Nothing specified | 08HR 80KMS |
| **OUTSTATION** | Different cities, Intercity travel | 250KMS or 300KMS |

**STEP 3: OUTSTATION DISTANCE LOGIC**
For outstation bookings, determine distance based on cities:
- **250KMS Cities:** Mumbai, Pune, Hyderabad, Chennai, Delhi, Ahmedabad, Bangalore
- **300KMS Cities:** Kolkata and all other cities in India

**STEP 4: FINAL DUTY TYPE FORMAT**
Combine G2G/P2P + Service Type:

| Corporate Type | Service | Final Format |
|----------------|---------|--------------|
| G2G | Drop/Airport | G-04HR 40KMS |
| G2G | Disposal | G-08HR 80KMS |
| G2G | Outstation (Major) | G-Outstation 250KMS |
| G2G | Outstation (Others) | G-Outstation 300KMS |
| P2P | Drop/Airport | P-04HR 40KMS |
| P2P | Disposal | P-08HR 80KMS |
| P2P | Outstation (Major) | P-Outstation 250KMS |
| P2P | Outstation (Others) | P-Outstation 300KMS |

**VEHICLE GROUP LOGIC:**

{vehicle_lookup}

**SPECIAL VEHICLE RULES:**
- If only "Sedan" mentioned → "Maruti Dzire"
- Map vehicle names from database exactly
- Use standardized vehicle names from "Vehicle Group (To be entered in Indecab)" column

**TABLE PROCESSING:**
- Look for "Cab Type", "Vehicle", "Car Type" rows/columns
- Look for service type indicators in "Drop at", "Type of duty" fields
- Extract from appropriate cell based on booking number

**EMAIL PROCESSING:**
- Analyze service requirements from email content
- Determine if it's drop, disposal, or outstation service
- Extract vehicle preferences or requirements

{self.get_standard_field_instructions()}

**OUTPUT FORMAT:**
Return ONLY a JSON object with these exact fields:
{{
    "duty_type": "G-04HR 40KMS or P-08HR 80KMS or G-Outstation 250KMS etc.",
    "vehicle_group": "Standardized vehicle name from mapping or null"
}}

**EXAMPLES:**

Example 1 - G2G Airport drop:
duty_type: "G-04HR 40KMS"
vehicle_group: "Toyota Innova Crysta"

Example 2 - P2P Local disposal:
duty_type: "P-08HR 80KMS"  
vehicle_group: "Swift Dzire"

Example 3 - G2G Outstation major city:
duty_type: "G-Outstation 250KMS"
vehicle_group: "Toyota Innova Crysta"

**IMPORTANT:**
- Use EXACT format for duty types (G- or P- prefix)
- Determine G2G/P2P from corporate database lookup
- Apply outstation distance logic correctly
- Use vehicle mapping database for standardized names
- Default to P2P if corporate not found
- Default to 08HR 80KMS if service type unclear"""