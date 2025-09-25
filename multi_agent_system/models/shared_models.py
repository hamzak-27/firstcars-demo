"""
Shared Data Models for Multi-Agent System
Common data structures used for communication between agents
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union
from enum import Enum
from datetime import datetime


class BookingType(Enum):
    """Booking type classification"""
    SINGLE = "single"
    MULTIPLE = "multiple"


class UsageType(Enum):
    """Usage type for booking classification"""
    LOCAL = "local"
    OUTSTATION = "outstation"
    AIRPORT_TRANSFER = "airport_transfer"
    UNKNOWN = "unknown"


@dataclass
class ClassificationResult:
    """Result from booking classification agent"""
    booking_type: BookingType
    booking_count: int
    usage_type: UsageType
    confidence_score: float
    
    # Detailed analysis
    has_multiple_dates: bool = False
    has_multiple_passengers: bool = False
    has_multiple_locations: bool = False
    separate_passenger_bookings: bool = False
    
    # Supporting evidence
    detected_dates: List[str] = field(default_factory=list)
    detected_passengers: List[str] = field(default_factory=list)
    detected_locations: List[str] = field(default_factory=list)
    
    # Processing guidance for next agents
    processing_strategy: str = "standard"
    special_instructions: Dict[str, Any] = field(default_factory=dict)
    
    # Analysis reasoning
    reasoning: str = ""
    

@dataclass
class ExtractionContext:
    """Context passed to extraction agents"""
    classification_result: ClassificationResult
    original_content: str
    sender_email: Optional[str] = None
    document_type: Optional[str] = None
    processing_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationContext:
    """Context for validation agent"""
    extracted_bookings: List[Dict[str, Any]]
    classification_result: ClassificationResult
    extraction_confidence: float
    processing_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProcessingMetadata:
    """Metadata about the processing pipeline"""
    start_time: datetime = field(default_factory=datetime.now)
    agent_timings: Dict[str, float] = field(default_factory=dict)
    agent_costs: Dict[str, float] = field(default_factory=dict)
    processing_notes: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    
    def add_agent_timing(self, agent_name: str, duration: float):
        """Add timing for an agent"""
        self.agent_timings[agent_name] = duration
    
    def add_agent_cost(self, agent_name: str, cost: float):
        """Add cost for an agent"""
        self.agent_costs[agent_name] = cost
    
    def add_note(self, note: str):
        """Add processing note"""
        self.processing_notes.append(note)
    
    def add_warning(self, warning: str):
        """Add warning"""
        self.warnings.append(warning)
    
    def add_error(self, error: str):
        """Add error"""
        self.errors.append(error)
    
    def get_total_time(self) -> float:
        """Get total processing time"""
        return sum(self.agent_timings.values())
    
    def get_total_cost(self) -> float:
        """Get total processing cost"""
        return sum(self.agent_costs.values())