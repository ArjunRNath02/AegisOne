# file_manip.py

import os
import shutil
import hashlib
import datetime
from zipfile import ZipFile

def get_files(path):
    try:
        dir_list = os.listdir(path)
        #print("Files and Directories in '", path, "' :")
        #print(dir_list)
        return dir_list
    except Exception as e:
        print(f"Error retrieving files : {e}")
        return []


def get_only_files(path):
    try:
        #print(f"Files in the directory : {path}")
        files = os.listdir(path)
        files = [f for f in files if os.path.isfile(path+'/'+f)]   #Filtering only the files
        #print(*files, sep="\n")
        return files
    except Exception as e:
        print(f"Error retrieving only files : {e}")
        return []


def get_all_file_paths(directory):
    try:
        file_paths = []
        for root, directories, files in os.walk(directory):
            for filename in files:
                filepath =os.path.join(root, filename)
                file_paths.append(filepath)
        return file_paths 
    except Exception as e:
        print(f"Error retrieving all files in the directory: {e}")
        return []


#Function to get SHA256 file signature
def get_file_signature(file_path):
    try:
        hasher = hashlib.sha256()
        with open(file_path, 'rb') as afile:
            buf = afile.read()
            hasher.update(buf)
        print(hasher.hexdigest())
        fsign = hasher.hexdigest()
        return fsign
    except Exception as e:
       print(f"Error generating file signature: {e}")
       return None


def quarantine(file):
    file_name = os.path.basename(file)
    src_file = file
    dst_file = os.path.join('./quarantine/', file_name)
    shutil.move(src_file, dst_file)


# Function to extract and list files in a ZIP archive
def zip_handler(fpath):
    extracted_files = []
    try:
        with ZipFile(fpath, 'r') as zip:
            zip.printdir()
            zip.extractall()
            for file_info in zip.infolist():
                extracted_files.append(file_info.filename)
        return extracted_files
    except Exception as e:
        print(f"Error handling zip file: {e}")
        return None


def zip_info(fpath):
    file_name = fpath
    with ZipFile(file_name, 'r') as zip:
        for info in zip.infolist():
            print(info.filename)
            print('\tModified:\t' + str(datetime.datetime(*info.date_time))) 
            print('\tSystem:\t\t' + str(info.create_system) + '(0 = Windows, 3 = Unix)') 
            print('\tZIP version:\t' + str(info.create_version)) 
            print('\tCompressed:\t' + str(info.compress_size) + ' bytes') 
            print('\tUncompressed:\t' + str(info.file_size) + ' bytes') 


