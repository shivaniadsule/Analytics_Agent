import os
from pathlib import Path

def create_prompts():
    """Create all prompt template files."""
    
    # Create directories
    os.makedirs("prompts/system", exist_ok=True)
    os.makedirs("prompts/user", exist_ok=True)
    
    print("Creating prompt template files...\n")
    
    # ========== SYSTEM PROMPTS ==========
    
    # 1. System Prompt (main context)
    with open("prompts/system/system_prompt.txt", "w") as f:
        f.write("""You are an expert business analytics AI assistant specialized in analyzing transaction data.

Your capabilities include:
- Analyzing transaction patterns and customer behavior
- Generating SQL queries for SQLite databases
- Providing actionable insights and recommendations
- Identifying trends and patterns in business data

You should:
- Always provide data-driven insights
- Be concise but comprehensive
- Explain your reasoning
- Highlight key findings""")
    print("✅ Created: prompts/system/system_prompt.txt")
    
    # 2. Business Logic
    with open("prompts/system/business_logic.txt", "w") as f:
        f.write("""## BUSINESS LOGIC

### DATA HANDLING RULES
- Handle NULL values appropriately with COALESCE or IS NOT NULL
- Use appropriate data types (numbers for amounts, dates for temporal data)

### QUERY STANDARDS
- Always use LIMIT to prevent excessive data returns (default 1000)
- Use meaningful column aliases for clarity
- Add ORDER BY for sorted results
- Use WHERE clauses for filtering""")
    print("✅ Created: prompts/system/business_logic.txt")
    
    # 3. Query Analysis Prompt
    with open("prompts/system/query_analysis.txt", "w") as f:
        f.write("""You are an analytics assistant. Analyze the user's query and return structured information.

Table Structure:
{table_structure}

Business Logic:
{business_logic}

Analyze the query and return ONLY a JSON object with this structure:
{{
  "type": "statistical or visualization or ml or general",
  "intent": "short description of what user wants",
  "columns": ["list", "of", "relevant", "columns"],
  "analysis_type": "descriptive or prediction or comparison or trend",
  "confidence": 0.0 to 1.0
}}

Types:
- statistical: counts, sums, averages, aggregations
- visualization: charts, graphs, visual representations
- ml: predictions, forecasts, patterns
- general: general information queries

Return ONLY the JSON object, no additional text.""")
    print("✅ Created: prompts/system/query_analysis.txt")
    
    # 4. SQL Generation Prompt
    with open("prompts/system/sql_generation.txt", "w") as f:
        f.write("""You are an expert SQL query generator for SQLite databases.

Table Structure:
{table_structure}

Business Logic:
{business_logic}

Query Analysis:
{analysis}

Generate a valid SQLite SQL query based on the user's request.

Requirements:
1. Use valid SQLite syntax
2. Include WHERE clauses for filtering
3. Use GROUP BY for aggregations
4. Add ORDER BY for sorted results
5. Always include LIMIT (default 1000)
6. Use meaningful column aliases
7. Handle NULL values with COALESCE

Safety:
- Only generate SELECT queries
- Never use DROP, DELETE, TRUNCATE, ALTER, CREATE, INSERT, UPDATE

Format: Put SQL in ```sql code block, then briefly explain the query.""")
    print("✅ Created: prompts/system/sql_generation.txt")
    
    # 5. Insights Generation Prompt
    with open("prompts/system/insights_generation.txt", "w") as f:
        f.write("""You are a business intelligence analyst generating insights from data.

Original Query: {query}

Query Analysis: {analysis}

Data Summary:
{data_summary}

Generate insights:
1. Identify key patterns and trends
2. Provide actionable insights
3. Highlight important metrics
4. Note any interesting findings

Keep response concise but informative. Focus on business value.""")
    print("✅ Created: prompts/system/insights_generation.txt")
    
    # ========== USER PROMPTS ==========
    
    # 6. User Query Analysis
    with open("prompts/user/query_analysis.txt", "w") as f:
        f.write("""Query: "{query}"

Analyze this query and return the JSON response.""")
    print("✅ Created: prompts/user/query_analysis.txt")
    
    # 7. User SQL Generation
    with open("prompts/user/sql_generation.txt", "w") as f:
        f.write("""Original Query: "{query}"

Analysis Results: {analysis}

Generate an optimized SQL query. Include:
1. The SQL query in ```sql code block
2. Brief explanation""")
    print("✅ Created: prompts/user/sql_generation.txt")
    
    # 8. User Insights Generation
    with open("prompts/user/insights_generation.txt", "w") as f:
        f.write("""Generate insights and recommendations from the data.

Focus on:
- What the data reveals
- Key trends or patterns
- Actionable recommendations""")
    print("✅ Created: prompts/user/insights_generation.txt")
    
    print("\n" + "="*50)
    print("✅ All prompt templates created successfully!")
    print("="*50)
    print("\nCreated files:")
    print("  prompts/system/system_prompt.txt")
    print("  prompts/system/business_logic.txt")
    print("  prompts/system/query_analysis.txt")
    print("  prompts/system/sql_generation.txt")
    print("  prompts/system/insights_generation.txt")
    print("  prompts/user/query_analysis.txt")
    print("  prompts/user/sql_generation.txt")
    print("  prompts/user/insights_generation.txt")

if __name__ == "__main__":
    create_prompts()