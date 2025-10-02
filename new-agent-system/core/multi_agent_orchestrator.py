"""
Multi-Agent Orchestrator
Coordinates all specialized agents for comprehensive booking data extraction
"""

import pandas as pd
import logging
from typing import Dict, List, Optional, Any
import json

from processors.textract_processor import TextractProcessor
from processors.classification_agent import ClassificationAgent
from agents.corporate_booker_agent import CorporateBookerAgent
from agents.passenger_details_agent import PassengerDetailsAgent
from agents.location_time_agent import LocationTimeAgent
from agents.duty_vehicle_agent import DutyVehicleAgent
from agents.special_requirements_agent import SpecialRequirementsAgent
from agents.flight_details_agent import FlightDetailsAgent

logger = logging.getLogger(__name__)

class MultiAgentOrchestrator:
    """
    Main orchestrator that coordinates all agents for booking data extraction
    """
    
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        """Initialize orchestrator with all agents"""
        self.api_key = api_key
        self.model = model
        
        # Initialize processors
        self.textract_processor = TextractProcessor()
        self.classification_agent = ClassificationAgent(api_key, model)
        
        # Initialize specialized agents
        self.agents = {
            'corporate_booker': CorporateBookerAgent(api_key, model),
            'passenger_details': PassengerDetailsAgent(api_key, model),
            'location_time': LocationTimeAgent(api_key, model),
            'duty_vehicle': DutyVehicleAgent(api_key, model),
            'flight_details': FlightDetailsAgent(api_key, model),
            'special_requirements': SpecialRequirementsAgent(api_key, model)
        }
        
        # Define the order of agent execution
        self.agent_sequence = [
            'corporate_booker',
            'passenger_details', 
            'location_time',
            'duty_vehicle',
            'flight_details',
            'special_requirements'
        ]
        
        logger.info("Multi-agent orchestrator initialized with 6 specialized agents")
    
    def process_unstructured_email(self, email_content: str, sender_email: str = "") -> pd.DataFrame:
        """
        Process unstructured email content through classification and agent pipeline
        
        Args:
            email_content: Raw email text
            sender_email: Optional sender email for company extraction
            
        Returns:
            Processed DataFrame with extracted booking data
        """
        logger.info("Processing unstructured email content")
        
        try:
            # Step 1: Classify email to determine booking count
            classification = self.classification_agent.classify_booking_type(email_content)
            logger.info(f"Email classified as: {classification}")
            
            # Step 2: Create appropriate DataFrame structure
            num_bookings = classification.get('booking_count', 1)
            df = self._create_booking_dataframe(num_bookings)
            
            # Step 3: Process through agent pipeline
            processed_df = self._process_through_agents(
                df=df,
                source_data={'email_content': email_content, 'sender_email': sender_email},
                data_type='email'
            )
            
            return processed_df
            
        except Exception as e:
            logger.error(f"Error processing unstructured email: {e}")
            return self._create_empty_dataframe()
    
    def process_table_data(self, image_path: str) -> pd.DataFrame:
        """
        Process table data from images using Textract and agent pipeline
        
        Args:
            image_path: Path to image/PDF file
            
        Returns:
            Processed DataFrame with extracted and enriched booking data
        """
        logger.info(f"Processing table data from: {image_path}")
        
        print("\n" + "=" * 80)
        print("🚀 MULTI-STAGE TABLE PROCESSING PIPELINE")
        print("=" * 80)
        print("📋 Stage 1: Raw Textract Extraction (Your exact code)")
        print("📋 Stage 2: DataFrame Conversion (Your exact code)")
        print("📋 Stage 3: Multi-Agent Processing (AI enhancement)")
        print("=" * 80)
        
        try:
            # Step 1: Extract table using Textract
            df = self.textract_processor.process_image(image_path)
            if df.empty:
                logger.warning("No table data extracted from image")
                return self._create_empty_dataframe()
            
            # Step 2: Analyze DataFrame structure
            structure_analysis = self._analyze_dataframe_structure(df)
            logger.info(f"DataFrame structure: {structure_analysis}")
            
            # Step 3: Process through agent pipeline
            processed_df = self._process_through_agents(
                df=df,
                source_data={'raw_df': df, 'image_path': image_path},
                data_type='table'
            )
            
            return processed_df
            
        except Exception as e:
            logger.error(f"Error processing table data: {e}")
            return self._create_empty_dataframe()
    
    def _analyze_dataframe_structure(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze DataFrame to determine layout type and booking structure"""
        
        analysis = {
            'rows': len(df),
            'cols': len(df.columns),
            'layout_type': 'unknown',
            'booking_indicators': [],
            'has_headers': False
        }
        
        # Detect horizontal layout (columns are bookings, rows are fields)
        horizontal_indicators = self._detect_horizontal_layout(df)
        
        # Detect vertical layout (rows are bookings, columns are fields)  
        vertical_indicators = self._detect_vertical_layout(df)
        
        logger.info(f"Layout detection - Horizontal score: {horizontal_indicators['score']}, Vertical score: {vertical_indicators['score']}")
        
        if horizontal_indicators['score'] > vertical_indicators['score'] and horizontal_indicators['score'] >= 3:
            # Horizontal layout: columns are bookings
            analysis['layout_type'] = 'horizontal_multi_booking'
            analysis['has_headers'] = True
            analysis['estimated_bookings'] = horizontal_indicators['booking_count']
            analysis['booking_indicators'] = horizontal_indicators['indicators']
            logger.info(f"Detected HORIZONTAL layout: {horizontal_indicators['booking_count']} bookings (columns)")
            
        elif vertical_indicators['score'] > horizontal_indicators['score'] and vertical_indicators['score'] >= 3:
            # Vertical layout: rows are bookings
            analysis['layout_type'] = 'vertical_multi_booking'
            analysis['has_headers'] = vertical_indicators['has_headers']
            analysis['estimated_bookings'] = vertical_indicators['booking_count'] 
            analysis['booking_indicators'] = vertical_indicators['indicators']
            logger.info(f"Detected VERTICAL layout: {vertical_indicators['booking_count']} bookings (rows)")
            
        else:
            # Fallback: assume vertical layout (rows are bookings)
            if self._looks_like_header_row(df):
                analysis['has_headers'] = True
                analysis['estimated_bookings'] = len(df) - 1  # Subtract header row
                analysis['layout_type'] = 'vertical_multi_booking'
            else:
                analysis['estimated_bookings'] = len(df)  # All rows are bookings
                analysis['layout_type'] = 'vertical_multi_booking'
            logger.info(f"FALLBACK to vertical layout: {analysis['estimated_bookings']} bookings (rows)")
        
        return analysis
    
    def _detect_horizontal_layout(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Detect horizontal layout where columns are bookings and rows are fields
        Example: Cab 1 | Cab 2 | Cab 3 | Cab 4
        
        Returns dict with score, booking_count, and indicators
        """
        result = {'score': 0, 'booking_count': 0, 'indicators': []}
        
        if df.empty or len(df.columns) < 2:
            return result
        
        # Check column headers for booking patterns
        columns = [str(col).lower() for col in df.columns]
        
        # Pattern 1: Cab 1, Cab 2, etc.
        cab_pattern_count = 0
        for col in columns[1:]:  # Skip first column (usually labels)
            if ('cab' in col and any(char.isdigit() for char in col)):
                cab_pattern_count += 1
        
        if cab_pattern_count >= 2:
            result['score'] += cab_pattern_count * 2  # High score for cab patterns
            result['booking_count'] = cab_pattern_count
            result['indicators'].append(f'{cab_pattern_count} cab columns')
        
        # Pattern 2: Sequential numbers (1, 2, 3, 4)
        numeric_sequence = 0
        for i, col in enumerate(columns[1:], 1):
            if col.strip().isdigit() and int(col.strip()) == i:
                numeric_sequence += 1
        
        if numeric_sequence >= 2:
            result['score'] += numeric_sequence
            if result['booking_count'] == 0:  # Don't override cab count
                result['booking_count'] = numeric_sequence
            result['indicators'].append(f'{numeric_sequence} sequential columns')
        
        # Pattern 3: Check first column for field indicators
        if len(df) > 0:
            first_col_values = df.iloc[:, 0].astype(str).str.lower()
            field_indicators = ['name', 'contact', 'city', 'date', 'pickup', 'drop', 'cab', 'flight', 'company']
            field_matches = sum(1 for val in first_col_values for indicator in field_indicators if indicator in val)
            
            if field_matches >= 3:
                result['score'] += field_matches
                result['indicators'].append(f'{field_matches} field labels in first column')
                if result['booking_count'] == 0:
                    result['booking_count'] = len(df.columns) - 1  # All columns except first are bookings
        
        return result
    
    def _detect_vertical_layout(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Detect vertical layout where rows are bookings and columns are fields
        Example: Each row is a separate booking with columns like Name, Date, etc.
        
        Returns dict with score, booking_count, has_headers, and indicators
        """
        result = {'score': 0, 'booking_count': 0, 'has_headers': False, 'indicators': []}
        
        if df.empty:
            return result
        
        # Check first row for header patterns
        if len(df) > 0:
            first_row = df.iloc[0].astype(str).str.lower()
            header_indicators = ['s.no', 'serial', 'name', 'date', 'time', 'phone', 'mobile', 'address', 'pickup', 'drop', 'location']
            header_matches = sum(1 for cell in first_row for indicator in header_indicators if indicator in cell)
            
            if header_matches >= 3:
                result['score'] += header_matches * 2
                result['has_headers'] = True
                result['booking_count'] = len(df) - 1  # Subtract header row
                result['indicators'].append(f'{header_matches} header fields detected')
        
        # Check for sequential booking numbers in first column
        if len(df) > 1:
            first_col = df.iloc[:, 0].astype(str)
            sequential_numbers = 0
            for i, val in enumerate(first_col[1:], 1):  # Skip potential header
                if val.strip().isdigit() and int(val.strip()) == i:
                    sequential_numbers += 1
            
            if sequential_numbers >= 2:
                result['score'] += sequential_numbers
                if result['booking_count'] == 0:
                    result['booking_count'] = sequential_numbers
                result['indicators'].append(f'{sequential_numbers} sequential booking numbers')
        
        # Check for data patterns in cells (vs field names)
        if len(df) > 1:
            data_indicators = 0
            sample_cells = df.iloc[1, :].astype(str)  # Second row (after potential header)
            for cell in sample_cells:
                if (cell.strip().isdigit() and len(cell.strip()) >= 8) or '@' in cell or any(char.isdigit() for char in cell):
                    data_indicators += 1
            
            if data_indicators >= 2:
                result['score'] += data_indicators
                result['indicators'].append(f'{data_indicators} data-like cells in sample row')
                if result['booking_count'] == 0:
                    result['booking_count'] = len(df) - (1 if result['has_headers'] else 0)
        
        return result
    
    def _looks_like_header_row(self, df: pd.DataFrame) -> bool:
        """
        Check if the first row looks like headers (contains field names vs data)
        
        Args:
            df: DataFrame to analyze
            
        Returns:
            True if first row looks like headers
        """
        if df.empty:
            return False
            
        first_row = df.iloc[0].astype(str)
        
        # Check for common header patterns
        header_indicators = [
            's.no', 'serial', 'number', 'date', 'time', 'name', 'phone', 'mobile', 
            'address', 'pickup', 'drop', 'cab', 'vehicle', 'duty', 'location', 
            'from', 'to', 'passenger', 'customer'
        ]
        
        # Count how many cells look like headers vs data
        header_like = 0
        data_like = 0
        
        for cell in first_row:
            cell_lower = str(cell).lower().strip()
            
            # Skip empty cells
            if not cell_lower:
                continue
                
            # Check if it looks like a header
            if any(indicator in cell_lower for indicator in header_indicators):
                header_like += 1
            # Check if it looks like data (numbers, specific patterns)
            elif (cell_lower.isdigit() or 
                  '@' in cell_lower or 
                  any(char.isdigit() for char in cell_lower) and len(cell_lower) > 8):
                data_like += 1
        
        # If more cells look like headers than data, it's probably a header row
        return header_like > data_like and header_like >= 2
    
    def _process_through_agents(self, df: pd.DataFrame, source_data: Dict, data_type: str) -> pd.DataFrame:
        """
        Process data through all specialized agents sequentially
        
        Args:
            df: DataFrame to process (either structured table or empty for emails)
            source_data: Original source data (email content or raw table)
            data_type: 'email' or 'table'
            
        Returns:
            Enhanced DataFrame with all extracted fields
        """
        logger.info(f"Processing {data_type} data through {len(self.agents)} specialized agents")
        
        # Determine number of bookings to process
        if data_type == 'email':
            num_bookings = len(df)
        else:
            # For tables, analyze structure to determine bookings
            structure = self._analyze_dataframe_structure(df)
            num_bookings = structure.get('estimated_bookings', 1)
        
        # Initialize shared context for all agents
        shared_context = {
            'source_type': data_type,
            'num_bookings': num_bookings,
            'extracted_data': {},
            'processing_history': []
        }
        
        # Process each booking through all agents
        for booking_idx in range(num_bookings):
            logger.info(f"Processing booking {booking_idx + 1}/{num_bookings}")
            
            # Prepare booking-specific data
            booking_data = self._prepare_booking_data(df, booking_idx, source_data, data_type)
            
            # Process through each agent sequentially
            for agent_name in self.agent_sequence:
                try:
                    agent = self.agents[agent_name]
                    logger.info(f"Running {agent_name} agent for booking {booking_idx + 1}")
                    
                    # Process with current agent
                    result = agent.process_booking_data(booking_data, shared_context)
                    
                    # Update shared context with results
                    extracted_fields = result.get('extracted_fields', {})
                    shared_context['extracted_data'][booking_idx] = shared_context['extracted_data'].get(booking_idx, {})
                    shared_context['extracted_data'][booking_idx].update(extracted_fields)
                    
                    # Add to processing history
                    shared_context['processing_history'].append({
                        'agent': agent_name,
                        'booking': booking_idx,
                        'fields_extracted': list(extracted_fields.keys()),
                        'success': result.get('success', False)
                    })
                    
                    logger.info(f"{agent_name} extracted: {list(extracted_fields.keys())}")
                    
                except Exception as e:
                    logger.error(f"Error in {agent_name} agent for booking {booking_idx}: {e}")
                    continue
        
        # Update DataFrame with all extracted data
        enhanced_df = self._update_dataframe_with_results(df, shared_context['extracted_data'])
        
        logger.info(f"Processing completed. Enhanced DataFrame shape: {enhanced_df.shape}")
        
        print("\n===== FINAL PROCESSED OUTPUT =====")
        print("\n📊 AGENTS PROCESSING RESULTS:")
        print(enhanced_df.to_string(index=False))
        print(f"\n🎯 Final DataFrame Info: Shape={enhanced_df.shape}, Columns={list(enhanced_df.columns)}")
        print("=" * 80)
        
        return enhanced_df
    
    def _prepare_booking_data(self, df: pd.DataFrame, booking_idx: int, source_data: Dict, data_type: str) -> Dict:
        """Prepare booking-specific data for agent processing"""
        
        booking_data = {
            'booking_index': booking_idx,
            'source_type': data_type
        }
        
        if data_type == 'email':
            # For emails, pass the full email content
            booking_data.update({
                'email_content': source_data.get('email_content', ''),
                'sender_email': source_data.get('sender_email', ''),
                'table_data': None
            })
        else:
            # For tables, extract relevant rows/columns for this booking
            booking_data.update({
                'email_content': '',
                'sender_email': '',
                'table_data': self._extract_booking_table_slice(df, booking_idx),
                'full_table': df
            })
        
        return booking_data
    
    def _extract_booking_table_slice(self, df: pd.DataFrame, booking_idx: int) -> pd.DataFrame:
        """Extract the relevant table slice for a specific booking based on layout type"""
        
        try:
            # Check if this is a form-style table (Field-Value format)
            if len(df.columns) == 2 and 'Field' in df.columns and 'Value' in df.columns:
                # Return the full form DataFrame for Field-Value pairs
                logger.info(f"Form-style table detected with {len(df)} fields")
                return df
            
            # Analyze layout to determine extraction method
            structure = self._analyze_dataframe_structure(df)
            layout_type = structure.get('layout_type', 'unknown')
            
            if layout_type == 'horizontal_multi_booking':
                # Horizontal layout: columns are bookings, rows are fields
                if len(df.columns) > booking_idx + 1:  # +1 because first column is usually labels
                    col_name = df.columns[booking_idx + 1]
                    booking_df = df.iloc[:, [0, booking_idx + 1]]  # Keep labels column and booking column
                    booking_df.columns = ['Field', 'Value']  # Rename for consistency
                    logger.info(f"HORIZONTAL: Extracted column '{col_name}' as DataFrame with shape {booking_df.shape}")
                    return booking_df
            
            elif layout_type in ['vertical_multi_booking', 'unknown']:
                # Vertical layout: rows are bookings, columns are fields
                if len(df) > booking_idx:
                    booking_row = df.iloc[[booking_idx]]  # Double brackets to keep as DataFrame
                    logger.info(f"VERTICAL: Extracted row {booking_idx} as DataFrame with shape {booking_row.shape}")
                    return booking_row
        
        except Exception as e:
            logger.error(f"Error extracting booking slice: {e}")
        
        # Fallback: return entire table
        logger.warning(f"Using fallback: returning full table for booking {booking_idx}")
        return df
    
    def _update_dataframe_with_results(self, original_df: pd.DataFrame, extracted_data: Dict) -> pd.DataFrame:
        """Update DataFrame with extracted data from all agents"""
        
        # Create standardized column structure - FIXED COLUMNS as specified
        standard_columns = [
            'Customer',                    # corporate_name 
            'Booked By Name',             # booker_name
            'Booked By Phone Number',     # booker_phone
            'Booked By Email',            # booker_email
            'Passenger Name',             # passenger_name
            'Passenger Phone Number',     # passenger_phone
            'Passenger Email',            # passenger_email
            'From (Service Location)',    # from_location
            'To',                        # to_location
            'Vehicle Group',             # vehicle_group
            'Duty Type',                 # duty_type
            'Start Date',                # start_date
            'End Date',                  # end_date
            'Rep. Time',                 # reporting_time
            'Reporting Address',         # reporting_address
            'Drop Address',              # drop_address
            'Flight/Train Number',       # flight_train_number
            'Dispatch center',           # dispatch_center (to be extracted from city mapping)
            'Remarks',                   # remarks
            'Labels'                     # labels
        ]
        
        # Determine number of bookings
        num_bookings = len(extracted_data) if extracted_data else max(1, len(original_df))
        
        # Create new DataFrame with standardized structure
        new_df = pd.DataFrame(index=range(num_bookings), columns=standard_columns)
        
        # Define field mapping from agent output to DataFrame columns
        field_mapping = {
            'corporate_name': 'Customer',
            'booker_name': 'Booked By Name',
            'booker_phone': 'Booked By Phone Number', 
            'booker_email': 'Booked By Email',
            'passenger_name': 'Passenger Name',
            'passenger_phone': 'Passenger Phone Number',
            'passenger_email': 'Passenger Email',
            'from_location': 'From (Service Location)',
            'to_location': 'To',
            'vehicle_group': 'Vehicle Group',
            'duty_type': 'Duty Type',
            'start_date': 'Start Date',
            'end_date': 'End Date',
            'reporting_time': 'Rep. Time',
            'reporting_address': 'Reporting Address',
            'drop_address': 'Drop Address',
            'flight_train_number': 'Flight/Train Number',
            'dispatch_center': 'Dispatch center',
            'remarks': 'Remarks',
            'labels': 'Labels'
        }
        
        # Fill with extracted data using field mapping
        logger.info(f"Processing extracted data: {extracted_data}")
        
        for booking_idx, booking_data in extracted_data.items():
            logger.info(f"Processing booking {booking_idx} with data: {booking_data}")
            
            if booking_idx < len(new_df):
                for field, value in booking_data.items():
                    # Map field to DataFrame column
                    df_column = field_mapping.get(field, field)
                    logger.info(f"Mapping field '{field}' → '{df_column}' with value: {value}")
                    
                    if df_column in standard_columns:
                        new_df.at[booking_idx, df_column] = value
                        logger.info(f"✅ Successfully set {df_column} = {value}")
                    else:
                        logger.warning(f"❌ Column '{df_column}' not in standard columns")
                        
                # Fill NA for empty fields
                for col in standard_columns:
                    if pd.isna(new_df.at[booking_idx, col]):
                        new_df.at[booking_idx, col] = "NA"
        
        # No booking IDs in new structure - removed
        
        return new_df
    
    def _create_booking_dataframe(self, num_bookings: int) -> pd.DataFrame:
        """Create empty DataFrame structure for bookings"""
        
        columns = [
            'Customer',                    
            'Booked By Name',             
            'Booked By Phone Number',     
            'Booked By Email',            
            'Passenger Name',             
            'Passenger Phone Number',     
            'Passenger Email',            
            'From (Service Location)',    
            'To',                        
            'Vehicle Group',             
            'Duty Type',                 
            'Start Date',                
            'End Date',                  
            'Rep. Time',                 
            'Reporting Address',         
            'Drop Address',              
            'Flight/Train Number',       
            'Dispatch center',           
            'Remarks',                   
            'Labels'                     
        ]
        
        df = pd.DataFrame(index=range(num_bookings), columns=columns)
        
        # Initialize all fields with "NA"
        for col in columns:
            df[col] = "NA"
        
        return df
    
    def _create_empty_dataframe(self) -> pd.DataFrame:
        """Create empty DataFrame with standard structure"""
        return self._create_booking_dataframe(1)
    
    def get_processing_summary(self) -> Dict:
        """Get summary of last processing operation"""
        # This could be expanded to track processing metrics
        return {
            'agents_available': len(self.agents),
            'agent_sequence': self.agent_sequence,
            'model': self.model
        }