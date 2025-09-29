#!/usr/bin/env python3
"""
Complete Multi-Agent Orchestrator for Car Rental Bookings
Coordinates the entire pipeline: Classification → Extraction → Validation
"""

import logging
import time
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple

# Import all agents
from gemma_classification_agent import GemmaClassificationAgent, ClassificationResult
from extraction_router import ExtractionRouter
from business_logic_validation_agent import BusinessLogicValidationAgent
from base_extraction_agent import ExtractionResult

logger = logging.getLogger(__name__)

class CompleteMultiAgentOrchestrator:
    """
    Complete orchestrator for the multi-agent car rental booking system
    
    Pipeline Flow:
    1. Classification Agent (Gemma) → Determines single vs multiple bookings
    2. Extraction Router → Routes to appropriate extraction agent
    3. Single/Multiple Booking Agents (Gemma) → Extract structured data to DataFrame
    4. Business Logic Validation Agent → Apply business rules and enhance DataFrame
    
    Final Output: Validated DataFrame with all business rules applied
    """
    
    def __init__(self, api_key: str = None):
        """Initialize the complete multi-agent system"""
        
        self.api_key = api_key
        
        # Initialize all agents
        try:
            self.classification_agent = GemmaClassificationAgent(api_key=api_key)
            logger.info("✅ Classification agent initialized")
        except Exception as e:
            logger.error(f"❌ Classification agent failed: {str(e)}")
            self.classification_agent = None
        
        try:
            self.extraction_router = ExtractionRouter(api_key=api_key)
            logger.info("✅ Extraction router initialized")
        except Exception as e:
            logger.error(f"❌ Extraction router failed: {str(e)}")
            self.extraction_router = None
        
        try:
            self.validation_agent = BusinessLogicValidationAgent(api_key=api_key)
            logger.info("✅ Validation agent initialized")
        except Exception as e:
            logger.error(f"❌ Validation agent failed: {str(e)}")
            self.validation_agent = None
        
        # System statistics
        self.system_stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'total_cost_inr': 0.0,
            'total_processing_time': 0.0,
            'classification_stats': {'single': 0, 'multiple': 0},
            'agent_costs': {'classification': 0.0, 'extraction': 0.0, 'validation': 0.0}
        }
        
        logger.info("CompleteMultiAgentOrchestrator initialized")
    
    def process_content(self, content: str, source_type: str = "email") -> Dict[str, Any]:
        """
        Process content through the complete multi-agent pipeline
        
        Args:
            content: Email content or OCR extracted text
            source_type: Type of source ("email", "pdf", "image", "word_doc")
            
        Returns:
            Dict containing final DataFrame and processing metadata
        """
        
        pipeline_start_time = time.time()
        self.system_stats['total_requests'] += 1
        
        logger.info(f"🚀 Starting complete multi-agent processing ({source_type})")
        
        result = {
            'success': False,
            'final_dataframe': None,
            'booking_count': 0,
            'confidence_score': 0.0,
            'total_processing_time': 0.0,
            'total_cost_inr': 0.0,
            'pipeline_stages': {},
            'error_message': '',
            'metadata': {
                'source_type': source_type,
                'content_length': len(content),
                'agents_used': [],
                'pipeline_version': 'complete_multi_agent_v1.0'
            }
        }
        
        try:
            # Check if content is already processed by EnhancedMultiBookingProcessor
            if "TABLE EXTRACTION RESULTS" in content:
                logger.info("🎯 Detected preprocessed multi-booking content - bypassing classification")
                
                # Create mock classification for preprocessed content
                from gemma_classification_agent import BookingType, DutyType
                booking_count = content.count("Booking ") if "Booking " in content else 1
                
                class MockClassification:
                    def __init__(self):
                        self.booking_type = BookingType.MULTIPLE
                        self.booking_count = booking_count
                        self.confidence_score = 0.95
                        self.detected_duty_type = DutyType.DROP_4_40
                        self.cost_inr = 0.0
                        self.processing_time = 0.01
                
                classification_result = MockClassification()
                result['pipeline_stages']['classification'] = {
                    'agent': 'PreprocessedBypass',
                    'booking_type': 'multiple',
                    'booking_count': booking_count,
                    'confidence': 0.95,
                    'duty_type': 'drop_4_40',
                    'cost_inr': 0.0,
                    'processing_time': 0.01
                }
                
            else:
                # Stage 1: Classification
                logger.info("📊 Stage 1: Classification (Determining booking type)")
                
                if not self.classification_agent:
                    raise ValueError("Classification agent not available")
                
                classification_result = self.classification_agent.classify_content(content, source_type)
                result['pipeline_stages']['classification'] = {
                    'agent': 'GemmaClassificationAgent',
                    'booking_type': classification_result.booking_type.value,
                    'booking_count': classification_result.booking_count,
                    'confidence': classification_result.confidence_score,
                    'duty_type': classification_result.detected_duty_type.value,
                    'cost_inr': classification_result.cost_inr,
                    'processing_time': classification_result.processing_time
                }
            
            # Handle both enum and mock classification results
            if hasattr(classification_result.booking_type, 'value'):
                booking_type_str = classification_result.booking_type.value
            else:
                # For mock classifications, convert to string
                booking_type_str = str(classification_result.booking_type).replace('BookingType.', '').lower()
            
            # Ensure we have valid keys for stats
            if booking_type_str not in ['multiple', 'single']:
                if 'MULTIPLE' in str(booking_type_str).upper():
                    booking_type_str = 'multiple'
                else:
                    booking_type_str = 'single'
            
            self.system_stats['classification_stats'][booking_type_str] += 1
            self.system_stats['agent_costs']['classification'] += classification_result.cost_inr
            
            # Add agent name based on classification type
            if "TABLE EXTRACTION RESULTS" in content:
                result['metadata']['agents_used'].append('PreprocessedBypass')
            else:
                result['metadata']['agents_used'].append('GemmaClassificationAgent')
            
            logger.info(f"✅ Classification: {booking_type_str} "
                       f"({classification_result.booking_count} bookings)")
            
            # Stage 2: Extraction
            logger.info("📋 Stage 2: Extraction (Converting to structured DataFrame)")
            
            if not self.extraction_router:
                raise ValueError("Extraction router not available")
            
            extraction_result = self.extraction_router.route_and_extract(content, classification_result)
            result['pipeline_stages']['extraction'] = {
                'agent': extraction_result.metadata.get('agent_selected', 'Unknown') if extraction_result.metadata else 'Unknown',
                'booking_count': extraction_result.booking_count,
                'extraction_method': extraction_result.extraction_method,
                'confidence': extraction_result.confidence_score,
                'cost_inr': extraction_result.cost_inr,
                'processing_time': extraction_result.processing_time,
                'dataframe_shape': extraction_result.bookings_dataframe.shape if not extraction_result.bookings_dataframe.empty else (0, 0)
            }
            
            self.system_stats['agent_costs']['extraction'] += extraction_result.cost_inr
            agent_name = extraction_result.metadata.get('agent_selected', 'ExtractionAgent') if extraction_result.metadata else 'ExtractionAgent'
            result['metadata']['agents_used'].append(agent_name)
            
            if not extraction_result.success:
                raise ValueError(f"Extraction failed: {extraction_result.error_message}")
            
            logger.info(f"✅ Extraction: {extraction_result.booking_count} bookings → "
                       f"{extraction_result.bookings_dataframe.shape} DataFrame")
            
            # Stage 3: Business Logic Validation
            logger.info("🔧 Stage 3: Business Logic Validation (Applying business rules)")
            
            if not self.validation_agent:
                raise ValueError("Validation agent not available")
            
            validation_result = self.validation_agent.validate_and_enhance(
                extraction_result, classification_result, content
            )
            
            result['pipeline_stages']['validation'] = {
                'agent': 'BusinessLogicValidationAgent',
                'booking_count': validation_result.booking_count,
                'confidence': validation_result.confidence_score,
                'cost_inr': validation_result.cost_inr,
                'processing_time': validation_result.processing_time,
                'final_dataframe_shape': validation_result.bookings_dataframe.shape if not validation_result.bookings_dataframe.empty else (0, 0),
                'validation_applied': validation_result.metadata.get('validation_applied', False) if validation_result.metadata else False
            }
            
            self.system_stats['agent_costs']['validation'] += validation_result.cost_inr
            result['metadata']['agents_used'].append('BusinessLogicValidationAgent')
            
            if not validation_result.success:
                raise ValueError(f"Validation failed: {validation_result.error_message}")
            
            logger.info(f"✅ Validation: Enhanced DataFrame with business rules applied")
            
            # Prepare final result
            total_processing_time = time.time() - pipeline_start_time
            total_cost = (classification_result.cost_inr + extraction_result.cost_inr + 
                         validation_result.cost_inr)
            
            result.update({
                'success': True,
                'final_dataframe': validation_result.bookings_dataframe,
                'booking_count': validation_result.booking_count,
                'confidence_score': validation_result.confidence_score,
                'total_processing_time': total_processing_time,
                'total_cost_inr': total_cost,
                'metadata': {
                    **result['metadata'],
                    'pipeline_success': True,
                    'total_agents_used': len(result['metadata']['agents_used']),
                    'final_extraction_method': validation_result.extraction_method
                }
            })
            
            # Update system statistics
            self.system_stats['successful_requests'] += 1
            self.system_stats['total_cost_inr'] += total_cost
            self.system_stats['total_processing_time'] += total_processing_time
            
            logger.info(f"🎉 Pipeline completed successfully! "
                       f"{validation_result.booking_count} bookings processed in {total_processing_time:.2f}s "
                       f"(Cost: ₹{total_cost:.4f})")
            
            return result
            
        except Exception as e:
            # Handle pipeline failure
            total_processing_time = time.time() - pipeline_start_time
            self.system_stats['failed_requests'] += 1
            self.system_stats['total_processing_time'] += total_processing_time
            
            logger.error(f"❌ Pipeline failed: {str(e)}")
            
            result.update({
                'success': False,
                'error_message': str(e),
                'total_processing_time': total_processing_time,
                'metadata': {
                    **result['metadata'],
                    'pipeline_success': False,
                    'failure_reason': str(e)
                }
            })
            
            return result
    
    def get_system_statistics(self) -> Dict[str, Any]:
        """Get comprehensive system statistics"""
        
        stats = self.system_stats.copy()
        
        # Add derived statistics
        if stats['total_requests'] > 0:
            stats['success_rate'] = stats['successful_requests'] / stats['total_requests']
            stats['avg_cost_per_request'] = stats['total_cost_inr'] / stats['total_requests']
            stats['avg_processing_time'] = stats['total_processing_time'] / stats['total_requests']
        else:
            stats['success_rate'] = 0.0
            stats['avg_cost_per_request'] = 0.0
            stats['avg_processing_time'] = 0.0
        
        # Add agent-specific statistics
        if self.classification_agent:
            stats['agent_stats'] = {
                'classification_agent': self.classification_agent.get_cost_summary()
            }
        
        if self.extraction_router:
            stats['routing_stats'] = self.extraction_router.get_routing_stats()
        
        return stats
    
    def reset_statistics(self):
        """Reset system statistics"""
        self.system_stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'total_cost_inr': 0.0,
            'total_processing_time': 0.0,
            'classification_stats': {'single': 0, 'multiple': 0},
            'agent_costs': {'classification': 0.0, 'extraction': 0.0, 'validation': 0.0}
        }
        
        if self.extraction_router:
            self.extraction_router.reset_stats()
        
        logger.info("System statistics reset")

# Test the complete system
def test_complete_multi_agent_system():
    """Test the complete multi-agent system end-to-end"""
    
    print("🧪 Testing Complete Multi-Agent System...")
    print("=" * 80)
    
    # Initialize the complete system
    orchestrator = CompleteMultiAgentOrchestrator()
    
    # Test cases
    test_cases = [
        {
            "name": "Single Booking - Airport Drop",
            "content": """
            Dear Team,
            
            Please arrange a car for Mr. Rajesh Kumar (9876543210) tomorrow at 10:30 AM.
            From: Mumbai Office to Mumbai Airport
            Vehicle: Innova Crysta preferred
            Corporate: Accenture India Ltd
            Purpose: Airport drop service
            
            Thanks,
            Travel Coordinator
            """,
            "source_type": "email"
        },
        {
            "name": "Multiple Bookings - Team Travel",
            "content": """
            Multiple car bookings required:
            
            1. John Smith (9876543210) - 25th Dec - Delhi to Gurgaon - Local disposal - Dzire
            2. Mary Wilson (9876543211) - 26th Dec - Mumbai to Pune - Outstation - Innova
            3. Peter Kumar (9876543212) - 27th Dec - Bangalore Airport pickup - Drop service - Crysta
            
            Corporate: TechCorp India
            Separate bookings for each passenger.
            """,
            "source_type": "email"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📊 Test Case {i}: {test_case['name']}")
        print("-" * 60)
        
        try:
            # Process through complete pipeline
            result = orchestrator.process_content(
                test_case['content'], 
                test_case['source_type']
            )
            
            print(f"✅ Success: {result['success']}")
            print(f"📊 Bookings: {result['booking_count']}")
            print(f"🎯 Confidence: {result['confidence_score']:.1%}")
            print(f"⏱️ Total Time: {result['total_processing_time']:.2f}s")
            print(f"💰 Total Cost: ₹{result['total_cost_inr']:.4f}")
            print(f"🤖 Agents Used: {', '.join(result['metadata']['agents_used'])}")
            
            if result['success'] and result['final_dataframe'] is not None:
                df = result['final_dataframe']
                print(f"📋 Final DataFrame: {df.shape}")
                
                print("\n🔍 Sample Data:")
                for idx in range(min(2, len(df))):
                    print(f"  Booking {idx+1}:")
                    print(f"    Customer: {df.iloc[idx]['Customer']}")
                    print(f"    Passenger: {df.iloc[idx]['Passenger Name']}")
                    print(f"    Vehicle: {df.iloc[idx]['Vehicle Group']}")
                    print(f"    Duty Type: {df.iloc[idx]['Duty Type']}")
                    print(f"    From → To: {df.iloc[idx]['From (Service Location)']} → {df.iloc[idx]['To']}")
                    print(f"    Labels: {df.iloc[idx]['Labels']}")
            
            if result['error_message']:
                print(f"⚠️ Error: {result['error_message']}")
            
            # Show pipeline stages
            print(f"\n🔄 Pipeline Stages:")
            for stage, info in result['pipeline_stages'].items():
                print(f"  {stage.title()}: {info['agent']} "
                      f"(₹{info['cost_inr']:.4f}, {info['processing_time']:.2f}s)")
            
        except Exception as e:
            print(f"❌ Test case failed: {str(e)}")
    
    # Show system statistics
    print(f"\n📈 System Statistics:")
    print("=" * 80)
    
    stats = orchestrator.get_system_statistics()
    print(f"Total requests: {stats['total_requests']}")
    print(f"Success rate: {stats['success_rate']:.1%}")
    print(f"Avg cost per request: ₹{stats['avg_cost_per_request']:.4f}")
    print(f"Avg processing time: {stats['avg_processing_time']:.2f}s")
    print(f"Classification breakdown: Single={stats['classification_stats']['single']}, Multiple={stats['classification_stats']['multiple']}")
    print(f"Agent costs: Classification=₹{stats['agent_costs']['classification']:.4f}, "
          f"Extraction=₹{stats['agent_costs']['extraction']:.4f}, "
          f"Validation=₹{stats['agent_costs']['validation']:.4f}")

if __name__ == "__main__":
    test_complete_multi_agent_system()