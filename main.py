#!/usr/local/bin/python3

import os
import sys
from functions.load_config import create_app, generate_default_config, load_config
from functions.daily import daily_local,daily_other
from functions.weekly import weekly_local,weekly_other
from functions.func import start_job

def show_help():
  print(f"Usage:\n\t./{os.path.basename(__file__)} Daily-Local  - do daily backups of databases for local server only - \"LocalServerBackups\" part of the config file.")
  print(f"\t./{os.path.basename(__file__)} Weekly-Local - do weekly backups of databases and folders for local server only - \"LocalServerBackups\" part of the config file.")
  print(f"\t./{os.path.basename(__file__)} Daily-Other  - do daily backups of any other databases - \"OtherBackups\" part of the config file.")
  print(f"\t./{os.path.basename(__file__)} Weekly-Other - do weekly backups of databases and folders for any others - \"OtherBackups\" part of the config file.")
  quit()

def run_job(jobtype: str):
  app = create_app()
  fresh = generate_default_config(app)
  if fresh:
    print("First launch. Database initialized - configure settings and backup jobs via the web admin panel, then re-run this command.")
    quit()
  with app.app_context():
    load_config(app)
    start_job(jobtype)
    if jobtype == "Daily-Local":
      daily_local()
    elif jobtype == "Daily-Other":
      daily_other()
    elif jobtype == "Weekly-Local":
      weekly_local()
    elif jobtype == "Weekly-Other":
      weekly_other()

if __name__ == "__main__":
  if len(sys.argv) >= 2:
    if sys.argv[1] == "--help" or sys.argv[1] == "-h":
      show_help()
    elif sys.argv[1] in ("Daily-Local", "Daily-Other", "Weekly-Local", "Weekly-Other"):
      run_job(sys.argv[1])
    else:
      show_help()
  else:
    show_help()
