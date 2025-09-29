#!/usr/bin/env python3
"""
Single Booking Extraction Agent
Specialized agent for extracting single booking data using Gemma API
"""

import logging
import time
from typing import Dict, List, Optional, Any

from base_extraction_agent import BaseExtractionAgent, BookingData, ExtractionResult
from gemma_classification_agent import ClassificationResult

logger = logging.getLogger(__name__)

class SingleBookingExtractionAgent(BaseExtractionAgent):
    """
    Specialized extraction agent for single bookings
    
    Optimized for:
    - Single booking scenarios
    - Simple text processing
    - Clean field extraction
    - Fast processing
    """
    
    def __init__(self, api_key: str = None, model_name: str = "models/gemini-2.5-flash"):
        """Initialize single booking extraction agent"""
        super().__init__(api_key, model_name)
        logger.info("SingleBookingExtractionAgent initialized")
    
    def extract(self, content: str, classification_result: ClassificationResult) -> ExtractionResult:
        """
        Extract single booking data from content
        
        Args:
            content: Email content or OCR extracted text
            classification_result: Result from classification agent
            
        Returns:
            ExtractionResult with single booking DataFrame
        """
        start_time = time.time()
        logger.info(f"Starting single booking extraction ({len(content)} chars)")
        
        try:
            # Use Gemma API if available, otherwise fallback
            if self.model:
                return self._extract_with_gemma(content, classification_result, start_time)
            else:
                return self._extract_with_fallback(content, classification_result, start_time)
                
        except Exception as e:
            logger.error(f"Single booking extraction failed: {str(e)}")
            processing_time = time.time() - start_time
            
            return ExtractionResult(
                success=False,
                bookings_dataframe=self._create_dataframe_from_bookings([]),
                booking_count=0,
                confidence_score=0.0,
                processing_time=processing_time,
                cost_inr=0.0,
                extraction_method="single_booking_extraction_failed",
                error_message=str(e)
            )
    
    def _extract_with_gemma(self, content: str, classification_result: ClassificationResult, start_time: float) -> ExtractionResult:
        """Extract using Gemma API"""
        
        try:
            # Build extraction prompt
            prompt = self._build_extraction_prompt(content, classification_result)
            
            # Generate response
            response_text, cost = self._generate_gemma_response(prompt)
            
            # Parse response
            parsed_data = self._parse_json_response(response_text)
            
            # Create booking data
            booking_dict = parsed_data.get('booking', {})
            booking = self._create_booking_from_dict(booking_dict)
            booking.extraction_method = "single_booking_gemma"
            
            # Create DataFrame
            df = self._create_dataframe_from_bookings([booking])
            
            processing_time = time.time() - start_time
            
            logger.info(f"Single booking extracted successfully (cost: ₹{cost:.4f}, time: {processing_time:.2f}s)")
            
            return ExtractionResult(
                success=True,
                bookings_dataframe=df,
                booking_count=1,
                confidence_score=parsed_data.get('confidence_score', 0.8),
                processing_time=processing_time,
                cost_inr=cost,
                extraction_method="single_booking_gemma",
                metadata={
                    'classification_confidence': classification_result.confidence_score,
                    'detected_duty_type': classification_result.detected_duty_type.value,
                    'gemma_response_length': len(response_text)
                }
            )
            
        except Exception as e:
            logger.error(f"Gemma extraction failed: {str(e)}")
            # Fallback to rule-based extraction
            return self._extract_with_fallback(content, classification_result, start_time, error=str(e))
    
    def _extract_with_fallback(self, content: str, classification_result: ClassificationResult, 
                             start_time: float, error: str = None) -> ExtractionResult:
        """Fallback rule-based extraction"""
        
        logger.warning("Using rule-based fallback extraction for single booking")
        
        # Simple rule-based extraction
        booking_dict = self._rule_based_extraction(content, classification_result)
        booking = self._create_booking_from_dict(booking_dict)
        booking.extraction_method = "single_booking_fallback"
        
        if error:
            booking.remarks = f"{booking.remarks} (Fallback used due to: {error})" if booking.remarks else f"Fallback used due to: {error}"
        
        # Create DataFrame
        df = self._create_dataframe_from_bookings([booking])
        
        processing_time = time.time() - start_time
        
        return ExtractionResult(
            success=True,
            bookings_dataframe=df,
            booking_count=1,
            confidence_score=0.6,  # Lower confidence for fallback
            processing_time=processing_time,
            cost_inr=0.0,  # No cost for fallback
            extraction_method="single_booking_fallback",
            error_message=error or "",
            metadata={
                'fallback_used': True,
                'classification_confidence': classification_result.confidence_score
            }
        )
    
    def _build_extraction_prompt(self, content: str, classification_result: ClassificationResult) -> str:
        """Build extraction prompt for single booking"""
        
        return f"""You are an expert car rental booking data extraction agent. Extract booking information for a SINGLE booking from the content.

CLASSIFICATION CONTEXT:
- Booking Type: {classification_result.booking_type.value} 
- Detected Duty Type: {classification_result.detected_duty_type.value}
- Confidence: {classification_result.confidence_score:.1%}

CONTENT TO EXTRACT FROM:
{content}

EXTRACTION RULES:
1. Extract ALL available information for the 19 standardized fields
2. Normalize phone numbers to 10 digits
3. Format dates as YYYY-MM-DD
4. Format times as HH:MM  
5. Clean and standardize all fields
6. Leave duty_type field empty (will be filled by validation agent)
7. If information is missing, leave field empty (don't guess)

FIELD MAPPING GUIDELINES:
- customer: Company/corporate name
- booked_by_name: Person who made the booking
- passenger_name: Actual traveler name
- from_location: Source city/location (city name only)
- to_location: Destination city/location (city name only)
- reporting_address: Full pickup address
- drop_address: Full drop address
- vehicle_group: Car type (Dzire, Innova, etc.)
- duty_type: Leave empty for now
- flight_train_number: Flight/train details if mentioned

Return ONLY this JSON format:

{{
    "analysis": "Step-by-step extraction process",
    "booking": {{
        "customer": "string",
        "booked_by_name": "string",
        "booked_by_phone": "string", 
        "booked_by_email": "string",
        "passenger_name": "string",
        "passenger_phone": "string",
        "passenger_email": "string",
        "from_location": "string",
        "to_location": "string", 
        "vehicle_group": "string",
        "duty_type": "",
        "start_date": "YYYY-MM-DD",
        "end_date": "YYYY-MM-DD",
        "reporting_time": "HH:MM",
        "reporting_address": "string",
        "drop_address": "string",
        "flight_train_number": "string",
        "dispatch_center": "string",
        "remarks": "string",
        "labels": "string"
    }},
    "confidence_score": 0.0-1.0,
    "extraction_notes": "Any notes about extraction quality or missing information"
}}

EXTRACT NOW:"""
    
    def _rule_based_extraction(self, content: str, classification_result: ClassificationResult) -> Dict[str, Any]:
        """Enhanced rule-based extraction with table detection for fallback"""
        
        import re
        
        content_lower = content.lower()
        
        # First try table detection
        if self._is_table_format(content):
            booking_data = self._extract_from_table_format(content)
            if booking_data:
                booking_data['confidence_score'] = 0.7  # Higher confidence for table extraction
                return booking_data
        
        # Fall back to regex extraction
        booking_data = {
            'customer': '',
            'passenger_name': '',
            'passenger_phone': '',
            'start_date': '',
            'reporting_time': '',
            'from_location': '',
            'to_location': '',
            'vehicle_group': '',
            'reporting_address': '',
            'remarks': '',
            'confidence_score': 0.6
        }
        
        # Extract phone numbers (Indian format)
        phone_pattern = r'(\d{10}|\+91\d{10}|91\d{10})'
        phones = re.findall(phone_pattern, content)
        if phones:
            booking_data['passenger_phone'] = self._normalize_phone_number(phones[0])
        
        # Extract names (simple patterns)
        name_patterns = [
            r'passenger[:\s]+([A-Za-z\s]+)',
            r'name[:\s]+([A-Za-z\s]+)',
            r'mr\.?\s+([A-Za-z\s]+)',
            r'ms\.?\s+([A-Za-z\s]+)'
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, content_lower)
            if match:
                booking_data['passenger_name'] = match.group(1).strip().title()
                break
        
        # Extract vehicle types
        vehicles = ['dzire', 'innova', 'crysta', 'ertiga', 'swift']
        for vehicle in vehicles:
            if vehicle in content_lower:
                booking_data['vehicle_group'] = vehicle.title()
                break
        
        # Extract cities (common Indian cities)
        cities = ['mumbai', 'delhi', 'bangalore', 'pune', 'hyderabad', 'chennai', 'gurgaon', 'noida']
        found_cities = [city for city in cities if city in content_lower]
        if len(found_cities) >= 2:
            booking_data['from_location'] = found_cities[0].title()
            booking_data['to_location'] = found_cities[1].title()
        elif len(found_cities) == 1:
            booking_data['from_location'] = found_cities[0].title()
        
        # Extract dates (simple patterns)
        date_patterns = [
            r'(\d{1,2}[-/]\d{1,2}[-/]\d{4})',
            r'(\d{4}[-/]\d{1,2}[-/]\d{1,2})'
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, content)
            if match:
                booking_data['start_date'] = self._normalize_date(match.group(1))
                break
        
        # Extract time
        time_pattern = r'(\d{1,2}:\d{2}\s*(?:AM|PM|am|pm)?)'
        time_match = re.search(time_pattern, content)
        if time_match:
            booking_data['reporting_time'] = self._normalize_time(time_match.group(1))
        
        # Use classification hints
        if hasattr(classification_result, 'detected_dates') and classification_result.detected_dates:
            booking_data['start_date'] = classification_result.detected_dates[0]
        
        if hasattr(classification_result, 'detected_vehicles') and classification_result.detected_vehicles:
            booking_data['vehicle_group'] = classification_result.detected_vehicles[0]
        
        # Set basic remarks
        booking_data['remarks'] = f"Rule-based extraction (Classification: {classification_result.booking_type.value})"
        
        return booking_data
    
    def _is_table_format(self, content: str) -> bool:
        """Detect if content has table format"""
        # Look for table indicators
        table_indicators = [
            'name:', 'passenger:', 'customer:', 'phone:', 'mobile:', 
            'date:', 'time:', 'pickup:', 'drop:', 'vehicle:', 'car:',
            '|', '\t', ':', 'from:', 'to:', 'address:', 'flight:',
            'employee name', 'contact number', 'travel date',
            'pick-up time', 'cab type', 'drop at', 'company name'
        ]
        
        content_lower = content.lower()
        
        # Count how many table indicators we find
        indicator_count = sum(1 for indicator in table_indicators if indicator in content_lower)
        
        # If we find multiple indicators, it's likely tabular data
        return indicator_count >= 3
    
    def _extract_from_table_format(self, content: str) -> Dict[str, Any]:
        """Extract booking from table/structured format"""
        
        booking_data = {
            'customer': '',
            'booked_by_name': '',
            'booked_by_phone': '',
            'booked_by_email': '',
            'passenger_name': '',
            'passenger_phone': '',
            'passenger_email': '',
            'start_date': '',
            'end_date': '',
            'reporting_time': '',
            'from_location': '',
            'to_location': '',
            'vehicle_group': '',
            'reporting_address': '',
            'drop_address': '',
            'flight_train_number': '',
            'dispatch_center': '',
            'remarks': '',
            'labels': '',
            'confidence_score': 0.7
        }
        
        # Field mappings for table detection (similar to multiple booking agent)
        field_mappings = {
            # Standard field patterns
            'name of employee': 'passenger_name',
            'employee name': 'passenger_name', 
            'passenger name': 'passenger_name',
            'guest name': 'passenger_name',
            'traveler name': 'passenger_name',
            'contact number': 'passenger_phone',
            'mobile number': 'passenger_phone',
            'phone number': 'passenger_phone',
            'passenger phone': 'passenger_phone',
            'email': 'passenger_email',
            'passenger email': 'passenger_email',
            
            'customer name': 'customer',
            'company name': 'customer',
            'corporate': 'customer',
            'client': 'customer',
            
            'booked by': 'booked_by_name',
            'booking person': 'booked_by_name',
            'coordinator': 'booked_by_name',
            
            'date of travel': 'start_date',
            'travel date': 'start_date',
            'journey date': 'start_date',
            'pickup date': 'start_date',
            'start date': 'start_date',
            
            'pick-up time': 'reporting_time',
            'pickup time': 'reporting_time',
            'reporting time': 'reporting_time',
            'departure time': 'reporting_time',
            
            'from location': 'from_location',
            'pickup location': 'from_location',
            'origin': 'from_location',
            'source': 'from_location',
            'city': 'from_location',
            
            'to location': 'to_location',
            'drop location': 'to_location',
            'destination': 'to_location',
            'drop at': 'to_location',
            
            'pickup address': 'reporting_address',
            'pick-up address': 'reporting_address',
            'reporting address': 'reporting_address',
            'from address': 'reporting_address',
            
            'drop address': 'drop_address',
            'destination address': 'drop_address',
            'to address': 'drop_address',
            
            'vehicle type': 'vehicle_group',
            'car type': 'vehicle_group',
            'cab type': 'vehicle_group',
            'vehicle group': 'vehicle_group',
            
            'flight details': 'flight_train_number',
            'flight number': 'flight_train_number',
            'train number': 'flight_train_number',
            'pnr': 'flight_train_number',
            
            'comments': 'remarks',
            'special instructions': 'remarks',
            'notes': 'remarks',
            'remarks': 'remarks'
        }
        
        # Process content line by line to find key-value pairs
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line or len(line) < 3:
                continue
                
            # Look for key-value patterns
            # Pattern 1: "Key: Value"
            if ':' in line:
                parts = line.split(':', 1)
                if len(parts) == 2:
                    key = parts[0].strip().lower()
                    value = parts[1].strip()
                    
                    # Map the key to our standard field
                    field_name = None
                    for pattern, field in field_mappings.items():
                        if pattern in key:
                            field_name = field
                            break
                    
                    if field_name and value:
                        # Apply normalization based on field type
                        if field_name in ['passenger_phone', 'booked_by_phone']:
                            booking_data[field_name] = self._normalize_phone_number(value)
                        elif field_name in ['start_date', 'end_date']:
                            booking_data[field_name] = self._normalize_date(value)
                        elif field_name == 'reporting_time':
                            booking_data[field_name] = self._normalize_time(value)
                        else:
                            booking_data[field_name] = value
            
            # Pattern 2: Look for specific known formats
            elif '|' in line:
                # Pipe-separated values - try to extract based on position
                parts = [p.strip() for p in line.split('|')]
                if len(parts) >= 2:
                    # Try to identify what these fields are
                    for i, part in enumerate(parts):
                        if self._looks_like_name(part):
                            booking_data['passenger_name'] = part
                        elif self._looks_like_phone(part):
                            booking_data['passenger_phone'] = self._normalize_phone_number(part)
                        elif self._looks_like_date(part):
                            booking_data['start_date'] = self._normalize_date(part)
                        elif self._looks_like_time(part):
                            booking_data['reporting_time'] = self._normalize_time(part)
        
        # Add table extraction note to remarks
        if booking_data['remarks']:
            booking_data['remarks'] += ' (Table format detected)'
        else:
            booking_data['remarks'] = 'Extracted from table format'
        
        return booking_data
    
    def _looks_like_name(self, text: str) -> bool:
        """Check if text looks like a person's name"""
        if not text or len(text) < 2:
            return False
        return bool(re.match(r'^[A-Za-z\s.]+$', text) and len(text.split()) >= 2)
    
    def _looks_like_phone(self, text: str) -> bool:
        """Check if text looks like a phone number"""
        if not text:
            return False
        # Remove all non-digits
        digits_only = re.sub(r'\D', '', text)
        return len(digits_only) >= 10
    
    def _looks_like_date(self, text: str) -> bool:
        """Check if text looks like a date"""
        if not text:
            return False
        date_patterns = [
            r'\d{1,2}[-/]\d{1,2}[-/]\d{4}',
            r'\d{4}[-/]\d{1,2}[-/]\d{1,2}',
            r'\d{1,2}\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)',
            r'(january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2}'
        ]
        text_lower = text.lower()
        return any(re.search(pattern, text_lower) for pattern in date_patterns)
    
    def _looks_like_time(self, text: str) -> bool:
        """Check if text looks like a time"""
        if not text:
            return False
        time_pattern = r'\d{1,2}:?\d{0,2}\s*(am|pm|AM|PM)?'
        return bool(re.search(time_pattern, text))

# Test function
def test_single_booking_agent():
    """Test single booking extraction agent"""
    
    print("🧪 Testing Single Booking Extraction Agent...")
    
    # Sample single booking content
    test_content = """
    Dear Team,
    
    Please arrange a car for Mr. Rajesh Kumar (9876543210) tomorrow.
    
    Details:
    - Date: 25th December 2024
    - Time: 10:30 AM
    - From: Andheri Office, Mumbai
    - To: Mumbai International Airport
    - Vehicle: Innova Crysta preferred
    - Corporate: Accenture India Ltd
    - Purpose: Airport drop service
    
    Thanks,
    Travel Coordinator
    """
    
    # Mock classification result
    from gemma_classification_agent import BookingType, DutyType, ClassificationResult
    
    classification_result = ClassificationResult(
        booking_type=BookingType.SINGLE,
        booking_count=1,
        confidence_score=0.9,
        reasoning="Single airport drop booking",
        detected_duty_type=DutyType.DROP_4_40,
        detected_dates=["2024-12-25"],
        detected_vehicles=["Innova Crysta"],
        detected_drops=["Mumbai Airport"]
    )
    
    # Initialize agent
    agent = SingleBookingExtractionAgent()
    
    print("📊 Processing single booking content...")
    
    try:
        result = agent.extract(test_content, classification_result)
        
        print(f"✅ Extraction Success: {result.success}")
        print(f"📊 Booking Count: {result.booking_count}")
        print(f"🎯 Confidence: {result.confidence_score:.1%}")
        print(f"⏱️ Processing Time: {result.processing_time:.2f}s")
        print(f"💰 Cost: ₹{result.cost_inr:.4f}")
        print(f"🔧 Method: {result.extraction_method}")
        
        if result.error_message:
            print(f"⚠️ Error: {result.error_message}")
        
        # Display DataFrame
        print("\n📋 Extracted Booking DataFrame:")
        print("="*80)
        df = result.bookings_dataframe
        
        # Display key fields
        if not df.empty:
            print(f"Passenger Name: {df.iloc[0]['Passenger Name']}")
            print(f"Phone: {df.iloc[0]['Passenger Phone Number']}")
            print(f"Customer: {df.iloc[0]['Customer']}")
            print(f"From: {df.iloc[0]['From (Service Location)']}")
            print(f"To: {df.iloc[0]['To']}")
            print(f"Date: {df.iloc[0]['Start Date']}")
            print(f"Time: {df.iloc[0]['Rep. Time']}")
            print(f"Vehicle: {df.iloc[0]['Vehicle Group']}")
            print(f"Remarks: {df.iloc[0]['Remarks']}")
        
        print(f"\n📐 DataFrame Shape: {df.shape}")
        print(f"📋 Columns: {len(df.columns)}")
        
        # Cost summary
        cost_summary = agent.get_cost_summary()
        print(f"\n💰 Agent Cost Summary:")
        print(f"Total requests: {cost_summary['total_requests']}")
        print(f"Avg cost per request: ₹{cost_summary['avg_cost_per_request']}")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_single_booking_agent()