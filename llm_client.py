import os
import json
import re
import requests
from typing import Dict, Any, List
from pathlib import Path

class LLMClient:
    """
    LLM client for Groq API.
    Handles all AI interactions for analytics.
    """
    
    def __init__(self):
        """Initialize Groq client."""
        self.api_key = os.getenv("GROQ_API_KEY")
        self.model = "llama-3.3-70b-versatile"  # Updated to current model
        self.base_url = "https://api.groq.com/openai/v1"
        self.prompts_cache = {}
        self.prompts_dir = Path("prompts")
        
        if not self.api_key:
            raise ValueError(
                "❌ GROQ_API_KEY not found!\n"
                "Set it: export GROQ_API_KEY='your_key_here'"
            )
        
        print(f"🤖 Groq AI initialized with model: {self.model}")
    
    def load_prompt(self, prompt_type: str, category: str = "system") -> str:
        """Load prompt template from file."""
        cache_key = f"{category}_{prompt_type}"
        
        if cache_key in self.prompts_cache:
            return self.prompts_cache[cache_key]
        
        prompt_path = self.prompts_dir / category / f"{prompt_type}.txt"
        
        if not prompt_path.exists():
            raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
        
        with open(prompt_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        self.prompts_cache[cache_key] = content
        return content
    
    def load_prompt_with_auto_split(self, prompt_type: str, **variables) -> Dict[str, str]:
        """Load system and user prompts and inject variables."""
        try:
            system_prompt = self.load_prompt(prompt_type, "system")
            user_prompt = self.load_prompt(prompt_type, "user")
        except FileNotFoundError:
            system_prompt = self.load_prompt("system_prompt", "system")
            user_prompt = "Query: {query}"
        
        # Replace {placeholders} with actual values
        system_prompt = self._inject_variables(system_prompt, variables)
        user_prompt = self._inject_variables(user_prompt, variables)
        
        return {"system": system_prompt, "user": user_prompt}
    
    def _inject_variables(self, template: str, variables: Dict[str, Any]) -> str:
        """Replace {variable} placeholders in template."""
        for key, value in variables.items():
            placeholder = f"{{{key}}}"
            if placeholder in template:
                template = template.replace(placeholder, str(value))
        return template
    
    def generate_response(self, system_prompt: str, user_prompt: str) -> str:
        """
        Call Groq API to generate response.
        
        Args:
            system_prompt: Instructions for the AI
            user_prompt: The actual question/request
            
        Returns:
            AI's response text
        """
        try:
            print(f"💭 Calling Groq API...")
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "max_tokens": 4000,
                    "temperature": 0.7
                },
                timeout=60
            )
            
            response.raise_for_status()
            data = response.json()
            
            result = data["choices"][0]["message"]["content"].strip()
            print(f"✅ Got response ({len(result)} characters)")
            
            return result
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                raise Exception("❌ Invalid Groq API key! Check your GROQ_API_KEY")
            elif e.response.status_code == 429:
                raise Exception("❌ Groq rate limit reached. Wait a minute and try again.")
            else:
                raise Exception(f"❌ Groq API error: {str(e)}")
        except Exception as e:
            raise Exception(f"❌ Groq API call failed: {str(e)}")
    
    def parse_json_response(self, response: str) -> Dict[str, Any]:
        """Parse JSON from AI response."""
        # Remove markdown code blocks
        response = re.sub(r'```json\s*', '', response)
        response = re.sub(r'```\s*', '', response)
        response = response.strip()
        
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            # Try to find JSON in the text
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group(0))
                except:
                    pass
            
            raise ValueError(f"Failed to parse JSON from response")
    
    def analyze_query(self, query: str, table_structure: str, business_logic: str = "") -> Dict[str, Any]:
        """
        STEP 1: Analyze user query to understand intent.
        
        Args:
            query: User's question
            table_structure: Database schema
            business_logic: Business rules
            
        Returns:
            Analysis JSON: {type, intent, columns, analysis_type, confidence}
        """
        print("\n" + "="*60)
        print("STEP 1: Analyzing Query")
        print("="*60)
        
        prompts = self.load_prompt_with_auto_split(
            "query_analysis",
            query=query,
            table_structure=table_structure,
            business_logic=business_logic
        )
        
        response = self.generate_response(prompts["system"], prompts["user"])
        
        try:
            analysis = self.parse_json_response(response)
            print(f"✅ Analysis: {analysis}")
            return analysis
        except ValueError:
            print(f"⚠️  JSON parsing failed, using fallback")
            return self._fallback_query_analysis(query)
    
    def _fallback_query_analysis(self, query: str) -> Dict[str, Any]:
        """Fallback if AI response can't be parsed."""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ['count', 'sum', 'average', 'total', 'how many']):
            query_type = "statistical"
        else:
            query_type = "general"
        
        return {
            "type": query_type,
            "intent": query,
            "columns": [],
            "analysis_type": "descriptive",
            "confidence": 0.5
        }
    
    def generate_sql(self, query: str, analysis: Dict[str, Any], 
                     table_structure: str, business_logic: str = "") -> Dict[str, Any]:
        """
        STEP 2: Generate SQL query from analysis.
        
        Returns:
            {sql: "SELECT ...", explanation: "..."}
        """
        print("\n" + "="*60)
        print("STEP 2: Generating SQL")
        print("="*60)
        
        prompts = self.load_prompt_with_auto_split(
            "sql_generation",
            query=query,
            analysis=json.dumps(analysis, indent=2),
            table_structure=table_structure,
            business_logic=business_logic
        )
        
        response = self.generate_response(prompts["system"], prompts["user"])
        sql = self._extract_sql(response)
        
        print(f"✅ Generated SQL:\n{sql}\n")
        
        return {"sql": sql, "explanation": response}
    
    def _extract_sql(self, response: str) -> str:
        """Extract SQL from AI response."""
        # Look for ```sql code blocks
        sql_match = re.search(r'```sql\s*(.*?)\s*```', response, re.DOTALL | re.IGNORECASE)
        if sql_match:
            return sql_match.group(1).strip()
        
        # Look for SELECT statements
        select_match = re.search(r'(SELECT\s+.*?(?:;|$))', response, re.DOTALL | re.IGNORECASE)
        if select_match:
            return select_match.group(1).strip()
        
        return response.strip()
    
    def validate_sql(self, sql: str) -> Dict[str, Any]:
        """
        STEP 3: Validate SQL for safety.
        
        Returns:
            {valid: bool, errors: []}
        """
        print("\n" + "="*60)
        print("STEP 3: Validating SQL")
        print("="*60)
        
        errors = []
        sql_upper = sql.upper().strip()
        
        # Must start with SELECT
        if not (sql_upper.startswith('SELECT') or sql_upper.startswith('WITH')):
            errors.append("Query must start with SELECT")
        
        # No dangerous keywords
        dangerous = ['DROP', 'DELETE', 'TRUNCATE', 'ALTER', 'CREATE', 'INSERT', 'UPDATE']
        for keyword in dangerous:
            if keyword in sql_upper:
                errors.append(f"Dangerous keyword: {keyword}")
        
        # Balanced parentheses
        if sql.count('(') != sql.count(')'):
            errors.append("Unbalanced parentheses")
        
        if errors:
            print(f"❌ Validation failed: {errors}")
        else:
            print("✅ SQL validation passed")
        
        return {"valid": len(errors) == 0, "errors": errors}
    
    def generate_insights(self, query: str, data: List[Dict], analysis: Dict[str, Any]) -> str:
        """
        STEP 5: Generate insights from results.
        
        Returns:
            Insights text
        """
        print("\n" + "="*60)
        print("STEP 5: Generating Insights")
        print("="*60)
        
        data_summary = self._summarize_data(data)
        
        prompts = self.load_prompt_with_auto_split(
            "insights_generation",
            query=query,
            analysis=json.dumps(analysis, indent=2),
            data_summary=data_summary
        )
        
        insights = self.generate_response(prompts["system"], prompts["user"])
        print(f"✅ Generated insights")
        
        return insights
    
    def _summarize_data(self, data: List[Dict], max_rows: int = 10) -> str:
        """Summarize data for AI."""
        if not data:
            return "No data returned"
        
        summary = f"Total rows: {len(data)}\n\n"
        summary += f"Sample (first {min(len(data), max_rows)} rows):\n"
        summary += json.dumps(data[:max_rows], indent=2, default=str)
        
        return summary