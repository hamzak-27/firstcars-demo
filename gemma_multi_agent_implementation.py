"""
Gemma Multi-Agent Implementation for Booking System
Cost-optimized multi-agent architecture using Gemma models
"""

import os
import json
import logging
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import asdict
from enum import Enum

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AgentType(Enum):
    CLASSIFIER = "classifier"
    EXTRACTOR = "extractor" 
    VALIDATOR = "validator"

class DocumentType(Enum):
    SINGLE_BOOKING = "single_booking"
    MULTI_BOOKING = "multi_booking"
    EXPENSE_REPORT = "expense_report"
    FLIGHT_DETAILS = "flight_details"
    UNKNOWN = "unknown"

try:
    import google.generativeai as genai
    GEMMA_AVAILABLE = True
except ImportError:
    GEMMA_AVAILABLE = False
    logger.warning("Google Generative AI not available. Install with: pip install google-generativeai")

class GemmaAgent:
    """Base Gemma agent with cost tracking"""
    
    def __init__(self, model_name: str = "gemma-2-9b-it", api_key: str = None):
        self.model_name = model_name
        self.api_key = api_key or os.getenv('GOOGLE_AI_API_KEY')
        self.request_count = 0
        self.total_cost = 0.0
        
        if not GEMMA_AVAILABLE:
            raise ImportError("Google Generative AI SDK not available")
        
        if not self.api_key:
            raise ValueError("Google AI API key required. Set GOOGLE_AI_API_KEY environment variable.")
        
        # Configure Gemma
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(model_name)
        
        # Cost tracking (in USD, converted to INR)
        self.cost_per_1m_input = 0.075 if "9b" in model_name else 0.035
        self.cost_per_1m_output = 0.30 if "9b" in model_name else 0.105
        self.usd_to_inr = 83
        
        logger.info(f"Initialized Gemma agent with model: {model_name}")
    
    def _estimate_tokens(self, text: str) -> int:
        """Rough token estimation (1 token ≈ 4 chars for English)"""
        return len(text) // 4
    
    def _track_cost(self, input_text: str, output_text: str):
        """Track API usage costs"""
        input_tokens = self._estimate_tokens(input_text)
        output_tokens = self._estimate_tokens(output_text)
        
        input_cost = (input_tokens / 1_000_000) * self.cost_per_1m_input
        output_cost = (output_tokens / 1_000_000) * self.cost_per_1m_output
        
        request_cost_usd = input_cost + output_cost
        request_cost_inr = request_cost_usd * self.usd_to_inr
        
        self.total_cost += request_cost_inr
        self.request_count += 1
        
        logger.debug(f"Request cost: ₹{request_cost_inr:.4f} (Input: {input_tokens}, Output: {output_tokens} tokens)")
    
    def generate_content(self, prompt: str, temperature: float = 0.1) -> str:
        """Generate content with cost tracking"""
        try:
            start_time = time.time()
            
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=temperature,
                    max_output_tokens=2000,
                    top_p=0.8,
                    top_k=40
                )
            )
            
            processing_time = time.time() - start_time
            output_text = response.text
            
            # Track costs
            self._track_cost(prompt, output_text)
            
            logger.debug(f"Generated response in {processing_time:.2f}s")
            return output_text
            
        except Exception as e:
            logger.error(f"Gemma generation failed: {str(e)}")
            raise
    
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

class DocumentClassificationAgent(GemmaAgent):
    """Agent 1: Classifies document types and routes to appropriate processor"""
    
    def __init__(self, api_key: str = None):
        # Use smaller model for classification (cost optimization)
        super().__init__("gemma-2-2b-it", api_key)
        self.agent_type = AgentType.CLASSIFIER
    
    def classify_document(self, content: str) -> Dict[str, Any]:
        """Classify document type and determine processing route"""
        
        prompt = f"""TASK: Classify this document for booking processing.

DOCUMENT CONTENT:
{content[:2000]}  # Limit content for classification

CLASSIFICATION RULES:
1. SINGLE_BOOKING: Contains one passenger/trip (travel requisition forms, individual requests)
2. MULTI_BOOKING: Contains multiple passengers/trips in tables (team schedules, bulk requests)  
3. EXPENSE_REPORT: Contains expense/reimbursement information
4. FLIGHT_DETAILS: Contains primarily flight information
5. UNKNOWN: Unclear or not booking-related

OUTPUT FORMAT (JSON only):
{{
    "document_type": "SINGLE_BOOKING|MULTI_BOOKING|EXPENSE_REPORT|FLIGHT_DETAILS|UNKNOWN",
    "confidence": 0.95,
    "reasoning": "Brief explanation",
    "suggested_processor": "enhanced_form_processor|multi_booking_processor|expense_processor|flight_processor|manual_review",
    "complexity_level": "low|medium|high"
}}

CLASSIFY:"""

        try:
            response = self.generate_content(prompt, temperature=0.1)
            
            # Parse JSON response
            result = json.loads(response.strip())
            
            # Validate response format
            if not all(key in result for key in ['document_type', 'confidence', 'suggested_processor']):
                raise ValueError("Invalid classification response format")
            
            logger.info(f"Document classified as: {result['document_type']} (confidence: {result['confidence']:.1%})")
            return result
            
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Classification parsing failed: {str(e)}")
            # Return safe default
            return {
                'document_type': 'UNKNOWN',
                'confidence': 0.0,
                'reasoning': f'Classification parsing failed: {str(e)}',
                'suggested_processor': 'manual_review',
                'complexity_level': 'high'
            }

class BookingExtractionAgent(GemmaAgent):
    """Agent 2: Extracts structured booking data"""
    
    def __init__(self, api_key: str = None):
        # Use larger model for complex extraction
        super().__init__("gemma-2-9b-it", api_key)
        self.agent_type = AgentType.EXTRACTOR
    
    def extract_booking_data(self, content: str, document_type: str) -> Dict[str, Any]:
        """Extract structured booking information"""
        
        # Customize extraction prompt based on document type
        if document_type == "MULTI_BOOKING":
            extraction_prompt = self._get_multi_booking_prompt(content)
        else:
            extraction_prompt = self._get_single_booking_prompt(content)
        
        try:
            response = self.generate_content(extraction_prompt, temperature=0.1)
            
            # Parse JSON response
            result = json.loads(response.strip())
            
            logger.info(f"Extracted {len(result.get('bookings', []))} bookings")
            return result
            
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Extraction parsing failed: {str(e)}")
            return {
                'bookings': [],
                'extraction_success': False,
                'error': str(e)
            }
    
    def _get_single_booking_prompt(self, content: str) -> str:
        return f"""TASK: Extract booking information from this document.

DOCUMENT CONTENT:
{content}

EXTRACTION RULES:
- Extract passenger name, phone, travel dates, vehicle type, locations
- Normalize vehicle types (Dzire→Swift Dzire, Crysta→Toyota Innova Crysta)
- Format dates as YYYY-MM-DD
- Format times as HH:MM
- Clean phone numbers to 10 digits

OUTPUT FORMAT (JSON only):
{{
    "bookings": [
        {{
            "passenger_name": "string",
            "passenger_phone": "string",
            "corporate": "string",
            "start_date": "YYYY-MM-DD",
            "end_date": "YYYY-MM-DD", 
            "reporting_time": "HH:MM",
            "vehicle_group": "string",
            "from_location": "string",
            "to_location": "string",
            "reporting_address": "string",
            "drop_address": "string",
            "flight_train_number": "string",
            "duty_type": "string",
            "remarks": "string",
            "confidence_score": 0.95
        }}
    ],
    "total_bookings": 1,
    "extraction_success": true
}}

EXTRACT:"""

    def _get_multi_booking_prompt(self, content: str) -> str:
        return f"""TASK: Extract multiple bookings from this table/document.

DOCUMENT CONTENT:
{content}

TABLE FORMATS SUPPORTED:
1. HORIZONTAL: Cab 1, Cab 2, Cab 3... columns with passenger data
2. VERTICAL: Key-value pairs with multiple entries

EXTRACTION RULES:
- Each column or entry = one booking
- Map field names intelligently (Name of Employee→passenger_name)
- Handle multi-date ranges (20-21 Sep 2025)
- Normalize all vehicle types and field formats

OUTPUT FORMAT (JSON only):
{{
    "bookings": [
        {{
            "passenger_name": "string",
            "passenger_phone": "string", 
            "corporate": "string",
            "start_date": "YYYY-MM-DD",
            "reporting_time": "HH:MM",
            "vehicle_group": "string",
            "from_location": "string",
            "to_location": "string",
            "reporting_address": "string",
            "drop_address": "string",
            "flight_train_number": "string",
            "remarks": "string",
            "confidence_score": 0.90
        }}
    ],
    "total_bookings": 4,
    "extraction_success": true,
    "table_format": "horizontal|vertical"
}}

EXTRACT ALL BOOKINGS:"""

class ValidationAgent(GemmaAgent):
    """Agent 3: Validates and enhances extracted data"""
    
    def __init__(self, api_key: str = None):
        # Use smaller model for validation (cost optimization)
        super().__init__("gemma-2-2b-it", api_key)
        self.agent_type = AgentType.VALIDATOR
    
    def validate_and_enhance(self, extracted_data: Dict[str, Any], business_rules: Dict[str, Any] = None) -> Dict[str, Any]:
        """Validate extracted data and apply business rules"""
        
        prompt = f"""TASK: Validate and enhance booking data with business rules.

EXTRACTED DATA:
{json.dumps(extracted_data, indent=2)}

VALIDATION RULES:
1. Check required fields: passenger_name, start_date, reporting_time
2. Validate date formats (YYYY-MM-DD)
3. Validate phone numbers (10 digits)
4. Apply duty type rules:
   - "disposal", "at disposal" → Local disposal (08HR 80KMS)
   - "drop", "airport" → Drop service (04HR 40KMS)  
   - "outstation" → Outstation (250KMS)
5. Normalize vehicle types
6. Flag missing critical information

ENHANCEMENT RULES:
- Auto-fill end_date if missing (same as start_date for single day)
- Apply corporate duty type (G2G/P2P) based on company
- Calculate confidence scores based on completeness

OUTPUT FORMAT (JSON only):
{{
    "validated_bookings": [
        {{
            "passenger_name": "string",
            "passenger_phone": "string",
            "start_date": "YYYY-MM-DD",
            "duty_type": "P2P-08HR 80KMS",
            "confidence_score": 0.92,
            "validation_status": "valid|incomplete|invalid",
            "missing_fields": ["field1", "field2"],
            "warnings": ["warning1", "warning2"]
        }}
    ],
    "overall_validation": "passed|failed|partial",
    "total_valid_bookings": 3,
    "requires_manual_review": false
}}

VALIDATE:"""

        try:
            response = self.generate_content(prompt, temperature=0.1)
            result = json.loads(response.strip())
            
            valid_bookings = len([b for b in result.get('validated_bookings', []) 
                                if b.get('validation_status') == 'valid'])
            
            logger.info(f"Validated {valid_bookings}/{len(result.get('validated_bookings', []))} bookings")
            return result
            
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Validation parsing failed: {str(e)}")
            return {
                'validated_bookings': extracted_data.get('bookings', []),
                'overall_validation': 'failed',
                'error': str(e),
                'requires_manual_review': True
            }

class GemmaMultiAgentSystem:
    """Orchestrates the multi-agent booking processing pipeline"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key
        
        # Initialize agents
        self.classifier = DocumentClassificationAgent(api_key)
        self.extractor = BookingExtractionAgent(api_key) 
        self.validator = ValidationAgent(api_key)
        
        # Fallback to GPT-4o for complex cases (optional)
        self.gpt_fallback_available = False
        try:
            from car_rental_ai_agent import CarRentalAIAgent
            self.gpt_agent = CarRentalAIAgent()
            self.gpt_fallback_available = True
            logger.info("GPT-4o fallback available for complex cases")
        except:
            logger.info("GPT-4o fallback not available")
    
    def process_document(self, content: str, filename: str = "document") -> Dict[str, Any]:
        """Process document through complete multi-agent pipeline"""
        
        start_time = time.time()
        pipeline_result = {
            'filename': filename,
            'pipeline_stages': {},
            'final_result': {},
            'cost_breakdown': {},
            'processing_time': 0.0,
            'success': False
        }
        
        try:
            # Stage 1: Classification
            logger.info(f"🔍 Stage 1: Classifying document: {filename}")
            classification = self.classifier.classify_document(content)
            pipeline_result['pipeline_stages']['classification'] = classification
            
            # Check if we need GPT-4o fallback
            if (classification['complexity_level'] == 'high' or 
                classification['confidence'] < 0.7 or
                classification['document_type'] == 'UNKNOWN'):
                
                if self.gpt_fallback_available:
                    logger.info("⚠️  High complexity detected, using GPT-4o fallback")
                    return self._fallback_to_gpt(content, filename)
            
            # Stage 2: Extraction
            logger.info(f"📊 Stage 2: Extracting data (type: {classification['document_type']})")
            extraction = self.extractor.extract_booking_data(content, classification['document_type'])
            pipeline_result['pipeline_stages']['extraction'] = extraction
            
            if not extraction.get('extraction_success', False):
                raise ValueError("Extraction failed")
            
            # Stage 3: Validation
            logger.info(f"✅ Stage 3: Validating {len(extraction.get('bookings', []))} bookings")
            validation = self.validator.validate_and_enhance(extraction)
            pipeline_result['pipeline_stages']['validation'] = validation
            
            # Prepare final result
            final_bookings = validation.get('validated_bookings', [])
            pipeline_result['final_result'] = {
                'bookings': final_bookings,
                'total_bookings_found': len(final_bookings),
                'extraction_method': 'gemma_multi_agent',
                'confidence_score': self._calculate_overall_confidence(final_bookings),
                'processing_notes': f"Processed via Gemma multi-agent: {classification['document_type']}"
            }
            
            pipeline_result['success'] = True
            
        except Exception as e:
            logger.error(f"Pipeline failed: {str(e)}")
            pipeline_result['error'] = str(e)
            
            # Fallback to GPT-4o if available
            if self.gpt_fallback_available:
                logger.info("🔄 Falling back to GPT-4o due to pipeline failure")
                return self._fallback_to_gpt(content, filename)
        
        finally:
            # Calculate costs and timing
            pipeline_result['processing_time'] = time.time() - start_time
            pipeline_result['cost_breakdown'] = {
                'classifier': self.classifier.get_cost_summary(),
                'extractor': self.extractor.get_cost_summary(), 
                'validator': self.validator.get_cost_summary(),
                'total_cost_inr': (self.classifier.total_cost + 
                                 self.extractor.total_cost + 
                                 self.validator.total_cost)
            }
            
            logger.info(f"Pipeline completed in {pipeline_result['processing_time']:.2f}s, "
                      f"cost: ₹{pipeline_result['cost_breakdown']['total_cost_inr']:.4f}")
        
        return pipeline_result
    
    def _calculate_overall_confidence(self, bookings: List[Dict]) -> float:
        """Calculate overall confidence score"""
        if not bookings:
            return 0.0
        
        confidences = [b.get('confidence_score', 0.5) for b in bookings]
        return sum(confidences) / len(confidences)
    
    def _fallback_to_gpt(self, content: str, filename: str) -> Dict[str, Any]:
        """Fallback to GPT-4o for complex cases"""
        try:
            result = self.gpt_agent.extract_bookings(content)
            return {
                'filename': filename,
                'final_result': result,
                'extraction_method': 'gpt4o_fallback',
                'success': True,
                'cost_breakdown': {'note': 'GPT-4o fallback used - higher cost'},
                'processing_time': 0.0  # Not tracked for fallback
            }
        except Exception as e:
            logger.error(f"GPT-4o fallback also failed: {str(e)}")
            return {
                'filename': filename,
                'success': False,
                'error': f'Both Gemma pipeline and GPT-4o fallback failed: {str(e)}'
            }
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get overall system statistics"""
        total_requests = (self.classifier.request_count + 
                         self.extractor.request_count + 
                         self.validator.request_count)
        total_cost = (self.classifier.total_cost + 
                     self.extractor.total_cost + 
                     self.validator.total_cost)
        
        return {
            'total_requests': total_requests,
            'total_cost_inr': round(total_cost, 4),
            'avg_cost_per_document': round(total_cost / max(1, total_requests//3), 4),
            'agent_breakdown': {
                'classifier': self.classifier.get_cost_summary(),
                'extractor': self.extractor.get_cost_summary(),
                'validator': self.validator.get_cost_summary()
            }
        }

# Example usage and testing
def test_gemma_multi_agent():
    """Test the Gemma multi-agent system"""
    
    # Sample booking email
    sample_email = """
    Dear Team,
    
    Please arrange cab for Mr. Rajesh Kumar (9876543210) on 15th October 2025 at 10:30 AM.
    Pickup from Gurgaon office, drop at Delhi Airport.
    Vehicle: Innova Crysta
    This is for airport drop service.
    
    Company: Accenture India
    
    Thanks,
    Travel Desk
    """
    
    # Initialize system
    try:
        system = GemmaMultiAgentSystem()
        
        # Process document
        result = system.process_document(sample_email, "test_email.txt")
        
        # Print results
        print("🎯 GEMMA MULTI-AGENT RESULTS:")
        print(f"Success: {result['success']}")
        print(f"Processing time: {result['processing_time']:.2f}s")
        print(f"Total cost: ₹{result['cost_breakdown']['total_cost_inr']:.4f}")
        
        if result['success']:
            final_result = result['final_result']
            print(f"Bookings found: {final_result['total_bookings_found']}")
            print(f"Confidence: {final_result['confidence_score']:.1%}")
            
            for i, booking in enumerate(final_result['bookings'][:2]):  # Show first 2
                print(f"\nBooking {i+1}:")
                print(f"  Passenger: {booking.get('passenger_name')}")
                print(f"  Phone: {booking.get('passenger_phone')}")
                print(f"  Date: {booking.get('start_date')}")
                print(f"  Vehicle: {booking.get('vehicle_group')}")
        
        # System stats
        stats = system.get_system_stats()
        print(f"\n📊 SYSTEM STATS:")
        print(f"Average cost per document: ₹{stats['avg_cost_per_document']}")
        print(f"Projected monthly cost (5k docs): ₹{stats['avg_cost_per_document'] * 5000:.2f}")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        print("Make sure to set GOOGLE_AI_API_KEY environment variable")

if __name__ == "__main__":
    test_gemma_multi_agent()