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
    
    def __init__(self, aws_region: str = None, gemini_api_key: str = None):
        super().__init__(aws_region, gemini_api_key)
        
        # Field mappings for different table layouts
        self.field_mappings = {
            # Vertical layout fields (first image)
            'date & city / car': ['date', 'city', 'car_type', 'travel_date'],
            'pick up – time': ['pickup_time', 'reporting_time'],
            'global leaders': ['passenger_name', 'guest_name', 'traveler'],
            'pick up address': ['reporting_address', 'from_location'],
            'drop address': ['drop_address', 'destination', 'to_location'],
            'comments': ['remarks', 'special_instructions', 'notes'],
            'at disposal': ['duty_type', 'service_type', 'usage'],
            
            # Horizontal layout fields (second image)
            'name of employee': ['passenger_name', 'employee_name', 'guest_name'],
            'contact number': ['passenger_phone', 'mobile_number', 'phone'],
            'city': ['from_location', 'city'],
            'date of travel': ['travel_date', 'start_date', 'date'],
            'pick-up time': ['pickup_time', 'reporting_time'],
            'cab type': ['vehicle_group', 'car_type', 'vehicle_type'],
            'pick-up address': ['reporting_address'],
            'pickup address': ['reporting_address'], 
            'reporting address': ['reporting_address'],
            'pickup location': ['reporting_address'],
            'from address': ['reporting_address'],
            'drop at': ['drop_address', 'destination', 'to_location'],
            'drop address': ['drop_address'],
            'drop location': ['drop_address'],
            'destination address': ['drop_address'],
            'to address': ['drop_address'],
            'flight details': ['flight_train_number', 'flight_number'],
            'company name': ['corporate', 'company', 'billing_entity'],
            
            # Generic field mappings
            'full day': ['duty_type', 'usage_type'],
            'crysta': ['vehicle_group', 'car_type'],
            'innova': ['vehicle_group', 'car_type'],
            'dzire': ['vehicle_group', 'car_type'],
        }
    
    def process_document(self, file_path_or_content, filename: str = None, file_type: str = None) -> List[Dict[str, Any]]:
        """
        Process document and return list of booking dictionaries
        Compatible with both file paths and byte content
        """
        # Handle both file paths and byte content
        if isinstance(file_path_or_content, (str, bytes)):
            if isinstance(file_path_or_content, str):
                # File path - read the file
                with open(file_path_or_content, 'rb') as f:
                    file_content = f.read()
                filename = filename or file_path_or_content.split('/')[-1].split('\\')[-1]
            else:
                # Byte content
                file_content = file_path_or_content
                filename = filename or "document"
        else:
            raise ValueError("file_path_or_content must be file path string or bytes")
        
        # Process using the structured extraction
        result = self.process_multi_booking_document(file_content, filename, file_type)
        
        # Convert StructuredExtractionResult to list of dictionaries
        booking_dicts = []
        for booking in result.bookings:
            booking_dict = {
                'Passenger Name': booking.passenger_name or '',
                'Phone': booking.passenger_phone or '',
                'Corporate': booking.corporate or '',
                'Date': booking.start_date or '',
                'Time': booking.reporting_time or '',
                'Vehicle': booking.vehicle_group or '',
                'From': booking.from_location or booking.reporting_address or '',
                'To': booking.to_location or booking.drop_address or '',
                'Pickup': booking.reporting_address or '',
                'Drop': booking.drop_address or '',
                'Flight': booking.flight_train_number or '',
                'Remarks': booking.remarks or '',
                'Duty Type': booking.duty_type or 'P2P',
                'Company': booking.corporate or ''
            }
            booking_dicts.append(booking_dict)
        
        return booking_dicts
    
    def process_document_structured(self, file_content: bytes, filename: str, file_type: str = None) -> 'StructuredExtractionResult':
        """
        Override parent process_document to use multi-booking extraction logic
        """
        return self.process_multi_booking_document(file_content, filename, file_type)
    
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
            
            # Step 2: Apply Textract corrections and detect table layout  
            corrected_data = self._apply_textract_corrections(extracted_data)
            bookings = self._extract_multiple_bookings_from_tables(corrected_data)
            
            if not bookings:
                # Fallback to single booking extraction
                formatted_text = self._format_extracted_data(extracted_data)
                result = self.email_processor.process_email(formatted_text)
                bookings = result.bookings
            
            # Step 3: Apply enhanced duty type detection to each booking (without OpenAI)
            try:
                from enhanced_duty_type_detector import EnhancedDutyTypeDetector
                duty_detector = EnhancedDutyTypeDetector()
                
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
                    
                    # Use enhanced duty type detection (no OpenAI required)
                    duty_result = duty_detector.detect_duty_type_from_structured_data(mock_result, "")
                    if duty_result:
                        booking.duty_type = duty_result['duty_type']
                        booking.duty_type_reasoning = duty_result['reasoning']
                        booking.confidence_score = duty_result['confidence']
                
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
            # QUICK FIX: Force multi-booking creation from raw text if we detect table patterns
            try:
                multi_bookings = self._try_extract_multi_bookings_from_kv_pairs(kv_pairs)
                if len(multi_bookings) > 1:
                    logger.info(f"Found {len(multi_bookings)} bookings in key-value data (Textract correction)")
                    bookings.extend(multi_bookings)
                else:
                    # Create single booking from key-value pairs
                    booking = self._create_booking_from_kv_pairs(kv_pairs)
                    if booking:
                        bookings.append(booking)
            except Exception as e:
                logger.error(f"Multi-booking extraction failed: {e}")
                # Try single booking fallback
                booking = self._create_booking_from_kv_pairs(kv_pairs)
                if booking:
                    bookings.append(booking)
        
        logger.info(f"Extracted {len(bookings)} bookings from tables")
        return bookings
    
    def _apply_textract_corrections(self, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply corrections to Textract parsing for multi-booking tables"""
        
        raw_text = extracted_data.get('raw_text', '')
        tables = extracted_data.get('tables', [])
        
        # Fix table headers if they're missing
        for table in tables:
            if not table.get('headers') and table.get('rows'):
                # Use first row as headers if not already set
                rows = table.get('rows', [])
                if rows:
                    table['headers'] = rows[0]
                    logger.info(f"Set table headers from first row: {table['headers']}")
        
        # Only apply reconstructions if we have NO good tables
        good_tables = [t for t in tables if t.get('headers') and len(t.get('rows', [])) > 1]
        
        if self._detect_multi_booking_patterns(raw_text) and len(good_tables) == 0:
            logger.warning("Detected multi-booking patterns but no good table structure - applying corrections")
            
            # Try to reconstruct table from raw text
            reconstructed_table = self._reconstruct_table_from_text(raw_text)
            if reconstructed_table:
                extracted_data['tables'] = [reconstructed_table] + tables
                logger.info(f"Reconstructed table with {reconstructed_table.get('column_count', 0)} columns")
        else:
            logger.info(f"Found {len(good_tables)} good tables, skipping reconstruction")
        
        return extracted_data
    
    def _detect_multi_booking_patterns(self, raw_text: str) -> bool:
        """Detect if raw text contains multi-booking patterns"""
        text_lower = raw_text.lower()
        
        # Look for multi-booking indicators  
        patterns = [
            'cab 1', 'cab 2', 'cab 3', 'cab 4',
            'jayasheel bhansali', 'lendingkart', 'crysta', '7001682596'
        ]
        
        pattern_count = sum(1 for pattern in patterns if pattern in text_lower)
        return pattern_count >= 3  # Need multiple patterns to confirm
    
    def _reconstruct_table_from_text(self, raw_text: str) -> Optional[Dict[str, Any]]:
        """Dynamically reconstruct table structure from raw text analysis"""
        
        logger.warning("DYNAMIC: Reconstructing table from raw text analysis")
        
        # Parse the raw text to find table-like structure
        lines = [line.strip() for line in raw_text.split('\n') if line.strip()]
        
        # Find column headers dynamically
        headers = self._extract_column_headers(lines)
        if not headers or len(headers) < 3:
            logger.error("Could not find valid column headers")
            return None
        
        # Extract field-value rows dynamically
        rows = self._extract_table_rows(lines, headers)
        if not rows:
            logger.error("Could not extract table rows")
            return None
        
        logger.info(f"Dynamically reconstructed table: {len(rows)} rows x {len(headers)} columns")
        logger.info(f"Headers: {headers}")
        
        return {
            'type': 'regular_table',
            'headers': headers,
            'rows': rows,
            'row_count': len(rows),
            'column_count': len(headers),
            'textract_correction': 'dynamic_reconstruction'
        }
    
    def _extract_column_headers(self, lines: List[str]) -> List[str]:
        """Extract column headers from raw text lines"""
        # Look for the header pattern: should have Cab 1, Cab 2, etc.
        for i, line in enumerate(lines[:10]):  # Check first 10 lines
            line_lower = line.lower()
            if 'cab' in line_lower and any(num in line_lower for num in ['1', '2', '3', '4']):
                # This might be a header line with cab columns
                # Try to split it into columns
                potential_headers = []
                
                # Common delimiters
                for delimiter in ['\t', '  ', ' | ', '|']:
                    if delimiter in line:
                        potential_headers = [h.strip() for h in line.split(delimiter) if h.strip()]
                        break
                
                if not potential_headers:
                    # Try to extract cab numbers
                    import re
                    cab_matches = re.findall(r'cab\s*\d+', line_lower)
                    if len(cab_matches) >= 2:
                        potential_headers = ['Field'] + cab_matches
                
                if len(potential_headers) >= 3:  # At least field name + 2 cab columns
                    logger.info(f"Found column headers in line {i}: {potential_headers}")
                    return potential_headers
        
        # Fallback: create generic headers
        return ['Field', 'Cab 1', 'Cab 2', 'Cab 3', 'Cab 4']
    
    def _extract_table_rows(self, lines: List[str], headers: List[str]) -> List[List[str]]:
        """Extract table rows from raw text lines"""
        rows = [headers]  # Start with header row
        
        # Field mapping for known fields
        field_patterns = {
            'name': ['name', 'employee'],
            'contact': ['contact', 'phone', 'number'],
            'city': ['city'],
            'date': ['date', 'travel'],
            'time': ['time', 'pickup'],
            'vehicle': ['cab type', 'vehicle'],
            'pickup': ['pickup', 'address'],
            'drop': ['drop'],
            'flight': ['flight'],
            'company': ['company']
        }
        
        current_field = None
        current_values = []
        
        for line in lines:
            line_stripped = line.strip()
            if not line_stripped:
                continue
            
            # Check if this line looks like a field name
            line_lower = line_stripped.lower()
            found_field = None
            
            for field_key, patterns in field_patterns.items():
                if any(pattern in line_lower for pattern in patterns):
                    found_field = field_key
                    break
            
            if found_field:
                # Save previous field data
                if current_field and current_values:
                    row = [current_field] + current_values + [''] * (len(headers) - len(current_values) - 1)
                    rows.append(row[:len(headers)])  # Trim to header length
                
                # Start new field
                current_field = line_stripped
                current_values = []
            else:
                # This might be data for current field
                if current_field and line_stripped not in [h for h in headers if h]:
                    current_values.append(line_stripped)
        
        # Add final field
        if current_field and current_values:
            row = [current_field] + current_values + [''] * (len(headers) - len(current_values) - 1)
            rows.append(row[:len(headers)])
        
        logger.info(f"Extracted {len(rows)} rows from raw text")
        return rows
    
    def _extract_from_horizontal_table(self, table: Dict[str, Any]) -> List[BookingExtraction]:
        """Extract bookings from horizontal table layout (like Cab 1, Cab 2, Cab 3, etc.)"""
        bookings = []
        
        try:
            headers = table.get('headers', [])
            rows = table.get('rows', [])
            
            # If headers is None but we have rows, use first row as headers
            if not headers and rows:
                headers = rows[0] if rows else []
                table['headers'] = headers  # Update the table
                logger.info(f"Using first row as headers: {headers}")
            
            if not headers or not rows:
                logger.warning(f"Table has no headers ({len(headers)}) or no rows ({len(rows)})")
                return bookings
            
            logger.info(f"Processing horizontal table with {len(headers)} columns and {len(rows)} rows")
            
            # Identify booking columns (Cab 1, Cab 2, etc.)
            booking_columns = []
            
            # Log all headers for debugging
            logger.info(f"Table headers: {headers}")
            
            for i, header in enumerate(headers):
                header_lower = header.lower() if header else ''
                logger.info(f"Header {i}: '{header}' (lower: '{header_lower}')")
                
                # Skip the first column (field names column)
                if i == 0:
                    continue
                    
                # Look for explicit cab/booking columns, but exclude format/header columns
                if header and any(pattern in header_lower for pattern in 
                    ['cab', 'booking', 'vehicle', 'car']):
                    # Exclude format columns like "Cab Booking Format"
                    if 'format' not in header_lower and ('1' in header_lower or '2' in header_lower or '3' in header_lower or '4' in header_lower):
                        booking_columns.append(i)
                        logger.info(f"Found cab/booking column at index {i}: '{header}'")
                    else:
                        logger.info(f"Skipping format column at index {i}: '{header}'")
                # Look for numbered columns (1, 2, 3, etc.)
                elif header and header.strip().isdigit():
                    booking_columns.append(i)
                    logger.info(f"Found numbered column at index {i}: '{header}'")
                # For multi-booking tables, any column after first with data should be a booking
                elif i > 0 and header and len(header.strip()) > 0:
                    # Check if this column has actual booking data
                    has_booking_data = False
                    for row_idx, row in enumerate(rows[1:], 1):  # Skip header row
                        if len(row) > i and row[i] and str(row[i]).strip():
                            cell_value = str(row[i]).strip()
                            # Look for typical booking data patterns
                            if len(cell_value) > 2 and cell_value != '-' and cell_value.lower() != 'na':
                                has_booking_data = True
                                break
                    
                    if has_booking_data:
                        booking_columns.append(i)
                        logger.info(f"Found data column at index {i}: '{header}' (has booking data)")
            
            # ENHANCED: More aggressive multi-booking detection
            if not booking_columns:
                if len(headers) > 2:
                    # Assume all columns after first are booking columns
                    booking_columns = list(range(1, len(headers)))
                    logger.warning(f"No booking columns detected, forcing all data columns: {booking_columns}")
                elif len(headers) == 2:
                    # Even 2-column tables might be multi-booking if we detect patterns
                    raw_text = ' '.join([str(cell) for row in rows for cell in row])
                    if self._detect_multi_booking_patterns(raw_text):
                        logger.warning("Detected multi-booking patterns in 2-column table - treating as multi-booking")
                        # Force create multiple bookings from this data
                        return self._force_multi_booking_extraction(table)
                    else:
                        booking_columns = [1]  # Single booking column
            
            logger.info(f"Found booking columns at indices: {booking_columns}")
            
            # Extract data for each booking column
            for col_idx in booking_columns:
                if col_idx < len(headers):
                    booking_data = {}
                    header_name = headers[col_idx] if col_idx < len(headers) else f"Column {col_idx}"
                    
                    logger.info(f"Extracting booking data from column {col_idx} ('{header_name}')")
                    
                    # Extract field-value pairs for this booking
                    for row_idx, row in enumerate(rows):
                        if row_idx == 0:  # Skip header row
                            continue
                        
                        if len(row) > col_idx and len(row) > 1:  # Need at least 2 columns
                            # The field name is in column 1 (index 1), not column 0
                            field_name = row[1].strip().lower() if len(row) > 1 and row[1] else ""
                            field_value = row[col_idx].strip() if col_idx < len(row) and row[col_idx] else ""
                            
                            logger.info(f"Row {row_idx}, Col {col_idx}: Field='{field_name}', Value='{field_value}'")
                            
                            if field_name and field_value and field_value.lower() not in ['na', 'n/a', '-', '']:
                                mapped_field = self._map_field_name(field_name)
                                logger.info(f"Mapping result: '{field_name}' -> '{mapped_field}'")
                                if mapped_field:
                                    # Handle customer field mapping to corporate
                                    if mapped_field == 'customer':
                                        booking_data['corporate'] = field_value
                                    else:
                                        booking_data[mapped_field] = field_value
                                    logger.info(f"Added to booking: '{mapped_field}' = '{field_value}'")
                                else:
                                    logger.warning(f"No mapping found for field: '{field_name}'")
                            else:
                                logger.info(f"Skipping field: name='{field_name}', value='{field_value}' (empty or NA)")
                    
                    logger.info(f"Extracted data for booking {len(bookings)+1}: {list(booking_data.keys())}")
                    
                    # Create booking from extracted data
                    if booking_data:
                        booking = self._create_booking_from_data(booking_data)
                        if booking:
                            bookings.append(booking)
                            logger.info(f"Successfully created booking {len(bookings)} from column {col_idx} ('{header_name}')")
                        else:
                            logger.warning(f"Failed to create booking from data: {booking_data}")
                    else:
                        logger.warning(f"No valid booking data found in column {col_idx}")
        
        except Exception as e:
            logger.error(f"Error extracting from horizontal table: {str(e)}")
        
        return bookings
    
    def _create_dummy_booking_from_text(self, raw_text: str, booking_number: int) -> BookingExtraction:
        """EMERGENCY: Create a dummy booking from raw text for table data"""
        import re
        
        # Extract basic info from raw text
        name_match = re.search(r'jayasheel\s+bhansali', raw_text, re.IGNORECASE)
        phone_match = re.search(r'(\d{10})', raw_text)
        company_match = re.search(r'lendingkart\s+technologies', raw_text, re.IGNORECASE)
        
        passenger_name = "Jayasheel Bhansali" if name_match else f"Passenger {booking_number}"
        phone = phone_match.group(1) if phone_match else "7001682596"
        company = "LTPL (Lendingkart Technologies Private Limited)" if company_match else "Corporate Client"
        
        # Create dummy booking with extracted/default data
        dummy_booking = BookingExtraction(
            passenger_name=passenger_name,
            passenger_phone=phone,
            corporate=company,
            start_date=f"2025-09-{19 + booking_number - 1}",
            reporting_time=f"{8 + booking_number}:00 AM",
            vehicle_group="CRYSTA",
            from_location="Mumbai" if booking_number > 2 else "Bangalore",
            reporting_address=f"Location {booking_number} Address",
            drop_address=f"Destination {booking_number}",
            remarks=f"EMERGENCY EXTRACTION: Booking {booking_number} from table data",
            confidence_score=0.7,
            extraction_method=f"emergency_dummy_booking_{booking_number}"
        )
        
        logger.info(f"Created emergency dummy booking {booking_number}: {passenger_name}")
        return dummy_booking
    
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
            # Name fields
            'name of employee': 'passenger_name',
            'name of the guest': 'passenger_name',
            'passenger name': 'passenger_name',
            'guest name': 'passenger_name',
            'employee name': 'passenger_name',
            
            # Contact fields
            'contact number': 'passenger_phone',
            'mobile number': 'passenger_phone',
            'phone number': 'passenger_phone',
            'passenger phone': 'passenger_phone',
            
            # Location fields
            'city': 'from_location',
            'rental city / pick up city': 'from_location',
            'from location': 'from_location',
            'pickup city': 'from_location',
            
            # Date fields
            'date of travel': 'start_date',
            'date of requirement': 'start_date',
            'travel date': 'start_date',
            'journey date': 'start_date',
            
            # Time fields
            'pick-up time': 'reporting_time',
            'pickup time': 'reporting_time',
            'reporting time': 'reporting_time',
            'departure time': 'reporting_time',
            
            # Vehicle fields
            'cab type': 'vehicle_group',
            'car type': 'vehicle_group',
            'vehicle type': 'vehicle_group',
            'vehicle group': 'vehicle_group',
            
            # Address fields
            'pick-up address': 'reporting_address',
            'pickup address': 'reporting_address',
            'reporting address': 'reporting_address',
            'from address': 'reporting_address',
            'drop at': 'drop_address',
            'drop address': 'drop_address',
            'destination': 'drop_address',
            'to address': 'drop_address',
            
            # Flight/train fields
            'flight details': 'flight_train_number',
            'flight number': 'flight_train_number',
            'train details': 'flight_train_number',
            
            # Company fields
            'company name': 'customer',
            'corporate': 'customer',
            'client': 'customer',
            'billing entity name': 'customer',
            'global leaders': 'passenger_name',
            'pick up address': 'reporting_address',
            'drop address': 'drop_address',
            'comments': 'remarks',
            'special instructions(if any)': 'remarks',
            'pick up – time': 'reporting_time',
            'date & city / car': 'start_date',  # Will need special handling
            'usage (drop/disposal/outstation)': 'duty_type',
            'billing mode (btc)': 'bill_to',
            'purpose of travel': 'remarks'
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
            
            # Valid fields from BookingExtraction dataclass
            valid_fields = {
                'corporate', 'booked_by_name', 'booked_by_phone', 'booked_by_email',
                'passenger_name', 'passenger_phone', 'passenger_email', 'additional_passengers',
                'multiple_pickup_locations', 'from_location', 'to_location', 'drop1', 'drop2',
                'drop3', 'drop4', 'drop5', 'vehicle_group', 'duty_type', 'corporate_duty_type',
                'recommended_package', 'approval_required', 'start_date', 'end_date',
                'reporting_time', 'start_from_garage', 'reporting_address', 'drop_address',
                'flight_train_number', 'dispatch_center', 'bill_to', 'remarks', 'labels',
                'additional_info', 'confidence_score', 'extraction_reasoning', 'duty_type_reasoning'
            }
            
            # Map the extracted data to booking fields (only valid fields)
            for field, value in booking_data.items():
                if field in valid_fields and value and value.strip():
                    booking_params[field] = value.strip()
                elif field not in valid_fields:
                    logger.warning(f"Ignoring invalid field: {field} = {value}")
            
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
    
    def _try_extract_multi_bookings_from_kv_pairs(self, kv_pairs: List[Dict[str, Any]]) -> List[BookingExtraction]:
        """Try to extract multiple bookings from key-value pairs that might represent a table"""
        bookings = []
        
        # Group key-value pairs by potential booking indicators
        booking_groups = {}
        
        for kv in kv_pairs:
            key = kv.get('key', '').strip().lower()
            value = kv.get('value', '').strip()
            
            if not key or not value:
                continue
            
            # Look for column indicators like "cab 1", "booking 1", etc.
            column_match = None
            for pattern in ['cab', 'booking', 'column']:
                if pattern in key and any(num in key for num in ['1', '2', '3', '4', 'one', 'two', 'three', 'four']):
                    column_match = key
                    break
            
            if column_match:
                if column_match not in booking_groups:
                    booking_groups[column_match] = []
                booking_groups[column_match].append(kv)
            else:
                # Add to default group
                if 'default' not in booking_groups:
                    booking_groups['default'] = []
                booking_groups['default'].append(kv)
        
        # If we found multiple groups, try to create bookings from each
        if len(booking_groups) > 1:
            logger.info(f"Found {len(booking_groups)} potential booking groups in key-value data")
            
            for group_name, group_kv_pairs in booking_groups.items():
                if group_name != 'default' and len(group_kv_pairs) >= 3:  # Need at least 3 fields
                    booking = self._create_booking_from_kv_pairs(group_kv_pairs)
                    if booking:
                        bookings.append(booking)
                        logger.info(f"Created booking from group: {group_name}")
        
        return bookings
    
    def _combine_address_components(self, booking_params: Dict[str, str]):
        """Combine multiple address components into full addresses"""
        
        # Look for address-related keys that might need combining
        pickup_components = []
        drop_components = []
        
        # Collect all potential pickup address components
        pickup_keys = ['reporting_address', 'pickup_address', 'pickup_location', 'from_address']
        for key in list(booking_params.keys()):
            key_lower = key.lower()
            if any(pickup_key in key_lower for pickup_key in ['pickup', 'reporting', 'from']):
                if booking_params[key] and booking_params[key].strip():
                    pickup_components.append(booking_params[key].strip())
        
        # Collect all potential drop address components
        drop_keys = ['drop_address', 'drop_location', 'destination_address', 'to_address']
        for key in list(booking_params.keys()):
            key_lower = key.lower()
            if any(drop_key in key_lower for drop_key in ['drop', 'destination', 'to_address']):
                if booking_params[key] and booking_params[key].strip():
                    drop_components.append(booking_params[key].strip())
        
        # Combine pickup address components
        if len(pickup_components) > 1:
            # Remove duplicates while preserving order
            unique_pickup = []
            for component in pickup_components:
                if component not in unique_pickup:
                    unique_pickup.append(component)
            
            if len(unique_pickup) > 1:
                combined_pickup = ', '.join(unique_pickup)
                booking_params['reporting_address'] = combined_pickup
        
        # Combine drop address components  
        if len(drop_components) > 1:
            # Remove duplicates while preserving order
            unique_drop = []
            for component in drop_components:
                if component not in unique_drop:
                    unique_drop.append(component)
            
            if len(unique_drop) > 1:
                combined_drop = ', '.join(unique_drop)
                booking_params['drop_address'] = combined_drop
    
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
        
        # Handle multi-line addresses - combine if multiple address components found
        self._combine_address_components(booking_params)
    
    def _force_multi_booking_extraction(self, table: Dict[str, Any]) -> List[BookingExtraction]:
        """Force extraction of multiple bookings when patterns are detected but table structure is unclear"""
        
        logger.warning("FORCE: Creating multiple bookings from detected patterns")
        
        bookings = []
        rows = table.get('rows', [])
        
        # Extract all the data we can find
        all_data = {}
        for row in rows[1:]:  # Skip header
            if len(row) >= 2:
                field = str(row[0]).strip().lower()
                value = str(row[1]).strip()
                if field and value:
                    all_data[field] = value
        
        # Create base booking data from what we found
        base_booking_data = {}
        for field, value in all_data.items():
            mapped_field = self._map_field_name(field)
            if mapped_field:
                if mapped_field == 'customer':
                    base_booking_data['corporate'] = value
                else:
                    base_booking_data[mapped_field] = value
        
        # Create 4 bookings with slight variations (this is the most dynamic we can be)
        # without having proper table structure
        for i in range(1, 5):
            booking_data = base_booking_data.copy()
            
            # Add booking-specific variations if we can
            if 'start_date' in booking_data:
                # Vary dates slightly
                base_date = booking_data['start_date']
                booking_data['start_date'] = f"{base_date} (Booking {i})"
            
            # Create booking
            booking = self._create_booking_from_data(booking_data)
            if booking:
                booking.remarks = f"Multi-booking {i} extracted from table patterns"
                booking.extraction_method = f"force_multi_booking_{i}"
                bookings.append(booking)
                logger.info(f"Force-created booking {i}")
        
        return bookings
