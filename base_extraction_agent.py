#!/usr/bin/env python3
"""
Base Extraction Agent for Car Rental Bookings
Shared functionality for single and multiple booking extraction agents
"""

import os
import json
import time
import logging
import pandas as pd
import re
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from abc import ABC, abstractmethod

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class BookingData:
    """Standardized booking data structure"""
    customer: str = ""
    booked_by_name: str = ""
    booked_by_phone: str = ""
    booked_by_email: str = ""
    passenger_name: str = ""
    passenger_phone: str = ""
    passenger_email: str = ""
    from_location: str = ""
    to_location: str = ""
    vehicle_group: str = ""
    duty_type: str = ""
    start_date: str = ""
    end_date: str = ""
    reporting_time: str = ""
    reporting_address: str = ""
    drop_address: str = ""
    flight_train_number: str = ""
    dispatch_center: str = ""
    remarks: str = ""
    labels: str = ""
    
    # Metadata
    confidence_score: float = 0.8
    extraction_method: str = ""

@dataclass
class ExtractionResult:
    """Result from extraction agent"""
    success: bool
    bookings_dataframe: pd.DataFrame
    booking_count: int
    confidence_score: float
    processing_time: float
    cost_inr: float
    extraction_method: str
    error_message: str = ""
    metadata: Dict[str, Any] = None

try:
    from openai_model_utils import create_openai_client, create_chat_messages
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI utilities not available. Install with: pip install openai")

class BaseExtractionAgent(ABC):
    """
    Base class for booking extraction agents
    Provides shared functionality for OpenAI API integration and DataFrame operations
    """
    
    def __init__(self, api_key: str = None, model_name: str = "gpt-4o-mini"):
        """Initialize base extraction agent"""
        
        if not OPENAI_AVAILABLE:
            logger.warning("OpenAI not available, will use fallback extraction")
        
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        self.model_name = model_name
        
        # Configure OpenAI client
        if OPENAI_AVAILABLE and self.api_key and self.api_key != "test-key":
            try:
                self.client = create_openai_client(self.api_key)
                if self.client:
                    logger.info(f"Successfully configured OpenAI client with model: {self.model_name}")
                else:
                    logger.error(f"Failed to create OpenAI client")
                    self.client = None
            except Exception as e:
                logger.error(f"Error creating OpenAI client: {e}")
                self.client = None
        else:
            self.client = None
            if not self.api_key:
                logger.info("No OpenAI API key found - will use fallback extraction")
            else:
                logger.info("Test mode - will use fallback extraction")
        
        # Cost tracking (OpenAI GPT-4o-mini rates in INR)
        self.cost_per_1k_input_tokens = 0.0125  # ₹0.0125 per 1K input tokens
        self.cost_per_1k_output_tokens = 0.05   # ₹0.05 per 1K output tokens
        self.total_cost = 0.0
        self.request_count = 0
        
        # Standard DataFrame columns (19 fields as specified)
        self.standard_columns = [
            'Customer',
            'Booked By Name', 
            'Booked By Phone Number',
            'Booked By Email',
            'Passenger Name',
            'Passenger Phone Number', 
            'Passenger Email',
            'From (Service Location)',
            'To',
            'Vehicle Group',
            'Duty Type',
            'Start Date',
            'End Date', 
            'Rep. Time',
            'Reporting Address',
            'Drop Address',
            'Flight/Train Number',
            'Dispatch center',
            'Remarks',
            'Labels'
        ]
        
        logger.info(f"BaseExtractionAgent initialized with model: {model_name}")
    
    def _estimate_tokens(self, text: str) -> int:
        """Rough token estimation"""
        return len(text) // 4
    
    def _track_cost(self, input_text: str, output_text: str) -> float:
        """Track and return API usage cost in INR (fallback method)"""
        input_tokens = self._estimate_tokens(input_text)
        output_tokens = self._estimate_tokens(output_text)
        
        cost_inr = (
            (input_tokens / 1000) * self.cost_per_1k_input_tokens +
            (output_tokens / 1000) * self.cost_per_1k_output_tokens
        )
        
        self.total_cost += cost_inr
        self.request_count += 1
        
        logger.debug(f"Request cost: ₹{cost_inr:.4f}")
        return cost_inr
    
    def _track_cost_with_tokens(self, input_tokens: int, output_tokens: int) -> float:
        """Track API usage cost with actual token counts from OpenAI"""
        
        cost_inr = (
            (input_tokens / 1000) * self.cost_per_1k_input_tokens +
            (output_tokens / 1000) * self.cost_per_1k_output_tokens
        )
        
        self.total_cost += cost_inr
        self.request_count += 1
        
        logger.debug(f"Cost tracking: {input_tokens} input + {output_tokens} output tokens = ₹{cost_inr:.4f}")
        
        return cost_inr
    
    def _generate_openai_response(self, prompt: str) -> Tuple[str, float]:
        """Generate response using OpenAI API"""
        if not self.client:
            raise ValueError("OpenAI client not available")
        
        try:
            # Create messages
            messages = create_chat_messages(prompt)
            
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=0.1,
                max_tokens=2000,
                top_p=0.8
            )
            
            if not response or not response.choices or len(response.choices) == 0:
                raise ValueError("Empty response from OpenAI")
            
            output_text = response.choices[0].message.content.strip()
            
            # Calculate cost using actual token usage
            input_tokens = response.usage.prompt_tokens
            output_tokens = response.usage.completion_tokens
            cost = self._track_cost_with_tokens(input_tokens, output_tokens)
            
            return output_text, cost
            
        except Exception as e:
            logger.error(f"OpenAI API call failed: {str(e)}")
            raise
    
    def _parse_json_response(self, response_text: str) -> Dict[str, Any]:
        """Parse JSON response from OpenAI"""
        try:
            # Clean response text
            response_text = response_text.strip()
            if response_text.startswith('```json'):
                response_text = response_text.replace('```json', '').replace('```', '').strip()
            
            # Find JSON boundaries
            start = response_text.find('{')
            if start == -1:
                start = response_text.find('[')
            
            if start == -1:
                raise ValueError("No JSON found in response")
            
            # For arrays, find the end bracket
            if response_text[start] == '[':
                end = response_text.rfind(']') + 1
            else:
                end = response_text.rfind('}') + 1
            
            if end <= start:
                raise ValueError("Invalid JSON boundaries")
            
            json_str = response_text[start:end]
            return json.loads(json_str)
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing failed: {str(e)}")
            logger.error(f"Response was: {response_text[:500]}...")
            raise ValueError(f"Invalid JSON in response: {str(e)}")
    
    def _normalize_phone_number(self, phone: str) -> str:
        """Normalize phone number to 10 digits"""
        if not phone:
            return ""
        
        # Extract digits only
        digits = re.sub(r'\D', '', phone)
        
        # Handle Indian numbers (remove country code if present)
        if len(digits) == 12 and digits.startswith('91'):
            digits = digits[2:]
        elif len(digits) == 13 and digits.startswith('091'):
            digits = digits[3:]
        
        # Return 10-digit number or original if not valid
        return digits if len(digits) == 10 else phone
    
    def _normalize_date(self, date_str: str) -> str:
        """Normalize date to YYYY-MM-DD format"""
        if not date_str:
            return ""
        
        # This is a simplified version - you might want to enhance this
        # with more robust date parsing
        date_str = date_str.strip()
        
        # If already in YYYY-MM-DD format, return as is
        if re.match(r'\d{4}-\d{2}-\d{2}', date_str):
            return date_str
        
        # Handle DD-MM-YYYY or DD/MM/YYYY
        if re.match(r'\d{2}[-/]\d{2}[-/]\d{4}', date_str):
            parts = re.split(r'[-/]', date_str)
            return f"{parts[2]}-{parts[1]}-{parts[0]}"
        
        # Return original if can't parse
        return date_str
    
    def _normalize_time(self, time_str: str) -> str:
        """Normalize time to HH:MM format"""
        if not time_str:
            return ""
        
        # Extract time pattern
        time_match = re.search(r'(\d{1,2}):?(\d{2})?\s*(AM|PM|am|pm)?', time_str)
        if time_match:
            hour = int(time_match.group(1))
            minute = int(time_match.group(2)) if time_match.group(2) else 0
            period = time_match.group(3)
            
            if period and period.upper() == 'PM' and hour != 12:
                hour += 12
            elif period and period.upper() == 'AM' and hour == 12:
                hour = 0
            
            return f"{hour:02d}:{minute:02d}"
        
        return time_str
    
    def _create_dataframe_from_bookings(self, bookings: List[BookingData]) -> pd.DataFrame:
        """Create standardized DataFrame from booking data"""
        if not bookings:
            # Return empty DataFrame with correct columns
            return pd.DataFrame(columns=self.standard_columns)
        
        data = []
        for booking in bookings:
            row = {
                'Customer': booking.customer or '',
                'Booked By Name': booking.booked_by_name or '',
                'Booked By Phone Number': booking.booked_by_phone or '',
                'Booked By Email': booking.booked_by_email or '',
                'Passenger Name': booking.passenger_name or '',
                'Passenger Phone Number': booking.passenger_phone or '',
                'Passenger Email': booking.passenger_email or '',
                'From (Service Location)': booking.from_location or '',
                'To': booking.to_location or '',
                'Vehicle Group': booking.vehicle_group or '',
                'Duty Type': booking.duty_type or '',  # Will be filled by validation agent
                'Start Date': booking.start_date or '',
                'End Date': booking.end_date or '',
                'Rep. Time': booking.reporting_time or '',
                'Reporting Address': booking.reporting_address or '',
                'Drop Address': booking.drop_address or '',
                'Flight/Train Number': booking.flight_train_number or '',
                'Dispatch center': booking.dispatch_center or '',
                'Remarks': booking.remarks or '',
                'Labels': booking.labels or ''
            }
            data.append(row)
        
        return pd.DataFrame(data, columns=self.standard_columns)
    
    def _create_booking_from_dict(self, booking_dict: Dict[str, Any]) -> BookingData:
        """Create BookingData from dictionary with field normalization"""
        
        # Normalize fields
        phone = self._normalize_phone_number(booking_dict.get('passenger_phone', ''))
        booked_by_phone = self._normalize_phone_number(booking_dict.get('booked_by_phone', ''))
        start_date = self._normalize_date(booking_dict.get('start_date', ''))
        end_date = self._normalize_date(booking_dict.get('end_date', ''))
        reporting_time = self._normalize_time(booking_dict.get('reporting_time', ''))
        
        # Normalize and validate addresses
        reporting_address = self._normalize_address(booking_dict.get('reporting_address', ''))
        drop_address = self._normalize_address(booking_dict.get('drop_address', ''))
        
        return BookingData(
            customer=booking_dict.get('customer', ''),
            booked_by_name=booking_dict.get('booked_by_name', ''),
            booked_by_phone=booked_by_phone,
            booked_by_email=booking_dict.get('booked_by_email', ''),
            passenger_name=booking_dict.get('passenger_name', ''),
            passenger_phone=phone,
            passenger_email=booking_dict.get('passenger_email', ''),
            from_location=booking_dict.get('from_location', ''),
            to_location=booking_dict.get('to_location', ''),
            vehicle_group=booking_dict.get('vehicle_group', ''),
            duty_type=booking_dict.get('duty_type', ''),
            start_date=start_date,
            end_date=end_date,
            reporting_time=reporting_time,
            reporting_address=reporting_address,
            drop_address=drop_address,
            flight_train_number=booking_dict.get('flight_train_number', ''),
            dispatch_center=booking_dict.get('dispatch_center', ''),
            remarks=booking_dict.get('remarks', ''),
            labels=booking_dict.get('labels', ''),
            confidence_score=booking_dict.get('confidence_score', 0.8),
            extraction_method=booking_dict.get('extraction_method', 'openai_extraction')
        )
    
    def _normalize_address(self, address: str) -> str:
        """Normalize and validate address format"""
        if not address or not isinstance(address, str):
            return ""
        
        address = address.strip()
        if not address:
            return ""
        
        # Remove excessive whitespace and normalize line breaks
        address = re.sub(r'\s+', ' ', address)
        address = re.sub(r'[\r\n]+', ', ', address)
        
        # Remove duplicate commas and clean up
        address = re.sub(r',\s*,+', ',', address)
        address = re.sub(r'^,\s*|\s*,$', '', address)
        
        # Capitalize first letter of each word for consistency
        words = address.split()
        normalized_words = []
        for word in words:
            if word.lower() in ['and', 'or', 'of', 'at', 'to', 'from', 'in', 'on', 'the']:
                normalized_words.append(word.lower())
            elif word.endswith(','):
                normalized_words.append(word[:-1].title() + ',')
            else:
                normalized_words.append(word.title())
        
        return ' '.join(normalized_words)
    
    @abstractmethod
    def extract(self, content: str, classification_result: Any) -> ExtractionResult:
        """Extract booking data from content - to be implemented by subclasses"""
        pass
    
    @abstractmethod
    def _build_extraction_prompt(self, content: str, classification_result: Any) -> str:
        """Build extraction prompt - to be implemented by subclasses"""
        pass
    
    def get_cost_summary(self) -> Dict[str, Any]:
        """Get cost summary for this agent"""
        avg_cost = self.total_cost / max(1, self.request_count)
        return {
            'model': self.model_name,
            'total_requests': self.request_count,
            'total_cost_inr': round(self.total_cost, 4),
            'avg_cost_per_request': round(avg_cost, 4),
            'estimated_monthly_cost_5k': round(avg_cost * 5000, 2)
        }