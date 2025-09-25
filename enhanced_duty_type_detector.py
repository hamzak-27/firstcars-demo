"""
Enhanced Duty Type Detector
Uses structured form data instead of raw text parsing for better accuracy
"""

import logging
import json
import re
from typing import Dict, List, Optional, Any, Tuple

logger = logging.getLogger(__name__)

class EnhancedDutyTypeDetector:
    """Enhanced duty type detector that uses structured form data"""
    
    def __init__(self):
        self.duty_type_mappings = {
            # Primary duty type indicators
            'disposal': 'disposal',
            'at disposal': 'disposal', 
            'local use': 'disposal',
            'local': 'disposal',
            'city use': 'disposal',
            'whole day': 'disposal',
            'full day': 'disposal',
            'as per guest': 'disposal',
            'visit': 'disposal',
            
            'drop': 'drop',
            'airport transfer': 'drop',
            'airport pickup': 'drop',
            'pickup from airport': 'drop',
            'drop to airport': 'drop',
            'transfer': 'drop',
            'one way': 'drop',
            
            'outstation': 'outstation',
            'out station': 'outstation',
            'intercity': 'outstation',
            'between cities': 'outstation',
            'travel': 'outstation',
            'round trip': 'outstation',
        }
    
    def detect_duty_type_from_structured_data(self, booking_result, raw_email_content: str = "") -> Dict[str, Any]:
        """
        Detect duty type using structured form data with fallback to text analysis
        
        Args:
            booking_result: The result from enhanced form processing with structured data
            raw_email_content: Raw email content as fallback
            
        Returns:
            Dict with duty type information and reasoning
        """
        reasoning = []
        reasoning.append("🔍 ENHANCED DUTY TYPE DETECTION")
        reasoning.append("=" * 50)
        
        detected_duty_type = None
        confidence = 0.0
        
        # Step 1: Extract structured data from booking result
        structured_data = self._extract_structured_data_from_booking(booking_result)
        
        if structured_data:
            reasoning.append("✅ STRUCTURED DATA FOUND:")
            reasoning.append(f"   Key-value pairs: {len(structured_data.get('key_value_pairs', []))}")
            reasoning.append(f"   Form tables: {len(structured_data.get('tables', []))}")
            
            # Step 2: Look for duty type in structured key-value pairs
            duty_from_structured = self._detect_from_structured_pairs(structured_data, reasoning)
            
            if duty_from_structured:
                detected_duty_type = duty_from_structured['type']
                confidence = duty_from_structured['confidence']
                reasoning.extend(duty_from_structured['reasoning'])
            else:
                reasoning.append("❌ No duty type found in structured data")
        else:
            reasoning.append("❌ NO STRUCTURED DATA AVAILABLE")
            reasoning.append("   Using fallback text analysis")
        
        # Step 3: Fallback to text analysis if no structured data
        if not detected_duty_type and raw_email_content:
            reasoning.append("\n🔄 FALLBACK TO TEXT ANALYSIS:")
            duty_from_text = self._detect_from_text_content(raw_email_content, reasoning)
            if duty_from_text:
                detected_duty_type = duty_from_text['type']
                confidence = duty_from_text['confidence'] * 0.7  # Lower confidence for text analysis
                reasoning.extend(duty_from_text['reasoning'])
        
        # Step 4: Final determination
        if not detected_duty_type:
            detected_duty_type = 'disposal'  # Default fallback
            confidence = 0.3
            reasoning.append(f"\n🔧 DEFAULT FALLBACK: Using 'disposal' (confidence: {confidence:.1%})")
        
        reasoning.append(f"\n🎯 FINAL DUTY TYPE: {detected_duty_type.upper()}")
        reasoning.append(f"🎯 CONFIDENCE: {confidence:.1%}")
        
        return {
            'duty_type': detected_duty_type,
            'confidence': confidence,
            'reasoning': "\\n".join(reasoning),
            'method': 'enhanced_structured' if structured_data else 'fallback_text'
        }
    
    def _extract_structured_data_from_booking(self, booking_result) -> Optional[Dict[str, Any]]:
        """Extract structured data from booking result"""
        try:
            if hasattr(booking_result, 'bookings') and booking_result.bookings:
                first_booking = booking_result.bookings[0]
                if hasattr(first_booking, 'additional_info') and first_booking.additional_info:
                    # Look for structured data in additional_info
                    if "Structured Data:" in first_booking.additional_info:
                        info_parts = first_booking.additional_info.split("Structured Data: ")
                        if len(info_parts) > 1:
                            json_str = info_parts[1].strip()
                            return json.loads(json_str)
            return None
        except (json.JSONDecodeError, AttributeError, IndexError) as e:
            logger.warning(f"Could not extract structured data: {str(e)}")
            return None
    
    def _detect_from_structured_pairs(self, structured_data: Dict[str, Any], reasoning: List[str]) -> Optional[Dict[str, Any]]:
        """Detect duty type from structured key-value pairs"""
        reasoning.append("\n📋 ANALYZING STRUCTURED KEY-VALUE PAIRS:")
        
        all_pairs = []
        
        # Collect all key-value pairs
        if structured_data.get('key_value_pairs'):
            all_pairs.extend(structured_data['key_value_pairs'])
        
        if structured_data.get('tables'):
            for table in structured_data['tables']:
                if table.get('type') == 'form_table' and table.get('key_value_pairs'):
                    all_pairs.extend(table['key_value_pairs'])
        
        reasoning.append(f"   Found {len(all_pairs)} key-value pairs to analyze")
        
        # Look for duty type related fields
        duty_type_fields = [
            'usage', 'duty type', 'type of duty', 'service type', 
            'usage type', 'drop/disposal/outstation', 'usage (drop/disposal/outstation)',
            'service', 'requirement', 'booking type'
        ]
        
        best_match = None
        highest_confidence = 0.0
        
        for pair in all_pairs:
            key = pair.get('key', '').lower().strip()
            value = pair.get('value', '').lower().strip()
            
            reasoning.append(f"   • {pair.get('key', '')}: {pair.get('value', '')}")
            
            # Check if this is a duty type field
            for field_name in duty_type_fields:
                if field_name in key:
                    reasoning.append(f"     ✅ DUTY TYPE FIELD DETECTED: '{field_name}' in key")
                    
                    # Analyze the value
                    duty_type, confidence = self._analyze_duty_type_value(value)
                    reasoning.append(f"     📊 Value analysis: '{value}' → {duty_type} (confidence: {confidence:.1%})")
                    
                    if confidence > highest_confidence:
                        best_match = {
                            'type': duty_type,
                            'confidence': confidence,
                            'field': pair.get('key', ''),
                            'value': pair.get('value', ''),
                            'reasoning': [f"Found in structured field: {pair.get('key', '')} = {pair.get('value', '')}"]
                        }
                        highest_confidence = confidence
                    break
        
        if best_match:
            reasoning.append(f"\n✅ BEST STRUCTURED MATCH:")
            reasoning.append(f"   Field: {best_match['field']}")
            reasoning.append(f"   Value: {best_match['value']}")
            reasoning.append(f"   Detected Type: {best_match['type']}")
            reasoning.append(f"   Confidence: {best_match['confidence']:.1%}")
            return best_match
        else:
            reasoning.append(f"\n❌ No duty type fields found in structured data")
            return None
    
    def _analyze_duty_type_value(self, value: str) -> Tuple[str, float]:
        """Analyze a value to determine duty type and confidence"""
        value_lower = value.lower().strip()
        
        # Direct matches with high confidence
        if 'disposal' in value_lower or 'outstation' in value_lower:
            if 'disposal' in value_lower and 'outstation' in value_lower:
                # Combined value like "Disposal / Outstation"
                return 'disposal', 0.95  # Treat as disposal primarily
            elif 'disposal' in value_lower:
                return 'disposal', 0.95
            else:
                return 'outstation', 0.95
        
        # Check for other patterns
        for pattern, duty_type in self.duty_type_mappings.items():
            if pattern in value_lower:
                confidence = 0.9 if len(pattern) > 5 else 0.7  # Longer patterns get higher confidence
                return duty_type, confidence
        
        # If value is very short or unclear
        if len(value_lower) < 3:
            return 'disposal', 0.3  # Low confidence default
        
        return 'disposal', 0.5  # Medium confidence default
    
    def _detect_from_text_content(self, text_content: str, reasoning: List[str]) -> Optional[Dict[str, Any]]:
        """Fallback detection from raw text content"""
        reasoning.append(f"   Analyzing {len(text_content)} characters of text")
        
        text_lower = text_content.lower()
        
        # Look for duty type patterns in text
        pattern_matches = {}
        
        for pattern, duty_type in self.duty_type_mappings.items():
            if pattern in text_lower:
                if duty_type not in pattern_matches:
                    pattern_matches[duty_type] = []
                pattern_matches[duty_type].append(pattern)
        
        reasoning.append(f"   Pattern matches found: {len(pattern_matches)} duty types")
        
        if pattern_matches:
            # Choose the duty type with the most/strongest matches
            best_type = None
            best_score = 0
            
            for duty_type, patterns in pattern_matches.items():
                score = len(patterns)
                reasoning.append(f"     • {duty_type}: {patterns} (score: {score})")
                
                if score > best_score:
                    best_type = duty_type
                    best_score = score
            
            confidence = min(0.8, best_score * 0.3)  # Cap at 80% for text analysis
            
            return {
                'type': best_type,
                'confidence': confidence,
                'reasoning': [f"Text analysis found: {pattern_matches[best_type]}"]
            }
        
        return None

def enhance_duty_type_detection(booking_result, original_ai_agent, raw_email_content: str = ""):
    """
    Enhance an existing booking result with better duty type detection
    
    Args:
        booking_result: Result from form processing
        original_ai_agent: Original AI agent for fallback corporate logic
        raw_email_content: Raw email content
        
    Returns:
        Enhanced booking result with improved duty type
    """
    detector = EnhancedDutyTypeDetector()
    
    # Run enhanced duty type detection
    duty_info = detector.detect_duty_type_from_structured_data(booking_result, raw_email_content)
    
    # Apply the enhanced duty type to all bookings
    for booking in booking_result.bookings:
        # Store the original duty type for comparison
        original_duty_type = booking.duty_type
        
        # Map detected duty type to package format
        detected_type = duty_info['duty_type']
        
        if detected_type == 'drop':
            package_type = "04HR 40KMS"
        elif detected_type == 'outstation':
            package_type = "Outstation 250KMS"  # Default, can be enhanced based on cities
        else:  # disposal/local
            package_type = "08HR 80KMS"
        
        # Determine G2G vs P2P (use original agent logic for corporate detection)
        corporate_info = None
        duty_category = "P2P"  # Default
        
        if hasattr(original_ai_agent, '_detect_corporate_company'):
            corporate_info = original_ai_agent._detect_corporate_company(raw_email_content)
            if corporate_info:
                duty_category = corporate_info.get('duty_type', 'P2P')
        
        # Set the enhanced duty type
        enhanced_duty_type = f"{duty_category}-{package_type}"
        booking.duty_type = enhanced_duty_type
        
        # Add enhanced reasoning to the booking
        enhanced_reasoning = f"""
🚀 ENHANCED DUTY TYPE DETECTION RESULTS:
{'=' * 50}

{duty_info['reasoning']}

📊 COMPARISON:
   Original Detection: {original_duty_type or 'None'}
   Enhanced Detection: {enhanced_duty_type}
   Improvement Method: {duty_info['method']}
   Detection Confidence: {duty_info['confidence']:.1%}

🎯 FINAL PACKAGE: {enhanced_duty_type}
"""
        
        booking.duty_type_reasoning = enhanced_reasoning
        booking.confidence_score = max(booking.confidence_score, duty_info['confidence'])
    
    return booking_result