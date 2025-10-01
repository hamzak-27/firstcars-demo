#!/usr/bin/env python3
"""
Form Extraction Utilities for Structured Documents
Handles form/table-based documents that contain field-value pairs
"""

import logging
import re
from typing import Dict, List, Tuple, Optional
import pandas as pd

logger = logging.getLogger(__name__)

class FormExtractionUtils:
    """Utilities for extracting data from form/table structured documents"""
    
    def __init__(self):
        """Initialize form extraction utilities"""
        self.form_field_mappings = {
            # Company/Corporate Information
            'company name': 'Customer',
            'company': 'Customer',
            'corporate': 'Customer',
            
            # Booker Information  
            'name & contact number of booker': 'Booked By Name',
            'booker name': 'Booked By Name',
            'booked by': 'Booked By Name',
            'email id of booker': 'Booked By Email',
            'booker email': 'Booked By Email',
            
            # Passenger Information
            'name of the user': 'Passenger Name',
            'passenger name': 'Passenger Name',
            'user name': 'Passenger Name',
            'mobile no. of the user': 'Passenger Phone Number',
            'user mobile': 'Passenger Phone Number', 
            'passenger phone': 'Passenger Phone Number',
            'email id of user': 'Passenger Email',
            'user email': 'Passenger Email',
            'passenger email': 'Passenger Email',
            
            # Location Information
            'city in which car is required': 'From (Service Location)',
            'pickup city': 'From (Service Location)',
            'service city': 'From (Service Location)',
            'reporting': 'Reporting Address',
            'reporting address': 'Reporting Address',
            'pickup address': 'Reporting Address',
            
            # Vehicle Information
            'car type': 'Vehicle Group',
            'vehicle type': 'Vehicle Group', 
            '1car type (indigo/dzire/fiesta)': 'Vehicle Group',
            'vehicle': 'Vehicle Group',
            
            # Date and Time
            'date of requirement': 'Start Date',
            'service date': 'Start Date',
            'from date & to date': 'Start Date',
            'reporting time': 'Rep. Time',
            'pickup time': 'Rep. Time',
            'time': 'Rep. Time',
            
            # Service Type
            'type of duty': 'Duty Type',
            'service type': 'Duty Type',
            'duty type': 'Duty Type',
            'only drop / local full day': 'Duty Type'
        }
    
    def detect_form_structure(self, content: str) -> bool:
        """Detect if content is a form/table structure"""
        
        content_lower = content.lower()
        
        # Form indicators
        form_indicators = [
            'company name',
            'name of the user',
            'email id of booker', 
            'city in which car is required',
            'reporting time',
            'type of duty'
        ]
        
        # Count how many form indicators are present
        indicator_count = sum(1 for indicator in form_indicators if indicator in content_lower)
        
        # If 3 or more indicators, likely a form
        return indicator_count >= 3
    
    def extract_form_data(self, content: str) -> Dict[str, str]:
        """Extract field-value pairs from form content"""
        
        extracted_data = {}
        
        # Split content into lines for processing
        lines = content.split('\n')
        
        # Try to find field-value patterns
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
                
            line_lower = line.lower()
            
            # Check if this line contains a known form field
            for form_field, column_name in self.form_field_mappings.items():
                if form_field in line_lower:
                    # Found a field, now find the value
                    value = self._extract_field_value(line, lines, i, form_field)
                    if value:
                        extracted_data[column_name] = value
                    break
        
        logger.info(f"Extracted {len(extracted_data)} form fields")
        return extracted_data
    
    def _extract_field_value(self, current_line: str, all_lines: List[str], 
                           line_index: int, field_name: str) -> Optional[str]:
        """Extract value for a specific form field"""
        
        current_lower = current_line.lower()
        
        # Method 1: Check for inline values (field | value format)
        if '|' in current_line:
            parts = current_line.split('|')
            if len(parts) >= 2:
                field_part = parts[0].strip().lower()
                value_part = parts[1].strip()
                
                if field_name in field_part and value_part:
                    return self._clean_field_value(value_part)
        
        # Method 2: Check for colon-separated values
        if ':' in current_line:
            parts = current_line.split(':')
            if len(parts) >= 2:
                field_part = parts[0].strip().lower()
                value_part = ':'.join(parts[1:]).strip()
                
                if field_name in field_part and value_part:
                    return self._clean_field_value(value_part)
        
        # Method 3: Look for value in next line
        if line_index + 1 < len(all_lines):
            next_line = all_lines[line_index + 1].strip()
            if next_line and not self._is_field_label(next_line):
                return self._clean_field_value(next_line)
        
        # Method 4: Look for value after the field in same line
        field_end_pos = current_lower.find(field_name) + len(field_name)
        remaining_text = current_line[field_end_pos:].strip()
        
        # Remove common separators
        for sep in [':', '|', '-', '=']:
            if remaining_text.startswith(sep):
                remaining_text = remaining_text[1:].strip()
        
        if remaining_text:
            return self._clean_field_value(remaining_text)
        
        return None
    
    def _clean_field_value(self, value: str) -> str:
        """Clean and format field value"""
        
        if not value:
            return ""
        
        # Basic cleaning
        value = value.strip()
        
        # Remove table formatting artifacts
        value = re.sub(r'[|]{2,}', '', value)  # Multiple pipes
        value = re.sub(r'^[|]+|[|]+$', '', value)  # Leading/trailing pipes
        
        # Clean up whitespace
        value = ' '.join(value.split())
        
        return value if value else ""
    
    def _is_field_label(self, text: str) -> bool:
        """Check if text looks like a field label"""
        
        text_lower = text.lower()
        
        # Check against known field names
        for field_name in self.form_field_mappings.keys():
            if field_name in text_lower:
                return True
        
        # Check for common field patterns
        field_patterns = [
            r'name.*:',
            r'email.*:',
            r'phone.*:',
            r'address.*:',
            r'time.*:',
            r'date.*:',
            r'type.*:'
        ]
        
        return any(re.search(pattern, text_lower) for pattern in field_patterns)
    
    def convert_to_dataframe(self, extracted_data: Dict[str, str]) -> pd.DataFrame:
        """Convert extracted form data to standard DataFrame format"""
        
        # Standard column names for car rental booking
        standard_columns = [
            'Customer', 'Booked By Name', 'Booked By Phone Number', 'Booked By Email',
            'Passenger Name', 'Passenger Phone Number', 'Passenger Email',
            'From (Service Location)', 'To', 'Vehicle Group', 'Duty Type',
            'Start Date', 'End Date', 'Rep. Time', 'Reporting Address', 'Drop Address',
            'Flight/Train Number', 'Dispatch center', 'Remarks', 'Labels'
        ]
        
        # Initialize with empty values
        row_data = {col: '' for col in standard_columns}
        
        # Fill with extracted data
        for col_name, value in extracted_data.items():
            if col_name in row_data:
                row_data[col_name] = value
        
        # Apply some basic post-processing
        row_data = self._post_process_form_data(row_data)
        
        # Create DataFrame with single row
        df = pd.DataFrame([row_data])
        
        logger.info(f"Created DataFrame with form data: {len([v for v in row_data.values() if v])} non-empty fields")
        return df
    
    def _post_process_form_data(self, data: Dict[str, str]) -> Dict[str, str]:
        """Post-process extracted form data"""
        
        # If no 'To' location specified, use same as 'From' (local service)
        if not data.get('To') and data.get('From (Service Location)'):
            data['To'] = data['From (Service Location)']
        
        # Set end date same as start date if not specified
        if not data.get('End Date') and data.get('Start Date'):
            data['End Date'] = data['Start Date']
        
        # Clean phone numbers
        for phone_field in ['Booked By Phone Number', 'Passenger Phone Number']:
            if data.get(phone_field):
                data[phone_field] = self._clean_phone_number(data[phone_field])
        
        # Handle vehicle type mapping
        if data.get('Vehicle Group'):
            vehicle = data['Vehicle Group'].lower()
            if 'dzire' in vehicle:
                data['Vehicle Group'] = 'Dzire'
            elif 'innova' in vehicle or 'crysta' in vehicle:
                data['Vehicle Group'] = 'Toyota Innova Crysta'
            elif 'indigo' in vehicle:
                data['Vehicle Group'] = 'Tata Indigo'
            elif 'fiesta' in vehicle:
                data['Vehicle Group'] = 'Ford Fiesta'
        
        # Format time
        if data.get('Rep. Time'):
            data['Rep. Time'] = self._format_time(data['Rep. Time'])
        
        return data
    
    def _clean_phone_number(self, phone: str) -> str:
        """Clean phone number to 10 digits"""
        
        if not phone:
            return ""
        
        # Extract digits only
        digits = re.sub(r'[^\d]', '', phone)
        
        # Remove country code if present
        if len(digits) == 12 and digits.startswith('91'):
            digits = digits[2:]
        elif len(digits) == 13 and digits.startswith('091'):
            digits = digits[3:]
        
        # Return 10 digit number or original if not valid
        return digits if len(digits) == 10 else phone
    
    def _format_time(self, time_str: str) -> str:
        """Format time to HH:MM format"""
        
        if not time_str:
            return ""
        
        time_str = time_str.strip().upper()
        
        # Handle AM/PM format
        if 'AM' in time_str or 'PM' in time_str:
            # Extract time part
            time_part = re.sub(r'\s*(AM|PM)\s*', '', time_str).strip()
            
            # Parse hour and minute
            if ':' in time_part:
                try:
                    hour, minute = time_part.split(':')
                    hour = int(hour)
                    minute = int(minute)
                    
                    # Convert to 24-hour format
                    if 'PM' in time_str and hour != 12:
                        hour += 12
                    elif 'AM' in time_str and hour == 12:
                        hour = 0
                    
                    return f"{hour:02d}:{minute:02d}"
                except:
                    pass
        
        # Return original if can't parse
        return time_str


def test_form_extraction():
    """Test form extraction with sample data"""
    
    print("🧪 Testing Form Extraction Utils...")
    
    # Sample form content (simulating the Medtronic form)
    sample_content = """
    Company Name | India Medtronic Pvt. Ltd.
    Is the booking for IMPL employee or SPR (Doctor) | IMPL Employee
    Name & Contact Number of booker | Hiba Mohammed
    Email ID of booker | hiba.mohammed@medtronic.com
    City in which car is required | Chengannur
    Name of the User | Hiba Mohammed
    Mobile No. of the User | 8281011554, 9319154943
    Email ID of user | hiba.mohammed@medtronic.com
    Date of Requirement – From date & To date for multi day | 01-10-25, 11:00 AM
    1Car Type (Indigo/Dzire/Fiesta) | Dzire
    Reporting | H.No 33/432B Thattekadu Rd Near Villa Exotica Bavasons Homes, Maradu Nettoor, kochi 682040
    Reporting Time | 01-10-25, 11:00 AM
    Type of duty (Only Drop / Local full day | chengannur
    """
    
    # Initialize form extractor
    extractor = FormExtractionUtils()
    
    # Test detection
    is_form = extractor.detect_form_structure(sample_content)
    print(f"✅ Form detected: {is_form}")
    
    # Test extraction
    extracted_data = extractor.extract_form_data(sample_content)
    print(f"📊 Extracted {len(extracted_data)} fields:")
    for field, value in extracted_data.items():
        print(f"  {field}: {value}")
    
    # Test DataFrame conversion
    df = extractor.convert_to_dataframe(extracted_data)
    print(f"\n📋 Generated DataFrame:")
    print(f"Shape: {df.shape}")
    print("\nNon-empty fields:")
    for col in df.columns:
        value = df.iloc[0][col]
        if value:
            print(f"  {col}: {value}")


if __name__ == "__main__":
    test_form_extraction()