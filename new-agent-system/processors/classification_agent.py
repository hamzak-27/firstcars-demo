"""
Email Classification Agent
Determines if unstructured emails require single or multiple bookings based on business rules
"""

import openai
import json
import logging
from typing import Dict, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ClassificationResult:
    """Result of email classification"""
    booking_count: int
    booking_type: str  # "single" or "multiple"
    reasoning: str
    confidence: float

class EmailClassificationAgent:
    """
    AI agent that classifies unstructured emails to determine booking count
    """
    
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        """Initialize classification agent"""
        self.client = openai.OpenAI(api_key=api_key)
        self.model = model
        logger.info(f"Classification agent initialized with model: {model}")
    
    def classify_email(self, email_content: str) -> ClassificationResult:
        """
        Classify email content to determine single vs multiple bookings
        
        Args:
            email_content: Raw email text content
            
        Returns:
            ClassificationResult with booking count and reasoning
        """
        
        prompt = self._build_classification_prompt()
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": f"Email Content:\n{email_content}"}
                ],
                temperature=0.1,
                max_tokens=800
            )
            
            response_text = response.choices[0].message.content.strip()
            return self._parse_classification_response(response_text)
            
        except Exception as e:
            logger.error(f"Classification failed: {str(e)}")
            return ClassificationResult(
                booking_count=1,
                booking_type="single", 
                reasoning="Classification failed, defaulting to single booking",
                confidence=0.3
            )
    
    def _build_classification_prompt(self) -> str:
        """Build the classification prompt with business rules"""
        
        return """You are an expert car rental booking classifier. Your job is to analyze email content and determine if it requires SINGLE or MULTIPLE bookings based on these specific business rules:

**DUTY TYPE PACKAGES:**
- 4/40 Package = Drop/Airport transfer (4 hours, 40km limit)
- 8/80 Package = At disposal/Local use/Whole day use (8 hours, 80km limit)
- Outstation = Travel between cities

**SINGLE BOOKING SCENARIOS:**
1. Client uses car for many consecutive days under 8/80 or outstation package
2. Client wants only ONE drop (4/40 package) in a day
3. Multi-day usage with same vehicle and consecutive dates
4. Round trips or airport transfers (even if return journey)

**MULTIPLE BOOKING SCENARIOS:**
1. Client wants TWO OR MORE drops in the same day
2. Client wants 8/80 usage on ALTERNATE days (day 1, skip day 2, day 3, etc.)
3. Client wants 8/80 for multiple days but CHANGES vehicle type on some days
4. Explicitly mentioned as "Booking 1", "Booking 2", "Car 1", "Car 2"
5. Different passengers for different bookings/days
6. Mixed duty types (some days 4/40, some days 8/80)
7. **MULTI-DAY BOOKINGS**: When client specifies different service types for different consecutive days
   - Example: "28th Sept & 01st Oct will be only Airport Transfers & rest 02 days 29th Sept & 30th will be local use"
   - Each day with different service type = separate booking
   - Count each day as one booking

**ANALYSIS APPROACH:**
1. Look for explicit booking numbering (Booking 1, Car 1, etc.)
2. Count number of drops/transfers requested per day
3. Identify duty type patterns (4/40 vs 8/80 vs Outstation)
4. Check for alternating days or gaps in dates
5. Look for vehicle type changes across dates
6. Check for different passengers or requirements

**OUTPUT FORMAT:**
Return ONLY a JSON object:
{
    "booking_count": <number>,
    "booking_type": "single" or "multiple", 
    "reasoning": "Detailed explanation of your analysis",
    "confidence": <0.0 to 1.0>
}

**EXAMPLES:**

Example 1 - SINGLE:
"Need car for Delhi to Mumbai outstation trip from 15th to 18th Oct for disposal use"
→ Single booking (consecutive days, same package, same route)

Example 2 - MULTIPLE: 
"Need airport drop at 9 AM and another drop to hotel at 6 PM same day"
→ Multiple bookings (2 drops same day)

Example 3 - MULTIPLE:
"Need car for disposal on Monday, Wednesday and Friday next week"  
→ Multiple bookings (alternate days, gaps between dates)

Example 4 - MULTIPLE (Multi-day with different services):
"Kindly book cab in Mumbai from 28th Sept to 01st Oct 25. (28th Sept & 01st Oct will be only Airport Transfers) & rest 02 days 29th Sept & 30th will be local use."
→ 4 bookings (4 different days: 28th=Airport, 29th=Local, 30th=Local, 01st=Airport)

Analyze the email carefully and classify accordingly."""

    def _parse_classification_response(self, response_text: str) -> ClassificationResult:
        """Parse the AI response into ClassificationResult"""
        
        try:
            # Extract JSON from response
            if '```json' in response_text:
                json_start = response_text.find('```json') + 7
                json_end = response_text.find('```', json_start)
                response_text = response_text[json_start:json_end].strip()
            elif '```' in response_text:
                json_start = response_text.find('```') + 3
                json_end = response_text.rfind('```')
                response_text = response_text[json_start:json_end].strip()
            
            # Find JSON boundaries
            start = response_text.find('{')
            end = response_text.rfind('}') + 1
            
            if start >= 0 and end > start:
                json_text = response_text[start:end]
                result_data = json.loads(json_text)
                
                return ClassificationResult(
                    booking_count=result_data.get('booking_count', 1),
                    booking_type=result_data.get('booking_type', 'single'),
                    reasoning=result_data.get('reasoning', 'AI classification completed'),
                    confidence=result_data.get('confidence', 0.8)
                )
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse classification response: {e}")
        except Exception as e:
            logger.error(f"Error parsing classification response: {e}")
        
        # Fallback: Try to extract basic info from text
        if 'multiple' in response_text.lower():
            booking_count = 2  # Default to 2 for multiple
            booking_type = 'multiple'
        else:
            booking_count = 1
            booking_type = 'single'
        
        return ClassificationResult(
            booking_count=booking_count,
            booking_type=booking_type,
            reasoning=f"Parsed from text response: {response_text[:200]}...",
            confidence=0.6
        )
    
    def classify_booking_type(self, email_content: str) -> Dict[str, Any]:
        """
        Alternative method name for orchestrator compatibility
        
        Args:
            email_content: Raw email text content
            
        Returns:
            Dict with booking count and classification details
        """
        result = self.classify_email(email_content)
        
        return {
            'booking_count': result.booking_count,
            'booking_type': result.booking_type,
            'reasoning': result.reasoning,
            'confidence': result.confidence
        }


# Alias for compatibility with orchestrator
ClassificationAgent = EmailClassificationAgent
