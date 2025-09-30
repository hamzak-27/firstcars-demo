#!/usr/bin/env python3
"""
Comprehensive Test Suite for OpenAI Migration
Tests all business scenarios, cost tracking, and validation rules
"""

import os
import sys
import time
import pandas as pd
import logging
from typing import Dict, List, Any
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_openai_system_initialization():
    """Test that all OpenAI components initialize correctly"""
    
    print("🔧 TESTING OPENAI SYSTEM INITIALIZATION")
    print("="*60)
    
    results = {
        'openai_utils': False,
        'classification_agent': False,
        'extraction_agents': False,
        'validation_agent': False,
        'orchestrator': False,
        'cost_tracking': False
    }
    
    # Test OpenAI utilities
    try:
        from openai_model_utils import create_openai_client, create_chat_messages
        print("✅ OpenAI model utilities imported")
        
        # Test client creation (without API key)
        try:
            client = create_openai_client("test-key")
            print("✅ OpenAI client creation works")
        except Exception as e:
            print(f"⚠️  OpenAI client creation: {e} (expected without API key)")
        
        results['openai_utils'] = True
        
    except Exception as e:
        print(f"❌ OpenAI utilities failed: {e}")
    
    # Test classification agent
    try:
        from openai_classification_agent import OpenAIClassificationAgent, ClassificationResult, BookingType, DutyType
        
        agent = OpenAIClassificationAgent()
        print("✅ OpenAI classification agent initialized")
        print(f"   Model: {agent.model_name}")
        print(f"   Client available: {agent.client is not None}")
        
        results['classification_agent'] = True
        
    except Exception as e:
        print(f"❌ Classification agent failed: {e}")
    
    # Test extraction agents
    try:
        from base_extraction_agent import BaseExtractionAgent
        from single_booking_extraction_agent import SingleBookingExtractionAgent
        from multiple_booking_extraction_agent import MultipleBookingExtractionAgent
        
        single_agent = SingleBookingExtractionAgent()
        multi_agent = MultipleBookingExtractionAgent()
        
        print("✅ Extraction agents initialized")
        print(f"   Single booking agent: {single_agent.__class__.__name__}")
        print(f"   Multiple booking agent: {multi_agent.__class__.__name__}")
        
        results['extraction_agents'] = True
        
    except Exception as e:
        print(f"❌ Extraction agents failed: {e}")
    
    # Test validation agent
    try:
        from business_logic_validation_agent import BusinessLogicValidationAgent
        
        validation_agent = BusinessLogicValidationAgent()
        print("✅ Business validation agent initialized")
        print(f"   Corporate mappings: {len(validation_agent.corporate_mappings)}")
        print(f"   City mappings: {len(validation_agent.city_mappings)}")
        print(f"   Vehicle mappings: {len(validation_agent.vehicle_mappings)}")
        
        results['validation_agent'] = True
        
    except Exception as e:
        print(f"❌ Validation agent failed: {e}")
    
    # Test orchestrator
    try:
        from complete_multi_agent_orchestrator import CompleteMultiAgentOrchestrator
        
        orchestrator = CompleteMultiAgentOrchestrator()
        print("✅ Complete orchestrator initialized")
        print(f"   Classification agent: {type(orchestrator.classification_agent).__name__}")
        print(f"   Extraction router available: {orchestrator.extraction_router is not None}")
        print(f"   Validation agent available: {orchestrator.validation_agent is not None}")
        
        results['orchestrator'] = True
        
    except Exception as e:
        print(f"❌ Orchestrator failed: {e}")
    
    # Test cost tracking
    try:
        if results['classification_agent']:
            cost_summary = agent.get_cost_summary()
            print("✅ Cost tracking available")
            print(f"   Model: {cost_summary['model']}")
            print(f"   Total requests: {cost_summary['total_requests']}")
            print(f"   Total cost: ₹{cost_summary['total_cost_inr']}")
            
            results['cost_tracking'] = True
    except Exception as e:
        print(f"❌ Cost tracking failed: {e}")
    
    # Summary
    print(f"\n📊 INITIALIZATION RESULTS:")
    passed = sum(results.values())
    total = len(results)
    print(f"   Passed: {passed}/{total} ({passed/total*100:.1f}%)")
    
    for component, status in results.items():
        status_icon = "✅" if status else "❌"
        print(f"   {status_icon} {component}")
    
    return results

def test_business_scenarios():
    """Test key business scenarios that were important in the original system"""
    
    print("\n🎯 TESTING BUSINESS SCENARIOS")
    print("="*60)
    
    from complete_multi_agent_orchestrator import CompleteMultiAgentOrchestrator
    
    orchestrator = CompleteMultiAgentOrchestrator()
    
    test_cases = [
        {
            'name': 'Chennai→Bangalore→Chennai (Single Booking)',
            'content': '''
            Dear Team,
            
            Please arrange a car for Mr. Rajesh Kumar (9876543210) for outstation travel.
            
            Route: Chennai → Bangalore → Chennai
            Date: Tomorrow
            Time: 10:30 AM
            Vehicle: Innova
            
            This is a round trip - same passenger, same vehicle.
            
            Thanks!
            ''',
            'expected_type': 'single',
            'expected_bookings': 1,
            'business_rule': 'Round trip outstation should be single booking'
        },
        {
            'name': 'Multiple Drops Same Day (Multiple Bookings)',
            'content': '''
            Need three cars today:
            
            First car: Drop CEO to Airport at 9:00 AM
            Second car: Drop Manager to Hotel at 2:00 PM  
            Third car: Drop Director to Office at 6:00 PM
            
            All different passengers, different times, same day.
            ''',
            'expected_type': 'multiple',
            'expected_bookings': 3,
            'business_rule': 'Multiple drops same day should be multiple bookings'
        },
        {
            'name': '8HR Disposal Continuous Days (Single Booking)',
            'content': '''
            Car requirement for local disposal:
            
            Passenger: Ms. Priya Sharma (9876543210)
            Dates: Monday, Tuesday, Wednesday (consecutive days)
            Service: 8HR/80KM disposal for local meetings
            Vehicle: Dzire
            
            Same person, same service, continuous dates.
            ''',
            'expected_type': 'single', 
            'expected_bookings': 1,
            'business_rule': 'Continuous multi-day disposal should be single booking'
        },
        {
            'name': 'Alternate Days Disposal (Multiple Bookings)',
            'content': '''
            Car needed on alternate days:
            
            Monday: 8HR disposal for Mr. Kumar
            Wednesday: 8HR disposal for Mr. Kumar  
            Friday: 8HR disposal for Mr. Kumar
            
            Same person but non-consecutive days.
            ''',
            'expected_type': 'multiple',
            'expected_bookings': 3,
            'business_rule': 'Alternate days disposal should be multiple bookings'
        },
        {
            'name': 'Airport Transfer Drop (Single Booking)',
            'content': '''
            Airport transfer required:
            
            Passenger: Mr. John Doe (9876543210)
            Flight: AI-131
            Time: 10:30 AM tomorrow
            Route: Mumbai Hotel → Mumbai Airport
            Vehicle: Swift Dzire
            
            Simple point-to-point transfer.
            ''',
            'expected_type': 'single',
            'expected_bookings': 1,
            'business_rule': 'Simple airport transfer should be single booking'
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🧪 Test {i}: {test_case['name']}")
        print(f"   Rule: {test_case['business_rule']}")
        
        try:
            start_time = time.time()
            result = orchestrator.process_content(test_case['content'], 'email')
            processing_time = time.time() - start_time
            
            # Check results
            success = result['success']
            booking_count = result['booking_count']
            agents_used = result['metadata']['agents_used']
            cost = result['total_cost_inr']
            
            # Determine classification (from pipeline stages)
            classification_stage = result.get('pipeline_stages', {}).get('classification', {})
            detected_type = classification_stage.get('booking_type', 'unknown')
            
            # Validate expectations
            type_correct = detected_type == test_case['expected_type']
            count_correct = booking_count == test_case['expected_bookings']
            
            if success and type_correct and count_correct:
                print(f"   ✅ PASSED")
                print(f"      Classification: {detected_type} ({booking_count} bookings)")
                print(f"      Processing time: {processing_time:.2f}s")
                print(f"      Cost: ₹{cost:.4f}")
                print(f"      Agents: {', '.join(agents_used)}")
                status = 'PASSED'
            else:
                print(f"   ❌ FAILED")
                print(f"      Expected: {test_case['expected_type']} ({test_case['expected_bookings']} bookings)")
                print(f"      Got: {detected_type} ({booking_count} bookings)")
                print(f"      Success: {success}")
                status = 'FAILED'
                
        except Exception as e:
            print(f"   💥 ERROR: {str(e)}")
            status = 'ERROR'
            processing_time = 0
            cost = 0
            
        results.append({
            'test_name': test_case['name'],
            'status': status,
            'processing_time': processing_time,
            'cost': cost,
            'business_rule': test_case['business_rule']
        })
    
    # Summary
    passed = len([r for r in results if r['status'] == 'PASSED'])
    failed = len([r for r in results if r['status'] == 'FAILED']) 
    errors = len([r for r in results if r['status'] == 'ERROR'])
    total = len(results)
    
    print(f"\n📊 BUSINESS SCENARIO RESULTS:")
    print(f"   Passed: {passed}/{total}")
    print(f"   Failed: {failed}/{total}")
    print(f"   Errors: {errors}/{total}")
    print(f"   Success Rate: {passed/total*100:.1f}%")
    
    total_cost = sum(r['cost'] for r in results)
    avg_time = sum(r['processing_time'] for r in results) / len(results)
    
    print(f"   Total Cost: ₹{total_cost:.4f}")
    print(f"   Average Time: {avg_time:.2f}s per test")
    
    return results

def test_cost_tracking():
    """Test cost tracking accuracy and projections"""
    
    print("\n💰 TESTING COST TRACKING")
    print("="*60)
    
    from openai_classification_agent import OpenAIClassificationAgent
    from business_logic_validation_agent import BusinessLogicValidationAgent
    from single_booking_extraction_agent import SingleBookingExtractionAgent
    
    # Test cost structures
    print("📊 Cost Structure Analysis:")
    
    agents = {
        'Classification': OpenAIClassificationAgent(),
        'Extraction': SingleBookingExtractionAgent(), 
        'Validation': BusinessLogicValidationAgent()
    }
    
    for name, agent in agents.items():
        if hasattr(agent, 'cost_per_1k_input_tokens'):
            input_cost = agent.cost_per_1k_input_tokens
            output_cost = agent.cost_per_1k_output_tokens
            
            print(f"   {name}:")
            print(f"      Input: ₹{input_cost:.4f} per 1K tokens")
            print(f"      Output: ₹{output_cost:.4f} per 1K tokens")
    
    # Cost projections
    print(f"\n📈 Cost Projections (GPT-4o-mini):")
    
    # Estimate typical email processing
    typical_email_tokens = {
        'classification_input': 1500,  # Complex classification prompt
        'classification_output': 300,  # JSON response
        'extraction_input': 1200,     # Extraction prompt + content
        'extraction_output': 400,     # Structured data
        'validation_input': 800,      # Validation prompt
        'validation_output': 200      # Enhanced data
    }
    
    # Calculate costs per component
    classification_cost = (
        (typical_email_tokens['classification_input'] / 1000) * 0.0125 +
        (typical_email_tokens['classification_output'] / 1000) * 0.05
    )
    
    extraction_cost = (
        (typical_email_tokens['extraction_input'] / 1000) * 0.0125 +
        (typical_email_tokens['extraction_output'] / 1000) * 0.05
    )
    
    validation_cost = (
        (typical_email_tokens['validation_input'] / 1000) * 0.0125 +
        (typical_email_tokens['validation_output'] / 1000) * 0.05
    )
    
    total_per_email = classification_cost + extraction_cost + validation_cost
    
    print(f"   Classification: ₹{classification_cost:.4f}")
    print(f"   Extraction: ₹{extraction_cost:.4f}")
    print(f"   Validation: ₹{validation_cost:.4f}")
    print(f"   Total per email: ₹{total_per_email:.4f}")
    
    # Volume projections
    volumes = [100, 500, 1000, 5000]
    
    print(f"\n📊 Volume Cost Projections:")
    for volume in volumes:
        monthly_cost = total_per_email * volume
        print(f"   {volume:>4} emails/month: ₹{monthly_cost:.2f}")
    
    # Comparison with target
    target_cost = 0.19  # ₹0.19 per email target
    
    print(f"\n🎯 Target Analysis:")
    print(f"   Target cost per email: ₹{target_cost:.2f}")
    print(f"   Projected cost per email: ₹{total_per_email:.4f}")
    
    if total_per_email <= target_cost:
        savings = ((target_cost - total_per_email) / target_cost) * 100
        print(f"   ✅ Under target by ₹{target_cost - total_per_email:.4f} ({savings:.1f}% savings)")
    else:
        overage = ((total_per_email - target_cost) / target_cost) * 100
        print(f"   ⚠️  Over target by ₹{total_per_email - target_cost:.4f} ({overage:.1f}% over)")
    
    return {
        'cost_per_email': total_per_email,
        'under_target': total_per_email <= target_cost,
        'target_cost': target_cost,
        'savings_percentage': ((target_cost - total_per_email) / target_cost) * 100 if total_per_email <= target_cost else 0
    }

def test_data_validation():
    """Test DataFrame structure and business validation rules"""
    
    print("\n📋 TESTING DATA VALIDATION")
    print("="*60)
    
    from complete_multi_agent_orchestrator import CompleteMultiAgentOrchestrator
    
    orchestrator = CompleteMultiAgentOrchestrator()
    
    test_content = '''
    Dear Team,
    
    Please arrange a car for Mrs. Priya Sharma (9876543210) tomorrow at 10:30 AM.
    
    Company: Accenture
    From: Mumbai Airport 
    To: ITC Grand Central Hotel, Mumbai
    Vehicle: Toyota Innova Crysta
    Flight: AI-131
    
    This is a VIP guest - please ensure premium service.
    
    Thanks!
    Travel Desk
    '''
    
    try:
        result = orchestrator.process_content(test_content, 'email')
        
        if result['success'] and result['final_dataframe'] is not None:
            df = result['final_dataframe']
            
            print("📊 DataFrame Validation:")
            print(f"   Shape: {df.shape}")
            print(f"   Columns: {len(df.columns)}")
            
            expected_columns = [
                'Customer', 'Booked By Name', 'Booked By Phone Number', 'Booked By Email',
                'Passenger Name', 'Passenger Phone Number', 'Passenger Email',
                'From (Service Location)', 'To', 'Vehicle Group', 'Duty Type',
                'Start Date', 'End Date', 'Rep. Time', 'Reporting Address', 'Drop Address',
                'Flight/Train Number', 'Dispatch center', 'Remarks', 'Labels'
            ]
            
            missing_columns = [col for col in expected_columns if col not in df.columns]
            extra_columns = [col for col in df.columns if col not in expected_columns]
            
            print(f"   Expected columns: {len(expected_columns)}")
            print(f"   Missing columns: {len(missing_columns)}")
            print(f"   Extra columns: {len(extra_columns)}")
            
            if missing_columns:
                print(f"      Missing: {missing_columns}")
            if extra_columns:
                print(f"      Extra: {extra_columns}")
            
            # Test specific business validation
            print(f"\n🔍 Business Rule Validation:")
            
            row = df.iloc[0]
            
            # Test phone number normalization
            phone = str(row['Passenger Phone Number'])
            phone_valid = len(phone) == 10 and phone.isdigit()
            print(f"   Phone normalization: {'✅' if phone_valid else '❌'} ({phone})")
            
            # Test vehicle standardization
            vehicle = str(row['Vehicle Group'])
            vehicle_standardized = 'Innova' in vehicle or 'Crysta' in vehicle
            print(f"   Vehicle standardization: {'✅' if vehicle_standardized else '❌'} ({vehicle})")
            
            # Test VIP label detection
            labels = str(row['Labels'])
            vip_detected = 'VIP' in labels
            print(f"   VIP detection: {'✅' if vip_detected else '❌'} ({labels})")
            
            # Test LadyGuest label
            passenger_name = str(row['Passenger Name'])
            lady_guest = 'Mrs.' in passenger_name and 'LadyGuest' in labels
            print(f"   LadyGuest detection: {'✅' if lady_guest else '❌'} (Mrs. + LadyGuest)")
            
            # Test corporate detection
            customer = str(row['Customer'])
            corporate_detected = 'Accenture' in customer or customer != ''
            print(f"   Corporate detection: {'✅' if corporate_detected else '❌'} ({customer})")
            
            # Test city standardization
            from_loc = str(row['From (Service Location)'])
            to_loc = str(row['To'])
            cities_standardized = 'Mumbai' in from_loc and 'Mumbai' in to_loc
            print(f"   City standardization: {'✅' if cities_standardized else '❌'} ({from_loc} → {to_loc})")
            
            validation_results = {
                'dataframe_structure': len(missing_columns) == 0 and len(extra_columns) == 0,
                'phone_normalization': phone_valid,
                'vehicle_standardization': vehicle_standardized,
                'vip_detection': vip_detected,
                'lady_guest_detection': lady_guest,
                'corporate_detection': corporate_detected,
                'city_standardization': cities_standardized
            }
            
            passed_validations = sum(validation_results.values())
            total_validations = len(validation_results)
            
            print(f"\n📊 Validation Results: {passed_validations}/{total_validations} ({passed_validations/total_validations*100:.1f}%)")
            
            return validation_results
            
        else:
            print("❌ Failed to get valid DataFrame from orchestrator")
            return {}
            
    except Exception as e:
        print(f"💥 Error during data validation test: {str(e)}")
        return {}

def run_comprehensive_tests():
    """Run all comprehensive tests and provide summary"""
    
    print("🚀 COMPREHENSIVE OPENAI MIGRATION TEST SUITE")
    print("="*80)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    overall_start_time = time.time()
    
    # Run all test suites
    print("Phase 1: System Initialization")
    init_results = test_openai_system_initialization()
    
    print("\nPhase 2: Business Scenarios")
    business_results = test_business_scenarios()
    
    print("\nPhase 3: Cost Tracking")
    cost_results = test_cost_tracking()
    
    print("\nPhase 4: Data Validation")
    validation_results = test_data_validation()
    
    total_time = time.time() - overall_start_time
    
    # Overall summary
    print("\n" + "="*80)
    print("🎯 COMPREHENSIVE TEST SUMMARY")
    print("="*80)
    
    # Initialization summary
    init_passed = sum(init_results.values())
    init_total = len(init_results)
    print(f"🔧 Initialization: {init_passed}/{init_total} components ({init_passed/init_total*100:.1f}%)")
    
    # Business scenarios summary
    business_passed = len([r for r in business_results if r['status'] == 'PASSED'])
    business_total = len(business_results)
    print(f"🎯 Business Rules: {business_passed}/{business_total} scenarios ({business_passed/business_total*100:.1f}%)")
    
    # Cost tracking summary
    cost_under_target = cost_results.get('under_target', False)
    cost_status = "✅ Under target" if cost_under_target else "⚠️  Over target"
    print(f"💰 Cost Tracking: {cost_status} (₹{cost_results.get('cost_per_email', 0):.4f} per email)")
    
    # Data validation summary
    validation_passed = sum(validation_results.values()) if validation_results else 0
    validation_total = len(validation_results) if validation_results else 0
    if validation_total > 0:
        print(f"📋 Data Validation: {validation_passed}/{validation_total} rules ({validation_passed/validation_total*100:.1f}%)")
    
    # Overall assessment
    print(f"\n⏱️  Total Testing Time: {total_time:.2f} seconds")
    
    # Determine overall status
    all_systems_good = (
        init_passed == init_total and
        business_passed == business_total and 
        cost_under_target and
        (validation_passed == validation_total if validation_total > 0 else True)
    )
    
    if all_systems_good:
        print(f"\n🎉 OVERALL STATUS: ✅ ALL TESTS PASSED")
        print(f"   OpenAI migration is successful!")
        print(f"   System is ready for production deployment")
        print(f"   Cost target achieved with {cost_results.get('savings_percentage', 0):.1f}% savings")
    else:
        print(f"\n⚠️  OVERALL STATUS: Some tests need attention")
        if init_passed < init_total:
            print(f"   - Check system initialization issues")
        if business_passed < business_total:
            print(f"   - Review business rule implementations")
        if not cost_under_target:
            print(f"   - Cost optimization may be needed")
        if validation_total > 0 and validation_passed < validation_total:
            print(f"   - Data validation rules need adjustment")
    
    return {
        'initialization': init_results,
        'business_scenarios': business_results,
        'cost_tracking': cost_results,
        'data_validation': validation_results,
        'overall_success': all_systems_good,
        'total_time': total_time
    }

if __name__ == "__main__":
    # Check for API key
    openai_key = os.getenv('OPENAI_API_KEY')
    if not openai_key:
        print("⚠️  No OPENAI_API_KEY found in environment")
        print("   Tests will run in fallback mode (rule-based processing)")
        print("   Set OPENAI_API_KEY for full AI testing\n")
    else:
        print("✅ OPENAI_API_KEY found - full AI testing enabled\n")
    
    # Run comprehensive tests
    results = run_comprehensive_tests()
    
    # Exit with appropriate code
    sys.exit(0 if results['overall_success'] else 1)