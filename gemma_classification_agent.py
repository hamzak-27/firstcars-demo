#!/usr/bin/env python3
"""
Enhanced Gemma Classification Agent for Car Rental Bookings
Determines single vs multiple bookings based on specific business rules
"""

import os
import json
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
    import google.generativeai as genai
    from gemini_model_utils import create_gemini_model
    GEMMA_AVAILABLE = True
except ImportError:
    GEMMA_AVAILABLE = False
    logger.warning("Google Generative AI not available. Install with: pip install google-generativeai")

class GemmaClassificationAgent:
    """
    Enhanced Classification Agent using Gemma API
    
    Applies specific business rules:
    SINGLE BOOKINGS:
    - Multi-day usage under 8HR/80KM package (continuous days)
    - Multi-day outstation package
    - Single drop per day (4HR/40KM package)
    
    MULTIPLE BOOKINGS:  
    - Two or more drops in a single day
    - 8HR/80KM usage on alternate days (Day 1, Day 3, Day 5, etc.)
    - Multi-day 8HR/80KM with changing vehicle types
    """
    
    def __init__(self, api_key: str = None, model_name: str = "models/gemini-2.5-flash"):
        """Initialize Gemma classification agent"""
        
        if not GEMMA_AVAILABLE:
            raise ImportError("Google Generative AI SDK not available. Install with: pip install google-generativeai")
        
        self.api_key = api_key or os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_AI_API_KEY')
        if not self.api_key and api_key != "test-key":  # Allow test key for development
            logger.warning("Gemini API key not found. Set GEMINI_API_KEY or GOOGLE_AI_API_KEY environment variable.")
            logger.info("For now, agent will work in demo mode - set API key later for actual usage.")
        
        self.model_name = model_name
        
        # Configure Gemini using the model manager
        if GEMMA_AVAILABLE and self.api_key and self.api_key != "test-key":
            try:
                self.model, actual_model_name = create_gemini_model(self.api_key, model_name)
                if self.model:
                    self.model_name = actual_model_name
                    logger.info(f"Successfully configured Gemini model: {actual_model_name}")
                else:
                    logger.error(f"Failed to create any Gemini model: {actual_model_name}")
            except Exception as e:
                logger.error(f"Error creating Gemini model: {e}")
                self.model = None
        else:
            self.model = None
            if not self.api_key:
                logger.info("No Gemini API key found - will use rule-based classification")
            else:
                logger.info("Test mode - will use rule-based classification")
        
        # Cost tracking (approximate rates in INR)
        self.cost_per_1k_input_tokens = 0.05  # ₹0.05 per 1K input tokens
        self.cost_per_1k_output_tokens = 0.15  # ₹0.15 per 1K output tokens
        self.total_cost = 0.0
        self.request_count = 0
        
        logger.info(f"GemmaClassificationAgent initialized with model: {model_name}")
    
    def _estimate_tokens(self, text: str) -> int:
        """Rough token estimation (1 token ≈ 4 chars for English)"""
        return len(text) // 4
    
    def _track_cost(self, input_text: str, output_text: str) -> float:
        """Track and return API usage cost in INR"""
        input_tokens = self._estimate_tokens(input_text)
        output_tokens = self._estimate_tokens(output_text)
        
        cost_inr = (
            (input_tokens / 1000) * self.cost_per_1k_input_tokens +
            (output_tokens / 1000) * self.cost_per_1k_output_tokens
        )
        
        self.total_cost += cost_inr
        self.request_count += 1
        
        logger.debug(f"Request cost: ₹{cost_inr:.4f} (Input: {input_tokens}, Output: {output_tokens} tokens)")
        return cost_inr
    
    def _build_classification_prompt(self, content: str) -> str:
        """Build the classification prompt with business rules"""
        return f"""You are an expert car rental booking classification agent. Analyze the content and determine if it requires SINGLE or MULTIPLE booking records.

CRITICAL BUSINESS RULES:

🟢 SINGLE BOOKINGS:
1. **Multi-day 8HR/80KM (8/80) continuous usage**: Client uses car for consecutive days under disposal package
   - Example: "Need car for 3 days (Mon-Wed) for local disposal" = SINGLE booking
   
2. **Outstation multi-day trips**: Inter-city travel spanning multiple days
   - Example: "Mumbai to Pune for 2 days, return on 3rd day" = SINGLE booking
   
3. **Single drop per day (4HR/40KM)**: One pickup and one drop location per day
   - Example: "Drop from office to airport tomorrow" = SINGLE booking

🔴 MULTIPLE BOOKINGS:
1. **Multiple drops in same day**: Two or more drop locations in a single day
   - Example: "Drop to Airport, then Hotel, then Office - all today" = MULTIPLE bookings (3 separate)
   
2. **8HR/80KM alternate days**: Disposal usage on non-consecutive days
   - Example: "Need car on Monday, Wednesday, Friday for local use" = MULTIPLE bookings (3 separate)
   
3. **Vehicle type changes during multi-day**: Different vehicles for different days
   - Example: "Dzire for Day 1-2, Innova for Day 3-4" = MULTIPLE bookings (2 separate)
   
4. **TABLE EXTRACTION with multiple bookings**: Table data showing multiple booking entries/columns
   - Example: "TABLE EXTRACTION RESULTS (4 bookings found)" = MULTIPLE bookings
   - Example: "Cab 1, Cab 2, Cab 3, Cab 4" column headers = MULTIPLE bookings (4 separate)
   - Example: Multiple rows with different passenger names/dates = MULTIPLE bookings
   
5. **STRUCTURED DATA with multiple records**: Multiple booking records extracted from forms/tables
   - Look for patterns like "Booking 1:", "Booking 2:", "Booking 3:" etc.
   - Multiple different dates, names, or addresses in structured format

DUTY TYPE DETECTION:
- **4HR/40KM (4/40)**: "drop", "pickup and drop", "airport transfer", "point to point"
- **8HR/80KM (8/80)**: "disposal", "at disposal", "local use", "within city", "8 hours"
- **Outstation**: city names, "outstation", "inter-city", "Mumbai to Pune"

CONTENT TO ANALYZE:
{content}

ANALYSIS REQUIRED:
1. Detect duty type (4/40, 8/80, outstation)
2. Identify all dates mentioned
3. Count drop locations per day
4. Check for vehicle type changes
5. Apply business rules to determine single vs multiple

Return ONLY this JSON format:

{{
    "analysis_steps": "Step-by-step reasoning following business rules",
    "detected_duty_type": "4HR/40KM|8HR/80KM|outstation|unknown",
    "detected_dates": ["2024-12-25", "2024-12-26"],
    "detected_vehicles": ["Dzire", "Innova"],
    "detected_drops": ["Airport", "Hotel", "Office"],
    
    "pattern_analysis": {{
        "is_multi_day_continuous": true|false,
        "is_alternate_days": true|false,
        "has_vehicle_changes": true|false,
        "has_multiple_drops_per_day": true|false
    }},
    
    "business_rule_applied": "single_multi_day_8_80|single_outstation|single_drop_4_40|multiple_drops_same_day|multiple_alternate_days|multiple_vehicle_changes",
    
    "booking_classification": {{
        "booking_type": "single|multiple",
        "booking_count": 1-10,
        "confidence_score": 0.0-1.0
    }},
    
    "reasoning": "Detailed explanation of why this classification was chosen based on business rules"
}}

CLASSIFY NOW:"""

    def classify_content(self, content: str, source_type: str = "email") -> ClassificationResult:
        """
        Classify content to determine single vs multiple bookings
        
        Args:
            content: Email content or OCR extracted text
            source_type: Type of source ("email", "pdf", "image", "word_doc")
        
        Returns:
            ClassificationResult with booking type and detailed analysis
        """
        
        start_time = time.time()
        logger.info(f"Starting classification for {source_type} content ({len(content)} chars)")
        
        # Handle demo mode (no API key)
        if not self.model:
            logger.warning("Demo mode: Using rule-based classification fallback")
            return self._rule_based_classification(content, start_time)
        
        try:
            # Build classification prompt
            prompt = self._build_classification_prompt(content)
            
            # Generate response
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1,
                    max_output_tokens=1500,
                    top_p=0.8
                )
            )
            
            # Check if response is valid
            if not response or not hasattr(response, 'text'):
                raise ValueError("Invalid response from Gemini API")
            
            if not response.text or not response.text.strip():
                raise ValueError("Empty response from Gemini API")
            
            output_text = response.text.strip()
            processing_time = time.time() - start_time
            
            # Track cost
            cost_inr = self._track_cost(prompt, output_text)
            
            # Parse response
            result_data = self._parse_classification_response(output_text)
            
            # Create result object
            classification_result = self._create_result_object(result_data, cost_inr, processing_time)
            
            logger.info(f"Classification completed: {classification_result.booking_type.value} booking(s), "
                      f"confidence: {classification_result.confidence_score:.1%}, "
                      f"cost: ₹{cost_inr:.4f}")
            
            return classification_result
            
        except Exception as e:
            logger.error(f"Gemma classification failed: {str(e)}")
            # Fallback to rule-based classification
            return self._rule_based_classification(content, start_time, error=str(e))
    
    def _parse_classification_response(self, response_text: str) -> Dict[str, Any]:
        """Parse JSON response from Gemma with enhanced error handling"""
        try:
            # Clean response text
            response_text = response_text.strip()
            if response_text.startswith('```json'):
                response_text = response_text.replace('```json', '').replace('```', '').strip()
            
            # Find JSON boundaries
            start = response_text.find('{')
            end = response_text.rfind('}') + 1
            
            if start == -1 or end == 0:
                raise ValueError("No JSON object found in response")
            
            json_str = response_text[start:end]
            
            # Try to fix common JSON issues
            json_str = self._fix_common_json_issues(json_str)
            
            return json.loads(json_str)
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing failed: {str(e)}")
            logger.error(f"Response was: {response_text[:500]}...")
            
            # Try to extract key information from malformed JSON
            return self._extract_fallback_classification(response_text)
    
    def _fix_common_json_issues(self, json_str: str) -> str:
        """Fix common JSON formatting issues"""
        # Remove trailing commas before closing braces/brackets
        json_str = re.sub(r',\s*([}\]])', r'\1', json_str)
        
        # Fix unescaped quotes in string values
        json_str = re.sub(r'"([^"]*?)"([^"]*?)"([^"]*?)":', r'"\1\'\2\'\3":', json_str)
        
        # Truncate if JSON is incomplete (common with large responses)
        brace_count = json_str.count('{') - json_str.count('}')
        if brace_count > 0:
            # Try to find a complete JSON portion
            lines = json_str.split('\n')
            for i, line in enumerate(lines):
                partial = '\n'.join(lines[:i+1])
                try:
                    json.loads(partial)
                    json_str = partial
                    break
                except:
                    continue
        
        return json_str
    
    def _extract_fallback_classification(self, response_text: str) -> Dict[str, Any]:
        """Extract classification info from malformed JSON response"""
        logger.warning("Using fallback classification extraction")
        
        # Extract key information using regex
        booking_type = 'single'  # default
        booking_count = 1
        confidence = 0.8
        
        if 'multiple' in response_text.lower():
            booking_type = 'multiple'
            booking_count = 2
        
        # Try to extract confidence if present
        conf_match = re.search(r'confidence["\s]*:["\s]*(\d+(?:\.\d+)?)', response_text, re.IGNORECASE)
        if conf_match:
            confidence = float(conf_match.group(1))
            if confidence > 1:  # Convert percentage to decimal
                confidence = confidence / 100
        
        return {
            'booking_classification': {
                'booking_type': booking_type,
                'booking_count': booking_count,
                'confidence_score': confidence
            },
            'pattern_analysis': {},
            'detected_duty_type': 'unknown',
            'detected_dates': [],
            'detected_vehicles': [],
            'detected_drops': [],
            'reasoning': 'Extracted from malformed JSON response'
        }
    
    def _create_result_object(self, data: Dict[str, Any], cost_inr: float, processing_time: float) -> ClassificationResult:
        """Create ClassificationResult from parsed data"""
        
        booking_data = data.get('booking_classification', {})
        pattern_data = data.get('pattern_analysis', {})
        
        # Map duty type
        duty_type_map = {
            '4HR/40KM': DutyType.DROP_4_40,
            '8HR/80KM': DutyType.DISPOSAL_8_80,
            'outstation': DutyType.OUTSTATION,
            'unknown': DutyType.UNKNOWN
        }
        
        detected_duty = data.get('detected_duty_type', 'unknown')
        duty_type = duty_type_map.get(detected_duty, DutyType.UNKNOWN)
        
        # Map booking type
        booking_type_str = booking_data.get('booking_type', 'single')
        booking_type = BookingType.SINGLE if booking_type_str == 'single' else BookingType.MULTIPLE
        
        return ClassificationResult(
            booking_type=booking_type,
            booking_count=booking_data.get('booking_count', 1),
            confidence_score=booking_data.get('confidence_score', 0.8),
            reasoning=data.get('reasoning', 'Classification completed'),
            
            # Detected patterns
            detected_duty_type=duty_type,
            detected_dates=data.get('detected_dates', []),
            detected_vehicles=data.get('detected_vehicles', []),
            detected_drops=data.get('detected_drops', []),
            
            # Business rule analysis
            is_multi_day_continuous=pattern_data.get('is_multi_day_continuous', False),
            is_alternate_days=pattern_data.get('is_alternate_days', False),
            has_vehicle_changes=pattern_data.get('has_vehicle_changes', False),
            has_multiple_drops_per_day=pattern_data.get('has_multiple_drops_per_day', False),
            
            # Processing metadata
            cost_inr=cost_inr,
            processing_time=processing_time
        )
    
    def _rule_based_classification(self, content: str, start_time: float, error: str = None) -> ClassificationResult:
        """Fallback rule-based classification when Gemma API fails"""
        
        content_lower = content.lower()
        processing_time = time.time() - start_time
        
        # Simple keyword-based detection
        drops_keywords = ['drop', 'airport', 'pickup and drop']
        disposal_keywords = ['disposal', 'at disposal', '8 hours', '8hr', '80km', 'local use']
        outstation_keywords = ['outstation', 'mumbai to pune', 'delhi to gurgaon']
        
        # Detect duty type
        if any(keyword in content_lower for keyword in outstation_keywords):
            duty_type = DutyType.OUTSTATION
        elif any(keyword in content_lower for keyword in disposal_keywords):
            duty_type = DutyType.DISPOSAL_8_80
        elif any(keyword in content_lower for keyword in drops_keywords):
            duty_type = DutyType.DROP_4_40
        else:
            duty_type = DutyType.UNKNOWN
        
        # Enhanced classification logic with table detection
        multiple_indicators = ['separate booking', 'different days', 'alternate', 'then', 'after that']
        
        # Table/multi-booking structure indicators
        table_indicators = [
            'cab 1', 'cab 2', 'cab 3', 'cab 4',
            'booking 1', 'booking 2', 'booking 3', 'booking 4',
            'table extraction results', 'bookings found',
            'multiple bookings', 'found 4 bookings', 'found 3 bookings',
            'enhanced multi-booking', 'textract'
        ]
        
        # Check for table patterns
        has_table_indicators = any(indicator in content_lower for indicator in table_indicators)
        has_multiple_indicators = any(indicator in content_lower for indicator in multiple_indicators)
        
        # Count booking-related patterns
        booking_count = 1
        if has_table_indicators:
            # Try to detect number of bookings from table patterns
            if 'cab 4' in content_lower or 'booking 4' in content_lower:
                booking_count = 4
            elif 'cab 3' in content_lower or 'booking 3' in content_lower:
                booking_count = 3
            elif 'cab 2' in content_lower or 'booking 2' in content_lower:
                booking_count = 2
            
            # Look for explicit booking count mentions
            import re
            count_matches = re.findall(r'(\d+)\s*bookings?\s*found', content_lower)
            if count_matches:
                booking_count = max(int(count_matches[0]), booking_count)
        elif has_multiple_indicators:
            booking_count = 2
        
        # Classification decision
        booking_type = BookingType.MULTIPLE if (has_table_indicators or has_multiple_indicators) else BookingType.SINGLE
        
        # Update reasoning
        reasoning = "Rule-based classification (Gemma API unavailable)"
        if has_table_indicators:
            reasoning += " - Detected table/multi-booking structure"
        elif has_multiple_indicators:
            reasoning += " - Detected multiple booking indicators"
        
        if error:
            reasoning += f" - Error: {error}"
        
        reasoning = "Rule-based classification (Gemma API unavailable)"
        if error:
            reasoning += f" - Error: {error}"
        
        return ClassificationResult(
            booking_type=booking_type,
            booking_count=booking_count,
            confidence_score=0.6,  # Lower confidence for rule-based
            reasoning=reasoning,
            
            detected_duty_type=duty_type,
            detected_dates=[],
            detected_vehicles=[],
            detected_drops=[],
            
            cost_inr=0.0,  # No cost for rule-based
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
            'estimated_monthly_cost_5k': round(avg_cost * 5000, 2)
        }

# Test function
def test_classification_agent():
    """Test the classification agent with sample scenarios"""
    
    print("🧪 Testing Gemma Classification Agent...")
    
    # Sample test cases covering all business rules
    test_cases = [
        {
            "name": "Single - Multi-day 8HR/80KM continuous",
            "content": """
            Dear Team,
            Please arrange a car for Mr. Rajesh (9876543210) for local disposal.
            Dates: 25th, 26th, 27th December 2024
            Time: 9 AM to 6 PM daily
            Vehicle: Dzire
            Usage: Local disposal within Mumbai (8HR/80KM package)
            Thanks!
            """,
            "expected": "single"
        },
        {
            "name": "Multiple - Alternate day 8HR/80KM",  
            "content": """
            Car needed for John Smith (9123456789):
            - Monday 25th Dec: Local disposal in Delhi
            - Wednesday 27th Dec: Local disposal in Delhi  
            - Friday 29th Dec: Local disposal in Delhi
            All 8HR/80KM package, same vehicle Innova.
            """,
            "expected": "multiple"
        },
        {
            "name": "Multiple - Multiple drops same day",
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
            "name": "Single - Outstation multi-day",
            "content": """
            Outstation trip required:
            Passenger: Manager (9876543210)
            Route: Mumbai to Pune (outstation)
            Dates: 25th to 28th Dec 2024
            Vehicle: Innova Crysta
            One complete outstation trip.
            """,
            "expected": "single"
        },
        {
            "name": "Multiple - Vehicle changes", 
            "content": """
            Multi-day booking with different vehicles:
            Day 1-2: Dzire for local disposal
            Day 3-4: Innova for local disposal  
            Same passenger but vehicle type changing.
            """,
            "expected": "multiple"
        }
    ]
    
    # Initialize agent (will work in demo mode without API key)
    agent = GemmaClassificationAgent()
    
    print(f"\n📊 Running {len(test_cases)} test cases...\n")
    
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

if __name__ == "__main__":
    test_classification_agent()