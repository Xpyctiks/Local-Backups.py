import logging
import os
import json
import re
from datetime import datetime
from functions.func import interrupt_job
from functions import variables
from functions.send_to_telegram import send_to_telegram

def load_config():
  #Check if config file exists. If not - generate the new one.
  if os.path.exists(variables.CONFIG_FILE):
    try:
      with open(variables.CONFIG_FILE, 'r',encoding='utf8') as file:
        config = json.load(file)     
      #Check if all parameters are set. If not - shows the error message
      REQUIRED_KEYS = [
        "telegramToken", "telegramChat", "logFolder", "dailyFolder", "weeklyFolder", "backupFolder", "DefaultDbHost", "DefaultDbPort",
        "DefaultDbSocket", "DefaultDbUser", "DefaultDbPass", "LocalServerBackups", "OtherBackups" 
      ]
      for key in REQUIRED_KEYS:
        if key not in config:
          print(f"Important key {key} is absent in config file! Can't proceed")
          interrupt_job("Program start")
      variables.TELEGRAM_TOKEN = config.get('telegramToken').strip()
      variables.TELEGRAM_CHATID = config.get('telegramChat').strip()
      variables.LOG_FOLDER = config.get('logFolder').strip()
      if not os.path.exists(variables.LOG_FOLDER):
        os.makedirs(variables.LOG_FOLDER,mode=0o770,exist_ok=True)
        text = f"Created new directory {variables.LOG_FOLDER}"
        print(text)
      LOG_FILE_NAME=datetime.now().strftime('%d.%m.%Y')
      LOG_FILE=os.path.join(variables.LOG_FOLDER,LOG_FILE_NAME)
      logging.basicConfig(filename=LOG_FILE,level=logging.INFO,format='%(asctime)s - Local-Backups - %(levelname)s - %(message)s',datefmt='%d-%m-%Y %H:%M:%S')
      logging.getLogger("httpx").setLevel(logging.WARNING)
      variables.DAILY_FOLDER = config.get('dailyFolder').strip()
      variables.WEEKLY_FOLDER = config.get('weeklyFolder').strip()
      variables.BCKP_FOLDER = config.get('backupFolder').strip()
      if not os.path.exists(variables.BCKP_FOLDER):
        os.makedirs(variables.BCKP_FOLDER,mode=0o770,exist_ok=True)
        text = f"Created new directory {variables.BCKP_FOLDER}"
        print(text)
      variables.BCKP_DEF_DB_HOST = config.get('DefaultDbHost').strip()
      variables.BCKP_DEF_DB_PORT = config.get('DefaultDbPort').strip()
      variables.BCKP_DEF_DB_SOCKET = config.get('DefaultDbSocket').strip()
      variables.BCKP_DEF_DB_USER = config.get('DefaultDbUser').strip()
      variables.BCKP_DEF_DB_PASS = config.get('DefaultDbPass').strip()
      variables.LOCAL_BCKP_LIST = config.get('LocalServerBackups', [])
      variables.OTHER_BCKP_LIST = config.get('OtherBackups', [])
      variables.HOSTNAME = os.uname().nodename
    except Exception as msg:
      text = f"Error while loading JSON config file - check structure and commas first of all. Error: {msg}"
      logging.error(text)
      print(text)
      send_to_telegram(text)
      interrupt_job("General-Job")
  else:
    generate_default_config()

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
  if not os.path.exists(variables.CONFIG_DIR):
    os.mkdir(variables.CONFIG_DIR,0o770)
  with open(variables.CONFIG_FILE, 'w',encoding='utf8') as file:
    json.dump(config, file, indent=4)
  os.chmod(variables.CONFIG_FILE, 0o600)
  print(f"First launch. New config file {variables.CONFIG_FILE} generated and needs to be configured.")
  quit()
