#!/usr/bin/env python3
"""
Multiple Booking Extraction Agent
Specialized agent for extracting multiple booking data using Gemma API
"""

import logging
import time
import re
from typing import Dict, List, Optional, Any

from base_extraction_agent import BaseExtractionAgent, BookingData, ExtractionResult
from gemma_classification_agent import ClassificationResult

logger = logging.getLogger(__name__)

class MultipleBookingExtractionAgent(BaseExtractionAgent):
    """
    Specialized extraction agent for multiple bookings
    
    Optimized for:
    - Multiple booking scenarios
    - Table format detection
    - Complex field mapping
    - Bulk processing
    """
    
    def __init__(self, api_key: str = None, model_name: str = "models/gemini-2.5-flash"):
        """Initialize multiple booking extraction agent"""
        super().__init__(api_key, model_name)
        
        # Field mappings from your current multi-booking system
        self.field_mappings = {
            # Vertical layout fields (first image)
            'date & city / car': ['date', 'city', 'car_type', 'travel_date'],
            'pick up – time': ['pickup_time', 'reporting_time'],
            'global leaders': ['passenger_name', 'guest_name', 'traveler'],
            'pick up address': ['pickup_address', 'reporting_address', 'from_location'],
            'drop address': ['drop_address', 'destination', 'to_location'],
            'comments': ['remarks', 'special_instructions', 'notes'],
            'at disposal': ['duty_type', 'service_type', 'usage'],
            
            # Horizontal layout fields (second image)
            'name of employee': ['passenger_name', 'employee_name', 'guest_name'],
            'contact number': ['passenger_phone', 'mobile_number', 'phone'],
            'city': ['pickup_city', 'from_location', 'city'],
            'date of travel': ['travel_date', 'start_date', 'date'],
            'pick-up time': ['pickup_time', 'reporting_time'],
            'cab type': ['vehicle_group', 'car_type', 'vehicle_type'],
            'pick-up address': ['pickup_address', 'reporting_address'],
            'drop at': ['drop_address', 'destination', 'to_location'],
            'flight details': ['flight_train_number', 'flight_number'],
            'company name': ['corporate', 'company', 'billing_entity'],
            
            # Generic field mappings
            'full day': ['duty_type', 'usage_type'],
            'crysta': ['vehicle_group', 'car_type'],
            'innova': ['vehicle_group', 'car_type'],
            'dzire': ['vehicle_group', 'car_type'],
        }
        
        logger.info("MultipleBookingExtractionAgent initialized with field mappings")
    
    def extract(self, content: str, classification_result: ClassificationResult) -> ExtractionResult:
        """
        Extract multiple booking data from content
        
        Args:
            content: Email content or OCR extracted text
            classification_result: Result from classification agent
            
        Returns:
            ExtractionResult with multiple bookings DataFrame
        """
        start_time = time.time()
        expected_count = classification_result.booking_count
        logger.info(f"Starting multiple booking extraction ({len(content)} chars, expecting {expected_count} bookings)")
        
        try:
            # Use Gemma API if available, otherwise fallback
            if self.model:
                return self._extract_with_gemma(content, classification_result, start_time)
            else:
                return self._extract_with_fallback(content, classification_result, start_time)
                
        except Exception as e:
            logger.error(f"Multiple booking extraction failed: {str(e)}")
            processing_time = time.time() - start_time
            
            return ExtractionResult(
                success=False,
                bookings_dataframe=self._create_dataframe_from_bookings([]),
                booking_count=0,
                confidence_score=0.0,
                processing_time=processing_time,
                cost_inr=0.0,
                extraction_method="multiple_booking_extraction_failed",
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
            bookings_list = parsed_data.get('bookings', [])
            bookings = []
            
            for i, booking_dict in enumerate(bookings_list):
                booking = self._create_booking_from_dict(booking_dict)
                booking.extraction_method = f"multiple_booking_gemma_{i+1}"
                bookings.append(booking)
            
            # Create DataFrame
            df = self._create_dataframe_from_bookings(bookings)
            
            processing_time = time.time() - start_time
            
            logger.info(f"Multiple bookings extracted successfully ({len(bookings)} bookings, cost: ₹{cost:.4f}, time: {processing_time:.2f}s)")
            
            return ExtractionResult(
                success=True,
                bookings_dataframe=df,
                booking_count=len(bookings),
                confidence_score=parsed_data.get('confidence_score', 0.8),
                processing_time=processing_time,
                cost_inr=cost,
                extraction_method="multiple_booking_gemma",
                metadata={
                    'classification_confidence': classification_result.confidence_score,
                    'detected_duty_type': classification_result.detected_duty_type.value,
                    'expected_booking_count': classification_result.booking_count,
                    'actual_booking_count': len(bookings),
                    'table_format_detected': parsed_data.get('table_format', 'unknown'),
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
        
        logger.warning("Using rule-based fallback extraction for multiple bookings")
        
        # Simple rule-based extraction
        bookings_data = self._rule_based_multiple_extraction(content, classification_result)
        bookings = []
        
        for i, booking_dict in enumerate(bookings_data):
            booking = self._create_booking_from_dict(booking_dict)
            booking.extraction_method = f"multiple_booking_fallback_{i+1}"
            
            if error:
                booking.remarks = f"{booking.remarks} (Fallback used due to: {error})" if booking.remarks else f"Fallback used due to: {error}"
            
            bookings.append(booking)
        
        # Create DataFrame
        df = self._create_dataframe_from_bookings(bookings)
        
        processing_time = time.time() - start_time
        
        return ExtractionResult(
            success=True,
            bookings_dataframe=df,
            booking_count=len(bookings),
            confidence_score=0.6,  # Lower confidence for fallback
            processing_time=processing_time,
            cost_inr=0.0,  # No cost for fallback
            extraction_method="multiple_booking_fallback",
            error_message=error or "",
            metadata={
                'fallback_used': True,
                'classification_confidence': classification_result.confidence_score,
                'expected_booking_count': classification_result.booking_count,
                'actual_booking_count': len(bookings)
            }
        )
    
    def _build_extraction_prompt(self, content: str, classification_result: ClassificationResult) -> str:
        """Build extraction prompt for multiple bookings"""
        
        expected_count = classification_result.booking_count
        
        return f"""You are an expert car rental booking data extraction agent. Extract booking information for MULTIPLE bookings from the content.

CLASSIFICATION CONTEXT:
- Booking Type: {classification_result.booking_type.value}
- Expected Booking Count: {expected_count}
- Detected Duty Type: {classification_result.detected_duty_type.value}
- Confidence: {classification_result.confidence_score:.1%}
- Business Rule Applied: Based on {classification_result.reasoning[:100]}...

CONTENT TO EXTRACT FROM:
{content}

MULTIPLE BOOKING PATTERNS TO DETECT:
1. **Table Format**: Horizontal columns (Cab 1, Cab 2, Cab 3) or vertical key-value pairs
2. **Sequential Format**: Separate booking sections with dates/passengers
3. **Alternate Days**: Same passenger, different non-consecutive dates  
4. **Vehicle Changes**: Same passenger, different vehicles across days
5. **Multiple Drops**: Same day, multiple drop locations

EXTRACTION RULES:
1. Extract exactly {expected_count} bookings based on classification
2. Each booking must have ALL 19 standardized fields
3. Normalize phone numbers to 10 digits
4. Format dates as YYYY-MM-DD
5. Format times as HH:MM
6. Clean and standardize all fields
7. Leave duty_type field empty (will be filled by validation agent)
8. If information is missing for a booking, leave field empty (don't guess)

FIELD MAPPING GUIDELINES:
- customer: Company/corporate name (may be same for all bookings)
- booked_by_name: Person who made the booking
- passenger_name: Actual traveler name (different for each booking)
- from_location: Source city/location (city name only)
- to_location: Destination city/location (city name only)
- reporting_address: Full pickup address
- drop_address: Full drop address
- vehicle_group: Car type (Dzire, Innova, etc.)
- duty_type: Leave empty for now
- flight_train_number: Flight/train details if mentioned

TABLE PROCESSING:
- If horizontal table format: Each column = one booking
- If vertical format: Each entry/row = one booking
- Map field names intelligently using the field mapping guidelines

Return ONLY this JSON format:

{{
    "analysis": "Step-by-step extraction process explaining how bookings were identified",
    "table_format": "horizontal|vertical|sequential|mixed",
    "bookings": [
        {{
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
        }}
    ],
    "confidence_score": 0.0-1.0,
    "extraction_notes": "Any notes about extraction quality, table format, or missing information"
}}

EXTRACT ALL {expected_count} BOOKINGS NOW:"""
    
    def _rule_based_multiple_extraction(self, content: str, classification_result: ClassificationResult) -> List[Dict[str, Any]]:
        """Simple rule-based extraction for multiple bookings"""
        
        expected_count = classification_result.booking_count
        bookings_data = []
        
        # Try to detect different patterns
        if self._is_table_format(content):
            bookings_data = self._extract_from_table_format(content, expected_count)
        elif self._is_sequential_format(content):
            bookings_data = self._extract_from_sequential_format(content, expected_count)
        else:
            # Default: create bookings based on detected patterns
            bookings_data = self._extract_from_general_format(content, classification_result)
        
        # Ensure we have at least the expected number of bookings
        while len(bookings_data) < expected_count:
            # Create additional bookings with partial information
            base_booking = bookings_data[0] if bookings_data else self._create_default_booking(content)
            additional_booking = base_booking.copy()
            additional_booking['remarks'] = f"Additional booking {len(bookings_data) + 1} (auto-generated)"
            bookings_data.append(additional_booking)
        
        # Limit to expected count
        return bookings_data[:expected_count]
    
    def _is_table_format(self, content: str) -> bool:
        """Detect if content has table format"""
        # Look for table indicators
        table_indicators = ['cab 1', 'cab 2', 'booking 1', 'booking 2', '|', '\t']
        content_lower = content.lower()
        return any(indicator in content_lower for indicator in table_indicators)
    
    def _is_sequential_format(self, content: str) -> bool:
        """Detect if content has sequential format"""
        # Look for sequential indicators
        sequential_indicators = ['booking 1:', 'booking 2:', '1.', '2.', 'first', 'second']
        content_lower = content.lower()
        return any(indicator in content_lower for indicator in sequential_indicators)
    
    def _extract_from_table_format(self, content: str, expected_count: int) -> List[Dict[str, Any]]:
        """Extract from table format"""
        bookings = []
        
        # Simple table parsing (this could be enhanced with your Textract logic)
        lines = content.split('\n')
        
        # Look for column headers
        for line in lines:
            if 'cab' in line.lower() or 'booking' in line.lower():
                # This is a table header - extract booking columns
                parts = line.split()
                for i, part in enumerate(parts):
                    if 'cab' in part.lower() or 'booking' in part.lower():
                        # Create a booking for this column
                        booking = self._create_default_booking(content)
                        booking['remarks'] = f"Extracted from table column: {part}"
                        bookings.append(booking)
                        
                        if len(bookings) >= expected_count:
                            break
                break
        
        return bookings
    
    def _extract_from_sequential_format(self, content: str, expected_count: int) -> List[Dict[str, Any]]:
        """Extract from sequential format"""
        bookings = []
        
        # Split content by booking indicators
        booking_sections = re.split(r'(?i)(booking\s+\d+|^\d+\.|\n\d+\.)', content)
        
        for section in booking_sections:
            if section and len(section.strip()) > 20:  # Ignore short sections
                booking = self._extract_single_booking_from_text(section)
                booking['remarks'] = f"Sequential booking {len(bookings) + 1}"
                bookings.append(booking)
                
                if len(bookings) >= expected_count:
                    break
        
        return bookings
    
    def _extract_from_general_format(self, content: str, classification_result: ClassificationResult) -> List[Dict[str, Any]]:
        """Extract from general format based on classification patterns"""
        bookings = []
        expected_count = classification_result.booking_count
        
        # Use classification hints to create bookings
        if hasattr(classification_result, 'detected_dates') and classification_result.detected_dates:
            # Create one booking per date
            for i, date in enumerate(classification_result.detected_dates[:expected_count]):
                booking = self._create_default_booking(content)
                booking['start_date'] = date
                booking['remarks'] = f"Booking for date: {date}"
                bookings.append(booking)
        
        elif hasattr(classification_result, 'detected_vehicles') and classification_result.detected_vehicles:
            # Create one booking per vehicle type
            for i, vehicle in enumerate(classification_result.detected_vehicles[:expected_count]):
                booking = self._create_default_booking(content)
                booking['vehicle_group'] = vehicle
                booking['remarks'] = f"Booking with vehicle: {vehicle}"
                bookings.append(booking)
        
        else:
            # Default: create expected number of bookings
            for i in range(expected_count):
                booking = self._create_default_booking(content)
                booking['remarks'] = f"Booking {i+1} (general extraction)"
                bookings.append(booking)
        
        return bookings
    
    def _extract_single_booking_from_text(self, text: str) -> Dict[str, Any]:
        """Extract a single booking from text section"""
        booking_data = self._create_default_booking(text)
        
        # Enhanced extraction for this section
        text_lower = text.lower()
        
        # Extract phone numbers
        phone_pattern = r'(\d{10}|\+91\d{10}|91\d{10})'
        phones = re.findall(phone_pattern, text)
        if phones:
            booking_data['passenger_phone'] = self._normalize_phone_number(phones[0])
        
        # Extract names
        name_patterns = [
            r'passenger[:\s]+([A-Za-z\s]+)',
            r'name[:\s]+([A-Za-z\s]+)',
            r'mr\.?\s+([A-Za-z\s]+)',
            r'ms\.?\s+([A-Za-z\s]+)'
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, text_lower)
            if match:
                booking_data['passenger_name'] = match.group(1).strip().title()
                break
        
        return booking_data
    
    def _create_default_booking(self, content: str) -> Dict[str, Any]:
        """Create default booking with basic extraction"""
        
        # Use the single booking rule-based extraction as base
        from single_booking_extraction_agent import SingleBookingExtractionAgent
        temp_agent = SingleBookingExtractionAgent()
        
        # Create mock classification result
        from gemma_classification_agent import BookingType, DutyType, ClassificationResult
        mock_result = ClassificationResult(
            booking_type=BookingType.SINGLE,
            booking_count=1,
            confidence_score=0.6,
            reasoning="Default booking creation",
            detected_duty_type=DutyType.UNKNOWN,
            detected_dates=[],
            detected_vehicles=[],
            detected_drops=[]
        )
        
        return temp_agent._rule_based_extraction(content, mock_result)

# Test function
def test_multiple_booking_agent():
    """Test multiple booking extraction agent"""
    
    print("🧪 Testing Multiple Booking Extraction Agent...")
    
    # Sample multiple booking content
    test_content = """
    Multiple car bookings required:
    
    Booking 1:
    - Passenger: John Smith (9876543210)
    - Date: 25th December 2024
    - Time: 9:00 AM
    - From: Delhi Office
    - To: Gurgaon
    - Vehicle: Dzire
    
    Booking 2:
    - Passenger: Mary Wilson (9876543211)
    - Date: 26th December 2024
    - Time: 10:00 AM
    - From: Mumbai Office
    - To: Mumbai Airport
    - Vehicle: Innova
    
    Booking 3:
    - Passenger: Peter Kumar (9876543212)
    - Date: 27th December 2024
    - Time: 2:00 PM
    - From: Bangalore Office
    - To: Electronic City
    - Vehicle: Crysta
    
    Corporate: TechCorp India
    Separate bookings for each passenger.
    """
    
    # Mock classification result
    from gemma_classification_agent import BookingType, DutyType, ClassificationResult
    
    classification_result = ClassificationResult(
        booking_type=BookingType.MULTIPLE,
        booking_count=3,
        confidence_score=0.9,
        reasoning="Multiple bookings - separate passengers and dates",
        detected_duty_type=DutyType.DISPOSAL_8_80,
        detected_dates=["2024-12-25", "2024-12-26", "2024-12-27"],
        detected_vehicles=["Dzire", "Innova", "Crysta"],
        detected_drops=["Gurgaon", "Mumbai Airport", "Electronic City"]
    )
    
    # Initialize agent
    agent = MultipleBookingExtractionAgent()
    
    print("📊 Processing multiple booking content...")
    
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
        print("\n📋 Extracted Bookings DataFrame:")
        print("="*80)
        df = result.bookings_dataframe
        
        # Display key fields for each booking
        for i in range(len(df)):
            print(f"\nBooking {i+1}:")
            print(f"  Passenger: {df.iloc[i]['Passenger Name']}")
            print(f"  Phone: {df.iloc[i]['Passenger Phone Number']}")
            print(f"  Date: {df.iloc[i]['Start Date']}")
            print(f"  From: {df.iloc[i]['From (Service Location)']}")
            print(f"  To: {df.iloc[i]['To']}")
            print(f"  Vehicle: {df.iloc[i]['Vehicle Group']}")
        
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
    test_multiple_booking_agent()