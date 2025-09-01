import sqlite3
import json
from datetime import datetime, timedelta
import os
import hashlib

def init_db():
    """Initialize database with required tables"""
    conn = sqlite3.connect('api_keys.db')
    cursor = conn.cursor()
    
    # Create API keys table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS api_keys (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        key TEXT UNIQUE NOT NULL,
        owner TEXT NOT NULL,
        max_usage INTEGER DEFAULT 1000,
        current_usage INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        expires_at TIMESTAMP,
        is_active BOOLEAN DEFAULT TRUE
    )
    ''')
    
    # Create usage logs table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS usage_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        api_key TEXT NOT NULL,
        phone_query TEXT NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        success BOOLEAN DEFAULT FALSE,
        response_time FLOAT DEFAULT 0
    )
    ''')
    
    # Create admin users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS admin_users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        is_active BOOLEAN DEFAULT TRUE
    )
    ''')
    
    # Insert default admin user
    password_hash = hashlib.sha256("admin123".encode()).hexdigest()
    cursor.execute('''
    INSERT OR IGNORE INTO admin_users (username, password_hash) 
    VALUES (?, ?)
    ''', ('admin', password_hash))
    
    conn.commit()
    conn.close()

def add_api_key(key, owner, max_usage=1000, days_valid=30):
    """Add a new API key"""
    conn = sqlite3.connect('api_keys.db')
    cursor = conn.cursor()
    
    expires_at = datetime.now() + timedelta(days=days_valid)
    
    try:
        cursor.execute('''
        INSERT INTO api_keys (key, owner, max_usage, expires_at)
        VALUES (?, ?, ?, ?)
        ''', (key, owner, max_usage, expires_at))
        
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def get_api_key_details(key):
    """Get details of a specific API key"""
    conn = sqlite3.connect('api_keys.db')
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT key, owner, max_usage, current_usage, created_at, expires_at, is_active
    FROM api_keys WHERE key = ?
    ''', (key,))
    
    result = cursor.fetchone()
    conn.close()
    
    if result:
        return {
            'key': result[0],
            'owner': result[1],
            'max_usage': result[2],
            'current_usage': result[3],
            'created_at': result[4],
            'expires_at': result[5],
            'is_active': bool(result[6])
        }
    return None

def get_all_api_keys():
    """Get all API keys"""
    conn = sqlite3.connect('api_keys.db')
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT key, owner, max_usage, current_usage, created_at, expires_at, is_active
    FROM api_keys ORDER BY created_at DESC
    ''')
    
    keys = []
    for row in cursor.fetchall():
        keys.append({
            'key': row[0],
            'owner': row[1],
            'max_usage': row[2],
            'current_usage': row[3],
            'created_at': row[4],
            'expires_at': row[5],
            'is_active': bool(row[6])
        })
    
    conn.close()
    return keys

def delete_api_key(key):
    """Delete an API key"""
    conn = sqlite3.connect('api_keys.db')
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM api_keys WHERE key = ?', (key,))
    deleted = cursor.rowcount > 0
    
    conn.commit()
    conn.close()
    return deleted

def increment_usage(key):
    """Increment usage count for an API key"""
    conn = sqlite3.connect('api_keys.db')
    cursor = conn.cursor()
    
    cursor.execute('''
    UPDATE api_keys 
    SET current_usage = current_usage + 1 
    WHERE key = ? AND (current_usage < max_usage OR max_usage = -1)
    ''', (key,))
    
    updated = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return updated

def can_use_key(key):
    """Check if API key can be used (within limits and active)"""
    conn = sqlite3.connect('api_keys.db')
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT is_active, current_usage, max_usage, expires_at
    FROM api_keys WHERE key = ?
    ''', (key,))
    
    result = cursor.fetchone()
    conn.close()
    
    if not result:
        return False
    
    is_active, current_usage, max_usage, expires_at = result
    
    # Check if key is active
    if not is_active:
        return False
    
    # Check if key has expired
    if expires_at and datetime.strptime(expires_at, '%Y-%m-%d %H:%M:%S') < datetime.now():
        return False
    
    # Check if usage limit reached (-1 means unlimited)
    if max_usage != -1 and current_usage >= max_usage:
        return False
    
    return True

def log_usage(key, phone_query, success, response_time=0):
    """Log API usage"""
    conn = sqlite3.connect('api_keys.db')
    cursor = conn.cursor()
    
    cursor.execute('''
    INSERT INTO usage_logs (api_key, phone_query, success, response_time)
    VALUES (?, ?, ?, ?)
    ''', (key, phone_query, success, response_time))
    
    conn.commit()
    conn.close()

def get_usage_stats():
    """Get usage statistics"""
    conn = sqlite3.connect('api_keys.db')
    cursor = conn.cursor()
    
    # Total API calls
    cursor.execute('SELECT COUNT(*) FROM usage_logs')
    total_calls = cursor.fetchone()[0]
    
    # Successful calls
    cursor.execute('SELECT COUNT(*) FROM usage_logs WHERE success = 1')
    success_calls = cursor.fetchone()[0]
    
    # Today's calls
    cursor.execute('SELECT COUNT(*) FROM usage_logs WHERE DATE(timestamp) = DATE("now")')
    today_calls = cursor.fetchone()[0]
    
    conn.close()
    
    return {
        'total_calls': total_calls,
        'success_calls': success_calls,
        'today_calls': today_calls,
        'success_rate': (success_calls / total_calls * 100) if total_calls > 0 else 0
    }

def validate_admin(username, password):
    """Validate admin credentials"""
    import hashlib
    conn = sqlite3.connect('api_keys.db')
    cursor = conn.cursor()
    
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    cursor.execute('''
    SELECT id FROM admin_users 
    WHERE username = ? AND password_hash = ? AND is_active = 1
    ''', (username, password_hash))
    
    result = cursor.fetchone()
    conn.close()
    
    return result is not None

# Initialize database when module is imported
init_db()