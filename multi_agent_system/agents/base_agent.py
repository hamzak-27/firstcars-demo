"""
Base Agent Framework for Multi-Agent System
Provides common functionality and interface for all agents
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Union
from enum import Enum
import time
import logging
import json

logger = logging.getLogger(__name__)


class AgentType(Enum):
    """Types of agents in the system"""
    CLASSIFICATION = "classification"
    SINGLE_BOOKING = "single_booking"
    MULTIPLE_BOOKING = "multiple_booking"
    VALIDATION = "validation"


@dataclass
class AgentResult:
    """Standardized result format for all agents"""
    agent_type: AgentType
    success: bool
    data: Dict[str, Any]
    confidence_score: float
    processing_time: float
    cost_estimate: float
    
    # Optional metadata
    metadata: Dict[str, Any] = None
    error_message: Optional[str] = None
    warnings: List[str] = None
    next_agent_guidance: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.warnings is None:
            self.warnings = []


class BaseAgent(ABC):
    """Base class for all specialized agents"""
    
    def __init__(self, agent_type: AgentType, model_config: Dict[str, Any] = None):
        """
        Initialize base agent
        
        Args:
            agent_type: Type of this agent
            model_config: Configuration for the AI model
        """
        self.agent_type = agent_type
        self.model_config = model_config or {}
        self.system_prompt = self._build_system_prompt()
        
        # Initialize logging
        self.logger = logging.getLogger(f"{self.__class__.__name__}")
        
        # Performance tracking
        self.call_count = 0
        self.total_processing_time = 0.0
        self.total_cost = 0.0
    
    @abstractmethod
    def _build_system_prompt(self) -> str:
        """Build the system prompt for this agent"""
        pass
    
    @abstractmethod
    def _process_internal(self, input_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Internal processing logic - to be implemented by each agent
        
        Args:
            input_data: Input data for processing
            context: Additional context from previous agents
            
        Returns:
            Dictionary with processing results
        """
        pass
    
    def process(self, input_data: Dict[str, Any], context: Dict[str, Any] = None) -> AgentResult:
        """
        Process input data and return standardized result
        
        Args:
            input_data: Input data for processing
            context: Additional context from previous agents
            
        Returns:
            AgentResult with processing outcome
        """
        start_time = time.time()
        context = context or {}
        
        try:
            self.logger.info(f"Starting {self.agent_type.value} agent processing")
            
            # Validate input
            self._validate_input(input_data)
            
            # Execute agent-specific processing
            result_data = self._process_internal(input_data, context)
            
            # Calculate metrics
            processing_time = time.time() - start_time
            confidence_score = self._calculate_confidence_score(result_data)
            cost_estimate = self._estimate_cost(input_data, result_data)
            
            # Update performance tracking
            self.call_count += 1
            self.total_processing_time += processing_time
            self.total_cost += cost_estimate
            
            # Generate next agent guidance
            next_agent_guidance = self._generate_next_agent_guidance(result_data)
            
            # Create successful result
            result = AgentResult(
                agent_type=self.agent_type,
                success=True,
                data=result_data,
                confidence_score=confidence_score,
                processing_time=processing_time,
                cost_estimate=cost_estimate,
                metadata=self._generate_metadata(input_data, result_data, processing_time),
                next_agent_guidance=next_agent_guidance
            )
            
            self.logger.info(f"{self.agent_type.value} agent completed successfully. "
                           f"Time: {processing_time:.2f}s, Confidence: {confidence_score:.2f}")
            
            return result
            
        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = str(e)
            
            self.logger.error(f"{self.agent_type.value} agent failed: {error_msg}")
            
            # Create error result
            return AgentResult(
                agent_type=self.agent_type,
                success=False,
                data={},
                confidence_score=0.0,
                processing_time=processing_time,
                cost_estimate=0.0,
                error_message=error_msg,
                metadata={'error_details': error_msg}
            )
    
    def _validate_input(self, input_data: Dict[str, Any]):
        """Validate input data - can be overridden by subclasses"""
        if not input_data:
            raise ValueError("Input data cannot be empty")
    
    def _calculate_confidence_score(self, result_data: Dict[str, Any]) -> float:
        """Calculate confidence score - can be overridden by subclasses"""
        return result_data.get('confidence_score', 0.8)
    
    def _estimate_cost(self, input_data: Dict[str, Any], result_data: Dict[str, Any]) -> float:
        """Estimate processing cost - can be overridden by subclasses"""
        # Base estimation - subclasses should implement actual cost calculation
        return 0.01
    
    def _generate_metadata(self, input_data: Dict[str, Any], result_data: Dict[str, Any], 
                          processing_time: float) -> Dict[str, Any]:
        """Generate metadata for result"""
        return {
            'agent_type': self.agent_type.value,
            'input_size': len(str(input_data)),
            'output_size': len(str(result_data)),
            'processing_time': processing_time,
            'call_count': self.call_count,
            'timestamp': time.time()
        }
    
    def _generate_next_agent_guidance(self, result_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate guidance for next agent - can be overridden by subclasses"""
        return None
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics for this agent"""
        avg_time = self.total_processing_time / max(self.call_count, 1)
        avg_cost = self.total_cost / max(self.call_count, 1)
        
        return {
            'agent_type': self.agent_type.value,
            'total_calls': self.call_count,
            'total_processing_time': self.total_processing_time,
            'average_processing_time': avg_time,
            'total_cost': self.total_cost,
            'average_cost': avg_cost
        }
    
    def reset_stats(self):
        """Reset performance statistics"""
        self.call_count = 0
        self.total_processing_time = 0.0
        self.total_cost = 0.0
    
    def _parse_json_response(self, response_text: str) -> Dict[str, Any]:
        """Parse JSON response from AI model"""
        try:
            # Clean response text
            cleaned = response_text.strip()
            if cleaned.startswith('```json'):
                cleaned = cleaned.replace('```json', '').replace('```', '').strip()
            
            # Find JSON object boundaries
            start = cleaned.find('{')
            end = cleaned.rfind('}') + 1
            
            if start == -1 or end == 0:
                raise ValueError("No JSON object found in response")
            
            json_str = cleaned[start:end]
            return json.loads(json_str)
            
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON parsing failed: {str(e)}")
            self.logger.error(f"Response was: {response_text[:500]}...")
            raise ValueError(f"Invalid JSON in AI response: {str(e)}")
    
    def __str__(self) -> str:
        return f"{self.__class__.__name__}(type={self.agent_type.value})"
    
    def __repr__(self) -> str:
        return self.__str__()