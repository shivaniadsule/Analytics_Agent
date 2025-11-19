import os
import sqlite3
from flask import Flask, render_template, request, session, redirect, url_for

from dotenv import load_dotenv
load_dotenv()  

from analytics_service import analytics_query

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'your_secret_here_change_later')

def get_db_connection():
    """Get database connection."""
    conn = sqlite3.connect('kaggle_transactions.sqlite')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/', methods=['GET', 'POST'])
def index():
    """Main chat interface."""
    if 'history' not in session:
        session['history'] = []
    
    if request.method == 'POST':
        user_query = request.form.get('query', '').strip()
        
        if user_query:
            try:
                print(f"\n{'='*60}")
                print(f" New Query: {user_query}")
                print(f"{'='*60}")
                
                answer = analytics_query(user_query)
                
            except Exception as e:
                error_msg = str(e)
                print(f" Error: {error_msg}")
                
                if "GROQ_API_KEY" in error_msg:
                    answer = (
                        " Groq API key not configured!\n\n"
                        "Please set your API key:\n"
                        "export GROQ_API_KEY='your_key_here'\n\n"
                        "Get free key at: https://console.groq.com/keys"
                    )
                else:
                    answer = f" Error: {error_msg}"
            
            # Add to conversation history
            history = session['history']
            history.append({
                'question': user_query,
                'answer': answer
            })
            session['history'] = history
    
    return render_template('index.html', history=session.get('history', []))

@app.route('/clear', methods=['POST'])
def clear_history():
    """Clear conversation history."""
    session.clear()  
    session['history'] = []  
    session.modified = True  
    return redirect(url_for('index'))

@app.route('/health')
def health():
    """Health check endpoint."""
    checks = {}
    
    # Check database
    try:
        conn = get_db_connection()
        conn.execute('SELECT 1')
        conn.close()
        checks['database'] = 'connected'
    except Exception as e:
        checks['database'] = f'error: {str(e)}'
    
    checks['groq_api_key'] = 'configured' if os.getenv('GROQ_API_KEY') else 'missing'
    
    checks['prompts'] = 'found' if os.path.exists('prompts') else 'missing'
    
    status = 'healthy' if all(v in ['connected', 'configured', 'found'] for v in checks.values()) else 'degraded'
    
    return {'status': status, 'checks': checks}, 200

if __name__ == '__main__':
    print("\n" + "="*60)
    print(" Analytics Agent with Groq AI")
    print("="*60)
    
    # Check database
    if not os.path.exists('kaggle_transactions.sqlite'):
        print("  WARNING: Database not found!")
        print("   Run: python Dataset.py")
    else:
        print(" Database found")
    
    # Check prompts
    if not os.path.exists('prompts'):
        print("  WARNING: Prompts directory not found!")
        print("   Run: python setup_prompts.py")
    else:
        print(" Prompts directory found")
    
    if os.getenv('GROQ_API_KEY'):
        print(" Groq API key configured")
    else:
        print(" Groq API key NOT configured!")
        print("   Set it: export GROQ_API_KEY='your_key_here'")
        print("   Get key: https://console.groq.com/keys")
    
    port = int(os.environ.get('PORT', 5000))
    
    is_production = os.getenv('FLASK_ENV') == 'production'
    
    if is_production:
        print(f"\n Starting in PRODUCTION mode on port {port}")
    else:
        print(f"\n Starting in DEVELOPMENT mode at: http://127.0.0.1:{port}")
        print("   Health check: http://127.0.0.1:5000/health")
        print("\n Try asking:")
        print("   - How many transactions are in the database?")
        print("   - What is the average transaction amount?")
        print("   - Show me the top 5 transactions")
    
    print("="*60 + "\n")
    
    
    app.run(
        host='0.0.0.0',           
        port=port,                 
        debug=not is_production    
    )