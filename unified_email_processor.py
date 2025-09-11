"""
Unified Email Processor
Combines structured and unstructured email processing into a single interface
"""

import logging
from typing import List, Union
from structured_email_agent import StructuredEmailAgent, StructuredExtractionResult
from car_rental_ai_agent import BookingExtraction

logger = logging.getLogger(__name__)

class UnifiedEmailProcessor:
    """
    Unified processor that can handle both structured and unstructured emails
    Automatically detects email type and routes to appropriate agent
    """
    
    def __init__(self, openai_api_key: str = None):
        """Initialize unified processor"""
        self.structured_agent = StructuredEmailAgent(openai_api_key)
        logger.info("Unified email processor initialized")
    
    def process_email(self, email_content: str, sender_email: str = None) -> StructuredExtractionResult:
        """
        Process any email (structured or unstructured) and return unified results
        
        Args:
            email_content: Email content to process
            sender_email: Sender email (optional)
            
        Returns:
            StructuredExtractionResult containing all extracted bookings
        """
        return self.structured_agent.process_email_intelligently(email_content, sender_email)
    
    def process_email_as_structured(self, email_content: str, sender_email: str = None) -> StructuredExtractionResult:
        """Force processing as structured email (for table data)"""
        return self.structured_agent.extract_structured_bookings(email_content, sender_email)
    
    def process_email_as_unstructured(self, email_content: str, sender_email: str = None) -> StructuredExtractionResult:
        """Force processing as unstructured email"""
        booking = self.structured_agent.extract_booking_data(email_content, sender_email)
        
        return StructuredExtractionResult(
            bookings=[booking],
            total_bookings_found=1,
            extraction_method="forced_unstructured",
            confidence_score=booking.confidence_score or 0.5,
            processing_notes="Processed as unstructured email (forced mode)"
        )
    
    def get_processing_summary(self, result: StructuredExtractionResult) -> str:
        """Generate human-readable summary"""
        return self.structured_agent.get_processing_summary(result)
    
    def get_bookings_for_sheets(self, result: StructuredExtractionResult) -> List[List[str]]:
        """
        Convert extraction result to format suitable for Google Sheets
        
        Returns:
            List of rows (each booking as a list of strings)
        """
        rows = []
        for booking in result.bookings:
            rows.append(booking.to_sheets_row())
        return rows
    
    def detect_email_type(self, email_content: str) -> str:
        """Detect if email is structured or unstructured"""
        return self.structured_agent.detect_email_type(email_content)
    
    def validate_results(self, result: StructuredExtractionResult) -> dict:
        """
        Validate extraction results and provide quality metrics
        
        Returns:
            Dictionary with validation information
        """
        validation_info = {
            'total_bookings': result.total_bookings_found,
            'valid_bookings': 0,
            'invalid_bookings': 0,
            'missing_critical_fields': [],
            'overall_quality_score': 0.0,
            'warnings': []
        }
        
        if not result.bookings:
            validation_info['warnings'].append("No bookings extracted")
            return validation_info
        
        quality_scores = []
        
        for i, booking in enumerate(result.bookings, 1):
            # Check critical fields for each booking
            missing_fields = booking.get_missing_critical_fields()
            
            if missing_fields:
                validation_info['invalid_bookings'] += 1
                validation_info['missing_critical_fields'].append({
                    'booking_number': i,
                    'missing_fields': missing_fields
                })
            else:
                validation_info['valid_bookings'] += 1
            
            # Calculate quality score for this booking
            booking_dict = booking.to_dict()
            filled_fields = sum(1 for value in booking_dict.values() 
                              if value is not None and str(value).strip() != "")
            total_fields = len(booking_dict)
            booking_quality = filled_fields / total_fields
            quality_scores.append(booking_quality)
        
        # Overall quality score
        validation_info['overall_quality_score'] = sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
        
        # Add warnings
        if validation_info['invalid_bookings'] > 0:
            validation_info['warnings'].append(f"{validation_info['invalid_bookings']} booking(s) missing critical fields")
        
        if validation_info['overall_quality_score'] < 0.5:
            validation_info['warnings'].append("Low data quality - many fields missing")
        
        return validation_info
