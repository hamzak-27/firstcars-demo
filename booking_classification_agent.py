"""
Booking Classification Agent
Determines whether content will result in single or multiple bookings using AI-based analysis
"""

import logging
import json
import os
import re
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime, timedelta

# Gemini AI imports
try:
    import google.generativeai as genai
    from gemini_model_utils import create_gemini_model
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

logger = logging.getLogger(__name__)

@dataclass
class ClassificationResult:
    """Result of booking classification analysis"""
    predicted_booking_count: int
    booking_type: str  # "single" or "multiple"
    confidence_score: float
    reasoning: str
    detected_patterns: List[str]
    duty_type_indicators: List[str]
    date_patterns: List[str]
    additional_info: str = ""

class BookingClassificationAgent:
    """AI-powered agent to classify content and predict booking count using Gemini"""
    
    def __init__(self, gemini_api_key: str = None):
        """Initialize with Gemini API key"""
        self.gemini_api_key = gemini_api_key or os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_AI_API_KEY')
        
        if not GEMINI_AVAILABLE:
            logger.warning("Gemini AI not available - install google-generativeai package")
            self.ai_available = False
            return
            
        if not self.gemini_api_key:
            logger.warning("No Gemini API key found - will use fallback pattern matching")
            self.ai_available = False
            return
            
        try:
            # Configure Gemini with safer model creation
            self.model, actual_model_name = create_gemini_model(self.gemini_api_key, 'models/gemini-2.5-flash')
            if self.model:
                self.ai_available = True
                logger.info(f"Gemini AI classification initialized successfully with {actual_model_name}")
            else:
                logger.error(f"Failed to create Gemini model: {actual_model_name}")
                self.ai_available = False
        except Exception as e:
            logger.error(f"Failed to initialize Gemini AI: {str(e)}")
            self.ai_available = False

    def classify_text_content(self, content: str) -> ClassificationResult:
        """Classify text content to predict booking count using AI"""
        if self.ai_available:
            return self._classify_with_ai(content)
        else:
            return self._classify_with_fallback(content)
    
    def _classify_with_ai(self, content: str) -> ClassificationResult:
        """AI-powered classification using Gemini with your business rules"""
        try:
            # Create the classification prompt with your specific business rules
            prompt = f"""
You are an expert car rental booking classifier. Analyze the following email/text content and determine if it requires SINGLE or MULTIPLE booking records.

BUSINESS RULES:

**SINGLE BOOKINGS:**
1. Client using a car for many days under 8/80 or outstation package (consecutive days)
2. Client only wants one drop (4/40) in a day
3. Multiple passengers traveling together (unless explicitly stated to create separate bookings)
4. Same car type for entire duration
5. Continuous multi-day travel
6. OUTSTATION ROUND TRIPS: Chennai→Bangalore→Chennai, Mumbai→Pune→Mumbai etc. (SINGLE booking)
7. One passenger requesting one continuous journey (even if multi-city or multi-day)

**MULTIPLE BOOKINGS:**
1. Client wants two or more drops in the same day
2. Client wants 8/80 but for alternate/non-consecutive days (one day, then skip a day, then another day, etc.)
3. Client wants 8/80 for a few days but car type is changing for different days
4. Explicitly mentioned separate bookings ("First car", "Second car", "arrange two cars", etc.)
5. Different passengers with different requirements
6. Table format with multiple rows of booking data

CONTENT TO ANALYZE:
{content}

ANALYZE AND RESPOND IN JSON FORMAT:
{{
    "predicted_booking_count": <number>,
    "booking_type": "single" or "multiple",
    "confidence_score": <0.0 to 1.0>,
    "reasoning": "Detailed explanation of your decision based on business rules",
    "detected_patterns": ["list of patterns you found"],
    "duty_type_indicators": ["8/80", "4/40", "outstation", etc.],
    "date_patterns": ["dates or date ranges found"],
    "additional_info": "Any other relevant observations"
}}

IMPORTANT CLARIFICATIONS:
1. Be very careful with structured content like "First car" and "Second car" or "arrange two cars" - these clearly indicate MULTIPLE bookings.
2. OUTSTATION ROUND TRIPS are SINGLE bookings: "Chennai to Bangalore to Chennai" = ONE continuous journey
3. Same passenger, same car type, continuous travel = SINGLE booking (even if multi-day or multi-city)
4. Only create MULTIPLE bookings if explicitly mentioned separate cars/bookings or different passengers
"""
            
            # Call Gemini API
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Parse the JSON response
            try:
                # Extract JSON from response (in case it's wrapped in markdown)
                if '```json' in response_text:
                    json_start = response_text.find('```json') + 7
                    json_end = response_text.find('```', json_start)
                    response_text = response_text[json_start:json_end].strip()
                elif '```' in response_text:
                    json_start = response_text.find('```') + 3
                    json_end = response_text.rfind('```')
                    response_text = response_text[json_start:json_end].strip()
                
                result_data = json.loads(response_text)
                
                return ClassificationResult(
                    predicted_booking_count=result_data.get('predicted_booking_count', 1),
                    booking_type=result_data.get('booking_type', 'single'),
                    confidence_score=result_data.get('confidence_score', 0.8),
                    reasoning=result_data.get('reasoning', 'AI classification completed'),
                    detected_patterns=result_data.get('detected_patterns', []),
                    duty_type_indicators=result_data.get('duty_type_indicators', []),
                    date_patterns=result_data.get('date_patterns', []),
                    additional_info=result_data.get('additional_info', 'AI-powered analysis')
                )
                
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse AI response as JSON: {e}")
                logger.warning(f"Raw response: {response_text}")
                
                # Try to extract basic information from text response
                if 'multiple' in response_text.lower():
                    booking_type = 'multiple'
                    # Try to extract number
                    import re
                    numbers = re.findall(r'(\d+)\s*booking', response_text.lower())
                    predicted_count = int(numbers[0]) if numbers else 2
                else:
                    booking_type = 'single'
                    predicted_count = 1
                
                return ClassificationResult(
                    predicted_booking_count=predicted_count,
                    booking_type=booking_type,
                    confidence_score=0.7,
                    reasoning=f"AI response parsing failed, extracted from text: {response_text[:200]}",
                    detected_patterns=[],
                    duty_type_indicators=[],
                    date_patterns=[],
                    additional_info="Fallback text parsing used"
                )
            
        except Exception as e:
            logger.error(f"AI classification failed: {str(e)}")
            return self._classify_with_fallback(content)
    
    def _classify_with_fallback(self, content: str) -> ClassificationResult:
        """Fallback classification using simple pattern matching"""
        try:
            content_lower = content.lower()
            
            # Simple but effective patterns for fallback
            multiple_indicators = [
                r'first\s*car|second\s*car|third\s*car',  # "First car", "Second car"
                r'arrange\s*(two|three|four|\d+)\s*(car|cab|vehicle)',  # "arrange two cars"
                r'need\s*(two|three|four|\d+)\s*(car|cab|vehicle)',     # "need two cars"
                r'book\s*(two|three|four|\d+)\s*(car|cab|vehicle)',     # "book two cars"
                r'cab\s*1|cab\s*2|booking\s*1|booking\s*2',  # "Cab 1", "Cab 2"
                r'contact\s*personnel.*contact\s*personnel',  # Multiple contact sections
                r'mobile\s*no.*mobile\s*no',  # Multiple mobile number sections
                r'multiple\s*drops|several\s*drops|two\s*drops',
                r'alternate\s*days|every\s*other\s*day',
                r'different\s*car.*different\s*day|car.*change.*day'
            ]
            
            matches_found = []
            for pattern in multiple_indicators:
                if re.search(pattern, content_lower):
                    matches_found.append(pattern)
            
            if matches_found:
                # Extract number if possible
                number_matches = re.findall(r'(two|three|four|five|\d+)\s*car', content_lower)
                if number_matches:
                    num_word = number_matches[0]
                    word_to_num = {'two': 2, 'three': 3, 'four': 4, 'five': 5}
                    predicted_count = word_to_num.get(num_word, int(num_word) if num_word.isdigit() else 2)
                else:
                    predicted_count = max(len(matches_found), 2)
                
                return ClassificationResult(
                    predicted_booking_count=predicted_count,
                    booking_type='multiple',
                    confidence_score=0.8,
                    reasoning=f"Found multiple booking indicators: {', '.join(matches_found)}",
                    detected_patterns=matches_found,
                    duty_type_indicators=[],
                    date_patterns=[],
                    additional_info="Fallback pattern matching used"
                )
            else:
                return ClassificationResult(
                    predicted_booking_count=1,
                    booking_type='single',
                    confidence_score=0.6,
                    reasoning="No multiple booking indicators found - defaulting to single",
                    detected_patterns=[],
                    duty_type_indicators=[],
                    date_patterns=[],
                    additional_info="Fallback classification - no AI available"
                )
                
        except Exception as e:
            logger.error(f"Fallback classification failed: {str(e)}")
            return ClassificationResult(
                predicted_booking_count=1,
                booking_type='single',
                confidence_score=0.3,
                reasoning=f"Classification error: {str(e)}",
                detected_patterns=[],
                duty_type_indicators=[],
                date_patterns=[],
                additional_info="Error occurred during classification"
            )

    def classify_from_table_data(self, table_rows: int, table_columns: int, table_content: str = "") -> ClassificationResult:
        """Classify based on table structure and content"""
        try:
            # If we have table data, use it for classification
            if table_rows > 1:
                # Each row typically represents a booking (excluding header)
                predicted_count = table_rows - 1  # Subtract header row
                
                # Also check table content for additional context
                content_result = self.classify_text_content(table_content) if table_content else None
                
                reasoning = f"Table with {table_rows} rows detected (excluding header = {predicted_count} bookings)"
                if content_result:
                    reasoning += f" | Content analysis: {content_result.reasoning}"
                
                return ClassificationResult(
                    predicted_booking_count=max(1, predicted_count),
                    booking_type="multiple" if predicted_count > 1 else "single",
                    confidence_score=0.9,  # High confidence for table-based classification
                    reasoning=reasoning,
                    detected_patterns=[f"Table structure: {table_rows}x{table_columns}"],
                    duty_type_indicators=content_result.duty_type_indicators if content_result else [],
                    date_patterns=content_result.date_patterns if content_result else [],
                    additional_info=f"Table-based classification with {table_rows} data rows"
                )
            
            # If no meaningful table structure, fall back to content analysis
            return self.classify_text_content(table_content)
            
        except Exception as e:
            logger.error(f"Error in table classification: {str(e)}")
            return ClassificationResult(
                predicted_booking_count=1,
                booking_type="single",
                confidence_score=0.3,
                reasoning=f"Table classification failed: {str(e)}",
                detected_patterns=[],
                duty_type_indicators=[],
                date_patterns=[]
            )

    def classify_from_extraction_result(self, extraction_result) -> ClassificationResult:
        """Classify based on actual extraction results"""
        try:
            if not extraction_result or not hasattr(extraction_result, 'bookings'):
                return ClassificationResult(
                    predicted_booking_count=0,
                    booking_type="none",
                    confidence_score=0.1,
                    reasoning="No extraction result available",
                    detected_patterns=[],
                    duty_type_indicators=[],
                    date_patterns=[]
                )
            
            actual_count = len(extraction_result.bookings)
            
            # Analyze the extracted bookings for patterns
            duty_types = []
            dates = []
            vehicles = []
            
            for booking in extraction_result.bookings:
                if booking.duty_type:
                    duty_types.append(booking.duty_type)
                if booking.start_date:
                    dates.append(booking.start_date)
                if booking.vehicle_group:
                    vehicles.append(booking.vehicle_group)
            
            # Determine classification based on actual data
            unique_duty_types = len(set(duty_types))
            unique_dates = len(set(dates))
            unique_vehicles = len(set(vehicles))
            
            reasoning_parts = []
            if actual_count > 1:
                reasoning_parts.append(f"Extracted {actual_count} bookings")
                if unique_duty_types > 1:
                    reasoning_parts.append(f"{unique_duty_types} different duty types")
                if unique_dates > 1:
                    reasoning_parts.append(f"{unique_dates} different dates")
                if unique_vehicles > 1:
                    reasoning_parts.append(f"{unique_vehicles} different vehicle types")
            
            return ClassificationResult(
                predicted_booking_count=actual_count,
                booking_type="multiple" if actual_count > 1 else "single",
                confidence_score=0.95,  # High confidence - based on actual extraction
                reasoning=" | ".join(reasoning_parts) if reasoning_parts else f"Single booking extracted",
                detected_patterns=[f"Actual extraction: {actual_count} bookings"],
                duty_type_indicators=duty_types,
                date_patterns=dates,
                additional_info=f"Vehicle types: {', '.join(set(vehicles)) if vehicles else 'None'}"
            )
            
        except Exception as e:
            logger.error(f"Error in extraction-based classification: {str(e)}")
            return ClassificationResult(
                predicted_booking_count=1,
                booking_type="single",
                confidence_score=0.3,
                reasoning=f"Extraction classification failed: {str(e)}",
                detected_patterns=[],
                duty_type_indicators=[],
                date_patterns=[]
            )