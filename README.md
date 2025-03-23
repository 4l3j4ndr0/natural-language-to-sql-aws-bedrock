> ```markdown
> # Natural Language to SQL AI API
>
> A lightweight Flask API that translates natural language queries into SQL, executes them securely against your database, and returns the results. Powered by AWS Bedrock and Claude AI.
>
> ## Overview
>
> This API allows non-technical users to query databases using natural language, democratizing access to data insights without requiring SQL knowledge. The service ensures security by allowing only read operations while providing rich context and explanations.
> ```

> ## Features
>
> - **Natural Language to SQL Translation**: Convert plain English questions into optimized SQL queries
> - **Secure Query Execution**: Only read operations (SELECT, SHOW, etc.) are permitted
> - **Database Schema Understanding**: Automatically extracts and understands your database structure
> - **Result Explanation**: Optional AI-generated explanations of query results in plain language
> - **Performance Metrics**: Track processing time and query efficiency
>
> ## Setup & Installation
>
> ### Prerequisites
>
> - Python 3.9 or higher
> - AWS account with Bedrock access
> - MySQL-compatible database
>
> ### Installation
>
> 1. Clone the repository:
>
> ```bash
> git clone https://github.com/yourusername/natural-language-to-sql-aws-bedrock.git
> cd natural-language-to-sql-aws-bedrock
> ```
>
> ````
>
> 2. Create and activate a virtual environment:
>
> ```bash
> python -m venv venv
> source venv/bin/activate  # On Windows: venv\Scripts\activate
> ```
>
> 3. Install dependencies:
>
> ```bash
> pip install -r requirements.txt
> ```
>
> 4. Create a `.env` file based on `.env.example`:
>
> ```bash
> cp .env.example .env
> # Edit the .env file with your configurations
> ```
>
> 5. Configure AWS credentials:
>    - For local development: Set up AWS CLI profile (`aws configure`) or
>    - Configure environment variables in `.env`
>
> ```
> AWS_PROFILE=your-profile-name
> AWS_REGION=your-aws-region
> BEDROCK_MODEL_ID=us.anthropic.claude-3-7-sonnet-20250219-v1:0
> ```
>
> 6. Configure database connection:
>
> ```
> DB_HOST=your-database-host
> DB_USER=your-database-user
> DB_PASSWORD=your-database-password
> DB_NAME=your-database-name
> DB_PORT=3306
> ```
>
> 7. Start the server:
>
> ```bash
> flask run
> ```
>
> ## API Endpoints
>
> ### Natural Language to SQL Query
>
> **POST /api/sql-query**
>
> Translates a natural language question into SQL, executes it, and returns the results.
>
> **Request:**
>
> ```json
> {
>   "query": "What were the total sales by product category last month?"
> }
> ```
>
> **Response:**
>
> ```json
> {
>   "natural_language_query": "What were the total sales by product category last month?",
>   "sql_query": "SELECT p.category, SUM(s.amount) as total_sales FROM sales s JOIN products p ON s.product_id = p.id WHERE s.sale_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 1 MONTH) GROUP BY p.category ORDER BY total_sales DESC",
>   "result": [
>     { "category": "Electronics", "total_sales": 45280.5 },
>     { "category": "Furniture", "total_sales": 28350.75 },
>     { "category": "Clothing", "total_sales": 15420.25 }
>   ],
>   "row_count": 3,
>   "column_names": ["category", "total_sales"],
>   "processing_time": 1.25
> }
> ```
>
> ### Health Check
>
> **GET /health**
>
> Checks if the API is functioning correctly.
>
> **Response:**
>
> ```json
> {
>   "status": "healthy"
> }
> ```
>
> ## Security Considerations
>
> The service implements several security measures:
>
> 1. **Read-Only Operations**: The system validates all generated queries to ensure they only perform read operations
> 2. **SQL Injection Protection**: Input is never directly incorporated into SQL queries
> 3. **Access Control**: The database user should be configured with read-only permissions
> 4. **Connection Security**: Database credentials are stored as environment variables, not in code
>
> ## Architecture
>
> The application consists of two main components:
>
> 1. **Flask API (app.py)**: Handles HTTP requests and responses
> 2. **Bedrock Service (bedrock_service.py)**: Core logic including:
>    - Database schema extraction
>    - Natural language to SQL translation
>    - Query security validation
>    - Database execution
>    - Result formatting
>
> ## Extending the API
>
> To add new AI-powered functionality:
>
> 1. Enhance the `BedrockService` class with additional methods
> 2. Create new endpoints in `app.py`
> 3. Update documentation as needed
>
> ## Deployment
>
> ### Local Development
>
> ```bash
> flask run --debug
> ```
>
> ### Production with Gunicorn
>
> ```bash
> gunicorn -w 4 -b 0.0.0.0:5000 app:app
> ```
>
> ### With Docker
>
> 1. Build the image: `docker build -t natural-language-to-sql-ai-api .`
> 2. Run the container: `docker run -p 5000:5000 natural-language-to-sql-ai-api`
>
> ## Testing the API
>
> You can test the API using curl:
>
> ```bash
> curl -X POST http://localhost:5000/api/sql-query \
>   -H "Content-Type: application/json" \
>   -d '{"query": "Show me the top 5 customers by revenue", "explain_results": true}'
> ```
>
> Or use the included test script:
>
> ```bash
> python tests/test_api.py
> ```
>
> ## Example Database
>
> For testing purposes, you can use a publicly available test database:
>
> - [MySQL Sample Database](https://www.mysqltutorial.org/mysql-sample-database.aspx)
> - [Microsoft's Adventure Works](https://learn.microsoft.com/en-us/sql/samples/adventureworks-install-configure)
>
> ## License
>
> This project is licensed under the MIT License - see the LICENSE file for details.
>
> ## Acknowledgments
>
> - AWS Bedrock and Anthropic's Claude for powering the AI capabilities
> - SQLAlchemy for database abstraction
> - Flask framework for the API layer
>
> ```
>
> This README provides a comprehensive overview of your Natural Language to SQL API, including:
>
> 1. Clear description of what the application does
> 2. Detailed setup instructions for different environments
> 3. API endpoint documentation with examples
> 4. Security considerations
> 5. Architecture overview
> 6. Deployment options
> 7. Example test databases for users to get started quickly
>
> The README now accurately reflects the functionality in your app.py and bedrock_service.py files, focusing on the natural language to SQL query feature that forms the core of your application.
> ```
> ````
