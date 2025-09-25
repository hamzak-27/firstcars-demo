"""
Agent 1: Booking Classification Agent
Analyzes email content to determine single vs multiple bookings based on business rules
"""

import os
import re
from typing import Dict, List, Optional, Any
from openai import OpenAI

from .base_agent import BaseAgent, AgentType
from ..models.shared_models import BookingType, UsageType, ClassificationResult


class BookingClassificationAgent(BaseAgent):
    """
    Agent 1: Booking Classification Agent
    
    Determines whether email content requires single or multiple booking records
    based on specific business rules:
    
    RULES:
    1. Single booking can have multiple passengers unless specified to create separate for each
    2. Multiple dates + outstation usage = single booking
    3. Multiple dates + local usage = multiple bookings  
    4. Single booking can have multiple pickup/drop addresses
    """
    
    def __init__(self, openai_api_key: str = None, model: str = "gpt-3.5-turbo"):
        """Initialize classification agent with lightweight model for cost efficiency"""
        super().__init__(AgentType.CLASSIFICATION)
        
        self.openai_api_key = openai_api_key or os.getenv('OPENAI_API_KEY')
        if not self.openai_api_key:
            raise ValueError("OpenAI API key is required")
        
        self.client = OpenAI(api_key=self.openai_api_key)
        self.model = model
        
        # Cost estimates (approximate for gpt-3.5-turbo)
        self.cost_per_1k_input_tokens = 0.0010  # $0.001 per 1K input tokens
        self.cost_per_1k_output_tokens = 0.0020  # $0.002 per 1K output tokens
    
    def _build_system_prompt(self) -> str:
        """Build system prompt for booking classification"""
        return """You are an expert booking classification agent for car rental emails.

Your SOLE responsibility is to analyze email content and determine if it requires SINGLE or MULTIPLE booking records.

CRITICAL BUSINESS RULES:

1. **Single Booking with Multiple Passengers**: 
   - DEFAULT: Multiple passengers = single booking unless explicitly stated "separate booking for each passenger"
   - Example: "John, Mary, Peter need car tomorrow" = SINGLE booking

2. **Multiple Dates Analysis**:
   - Multiple dates + OUTSTATION usage = SINGLE booking (multi-day outstation trip)
   - Multiple dates + LOCAL usage = MULTIPLE bookings (separate local trips)
   - Example: "Mumbai to Pune 25th-27th Dec" = SINGLE (outstation)
   - Example: "Local Bangalore 25th, 26th, 27th" = MULTIPLE (3 bookings)

3. **Multiple Addresses**:
   - Single booking can have multiple pickup/drop locations
   - Example: "Pickup from Hotel, drop to Airport, then Office" = SINGLE booking

4. **Explicit Separation Indicators**:
   - "separate booking for each", "individual bookings", "different bookings" = MULTIPLE
   - Table format with different passengers/dates = MULTIPLE

5. **Usage Type Detection**:
   - LOCAL: "local use", "at disposal", "within city", "same city" 
   - OUTSTATION: city to different city, "Mumbai to Pune", inter-city travel
   - AIRPORT_TRANSFER: "airport pickup", "airport drop", flight numbers mentioned

ANALYSIS PROCESS:
1. Detect all dates mentioned
2. Identify usage type (local/outstation/airport)  
3. Count distinct passengers
4. Look for explicit separation requests
5. Apply business rules to determine single vs multiple

Return classification with confidence score and detailed reasoning."""

    def _process_internal(self, input_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Process email content and classify booking type"""
        
        email_content = input_data.get('email_content', '')
        sender_email = input_data.get('sender_email', '')
        
        if not email_content:
            raise ValueError("Email content is required for classification")
        
        # Build user prompt with classification request
        user_prompt = f"""
Analyze this car rental email and classify the booking requirements:

EMAIL CONTENT:
{email_content}

SENDER: {sender_email}

Perform step-by-step analysis and classify according to business rules:

STEP 1: Extract key information
- All dates mentioned
- All passenger names  
- All locations (pickup/drop/destinations)
- Usage keywords (local/outstation/airport)

STEP 2: Apply business rules
- Check for explicit separation requests
- Determine usage type (local/outstation/airport_transfer)
- Apply date + usage rules
- Count required bookings

STEP 3: Classification decision
Based on rules, determine if SINGLE or MULTIPLE bookings needed.

Return ONLY this JSON format:

{{
    "analysis": "Step-by-step reasoning following the business rules",
    "booking_type": "single|multiple", 
    "booking_count": 1-10,
    "usage_type": "local|outstation|airport_transfer|unknown",
    "confidence_score": 0.0-1.0,
    
    "has_multiple_dates": true|false,
    "has_multiple_passengers": true|false,
    "has_multiple_locations": true|false,
    "separate_passenger_bookings": true|false,
    
    "detected_dates": ["2024-12-25", "2024-12-26"],
    "detected_passengers": ["John Doe", "Mary Smith"],
    "detected_locations": ["Mumbai", "Pune", "Delhi"],
    
    "processing_strategy": "standard|table_extraction|complex_parsing",
    "special_instructions": {{
        "requires_table_parsing": true|false,
        "has_structured_data": true|false,
        "needs_date_parsing": true|false
    }},
    
    "reasoning": "Detailed explanation of why single/multiple bookings are needed"
}}
"""
        
        # Call OpenAI API
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1,
            max_tokens=1000
        )
        
        # Parse response
        response_text = response.choices[0].message.content.strip()
        result_data = self._parse_json_response(response_text)
        
        # Add token usage for cost calculation
        result_data['token_usage'] = {
            'input_tokens': response.usage.prompt_tokens,
            'output_tokens': response.usage.completion_tokens,
            'total_tokens': response.usage.total_tokens
        }
        
        return result_data
    
    def _estimate_cost(self, input_data: Dict[str, Any], result_data: Dict[str, Any]) -> float:
        """Calculate actual cost based on token usage"""
        token_usage = result_data.get('token_usage', {})
        input_tokens = token_usage.get('input_tokens', 0)
        output_tokens = token_usage.get('output_tokens', 0)
        
        cost = (
            (input_tokens / 1000) * self.cost_per_1k_input_tokens +
            (output_tokens / 1000) * self.cost_per_1k_output_tokens
        )
        
        return cost
    
    def _generate_next_agent_guidance(self, result_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate guidance for extraction agents"""
        return {
            'booking_type': result_data.get('booking_type'),
            'booking_count': result_data.get('booking_count', 1),
            'usage_type': result_data.get('usage_type'),
            'processing_strategy': result_data.get('processing_strategy', 'standard'),
            'special_instructions': result_data.get('special_instructions', {}),
            'detected_entities': {
                'dates': result_data.get('detected_dates', []),
                'passengers': result_data.get('detected_passengers', []),
                'locations': result_data.get('detected_locations', [])
            }
        }
    
    def create_classification_result(self, agent_result) -> ClassificationResult:
        """Convert agent result to ClassificationResult object"""
        if not agent_result.success:
            # Return default classification on failure
            return ClassificationResult(
                booking_type=BookingType.SINGLE,
                booking_count=1,
                usage_type=UsageType.UNKNOWN,
                confidence_score=0.0,
                reasoning="Classification failed - defaulting to single booking"
            )
        
        data = agent_result.data
        
        # Map string values to enums
        booking_type = BookingType.SINGLE if data.get('booking_type') == 'single' else BookingType.MULTIPLE
        
        usage_type_map = {
            'local': UsageType.LOCAL,
            'outstation': UsageType.OUTSTATION,
            'airport_transfer': UsageType.AIRPORT_TRANSFER,
            'unknown': UsageType.UNKNOWN
        }
        usage_type = usage_type_map.get(data.get('usage_type', 'unknown'), UsageType.UNKNOWN)
        
        return ClassificationResult(
            booking_type=booking_type,
            booking_count=data.get('booking_count', 1),
            usage_type=usage_type,
            confidence_score=data.get('confidence_score', 0.8),
            
            # Detailed analysis
            has_multiple_dates=data.get('has_multiple_dates', False),
            has_multiple_passengers=data.get('has_multiple_passengers', False),
            has_multiple_locations=data.get('has_multiple_locations', False),
            separate_passenger_bookings=data.get('separate_passenger_bookings', False),
            
            # Supporting evidence
            detected_dates=data.get('detected_dates', []),
            detected_passengers=data.get('detected_passengers', []),
            detected_locations=data.get('detected_locations', []),
            
            # Processing guidance
            processing_strategy=data.get('processing_strategy', 'standard'),
            special_instructions=data.get('special_instructions', {}),
            
            # Analysis reasoning
            reasoning=data.get('reasoning', data.get('analysis', ''))
        )