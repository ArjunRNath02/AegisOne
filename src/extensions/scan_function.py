# scan_function.py

import time
import datetime
import threading
from src.extensions.file_manip import *
from src.extensions.db_handler import *
from src.extensions.ml_algo import get_ml_results
scan_result_data = ''

def scan_directory(scan_type, directory):
    global scan_result_data
    start_time = time.time()

    file_path = get_all_file_paths(directory)   # Get all file paths
    fn_list = get_all_file_name_db()            # Fetch malware file names
    fs_list = get_all_file_signature_db()       # Fetch malware file signatures
    fc_list = get_all_file_content_db()         # Fetch malware file content

    scan_result_data = {'msg' : '', 'file_list' : []}
    virus_file_list = []

    #result_list = []
    virus_list = []
    ml_virus_list = []

    for f in file_path:
        result = ''
        result += f + ' '
        #print(f)
        namelevel,signaturelevel,contentlevel = 0,0,0        
        for fn in fn_list:
            if fn['file_name'] in f:
                r = get_type_master(fn['type_id'])
                if r:  
                    result += '-- Name Virus'
                    virus_list.append(f"{f} -- {r[0]['type_name']}") 
                    namelevel = r[0]['id']
        try:
            f_sign = get_file_signature(f)
            #print(f_sign)
            for fs in fs_list:
                if fs['file_signature'] in f_sign:
                    r = get_type_master(fs['type_id'])
                    result += '-- Signature Virus'
                    virus_list.append(f"{f} -- {r[0]['type_name']}")
                    #quarantine(f)
                    signaturelevel=r[0]['id']

            for fc in fc_list:
                fc_result = open(f, 'r').read().find(fc['file_content'])
                if fc_result != -1 :
                    r = get_type_master(fc['type_id'])
                    result += '-- Content Virus'
                    virus_list.append(f"{f} -- {r[0]['type_name']}")
                    #quarantine(f)
                    contentlevel=r[0]['id']
        except:
            continue
        print('Data Frame==',[namelevel,signaturelevel,contentlevel])
        ml_result = get_ml_results([namelevel,signaturelevel,contentlevel])
        print(ml_result)
        if ml_result != 'ignore':
            ml_virus_list.append(f'{f} -- ML Alert')
            virus_file_list.append({'file':f,'namelevel':namelevel, 'signaturelevel':signaturelevel,'contentlevel':contentlevel})    
            
            # quarantine(f)
        #result_list.append(result)
    #virus_list.extend(ml_virus_list)

    end_time = time.time()
    duration = round(end_time - start_time, 2)

    #ScanLogEntry
    dt = datetime.datetime.today().strftime('%Y-%m-%d')
    tm = datetime.datetime.today().strftime('%H:%M:%S')
    
    max_id = get_max_id('scan_log') + 1
    title = f'{scan_type} Scanned Result'
    
    vl = "\n".join(virus_list)
    descp = f'''Total Files Scanned :{len(file_path)}
Total Anomalies :{len(virus_list)}
-----------------------------------
{vl}
'''
    status = str(len(virus_list))
    insert_scan_log(max_id, title, descp, dt, tm, status, duration)
   
    result_descp = f'''Total Files Scanned :{len(file_path)}
Total Anomalies :{len(virus_list)}
-----------------------------------
{vl}
------------------------------------
{dt} {tm}
Scan Duration: {duration} seconds
'''
    scan_result_data = {'msg' : result_descp, 'file_list' : virus_file_list}
    return scan_result_data       #result_list

def callThread(scan_type, dir_path):
    global scan_result
    t1 = threading.Thread(target=scan_directory, args=(scan_type, dir_path))
    t1.start()
    t1.join()
    print("**********",scan_result)
    return scan_result_data

#callThread('custom', '../scan_test')