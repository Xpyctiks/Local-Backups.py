import os
import logging
from functions.func import create_sha256,finish_job
from functions.mysql_backup import mysql_backup
from functions import variables
from functions.send_to_telegram import send_to_telegram

def daily_local():
  try:
    if len(variables.LOCAL_BCKP_LIST) < 2:
      text = "Daily-Local: empty config for this type of job"
      logging.info(text)
      print(text)
      send_to_telegram("⚠"+text)
      finish_job("Daily-Local")
    #if ok, check and create for the today's folder
    if not os.path.exists(os.path.join(variables.BCKP_FOLDER,variables.DAILY_FOLDER,variables.CURR_FOLDER_NAME)):
      os.makedirs(os.path.join(variables.BCKP_FOLDER,variables.DAILY_FOLDER,variables.CURR_FOLDER_NAME),mode=0o770,exist_ok=True)
      text = f"\tCreated new directory {os.path.join(variables.BCKP_FOLDER,variables.DAILY_FOLDER,variables.CURR_FOLDER_NAME)}"
      print(text)
      logging.info(text)
    #Making full path to the destination folder
    TO_FOLDER = os.path.join(variables.BCKP_FOLDER,variables.DAILY_FOLDER,variables.CURR_FOLDER_NAME)
    #listing items, dividing them to Folder and DB versions
    for item in variables.LOCAL_BCKP_LIST:
      #If there is DB variable - doing backup of DB
      if item.get('DB'):
        mysql_backup(TO_FOLDER,item.get('Name'),item.get('DB'),item.get('User'),item.get('Host'),item.get('Socket'),item.get('Port'),item.get('Password'),"Daily-Local")
        text = f"\tDaily-Local DB backup of {item.get('Name')} done successfully!"
        print(text)
        logging.info(text)
    create_sha256(TO_FOLDER)
    finish_job("Daily-Local")
  except Exception as msg:
    logging.error(f"Daily-Local: Global error {msg}")
    send_to_telegram(f"🚨Daily-Local: Global error {msg}")

def daily_other():
  try:
    if len(variables.OTHER_BCKP_LIST) < 2:
      text = "Daily-Other: empty config for this type of job"
      logging.info(text)
      print(text)
      send_to_telegram("⚠"+text)
      finish_job("Daily-Other")
    #listing items, dividing them to Folder and DB versions
    for item in variables.OTHER_BCKP_LIST:
      #If there is DB variable - doing backup of DB
      if item.get('DB'):
        # #Making full path to the destination folder
        TO_FOLDER = os.path.join(variables.BCKP_FOLDER,item.get('Name'),variables.DAILY_FOLDER,variables.CURR_FOLDER_NAME)
        #if ok, check and create for the today's folder
        if not os.path.exists(TO_FOLDER):
          os.makedirs(TO_FOLDER,mode=0o770,exist_ok=True)
          text = f"\tCreated new directory {TO_FOLDER}"
          print(text)
          logging.info(text)
        mysql_backup(TO_FOLDER,item.get('Name'),item.get('DB'),item.get('User'),item.get('Host'),item.get('Socket'),item.get('Port'),item.get('Password'),"Daily-Other")
        create_sha256(TO_FOLDER)
        text = f"\tDaily-Other DB backup of {item.get('Name')} done successfully!"
        print(text)
        logging.info(text)
    finish_job("Daily-Other")
  except Exception as msg:
    logging.error(f"Daily-Other: Global error {msg}")
    send_to_telegram(f"🚨Daily-Other: Global error {msg}")
