# db_handler.py

import os
from pathlib import Path
import sqlite3
import sys

#DB_NAME = r'D:\Project\UI\src\db\antivirus.sqlite'
if getattr(sys, 'frozen', False):  # Running as PyInstaller .exe
    BASE_DIR = Path(sys._MEIPASS)
else:
    BASE_DIR = Path(__file__).resolve().parent.parent

DB_NAME = BASE_DIR / "db" / "antivirus.sqlite"

print(f"🔍 Checking database at: {DB_NAME}")

# Ensure the DB directory exists
os.makedirs(BASE_DIR / "db", exist_ok=True)

def init_db():
    tables = [
        '''CREATE TABLE IF NOT EXISTS type_master (id INTEGER PRIMARY KEY, type_name TEXT NOT NULL);''',
        '''CREATE TABLE IF NOT EXISTS file_name_db (id INTEGER PRIMARY KEY, type_id INTEGER NOT NULL, file_name TEXT);''',
        '''CREATE TABLE IF NOT EXISTS file_signature_db (id INTEGER PRIMARY KEY, type_id INTEGER NOT NULL, file_signature TEXT);''',
        '''CREATE TABLE IF NOT EXISTS file_content_db (id INTEGER PRIMARY KEY, type_id INTEGER NOT NULL, file_content TEXT);''',
        '''CREATE TABLE IF NOT EXISTS scan_log (id INTEGER PRIMARY KEY, title TEXT NOT NULL, descp TEXT, dt TEXT NOT NULL, tm TEXT NOT NULL, status TEXT NOT NULL, duration TEXT NOT NULL);''',
        '''CREATE TABLE IF NOT EXISTS action_details (id INTEGER PRIMARY KEY, type_action TEXT NOT NULL, fname TEXT NOT NULL, fnew_name TEXT NOT NULL, action TEXT NOT NULL, action_descp TEXT, dt TEXT NOT NULL, tm TEXT NOT NULL, status TEXT NOT NULL, duration TEXT NOT NULL);'''
    ]
    for table in tables:
        execute_query(table)


if not DB_NAME.exists():
    print("🚨 Database file missing! Creating a new one...")
    open(DB_NAME, 'a').close()
    init_db()  # Initialize database

def execute_query(query, params = ()):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        return cursor


def fetch_all(query, params = ()):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchall()


def fetch_one(query, params=()):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchone()
  

def get_max_id(table_name):
    result = fetch_one(f"SELECT COALESCE(MAX(id), 0) FROM {table_name}")
    return result[0] if result else 0

###################################################################################################################################################################################################################################################################
'''MALWARE TYPE'''

def insert_type_master(type_name):
    execute_query("INSERT INTO type_master (id, type_name) VALUES (?, ?)", (get_max_id('type_master') + 1, type_name))

def update_type_master(id, type_name):
    execute_query("UPDATE type_master SET type_name = ? WHERE id = ?", (type_name, id))

def delete_type_master(id):
    execute_query("DELETE FROM type_master WHERE id = ?", (id,))

def get_type_master(id):
    query = f"SELECT id, type_name from type_master WHERE id={id}"
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.execute(query)
    result = []
    for row in cursor:
        result.append({"id":row[0],"type_name":row[1]})    
    conn.close()
    print('Query>>', query)
    return result

def get_all_type_master():
    return [{"id": row[0], "type_name": row[1]} for row in fetch_all("SELECT id, type_name FROM type_master")]  

###################################################################################################################################################################################################################################################################
'''MALWARE NAME'''

def insert_file_name_db(type_id, file_name):
    execute_query("INSERT INTO file_name_db (id, type_id, file_name) VALUES (?, ?, ?)", (get_max_id('file_name_db') + 1, type_id, file_name))

def update_file_name_db(id, type_id, file_name):
    execute_query("UPDATE file_name_db set type_id = ? file_name = ? WHERE id = ?", (type_id, file_name, id))

def delete_file_name_db(id):
    execute_query("DELETE FROM file_name_db WHERE id = ?", (id,))

def get_file_name_db(id):
    result = fetch_one("SELECT id, file_name, type_id FROM file_name_db WHERE id = ?", (id,))
    return {"id": result[0], "file_name": result[1], "type_id": result[2]} if result else None

def get_all_file_name_db():
    return [{"id": row[0], "file_name": row[1], "type_id": row[2]} for row in fetch_all("SELECT id, file_name, type_id FROM file_name_db")]  

###################################################################################################################################################################################################################################################################
'''MALWARE SIGNATURE'''

def insert_file_signature_db(type_id, file_signature):
    execute_query("INSERT INTO file_signature_db (id,type_id, file_signature) VALUES (?, ?, ?)", (get_max_id('file_signature_db') + 1, type_id, file_signature))

def update_file_signature_db(id, type_id, file_signature):
    execute_query("UPDATE file_signature_db set type_id = ? file_signature = ? WHERE id = ?", (type_id, file_signature, id))

def delete_file_signature_db(id):
    execute_query("DELETE FROM file_signature_db WHERE id = ?", (id,))

def get_file_signature_db(id):
    result = fetch_one("SELECT id, file_signature, type_id FROM file_signature_db WHERE id = ?", (id,))
    return {"id": result[0], "file_signature": result[1], "type_id": result[2]} if result else None

def get_all_file_signature_db():
    return [{"id": row[0], "file_signature": row[1], "type_id": row[2]} for row in fetch_all("SELECT id, file_signature, type_id FROM file_signature_db")]  

###################################################################################################################################################################################################################################################################
'''MALWARE CONTENT'''

def insert_file_content_db(type_id, file_content):
    execute_query("INSERT INTO file_content_db (id,type_id, file_content) VALUES (?, ?, ?)", (get_max_id('file_content_db') + 1, type_id, file_content))

def update_file_content_db(id, type_id, file_content):
    execute_query("UPDATE file_content_db set type_id = ? file_content = ? WHERE id = ?", (type_id, file_content, id))

def delete_file_content_db(id):
    execute_query("DELETE FROM file_content_db WHERE id = ?", (id,))

def get_file_content_db(id):
    result = fetch_one("SELECT id, file_content, type_id FROM file_content_db WHERE id = ?", (id,))
    return {"id": result[0], "file_content": result[1], "type_id": result[2]} if result else None

def get_all_file_content_db():
    return [{"id": row[0], "file_content": row[1], "type_id": row[2]} for row in fetch_all("SELECT id, file_content, type_id FROM file_content_db")]  

###################################################################################################################################################################################################################################################################
'''scan_log- id,title,descp,dt,tm,status, duration'''    

def insert_scan_log(id,title,descp,dt,tm,status,duration):
  query = f"INSERT INTO scan_log (id,title,descp,dt,tm,status,duration) VALUES ({id}, '{title}','{descp}','{dt}','{tm}','{status}','{duration}')"
  conn = sqlite3.connect(DB_NAME)
  conn.execute(query)
  conn.commit()
  print ("Query>>", query)
  conn.close()

def update_scan_log(id,title,descp,dt,tm,status,duration):
  query = f"UPDATE scan_log set title = '{title}',descp='{descp}',dt='{dt}',tm='{tm}',status='{status}, duration='{duration}' where id = {id}"
  conn = sqlite3.connect(DB_NAME)
  conn.execute(query)
  conn.commit()
  print('Query>>',query)
  print ("Total number of rows updated :", conn.total_changes)
  conn.close()

def delete_scan_log(id):
  query = f"DELETE from scan_log where id = {id};"
  conn = sqlite3.connect(DB_NAME)
  conn.execute(query)
  conn.commit()
  print('Query>>', query)
  print ("Total number of rows deleted :", conn.total_changes)
  conn.close()

def get_scan_log(id=None):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    if id is None:
        query = "SELECT id, title, descp, dt, tm, status, duration FROM scan_log"
        cursor.execute(query)
    else:
        query = "SELECT id, title, descp, dt, tm, status, duration FROM scan_log WHERE id=?"
        cursor.execute(query, (id,))  # Use parameterized queries to avoid SQL injection

    result = [
        {
            "scan_id": row[0],
            "summary": row[1],
            "description": row[2],
            "date": row[3],
            "time": row[4],
            "status": row[5],
            "duration": row[6]
        }
        for row in cursor.fetchall()
    ]

    conn.close()
    return result


def get_all_scan_log():
  query = f"SELECT id, title,descp,dt,tm,status,duration from scan_log "
  conn = sqlite3.connect(str(DB_NAME))
  cursor = conn.execute(query)
  result = []
  for row in cursor:
    result.append({"id":row[0],'title':row[1],'descp':row[2],'dt':row[3],'tm':row[4],'status':row[5],'duration':row[6]})    
  conn.close()
  print('Query>>', query)
  return result

###################################################################################################################################################################################################################################################################
'''action_details - id,type_action,fname,fnew_name,action,action_descp,dt,tm,status,duration'''

def insert_action_details(id,type_action,fname,fnew_name,action,action_descp,dt,tm,status,duration):
  query = f"INSERT INTO action_details (id,type_action,fname,fnew_name,action,action_descp,dt,tm,status,duration) VALUES ({id}, '{type_action}','{fname}','{fnew_name}','{action}','{action_descp}','{dt}','{tm}','{status}','{duration}')"
  conn = sqlite3.connect(DB_NAME)
  conn.execute(query);
  conn.commit()
  print ("Query>>", query);
  conn.close()

def update_action_details(id,type_action,fname,fnew_name,action,action_descp,dt,tm,status,duration):
  query = f"UPDATE action_details set type_action='{type_action}',fname='{fname}',fnew_name='{fnew_name}',action='{action}',action_descp='{action_descp}',dt='{dt}',tm='{tm}',status='{status}',duration='{duration} where id = {id}"
  conn = sqlite3.connect(DB_NAME)
  conn.execute(query)
  conn.commit()
  print('Query>>',query)
  print ("Total number of rows updated :", conn.total_changes)
  conn.close()

def delete_action_details(id):
  query = f"DELETE from action_details where id = {id};"
  conn = sqlite3.connect(DB_NAME)
  conn.execute(query)
  conn.commit()
  print('Query>>', query)
  print ("Total number of rows deleted :", conn.total_changes)
  conn.close()

def get_action_details(id):
  query = f"SELECT id, type_action,fname,fnew_name,action,action_descp,dt,tm,status,duration from action_details WHERE id={id}"
  conn = sqlite3.connect(DB_NAME)
  cursor = conn.execute(query)
  result = []
  for row in cursor:
    result.append({"id":row[0],'type_action':row[1],'fname':row[2],'fnew_name':row[3],'action':row[4],'action_descp':row[5],'dt':row[6],'tm':row[7],'status':row[8],'duration':row[9]})    
  conn.close()
  print('Query>>', query)
  return result

def get_all_action_details():
  query = f"SELECT id, type_action,fname,fnew_name,action,action_descp,dt,tm,status,duration from action_details "
  conn = sqlite3.connect(DB_NAME)
  cursor = conn.execute(query)
  result = []
  for row in cursor:
    result.append({"id":row[0],'type_action':row[1],'fname':row[2],'fnew_name':row[3],'action':row[4],'action_descp':row[5],'dt':row[6],'tm':row[7],'status':row[8],'duration':row[9]}) 
  conn.close()
  print('Query>>', query)
  return result

###################################################################################################################################################################################################################################################################