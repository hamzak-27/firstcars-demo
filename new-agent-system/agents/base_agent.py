"""
Base Agent Class
Template for all field-specific extraction agents
"""

import openai
import json
import logging
import pandas as pd
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    """
    Abstract base class for all field-specific extraction agents
    """
    
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        """Initialize base agent"""
        self.client = openai.OpenAI(api_key=api_key)
        self.model = model
        self.agent_name = self.__class__.__name__
        logger.info(f"{self.agent_name} initialized with model: {model}")
    
    @abstractmethod
    def get_target_fields(self) -> List[str]:
        """Return list of fields this agent is responsible for extracting"""
        pass
    
    @abstractmethod
    def build_extraction_prompt(self) -> str:
        """Build the specialized prompt for this agent"""
        pass
    
    def extract_fields(self, content: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract fields from content with context
        
        Args:
            content: Original email/document content
            context: Dictionary containing:
                - table_data: pandas DataFrame (if table processing)
                - booking_number: Current booking index
                - previous_results: Results from previous agents
                - document_type: 'email' or 'table'
                
        Returns:
            Dictionary with extracted field values
        """
        
        prompt = self.build_extraction_prompt()
        user_content = self._prepare_user_content(content, context)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": user_content}
                ],
                temperature=0.1,
                max_tokens=800
            )
            
            response_text = response.choices[0].message.content.strip()
            return self._parse_extraction_response(response_text)
            
        except Exception as e:
            logger.error(f"{self.agent_name} extraction failed: {str(e)}")
            return self._get_empty_result()
    
    def _prepare_user_content(self, content: str, context: Dict[str, Any]) -> str:
        """Prepare the user content with context information"""
        
        document_type = context.get('document_type', 'unknown')
        booking_number = context.get('booking_number', 0)
        previous_results = context.get('previous_results', {})
        
        user_content = f"""
**DOCUMENT TYPE:** {document_type}
**BOOKING NUMBER:** {booking_number + 1}

**ORIGINAL CONTENT:**
{content}

**CONTEXT FROM PREVIOUS AGENTS:**
{json.dumps(previous_results, indent=2) if previous_results else "No previous results"}
"""
        
        # Add table-specific context if available
        if document_type == 'table':
            table_data = context.get('table_data')
            if table_data is not None:
                try:
                    # Handle both DataFrame and dict formats
                    if hasattr(table_data, 'columns'):
                        # It's a DataFrame
                        user_content += f"""

**TABLE STRUCTURE:**
Columns: {list(table_data.columns)}
Shape: {table_data.shape}

**TABLE DATA:**
{table_data.to_string()}
"""
                    else:
                        # It's a dict or other format
                        user_content += f"""

**TABLE DATA (Dictionary format):**
{str(table_data)}
"""
                except Exception as e:
                    # Fallback to string representation
                    user_content += f"""

**TABLE DATA (Raw):**
{str(table_data)}
"""
        
        return user_content
    
    def _parse_extraction_response(self, response_text: str) -> Dict[str, Any]:
        """Parse the AI response into field dictionary"""
        
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
                
                # Filter to only include fields this agent is responsible for
                target_fields = self.get_target_fields()
                filtered_result = {}
                
                for field in target_fields:
                    if field in result_data:
                        value = result_data[field]
                        # Convert null/none strings to None
                        if isinstance(value, str) and value.lower() in ['null', 'none', 'na', 'not available', '']:
                            filtered_result[field] = None
                        else:
                            filtered_result[field] = value
                    else:
                        filtered_result[field] = None
                
                return filtered_result
            
        except json.JSONDecodeError as e:
            logger.error(f"{self.agent_name} failed to parse JSON response: {e}")
        except Exception as e:
            logger.error(f"{self.agent_name} error parsing response: {e}")
        
        # Return empty result if parsing fails
        return self._get_empty_result()
    
    def _get_empty_result(self) -> Dict[str, Any]:
        """Return empty result dictionary for this agent's fields"""
        target_fields = self.get_target_fields()
        return {field: None for field in target_fields}
    
    def process_booking_data(self, booking_data: dict, shared_context: dict) -> dict:
        """
        Process booking data through this agent
        
        Args:
            booking_data: Dictionary containing booking information
            shared_context: Shared context from orchestrator
            
        Returns:
            Dictionary with processing results
        """
        try:
            # Extract content based on data type
            if booking_data['source_type'] == 'email':
                content = booking_data['email_content']
            else:
                content = str(booking_data.get('table_data', {}))
            
            # Prepare context for this agent
            context = {
                'document_type': booking_data['source_type'],
                'booking_number': booking_data['booking_index'],
                'previous_results': shared_context.get('extracted_data', {}).get(booking_data['booking_index'], {}),
                'table_data': booking_data.get('table_data')
            }
            
            # Extract fields using this agent
            extracted_fields = self.extract_fields(content, context)
            
            logger.info(f"{self.agent_name} extracted fields: {list(extracted_fields.keys())}")
            
            return {
                'success': True,
                'extracted_fields': extracted_fields,
                'agent_name': self.agent_name
            }
            
        except Exception as e:
            logger.error(f"{self.agent_name} processing failed: {e}")
            return {
                'success': False,
                'extracted_fields': self._get_empty_result(),
                'agent_name': self.agent_name,
                'error': str(e)
            }
    
    def get_standard_field_instructions(self) -> str:
        """Common field processing instructions for all agents"""
        return """
**FIELD PROCESSING RULES:**
- Use null for missing information (do not guess)
- Clean and normalize data (remove extra spaces, fix formatting)
- Phone numbers: Remove +91, spaces, hyphens (keep 10 digits only)
- Dates: Convert to YYYY-MM-DD format
- Times: Convert to HH:MM 24-hour format
- City names: Use city name only (not full addresses)
- Vehicle names: Use standard names (Dzire → Swift Dzire, Innova → Toyota Innova Crysta)
"""
