"""
Service for interacting with AWS Bedrock for AI insights generation and SQL query execution
"""

import os
import json
import logging
import base64
import boto3
import re
import pymysql
import pandas as pd
from botocore.exceptions import ClientError
from io import StringIO
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from decimal import Decimal

# Configure logging
logger = logging.getLogger(__name__)

class BedrockService:
    """Service for interacting with AWS Bedrock for AI insights generation and SQL query execution"""

    def __init__(self):
        # Use the specified model ID or fallback to default
        self.model_id = os.environ.get('BEDROCK_MODEL_ID', 'us.anthropic.claude-3-7-sonnet-20250219-v1:0')
        self.aws_region = os.environ.get('AWS_REGION', 'us-east-1')

        # Check if we're in a local environment
        is_local = os.environ.get('ENVIRONMENT', 'local') == 'local'

        # Configure AWS clients differently based on environment
        if is_local:
            # Use profile in local environment
            profile_name = os.environ.get('AWS_PROFILE', 'sso-personal')
            session = boto3.Session(profile_name=profile_name, region_name=self.aws_region)
            self.bedrock_runtime = session.client('bedrock-runtime')
            logger.info(f"Using AWS profile '{profile_name}' in local environment")
        else:
            # Use standard credential provider chain in non-local environments
            self.bedrock_runtime = boto3.client('bedrock-runtime', region_name=self.aws_region)
        
        # Database configuration
        # You can replace these with your own database credentials
        self.db_config = {
            'host': os.environ.get('DB_HOST', ''),
            'user': os.environ.get('DB_USER', ''),
            'password': os.environ.get('DB_PASSWORD', ''),
            'db': os.environ.get('DB_NAME', ''),
            'port': int(os.environ.get('DB_PORT', 3306))
        }
        
        # Initialize database connection
        self.initialize_db_connection()

    def initialize_db_connection(self):
        """Initialize database connection"""
        try:
            # Create SQLAlchemy engine for database operations
            connection_string = f"mysql+pymysql://{self.db_config['user']}:{self.db_config['password']}@{self.db_config['host']}:{self.db_config['port']}/{self.db_config['db']}"
            self.engine = create_engine(connection_string)
            
            # Test connection
            with self.engine.connect() as connection:
                result = connection.execute(text("SELECT 1"))
                logger.info("Database connection successful")
                
            # Get database schema
            self.db_schema = self.get_database_schema()
            logger.info(f"Retrieved database schema with {len(self.db_schema)} tables")
            
        except SQLAlchemyError as e:
            logger.error(f"Database connection error: {e}")
            self.engine = None
            self.db_schema = ""
    
    def get_database_schema(self):
        """Get database schema information to provide context to the model"""
        if not self.engine:
            return "Database connection not available."
            
        schema_info = []
        
        try:
            with self.engine.connect() as connection:
                # Get all tables
                tables_query = """
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = :db_name
                """
                tables_result = connection.execute(text(tables_query), {"db_name": self.db_config['db']})
                tables = [row[0] for row in tables_result]
                
                # For each table, get column information
                for table in tables:
                    columns_query = """
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_schema = :db_name AND table_name = :table_name
                    """
                    columns_result = connection.execute(
                        text(columns_query), 
                        {"db_name": self.db_config['db'], "table_name": table}
                    )
                    columns = [f"{row[0]} ({row[1]})" for row in columns_result]
                    
                    table_info = f"Table: {table}\nColumns: {', '.join(columns)}\n"
                    schema_info.append(table_info)
                    
        except SQLAlchemyError as e:
            logger.error(f"Error retrieving database schema: {e}")
            return "Error retrieving database schema."
            
        return "\n".join(schema_info)

    def is_safe_query(self, query):
        """
        Check if the SQL query is safe (read-only)
        
        Args:
            query (str): SQL query to validate
            
        Returns:
            bool: True if the query is safe, False otherwise
        """
        # Convert to lowercase for case-insensitive matching
        query_lower = query.lower()
        
        # Check for write operations keywords
        unsafe_keywords = ['insert', 'update', 'delete', 'drop', 'alter', 'create', 'truncate', 
                          'replace', 'exec', 'execute', 'merge', 'grant', 'revoke', 'commit', 
                          'rollback', 'call', 'begin']
        
        # Check if query starts with any unsafe keyword
        for keyword in unsafe_keywords:
            pattern = r'^\s*' + keyword + r'\s'
            if re.search(pattern, query_lower):
                return False
                
        # Ensure query starts with SELECT or similar read operations
        select_pattern = r'^\s*(select|show|describe|explain|with)\s'
        if not re.search(select_pattern, query_lower):
            return False
            
        return True
    
    def generate_sql_query(self, natural_language_query):
        """
        Generate SQL query from natural language instruction
        
        Args:
            natural_language_query (str): Natural language instruction
            
        Returns:
            str: Generated SQL query
        """
        try:
            current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            # Create the system prompt with database schema and current date
            system_prompt = f"""
            You are an expert SQL assistant that helps users query a MySQL database.
            Your task is to generate a SQL query based on the user's natural language request.
            
            Current date and time: {current_datetime}

            Here is the database schema information:
            {self.db_schema}
            
            IMPORTANT RULES:
            1. ONLY generate SELECT queries. DO NOT generate any INSERT, UPDATE, DELETE, or other data modification queries.
            2. Make your queries as efficient as possible.
            3. Use proper table and column names from the schema provided.
            4. DO NOT include any explanations or markdown formatting in your response.
            5. Return ONLY the SQL query as plain text - nothing else.
            6. If the user request involves dates or time periods like "today", "this month", etc., use the current date provided above.
            
            Generate a SQL query for the following request:
            """

            # Generate SQL query using Bedrock model
            response = self.bedrock_runtime.converse(
                modelId=self.model_id,
                messages=[
                    {
                        'role': 'user',
                        'content': [
                            {
                                'text': natural_language_query
                            },
                        ]
                    }
                ],
                system=[
                    {
                        "text": system_prompt
                    }
                ],
                inferenceConfig={
                    'temperature': 0.1,  # Lower temperature for more focused output
                    'maxTokens': 1000,
                }
            )
            
            # Extract the SQL query from response
            sql_query = response['output']['message']['content'][0]['text']
            
            # Clean up any possible formatting in the response
            sql_query = sql_query.strip()
            if sql_query.startswith("```sql"):
                sql_query = sql_query[6:]
            if sql_query.endswith("```"):
                sql_query = sql_query[:-3]
            
            return sql_query.strip()
            
        except ClientError as e:
            logger.error(f"Bedrock error in SQL generation: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in SQL generation: {e}")
            raise
    
    @staticmethod
    def serialize_dataframe_results(result_list):
        """
        Convierte todos los tipos de datos no serializables a JSON en strings o None
        sin usar numpy
        """
        serialized_results = []
        
        for record in result_list:
            serialized_record = {}
            for key, value in record.items():
                # Manejar NaT de pandas
                if pd.isna(value) or (hasattr(pd, '_libs') and isinstance(value, pd._libs.NaTType)):
                    serialized_record[key] = None
                # Manejar Decimals
                elif isinstance(value, Decimal):
                    serialized_record[key] = float(value)
                # Manejar Timestamps de pandas
                elif isinstance(value, pd.Timestamp):
                    serialized_record[key] = value.isoformat()
                # Todos los demás tipos
                else:
                    try:
                        # Verificar si es serializable
                        json.dumps(value)
                        serialized_record[key] = value
                    except (TypeError, OverflowError):
                        # Si no es serializable, convertir a string
                        serialized_record[key] = str(value)
                        
            serialized_results.append(serialized_record)
        
        return serialized_results
    
    def execute_sql_query(self, sql_query):
        """
        Execute SQL query and return results
        
        Args:
            sql_query (str): SQL query to execute
            
        Returns:
            dict: Query results and metadata
        """
        if not self.engine:
            return {"error": "Database connection not available"}
            
        # Validate query is read-only
        if not self.is_safe_query(sql_query):
            return {"error": "Only read operations are allowed"}
            
        try:
            # Execute query
            with self.engine.connect() as connection:
                result = connection.execute(text(sql_query))
                
                # Convert result to DataFrame for easier manipulation
                df = pd.DataFrame(result.fetchall())
                if not df.empty:
                    df.columns = result.keys()
                
                # Convert DataFrame to dict for response
                if df.empty:
                    records = []
                else:
                    records = df.to_dict(orient='records')
                    records = self.serialize_dataframe_results(records)
                
                return {
                    "query": sql_query,
                    "result": records,
                    "row_count": len(records),
                    "column_names": list(df.columns) if not df.empty else []
                }
                
        except SQLAlchemyError as e:
            logger.error(f"Error executing SQL query: {e}")
            return {"error": f"Error executing SQL query: {str(e)}"}
            
    def natural_language_to_sql_result(self, natural_language_query):
        """
        Process a natural language query, convert it to SQL, execute it, and return results
        
        Args:
            natural_language_query (str): Natural language instruction
            
        Returns:
            dict: Results of the query execution and related metadata
        """
        try:
            # First check if database connection is available
            if not self.engine:
                return {
                    "error": "Database connection not available",
                    "natural_language_query": natural_language_query,
                    "sql_query": None,
                    "result": None
                }
                
            # Generate SQL query from natural language
            sql_query = self.generate_sql_query(natural_language_query)
            logger.info(f"Generated SQL query: {sql_query}")
            
            # Execute the generated SQL query
            query_result = self.execute_sql_query(sql_query)
            
            # Prepare and return response
            response = {
                "natural_language_query": natural_language_query,
                "sql_query": sql_query,
                "result": query_result.get("result", []),
                "row_count": query_result.get("row_count", 0),
                "column_names": query_result.get("column_names", []),
                "error": query_result.get("error", None)
            }
            
            # If there was an error in execution, log it
            if "error" in query_result:
                logger.warning(f"Error in query execution: {query_result['error']}")
                
            return response
            
        except Exception as e:
            logger.error(f"Error in natural language to SQL processing: {e}")
            return {
                "natural_language_query": natural_language_query,
                "sql_query": None,
                "result": None,
                "error": f"Failed to process query: {str(e)}"
            }