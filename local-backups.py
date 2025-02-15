#!/bin/env python3

import os
import sys
import json
import logging
import logging.handlers
import requests
from datetime import datetime
import tarfile
import subprocess
import hashlib

CONFIG_FILE = os.path.expanduser(os.path.splitext(os.path.abspath(__file__))[0]+".config.json")
SCRIPT_NAME = os.path.splitext(os.path.basename(__file__))[0]
PID_FILE = os.path.join("/var/run/",os.path.splitext(os.path.basename(__file__))[0])[:-1]+".pid"
LOCAL_BCKP_LIST = OTHER_BCKP_LIST = []
TELEGRAM_TOKEN = TELEGRAM_CHATID = LOG_FOLDER = BCKP_FOLDER = BCKP_DEF_DB_HOST = BCKP_DEF_DB_PORT = BCKP_DEF_DB_SOCKET = BCKP_DEF_DB_USER = BCKP_DEF_DB_PASS = \
DAILY_FOLDER = WEEKLY_FOLDER = CURR_FOLDER_NAME = ""

def generate_default_config():
    config =  {
        "telegramToken": "",
        "telegramChat": "",
        "logFolder": f"{os.path.join(os.path.expanduser(os.getcwd()),'Log')}",
        "backupFolder": f"{os.path.join(os.path.expanduser(os.getcwd()),'Backups')}",
        "dailyFolder": "Daily",
        "weeklyFolder": "Weekly",
        "DefaultDbHost": "127.0.0.1",
        "DefaultDbPort": "3306",
        "DefaultDbSocket": "",
        "DefaultDbUser": "root",
        "DefaultDbPass": "123Passw0rd123",
        "LocalServerBackups" : [
            {
                "Name": "server-etc",
                "Folder": "/etc"
            },
            {
                "Name": "server-bin",
                "Folder": "/usr/local/bin"
            },
            {
                "Name": "Observium",
                "DB": "observium",
                "User":"observium",
                "Password": "123Passw0rd123"
            }
        ],
        "OtherBackups": [
            {
                "Name": "Site1.com",
                "Folder": "/var/www/site1.lan"
            },
            {
                "Name": "Site1.com",
                "DB": "observium",
                "User":"observium",
                "Password": "123Passw0rd123"
            }
        ]
    }
    with open(CONFIG_FILE, 'w',encoding='utf8') as file:
        json.dump(config, file, indent=4)
    os.chmod(CONFIG_FILE, 0o600)
    print(f"First launch. New config file {CONFIG_FILE} generated and needs to be configured.")
    quit()

def send_to_telegram(subject,message):
    headers = {
        'Content-Type': 'application/json',
    }
    data = {
        "chat_id": f"{TELEGRAM_CHATID}",
        "text": f"[{os.uname().nodename}] {SCRIPT_NAME}:\n{subject}\n{message}",
    }
    if not any(important in [None, "", "None"] for important in [f"{TELEGRAM_CHATID}", f"{TELEGRAM_TOKEN}"]):
        response = requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",headers=headers,json=data)
        if response.status_code != 200:
            err = response.json()
            logging.error(f"Error while sending message to Telegram: {err}")

def load_config():
    #main initialization phase starts here
    global TELEGRAM_TOKEN, TELEGRAM_CHATID, LOG_FOLDER, BCKP_FOLDER, BCKP_DEF_DB_HOST, BCKP_DEF_DB_PORT, BCKP_DEF_DB_SOCKET, BCKP_DEF_DB_USER, BCKP_DEF_DB_PASS, LOCAL_BCKP_LIST, \
    DAILY_FOLDER, WEEKLY_FOLDER, OTHER_BCKP_LIST
    #Check if config file exists. If not - generate the new one.
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r',encoding='utf8') as file:
                config = json.load(file)
            #Check if all parameters are set. If not - shows the error message
            for id,key in enumerate(config.keys()):
                if not (key in ["telegramToken", "telegramChat", "logFolder", "dailyFolder", "weeklyFolder", "backupFolder", "DefaultDbHost", "DefaultDbPort", "DefaultDbSocket","DefaultDbUser", "DefaultDbPass", "LocalServerBackups", "OtherBackups"]):
                    print(f"Important key {key} is absent in config file! Can't proceed")
                    interrupt_job()
            TELEGRAM_TOKEN = config.get('telegramToken').strip()
            TELEGRAM_CHATID = config.get('telegramChat').strip()
            LOG_FOLDER = config.get('logFolder').strip()
            DAILY_FOLDER = config.get('dailyFolder').strip()
            WEEKLY_FOLDER = config.get('weeklyFolder').strip()
            BCKP_FOLDER = config.get('backupFolder').strip()
            BCKP_DEF_DB_HOST = config.get('DefaultDbHost').strip()
            BCKP_DEF_DB_PORT = config.get('DefaultDbPort').strip()
            BCKP_DEF_DB_SOCKET = config.get('DefaultDbSocket').strip()
            BCKP_DEF_DB_USER = config.get('DefaultDbUser').strip()
            BCKP_DEF_DB_PASS = config.get('DefaultDbPass').strip()
            LOCAL_BCKP_LIST = config.get('LocalServerBackups', [])
            OTHER_BCKP_LIST = config.get('OtherBackups', [])
            if not os.path.exists(LOG_FOLDER):
                os.makedirs(LOG_FOLDER,mode=0o770,exist_ok=True)
                text = f"Created new directory {LOG_FOLDER}"
                print(text)
            LOG_FILE_NAME=datetime.now().strftime('%d.%m.%Y')
            LOG_FILE=os.path.join(LOG_FOLDER,LOG_FILE_NAME)
            logging.basicConfig(filename=LOG_FILE,level=logging.INFO,format='%(asctime)s - Local-Backups - %(levelname)s - %(message)s',datefmt='%d-%m-%Y %H:%M:%S')
            if not os.path.exists(BCKP_FOLDER):
                os.makedirs(BCKP_FOLDER,mode=0o770,exist_ok=True)
                text = f"Created new directory {BCKP_FOLDER}"
                print(text)
        except Exception as msg:
            text = f"Error while loading JSON config file - check structure and commas first of all. Error: {msg}"
            logging.error(text)
            print(text)
            interrupt_job("General-Job")
    else:
        generate_default_config()

def check_pid():
    if os.path.exists(PID_FILE):
        with open(PID_FILE, "r") as f:
            old_pid = int(f.read().strip())        
        if os.path.exists(f"/proc/{old_pid}"):
            print(f"Another copy is running. Can't proceed.")
            logging.error("Previous copy is running. Can't proceed.")
            send_to_telegram("🚫Error!","Previous copy is running. Can't proceed.")
            interrupt_job("General-Job")
    with open(PID_FILE, "w") as f:
        f.write(str(os.getpid()))
        return True

def del_pid():    
    if os.path.exists(PID_FILE):
        os.remove(PID_FILE)

def start_job(type):
    global CURR_FOLDER_NAME
    time=datetime.now().strftime('%H:%M:%S %d.%m.%Y')
    CURR_FOLDER_NAME=datetime.now().strftime('%d.%m.%Y')
    text = f"----------------------------------------{time} Starting {type} backup jobs----------------------------------------"
    print(text)
    logging.info(text)
    send_to_telegram(f"☕{type} backup job started","")
    check_pid()

def finish_job(type):
    time=datetime.now().strftime('%H:%M:%S %d.%m.%Y')
    text = f"----------------------------------------{time} Finished all {type} backup job-------------------------------------"
    print(text)
    logging.info(text)
    send_to_telegram(f"✅All {type} jobs done.","")
    del_pid()
    sys.exit(0)

def interrupt_job(type):
    time=datetime.now().strftime('%H:%M:%S %d.%m.%Y')
    text = f"----------------------------------------{time} Interruption of all {type} backup job-------------------------------------"
    print(text)
    logging.info(text)
    send_to_telegram(f"❌All {type} jobs have been interrupted!","")
    del_pid()
    sys.exit(1)

def part_of_day():
    now = datetime.now().hour
    if 2 <= now < 12:
        return "morning"
    else:
        return "evening"

def create_sha256(folder):
    sha256_hash = hashlib.sha256()
    sha256_output_file = os.path.join(folder,"sha256sum.txt")
    sha256_output_data = ""
    files = [f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))]
    for file in files:
        with open(os.path.join(folder,file), "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        sha256_output_data += sha256_hash.hexdigest()+" "+file+"\n"
    with open(os.path.join(folder,sha256_output_file), "w") as f2:
        f2.write(sha256_output_data)
    text = f"SHA256 checksums for {folder} created successfully!"
    print(text)
    logging.info(text)

def mysql_backup(tofolderIn,nameIn,dbIn,userIn,hostIn,socketIn,portIn,passIn,typeIn):
    text = f"Processing {typeIn} DB backup {nameIn} - DB name {dbIn} - TO folder {tofolderIn}"
    print(text)
    logging.info(text)
    #checking if all necessary default variables for mysql are set
    if any(key in [None, "", "None"] for key in [BCKP_DEF_DB_HOST, BCKP_DEF_DB_USER, BCKP_DEF_DB_PASS]):
        print(f"Key is empty!")
    #check what we use: default or personal credentials
    if hostIn:
        mysqlHost = hostIn
    else:
        mysqlHost = BCKP_DEF_DB_HOST
    if userIn:
        mysqlUser = userIn
    else:
        mysqlUser = BCKP_DEF_DB_USER
    if passIn:
        mysqlPass = passIn
    else:
        mysqlPass = BCKP_DEF_DB_PASS
    #check first of all for the personal defined parameters Socket and Port
    #if set both at the same time:
    if portIn and socketIn:
        additional = f"-S{socketIn}"
        text = f"Both personal Socket and Port are defined. Taking Socket as high priority."
        print(text)
        logging.info(text)
    #if not set both, trying to switch to default defined values
    elif not portIn and not socketIn:
        #if both default values are not set - sending alert
        if not BCKP_DEF_DB_SOCKET and not BCKP_DEF_DB_PORT:
            text = f"Neither default socket nor default port is set. Can't proceed with DB {nameIn} backup"
            print(text)
            logging.info(text)
            send_to_telegram("🚒Error:",text)
        elif BCKP_DEF_DB_SOCKET and not BCKP_DEF_DB_PORT:
            additional = f"-S{BCKP_DEF_DB_SOCKET}"
            text = f"Using default SOCKET with DB {nameIn} backup"
            print(text)
            logging.info(text)
        elif not BCKP_DEF_DB_SOCKET and BCKP_DEF_DB_PORT:
            additional = f"-h{mysqlHost} -P{BCKP_DEF_DB_PORT}"
            text = f"Using default PORT with DB {nameIn} backup"
            print(text)
            logging.info(text)
    #if set any of two personal values
    elif portIn and not socketIn:
        additional = f"-h{mysqlHost} -P{portIn}"
        text = f"Using personal PORT value with DB {nameIn} backup"
        print(text)
        logging.info(text)
    elif not portIn and socketIn:
        additional = f"-S{socketIn}"
        text = f"Using personal SOCKET value with DB {nameIn} backup"
        print(text)
        logging.info(text)
    #now check if ALL selected
    if dbIn == "ALL":
        if (typeIn in ["Daily-Local", "Daily-Other"] and part_of_day() == "morning"):
            cmd = f"mysqldump -u{mysqlUser} -p{mysqlPass} {additional} --single-transaction --quick --all-databases | gzip > {tofolderIn}/All-databases-morning.sql.gz"
        elif (typeIn in ["Daily-Local", "Daily-Other"] and part_of_day() == "evening"):
            cmd = f"mysqldump -u{mysqlUser} -p{mysqlPass} {additional} --single-transaction --quick --all-databases | gzip > {tofolderIn}/All-databases-evening.sql.gz"
        else:
            cmd = f"mysqldump -u{mysqlUser} -p{mysqlPass} {additional} --single-transaction --quick --all-databases | gzip > {tofolderIn}/All-databases.sql.gz"
        result = subprocess.run(cmd, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,text=True)
        if "error" in str(result):
            text = f"Some error while dumping Daily ALL DB backup of {nameIn}. Error: {result.stderr}"
            logging.error(text)
            print(text)
            send_to_telegram("🚒Error:",text)
        text = f"Daily ALL DB Local backup of {nameIn} done successfully!"
        print(text)
        logging.info(text)
    #now check if FETCH selected
    elif dbIn == "FETCH":
        cmd = f'mysql -u{mysqlUser} -p{mysqlPass} {additional} -e "SHOW DATABASES;"'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        databases = result.stdout.strip().split("\n")[1:]
        text = f"Total fetched databases: {databases}"
        print(text)
        logging.info(text)
        exclude_dbs = {"information_schema", "performance_schema", "mysql", "sys"}
        databases = [db for db in databases if db not in exclude_dbs]
        for db in databases:
            print(f"Creating dump for {db}...")
            if (typeIn in ["Daily-Local", "Daily-Other"] and part_of_day() == "morning"):
                cmd = f"mysqldump -u{mysqlUser} -p{mysqlPass} {additional} --single-transaction --quick {db} | gzip > {tofolderIn}/{db}-morning.sql.gz"
            elif (typeIn in ["Daily-Local", "Daily-Other"] and part_of_day() == "evening"):
                cmd = f"mysqldump -u{mysqlUser} -p{mysqlPass} {additional} --single-transaction --quick {db} | gzip > {tofolderIn}/{db}-evening.sql.gz"
            else:
                cmd = f"mysqldump -u{mysqlUser} -p{mysqlPass} {additional} --single-transaction --quick {db} | gzip > {tofolderIn}/{db}.sql.gz"
            result = subprocess.run(cmd, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,text=True)
            if "error" in str(result):
                text = f"Some error while dumping Daily FETCH DB backup of {db}. Error: {result.stderr}"
                logging.error(text)
                print(text)
                send_to_telegram("🚒Error:",text)
                continue
    #if individual database selected
    else:
        if (typeIn in ["Daily-Local", "Daily-Other"] and part_of_day() == "morning"):
            backup_file = tofolderIn+"/"+nameIn+"-morning.sql.gz"
            cmd = f"mysqldump -u{mysqlUser} -p{mysqlPass} {additional} --single-transaction --quick {dbIn} | gzip > {backup_file}"
        elif (typeIn in ["Daily-Local", "Daily-Other"] and part_of_day() == "evening"):
            backup_file = tofolderIn+"/"+nameIn+"-evening.sql.gz"
            cmd = f"mysqldump -u{mysqlUser} -p{mysqlPass} {additional} --single-transaction --quick {dbIn} | gzip > {backup_file}"
        else:
            backup_file = tofolderIn+"/"+nameIn+".sql.gz"
            cmd = f"mysqldump -u{mysqlUser} -p{mysqlPass} {additional} --single-transaction --quick {dbIn} | gzip > {backup_file}"
        result = subprocess.run(cmd, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,text=True)
        if "error" in str(result):
            text = f"Some error while dumping Weekly DB backup of {nameIn}. Error: {result.stderr}"
            logging.error(text)
            print(text)
            send_to_telegram("🚒Error:",text)

def daily_local():
    #if ok, check and create for the today's folder
    if not os.path.exists(os.path.join(BCKP_FOLDER,DAILY_FOLDER,CURR_FOLDER_NAME)):
        os.mkdir(os.path.join(BCKP_FOLDER,DAILY_FOLDER,CURR_FOLDER_NAME),mode=0o770)
        text = f"Created new directory {os.path.join(BCKP_FOLDER,DAILY_FOLDER,CURR_FOLDER_NAME)}"
        print(text)
        logging.info(text)
    #Making full path to the destination folder
    TO_FOLDER = os.path.join(BCKP_FOLDER,DAILY_FOLDER,CURR_FOLDER_NAME)
    #listing items, dividing them to Folder and DB versions
    for item in LOCAL_BCKP_LIST:
        #If there is DB variable - doing backup of DB
        if item.get('DB'):
            mysql_backup(TO_FOLDER,item.get('Name'),item.get('DB'),item.get('User'),item.get('Host'),item.get('Socket'),item.get('Port'),item.get('Password'),"Daily-Local")
            text = f"Daily-Local DB backup of {item.get('Name')} done successfully!"
            print(text)
            logging.info(text)
    create_sha256(TO_FOLDER)
    finish_job("Daily-Local")

def weekly_local():
    #if ok, check and create for the today's folder
    if not os.path.exists(os.path.join(BCKP_FOLDER,WEEKLY_FOLDER,CURR_FOLDER_NAME)):
        os.mkdir(os.path.join(BCKP_FOLDER,WEEKLY_FOLDER,CURR_FOLDER_NAME),mode=0o770)
        text = f"Created new directory {os.path.join(BCKP_FOLDER,WEEKLY_FOLDER,CURR_FOLDER_NAME)}"
        print(text)
        logging.info(text)
    #Making full path to the destination folder
    TO_FOLDER = os.path.join(BCKP_FOLDER,WEEKLY_FOLDER,CURR_FOLDER_NAME)
    #listing items, dividing them to Folder and DB versions
    for item in LOCAL_BCKP_LIST:
        #If there is Folder variable - doing backup of folder
        if item.get('Folder'):
            text = f"Processing files backup - FROM folder {item.get('Folder')} - TO folder {TO_FOLDER} - file {item.get('Name')}.tar.gz"
            print(text)
            logging.info(text)
            try:
                #creating TAR.GZ archive where the file's name is taken from Name variable.
                with tarfile.open(TO_FOLDER+"/"+item.get('Name')+".tar.gz", "w:gz") as tar:
                    tar.add(item.get('Folder'))
                text = f"Archive {TO_FOLDER+'/'+item.get('Name')+'.tar.gz'} created sucessfully!"
                logging.info(text)
                print(text)
            except Exception as msg:
                text = f"Some error while packing folder {item.get('Folder')}. Error: {msg}"
                logging.error(text)
                print(text)
                send_to_telegram("🚒Error:",text)
                continue
        #If there is DB variable - doing backup of DB
        elif item.get('DB'):
            mysql_backup(TO_FOLDER,item.get('Name'),item.get('DB'),item.get('User'),item.get('Host'),item.get('Socket'),item.get('Port'),item.get('Password'),"Weekly-Local")
    create_sha256(TO_FOLDER)
    text = f"Weekly-Local Files and DB backups done successfully!"
    print(text)
    logging.info(text)
    finish_job("Weekly-Local")

def daily_other():
    #listing items, dividing them to Folder and DB versions
    for item in OTHER_BCKP_LIST:
        #If there is DB variable - doing backup of DB
        if item.get('DB'):
            # #Making full path to the destination folder
            TO_FOLDER = os.path.join(BCKP_FOLDER,item.get('Name'),DAILY_FOLDER,CURR_FOLDER_NAME)
            #if ok, check and create for the today's folder
            if not os.path.exists(TO_FOLDER):
                os.makedirs(TO_FOLDER,mode=0o770,exist_ok=True)
                text = f"Created new directory {TO_FOLDER}"
                print(text)
                logging.info(text)
            mysql_backup(TO_FOLDER,item.get('Name'),item.get('DB'),item.get('User'),item.get('Host'),item.get('Socket'),item.get('Port'),item.get('Password'),"Daily-Other")
    create_sha256(TO_FOLDER)
    text = f"Daily-Other DB backup of {item.get('Name')} done successfully!"
    print(text)
    logging.info(text)
    finish_job("Daily-Other")

def weekly_other():
    #listing items, dividing them to Folder and DB versions
    for item in OTHER_BCKP_LIST:
        #If there is Folder variable - doing backup of folder
        if item.get('Folder'):
            #Making full path to the destination folder
            TO_FOLDER = os.path.join(BCKP_FOLDER,item.get('Name'),WEEKLY_FOLDER,CURR_FOLDER_NAME)
            #if ok, check and create for the today's folder
            if not os.path.exists(TO_FOLDER):
                os.makedirs(TO_FOLDER,mode=0o770,exist_ok=True)
                text = f"Created new directory {TO_FOLDER}"
                print(text)
                logging.info(text)
            text = f"Processing files backup - FROM folder {item.get('Folder')} - TO folder {TO_FOLDER} - file {item.get('Name')}.tar.gz"
            print(text)
            logging.info(text)
            try:
                #creating TAR.GZ archive where the file's name is taken from Name variable.
                with tarfile.open(TO_FOLDER+"/"+item.get('Name')+".tar.gz", "w:gz") as tar:
                    tar.add(item.get('Folder'))
                text = f"Archive {TO_FOLDER+'/'+item.get('Name')+'.tar.gz'} created sucessfully!"
                logging.info(text)
                print(text)
            except Exception as msg:
                text = f"Some error while packing folder {item.get('Folder')}. Error: {msg}"
                logging.error(text)
                print(text)
                send_to_telegram("🚒Error:",text)
                continue
        #If there is DB variable - doing backup of DB
        elif item.get('DB'):
            #Making full path to the destination folder
            TO_FOLDER = os.path.join(BCKP_FOLDER,item.get('Name'),WEEKLY_FOLDER,CURR_FOLDER_NAME)
            #if ok, check and create for the today's folder
            if not os.path.exists(TO_FOLDER):
                os.makedirs(TO_FOLDER,mode=0o770,exist_ok=True)
                text = f"Created new directory {TO_FOLDER}"
                print(text)
                logging.info(text)
            mysql_backup(TO_FOLDER,item.get('Name'),item.get('DB'),item.get('User'),item.get('Host'),item.get('Socket'),item.get('Port'),item.get('Password'),"Weekly-Other")
    create_sha256(TO_FOLDER)
    text = f"Weekly-Other Files and DB backups done successfully!"
    print(text)
    logging.info(text)
    finish_job("Weekly-Other")

def show_help():
    print(f"Usage:\n\t./{os.path.basename(__file__)} Daily-Local  - do daily backups of databases for local server only - \"LocalServerBackups\" part of the config file.")
    print(f"\t./{os.path.basename(__file__)} Weekly-Local - do weekly backups of databases and folders for local server only - \"LocalServerBackups\" part of the config file.")
    print(f"\t./{os.path.basename(__file__)} Daily-Other  - do daily backups of any other databases - \"OtherBackups\" part of the config file.")
    print(f"\t./{os.path.basename(__file__)} Weekly-Other - do weekly backups of databases and folders for any others - \"OtherBackups\" part of the config file.")
    quit()

if __name__ == "__main__":
    if len(sys.argv) >= 2:
        if sys.argv[1] == "--help" or sys.argv[1] == "-h":
            show_help()
        elif sys.argv[1] == "Daily-Local":
            load_config()
            start_job("Daily-Local")
            daily_local()
        elif sys.argv[1] == "Daily-Other":
            load_config()
            start_job("Daily-Other")
            daily_other()
        elif sys.argv[1] == "Weekly-Local":
            load_config()
            start_job("Weekly-Local")
            weekly_local()
        elif sys.argv[1] == "Weekly-Other":
            load_config()
            start_job("Weekly-Other")
            weekly_other()
    show_help()
