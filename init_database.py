import sqlite3
import json
import gdown
import os
import requests
from datetime import datetime
import sys
from config import GOOGLE_DRIVE_FILE_ID

def download_from_drive():
    """Download file from Google Drive with progress"""
    try:
        download_url = f"https://drive.google.com/uc?id={GOOGLE_DRIVE_FILE_ID}&export=download"
        
        print("📥 Downloading data from Google Drive...")
        
        # Download using requests with progress
        response = requests.get(download_url, stream=True)
        total_size = int(response.headers.get('content-length', 0))
        
        with open('temp_data.json', 'wb') as f:
            downloaded = 0
            for data in response.iter_content(chunk_size=8192):
                downloaded += len(data)
                f.write(data)
                if total_size > 0:
                    progress = (downloaded / total_size) * 100
                    print(f"Download progress: {progress:.1f}%", end='\r')
        
        print("\n✅ Download completed!")
        return True
        
    except Exception as e:
        print(f"❌ Download error: {str(e)}")
        return False

def create_database():
    """Create SQLite database from JSON data"""
    try:
        print("📊 Reading JSON data...")
        with open('temp_data.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print("🗄️ Creating database...")
        conn = sqlite3.connect('phone_data.db')
        cursor = conn.cursor()
        
        # Create table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS phone_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            fathersName TEXT,
            phoneNumber TEXT UNIQUE,
            otherNumber TEXT,
            passportNumber TEXT,
            aadharNumber TEXT,
            age TEXT,
            gender TEXT,
            address TEXT,
            district TEXT,
            pincode TEXT,
            state TEXT,
            town TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_phone ON phone_data(phoneNumber)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_other_phone ON phone_data(otherNumber)')
        
        print("📝 Inserting data...")
        batch_size = 1000
        total_records = len(data)
        
        for i in range(0, total_records, batch_size):
            batch = data[i:i+batch_size]
            for record in batch:
                cursor.execute('''
                INSERT OR IGNORE INTO phone_data 
                (name, fathersName, phoneNumber, otherNumber, passportNumber, 
                 aadharNumber, age, gender, address, district, pincode, state, town)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    record.get('name'),
                    record.get('fathersName'),
                    record.get('phoneNumber'),
                    record.get('otherNumber'),
                    record.get('passportNumber'),
                    record.get('aadharNumber'),
                    record.get('age'),
                    record.get('gender'),
                    record.get('address'),
                    record.get('district'),
                    record.get('pincode'),
                    record.get('state'),
                    record.get('town')
                ))
            
            conn.commit()
            progress = min(i + batch_size, total_records)
            print(f"✅ Inserted {progress}/{total_records} records ({progress/total_records*100:.1f}%)")
        
        # Show statistics
        cursor.execute('SELECT COUNT(*) FROM phone_data')
        count = cursor.fetchone()[0]
        print(f"🎉 Database created with {count} records!")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database creation error: {str(e)}")
        return False
    finally:
        # Clean up
        if os.path.exists('temp_data.json'):
            os.remove('temp_data.json')

def main():
    """Main function"""
    print("=" * 50)
    print("🚀 Phone Database Initialization")
    print("=" * 50)
    
    # Check if database already exists
    if os.path.exists('phone_data.db'):
        print("📦 Database already exists. Skipping initialization.")
        return True
    
    # Download and create database
    if download_from_drive() and create_database():
        print("✅ Initialization completed successfully!")
        return True
    else:
        print("❌ Initialization failed!")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)