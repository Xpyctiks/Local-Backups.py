#!/usr/local/bin/python3

import os,sys
from functions.load_config import load_config
from functions.daily import daily_local,daily_other
from functions.weekly import weekly_local,weekly_other
from functions.func import start_job

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
  else:
    show_help()
