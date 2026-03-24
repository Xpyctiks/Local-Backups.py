import os,logging,tarfile
from functions.send_to_telegram import send_to_telegram
from functions.func import create_sha256,finish_job
from functions.mysql_backup import mysql_backup
from functions import variables

def weekly_local():
  #if ok, check and create for the today's folder
  if not os.path.exists(os.path.join(variables.BCKP_FOLDER,variables.WEEKLY_FOLDER,variables.CURR_FOLDER_NAME)):
    os.makedirs(os.path.join(variables.BCKP_FOLDER,variables.WEEKLY_FOLDER,variables.CURR_FOLDER_NAME),mode=0o770,exist_ok=True)
    text = f"\tCreated new directory {os.path.join(variables.BCKP_FOLDER,variables.WEEKLY_FOLDER,variables.CURR_FOLDER_NAME)}"
    print(text)
    logging.info(text)
  #Making full path to the destination folder
  TO_FOLDER = os.path.join(variables.BCKP_FOLDER,variables.WEEKLY_FOLDER,variables.CURR_FOLDER_NAME)
  #listing items, dividing them to Folder and DB versions
  for item in variables.LOCAL_BCKP_LIST:
    #If there is Folder variable - doing backup of folder
    if item.get('Folder'):
      #first of all check if the directory exists at all
      if not os.path.exists(item.get('Folder')):
        text = f"Weekly-Local: The directory {item.get('Folder')} doesn't exists! Skipping..."
        print(text)
        logging.error(text)
        send_to_telegram(text)
        continue
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
        send_to_telegram(text)
        continue
    #If there is DB variable - doing backup of DB
    elif item.get('DB'):
      mysql_backup(TO_FOLDER,item.get('Name'),item.get('DB'),item.get('User'),item.get('Host'),item.get('Socket'),item.get('Port'),item.get('Password'),"Weekly-Local")
  create_sha256(TO_FOLDER)
  text = f"\tWeekly-Local Files and DB backups done successfully!"
  print(text)
  logging.info(text)
  finish_job("Weekly-Local")

def weekly_other():
  #listing items, dividing them to Folder and DB versions
  for item in variables.OTHER_BCKP_LIST:
    #If there is Folder variable - doing backup of folder
    if item.get('Folder'):
      #first of all check if the directory exists at all
      if not os.path.exists(item.get('Folder')):
        text = f"Weekly-Other: The directory {item.get('Folder')} doesn't exists! Skipping..."
        print(text)
        logging.error(text)
        send_to_telegram(text)
        continue
      #Making full path to the destination folder
      TO_FOLDER = os.path.join(variables.BCKP_FOLDER,item.get('Name'),variables.WEEKLY_FOLDER,variables.CURR_FOLDER_NAME)
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
        create_sha256(TO_FOLDER)
      except Exception as msg:
        text = f"Some error while packing folder {item.get('Folder')}. Error: {msg}"
        logging.error(text)
        print(text)
        send_to_telegram(text)
        continue
      #If there is DB variable - doing backup of DB
    elif item.get('DB'):
      #Making full path to the destination folder
      TO_FOLDER = os.path.join(variables.BCKP_FOLDER,item.get('Name'),variables.WEEKLY_FOLDER,variables.CURR_FOLDER_NAME)
      #if ok, check and create for the today's folder
      if not os.path.exists(TO_FOLDER):
        os.makedirs(TO_FOLDER,mode=0o770,exist_ok=True)
        text = f"Created new directory {TO_FOLDER}"
        print(text)
        logging.info(text)
      mysql_backup(TO_FOLDER,item.get('Name'),item.get('DB'),item.get('User'),item.get('Host'),item.get('Socket'),item.get('Port'),item.get('Password'),"Weekly-Other")
      create_sha256(TO_FOLDER)
  text = f"\tWeekly-Other Files and DB backups done successfully!"
  print(text)
  logging.info(text)
  finish_job("Weekly-Other")
