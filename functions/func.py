import os,logging,sys,hashlib
from datetime import datetime
from functions.send_to_telegram import send_to_telegram
from functions import variables

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

def del_pid():
  if os.path.exists(variables.PID_FILE):
    os.remove(variables.PID_FILE)

def start_job(jobtype):
  timestamp=datetime.now().strftime('%H:%M:%S %d.%m.%Y')
  variables.CURR_FOLDER_NAME=datetime.now().strftime('%d.%m.%Y')
  text = f"----------------------------------------{timestamp} Starting {jobtype} backup jobs----------------------------------------"
  print(text)
  logging.info(text)
  send_to_telegram(f"☕{jobtype} backup job started")
  check_pid(jobtype)

def finish_job(jobtype):
  timestamp=datetime.now().strftime('%H:%M:%S %d.%m.%Y')
  text = f"----------------------------------------{timestamp} Finished all {jobtype} backup job-------------------------------------"
  print(text)
  logging.info(text)
  send_to_telegram(f"✅All {jobtype} jobs done.")
  del_pid()
  sys.exit(0)

def interrupt_job(jobtype):
  timestamp=datetime.now().strftime('%H:%M:%S %d.%m.%Y')
  text = f"----------------------------------------{timestamp} Interruption of all {jobtype} backup job-------------------------------------"
  print(text)
  logging.info(text)
  send_to_telegram(f"❌All {jobtype} jobs have been interrupted!")
  del_pid()
  sys.exit(1)

def part_of_day():
  now = datetime.now().hour
  if 2 <= now < 12:
    return "morning"
  else:
    return "evening"

def create_sha256(folder):
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
