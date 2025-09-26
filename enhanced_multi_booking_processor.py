"""
Enhanced Multi-Booking Table Processor
Handles complex table layouts with multiple bookings in vertical and horizontal formats
"""

import logging
import json
import re
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import asdict

from enhanced_form_processor import EnhancedFormProcessor
from enhanced_duty_type_detector import enhance_duty_type_detection
from car_rental_ai_agent import BookingExtraction

logger = logging.getLogger(__name__)

class EnhancedMultiBookingProcessor(EnhancedFormProcessor):
    """Enhanced processor for multi-booking tables with complex layouts"""
    
    def __init__(self, aws_region: str = 'us-east-1', openai_api_key: str = None):
        super().__init__(aws_region, openai_api_key)
        
        # Field mappings for different table layouts
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
    
    def process_multi_booking_document(self, file_content: bytes, filename: str, file_type: str = None) -> 'StructuredExtractionResult':
        """
        Process a document with enhanced multi-booking table extraction
        """
        logger.info(f"Enhanced multi-booking processing document: {filename}")
        
        if not self.textract_available:
            logger.warning("Textract not available, using fallback processing")
            return self._fallback_processing(file_content, filename, file_type)
        
        try:
            # Step 1: Extract structured data using enhanced Textract features
            extracted_data = self._extract_structured_data(file_content, filename)
            
            if not extracted_data:
                return self._create_error_result("Could not extract structured data from document", filename)
            
            # Step 2: Detect table layout and extract multiple bookings
            bookings = self._extract_multiple_bookings_from_tables(extracted_data)
            
            if not bookings:
                # Fallback to single booking extraction
                formatted_text = self._format_extracted_data(extracted_data)
                result = self.email_processor.process_email(formatted_text)
                bookings = result.bookings
            
            # Step 3: Apply enhanced duty type detection to each booking
            try:
                from car_rental_ai_agent import CarRentalAIAgent
                temp_agent = CarRentalAIAgent(openai_api_key=self.openai_api_key)
                
                for booking in bookings:
                    # Create a mock result for duty type detection
                    from structured_email_agent import StructuredExtractionResult
                    mock_result = StructuredExtractionResult(
                        bookings=[booking],
                        total_bookings_found=1,
                        extraction_method="multi_booking_processing",
                        confidence_score=0.8,
                        processing_notes=""
                    )
                    
                    # Add structured data to booking for duty type detection
                    if not booking.additional_info:
                        booking.additional_info = ""
                    booking.additional_info += f"\\nStructured Data: {json.dumps(extracted_data, indent=2)}"
                    
                    # Enhance duty type detection
                    enhanced_result = enhance_duty_type_detection(mock_result, temp_agent, "")
                    if enhanced_result.bookings:
                        enhanced_booking = enhanced_result.bookings[0]
                        booking.duty_type = enhanced_booking.duty_type
                        booking.duty_type_reasoning = enhanced_booking.duty_type_reasoning
                
                logger.info(f"Enhanced duty type detection applied to {len(bookings)} bookings")
            except Exception as e:
                logger.warning(f"Enhanced duty type detection failed: {str(e)}")
            
            # Step 4: Create result
            from structured_email_agent import StructuredExtractionResult
            result = StructuredExtractionResult(
                bookings=bookings,
                total_bookings_found=len(bookings),
                extraction_method=f"enhanced_multi_booking_extraction ({file_type or 'unknown'})",
                confidence_score=0.85,
                processing_notes=f"Multi-booking processing: {filename}. Found {len(bookings)} bookings from tables."
            )
            
            logger.info(f"Enhanced multi-booking processing completed: {filename}")
            return result
            
        except Exception as e:
            logger.error(f"Enhanced multi-booking processing failed for {filename}: {str(e)}")
            return self._fallback_processing(file_content, filename, file_type)
    
    def _extract_multiple_bookings_from_tables(self, extracted_data: Dict[str, Any]) -> List[BookingExtraction]:
        """Extract multiple bookings from table structures"""
        bookings = []
        
        # Process tables to find booking data
        tables = extracted_data.get('tables', [])
        
        for table in tables:
            if table['type'] == 'regular_table':
                # Handle regular tables (like your second image - horizontal layout)
                table_bookings = self._extract_from_horizontal_table(table)
                bookings.extend(table_bookings)
            elif table['type'] == 'form_table':
                # Handle form tables (like your first image - vertical layout)
                table_bookings = self._extract_from_vertical_table(table)
                bookings.extend(table_bookings)
        
        # Also check key-value pairs for additional booking info
        kv_pairs = extracted_data.get('key_value_pairs', [])
        if kv_pairs and not bookings:
            # Create single booking from key-value pairs
            booking = self._create_booking_from_kv_pairs(kv_pairs)
            if booking:
                bookings.append(booking)
        
        logger.info(f"Extracted {len(bookings)} bookings from tables")
        return bookings
    
    def _extract_from_horizontal_table(self, table: Dict[str, Any]) -> List[BookingExtraction]:
        """Extract bookings from horizontal table layout (like Cab 1, Cab 2, Cab 3, etc.)"""
        bookings = []
        
        try:
            headers = table.get('headers', [])
            rows = table.get('rows', [])
            
            if not headers or not rows:
                return bookings
            
            logger.info(f"Processing horizontal table with {len(headers)} columns and {len(rows)} rows")
            
            # Identify booking columns (Cab 1, Cab 2, etc.)
            booking_columns = []
            for i, header in enumerate(headers):
                if header and ('cab' in header.lower() or 'booking' in header.lower() or header.strip().isdigit()):
                    booking_columns.append(i)
            
            # If no specific booking columns found, treat each column after the first as a booking
            if not booking_columns and len(headers) > 1:
                booking_columns = list(range(1, len(headers)))  # Skip first column (field names)
            
            logger.info(f"Found booking columns at indices: {booking_columns}")
            
            # Extract data for each booking column
            for col_idx in booking_columns:
                if col_idx < len(headers):
                    booking_data = {}
                    
                    # Extract field-value pairs for this booking
                    for row_idx, row in enumerate(rows):
                        if row_idx == 0:  # Skip header row
                            continue
                        
                        if len(row) > col_idx and len(row) > 0:
                            field_name = row[0].strip().lower() if row[0] else ""
                            field_value = row[col_idx].strip() if col_idx < len(row) and row[col_idx] else ""
                            
                            if field_name and field_value:
                                mapped_field = self._map_field_name(field_name)
                                if mapped_field:
                                    booking_data[mapped_field] = field_value
                    
                    # Create booking from extracted data
                    if booking_data:
                        booking = self._create_booking_from_data(booking_data)
                        if booking:
                            bookings.append(booking)
                            logger.info(f"Created booking {len(bookings)} from column {col_idx}")
        
        except Exception as e:
            logger.error(f"Error extracting from horizontal table: {str(e)}")
        
        return bookings
    
    def _extract_from_vertical_table(self, table: Dict[str, Any]) -> List[BookingExtraction]:
        """Extract bookings from vertical table layout (key-value pairs)"""
        bookings = []
        
        try:
            kv_pairs = table.get('key_value_pairs', [])
            
            if not kv_pairs:
                return bookings
            
            logger.info(f"Processing vertical table with {len(kv_pairs)} key-value pairs")
            
            # Group related fields into bookings
            # Look for patterns that indicate multiple bookings
            booking_groups = self._group_kv_pairs_into_bookings(kv_pairs)
            
            for group in booking_groups:
                booking = self._create_booking_from_kv_pairs(group)
                if booking:
                    bookings.append(booking)
                    logger.info(f"Created booking {len(bookings)} from vertical table")
        
        except Exception as e:
            logger.error(f"Error extracting from vertical table: {str(e)}")
        
        return bookings
    
    def _group_kv_pairs_into_bookings(self, kv_pairs: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
        """Group key-value pairs into separate bookings based on patterns"""
        groups = []
        current_group = []
        
        # Simple grouping logic - can be enhanced based on your specific patterns
        for kv in kv_pairs:
            key = kv.get('key', '').lower()
            value = kv.get('value', '')
            
            # Check if this starts a new booking (e.g., date field, name field)
            if any(pattern in key for pattern in ['date', 'name', 'employee']) and current_group:
                # Start new group
                groups.append(current_group)
                current_group = [kv]
            else:
                current_group.append(kv)
        
        # Add the last group
        if current_group:
            groups.append(current_group)
        
        return groups if len(groups) > 1 else [kv_pairs]  # If only one group, return all as single booking
    
    def _map_field_name(self, field_name: str) -> Optional[str]:
        """Map a field name to standard booking field"""
        field_lower = field_name.lower().strip()
        
        # Direct mappings
        field_mapping = {
            'name of employee': 'passenger_name',
            'contact number': 'passenger_phone',
            'city': 'from_location',
            'date of travel': 'start_date',
            'pick-up time': 'reporting_time',
            'cab type': 'vehicle_group',
            'pick-up address': 'reporting_address',
            'drop at': 'drop_address',
            'flight details': 'flight_train_number',
            'company name': 'corporate',
            'global leaders': 'passenger_name',
            'pick up address': 'reporting_address',
            'drop address': 'drop_address',
            'comments': 'remarks',
            'pick up – time': 'reporting_time',
            'date & city / car': 'start_date'  # Will need special handling
        }
        
        # Check direct mappings first
        if field_lower in field_mapping:
            return field_mapping[field_lower]
        
        # Check partial matches
        for pattern, target_field in self.field_mappings.items():
            if pattern in field_lower:
                return target_field[0]  # Return first mapped field
        
        # Fallback patterns
        if 'name' in field_lower:
            return 'passenger_name'
        elif 'phone' in field_lower or 'contact' in field_lower:
            return 'passenger_phone'
        elif 'date' in field_lower:
            return 'start_date'
        elif 'time' in field_lower:
            return 'reporting_time'
        elif 'address' in field_lower:
            if 'pickup' in field_lower or 'pick up' in field_lower:
                return 'reporting_address'
            elif 'drop' in field_lower:
                return 'drop_address'
        elif 'vehicle' in field_lower or 'car' in field_lower or 'cab' in field_lower:
            return 'vehicle_group'
        elif 'company' in field_lower or 'corporate' in field_lower:
            return 'corporate'
        elif 'flight' in field_lower:
            return 'flight_train_number'
        elif 'remark' in field_lower or 'comment' in field_lower:
            return 'remarks'
        
        return None
    
    def _create_booking_from_data(self, booking_data: Dict[str, str]) -> Optional[BookingExtraction]:
        """Create BookingExtraction from mapped data"""
        try:
            # Initialize booking with default values
            booking_params = {}
            
            # Map the extracted data to booking fields
            for field, value in booking_data.items():
                if value and value.strip():
                    booking_params[field] = value.strip()
            
            # Handle special cases
            self._handle_special_field_cases(booking_params)
            
            # Create booking
            booking = BookingExtraction(**booking_params)
            
            # Set confidence based on completeness
            required_fields = ['passenger_name', 'start_date', 'reporting_time']
            filled_required = sum(1 for field in required_fields if getattr(booking, field, None))
            confidence = min(0.9, 0.3 + (filled_required / len(required_fields)) * 0.6)
            booking.confidence_score = confidence
            
            logger.info(f"Created booking with confidence {confidence:.2f}")
            return booking
            
        except Exception as e:
            logger.error(f"Error creating booking from data: {str(e)}")
            return None
    
    def _create_booking_from_kv_pairs(self, kv_pairs: List[Dict[str, Any]]) -> Optional[BookingExtraction]:
        """Create BookingExtraction from key-value pairs"""
        booking_data = {}
        
        for kv in kv_pairs:
            key = kv.get('key', '').strip()
            value = kv.get('value', '').strip()
            
            if not key or not value:
                continue
            
            mapped_field = self._map_field_name(key)
            if mapped_field:
                booking_data[mapped_field] = value
        
        return self._create_booking_from_data(booking_data) if booking_data else None
    
    def _handle_special_field_cases(self, booking_params: Dict[str, str]):
        """Handle special field cases like combined date/city fields"""
        
        # Handle "Date & City / Car" field
        if 'start_date' in booking_params:
            date_value = booking_params['start_date']
            
            # Check if it contains combined information
            if ',' in date_value or '\\n' in date_value:
                parts = re.split(r'[,\\n]', date_value)
                for part in parts:
                    part = part.strip().lower()
                    if 'sep' in part or 'oct' in part or 'nov' in part or 'dec' in part:
                        # This looks like a date
                        booking_params['start_date'] = part
                    elif 'disposal' in part or 'drop' in part or 'outstation' in part:
                        # This looks like duty type
                        if 'duty_type' not in booking_params:
                            booking_params['duty_type'] = part
                    elif len(part) > 3 and not any(char.isdigit() for char in part):
                        # This might be a city
                        if 'from_location' not in booking_params:
                            booking_params['from_location'] = part
        
        # Normalize vehicle types
        if 'vehicle_group' in booking_params:
            vehicle = booking_params['vehicle_group'].lower()
            if 'crysta' in vehicle:
                booking_params['vehicle_group'] = 'Toyota Innova Crysta'
            elif 'innova' in vehicle:
                booking_params['vehicle_group'] = 'Toyota Innova Crysta'
            elif 'dzire' in vehicle:
                booking_params['vehicle_group'] = 'Swift Dzire'
        
        # Handle duty type indicators
        duty_indicators = ['at disposal', 'full day', 'drop', 'outstation']
        for key, value in list(booking_params.items()):
            if any(indicator in value.lower() for indicator in duty_indicators):
                if 'duty_type' not in booking_params:
                    booking_params['duty_type'] = value
        
        # Set default end_date if not provided
        if 'start_date' in booking_params and 'end_date' not in booking_params:
            booking_params['end_date'] = booking_params['start_date']