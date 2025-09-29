"""
Fallback Email Processor
Simple rule-based email processing when OpenAI/Gemini is not available
"""

import logging
import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from car_rental_ai_agent import BookingExtraction
from structured_email_agent import StructuredExtractionResult

logger = logging.getLogger(__name__)

class FallbackEmailProcessor:
    """Fallback processor that uses rule-based extraction"""
    
    def __init__(self, openai_api_key: str = None):
        """Initialize fallback processor (ignores API key)"""
        self.phone_pattern = re.compile(r'\b(?:\+91[-\s]?)?[6-9]\d{9}\b')
        self.email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
        self.date_patterns = [
            re.compile(r'\b(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})\b'),
            re.compile(r'\b(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[,\s]*(\d{2,4})\b', re.IGNORECASE),
        ]
        self.time_pattern = re.compile(r'\b(\d{1,2}):(\d{2})\s*(AM|PM|am|pm)?\b')
        logger.info("Fallback email processor initialized")
    
    def process_email(self, email_content: str, sender_email: str = None) -> StructuredExtractionResult:
        """Process email content using rule-based extraction"""
        
        # Create a basic booking extraction
        booking = BookingExtraction()
        
        # Extract basic information
        booking.passenger_name = self._extract_passenger_name(email_content)
        booking.passenger_phone = self._extract_phone(email_content)
        booking.passenger_email = self._extract_email(email_content) or sender_email
        booking.start_date = self._extract_date(email_content)
        booking.reporting_time = self._extract_time(email_content)
        booking.from_location = self._extract_location(email_content, 'from')
        booking.to_location = self._extract_location(email_content, 'to')
        booking.vehicle_group = self._extract_vehicle(email_content)
        booking.duty_type = self._extract_duty_type(email_content)
        booking.corporate = self._extract_corporate(email_content)
        booking.remarks = "Extracted from table format"
        booking.labels = "DISPOSAL-SERVICE, SEDAN, INDIVIDUAL"  # Default labels
        booking.additional_info = f"Processed by fallback processor from: {email_content[:100]}..."
        booking.confidence_score = 0.6  # Lower confidence for rule-based
        
        return StructuredExtractionResult(
            bookings=[booking],
            total_bookings_found=1,
            extraction_method="fallback_rule_based",
            confidence_score=0.6,
            processing_notes="Processed using rule-based fallback method"
        )
    
    def _extract_passenger_name(self, content: str) -> Optional[str]:
        """Extract passenger name using simple rules"""
        # Look for common patterns
        name_patterns = [
            r'passenger[:\s]+([A-Za-z\s]+)',
            r'name[:\s]+([A-Za-z\s]+)',
            r'mr\.?\s+([A-Za-z\s]+)',
            r'mrs\.?\s+([A-Za-z\s]+)',
            r'guest[:\s]+([A-Za-z\s]+)'
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                # Clean up the name (remove extra words)
                name_words = name.split()
                if len(name_words) <= 3:  # Reasonable name length
                    return ' '.join(name_words)
        
        return "Corporate Client"  # Default
    
    def _extract_phone(self, content: str) -> Optional[str]:
        """Extract phone number"""
        match = self.phone_pattern.search(content)
        if match:
            phone = re.sub(r'[^\d]', '', match.group())
            if len(phone) == 10:
                return phone
            elif len(phone) == 12 and phone.startswith('91'):
                return phone[2:]
        return None
    
    def _extract_email(self, content: str) -> Optional[str]:
        """Extract email address"""
        match = self.email_pattern.search(content)
        return match.group() if match else None
    
    def _extract_date(self, content: str) -> Optional[str]:
        """Extract date and convert to YYYY-MM-DD"""
        for pattern in self.date_patterns:
            match = pattern.search(content)
            if match:
                try:
                    if len(match.groups()) == 3:
                        day, month, year = match.groups()
                        if month.isdigit():
                            # DD/MM/YYYY format
                            year = int(year)
                            if year < 100:
                                year += 2000
                            return f"{year:04d}-{int(month):02d}-{int(day):02d}"
                        else:
                            # DD Month YYYY format
                            month_map = {
                                'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
                                'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
                            }
                            month_num = month_map.get(month[:3].lower(), 1)
                            year = int(year)
                            if year < 100:
                                year += 2000
                            return f"{year:04d}-{month_num:02d}-{int(day):02d}"
                except:
                    pass
        return None
    
    def _extract_time(self, content: str) -> Optional[str]:
        """Extract time and convert to HH:MM format"""
        match = self.time_pattern.search(content)
        if match:
            hour, minute = int(match.group(1)), int(match.group(2))
            am_pm = match.group(3)
            
            if am_pm and am_pm.lower() == 'pm' and hour != 12:
                hour += 12
            elif am_pm and am_pm.lower() == 'am' and hour == 12:
                hour = 0
                
            return f"{hour:02d}:{minute:02d}"
        return None
    
    def _extract_location(self, content: str, location_type: str) -> Optional[str]:
        """Extract location (from/to)"""
        if location_type == 'from':
            patterns = [
                r'from[:\s]+([A-Za-z\s,]+?)(?:to|$)',
                r'pickup[:\s]+([A-Za-z\s,]+?)(?:to|drop|$)',
                r'source[:\s]+([A-Za-z\s,]+?)(?:to|$)'
            ]
        else:  # to
            patterns = [
                r'to[:\s]+([A-Za-z\s,]+?)(?:$|\n)',
                r'drop[:\s]+([A-Za-z\s,]+?)(?:$|\n)',
                r'destination[:\s]+([A-Za-z\s,]+?)(?:$|\n)'
            ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                location = match.group(1).strip()
                # Clean up location
                location = re.sub(r'[,\n\r]+$', '', location).strip()
                if len(location) > 3 and len(location) < 100:
                    return location
        
        return None
    
    def _extract_vehicle(self, content: str) -> Optional[str]:
        """Extract vehicle type"""
        vehicle_patterns = [
            r'dzire', r'swift', r'innova', r'crysta', r'etios', r'sedan', r'suv'
        ]
        
        content_lower = content.lower()
        for vehicle in vehicle_patterns:
            if vehicle in content_lower:
                return vehicle.title()
        
        return "Dzire"  # Default
    
    def _extract_duty_type(self, content: str) -> Optional[str]:
        """Extract duty type and determine package"""
        content_lower = content.lower()
        
        # Check for drop/airport patterns
        if any(keyword in content_lower for keyword in ['drop', 'airport', 'transfer']):
            return "P-04HR 40KMS"  # Default to P2P drop
        
        # Check for outstation patterns  
        if any(keyword in content_lower for keyword in ['outstation', 'intercity']):
            return "P-Outstation 250KMS"  # Default to P2P outstation
        
        # Default to disposal/local
        return "P-08HR 80KMS"  # Default to P2P disposal
    
    def _extract_corporate(self, content: str) -> Optional[str]:
        """Extract corporate name"""
        # Look for common corporate keywords
        corporate_patterns = [
            r'corporate[:\s]+([A-Za-z\s&]+)',
            r'company[:\s]+([A-Za-z\s&]+)',
            r'(ltd|limited|pvt|private|corporation|corp|inc)',
        ]
        
        for pattern in corporate_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                corp = match.group(1).strip() if len(match.groups()) > 0 else match.group(0)
                if len(corp) > 2 and len(corp) < 50:
                    return corp
        
        return "Corporate Client"  # Default