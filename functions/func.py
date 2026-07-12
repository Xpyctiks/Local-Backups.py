import os
import logging
import sys
import socket
import threading
import hashlib
import pwd
import grp
from datetime import datetime
from functions.send_to_telegram import send_to_telegram
from functions import variables
from db.db import db
from db.database import Settings, RemoteReports

def configure_job_logging() -> None:
  """Called at the start of every daily/weekly job function (daily.py/weekly.py)"""
  log_file = os.path.join(variables.LOG_FOLDER, datetime.now().strftime('%d-%m-%Y')+'.log')
  logging.basicConfig(filename=log_file,level=logging.INFO,format='%(asctime)s - Local-Backups - %(levelname)s - %(message)s',datefmt='%d-%m-%Y %H:%M:%S',force=True)
  logging.getLogger("httpx").setLevel(logging.WARNING)

def _send_remote_report_tcp(address: str, port: int, message: str) -> None:
  try:
    with socket.create_connection((address, port), timeout=5) as sock:
      sock.sendall(message.encode("utf-8"))
    logging.info(f"send_remote_reports(): notified {address}:{port} - {message}")
  except Exception as msg:
    logging.error(f"send_remote_reports(): failed to notify {address}:{port} - {msg}")

def send_remote_reports(jobtype: str,error: str) -> None:
  try:
    settings = db.session.get(Settings, 1)
    if not settings or not settings.remoteReportsKey:
      return
    servers = RemoteReports.query.all()
    if not servers:
      return
    message = f"{settings.remoteReportsKey},{jobtype},{error}"
    threads = []
    for server in servers:
      t = threading.Thread(target=_send_remote_report_tcp, args=(server.address, server.port, message), daemon=True)
      t.start()
      threads.append(t)
    for t in threads:
      t.join(timeout=5)
  except Exception as msg:
    logging.error(f"send_remote_reports(): global error: {msg}")

def check_pid(jobtype: str):
  if os.path.exists(variables.PID_FILE):
    with open(variables.PID_FILE, "r") as f:
      old_pid = int(f.read().strip())        
    if os.path.exists(f"/proc/{old_pid}"):
      print(f"Another copy is running. Can't start new job {jobtype}")
      logging.error(f"Previous copy is running. Can't start new job {jobtype}")
      send_to_telegram(f"Previous copy is running. Can't start new job {jobtype}")
      interrupt_job("General-Job")
  with open(variables.PID_FILE, "w") as f:
    f.write(str(os.getpid()))
    return True

def del_pid() -> None:
  if os.path.exists(variables.PID_FILE):
    os.remove(variables.PID_FILE)

def start_job(jobtype) -> None:
  timestamp=datetime.now().strftime('%H:%M:%S %d.%m.%Y')
  variables.CURR_FOLDER_NAME=datetime.now().strftime('%d.%m.%Y')
  text = f"----------------------------------------{timestamp} Starting {jobtype} backup jobs----------------------------------------"
  print(text)
  logging.info(text)
  send_to_telegram(f"☕{jobtype} backup job started")
  check_pid(jobtype)

def finish_job(jobtype) -> None:
  timestamp=datetime.now().strftime('%H:%M:%S %d.%m.%Y')
  text = f"----------------------------------------{timestamp} Finished all {jobtype} backup job-------------------------------------"
  print(text)
  logging.info(text)
  send_to_telegram(f"✅All {jobtype} jobs done.")
  del_pid()
  sys.exit(0)

def interrupt_job(jobtype) -> None:
  timestamp=datetime.now().strftime('%H:%M:%S %d.%m.%Y')
  text = f"----------------------------------------{timestamp} Interruption of all {jobtype} backup job-------------------------------------"
  print(text)
  logging.info(text)
  send_to_telegram(f"❌All {jobtype} jobs have been interrupted!")
  del_pid()
  sys.exit(1)

def part_of_day() -> str:
  now = datetime.now().hour
  if 2 <= now < 12:
    return "morning"
  else:
    return "evening"

def create_sha256(folder) -> bool:
  try:
    sha256_output_file = os.path.join(folder,"sha256sum.txt")
    sha256_output_data = ""
    files = [f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))]
    for file in files:
      sha256_hash = hashlib.sha256()
      with open(os.path.join(folder,file), "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
          sha256_hash.update(chunk)
      sha256_output_data += sha256_hash.hexdigest()+" "+file+"\n"
    with open(sha256_output_file, "w") as f2:
      f2.write(sha256_output_data)
    text = f"\tSHA256 checksums for {folder} created successfully!"
    print(text)
    logging.info(text)
    return True
  except Exception as msg:
    logging.error(f"create_sha256(): global error: {msg}")
    return False

def chown(path: str) -> bool:
  try:
    uid = variables.USER
    gid = variables.GROUP
    if not isinstance(uid, int):
      uid = pwd.getpwnam(uid).pw_uid
    if not isinstance(gid, int):
      gid = grp.getgrnam(gid).gr_gid
    os.chown(path, uid, gid)
    for dirpath, dirnames, filenames in os.walk(path):
      for d in dirnames:
        os.chown(os.path.join(dirpath, d), uid, gid)
      for f in filenames:
        os.chown(os.path.join(dirpath, f), uid, gid)
    return True
  except Exception as msg:
    logging.error(f"Chown() global error: {msg}")
    return False
