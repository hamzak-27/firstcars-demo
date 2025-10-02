"""
AWS Textract Table Processor
Extracts table data from images and converts to pandas DataFrames
"""

import boto3
import pandas as pd
import json
import logging
import os
from typing import List, Dict, Tuple, Any

logger = logging.getLogger(__name__)

class TextractTableProcessor:
    """
    Processes table images using AWS Textract and converts to structured DataFrames
    """
    
    def __init__(self, aws_region: str = 'ap-south-1', 
                 aws_access_key_id: str = None, 
                 aws_secret_access_key: str = None):
        """Initialize Textract client"""
        
        # Initialize Textract client with credentials
        self.textract = boto3.client(
            'textract', 
            region_name=aws_region,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key
        )
        logger.info(f"Textract initialized for region: {aws_region}")
    
    def extract_data_from_file(self, file_path: str) -> Tuple[Dict[str, str], List[List[str]]]:
        """
        Extract forms and tables from file using Textract
        
        Args:
            file_path: Path to image/PDF file
            
        Returns:
            Tuple of (forms_dict, tables_list)
        """
        
        # Read the file (image or PDF)
        with open(file_path, 'rb') as f:
            img_bytes = f.read()

        # Call Textract API
        response = self.textract.analyze_document(
            Document={'Bytes': img_bytes},
            FeatureTypes=["TABLES", "FORMS"]
        )

        blocks = response['Blocks']

        # Extract Key-Value Pairs (Forms)
        kvs = self._extract_key_value_pairs(blocks)
        
        # Extract Tables
        tables = self._extract_tables(blocks)

        return kvs, tables
    
    def extract_data_from_bytes(self, img_bytes: bytes) -> Tuple[Dict[str, str], List[List[str]]]:
        """
        Extract forms and tables from image bytes using Textract
        
        Args:
            img_bytes: Image data as bytes
            
        Returns:
            Tuple of (forms_dict, tables_list)
        """
        
        # Call Textract API
        response = self.textract.analyze_document(
            Document={'Bytes': img_bytes},
            FeatureTypes=["TABLES", "FORMS"]
        )

        blocks = response['Blocks']

        # Extract Key-Value Pairs (Forms)
        kvs = self._extract_key_value_pairs(blocks)
        
        # Extract Tables
        tables = self._extract_tables(blocks)

        return kvs, tables
    
    def _extract_key_value_pairs(self, blocks: List[Dict]) -> Dict[str, str]:
        """Extract key-value pairs (forms) from Textract blocks"""
        
        kvs = {}
        key_map = {}
        value_map = {}
        block_map = {}

        for block in blocks:
            block_id = block['Id']
            block_map[block_id] = block
            if block['BlockType'] == "KEY_VALUE_SET":
                if "KEY" in block['EntityTypes']:
                    key_map[block_id] = block
                else:
                    value_map[block_id] = block

        def get_text(result, blocks_map):
            text = ''
            if 'Relationships' in result:
                for rel in result['Relationships']:
                    if rel['Type'] == 'CHILD':
                        for cid in rel['Ids']:
                            word = blocks_map[cid]
                            if word['BlockType'] == 'WORD':
                                text += word['Text'] + ' '
                            elif word['BlockType'] == 'SELECTION_ELEMENT':
                                if word['SelectionStatus'] == 'SELECTED':
                                    text += 'X '
            return text.strip()

        def find_value_block(key_block):
            for rel in key_block.get('Relationships', []):
                if rel['Type'] == 'VALUE':
                    for v_id in rel['Ids']:
                        return value_map[v_id]
            return None

        for block_id, key_block in key_map.items():
            value_block = find_value_block(key_block)
            key = get_text(key_block, block_map)
            val = get_text(value_block, block_map) if value_block else ""
            kvs[key] = val
            
        return kvs
    
    def _extract_tables(self, blocks: List[Dict]) -> List[List[str]]:
        """Extract tables from Textract blocks"""
        
        tables = []
        block_map = {block['Id']: block for block in blocks}
        
        def get_text(result, blocks_map):
            text = ''
            if 'Relationships' in result:
                for rel in result['Relationships']:
                    if rel['Type'] == 'CHILD':
                        for cid in rel['Ids']:
                            word = blocks_map[cid]
                            if word['BlockType'] == 'WORD':
                                text += word['Text'] + ' '
                            elif word['BlockType'] == 'SELECTION_ELEMENT':
                                if word['SelectionStatus'] == 'SELECTED':
                                    text += 'X '
            return text.strip()
        
        for block in blocks:
            if block['BlockType'] == "TABLE":
                table = []
                for relationship in block.get('Relationships', []):
                    if relationship['Type'] == "CHILD":
                        for cid in relationship['Ids']:
                            cell = block_map[cid]
                            if cell['BlockType'] == "CELL":
                                row_index = cell['RowIndex']
                                col_index = cell['ColumnIndex']
                                txt = get_text(cell, block_map)

                                while len(table) < row_index:
                                    table.append([])

                                row = table[row_index - 1]
                                while len(row) < col_index:
                                    row.append("")
                                row[col_index - 1] = txt
                tables.append(table)
        
        return tables
    
    def tables_to_dataframes(self, tables: List[List[str]]) -> List[pd.DataFrame]:
        """
        Convert Textract tables (list of lists) into pandas DataFrames
        
        Args:
            tables: List of table data (each table is list of lists)
            
        Returns:
            List of pandas DataFrames
        """
        dataframes = []

        for i, table in enumerate(tables):
            try:
                if not table or len(table) < 2:  # Need at least header + 1 data row
                    logger.warning(f"Skipping empty or single-row table {i}")
                    continue
                    
                # Ensure all rows are of equal length (pad with empty strings if needed)
                max_len = max(len(row) for row in table)
                normalized = [row + [""] * (max_len - len(row)) for row in table]

                # Assume first row is header
                headers = normalized[0]
                data_rows = normalized[1:]
                
                # Create DataFrame
                df = pd.DataFrame(data_rows, columns=headers)
                dataframes.append(df)
                
                logger.info(f"Created DataFrame {i+1} with shape {df.shape}")
                
            except Exception as e:
                logger.error(f"Error converting table {i} to DataFrame: {str(e)}")
                continue

        return dataframes
    
    def get_booking_count_from_tables(self, dataframes: List[pd.DataFrame]) -> int:
        """
        Determine booking count from table structure
        
        Args:
            dataframes: List of pandas DataFrames from tables
            
        Returns:
            Number of bookings detected
        """
        total_bookings = 0
        
        for i, df in enumerate(dataframes):
            try:
                # Method 1: Check for horizontal multi-booking (columns like Cab 1, Cab 2)
                cab_columns = [col for col in df.columns if 'cab' in col.lower() and any(char.isdigit() for char in col)]
                if cab_columns:
                    booking_count = len(cab_columns)
                    logger.info(f"Table {i+1}: Found {booking_count} horizontal bookings from columns: {cab_columns}")
                    total_bookings += booking_count
                    continue
                
                # Method 2: Check for vertical multi-booking (rows with S.No or numbered entries)
                first_col = df.columns[0].lower()
                if 's.no' in first_col or 'sr' in first_col or 'serial' in first_col:
                    booking_count = len(df)  # Each row is a booking
                    logger.info(f"Table {i+1}: Found {booking_count} vertical bookings from rows")
                    total_bookings += booking_count
                    continue
                
                # Method 3: Form-style table (2 columns, key-value pairs)
                if len(df.columns) == 2:
                    booking_count = 1  # Single booking in form format
                    logger.info(f"Table {i+1}: Found {booking_count} form-style booking")
                    total_bookings += booking_count
                    continue
                
                # Default: Assume single booking
                booking_count = 1
                logger.info(f"Table {i+1}: Defaulting to {booking_count} booking")
                total_bookings += booking_count
                
            except Exception as e:
                logger.error(f"Error analyzing table {i} for booking count: {str(e)}")
                total_bookings += 1  # Default to 1 booking
        
        logger.info(f"Total bookings detected from all tables: {total_bookings}")
        return total_bookings
    
    def process_document(self, file_path: str) -> Tuple[List[pd.DataFrame], int]:
        """
        Complete processing pipeline: Extract → Convert → Count bookings
        
        Args:
            file_path: Path to document file
            
        Returns:
            Tuple of (dataframes_list, total_booking_count)
        """
        try:
            # Extract raw data
            forms, tables = self.extract_data_from_file(file_path)
            
            # Convert to DataFrames
            dataframes = self.tables_to_dataframes(tables)
            
            # Count bookings
            booking_count = self.get_booking_count_from_tables(dataframes)
            
            logger.info(f"Document processing complete: {len(dataframes)} tables, {booking_count} bookings")
            return dataframes, booking_count
            
        except Exception as e:
            logger.error(f"Error processing document {file_path}: {str(e)}")
            return [], 0


class TextractProcessor:
    """
    Direct Textract processor using the working code provided
    """
    
    def __init__(self):
        """Initialize Textract processor with credentials from environment"""
        
        # Get AWS credentials from environment variables
        aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
        aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        aws_region = os.getenv('AWS_REGION', 'ap-south-1')
        
        if not aws_access_key_id or not aws_secret_access_key:
            raise ValueError("AWS credentials not found in environment variables. Please set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY.")
        
        # Initialize Textract client with environment credentials
        self.textract = boto3.client(
            'textract', 
            region_name=aws_region,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key
        )
        
        # Initialize S3 client with same credentials
        self.s3_client = boto3.client(
            's3',
            region_name=aws_region,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key
        )
        
        # S3 bucket for temporary file storage
        self.s3_bucket = os.getenv('AWS_S3_BUCKET', 'aws-textract-bucket3')
        
        logger.info("TextractProcessor initialized with AWS credentials and S3 client")
    
    def extract_data_from_file(self, file_path: str):
        """
        Extract data from file using Textract via S3 - Enhanced with S3 processing
        
        Args:
            file_path: Path to image file
            
        Returns:
            Tuple of (forms_dict, tables_list)
        """
        # Convert image to supported format if needed
        processed_path = self._ensure_supported_format(file_path)
        
        # Check file size before processing
        with open(processed_path, 'rb') as f:
            file_size = len(f.read())
        
        logger.info(f"Processing file: {processed_path}, size: {file_size} bytes")
        
        if file_size < 100:  # Less than 100 bytes is likely corrupted
            logger.error(f"File too small ({file_size} bytes), likely corrupted")
            return {}, []
        
        s3_key = None
        try:
            # Upload to S3 first
            s3_key = self._upload_to_s3(processed_path)
            
            # Process from S3
            logger.info(f"Processing from S3: s3://{self.s3_bucket}/{s3_key}")
            kvs, tables = self.extract_data_from_s3(s3_key)
            
            logger.info(f"Textract processing successful via S3")
            return kvs, tables
            
        except Exception as e:
            logger.error(f"S3 processing failed: {e}")
            # Fallback to direct bytes processing
            logger.info("Attempting fallback to direct bytes processing...")
            
            try:
                with open(processed_path, 'rb') as f:
                    img_bytes = f.read()
                
                # Call Textract API with bytes
                response = self.textract.analyze_document(
                    Document={'Bytes': img_bytes},
                    FeatureTypes=["TABLES", "FORMS"]
                )
                
                blocks = response['Blocks']

                # Extract Key-Value Pairs (Forms) - same logic as S3 method
                kvs = {}
                key_map = {}
                value_map = {}
                block_map = {}

                for block in blocks:
                    block_id = block['Id']
                    block_map[block_id] = block
                    if block['BlockType'] == "KEY_VALUE_SET":
                        if "KEY" in block['EntityTypes']:
                            key_map[block_id] = block
                        else:
                            value_map[block_id] = block

                def get_text(result, blocks_map):
                    text = ''
                    if 'Relationships' in result:
                        for rel in result['Relationships']:
                            if rel['Type'] == 'CHILD':
                                for cid in rel['Ids']:
                                    word = blocks_map[cid]
                                    if word['BlockType'] == 'WORD':
                                        text += word['Text'] + ' '
                                    elif word['BlockType'] == 'SELECTION_ELEMENT':
                                        if word['SelectionStatus'] == 'SELECTED':
                                            text += 'X '
                    return text.strip()

                def find_value_block(key_block):
                    for rel in key_block.get('Relationships', []):
                        if rel['Type'] == 'VALUE':
                            for v_id in rel['Ids']:
                                return value_map[v_id]
                    return None

                for block_id, key_block in key_map.items():
                    value_block = find_value_block(key_block)
                    key = get_text(key_block, block_map)
                    val = get_text(value_block, block_map) if value_block else ""
                    kvs[key] = val

                # Extract Tables
                tables = []
                for block in blocks:
                    if block['BlockType'] == "TABLE":
                        table = []
                        for relationship in block.get('Relationships', []):
                            if relationship['Type'] == "CHILD":
                                for cid in relationship['Ids']:
                                    cell = block_map[cid]
                                    if cell['BlockType'] == "CELL":
                                        row_index = cell['RowIndex']
                                        col_index = cell['ColumnIndex']
                                        txt = get_text(cell, block_map)

                                        while len(table) < row_index:
                                            table.append([])

                                        row = table[row_index - 1]
                                        while len(row) < col_index:
                                            row.append("")
                                        row[col_index - 1] = txt
                        tables.append(table)

                logger.info(f"Fallback processing successful")
                return kvs, tables
                
            except Exception as fallback_error:
                logger.error(f"Fallback processing also failed: {fallback_error}")
                return {}, []
                
        finally:
            # Cleanup S3 file if it was uploaded
            if s3_key:
                self._cleanup_s3_file(s3_key)
    
    def _upload_to_s3(self, file_path: str) -> str:
        """
        Upload file to S3 for Textract processing
        
        Args:
            file_path: Local file path
            
        Returns:
            S3 key for the uploaded file
        """
        import uuid
        import os
        
        try:
            # Generate unique S3 key
            file_extension = os.path.splitext(file_path)[1]
            s3_key = f"textract-temp/{uuid.uuid4()}{file_extension}"
            
            # Using existing S3 bucket
            logger.info(f"Using S3 bucket: {self.s3_bucket}")
            
            # Upload file to S3
            logger.info(f"Uploading {file_path} to S3 bucket {self.s3_bucket} with key {s3_key}")
            
            with open(file_path, 'rb') as f:
                file_size = len(f.read())
                f.seek(0)  # Reset file pointer
                logger.info(f"Uploading file of size: {file_size} bytes")
                
                self.s3_client.upload_fileobj(f, self.s3_bucket, s3_key)
            
            logger.info(f"File uploaded successfully to s3://{self.s3_bucket}/{s3_key}")
            return s3_key
            
        except Exception as e:
            logger.error(f"Error uploading file to S3: {e}")
            raise
    
    def _cleanup_s3_file(self, s3_key: str):
        """
        Delete temporary file from S3
        
        Args:
            s3_key: S3 key to delete
        """
        try:
            self.s3_client.delete_object(Bucket=self.s3_bucket, Key=s3_key)
            logger.info(f"Cleaned up S3 file: s3://{self.s3_bucket}/{s3_key}")
        except Exception as e:
            logger.warning(f"Failed to cleanup S3 file {s3_key}: {e}")
    
    def extract_data_from_s3(self, s3_key: str):
        """
        Extract data from S3 file using Textract
        
        Args:
            s3_key: S3 key for the file
            
        Returns:
            Tuple of (forms_dict, tables_list)
        """
        # Call Textract API with S3 reference
        response = self.textract.analyze_document(
            Document={
                'S3Object': {
                    'Bucket': self.s3_bucket,
                    'Name': s3_key
                }
            },
            FeatureTypes=["TABLES", "FORMS"]
        )

        blocks = response['Blocks']

        # Extract Key-Value Pairs (Forms) - same logic as before
        kvs = {}
        key_map = {}
        value_map = {}
        block_map = {}

        for block in blocks:
            block_id = block['Id']
            block_map[block_id] = block
            if block['BlockType'] == "KEY_VALUE_SET":
                if "KEY" in block['EntityTypes']:
                    key_map[block_id] = block
                else:
                    value_map[block_id] = block

        def get_text(result, blocks_map):
            text = ''
            if 'Relationships' in result:
                for rel in result['Relationships']:
                    if rel['Type'] == 'CHILD':
                        for cid in rel['Ids']:
                            word = blocks_map[cid]
                            if word['BlockType'] == 'WORD':
                                text += word['Text'] + ' '
                            elif word['BlockType'] == 'SELECTION_ELEMENT':
                                if word['SelectionStatus'] == 'SELECTED':
                                    text += 'X '
            return text.strip()

        def find_value_block(key_block):
            for rel in key_block.get('Relationships', []):
                if rel['Type'] == 'VALUE':
                    for v_id in rel['Ids']:
                        return value_map[v_id]
            return None

        for block_id, key_block in key_map.items():
            value_block = find_value_block(key_block)
            key = get_text(key_block, block_map)
            val = get_text(value_block, block_map) if value_block else ""
            kvs[key] = val

        # Extract Tables - same logic as before
        tables = []
        for block in blocks:
            if block['BlockType'] == "TABLE":
                table = []
                for relationship in block.get('Relationships', []):
                    if relationship['Type'] == "CHILD":
                        for cid in relationship['Ids']:
                            cell = block_map[cid]
                            if cell['BlockType'] == "CELL":
                                row_index = cell['RowIndex']
                                col_index = cell['ColumnIndex']
                                txt = get_text(cell, block_map)

                                while len(table) < row_index:
                                    table.append([])

                                row = table[row_index - 1]
                                while len(row) < col_index:
                                    row.append("")
                                row[col_index - 1] = txt
                tables.append(table)

        return kvs, tables
    
    def _ensure_supported_format(self, file_path: str) -> str:
        """
        Convert image to supported format if needed (PNG, JPEG, PDF)
        
        Args:
            file_path: Original file path
            
        Returns:
            Path to supported format file
        """
        import tempfile
        from PIL import Image
        
        # Get file extension
        file_ext = os.path.splitext(file_path)[1].lower()
        
        # Textract supported formats
        supported_formats = ['.png', '.jpg', '.jpeg', '.pdf']
        
        if file_ext in supported_formats:
            logger.info(f"File format {file_ext} is supported by Textract")
            return file_path
        
        logger.info(f"Converting {file_ext} to PNG for Textract compatibility")
        
        try:
            # Load image with PIL
            with Image.open(file_path) as img:
                # Convert to RGB if necessary
                if img.mode in ('RGBA', 'P'):
                    img = img.convert('RGB')
                
                # Create temporary PNG file
                temp_fd, temp_path = tempfile.mkstemp(suffix='.png')
                os.close(temp_fd)  # Close file descriptor
                
                # Save as PNG
                img.save(temp_path, 'PNG')
                
                logger.info(f"Image converted and saved to: {temp_path}")
                return temp_path
                
        except Exception as e:
            logger.error(f"Error converting image format: {e}")
            # Return original path and let Textract handle the error
            return file_path
    
    def tables_to_dataframes(self, tables):
        """
        Convert Textract tables (list of lists) into pandas DataFrames - EXACT code from user
        """
        dataframes = []

        for table in tables:
            if not table:  # Skip empty tables
                continue
                
            # Ensure all rows are of equal length (pad with empty strings if needed)
            max_len = max(len(row) for row in table) if table else 0
            if max_len == 0:
                continue
                
            normalized = [row + [""] * (max_len - len(row)) for row in table]

            # Assume first row is header
            if len(normalized) > 1:
                df = pd.DataFrame(normalized[1:], columns=normalized[0])
                dataframes.append(df)
            elif len(normalized) == 1:
                # Single row, treat as key-value pairs if it has 2 columns
                if len(normalized[0]) == 2:
                    df = pd.DataFrame([normalized[0]], columns=['Field', 'Value'])
                    dataframes.append(df)

        return dataframes
    
    def process_image(self, image_path: str) -> pd.DataFrame:
        """
        Process image and return single combined DataFrame
        
        Args:
            image_path: Path to image file
            
        Returns:
            Single pandas DataFrame with extracted table data
        """
        try:
            # Check if file exists
            if not os.path.exists(image_path):
                logger.error(f"Image file not found: {image_path}")
                return pd.DataFrame()
            
            logger.info(f"Processing image with Textract: {image_path}")
            
            # Use the working Textract code
            forms, tables = self.extract_data_from_file(image_path)
            
            logger.info(f"Extracted {len(forms)} form fields and {len(tables)} tables")
            
            # Debug: Print what was extracted
            if forms:
                logger.info(f"Forms extracted: {list(forms.keys())[:5]}...")  # First 5 keys
                print("\n===== KEY VALUE PAIRS (Forms) =====")
                for k, v in list(forms.items())[:10]:  # First 10 key-value pairs
                    print(f"{k}: {v}")
            
            if tables:
                logger.info(f"Tables structure: {[len(table) for table in tables]} rows per table")
                print("\n===== TABLES (Raw) =====")
                for i, table in enumerate(tables):
                    print(f"\n--- Table {i+1} ---")
                    for row in table:
                        print(row)
                    print("-" * 50)
                
            # Convert forms to DataFrame if no tables found
            if not tables and forms:
                logger.info("No tables found, converting forms to DataFrame")
                df = pd.DataFrame(list(forms.items()), columns=['Field', 'Value'])
                logger.info(f"Forms DataFrame shape: {df.shape}")
                logger.info(f"Forms DataFrame preview:\n{df.head()}")
                return df
            
            # Convert tables to DataFrames
            if tables:
                logger.info(f"Processing {len(tables)} tables...")
                dataframes = self.tables_to_dataframes(tables)
                
                print("\n===== DATAFRAMES (Converted) =====")
                for i, df in enumerate(dataframes):
                    print(f"\n===== Table {i+1} =====")
                    print(df.to_string())
                    print(f"\nDataFrame Info: Shape={df.shape}, Columns={list(df.columns)}")
                
                if dataframes:
                    # Return the first DataFrame (or combine multiple if needed)
                    main_df = dataframes[0]
                    logger.info(f"Table DataFrame shape: {main_df.shape}")
                    logger.info(f"Table DataFrame columns: {list(main_df.columns)}")
                    logger.info(f"Table DataFrame preview:\n{main_df.head()}")
                    return main_df
                else:
                    logger.warning("Tables found but conversion to DataFrame failed")
                    # Fallback to forms
                    if forms:
                        logger.info("Falling back to forms data")
                        df = pd.DataFrame(list(forms.items()), columns=['Field', 'Value'])
                        logger.info(f"Fallback forms DataFrame shape: {df.shape}")
                        return df
            
            logger.warning("No tables or forms extracted - returning empty DataFrame")
            return pd.DataFrame()
            
        except Exception as e:
            logger.error(f"Error processing image {image_path}: {e}")
            return pd.DataFrame()
