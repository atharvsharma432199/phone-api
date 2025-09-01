import sqlite3
import json
import gdown
import os
import requests
from datetime import datetime
import sys
from config import GOOGLE_DRIVE_FILE_ID  # Config se import karo

def get_file_id_from_url(url):
    """Extract file ID from Google Drive URL"""
    if 'id=' in url:
        return url.split('id=')[1].split('&')[0]
    elif 'file/d/' in url:
        return url.split('file/d/')[1].split('/')[0]
    return url

def download_from_drive():
    """Download file from Google Drive with progress"""
    try:
        # File ID extract karo
        file_id = get_file_id_from_url(GOOGLE_DRIVE_FILE_ID)
        download_url = f"https://drive.google.com/uc?id={file_id}&export=download"
        
        print("📥 Downloading data from Google Drive...")
        print(f"📎 File ID: {file_id}")
        print(f"🔗 Download URL: {download_url}")
        
        # Download using gdown
        output_file = 'temp_data.json'
        gdown.download(download_url, output_file, quiet=False)
        
        if os.path.exists(output_file):
            file_size = os.path.getsize(output_file)
            print(f"✅ Download completed! File size: {file_size} bytes")
            return True
        else:
            print("❌ Download failed! File not found.")
            return False
            
    except Exception as e:
        print(f"❌ Download error: {str(e)}")
        return False

def create_database():
    """Create SQLite database from JSON data"""
    try:
        if not os.path.exists('temp_data.json'):
            print("❌ No JSON file found for database creation")
            return False
        
        print("📊 Reading JSON data...")
        with open('temp_data.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"📁 JSON data loaded: {len(data)} records found")
        
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
        
        print("📝 Inserting data into database...")
        total_records = len(data)
        inserted_count = 0
        error_count = 0
        
        for i, record in enumerate(data):
            try:
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
                
                inserted_count += 1
                
                # Show progress every 1000 records
                if inserted_count % 1000 == 0:
                    print(f"✅ Inserted {inserted_count}/{total_records} records")
                    
            except Exception as e:
                error_count += 1
                if error_count <= 5:  # Only show first 5 errors
                    print(f"⚠️ Error inserting record {i}: {str(e)}")
                continue
        
        conn.commit()
        
        # Show final statistics
        cursor.execute('SELECT COUNT(*) FROM phone_data')
        final_count = cursor.fetchone()[0]
        
        print(f"🎉 Database creation completed!")
        print(f"📊 Total records attempted: {total_records}")
        print(f"✅ Successfully inserted: {inserted_count}")
        print(f"❌ Errors encountered: {error_count}")
        print(f"💾 Final database count: {final_count} records")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database creation error: {str(e)}")
        return False
    finally:
        # Clean up temporary file
        if os.path.exists('temp_data.json'):
            os.remove('temp_data.json')
            print("🧹 Temporary file cleaned up")

def main():
    """Main function"""
    print("=" * 60)
    print("🚀 Phone Database Initialization Script")
    print("=" * 60)
    
    # Check if database already exists
    if os.path.exists('phone_data.db'):
        print("📦 Database already exists. Checking if reinitialization is needed...")
        # Yahan aap additional checks kar sakte ho agar reinitialize karna ho toh
        reinitialize = input("Do you want to reinitialize database? (y/N): ")
        if reinitialize.lower() != 'y':
            print("Skipping initialization.")
            return True
    
    print("🔄 Starting database initialization process...")
    
    # Step 1: Download from Google Drive
    print("\n" + "="*30)
    print("📥 STEP 1: Downloading from Google Drive")
    print("="*30)
    if not download_from_drive():
        print("❌ Failed to download from Google Drive")
        return False
    
    # Step 2: Create database
    print("\n" + "="*30)
    print("🗄️ STEP 2: Creating Database")
    print("="*30)
    if not create_database():
        print("❌ Failed to create database")
        return False
    
    print("\n" + "="*60)
    print("✅ Initialization completed successfully!")
    print("="*60)
    return True

if __name__ == '__main__':
    success = main()
    if success:
        print("🎯 Script executed successfully!")
    else:
        print("💥 Script failed!")
    sys.exit(0 if success else 1)
