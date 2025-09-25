"""
Multi-Agent System - Models Module
Shared data structures and models for inter-agent communication
"""

from .shared_models import (
    ClassificationResult,
    ExtractionContext,
    ValidationContext,
    ProcessingMetadata
)

__all__ = [
    'ClassificationResult',
    'ExtractionContext', 
    'ValidationContext',
    'ProcessingMetadata'
]