# Analytics AI Agent

This project implements an intelligent analytics agent that enables users to query business transaction data using natural language. Leveraging a comprehensive dataset of transactional records sourced from Kaggle, the system employs large language model (LLM) technology to automatically convert user questions into SQL queries, execute them against a SQLite database, and generate actionable insights. This approach eliminates the need for SQL expertise, making data analytics accessible to non-technical stakeholders through a conversational chat interface.

The system demonstrates practical integration of generative AI into business intelligence workflows, showcasing how modern LLM capabilities can transform raw transactional data into meaningful business insights through natural language interaction.

## System Architecture

```
User Query (Natural Language)
        ↓
[Flask Web Server]
        ↓
[Query Analysis] ← Groq LLM analyzes intent
        ↓
[SQL Generation] ← LLM creates optimized query
        ↓
[Query Validation] ← Safety checks
        ↓
[Database Execution] ← SQLite query execution
        ↓
[Insights Generation] ← LLM interprets results
        ↓
Formatted Response (Human-readable)
```

---



### Core Components
**Backend Framework**  
- **Flask**: Python web framework for handling HTTP requests and routing
- **SQLite**: Lightweight relational database for transaction storage
- **Gunicorn**: Production WSGI server for deployment

**AI/LLM Integration**  
- **Groq Cloud API**: High-performance LLM inference platform
- **Model**: Llama 3.3 70B Versatile - Advanced language model for query understanding and SQL generation
- **Free Tier**: 14,400 requests/day, suitable for demo and small-scale applications

**Supporting Libraries**  
- **requests**: HTTP client for API communication
- **python-dotenv**: Environment variable management for secure API key storage

**Deployment**  
- **Platform**: Render (free tier)
- **Version Control**: Git/GitHub
- **CI/CD**: Automatic deployment on code push
