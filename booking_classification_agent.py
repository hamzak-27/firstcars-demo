"""
Booking Classification Agent
Determines whether content will result in single or multiple bookings based on business rules
"""

import logging
import re
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime, timedelta

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
    """Agent to classify content and predict booking count"""
    
    def __init__(self):
        # Duty type patterns
        self.duty_type_patterns = {
            '8/80': r'8[/\-\\]80|8\s*hrs?[/\-\\]80\s*km|8\s*hour[s]?[/\-\\]80|outstation',
            '4/40': r'4[/\-\\]40|4\s*hrs?[/\-\\]40\s*km|4\s*hour[s]?[/\-\\]40|drop',
            'outstation': r'outstation|out\s*station|long\s*distance|multi[_\-\s]?day',
            'drop': r'\bdrop\b|one\s*way|single\s*trip|airport\s*drop|station\s*drop'
        }
        
        # Multiple booking indicators
        self.multiple_booking_patterns = [
            r'cab\s*[1-9]|booking\s*[1-9]|trip\s*[1-9]',  # Cab 1, Cab 2, etc.
            r'first\s*trip|second\s*trip|next\s*trip',
            r'morning\s*trip|evening\s*trip|afternoon\s*trip',
            r'multiple\s*drops|several\s*drops|many\s*drops',
            r'two\s*trips|three\s*trips|four\s*trips',
            r'different\s*times|various\s*times|separate\s*times',
            r'and\s*then|followed\s*by|after\s*that',
            r'alternate\s*days|every\s*other\s*day|non[-\s]?consecutive'
        ]
        
        # Single booking indicators
        self.single_booking_patterns = [
            r'continuous\s*days|consecutive\s*days|back\s*to\s*back',
            r'same\s*car|same\s*vehicle|same\s*type',
            r'entire\s*duration|whole\s*period|complete\s*stay',
            r'multi[-\s]?day\s*package|outstation\s*package'
        ]
        
        # Date range patterns
        self.date_patterns = [
            r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}',  # Date formats
            r'[a-zA-Z]{3,9}\s+\d{1,2}',  # Month Day
            r'tomorrow|next\s*\w+|this\s*\w+',  # Relative dates
            r'from\s*\d+|to\s*\d+|until\s*\d+'  # Date ranges
        ]
        
        # Car type change indicators
        self.car_change_patterns = [
            r'different\s*car|change\s*car|switch\s*to',
            r'crysta.*dzire|dzire.*crysta|innova.*dzire|crysta.*innova|innova.*crysta',
            r'sedan.*suv|suv.*sedan|hatchback.*sedan',
            r'\b(crysta|dzire|innova|sedan|suv|hatchback)\b.*\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b.*\b(crysta|dzire|innova|sedan|suv|hatchback)\b',
            r'\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b.*\b(crysta|dzire|innova|sedan|suv|hatchback)\b.*\b(crysta|dzire|innova|sedan|suv|hatchback)\b'
        ]

    def classify_text_content(self, content: str) -> ClassificationResult:
        """Classify text content to predict booking count"""
        try:
            content_lower = content.lower()
            detected_patterns = []
            reasoning_parts = []
            duty_type_indicators = []
            date_patterns = []
            
            # Detect duty types
            detected_duty_types = []
            for duty_type, pattern in self.duty_type_patterns.items():
                matches = re.findall(pattern, content_lower)
                if matches:
                    detected_duty_types.append(duty_type)
                    duty_type_indicators.extend(matches)
            
            # Detect date patterns
            for pattern in self.date_patterns:
                matches = re.findall(pattern, content_lower)
                if matches:
                    date_patterns.extend(matches)
            
            # Count potential date ranges
            date_count = len(set(date_patterns))
            
            # Check for multiple booking indicators
            multiple_indicators = 0
            for pattern in self.multiple_booking_patterns:
                if re.search(pattern, content_lower):
                    multiple_indicators += 1
                    detected_patterns.append(f"Multiple indicator: {pattern}")
            
            # Check for single booking indicators
            single_indicators = 0
            for pattern in self.single_booking_patterns:
                if re.search(pattern, content_lower):
                    single_indicators += 1
                    detected_patterns.append(f"Single indicator: {pattern}")
            
            # Check for car type changes
            car_changes = 0
            for pattern in self.car_change_patterns:
                if re.search(pattern, content_lower):
                    car_changes += 1
                    detected_patterns.append(f"Car change indicator: {pattern}")
            
            # Apply business logic
            predicted_count = 1  # Default to single
            confidence = 0.5
            booking_type = "single"
            
            # Rule 1: Multiple drops in same day
            if (multiple_indicators >= 2 or 
                re.search(r'multiple\s*drops|several\s*drops|two\s*drops|three\s*drops|\d+\s*drops', content_lower) or
                re.search(r'\d+\s*(trips|bookings|cabs).*today|today.*\d+\s*(trips|bookings|cabs)', content_lower) or
                re.search(r'one.*at.*another.*at|first.*then|morning.*evening', content_lower)):
                
                # Try to extract number from text
                number_matches = re.findall(r'(\d+)\s*drops', content_lower)
                if number_matches:
                    predicted_count = max(int(number_matches[0]), 2)
                elif re.search(r'two\s*(drops|trips)', content_lower):
                    predicted_count = 2
                elif re.search(r'three\s*(drops|trips)', content_lower):
                    predicted_count = 3
                elif re.search(r'four\s*(drops|trips)', content_lower):
                    predicted_count = 4
                else:
                    predicted_count = max(multiple_indicators + 1, 2)
                
                booking_type = "multiple"
                confidence = 0.85
                reasoning_parts.append("Detected multiple drops in same day")
            
            # Rule 2: 8/80 for alternate days
            elif '8/80' in detected_duty_types and re.search(r'alternate|every\s*other|non[-\s]?consecutive', content_lower):
                predicted_count = max(2, date_count)
                booking_type = "multiple"
                confidence = 0.9
                reasoning_parts.append("8/80 duty type with alternate days pattern")
            
            # Rule 3: Car type changes
            elif car_changes > 0:
                # If car changes detected, it's likely multiple bookings
                # Try to count the number of different days/dates mentioned
                day_patterns = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
                days_found = [day for day in day_patterns if day in content_lower]
                
                if len(days_found) >= 2:
                    predicted_count = len(days_found)
                elif date_count > 1:
                    predicted_count = date_count
                else:
                    predicted_count = 2  # Assume at least 2 if car changes detected
                
                booking_type = "multiple"
                confidence = 0.85
                reasoning_parts.append(f"Different car types detected with {predicted_count} separate requirements")
            
            # Rule 4: Multiple 4/40 trips
            elif '4/40' in detected_duty_types and multiple_indicators > 0:
                predicted_count = multiple_indicators + 1
                booking_type = "multiple"
                confidence = 0.8
                reasoning_parts.append("Multiple 4/40 drops detected")
            
            # Rule 5: Single 8/80 outstation for consecutive days
            elif ('8/80' in detected_duty_types or 'outstation' in detected_duty_types) and single_indicators > 0:
                predicted_count = 1
                booking_type = "single"
                confidence = 0.9
                reasoning_parts.append("8/80 outstation package for consecutive days")
            
            # Rule 6: Single 4/40 drop
            elif '4/40' in detected_duty_types and multiple_indicators == 0:
                predicted_count = 1
                booking_type = "single"
                confidence = 0.8
                reasoning_parts.append("Single 4/40 drop")
            
            # Fallback: Use date count and indicators
            else:
                if date_count > 1 and multiple_indicators > single_indicators:
                    predicted_count = max(date_count, multiple_indicators)
                    booking_type = "multiple"
                    confidence = 0.6
                    reasoning_parts.append("Multiple dates detected with multiple booking indicators")
                else:
                    predicted_count = 1
                    booking_type = "single"
                    confidence = 0.6
                    reasoning_parts.append("Default single booking classification")
            
            # Cap the maximum predicted count
            predicted_count = min(predicted_count, 10)
            
            reasoning = " | ".join(reasoning_parts) if reasoning_parts else "No specific patterns detected"
            
            return ClassificationResult(
                predicted_booking_count=predicted_count,
                booking_type=booking_type,
                confidence_score=confidence,
                reasoning=reasoning,
                detected_patterns=detected_patterns,
                duty_type_indicators=duty_type_indicators,
                date_patterns=date_patterns,
                additional_info=f"Detected duty types: {', '.join(detected_duty_types) if detected_duty_types else 'None'}"
            )
            
        except Exception as e:
            logger.error(f"Error in text classification: {str(e)}")
            return ClassificationResult(
                predicted_booking_count=1,
                booking_type="single",
                confidence_score=0.3,
                reasoning=f"Classification failed: {str(e)}",
                detected_patterns=[],
                duty_type_indicators=[],
                date_patterns=[]
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