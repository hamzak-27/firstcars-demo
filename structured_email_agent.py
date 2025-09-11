"""
Structured Email AI Agent
Specialized agent for extracting multiple booking records from structured/table-based emails
"""

import os
import json
import re
import csv
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
import openai
from openai import OpenAI

# Import the base BookingExtraction class
from car_rental_ai_agent import BookingExtraction, CarRentalAIAgent

# Configure logging
logger = logging.getLogger(__name__)

@dataclass
class StructuredExtractionResult:
    """Result from structured email processing"""
    bookings: List[BookingExtraction]
    total_bookings_found: int
    extraction_method: str
    confidence_score: float
    processing_notes: str

class StructuredEmailAgent(CarRentalAIAgent):
    """Specialized AI agent for structured/table-based email processing"""
    
    def __init__(self, openai_api_key: str = None):
        """Initialize the structured email agent"""
        super().__init__(openai_api_key)
        self.structured_system_prompt = self._build_structured_system_prompt()
    
    def extract_structured_bookings(self, email_content: str, sender_email: str = None) -> StructuredExtractionResult:
        """
        Extract multiple booking records from structured email content
        
        Args:
            email_content: Raw email content containing tables/structured data
            sender_email: Sender's email address (optional)
            
        Returns:
            StructuredExtractionResult with multiple BookingExtraction objects
        """
        logger.info("Starting structured booking data extraction")
        
        try:
            # Use GPT-4o to analyze and extract structured data
            extraction_result = self._extract_structured_with_reasoning(email_content, sender_email)
            
            # Process the results into BookingExtraction objects
            bookings = self._process_structured_results(extraction_result)
            
            # Create result object
            result = StructuredExtractionResult(
                bookings=bookings,
                total_bookings_found=len(bookings),
                extraction_method="structured_ai_analysis",
                confidence_score=extraction_result.get('overall_confidence', 0.5),
                processing_notes=extraction_result.get('processing_notes', '')
            )
            
            logger.info(f"Structured extraction completed. Found {len(bookings)} booking(s)")
            return result
            
        except Exception as e:
            logger.error(f"Structured extraction failed: {str(e)}")
            # Return empty result with error
            return StructuredExtractionResult(
                bookings=[],
                total_bookings_found=0,
                extraction_method="error",
                confidence_score=0.0,
                processing_notes=f"Extraction failed: {str(e)}"
            )
    
    def _extract_structured_with_reasoning(self, email_content: str, sender_email: str = None) -> Dict:
        """Use GPT-4o to analyze structured email content and extract multiple bookings"""
        
        user_prompt = f"""
Please analyze this structured email content and extract ALL booking information. This email may contain:
- Tables with multiple booking rows
- Tables with booking information in columns  
- Mixed formats with multiple bookings
- Single structured booking

EMAIL CONTENT:
{email_content}

SENDER EMAIL: {sender_email or 'Not provided'}

INSTRUCTIONS:
1. Carefully analyze the structure to identify how many separate bookings are present
2. Each booking should be a separate record, even if they share some common information
3. Extract the same fields as unstructured emails for each booking
4. If information is missing for a booking, use null
5. Pay attention to table headers and data organization

Please provide your analysis in this EXACT JSON format:

{{
    "analysis": "Your step-by-step analysis of the structured content and how many bookings you found",
    "bookings_count": 3,
    "bookings": [
        {{
            "booking_number": 1,
            "corporate": "company name or null",
            "booked_by_name": "booker name or null",
            "booked_by_phone": "booker phone or null", 
            "booked_by_email": "booker email or null",
            "passenger_name": "passenger name or null",
            "passenger_phone": "passenger phone (10 digits) or null",
            "passenger_email": "passenger email or null",
            "from_location": "source location/city or null",
            "to_location": "destination location/city or null", 
            "vehicle_group": "vehicle type or null",
            "duty_type": "duty type or null",
            "start_date": "YYYY-MM-DD format or null",
            "end_date": "YYYY-MM-DD format or null",
            "reporting_time": "HH:MM format or null",
            "start_from_garage": "garage info or null",
            "reporting_address": "complete pickup address or null",
            "drop_address": "complete drop address or null",
            "flight_train_number": "flight/train number or null",
            "dispatch_center": "dispatch info or null",
            "bill_to": "billing entity or null",
            "price": "price info or null",
            "remarks": "special instructions/notes or null",
            "labels": "any labels or null",
            "additional_info": "any other relevant information or null"
        }}
        // ... more bookings if found
    ],
    "overall_confidence": 0.85,
    "processing_notes": "Notes about the extraction process"
}}

Return ONLY valid JSON, no additional text.
"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": self.structured_system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                max_tokens=4000  # Increased for multiple bookings
            )
            
            # Extract and parse JSON response
            ai_response = response.choices[0].message.content.strip()
            json_data = self._parse_json_response(ai_response)
            
            return json_data
            
        except Exception as e:
            logger.error(f"Structured GPT-4o extraction failed: {str(e)}")
            raise
    
    def _process_structured_results(self, extraction_result: Dict) -> List[BookingExtraction]:
        """Process AI extraction results into BookingExtraction objects"""
        
        bookings = []
        
        if 'bookings' not in extraction_result:
            logger.warning("No 'bookings' key found in extraction result")
            return bookings
        
        for i, booking_data in enumerate(extraction_result['bookings']):
            try:
                # Remove booking_number if present (not part of BookingExtraction)
                booking_data.pop('booking_number', None)
                
                # Process each field with validation and normalization
                processed_data = {}
                
                for field, value in booking_data.items():
                    if value is None or (isinstance(value, str) and value.lower() in ['null', 'none', 'not provided', '']):
                        processed_data[field] = None
                    elif isinstance(value, str):
                        value = value.strip()
                        
                        # Apply same field-specific processing as unstructured agent
                        if field == 'vehicle_group':
                            processed_data[field] = self._map_vehicle_type(value)
                        elif field in ['from_location', 'to_location']:
                            processed_data[field] = self._map_city_name(value)
                        elif field in ['booked_by_phone', 'passenger_phone']:
                            processed_data[field] = self._clean_phone_number(value)
                        elif field in ['start_date', 'end_date']:
                            processed_data[field] = self._normalize_date(value)
                        elif field == 'reporting_time':
                            normalized_time = self._normalize_time(value)
                            processed_data[field] = self._round_time_to_15_minutes(normalized_time)
                        else:
                            processed_data[field] = value if value else None
                    else:
                        processed_data[field] = value
                
                # Add confidence score
                processed_data['confidence_score'] = extraction_result.get('overall_confidence', 0.5)
                processed_data['extraction_reasoning'] = f"Structured extraction - booking {i+1} of {len(extraction_result['bookings'])}"
                
                # Auto-fill end_date if not provided
                if processed_data.get('start_date') and not processed_data.get('end_date'):
                    remarks = processed_data.get('remarks') or ''
                    if 'round trip' not in remarks.lower():
                        processed_data['end_date'] = processed_data['start_date']
                
                # Create BookingExtraction object
                booking = BookingExtraction(**processed_data)
                bookings.append(booking)
                
            except Exception as e:
                logger.error(f"Error processing booking {i+1}: {str(e)}")
                # Create error booking
                error_booking = BookingExtraction(
                    remarks=f"Processing failed for booking {i+1}: {str(e)}",
                    confidence_score=0.0
                )
                bookings.append(error_booking)
        
        return bookings
    
    def _build_structured_system_prompt(self) -> str:
        """Build system prompt for structured email processing"""
        return """You are an expert AI agent specialized in extracting car rental booking information from STRUCTURED emails and tables. You excel at:

STRUCTURED DATA ANALYSIS:
1. Analyzing tables, forms, and structured content to identify multiple bookings
2. Understanding different table layouts (rows vs columns vs mixed)
3. Detecting when data represents multiple separate bookings vs single booking
4. Extracting consistent information across different structured formats

MULTI-BOOKING DETECTION RULES:
1. Each row in a booking table typically represents ONE separate booking
2. Each column might represent ONE booking in some formats
3. Some tables mix information - use context to determine booking boundaries
4. Common booking indicators: different passenger names, different dates/times, different destinations
5. Shared information (like company name) may apply to multiple bookings

IMPORTANT PROCESSING RULES:
1. Always think step-by-step about the table structure first
2. Identify how many distinct bookings are present
3. Extract the same comprehensive field set for each booking
4. Apply proper data normalization and standardization
5. Use null for genuinely missing information
6. Provide high confidence scores for well-structured data

DATA STANDARDIZATION:
- Vehicle names: Map to standard types (e.g., "Dzire" → "Swift Dzire")
- City names: Use location mapping for consistency  
- Phone numbers: Clean to 10 digits (remove +91, spaces, hyphens)
- Dates: Convert to YYYY-MM-DD format
- Times: Convert to HH:MM 24-hour format and round to 15-minute intervals
- Addresses: Extract city names for from/to locations

TABLE ANALYSIS APPROACH:
1. First, identify table headers and structure
2. Determine data organization pattern (row-based vs column-based)
3. Count distinct bookings based on unique combinations of key fields
4. Extract each booking maintaining data relationships
5. Apply validation and standardization to each booking"""
    
    def detect_email_type(self, email_content: str) -> str:
        """
        Detect if email contains structured data (tables) or is unstructured text
        
        Returns: 'structured' or 'unstructured'
        """
        content_lower = email_content.lower()
        
        # Look for table indicators
        table_indicators = [
            '<table', '</table>', '<tr>', '</tr>', '<td>', '</td>',
            '|', '├', '┌', '└', '─', '│',  # ASCII table chars
            'reservation form', 'booking form', 'travel requisition',
            'corporate name', 'booked by', 'passenger details'
        ]
        
        # Count structured indicators
        structured_score = 0
        for indicator in table_indicators:
            if indicator in content_lower:
                structured_score += content_lower.count(indicator)
        
        # Also check for repetitive field patterns (common in tables)
        field_patterns = [
            r'name.*:.*\n.*phone.*:',
            r'passenger.*\n.*mobile.*\n.*date',
            r'pick.*up.*\n.*destination',
            r'corporate.*\n.*booked.*by',
        ]
        
        for pattern in field_patterns:
            if re.search(pattern, content_lower, re.DOTALL):
                structured_score += 5
        
        # Decision threshold
        if structured_score >= 3:
            return 'structured'
        else:
            return 'unstructured'
    
    def process_email_intelligently(self, email_content: str, sender_email: str = None) -> StructuredExtractionResult:
        """
        Intelligently route email to appropriate processing method
        
        Args:
            email_content: Email content to process
            sender_email: Sender email (optional)
            
        Returns:
            StructuredExtractionResult (even for unstructured, converted to this format)
        """
        email_type = self.detect_email_type(email_content)
        
        logger.info(f"Detected email type: {email_type}")
        
        if email_type == 'structured':
            return self.extract_structured_bookings(email_content, sender_email)
        else:
            # Process as unstructured but convert to structured result format
            booking = self.extract_booking_data(email_content, sender_email)
            
            return StructuredExtractionResult(
                bookings=[booking],
                total_bookings_found=1,
                extraction_method="unstructured_converted",
                confidence_score=booking.confidence_score or 0.5,
                processing_notes="Processed as unstructured email, converted to structured result format"
            )
    
    def get_processing_summary(self, result: StructuredExtractionResult) -> str:
        """Generate human-readable summary of processing results"""
        if not result.bookings:
            return f"❌ No bookings extracted. {result.processing_notes}"
        
        summary_lines = [
            f"📧 Email processing completed",
            f"📊 Found {result.total_bookings_found} booking(s)",
            f"🔧 Method: {result.extraction_method}",
            f"🎯 Confidence: {result.confidence_score:.1%}"
        ]
        
        # Add booking summaries
        for i, booking in enumerate(result.bookings, 1):
            if booking.passenger_name:
                summary_lines.append(f"  {i}. {booking.passenger_name} - {booking.from_location or 'Unknown'} to {booking.to_location or 'Unknown'}")
            else:
                summary_lines.append(f"  {i}. Booking {i} (incomplete data)")
        
        if result.processing_notes:
            summary_lines.append(f"📝 Notes: {result.processing_notes}")
        
        return "\n".join(summary_lines)
