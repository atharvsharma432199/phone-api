from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import time
from functools import lru_cache
import database as db
import os
import subprocess
import threading

app = Flask(__name__)
CORS(app)

# Global variable to track database status
database_initialized = False
initialization_lock = threading.Lock()

def check_and_initialize_database():
    """Check if database exists and initialize if not"""
    global database_initialized
    
    with initialization_lock:
        if database_initialized:
            return True
            
        if not os.path.exists('phone_data.db'):
            print("📦 Database not found. Initializing...")
            try:
                result = subprocess.run(['python', 'init_database.py'], 
                                      capture_output=True, text=True, timeout=300)
                if result.returncode == 0:
                    print("✅ Database initialized successfully")
                    database_initialized = True
                    return True
                else:
                    print(f"❌ Database initialization failed: {result.stderr}")
                    return False
            except Exception as e:
                print(f"❌ Error initializing database: {str(e)}")
                return False
        else:
            print("✅ Database already exists")
            database_initialized = True
            return True

# Check database on startup
@app.before_first_request
def initialize_on_startup():
    """Initialize database before first request"""
    check_and_initialize_database()

@lru_cache(maxsize=1000)
def find_person_info(phone_query):
    """Find person information by phone number from SQLite database"""
    if not phone_query:
        return None
    
    # Clean the phone number (remove spaces, +91, etc.)
    clean_query = ''.join(filter(str.isdigit, str(phone_query)))
    
    if not clean_query:
        return None
    
    # Remove country code if present
    if clean_query.startswith('91') and len(clean_query) > 10:
        clean_query = clean_query[2:]
    
    try:
        conn = sqlite3.connect('phone_data.db')
        cursor = conn.cursor()
        
        # Search in phoneNumber field
        cursor.execute('''
        SELECT name, fathersName, phoneNumber, otherNumber, passportNumber, 
               aadharNumber, age, gender, address, district, pincode, state, town
        FROM phone_data 
        WHERE phoneNumber LIKE ? OR otherNumber LIKE ?
        ''', (f'%{clean_query}%', f'%{clean_query}%'))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'name': result[0],
                'fathersName': result[1],
                'phoneNumber': result[2],
                'otherNumber': result[3],
                'passportNumber': result[4],
                'aadharNumber': result[5],
                'age': result[6],
                'gender': result[7],
                'address': result[8],
                'district': result[9],
                'pincode': result[10],
                'state': result[11],
                'town': result[12]
            }
        return None
        
    except sqlite3.OperationalError as e:
        if "no such table" in str(e):
            print("❌ Phone data table not found. Database may need initialization.")
        return None
    except Exception as e:
        print(f"Database error: {str(e)}")
        return None

@app.route('/')
def api_root():
    """Main API endpoint with query parameters"""
    # Check if database is initialized
    if not check_and_initialize_database():
        return jsonify({
            "status": "error",
            "message": "Database initialization failed. Please try again later."
        }), 500
    
    start_time = time.time()
    api_key = request.args.get('apikey', '').strip()
    search_query = request.args.get('query', '').strip()
    
    # Validate API key
    if not api_key:
        return jsonify({
            "status": "error",
            "message": "API key is required. Use ?apikey=YOUR_KEY"
        }), 401
    
    # Check if API key is valid
    if not db.can_use_key(api_key):
        key_details = db.get_api_key_details(api_key)
        if not key_details:
            return jsonify({
                "status": "error",
                "message": "Invalid API key"
            }), 401
        else:
            return jsonify({
                "status": "error",
                "message": "API key limit exceeded or inactive"
            }), 403
    
    # Validate search query
    if not search_query:
        db.log_usage(api_key, "NO_QUERY", False, 0)
        return jsonify({
            "status": "error",
            "message": "Query parameter is required. Use &query=PHONE_NUMBER"
        }), 400
    
    # Find person information
    result = find_person_info(search_query)
    response_time = time.time() - start_time
    
    if result:
        # Increment usage and log success
        db.increment_usage(api_key)
        db.log_usage(api_key, search_query, True, response_time)
        
        return jsonify({
            "status": "success",
            "data": result,
            "usage": db.get_api_key_details(api_key)['current_usage'],
            "response_time": f"{response_time:.3f}s"
        })
    else:
        # Log failure
        db.log_usage(api_key, search_query, False, response_time)
        
        return jsonify({
            "status": "error",
            "message": "Phone number not found in database",
            "response_time": f"{response_time:.3f}s"
        }), 404

@app.route('/api/status')
def api_status():
    """Check API status"""
    try:
        # Check if database is initialized first
        if not check_and_initialize_database():
            return jsonify({
                "status": "error",
                "message": "Database not initialized"
            }), 500
        
        # Get phone database stats
        conn = sqlite3.connect('phone_data.db')
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM phone_data')
        record_count = cursor.fetchone()[0]
        conn.close()
        
        # Get API stats
        key_count = len(db.get_all_api_keys())
        active_keys = len([k for k in db.get_all_api_keys() if k['is_active']])
        usage_stats = db.get_usage_stats()
        
        return jsonify({
            "status": "active",
            "database": {
                "records": record_count,
                "initialized": True
            },
            "api": {
                "total_keys": key_count,
                "active_keys": active_keys,
                "total_calls": usage_stats['total_calls'],
                "today_calls": usage_stats['today_calls'],
                "success_rate": f"{usage_stats['success_rate']:.1f}%"
            },
            "message": "API is running successfully"
        })
        
    except sqlite3.OperationalError as e:
        if "no such table" in str(e):
            return jsonify({
                "status": "error",
                "message": "Database table not found. Please initialize database.",
                "initialization_url": "/api/admin/initdb?user=admin&pass=admin123"
            }), 500
        else:
            return jsonify({
                "status": "error",
                "message": f"Database error: {str(e)}"
            }), 500
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Error getting status: {str(e)}"
        }), 500

@app.route('/api/admin/initdb')
def admin_init_db():
    """Admin endpoint to initialize database"""
    admin_user = request.args.get('user')
    admin_pass = request.args.get('pass')
    
    if not db.validate_admin(admin_user, admin_pass):
        return jsonify({
            "status": "error",
            "message": "Admin authentication failed"
        }), 401
    
    try:
        result = subprocess.run(['python', 'init_database.py'], 
                              capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            # Reset initialization flag
            global database_initialized
            database_initialized = True
            
            return jsonify({
                "status": "success",
                "message": "Database initialized successfully",
                "records": get_record_count(),
                "output": result.stdout[-500:]  # Last 500 characters only
            })
        else:
            return jsonify({
                "status": "error",
                "message": "Database initialization failed",
                "error": result.stderr[-500:]  # Last 500 characters only
            }), 500
            
    except subprocess.TimeoutExpired:
        return jsonify({
            "status": "error",
            "message": "Database initialization timeout (5 minutes)"
        }), 500
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Error: {str(e)}"
        }), 500

def get_record_count():
    """Get number of records in phone_data table"""
    try:
        conn = sqlite3.connect('phone_data.db')
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM phone_data')
        count = cursor.fetchone()[0]
        conn.close()
        return count
    except:
        return 0

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    # Initialize database on startup
    check_and_initialize_database()
    app.run(host='0.0.0.0', port=port, debug=False)
