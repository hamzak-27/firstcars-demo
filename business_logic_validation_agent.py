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
    GEMMA_AVAILABLE = True
except ImportError:
    GEMMA_AVAILABLE = False
    logger.warning("Google Generative AI not available. Install with: pip install google-generativeai")

class BusinessLogicValidationAgent:
    """
    Final validation agent that applies business rules and enhances DataFrame
    
    Validates and enhances:
    - Duty Type (with existing logic)
    - Vehicle Group standardization
    - Time calculations (15-minute buffers)
    - Dispatch Center assignment
    - Corporate/Customer field completion
    - City name validation for From/To
    - Labels assignment
    - All other DataFrame fields
    """
    
    def __init__(self, api_key: str = None, model_name: str = "models/gemini-2.5-flash"):
        """Initialize business logic validation agent"""
        
        self.api_key = api_key or os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_AI_API_KEY')
        self.model_name = model_name
        
        # Configure Gemini if available
        if GEMMA_AVAILABLE and self.api_key and self.api_key != "test-key":
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(model_name)
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
        """Initialize all business rule mappings"""
        
        # Vehicle standardization mappings
        self.vehicle_mappings = {
            'dzire': 'Swift Dzire',
            'swift dzire': 'Swift Dzire',
            'maruti dzire': 'Swift Dzire',
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
        
        # City standardization mappings
        self.city_mappings = {
            'mumbai': 'Mumbai',
            'bombay': 'Mumbai',
            'delhi': 'Delhi',
            'new delhi': 'Delhi',
            'ncr': 'Delhi',
            'bangalore': 'Bangalore',
            'bengaluru': 'Bangalore',
            'pune': 'Pune',
            'hyderabad': 'Hyderabad',
            'chennai': 'Chennai',
            'madras': 'Chennai',
            'kolkata': 'Kolkata',
            'calcutta': 'Kolkata',
            'gurgaon': 'Gurgaon',
            'gurugram': 'Gurgaon',
            'noida': 'Noida',
            'faridabad': 'Faridabad',
            'ghaziabad': 'Ghaziabad'
        }
        
        # Corporate detection patterns
        self.corporate_patterns = {
            'accenture': {'name': 'Accenture India Ltd', 'category': 'G2G'},
            'tcs': {'name': 'Tata Consultancy Services', 'category': 'G2G'},
            'infosys': {'name': 'Infosys Limited', 'category': 'G2G'},
            'wipro': {'name': 'Wipro Limited', 'category': 'G2G'},
            'hcl': {'name': 'HCL Technologies', 'category': 'G2G'},
            'cognizant': {'name': 'Cognizant Technology Solutions', 'category': 'G2G'},
            'tech mahindra': {'name': 'Tech Mahindra', 'category': 'G2G'},
            'capgemini': {'name': 'Capgemini India', 'category': 'G2G'},
            'deloitte': {'name': 'Deloitte India', 'category': 'G2G'},
            'pwc': {'name': 'PwC India', 'category': 'G2G'},
            'microsoft': {'name': 'Microsoft India', 'category': 'G2G'},
            'google': {'name': 'Google India', 'category': 'G2G'},
            'amazon': {'name': 'Amazon India', 'category': 'G2G'}
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
        
        # Duty type detection patterns (from existing logic)
        self.duty_type_patterns = {
            'disposal': ['disposal', 'at disposal', 'local use', 'city use', 'whole day', 'full day', '8 hour', '8hr', '80km'],
            'drop': ['drop', 'airport transfer', 'pickup', 'one way', 'transfer', '4 hour', '4hr', '40km'],
            'outstation': ['outstation', 'out station', 'intercity', 'travel', 'round trip', '250km']
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
        
        # 7. Generate appropriate labels
        df = self._generate_labels(df, row_idx, classification_result)
        
        # 8. Validate and clean other fields
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
        """Standardize vehicle group names"""
        
        current_vehicle = str(df.iloc[row_idx]['Vehicle Group']).strip().lower()
        
        if not current_vehicle or current_vehicle == 'nan':
            # Default vehicle
            df.iloc[row_idx, df.columns.get_loc('Vehicle Group')] = 'Swift Dzire'
        else:
            # Map to standardized name
            standardized = self.vehicle_mappings.get(current_vehicle, current_vehicle.title())
            df.iloc[row_idx, df.columns.get_loc('Vehicle Group')] = standardized
        
        return df
    
    def _enhance_time_fields(self, df: pd.DataFrame, row_idx: int) -> pd.DataFrame:
        """Enhance time fields with 15-minute buffer calculations"""
        
        reporting_time = str(df.iloc[row_idx]['Rep. Time']).strip()
        
        if reporting_time and reporting_time != 'nan':
            # Parse time and add 15-minute buffer for actual pickup
            try:
                # Parse current time format (HH:MM)
                if re.match(r'\d{1,2}:\d{2}', reporting_time):
                    time_parts = reporting_time.split(':')
                    hour = int(time_parts[0])
                    minute = int(time_parts[1])
                    
                    # Create datetime for calculation
                    base_time = datetime.strptime(f"{hour:02d}:{minute:02d}", "%H:%M")
                    
                    # Add 15-minute buffer for pickup time
                    buffer_time = base_time + timedelta(minutes=15)
                    
                    # Update reporting time with buffer note in remarks
                    current_remarks = str(df.iloc[row_idx]['Remarks'])
                    if current_remarks == 'nan' or not current_remarks:
                        current_remarks = ""
                    
                    buffer_note = f"Reporting: {reporting_time}, Pickup: {buffer_time.strftime('%H:%M')} (15min buffer)"
                    
                    if "15min buffer" not in current_remarks:
                        enhanced_remarks = f"{current_remarks}; {buffer_note}".strip('; ')
                        df.iloc[row_idx, df.columns.get_loc('Remarks')] = enhanced_remarks
                        
            except (ValueError, IndexError):
                logger.warning(f"Could not parse time: {reporting_time}")
        
        return df
    
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
        """Generate appropriate labels for the booking"""
        
        labels = []
        
        # Add classification-based labels
        if classification_result.booking_type.value == 'multiple':
            labels.append('MULTI-BOOKING')
        
        # Add duty type labels
        duty_type = str(df.iloc[row_idx]['Duty Type'])
        if '04HR 40KMS' in duty_type:
            labels.append('DROP-SERVICE')
        elif '08HR 80KMS' in duty_type:
            labels.append('DISPOSAL-SERVICE')
        elif 'Outstation' in duty_type:
            labels.append('OUTSTATION-SERVICE')
        
        # Add vehicle type labels
        vehicle = str(df.iloc[row_idx]['Vehicle Group'])
        if 'Innova' in vehicle:
            labels.append('SUV')
        elif 'Dzire' in vehicle:
            labels.append('SEDAN')
        
        # Add corporate labels
        if 'G2G' in duty_type:
            labels.append('CORPORATE')
        else:
            labels.append('INDIVIDUAL')
        
        # Join labels
        df.iloc[row_idx, df.columns.get_loc('Labels')] = ', '.join(labels)
        
        return df
    
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