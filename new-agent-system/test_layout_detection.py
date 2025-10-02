"""
Test script for enhanced layout detection
"""

import pandas as pd
from core.multi_agent_orchestrator import MultiAgentOrchestrator

def test_layout_detection():
    print('🧪 Testing Enhanced Layout Detection')
    print('=' * 50)
    
    # Test horizontal layout (your Cab example)
    print('\n📊 TEST 1: Horizontal Layout (Cab 1, Cab 2, Cab 3, Cab 4)')
    horizontal_df = pd.DataFrame({
        'Cab Booking Format': ['Name of Employee', 'Contact Number', 'City', 'Date of Travel', 'Company Name'],
        'Cab 1': ['Jayasheel Bhansali', '7001682596', 'Bangalore', '19-Sep-25', 'LTPL'],
        'Cab 2': ['Jayasheel Bhansali', '7001682596', 'Bangalore', '20 Sep 2025', 'LTPL'],
        'Cab 3': ['Jayasheel Bhansali', '7001682596', 'Mumbai', '21-Sep-25', 'LTPL'],
        'Cab 4': ['Jayasheel Bhansali', '7001682596', 'Mumbai', '22 Sep 2025', 'LTPL']
    })
    
    orchestrator = MultiAgentOrchestrator('fake-key')
    horizontal_analysis = orchestrator._analyze_dataframe_structure(horizontal_df)
    
    print(f'Shape: {horizontal_df.shape}')
    print('Analysis:')
    for key, value in horizontal_analysis.items():
        print(f'  {key}: {value}')
    
    # Test vertical layout 
    print('\n📊 TEST 2: Vertical Layout (Regular booking table)')
    vertical_df = pd.DataFrame({
        'S.No': ['1', '2', '3'],
        'Name': ['Aashima Malik', 'Somya Jain', 'Muskan Jindal'],
        'Date': ['30-SEP25', '30-Sep-25', '30-Sep-25'],
        'Mobile': ['9999570142', '9711829546', '8810600875']
    })
    
    vertical_analysis = orchestrator._analyze_dataframe_structure(vertical_df)
    
    print(f'Shape: {vertical_df.shape}')
    print('Analysis:')
    for key, value in vertical_analysis.items():
        print(f'  {key}: {value}')
    
    print('\n✅ Layout Detection Summary:')
    h_bookings = horizontal_analysis['estimated_bookings']
    h_type = horizontal_analysis['layout_type']
    v_bookings = vertical_analysis['estimated_bookings'] 
    v_type = vertical_analysis['layout_type']
    
    print(f'Horizontal (Cab 1-4): {h_bookings} bookings ({h_type})')
    print(f'Vertical (Rows 1-3): {v_bookings} bookings ({v_type})')
    
    # Validation
    if h_bookings == 4 and h_type == 'horizontal_multi_booking':
        print('✅ Horizontal detection CORRECT!')
    else:
        print('❌ Horizontal detection FAILED!')
        
    if v_bookings == 3 and 'vertical' in v_type:
        print('✅ Vertical detection CORRECT!')  
    else:
        print('❌ Vertical detection FAILED!')

if __name__ == '__main__':
    test_layout_detection()