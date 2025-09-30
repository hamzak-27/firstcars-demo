#!/usr/bin/env python3
"""
OpenAI Classification Agent for Car Rental Bookings
Determines single vs multiple bookings using ALL ORIGINAL COMPLEX BUSINESS RULES
Replaces gemma_classification_agent.py with OpenAI GPT-4o-mini
"""

import os
import json
import re
import time
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BookingType(Enum):
    SINGLE = "single"
    MULTIPLE = "multiple"

class DutyType(Enum):
    DROP_4_40 = "4HR/40KM"  # 4 hour 40 km drop service
    DISPOSAL_8_80 = "8HR/80KM"  # 8 hour 80 km disposal
    OUTSTATION = "outstation"
    UNKNOWN = "unknown"

@dataclass
class ClassificationResult:
    """Result from classification agent"""
    booking_type: BookingType
    booking_count: int
    confidence_score: float
    reasoning: str
    
    # Detected patterns
    detected_duty_type: DutyType
    detected_dates: List[str]
    detected_vehicles: List[str]
    detected_drops: List[str]
    
    # Business rule analysis
    is_multi_day_continuous: bool = False
    is_alternate_days: bool = False
    has_vehicle_changes: bool = False
    has_multiple_drops_per_day: bool = False
    
    # Processing metadata
    cost_inr: float = 0.0
    processing_time: float = 0.0

try:
    from openai_model_utils import create_openai_client, create_chat_messages
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI utilities not available")

class OpenAIClassificationAgent:
    """
    Enhanced Classification Agent using OpenAI GPT-4o-mini
    
    Applies ALL ORIGINAL COMPLEX BUSINESS RULES:
    SINGLE BOOKINGS:
    - Multi-day usage under 8HR/80KM package (continuous days)
    - Multi-day outstation package
    - Single drop per day (4HR/40KM package)
    - Chennai→Bangalore→Chennai outstation round trips
    
    MULTIPLE BOOKINGS:  
    - Two or more drops in a single day
    - 8HR/80KM usage on alternate days (Day 1, Day 3, Day 5, etc.)
    - Multi-day 8HR/80KM with changing vehicle types
    - Explicitly mentioned separate bookings ("First car", "Second car", etc.)
    - Table extraction with multiple booking records
    """
    
    def __init__(self, api_key: str = None, model_name: str = "gpt-4o-mini"):
        """Initialize OpenAI classification agent"""
        
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI utilities not available. Check openai_model_utils.py")
        
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            logger.warning("OpenAI API key not found. Set OPENAI_API_KEY environment variable.")
            logger.info("Agent will work in demo mode - set API key later for actual usage.")
        
        self.model_name = model_name
        
        # Configure OpenAI using the model manager
        if self.api_key:
            try:
                self.client, actual_model_name = create_openai_client(self.api_key, model_name)
                if self.client:
                    self.model_name = actual_model_name
                    logger.info(f"Successfully configured OpenAI model: {actual_model_name}")
                else:
                    logger.error(f"Failed to create OpenAI client")
            except Exception as e:
                logger.error(f"Error creating OpenAI client: {e}")
                self.client = None
        else:
            self.client = None
            logger.info("No OpenAI API key found - will use rule-based classification")
        
        # Cost tracking (rates in INR)
        self.total_cost = 0.0
        self.request_count = 0
        
        logger.info(f"OpenAIClassificationAgent initialized with model: {model_name}")
    
    def _track_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Track and return API usage cost in INR"""
        if self.client:
            cost_inr = self.client.calculate_cost(input_tokens, output_tokens, self.model_name)
            self.total_cost += cost_inr
            self.request_count += 1
            logger.debug(f"Request cost: ₹{cost_inr:.4f} (Input: {input_tokens}, Output: {output_tokens} tokens)")
            return cost_inr
        return 0.0
    
    def _build_classification_prompt(self) -> str:
        """Build the FULL ORIGINAL COMPLEX classification prompt with ALL business rules"""
        return """You are an expert car rental booking classification agent with comprehensive knowledge of transportation industry business rules. Analyze the content and determine if it requires SINGLE or MULTIPLE booking records.

**CRITICAL BUSINESS RULES - APPLY WITH PRECISION:**

🟢 **SINGLE BOOKINGS (One booking record required):**

1. **Multi-day 8HR/80KM (8/80) continuous usage**: Client uses car for consecutive days under disposal package
   - Example: "Need car for 3 days (Mon-Wed) for local disposal in Mumbai" = SINGLE booking
   - Example: "Car required for 5 consecutive days for company visits" = SINGLE booking
   - Key: Same passenger, same duty type, consecutive dates
   
2. **Outstation multi-day trips**: Inter-city travel spanning multiple days with same passenger
   - Example: "Mumbai to Pune for 2 days, return on 3rd day" = SINGLE booking
   - Example: "Chennai to Bangalore to Chennai round trip" = SINGLE booking ⭐
   - Example: "Delhi to Gurgaon outstation, staying 4 days" = SINGLE booking
   - Key: Round trips and multi-city continuous journeys are SINGLE bookings
   
3. **Single drop per day (4HR/40KM)**: One pickup and one drop location per day
   - Example: "Drop from office to airport tomorrow morning" = SINGLE booking
   - Example: "Pickup from hotel, drop at railway station" = SINGLE booking
   - Key: Point-to-point transfers with single origin and destination

4. **Continuous multi-day travel with same parameters**:
   - Same passenger name throughout
   - Same vehicle type/category 
   - Same service package (8/80 or outstation)
   - Sequential/continuous date range

🔴 **MULTIPLE BOOKINGS (Separate booking records required):**

1. **Multiple drops in same day**: Two or more drop locations in a single day
   - Example: "Drop to Airport at 9 AM, then Hotel at 2 PM, then Office at 6 PM - all today" = MULTIPLE bookings (3 separate)
   - Example: "First drop to client office, second drop to airport, third drop home" = MULTIPLE bookings (3 separate)
   - Key: Each drop location = separate booking record

2. **8HR/80KM alternate/non-consecutive days**: Disposal usage on non-consecutive days
   - Example: "Need car on Monday, Wednesday, Friday for local use" = MULTIPLE bookings (3 separate)
   - Example: "Car required on 1st, 3rd, 5th of the month for disposal" = MULTIPLE bookings (3 separate)
   - Key: Gaps between service days = separate bookings

3. **Vehicle type changes during multi-day usage**: Different vehicles for different days
   - Example: "Dzire for Day 1-2, Innova for Day 3-4" = MULTIPLE bookings (2 separate)
   - Example: "Sedan for meetings Mon-Tue, SUV for outstation Wed-Thu" = MULTIPLE bookings (2 separate)
   - Key: Vehicle category change = separate booking records

4. **Explicit multiple booking structure**: Clear indication of separate bookings
   - Example: "First car: Chennai to Airport", "Second car: Bangalore to Hotel" = MULTIPLE bookings (2 separate)
   - Example: "Arrange two cars: Car 1 for CEO, Car 2 for Manager" = MULTIPLE bookings (2 separate)
   - Example: "Need separate bookings for different departments" = MULTIPLE bookings
   - Key: "First car", "Second car", "Car 1", "Car 2", "separate bookings" indicators

5. **TABLE EXTRACTION with multiple booking entries**: Structured data showing multiple records
   - Example: "TABLE EXTRACTION RESULTS (4 bookings found)" = MULTIPLE bookings (4 separate)
   - Example: Headers like "Cab 1, Cab 2, Cab 3, Cab 4" = MULTIPLE bookings (4 separate)
   - Example: Multiple rows with different passenger names/dates = MULTIPLE bookings
   - Key: Table structure with multiple data rows = multiple booking records

6. **Different passengers with separate requirements**:
   - Example: "Car for Mr. A at 9 AM, different car for Ms. B at 2 PM" = MULTIPLE bookings (2 separate)
   - Example: "Booking for Manager (Dzire), separate booking for Director (Innova)" = MULTIPLE bookings (2 separate)
   - Key: Different passenger names with separate service requirements

**DUTY TYPE DETECTION PATTERNS:**
- **4HR/40KM (4/40)**: "drop", "pickup and drop", "airport transfer", "point to point", "one way"
- **8HR/80KM (8/80)**: "disposal", "at disposal", "local use", "within city", "8 hours", "full day"
- **Outstation**: city names, "outstation", "inter-city", "Mumbai to Pune", "Chennai to Bangalore"

**ADVANCED PATTERN RECOGNITION:**
- Look for structured data patterns (tables, lists, numbered items)
- Identify temporal patterns (consecutive vs alternate days)
- Recognize passenger-specific requirements
- Detect vehicle-specific allocations
- Analyze geographic patterns (same city vs different cities)

**RESPONSE FORMAT - PROVIDE COMPREHENSIVE ANALYSIS:**

Return detailed analysis in this exact JSON format:

{
    "analysis_steps": "Step-by-step reasoning process following the business rules above",
    "detected_patterns": {
        "multiple_booking_indicators": ["list any found: first car, second car, etc."],
        "duty_type_indicators": ["4HR/40KM", "8HR/80KM", "outstation", or "unknown"],
        "temporal_patterns": ["consecutive days", "alternate days", "single day", etc."],
        "passenger_patterns": ["single passenger", "multiple passengers", etc."],
        "vehicle_patterns": ["same vehicle", "different vehicles", etc."],
        "geographic_patterns": ["same city", "different cities", "round trip", etc.]
    },
    "business_rule_analysis": {
        "is_multi_day_continuous": true or false,
        "is_alternate_days": true or false,
        "has_vehicle_changes": true or false,
        "has_multiple_drops_per_day": true or false,
        "has_explicit_multiple_structure": true or false,
        "has_table_structure": true or false
    },
    "classification_decision": {
        "booking_type": "single" or "multiple",
        "booking_count": number,
        "confidence_score": 0.0 to 1.0,
        "primary_reasoning": "Main reason for the classification decision",
        "supporting_evidence": ["additional evidence supporting the decision"]
    },
    "extracted_details": {
        "detected_dates": ["2024-12-25", "2024-12-26", etc.],
        "detected_vehicles": ["Dzire", "Innova", etc.],
        "detected_locations": ["Mumbai", "Airport", "Hotel", etc.],
        "detected_passengers": ["Mr. Rajesh", "Manager", etc.]
    }
}"""

    def classify_content(self, content: str, source_type: str = "email") -> ClassificationResult:
        """Classify content using OpenAI with full business rules"""
        
        start_time = time.time()
        
        if not self.client:
            logger.warning("OpenAI client not available - using rule-based fallback")
            return self._rule_based_classification(content, start_time)
        
        try:
            logger.info(f"Starting OpenAI classification for content ({len(content)} chars)")
            
            # Build the comprehensive prompt
            system_prompt = self._build_classification_prompt()
            
            # Create user message with content
            user_message = f"""**CONTENT TO ANALYZE:**

{content}

**TASK:** Apply the business rules above to analyze this content thoroughly. Determine if this requires SINGLE or MULTIPLE booking records. Consider all factors: passenger count, duty types, dates, vehicles, geographic patterns, and explicit booking structure indicators.

Provide comprehensive analysis following the exact JSON format specified above."""

            # Create chat messages
            messages = create_chat_messages(system_prompt, user_message)
            
            # Call OpenAI API
            response_text, metadata = self.client.create_completion(
                messages=messages,
                model=self.model_name,
                temperature=0.1,
                max_tokens=2000
            )
            
            processing_time = time.time() - start_time
            
            # Track cost
            cost_inr = self._track_cost(metadata['input_tokens'], metadata['output_tokens'])
            
            # Parse response
            result_data = self._parse_classification_response(response_text)
            
            # Create result object
            classification_result = self._create_result_object(result_data, cost_inr, processing_time)
            
            logger.info(f"OpenAI classification completed: {classification_result.booking_type.value} booking(s), "
                      f"confidence: {classification_result.confidence_score:.1%}, "
                      f"cost: ₹{cost_inr:.4f}")
            
            return classification_result
            
        except Exception as e:
            logger.error(f"OpenAI classification failed: {str(e)}")
            # Fallback to rule-based classification
            return self._rule_based_classification(content, start_time, error=str(e))
    
    def _parse_classification_response(self, response_text: str) -> Dict[str, Any]:
        """Parse JSON response from OpenAI"""
        try:
            # Clean response text
            response_text = response_text.strip()
            
            # Try to parse as JSON directly
            result_data = json.loads(response_text)
            return result_data
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing failed: {str(e)}")
            logger.error(f"Response was: {response_text[:500]}...")
            
            # Try to extract key information from malformed response
            return self._extract_fallback_classification(response_text)
    
    def _extract_fallback_classification(self, response_text: str) -> Dict[str, Any]:
        """Extract classification info from malformed response"""
        logger.warning("Using fallback classification extraction")
        
        # Extract key information using regex
        booking_type = 'single'  # default
        booking_count = 1
        confidence = 0.8
        
        if 'multiple' in response_text.lower():
            booking_type = 'multiple'
            booking_count = 2
        
        return {
            'classification_decision': {
                'booking_type': booking_type,
                'booking_count': booking_count,
                'confidence_score': confidence,
                'primary_reasoning': 'Extracted from malformed JSON response'
            },
            'detected_patterns': {},
            'business_rule_analysis': {},
            'extracted_details': {
                'detected_dates': [],
                'detected_vehicles': [],
                'detected_locations': [],
                'detected_passengers': []
            }
        }
    
    def _create_result_object(self, data: Dict[str, Any], cost_inr: float, processing_time: float) -> ClassificationResult:
        """Create ClassificationResult from parsed data"""
        
        # Extract classification decision
        decision = data.get('classification_decision', {})
        patterns = data.get('detected_patterns', {})
        business_analysis = data.get('business_rule_analysis', {})
        details = data.get('extracted_details', {})
        
        # Map duty type
        duty_type_indicators = patterns.get('duty_type_indicators', ['unknown'])
        detected_duty = duty_type_indicators[0] if duty_type_indicators else 'unknown'
        
        duty_type_map = {
            '4HR/40KM': DutyType.DROP_4_40,
            '8HR/80KM': DutyType.DISPOSAL_8_80,
            'outstation': DutyType.OUTSTATION,
            'unknown': DutyType.UNKNOWN
        }
        duty_type = duty_type_map.get(detected_duty, DutyType.UNKNOWN)
        
        # Map booking type
        booking_type_str = decision.get('booking_type', 'single')
        booking_type = BookingType.SINGLE if booking_type_str == 'single' else BookingType.MULTIPLE
        
        # Build reasoning
        reasoning = decision.get('primary_reasoning', 'OpenAI classification completed')
        analysis_steps = data.get('analysis_steps', '')
        if analysis_steps:
            reasoning = f"{reasoning} | Analysis: {analysis_steps[:200]}..."
        
        return ClassificationResult(
            booking_type=booking_type,
            booking_count=decision.get('booking_count', 1),
            confidence_score=decision.get('confidence_score', 0.8),
            reasoning=reasoning,
            
            # Detected patterns
            detected_duty_type=duty_type,
            detected_dates=details.get('detected_dates', []),
            detected_vehicles=details.get('detected_vehicles', []),
            detected_drops=details.get('detected_locations', []),
            
            # Business rule analysis
            is_multi_day_continuous=business_analysis.get('is_multi_day_continuous', False),
            is_alternate_days=business_analysis.get('is_alternate_days', False),
            has_vehicle_changes=business_analysis.get('has_vehicle_changes', False),
            has_multiple_drops_per_day=business_analysis.get('has_multiple_drops_per_day', False),
            
            # Processing metadata
            cost_inr=cost_inr,
            processing_time=processing_time
        )
    
    def _rule_based_classification(self, content: str, start_time: float, error: str = None) -> ClassificationResult:
        """Fallback rule-based classification when OpenAI fails"""
        
        content_lower = content.lower()
        processing_time = time.time() - start_time
        
        # Enhanced classification logic with business rules
        multiple_indicators = [
            'first car', 'second car', 'third car', 'fourth car',
            'car 1:', 'car 2:', 'car 3:', 'car 4:',
            'arrange two', 'arrange 2', 'two separate', '2 separate',
            'arrange three', 'arrange 3', 'three separate', '3 separate',
            'multiple cars', 'two cars', 'three cars', 'different cars',
            'separate booking', 'different days', 'alternate days',
            'table extraction results', 'bookings found', 'cab 1', 'cab 2'
        ]
        
        # Chennai→Bangalore→Chennai specific patterns (SINGLE booking)
        outstation_round_trip_patterns = [
            r'chennai.*to.*bangalore.*to.*chennai',
            r'mumbai.*to.*pune.*to.*mumbai',
            r'delhi.*to.*gurgaon.*to.*delhi',
            r'(\w+).*to.*(\w+).*to.*\1'  # Any city round trip pattern
        ]
        
        # Check for outstation round trips first (these should be SINGLE)
        for pattern in outstation_round_trip_patterns:
            if re.search(pattern, content_lower):
                return ClassificationResult(
                    booking_type=BookingType.SINGLE,
                    booking_count=1,
                    confidence_score=0.9,
                    reasoning="Rule-based: Outstation round trip detected (Chennai→Bangalore→Chennai pattern)",
                    detected_duty_type=DutyType.OUTSTATION,
                    detected_dates=[],
                    detected_vehicles=[],
                    detected_drops=[],
                    cost_inr=0.0,
                    processing_time=processing_time
                )
        
        # Check for multiple booking indicators
        found_indicators = []
        for indicator in multiple_indicators:
            if indicator in content_lower:
                found_indicators.append(indicator)
        
        # Count booking-related patterns
        booking_count = len(found_indicators) if found_indicators else 1
        booking_type = BookingType.MULTIPLE if found_indicators else BookingType.SINGLE
        
        reasoning = "Rule-based classification (OpenAI unavailable)"
        if found_indicators:
            reasoning += f" - Found indicators: {', '.join(found_indicators[:3])}"
        if error:
            reasoning += f" - Error: {error}"
        
        return ClassificationResult(
            booking_type=booking_type,
            booking_count=max(booking_count, 1),
            confidence_score=0.7,  # Lower confidence for rule-based
            reasoning=reasoning,
            detected_duty_type=DutyType.UNKNOWN,
            detected_dates=[],
            detected_vehicles=[],
            detected_drops=[],
            cost_inr=0.0,
            processing_time=processing_time
        )
    
    def get_cost_summary(self) -> Dict[str, Any]:
        """Get cost summary for this agent"""
        avg_cost = self.total_cost / max(1, self.request_count)
        return {
            'model': self.model_name,
            'total_requests': self.request_count,
            'total_cost_inr': round(self.total_cost, 4),
            'avg_cost_per_request': round(avg_cost, 4),
            'estimated_monthly_cost_1k': round(avg_cost * 1000, 2)
        }

# Test function
def test_openai_classification():
    """Test the OpenAI classification agent"""
    print("🧪 Testing OpenAI Classification Agent...")
    print("=" * 60)
    
    # Test cases covering all business rules
    test_cases = [
        {
            "name": "Chennai→Bangalore→Chennai Round Trip (SINGLE)",
            "content": """
            Subject: Outstation Cab Booking
            
            Dear Team,
            Please arrange a cab for Chennai to Bangalore to Chennai trip.
            Date: Tomorrow
            Time: 5 AM  
            Passenger: Rajesh Kumar
            Phone: 9876543210
            Vehicle: Dzire preferred
            
            Round trip required - same day return.
            Thanks!
            """,
            "expected": "single"
        },
        {
            "name": "Multiple Drops Same Day (MULTIPLE)",
            "content": """
            Need car for CEO tomorrow:
            - 9 AM: Pickup from Hotel, drop at Office
            - 2 PM: Pickup from Office, drop at Airport  
            - 6 PM: Pickup from Airport, drop at Home
            Three separate drops same day.
            """,
            "expected": "multiple"
        },
        {
            "name": "Explicit Multiple Cars (MULTIPLE)",
            "content": """
            Please arrange:
            First car: Chennai to Airport for Manager
            Second car: Bangalore to Hotel for Director
            Two separate bookings required.
            """,
            "expected": "multiple"
        }
    ]
    
    # Initialize agent
    agent = OpenAIClassificationAgent()
    
    print(f"📊 Running {len(test_cases)} test cases...\n")
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"Test {i}: {test_case['name']}")
        print(f"Expected: {test_case['expected']}")
        
        try:
            result = agent.classify_content(test_case['content'])
            
            print(f"Result: {result.booking_type.value} ({result.booking_count} booking(s))")
            print(f"Confidence: {result.confidence_score:.1%}")
            print(f"Duty Type: {result.detected_duty_type.value}")
            print(f"Cost: ₹{result.cost_inr:.4f}")
            print(f"Reasoning: {result.reasoning[:100]}...")
            
            # Check if result matches expectation
            status = "✅ PASS" if result.booking_type.value == test_case['expected'] else "❌ FAIL"
            print(f"Status: {status}")
            
        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
        
        print("-" * 80)
    
    # Print cost summary
    cost_summary = agent.get_cost_summary()
    print(f"\n💰 Cost Summary:")
    print(f"Total requests: {cost_summary['total_requests']}")
    print(f"Total cost: ₹{cost_summary['total_cost_inr']}")
    print(f"Avg cost per request: ₹{cost_summary['avg_cost_per_request']}")
    print(f"Estimated monthly cost (1000 emails): ₹{cost_summary['estimated_monthly_cost_1k']}")

if __name__ == "__main__":
    test_openai_classification()