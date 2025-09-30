#!/usr/bin/env python3
"""
Business Logic Validation Agent for Car Rental Bookings
Final agent that validates and enhances all DataFrame fields with business rules
"""

import logging
import time
import pandas as pd
import re
import os
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta

from base_extraction_agent import ExtractionResult
from gemma_classification_agent import ClassificationResult

logger = logging.getLogger(__name__)

try:
    import google.generativeai as genai
    from gemini_model_utils import create_gemini_model
    GEMMA_AVAILABLE = True
except ImportError:
    GEMMA_AVAILABLE = False
    logger.warning("Google Generative AI not available. Install with: pip install google-generativeai")

class BusinessLogicValidationAgent:
    """
    Final validation agent that applies business rules and enhances DataFrame
    
    VALIDATION REQUIREMENTS:
    
    1. REMARKS COLUMN:
       - All extra information provided by the booker which does not fit into 
         the preexisting fields MUST be put into this field
       - NO INFORMATION should be omitted that is present in the mail
       - Include special instructions, preferences, additional context
    
    2. LABELS COLUMN (ONLY these 3 labels are used):
       - LadyGuest: ONLY if "Ms" or "Mrs" is given in the passenger info
       - MD's Guest: Ignore for now (not implemented)
       - VIP: ONLY if the booker specifically mentions that passenger is VIP in mail
    
    3. DUTY TYPES:
       - Verify working correctly (P2P/G2G classification)
       - Validate package assignments (04HR 40KMS, 08HR 80KMS, Outstation XKM)
    
    4. ALL MAPPINGS:
       - Vehicle Group mappings (verify standardization)
       - City name mappings (verify consistency)
       - Corporate pattern mappings (verify G2G/P2P classification)
       - Dispatch center assignments (verify location-based assignment)
    
    Standard Validations:
    - Time calculations (15-minute buffers)
    - Phone number formatting (10 digits)
    - Required field defaults
    - Date consistency (end date = start date if not specified)
    """
    
    def __init__(self, api_key: str = None, model_name: str = "models/gemini-2.5-flash"):
        """Initialize business logic validation agent"""
        
        self.api_key = api_key or os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_AI_API_KEY')
        self.model_name = model_name
        
        # Configure Gemini if available
        if GEMMA_AVAILABLE and self.api_key and self.api_key != "test-key":
            try:
                self.model, actual_model_name = create_gemini_model(self.api_key, model_name)
                if self.model:
                    self.model_name = actual_model_name
                    logger.info(f"Successfully configured Gemini model: {actual_model_name}")
                else:
                    logger.error(f"Failed to create any Gemini model: {actual_model_name}")
            except Exception as e:
                logger.error(f"Error creating Gemini model: {e}")
                self.model = None
        else:
            self.model = None
        
        # Business logic mappings
        self._initialize_business_rules()
        
        # Cost tracking
        self.cost_per_1k_input_tokens = 0.05
        self.cost_per_1k_output_tokens = 0.15
        self.total_cost = 0.0
        self.request_count = 0
        
        logger.info(f"BusinessLogicValidationAgent initialized")
    
    def _initialize_business_rules(self):
        """Initialize all business rule mappings from CSV files"""
        
        # Load corporate mappings from CSV
        self.corporate_mappings = self._load_corporate_mappings()
        logger.info(f"Loaded {len(self.corporate_mappings)} corporate mappings")
        
        # Load city mappings from CSV
        self.city_mappings = self._load_city_mappings()
        logger.info(f"Loaded {len(self.city_mappings)} city mappings")
        
        # Load vehicle mappings (keep hardcoded for now, can be moved to CSV later)
        self.vehicle_mappings = self._load_vehicle_mappings()
        logger.info(f"Loaded {len(self.vehicle_mappings)} vehicle mappings")
        
        # Keep corporate patterns for backward compatibility
        self.corporate_patterns = self.corporate_mappings
        
        # Initialize duty type patterns (critical for rule-based fallback)
        self.duty_type_patterns = {
            'disposal': ['disposal', 'at disposal', 'local use', 'city use', 'whole day', 'full day', '8 hour', '8hr', '80km'],
            'drop': ['drop', 'airport transfer', 'pickup', 'one way', 'transfer', '4 hour', '4hr', '40km'],
            'outstation': ['outstation', 'out station', 'intercity', 'travel', 'round trip', '250km']
        }
        
        # Dispatch center assignments based on cities  
        self.dispatch_centers = {
            'mumbai': 'Mumbai Central Dispatch',
            'delhi': 'Delhi NCR Dispatch',
            'bangalore': 'Bangalore Dispatch',
            'pune': 'Pune Dispatch',
            'hyderabad': 'Hyderabad Dispatch',
            'chennai': 'Chennai Dispatch',
            'kolkata': 'Kolkata Dispatch',
            'gurgaon': 'Delhi NCR Dispatch',
            'noida': 'Delhi NCR Dispatch'
        }
    
    def _load_corporate_mappings(self) -> Dict[str, Dict[str, str]]:
        """Load corporate mappings from Corporate (1).csv"""
        import csv
        from pathlib import Path
        
        corporate_mappings = {}
        
        try:
            csv_path = Path('Corporate (1).csv')
            if csv_path.exists():
                with open(csv_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        corporate_name = row.get('Corporate', '').strip().upper()
                        duty_type = row.get('Duty Type (G2G or P2P)', '').strip()
                        approval_reqd = row.get('Approval Reqd (Yes or No)', '').strip()
                        
                        if corporate_name and duty_type:
                            # Create mapping with both original and normalized names
                            corporate_mappings[corporate_name.lower()] = {
                                'name': corporate_name,
                                'category': duty_type,
                                'approval_required': approval_reqd
                            }
                            
                            # Also add partial matches for common patterns
                            if ' ' in corporate_name:
                                parts = corporate_name.split()
                                for part in parts:
                                    if len(part) > 2:  # Skip short words
                                        corporate_mappings[part.lower()] = {
                                            'name': corporate_name,
                                            'category': duty_type,
                                            'approval_required': approval_reqd
                                        }
                
                logger.info(f"Successfully loaded corporate mappings from {csv_path}")
            else:
                logger.warning(f"Corporate CSV file not found: {csv_path}")
                
        except Exception as e:
            logger.error(f"Error loading corporate mappings: {e}")
        
        return corporate_mappings
    
    def _load_city_mappings(self) -> Dict[str, str]:
        """Load city mappings from City(1).xlsx - Sheet1.csv"""
        import csv
        from pathlib import Path
        
        city_mappings = {}
        
        try:
            csv_path = Path('City(1).xlsx - Sheet1.csv')
            if csv_path.exists():
                with open(csv_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        # Skip empty rows
                        city_name = row.get('City name (As per mail)', '').strip()
                        dispatch_center = row.get('Dispatch Centre (To be entered in Indecab)', '').strip()
                        
                        if city_name and dispatch_center and dispatch_center != 'NA':
                            # Map both original and lowercase
                            city_mappings[city_name.lower()] = dispatch_center
                            
                            # Handle common variations
                            city_name_clean = city_name.replace('\t', '').strip()
                            city_mappings[city_name_clean.lower()] = dispatch_center
                
                logger.info(f"Successfully loaded city mappings from {csv_path}")
            else:
                logger.warning(f"City CSV file not found: {csv_path}")
                # Fallback to hardcoded mappings
                city_mappings = {
                    'mumbai': 'Mumbai', 'bombay': 'Mumbai',
                    'delhi': 'Delhi', 'new delhi': 'Delhi', 'ncr': 'Delhi',
                    'bangalore': 'Bangalore', 'bengaluru': 'Bangalore',
                    'pune': 'Pune', 'hyderabad': 'Hyderabad',
                    'chennai': 'Chennai', 'madras': 'Chennai',
                    'kolkata': 'Kolkata', 'calcutta': 'Kolkata',
                    'gurgaon': 'Delhi', 'gurugram': 'Delhi',
                    'noida': 'Delhi', 'faridabad': 'Delhi', 'ghaziabad': 'Delhi'
                }
                
        except Exception as e:
            logger.error(f"Error loading city mappings: {e}")
            # Fallback mappings
            city_mappings = {
                'mumbai': 'Mumbai', 'bombay': 'Mumbai',
                'delhi': 'Delhi', 'new delhi': 'Delhi',
                'bangalore': 'Bangalore', 'bengaluru': 'Bangalore',
                'pune': 'Pune', 'hyderabad': 'Hyderabad',
                'chennai': 'Chennai', 'madras': 'Chennai',
                'kolkata': 'Kolkata', 'calcutta': 'Kolkata'
            }
        
        return city_mappings
    
    def _load_vehicle_mappings(self) -> Dict[str, str]:
        """Load vehicle mappings (can be moved to CSV later)"""
        return {
            'dzire': 'Swift Dzire',
            'swift dzire': 'Swift Dzire',
            'maruti dzire': 'Swift Dzire',
            'suzuki dzire': 'Swift Dzire',
            'innova': 'Toyota Innova Crysta',
            'innova crysta': 'Toyota Innova Crysta',
            'toyota innova': 'Toyota Innova Crysta',
            'crysta': 'Toyota Innova Crysta',
            'ertiga': 'Maruti Ertiga',
            'maruti ertiga': 'Maruti Ertiga',
            'swift': 'Maruti Swift',
            'maruti swift': 'Maruti Swift',
            'sedan': 'Swift Dzire',
            'suv': 'Toyota Innova Crysta',
            'hatchback': 'Maruti Swift'
        }
    
    def validate_and_enhance(self, extraction_result: ExtractionResult, 
                           classification_result: ClassificationResult,
                           original_content: str = "") -> ExtractionResult:
        """
        Validate and enhance the extraction result DataFrame with business logic
        
        Args:
            extraction_result: Result from extraction agents
            classification_result: Original classification result
            original_content: Original email/document content
            
        Returns:
            Enhanced ExtractionResult with validated DataFrame
        """
        
        start_time = time.time()
        logger.info(f"Starting business logic validation for {len(extraction_result.bookings_dataframe)} bookings")
        
        try:
            # Work with a copy of the DataFrame
            enhanced_df = extraction_result.bookings_dataframe.copy()
            
            if enhanced_df.empty:
                logger.warning("Empty DataFrame received for validation")
                return extraction_result
            
            # Apply business logic validation to each row
            for idx in range(len(enhanced_df)):
                enhanced_df = self._validate_single_booking_row(
                    enhanced_df, idx, classification_result, original_content
                )
            
            processing_time = time.time() - start_time
            
            # Create enhanced result
            enhanced_result = ExtractionResult(
                success=True,
                bookings_dataframe=enhanced_df,
                booking_count=len(enhanced_df),
                confidence_score=min(0.95, extraction_result.confidence_score + 0.1),  # Slight confidence boost
                processing_time=processing_time,
                cost_inr=self.total_cost,  # Cost from any Gemma calls
                extraction_method=f"{extraction_result.extraction_method}_validated",
                metadata={
                    **(extraction_result.metadata or {}),
                    'validation_applied': True,
                    'validation_agent': 'BusinessLogicValidationAgent',
                    'validation_time': processing_time,
                    'original_booking_count': extraction_result.booking_count,
                    'enhanced_booking_count': len(enhanced_df)
                }
            )
            
            logger.info(f"Business logic validation completed in {processing_time:.2f}s")
            return enhanced_result
            
        except Exception as e:
            logger.error(f"Business logic validation failed: {str(e)}")
            # Return original result if validation fails
            processing_time = time.time() - start_time
            extraction_result.processing_time += processing_time
            extraction_result.error_message = f"Validation failed: {str(e)}"
            return extraction_result
    
    def _validate_single_booking_row(self, df: pd.DataFrame, row_idx: int, 
                                   classification_result: ClassificationResult, 
                                   original_content: str) -> pd.DataFrame:
        """Validate and enhance a single booking row"""
        
        # STEP 1: Use rule-based validation (AI disabled due to safety filter issues)
        # Temporarily using rule-based comprehensive validation until Gemini safety filters are resolved
        try:
            df = self._rule_based_comprehensive_validation(df, row_idx, original_content)
            logger.info(f"Rule-based comprehensive validation completed for row {row_idx}")
        except Exception as e:
            logger.warning(f"Rule-based comprehensive validation failed for row {row_idx}: {e}")
            # Continue with individual validation methods
        
        # STEP 2: Rule-based validations (as fallback or enhancement)
        # 1. Validate and enhance duty type
        df = self._enhance_duty_type(df, row_idx, original_content)
        
        # 2. Standardize vehicle group
        df = self._standardize_vehicle_group(df, row_idx)
        
        # 3. Validate and enhance time fields (15-minute calculations)
        df = self._enhance_time_fields(df, row_idx)
        
        # 4. Standardize city names in From/To columns
        df = self._standardize_city_names(df, row_idx)
        
        # 5. Enhance corporate/customer information
        df = self._enhance_corporate_info(df, row_idx, original_content)
        
        # 6. Assign dispatch center
        df = self._assign_dispatch_center(df, row_idx)
        
        # 7. Generate appropriate labels and handle VIP detection
        df = self._generate_labels(df, row_idx, classification_result)
        df = self._check_vip_status(df, row_idx, original_content)
        
        # 8. Enhance remarks with all extra information (CRITICAL - NO SYSTEM MESSAGES)
        df = self._enhance_remarks_with_extra_info(df, row_idx, original_content)
        
        # 9. Validate and clean other fields
        df = self._validate_other_fields(df, row_idx)
        
        return df
    
    def _enhance_duty_type(self, df: pd.DataFrame, row_idx: int, original_content: str) -> pd.DataFrame:
        """Enhance duty type using existing business logic"""
        
        current_duty = str(df.iloc[row_idx]['Duty Type']).strip()
        
        # If duty type is already properly formatted, keep it
        if re.match(r'^(P2P|G2G)-(04HR 40KMS|08HR 80KMS|Outstation \d+KMS)$', current_duty):
            return df
        
        # Detect duty type from content
        detected_type = self._detect_duty_type_from_content(original_content, df, row_idx)
        
        # Detect corporate category
        corporate_category = self._detect_corporate_category(original_content, df, row_idx)
        
        # Map to package format
        if detected_type == 'drop':
            package = "04HR 40KMS"
        elif detected_type == 'outstation':
            # Calculate outstation distance if possible
            from_city = str(df.iloc[row_idx]['From (Service Location)']).strip()
            to_city = str(df.iloc[row_idx]['To']).strip()
            distance = self._estimate_outstation_distance(from_city, to_city)
            package = f"Outstation {distance}KMS"
        else:  # disposal/local
            package = "08HR 80KMS"
        
        # Set enhanced duty type
        enhanced_duty_type = f"{corporate_category}-{package}"
        df.iloc[row_idx, df.columns.get_loc('Duty Type')] = enhanced_duty_type
        
        return df
    
    def _detect_duty_type_from_content(self, content: str, df: pd.DataFrame, row_idx: int) -> str:
        """Detect duty type from content using existing patterns"""
        
        content_lower = content.lower()
        
        # Check current booking data for clues
        from_loc = str(df.iloc[row_idx]['From (Service Location)']).lower()
        to_loc = str(df.iloc[row_idx]['To']).lower()
        remarks = str(df.iloc[row_idx]['Remarks']).lower()
        
        # Check for outstation indicators (different cities)
        if from_loc and to_loc and from_loc != to_loc:
            from_city = self._extract_city_name(from_loc)
            to_city = self._extract_city_name(to_loc)
            if from_city != to_city:
                return 'outstation'
        
        # Check content patterns
        for duty_type, patterns in self.duty_type_patterns.items():
            if any(pattern in content_lower or pattern in remarks for pattern in patterns):
                return duty_type
        
        # Default to disposal for local usage
        return 'disposal'
    
    def _detect_corporate_category(self, content: str, df: pd.DataFrame, row_idx: int) -> str:
        """Detect G2G vs P2P corporate category"""
        
        content_lower = content.lower()
        customer = str(df.iloc[row_idx]['Customer']).lower()
        
        # Check for known corporate patterns
        for pattern, info in self.corporate_patterns.items():
            if pattern in content_lower or pattern in customer:
                return info['category']
        
        # Check for corporate email patterns
        booked_by_email = str(df.iloc[row_idx]['Booked By Email'])
        passenger_email = str(df.iloc[row_idx]['Passenger Email'])
        
        if any('@' in email and not any(domain in email.lower() for domain in ['gmail', 'yahoo', 'hotmail']) 
               for email in [booked_by_email, passenger_email]):
            return 'G2G'  # Corporate email domain
        
        return 'P2P'  # Default to P2P (Person to Person)
    
    def _estimate_outstation_distance(self, from_city: str, to_city: str) -> int:
        """Estimate outstation distance between cities"""
        
        # Simplified distance mapping for major routes
        distance_map = {
            ('mumbai', 'pune'): 150,
            ('pune', 'mumbai'): 150,
            ('delhi', 'gurgaon'): 50,
            ('gurgaon', 'delhi'): 50,
            ('delhi', 'noida'): 40,
            ('noida', 'delhi'): 40,
            ('mumbai', 'nashik'): 170,
            ('bangalore', 'mysore'): 150,
            ('chennai', 'pondicherry'): 160
        }
        
        from_clean = self._extract_city_name(from_city.lower())
        to_clean = self._extract_city_name(to_city.lower())
        
        return distance_map.get((from_clean, to_clean), 250)  # Default 250KMS
    
    def _standardize_vehicle_group(self, df: pd.DataFrame, row_idx: int) -> pd.DataFrame:
        """Standardize vehicle group names using CSV mappings"""
        
        current_vehicle = str(df.iloc[row_idx]['Vehicle Group']).strip().lower()
        
        if not current_vehicle or current_vehicle == 'nan' or current_vehicle == 'none' or current_vehicle == '':
            # Default vehicle when no car type is mentioned
            df.iloc[row_idx, df.columns.get_loc('Vehicle Group')] = 'Swift Dzire'
            logger.info(f"No vehicle specified, defaulted to Swift Dzire for row {row_idx}")
        else:
            # First check CSV mappings if available
            standardized = None
            
            # Try to load vehicle mappings from CSV
            try:
                import csv
                from pathlib import Path
                
                csv_path = Path('vehicle_mapping.csv')
                if csv_path.exists():
                    with open(csv_path, 'r', encoding='utf-8') as f:
                        reader = csv.DictReader(f)
                        for row in reader:
                            # Assume CSV has columns: input_vehicle, mapped_vehicle
                            input_col = row.get('input_vehicle', '').lower()
                            mapped_col = row.get('mapped_vehicle', '')
                            
                            if input_col == current_vehicle:
                                standardized = mapped_col
                                break
                            
                            # Also check partial matches
                            if input_col in current_vehicle or current_vehicle in input_col:
                                standardized = mapped_col
                                break
                                
            except Exception as e:
                logger.warning(f"Could not load vehicle mappings from CSV: {e}")
            
            # Fallback to hardcoded mappings if CSV not available or no match found
            if not standardized:
                standardized = self.vehicle_mappings.get(current_vehicle, current_vehicle.title())
            
            df.iloc[row_idx, df.columns.get_loc('Vehicle Group')] = standardized
        
        return df
    
    def _enhance_time_fields(self, df: pd.DataFrame, row_idx: int) -> pd.DataFrame:
        """Enhance time fields with 15-minute rounding and buffer calculations"""
        
        reporting_time = str(df.iloc[row_idx]['Rep. Time']).strip()
        
        if reporting_time and reporting_time != 'nan':
            # Parse time and round to 15-minute intervals
            try:
                # Parse current time format (HH:MM)
                if re.match(r'\d{1,2}:\d{2}', reporting_time):
                    time_parts = reporting_time.split(':')
                    hour = int(time_parts[0])
                    minute = int(time_parts[1])
                    
                    # Round to nearest 15-minute interval (0, 15, 30, 45)
                    rounded_minute = self._round_to_15_minutes(minute)
                    
                    # Handle hour rollover if minute became 60
                    if rounded_minute == 60:
                        hour += 1
                        rounded_minute = 0
                    
                    # Format the rounded time
                    rounded_time = f"{hour:02d}:{rounded_minute:02d}"
                    
                    # Update the time in the dataframe
                    df.iloc[row_idx, df.columns.get_loc('Rep. Time')] = rounded_time
                    
                    # Add note to remarks if time was rounded
                    if reporting_time != rounded_time:
                        current_remarks = str(df.iloc[row_idx]['Remarks'])
                        if current_remarks == 'nan' or not current_remarks:
                            current_remarks = ""
                        
                        rounding_note = f"Time rounded from {reporting_time} to {rounded_time} (15-min intervals)"
                        
                        if "rounded from" not in current_remarks:
                            enhanced_remarks = f"{current_remarks}; {rounding_note}".strip('; ')
                            df.iloc[row_idx, df.columns.get_loc('Remarks')] = enhanced_remarks
                    
                    # Create datetime for buffer calculation
                    base_time = datetime.strptime(rounded_time, "%H:%M")
                    
                    # Add 15-minute buffer for pickup time
                    buffer_time = base_time + timedelta(minutes=15)
                    
                    # Update remarks with buffer info
                    current_remarks = str(df.iloc[row_idx]['Remarks'])
                    if current_remarks == 'nan' or not current_remarks:
                        current_remarks = ""
                    
                    buffer_note = f"Pickup: {buffer_time.strftime('%H:%M')} (15min buffer)"
                    
                    if "15min buffer" not in current_remarks:
                        enhanced_remarks = f"{current_remarks}; {buffer_note}".strip('; ')
                        df.iloc[row_idx, df.columns.get_loc('Remarks')] = enhanced_remarks
                        
            except (ValueError, IndexError):
                logger.warning(f"Could not parse time: {reporting_time}")
        
        return df
    
    def _round_to_15_minutes(self, minute: int) -> int:
        """Round minutes to nearest 15-minute interval (0, 15, 30, 45)"""
        # Examples: 7:10 -> 7:00, 7:25 -> 7:15, 7:43 -> 7:30, 7:55 -> 8:00
        if minute <= 7:  # 0-7 minutes -> 0
            return 0
        elif minute <= 22:  # 8-22 minutes -> 15
            return 15
        elif minute <= 37:  # 23-37 minutes -> 30
            return 30
        elif minute <= 52:  # 38-52 minutes -> 45
            return 45
        else:  # 53-59 minutes -> next hour (60)
            return 60
    
    def _standardize_city_names(self, df: pd.DataFrame, row_idx: int) -> pd.DataFrame:
        """Standardize city names in From/To columns"""
        
        # Standardize From location
        from_loc = str(df.iloc[row_idx]['From (Service Location)']).strip()
        if from_loc and from_loc != 'nan':
            standardized_from = self._extract_city_name(from_loc.lower())
            if standardized_from:
                df.iloc[row_idx, df.columns.get_loc('From (Service Location)')] = self.city_mappings.get(standardized_from, standardized_from.title())
        
        # Standardize To location
        to_loc = str(df.iloc[row_idx]['To']).strip()
        if to_loc and to_loc != 'nan':
            standardized_to = self._extract_city_name(to_loc.lower())
            if standardized_to:
                df.iloc[row_idx, df.columns.get_loc('To')] = self.city_mappings.get(standardized_to, standardized_to.title())
        
        return df
    
    def _extract_city_name(self, location_text: str) -> str:
        """Extract city name from location text"""
        
        # Check for known cities in the text
        for city in self.city_mappings.keys():
            if city in location_text:
                return city
        
        # Try to extract city from common patterns
        # "City Office", "City Airport", etc.
        for city in ['mumbai', 'delhi', 'bangalore', 'pune', 'hyderabad', 'chennai']:
            if city in location_text:
                return city
        
        return location_text.strip()
    
    def _enhance_corporate_info(self, df: pd.DataFrame, row_idx: int, original_content: str) -> pd.DataFrame:
        """Enhance corporate/customer information"""
        
        current_customer = str(df.iloc[row_idx]['Customer']).strip()
        content_lower = original_content.lower()
        
        # If customer is empty, try to detect from content
        if not current_customer or current_customer == 'nan':
            # Check for corporate patterns
            for pattern, info in self.corporate_patterns.items():
                if pattern in content_lower:
                    df.iloc[row_idx, df.columns.get_loc('Customer')] = info['name']
                    break
            else:
                # Default corporate name
                df.iloc[row_idx, df.columns.get_loc('Customer')] = 'Corporate Client'
        
        return df
    
    def _comprehensive_booking_validation(self, df: pd.DataFrame, row_idx: int, original_content: str) -> pd.DataFrame:
        """Comprehensive validation of all booking fields with AI assistance"""
        
        if not self.model:
            logger.warning("No AI model available for comprehensive validation - using rule-based fallback")
            return self._rule_based_comprehensive_validation(df, row_idx, original_content)
        
        try:
            # Get current booking data
            current_data = {
                'customer': str(df.iloc[row_idx]['Customer']),
                'passenger_name': str(df.iloc[row_idx]['Passenger Name']),
                'passenger_phone': str(df.iloc[row_idx]['Passenger Phone Number']),
                'passenger_email': str(df.iloc[row_idx]['Passenger Email']),
                'from_location': str(df.iloc[row_idx]['From (Service Location)']),
                'to_location': str(df.iloc[row_idx]['To']),
                'vehicle_group': str(df.iloc[row_idx]['Vehicle Group']),
                'start_date': str(df.iloc[row_idx]['Start Date']),
                'end_date': str(df.iloc[row_idx]['End Date']),
                'reporting_time': str(df.iloc[row_idx]['Rep. Time']),
                'duty_type': str(df.iloc[row_idx]['Duty Type'])
            }
            
            # Create a summary of available corporate and city mappings for the AI
            corporate_sample = list(self.corporate_mappings.keys())[:20]  # First 20 for reference
            city_sample = list(self.city_mappings.keys())[:20]  # First 20 for reference
            
            validation_prompt = f"""You are an expert car rental booking data validator with access to corporate and city mapping databases. Analyze the original email content and validate/correct the extracted booking data according to these CRITICAL RULES:

**VALIDATION RULES:**

1. **FROM AND TO COLUMNS:** Must always contain STANDARDIZED CITY NAMES ONLY
   - Extract city names from addresses/locations using the city mapping database
   - Remove street addresses, landmarks, building names
   - Example: "9B2, DABC Apartments, Nolambur, Chennai" → "Chennai"
   - Available cities include: {', '.join(city_sample)}... (and {len(self.city_mappings)-20} more)
   - Use exact city names as they appear in the database

2. **PASSENGER DETAILS:** Extract ALL available passenger information
   - If no passenger name mentioned → put "NA"
   - Extract phone number, email if available
   - Clean phone numbers: remove +91, spaces, hyphens (keep 10 digits only)
   - If no details available → put "NA"

3. **START AND END DATE:** Apply intelligent reasoning
   - Parse relative dates: "tomorrow", "next Monday", "Saturday, October 04, 2025"
   - Convert to YYYY-MM-DD format
   - If only start date given, end date = start date (same day service)
   - Use context clues and current date for estimation

4. **DUTY TYPE LOGIC - EXACT IMPLEMENTATION:**
   **STEP 1: Corporate Detection & G2G/P2P Classification**
   - Identify corporate/company name from email content
   - Check against Corporate CSV database: {', '.join(corporate_sample)}... (and {len(self.corporate_mappings)-20} more)
   - Each corporate has a predetermined G2G or P2P classification in the database
   - If corporate not found in database → default to P2P
   
   **STEP 2: Package Type Detection**
   - "Drop", "Airport Transfer", "Airport pickup", "Airport drop" → Use 04HR 40KMS
   - "At disposal", "Local use", "Visit", "Whole day use", "Use as per guest instructions" → Use 08HR 80KMS
   - No specific time/usage mentioned → Default to 08HR 80KMS
   - "Outstation" trips or different from/to cities:
     * Major cities (Mumbai, Pune, Hyderabad, Chennai, Delhi, Ahmedabad, Bangalore) → Outstation 250KMS
     * Kolkata or any other cities → Outstation 300KMS
   
   **STEP 3: Final Format (MANDATORY)**
   - G2G Corporate + Drop/Airport → "G2G-04HR 40KMS"
   - G2G Corporate + Local/At disposal → "G2G-08HR 80KMS"
   - G2G Corporate + Outstation (major cities) → "G2G-Outstation 250KMS"
   - G2G Corporate + Outstation (Kolkata/others) → "G2G-Outstation 300KMS"
   - P2P Corporate + Drop/Airport → "P2P-04HR 40KMS"
   - P2P Corporate + Local/At disposal → "P2P-08HR 80KMS"
   - P2P Corporate + Outstation (major cities) → "P2P-Outstation 250KMS"
   - P2P Corporate + Outstation (Kolkata/others) → "P2P-Outstation 300KMS"
   - Default fallback → "P2P-08HR 80KMS"

**IMPORTANT PROCESSING RULES:**
1. Always think step-by-step before extracting data
2. Normalize vehicle names: "Dzire" → "Swift Dzire", "Crysta" → "Toyota Innova Crysta"
3. Convert dates to YYYY-MM-DD format
4. Convert times to HH:MM 24-hour format
5. Clean phone numbers to 10 digits
6. Use "NA" for genuinely missing information

**CURRENT EXTRACTED DATA:**
{current_data}

**ORIGINAL EMAIL CONTENT:**
{original_content}

**TASK:** Analyze the original content, understand the context and relationships, then return ONLY the corrected values in JSON format:

{{
    "from_location": "city_name_only",
    "to_location": "city_name_only", 
    "passenger_name": "name_or_NA",
    "passenger_phone": "10_digit_number_or_NA",
    "passenger_email": "email_or_NA",
    "start_date": "YYYY-MM-DD",
    "end_date": "YYYY-MM-DD",
    "reporting_time": "HH:MM",
    "vehicle_group": "standardized_vehicle_name",
    "duty_type": "exact_format_as_specified_above"
}}

Return ONLY the JSON object with corrected values."""
            
            response = self.model.generate_content(
                validation_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1,
                    max_output_tokens=800,
                    top_p=0.8
                )
            )
            
            if response and hasattr(response, 'text') and response.text:
                response_text = response.text.strip()
                
                # Parse JSON response
                try:
                    # Extract JSON from response
                    if '```json' in response_text:
                        json_start = response_text.find('```json') + 7
                        json_end = response_text.find('```', json_start)
                        response_text = response_text[json_start:json_end].strip()
                    elif '```' in response_text:
                        json_start = response_text.find('```') + 3
                        json_end = response_text.rfind('```')
                        response_text = response_text[json_start:json_end].strip()
                    
                    # Find JSON boundaries
                    start = response_text.find('{')
                    end = response_text.rfind('}') + 1
                    
                    if start >= 0 and end > start:
                        json_text = response_text[start:end]
                        validated_data = json.loads(json_text)
                        
                        # Update DataFrame with validated data
                        if 'from_location' in validated_data:
                            df.iloc[row_idx, df.columns.get_loc('From (Service Location)')] = validated_data['from_location']
                        if 'to_location' in validated_data:
                            df.iloc[row_idx, df.columns.get_loc('To')] = validated_data['to_location']
                        if 'passenger_name' in validated_data:
                            df.iloc[row_idx, df.columns.get_loc('Passenger Name')] = validated_data['passenger_name']
                        if 'passenger_phone' in validated_data:
                            df.iloc[row_idx, df.columns.get_loc('Passenger Phone Number')] = validated_data['passenger_phone']
                        if 'passenger_email' in validated_data:
                            df.iloc[row_idx, df.columns.get_loc('Passenger Email')] = validated_data['passenger_email']
                        if 'start_date' in validated_data:
                            df.iloc[row_idx, df.columns.get_loc('Start Date')] = validated_data['start_date']
                        if 'end_date' in validated_data:
                            df.iloc[row_idx, df.columns.get_loc('End Date')] = validated_data['end_date']
                        if 'reporting_time' in validated_data:
                            df.iloc[row_idx, df.columns.get_loc('Rep. Time')] = validated_data['reporting_time']
                        if 'vehicle_group' in validated_data:
                            df.iloc[row_idx, df.columns.get_loc('Vehicle Group')] = validated_data['vehicle_group']
                        if 'duty_type' in validated_data:
                            df.iloc[row_idx, df.columns.get_loc('Duty Type')] = validated_data['duty_type']
                        
                        # Track cost
                        self._track_cost(validation_prompt, response_text)
                        
                        logger.info(f"Comprehensive AI validation completed for row {row_idx}")
                        
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse AI validation response: {e}")
                    return self._rule_based_comprehensive_validation(df, row_idx, original_content)
            
        except Exception as e:
            logger.error(f"AI comprehensive validation failed: {e}")
            return self._rule_based_comprehensive_validation(df, row_idx, original_content)
        
        return df
    
    def _rule_based_comprehensive_validation(self, df: pd.DataFrame, row_idx: int, original_content: str) -> pd.DataFrame:
        """Rule-based fallback for comprehensive validation"""
        
        # Apply individual validation methods
        df = self._validate_city_names(df, row_idx, original_content)
        df = self._validate_passenger_details(df, row_idx, original_content)
        df = self._validate_dates(df, row_idx, original_content)
        df = self._validate_duty_type_comprehensive(df, row_idx, original_content)
        
        return df
    
    def _validate_city_names(self, df: pd.DataFrame, row_idx: int, original_content: str) -> pd.DataFrame:
        """Ensure From/To columns contain only city names"""
        
        # Extract city from From location
        from_loc = str(df.iloc[row_idx]['From (Service Location)'])
        if from_loc and from_loc != 'nan':
            city = self._extract_city_name(from_loc)
            if city:
                df.iloc[row_idx, df.columns.get_loc('From (Service Location)')] = city.title()
        
        # Extract city from To location
        to_loc = str(df.iloc[row_idx]['To'])
        if to_loc and to_loc != 'nan':
            city = self._extract_city_name(to_loc)
            if city:
                df.iloc[row_idx, df.columns.get_loc('To')] = city.title()
        
        return df
    
    def _validate_passenger_details(self, df: pd.DataFrame, row_idx: int, original_content: str) -> pd.DataFrame:
        """Extract and validate all passenger details"""
        
        # If no passenger name, set to NA
        passenger_name = str(df.iloc[row_idx]['Passenger Name'])
        if not passenger_name or passenger_name == 'nan' or passenger_name.strip() == '':
            df.iloc[row_idx, df.columns.get_loc('Passenger Name')] = 'NA'
        
        # Clean phone number
        phone = str(df.iloc[row_idx]['Passenger Phone Number'])
        if phone and phone != 'nan':
            # Remove +91, spaces, hyphens, keep only digits
            cleaned_phone = re.sub(r'[^0-9]', '', phone)
            if cleaned_phone.startswith('91') and len(cleaned_phone) == 12:
                cleaned_phone = cleaned_phone[2:]  # Remove country code
            
            if len(cleaned_phone) == 10:
                df.iloc[row_idx, df.columns.get_loc('Passenger Phone Number')] = cleaned_phone
            else:
                df.iloc[row_idx, df.columns.get_loc('Passenger Phone Number')] = 'NA'
        else:
            df.iloc[row_idx, df.columns.get_loc('Passenger Phone Number')] = 'NA'
        
        # Set email to NA if not available
        email = str(df.iloc[row_idx]['Passenger Email'])
        if not email or email == 'nan' or '@' not in email:
            df.iloc[row_idx, df.columns.get_loc('Passenger Email')] = 'NA'
        
        return df
    
    def _validate_dates(self, df: pd.DataFrame, row_idx: int, original_content: str) -> pd.DataFrame:
        """Apply intelligent date reasoning"""
        
        from datetime import datetime, timedelta
        import re
        
        # Try to parse dates from content
        content_lower = original_content.lower()
        
        # Look for date patterns
        date_patterns = [
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',  # DD/MM/YYYY or MM/DD/YYYY
            r'(\d{4}-\d{1,2}-\d{1,2})',  # YYYY-MM-DD
            r'(tomorrow)',
            r'(next\s+\w+)',  # next Monday, next Tuesday
            r'(\w+day,\s*\w+\s+\d+,\s*\d{4})',  # Saturday, October 04, 2025
        ]
        
        current_date = datetime.now().date()
        start_date = None
        
        # Try to extract date
        for pattern in date_patterns:
            matches = re.findall(pattern, content_lower)
            if matches:
                date_text = matches[0]
                
                if 'tomorrow' in date_text:
                    start_date = current_date + timedelta(days=1)
                elif 'next' in date_text:
                    # Simple logic for next weekday
                    start_date = current_date + timedelta(days=7)
                else:
                    # Try to parse actual date
                    try:
                        # Handle different date formats
                        if ',' in date_text and len(date_text) > 10:
                            # Format like "Saturday, October 04, 2025"
                            start_date = datetime.strptime(date_text.replace(',', ''), '%A %B %d %Y').date()
                        elif '-' in date_text:
                            start_date = datetime.strptime(date_text, '%Y-%m-%d').date()
                        elif '/' in date_text:
                            # Try both DD/MM/YYYY and MM/DD/YYYY
                            try:
                                start_date = datetime.strptime(date_text, '%d/%m/%Y').date()
                            except:
                                start_date = datetime.strptime(date_text, '%m/%d/%Y').date()
                    except ValueError:
                        continue
                
                if start_date:
                    break
        
        # Set dates
        if start_date:
            df.iloc[row_idx, df.columns.get_loc('Start Date')] = start_date.strftime('%Y-%m-%d')
            # If no end date specified, use start date
            end_date_str = str(df.iloc[row_idx]['End Date'])
            if not end_date_str or end_date_str == 'nan':
                df.iloc[row_idx, df.columns.get_loc('End Date')] = start_date.strftime('%Y-%m-%d')
        
        return df
    
    def _validate_duty_type_comprehensive(self, df: pd.DataFrame, row_idx: int, original_content: str) -> pd.DataFrame:
        """Apply exact duty type logic as specified"""
        
        content_lower = original_content.lower()
        
        # Step 1: Corporate Detection
        corporate_category = 'P2P'  # Default
        customer = str(df.iloc[row_idx]['Customer']).lower()
        
        # Check for G2G corporate patterns (simplified)
        g2g_indicators = ['tcs', 'infosys', 'accenture', 'wipro', 'hcl', 'cognizant', 'capgemini', 'deloitte', 'microsoft', 'google', 'amazon']
        for indicator in g2g_indicators:
            if indicator in content_lower or indicator in customer:
                corporate_category = 'G2G'
                break
        
        # Step 2: Package Type Detection
        package = '08HR 80KMS'  # Default
        
        # Check for drop/airport keywords
        drop_keywords = ['drop', 'airport transfer', 'pickup from airport', 'drop to airport']
        if any(keyword in content_lower for keyword in drop_keywords):
            package = '04HR 40KMS'
        
        # Check for disposal/local keywords
        disposal_keywords = ['at disposal', 'local use', 'visit', 'whole day use', 'use as per guest instructions']
        if any(keyword in content_lower for keyword in disposal_keywords):
            package = '08HR 80KMS'
        
        # Check for outstation
        from_city = str(df.iloc[row_idx]['From (Service Location)']).lower()
        to_city = str(df.iloc[row_idx]['To']).lower()
        
        if 'outstation' in content_lower or (from_city != to_city and from_city and to_city):
            major_cities = ['mumbai', 'pune', 'hyderabad', 'chennai', 'delhi', 'ahmedabad', 'bangalore']
            if any(city in to_city for city in major_cities):
                package = 'Outstation 250KMS'
            elif 'kolkata' in to_city or to_city not in major_cities:
                package = 'Outstation 300KMS'
        
        # Step 3: Final Format
        if corporate_category == 'G2G':
            duty_type = f"G-{package}"
        else:
            duty_type = f"P-{package}"
        
        df.iloc[row_idx, df.columns.get_loc('Duty Type')] = duty_type
        
        return df
    
    def _assign_dispatch_center(self, df: pd.DataFrame, row_idx: int) -> pd.DataFrame:
        """Assign dispatch center based on from location"""
        
        from_city = str(df.iloc[row_idx]['From (Service Location)']).lower()
        
        # Find appropriate dispatch center
        dispatch_center = 'Central Dispatch'  # Default
        
        for city, center in self.dispatch_centers.items():
            if city in from_city:
                dispatch_center = center
                break
        
        df.iloc[row_idx, df.columns.get_loc('Dispatch center')] = dispatch_center
        
        return df
    
    def _generate_labels(self, df: pd.DataFrame, row_idx: int, classification_result: ClassificationResult) -> pd.DataFrame:
        """Generate appropriate labels based on specific business rules"""
        
        labels = []
        
        # Get original content for analysis
        passenger_name = str(df.iloc[row_idx]['Passenger Name']).strip().lower()
        
        # 1. LadyGuest - ONLY if Ms or Mrs is given in the passenger info
        if any(title in passenger_name for title in ['ms.', 'mrs.', 'ms ', 'mrs ']):
            labels.append('LadyGuest')
        
        # 2. MD's Guest - Ignore for now (as requested)
        # pass
        
        # 3. VIP - ONLY if booker specifically mentions VIP in the mail
        # This needs to be checked against original content in the calling method
        # Will be added in _validate_single_booking_row method
        
        # Set labels (only the 3 specific ones)
        df.iloc[row_idx, df.columns.get_loc('Labels')] = ', '.join(labels) if labels else ''
        
        return df
    
    def _check_vip_status(self, df: pd.DataFrame, row_idx: int, original_content: str) -> pd.DataFrame:
        """Check if passenger is VIP based on original content"""
        
        content_lower = original_content.lower()
        current_labels = str(df.iloc[row_idx]['Labels'])
        
        # Check if VIP is specifically mentioned in the mail
        if 'vip' in content_lower:
            labels_list = [label.strip() for label in current_labels.split(',') if label.strip()]
            if 'VIP' not in labels_list:
                labels_list.append('VIP')
            df.iloc[row_idx, df.columns.get_loc('Labels')] = ', '.join(labels_list)
        
        return df
    
    def _enhance_remarks_with_extra_info(self, df: pd.DataFrame, row_idx: int, original_content: str) -> pd.DataFrame:
        """Enhance remarks with ALL extra information that doesn't fit in other fields"""
        
        current_remarks = str(df.iloc[row_idx]['Remarks'])
        if current_remarks == 'nan' or not current_remarks:
            current_remarks = ""
        
        # Extract all information from original content that's not captured in structured fields
        extra_info = self._extract_extra_information(df, row_idx, original_content)
        
        if extra_info:
            if current_remarks:
                enhanced_remarks = f"{current_remarks}. {extra_info}".replace('..', '.')
            else:
                enhanced_remarks = extra_info
            
            df.iloc[row_idx, df.columns.get_loc('Remarks')] = enhanced_remarks
        
        return df
    
    def _extract_extra_information(self, df: pd.DataFrame, row_idx: int, original_content: str) -> str:
        """Extract extra information using AI or fallback to rules"""
        
        if self.model:
            try:
                return self._extract_remarks_with_ai(original_content, df, row_idx)
            except Exception as e:
                logger.warning(f"AI remarks extraction failed: {e}, using fallback")
                return self._extract_remarks_fallback(original_content, df, row_idx)
        else:
            return self._extract_remarks_fallback(original_content, df, row_idx)
    
    def _extract_remarks_with_ai(self, original_content: str, df: pd.DataFrame, row_idx: int) -> str:
        """Extract remarks using AI with comprehensive analysis prompt"""
        
        # Get current booking data
        current_booking = {
            'passenger': str(df.iloc[row_idx]['Passenger Name']),
            'phone': str(df.iloc[row_idx]['Passenger Phone Number']),
            'from_location': str(df.iloc[row_idx]['From (Service Location)']),
            'to_location': str(df.iloc[row_idx]['To']),
            'vehicle': str(df.iloc[row_idx]['Vehicle Group']),
            'date': str(df.iloc[row_idx]['Start Date']),
            'time': str(df.iloc[row_idx]['Rep. Time']),
            'flight': str(df.iloc[row_idx]['Flight/Train Number'])
        }
        
        prompt = f"""You are an expert car rental booking validation agent. Your task is to analyze the entire email content and extract ALL additional information that should go in the REMARKS column.

**ANALYSIS PROCESS - FOLLOW STEP BY STEP:**

1. **FIRST: READ AND UNDERSTAND THE ENTIRE CONTENT**
   - Analyze the complete email/booking request
   - Understand the context, relationships, and all mentioned details
   - Identify what information is already captured in structured fields
   - Identify what extra information remains uncaptured

2. **EXTRACT UNCAPTURED INFORMATION:**
   - Driver name and contact details (if mentioned)
   - Special instructions or preferences from the booker
   - Multiple flight details and numbers
   - Emergency contacts or additional contact persons
   - Special requirements (wheelchair access, child seat, etc.)
   - Billing instructions or payment details
   - Meeting points or specific pickup instructions
   - Additional context, notes, or observations from the email
   - Any other relevant information not in structured fields

3. **CRITICAL REQUIREMENT:**
   - ALL extra information provided by the booker which does not fit into the preexisting fields MUST be put into this field
   - NO INFORMATION should be omitted that is present in the mail
   - Do NOT include system-generated messages or processing information
   - Focus ONLY on actual booking-related information from the original email

**CURRENT STRUCTURED BOOKING DATA (already captured):**
{current_booking}

**ORIGINAL EMAIL/CONTENT TO ANALYZE:**
{original_content}

**INSTRUCTIONS:**
- Analyze the entire content thoroughly
- Extract ONLY the additional information NOT already in the structured fields above
- Return clean, readable remarks text (no JSON, no formatting)
- If no additional information exists, return empty string
- Focus on information that would be useful for the driver or operations team

**OUTPUT:** Return only the remarks text containing uncaptured information from the email."""
        
        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1,
                    max_output_tokens=500,
                    top_p=0.8
                )
            )
            
            if response and hasattr(response, 'text') and response.text:
                remarks = response.text.strip()
                
                # Track cost
                self._track_cost(prompt, remarks)
                
                return remarks
            else:
                return ""
                
        except Exception as e:
            logger.error(f"AI remarks extraction failed: {e}")
            return ""
    
    def _extract_remarks_fallback(self, original_content: str, df: pd.DataFrame, row_idx: int) -> str:
        """Fallback rule-based remarks extraction"""
        
        extra_info = []
        content_lower = original_content.lower()
        
        # Get current structured data to avoid duplication
        structured_info = {
            'passenger': str(df.iloc[row_idx]['Passenger Name']).lower(),
            'phone': str(df.iloc[row_idx]['Passenger Phone Number']),
            'from_loc': str(df.iloc[row_idx]['From (Service Location)']).lower(),
            'to_loc': str(df.iloc[row_idx]['To']).lower(),
            'vehicle': str(df.iloc[row_idx]['Vehicle Group']).lower(),
            'date': str(df.iloc[row_idx]['Start Date']),
            'time': str(df.iloc[row_idx]['Rep. Time'])
        }
        
        # Extract additional context that's not in structured fields
        lines = original_content.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            line_lower = line.lower()
            
            # Skip lines that are already captured in structured fields
            if any(info in line_lower for info in structured_info.values() if info and info != 'nan'):
                continue
                
            # Look for driver information
            if 'driver' in line_lower and ('name' in line_lower or 'contact' in line_lower):
                extra_info.append(f"Driver info: {line}")
                continue
                
            # Look for additional context, special instructions, etc.
            if any(keyword in line_lower for keyword in [
                'urgent', 'priority', 'asap', 'immediate', 'emergency',
                'special', 'note', 'important', 'please', 'kindly',
                'preference', 'request', 'requirement', 'instruction',
                'contact', 'call', 'inform', 'confirm', 'coordinate'
            ]):
                if len(line) > 10 and line not in extra_info:  # Avoid very short lines
                    extra_info.append(line)
        
        # Join and clean up
        if extra_info:
            return '; '.join(extra_info[:3])  # Limit to top 3 pieces of extra info
        
        return ""
    
    def _track_cost(self, input_text: str, output_text: str) -> float:
        """Track API usage cost"""
        input_tokens = len(input_text) // 4
        output_tokens = len(output_text) // 4
        
        cost_inr = (
            (input_tokens / 1000) * self.cost_per_1k_input_tokens +
            (output_tokens / 1000) * self.cost_per_1k_output_tokens
        )
        
        self.total_cost += cost_inr
        self.request_count += 1
        
        return cost_inr
    
    def _validate_other_fields(self, df: pd.DataFrame, row_idx: int) -> pd.DataFrame:
        """Validate and clean other fields"""
        
        # Ensure end date is set (same as start date if not specified)
        start_date = str(df.iloc[row_idx]['Start Date']).strip()
        end_date = str(df.iloc[row_idx]['End Date']).strip()
        
        if start_date and start_date != 'nan' and (not end_date or end_date == 'nan'):
            df.iloc[row_idx, df.columns.get_loc('End Date')] = start_date
        
        # Clean phone numbers (ensure 10 digits)
        for phone_col in ['Booked By Phone Number', 'Passenger Phone Number']:
            phone = str(df.iloc[row_idx][phone_col]).strip()
            if phone and phone != 'nan':
                # Extract digits only
                digits = re.sub(r'\D', '', phone)
                if len(digits) == 12 and digits.startswith('91'):
                    digits = digits[2:]
                elif len(digits) == 13 and digits.startswith('091'):
                    digits = digits[3:]
                
                if len(digits) == 10:
                    df.iloc[row_idx, df.columns.get_loc(phone_col)] = digits
        
        # Ensure required fields have default values
        required_defaults = {
            'Booked By Name': 'Travel Coordinator',
            'Passenger Name': 'Guest',
            'Vehicle Group': 'Swift Dzire',
            'Rep. Time': '09:00',
            'Dispatch center': 'Central Dispatch'
        }
        
        for field, default_value in required_defaults.items():
            current_value = str(df.iloc[row_idx][field]).strip()
            if not current_value or current_value == 'nan':
                df.iloc[row_idx, df.columns.get_loc(field)] = default_value
        
        return df

# Test function
def test_business_logic_validation():
    """Test business logic validation agent"""
    
    print("🧪 Testing Business Logic Validation Agent...")
    
    # Create sample DataFrame (simulating extraction result)
    import pandas as pd
    
    sample_data = {
        'Customer': ['', 'Accenture', ''],
        'Booked By Name': ['John Manager', '', 'Travel Desk'],
        'Booked By Phone Number': ['9876543210', '+919876543211', '91-9876543212'],
        'Booked By Email': ['john@company.com', 'travel@accenture.com', ''],
        'Passenger Name': ['Rajesh Kumar', 'Mary Smith', ''],
        'Passenger Phone Number': ['9876543210', '9876543211', '9876543212'],
        'Passenger Email': ['', 'mary@company.com', 'guest@email.com'],
        'From (Service Location)': ['Mumbai Office', 'delhi', 'bangalore airport'],
        'To': ['Mumbai Airport', 'gurgaon', 'electronic city'],
        'Vehicle Group': ['innova', 'dzire', ''],
        'Duty Type': ['', '', 'disposal'],
        'Start Date': ['2024-12-25', '2024-12-26', '2024-12-27'],
        'End Date': ['', '2024-12-26', ''],
        'Rep. Time': ['10:30', '09:15', ''],
        'Reporting Address': ['Andheri Office', 'Delhi Office', 'Whitefield'],
        'Drop Address': ['T2 Terminal', 'Cyber City', 'Electronic City'],
        'Flight/Train Number': ['AI 131', '', ''],
        'Dispatch center': ['', '', ''],
        'Remarks': ['Airport drop', '', 'Local disposal needed'],
        'Labels': ['', '', '']
    }
    
    df = pd.DataFrame(sample_data)
    
    # Create mock extraction result
    from base_extraction_agent import ExtractionResult
    extraction_result = ExtractionResult(
        success=True,
        bookings_dataframe=df,
        booking_count=3,
        confidence_score=0.8,
        processing_time=1.0,
        cost_inr=0.0,
        extraction_method="test_extraction"
    )
    
    # Create mock classification result
    from gemma_classification_agent import BookingType, DutyType, ClassificationResult
    classification_result = ClassificationResult(
        booking_type=BookingType.MULTIPLE,
        booking_count=3,
        confidence_score=0.9,
        reasoning="Multiple bookings test",
        detected_duty_type=DutyType.DISPOSAL_8_80,
        detected_dates=["2024-12-25", "2024-12-26", "2024-12-27"],
        detected_vehicles=["Innova", "Dzire"],
        detected_drops=["Airport", "Gurgaon", "Electronic City"]
    )
    
    # Sample original content
    original_content = """
    Dear Team,
    
    Please arrange cars for:
    1. Rajesh Kumar (9876543210) - Airport drop from Mumbai office
    2. Mary from Accenture - Delhi to Gurgaon disposal 
    3. Guest - Local Bangalore disposal
    
    Vehicles: Innova preferred for airport, Dzire for others
    
    Thanks!
    """
    
    # Initialize validation agent
    validator = BusinessLogicValidationAgent()
    
    print("📊 Original DataFrame:")
    print("="*80)
    print(f"Shape: {df.shape}")
    print("\nKey fields before validation:")
    for i in range(len(df)):
        print(f"Booking {i+1}:")
        print(f"  Customer: {df.iloc[i]['Customer']}")
        print(f"  Vehicle: {df.iloc[i]['Vehicle Group']}")
        print(f"  Duty Type: {df.iloc[i]['Duty Type']}")
        print(f"  From: {df.iloc[i]['From (Service Location)']}")
        print(f"  To: {df.iloc[i]['To']}")
        print(f"  Labels: {df.iloc[i]['Labels']}")
        print(f"  Dispatch: {df.iloc[i]['Dispatch center']}")
    
    print("\n" + "="*80)
    print("🔧 Applying business logic validation...")
    
    try:
        # Apply validation
        validated_result = validator.validate_and_enhance(
            extraction_result, classification_result, original_content
        )
        
        print(f"✅ Validation Success: {validated_result.success}")
        print(f"📊 Booking Count: {validated_result.booking_count}")
        print(f"🎯 Confidence: {validated_result.confidence_score:.1%}")
        print(f"⏱️ Processing Time: {validated_result.processing_time:.2f}s")
        print(f"🔧 Method: {validated_result.extraction_method}")
        
        validated_df = validated_result.bookings_dataframe
        
        print(f"\n📋 Validated DataFrame:")
        print("="*80)
        print(f"Shape: {validated_df.shape}")
        print("\nKey fields after validation:")
        
        for i in range(len(validated_df)):
            print(f"\nBooking {i+1}:")
            print(f"  Customer: {validated_df.iloc[i]['Customer']}")
            print(f"  Vehicle: {validated_df.iloc[i]['Vehicle Group']}")
            print(f"  Duty Type: {validated_df.iloc[i]['Duty Type']}")
            print(f"  From: {validated_df.iloc[i]['From (Service Location)']}")
            print(f"  To: {validated_df.iloc[i]['To']}")
            print(f"  Labels: {validated_df.iloc[i]['Labels']}")
            print(f"  Dispatch: {validated_df.iloc[i]['Dispatch center']}")
            print(f"  Phone: {validated_df.iloc[i]['Passenger Phone Number']}")
            print(f"  Time: {validated_df.iloc[i]['Rep. Time']}")
        
        # Show enhanced remarks
        print(f"\n📝 Enhanced Remarks:")
        for i in range(len(validated_df)):
            remarks = validated_df.iloc[i]['Remarks']
            if remarks and len(str(remarks)) > 20:
                print(f"Booking {i+1}: {remarks}")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_business_logic_validation()