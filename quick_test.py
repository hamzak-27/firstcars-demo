#!/usr/bin/env python3
"""
Quick test to verify the multi-agent system works with corrected model names
"""

import os

# Check API key
if 'GEMINI_API_KEY' not in os.environ:
    print("⚠️ GEMINI_API_KEY not found in environment variables")
    print("Please set: export GEMINI_API_KEY=your_api_key")
    exit(1)

from complete_multi_agent_orchestrator import CompleteMultiAgentOrchestrator

def test_system():
    print('🧪 Testing Multi-Agent System with Corrected Model Names...')
    print('=' * 60)
    
    try:
        orchestrator = CompleteMultiAgentOrchestrator()
        
        test_content = '''
        Please arrange a cab for John Smith (9876543210) tomorrow at 10 AM from Mumbai to Airport.
        Vehicle preferred: Innova
        Corporate: TechCorp India
        '''
        
        result = orchestrator.process_content(test_content, 'test')
        
        success = result.get('success', False)
        booking_count = result.get('booking_count', 0)
        cost = result.get('total_cost_inr', 0.0)
        
        print(f'✅ Processing successful: {success}')
        print(f'📊 Bookings found: {booking_count}')
        print(f'💰 Total cost: ₹{cost:.4f}')
        
        # Check each pipeline stage
        if result.get('pipeline_stages'):
            print('\n🔧 Pipeline Stages:')
            stages = result['pipeline_stages']
            for stage, info in stages.items():
                agent = info.get('agent', 'Unknown')
                stage_cost = info.get('cost_inr', 0)
                processing_time = info.get('processing_time', 0)
                print(f'  {stage.title()}: {agent} (₹{stage_cost:.4f}, {processing_time:.2f}s)')
        
        # Check for errors
        error_msg = result.get('error_message')
        if error_msg:
            print(f'\n⚠️ Error occurred: {error_msg}')
        else:
            print('\n🎉 No errors - system working correctly!')
        
        # Check final DataFrame
        final_df = result.get('final_dataframe')
        if final_df is not None and not final_df.empty:
            print(f'\n📋 Final DataFrame shape: {final_df.shape}')
            print('📋 Sample booking data:')
            first_row = final_df.iloc[0]
            print(f'  Customer: {first_row.get("Customer", "N/A")}')
            print(f'  Passenger: {first_row.get("Passenger Name", "N/A")}')
            print(f'  Phone: {first_row.get("Passenger Phone Number", "N/A")}')
            print(f'  From: {first_row.get("From (Service Location)", "N/A")}')
            print(f'  To: {first_row.get("To", "N/A")}')
            print(f'  Vehicle: {first_row.get("Vehicle Group", "N/A")}')
        
        # Check metadata
        metadata = result.get('metadata', {})
        agents_used = metadata.get('agents_used', [])
        if agents_used:
            print(f'\n🤖 Agents used: {", ".join(agents_used)}')
        
        return success
        
    except Exception as e:
        print(f'❌ Test failed with exception: {e}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_system()
    if success:
        print('\n✅ System is ready for Streamlit!')
        print('Run: streamlit run car_rental_app.py')
    else:
        print('\n❌ System needs debugging')