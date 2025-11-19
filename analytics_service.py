import sqlite3
from typing import Dict, Any, List
from pathlib import Path
from llm_client import LLMClient

class AnalyticsService:
    
    def __init__(self, db_path: str = "kaggle_transactions.sqlite"):
        """
        Initialize Analytics Service.
        
        Args:
            db_path: Path to your SQLite database
        """
        self.db_path = db_path
        self.llm_client = LLMClient()  # Groq connection
        self.table_structure = self._load_table_structure()
        self.business_logic = self._load_business_logic()
        
        print(f"Analytics Service initialized")
        print(f"   Database: {db_path}")
    
    def _load_table_structure(self) -> str:
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            
            structure = "DATABASE SCHEMA:\n" + "="*60 + "\n\n"
            
            for (table_name,) in tables:
                structure += f"Table: {table_name}\n"
                structure += "-" * 40 + "\n"
                
                # Get columns
                cursor.execute(f"PRAGMA table_info({table_name});")
                columns = cursor.fetchall()
                
                structure += "Columns:\n"
                for col in columns:
                    col_id, name, type_, notnull, default, pk = col
                    structure += f"  - {name} ({type_})"
                    if pk:
                        structure += " [PRIMARY KEY]"
                    structure += "\n"
                
                # Get row count
                cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
                count = cursor.fetchone()[0]
                structure += f"\nTotal rows: {count:,}\n\n"
            
            conn.close()
            print(f"    Loaded database schema")
            return structure
            
        except Exception as e:
            print(f"    Could not load database schema: {e}")
            return "Database schema not available"
    
    def _load_business_logic(self) -> str:
        """Load business logic rules from prompts folder."""
        try:
            logic_path = Path("prompts/system/business_logic.txt")
            if logic_path.exists():
                with open(logic_path, 'r') as f:
                    return f.read()
        except Exception as e:
            print(f"     Could not load business logic: {e}")
        
        return "No specific business logic defined"
    
    def execute_sql(self, sql: str) -> List[Dict[str, Any]]:
        """
        Execute SQL query on database and return results.
        
        Args:
            sql: SQL query to execute
            
        Returns:
            List of row dictionaries
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        cursor = conn.cursor()
        
        try:
            print(f"\n Executing SQL query...")
            cursor.execute(sql)
            rows = cursor.fetchall()
            
            # Convert to list of dicts
            results = [dict(row) for row in rows]
            
            print(f" Retrieved {len(results)} rows")
            return results
            
        except Exception as e:
            print(f" SQL execution failed: {str(e)}")
            raise Exception(f"SQL execution error: {str(e)}")
        finally:
            conn.close()
    
    def analyze_query_full(self, user_query: str) -> Dict[str, Any]:
        """
        Full analytics pipeline - this is the main function!
        
        Steps:
        1. Groq analyzes the query (understands what user wants)
        2. Groq generates SQL (creates database query)
        3. System validates SQL (safety checks)
        4. System executes SQL (runs on database)
        5. Groq generates insights (explains results)
        
        Args:
            user_query: User's question in plain English
            
        Returns:
            Dict with all results (analysis, sql, data, insights)
        """
        print("\n" + "="*60)
        print(f" User Query: {user_query}")
        print("="*60)
        
        try:
            # STEP 1: Analyze query (Groq understands the question)
            analysis = self.llm_client.analyze_query(
                query=user_query,
                table_structure=self.table_structure,
                business_logic=self.business_logic
            )
            
            # STEP 2: Generate SQL (Groq creates the query)
            sql_result = self.llm_client.generate_sql(
                query=user_query,
                analysis=analysis,
                table_structure=self.table_structure,
                business_logic=self.business_logic
            )
            
            # STEP 3: Validate SQL (safety checks)
            validation = self.llm_client.validate_sql(sql_result['sql'])
            if not validation['valid']:
                return {
                    "success": False,
                    "error": f"SQL validation failed: {', '.join(validation['errors'])}",
                    "analysis": analysis,
                    "sql": sql_result['sql']
                }
            
            # STEP 4: Execute SQL (run on database)
            print("\n" + "="*60)
            print("STEP 4: Executing Query")
            print("="*60)
            data = self.execute_sql(sql_result['sql'])
            
            # STEP 5: Generate insights (Groq explains results)
            insights = self.llm_client.generate_insights(
                query=user_query,
                data=data,
                analysis=analysis
            )
            
            print("\n" + "="*60)
            print("ANALYSIS COMPLETE")
            print("="*60)
            
            return {
                "success": True,
                "analysis": analysis,
                "sql": sql_result['sql'],
                "sql_explanation": sql_result['explanation'],
                "data": data,
                "data_count": len(data),
                "insights": insights
            }
            
        except Exception as e:
            print(f"\n Analysis failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "user_query": user_query
            }
    
    def format_response(self, result: Dict[str, Any]) -> str:
        """
        Format the result into a nice text response for the user.
        
        Args:
            result: Result from analyze_query_full
            
        Returns:
            Formatted text response
        """
        if not result.get("success"):
            return f" Error: {result.get('error', 'Unknown error occurred')}"
        
        response = []
        
        # Add insights from Groq
        if result.get("insights"):
            # response.append(" Insights:")
            response.append(result["insights"])
            response.append("")
        
        # Add data summary
        data_count = result.get("data_count", 0)
        if data_count > 0:
            response.append(f" Found {data_count} records")
            
            # Show sample of data
            data = result.get("data", [])
            if data:
                response.append("\nSample data:")
                for i, row in enumerate(data[:5], 1):
                    # Show first 3 columns of each row
                    items = list(row.items())[:3]
                    row_str = ", ".join([f"{k}: {v}" for k, v in items])
                    response.append(f"  {i}. {row_str}")
                    if len(row) > 3:
                        response[-1] += "..."
                
                if data_count > 5:
                    response.append(f"  ... and {data_count - 5} more")
        else:
            response.append(" No data found matching your criteria.")
        
        # Add SQL query used (for transparency)
        # if result.get("sql"):
        #     response.append(f"\n💻 SQL Query used:")
        #     response.append(f"```\n{result['sql']}\n```")
        
        return "\n".join(response)



def analytics_query(user_query: str) -> str:
    
    service = AnalyticsService()
    result = service.analyze_query_full(user_query)
    return service.format_response(result)