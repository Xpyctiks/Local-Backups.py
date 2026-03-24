import logging,subprocess
from functions.send_to_telegram import send_to_telegram
from functions.func import part_of_day
from functions import variables

def mysql_backup(tofolderIn,nameIn,dbIn,userIn,hostIn,socketIn,portIn,passIn,typeIn):
  text = f"Processing {typeIn} DB backup {nameIn} - DB name {dbIn} - TO folder {tofolderIn}"
  print(text)
  logging.info(text)
  #checking if all necessary default variables for mysql are set
  if any(key in [None, "", "None"] for key in [variables.BCKP_DEF_DB_HOST, variables.BCKP_DEF_DB_USER, variables.BCKP_DEF_DB_PASS]):
    print(f"\tKey is empty!")
  #check what we use: default or personal credentials
  text2=f"\t"
  if hostIn:
    mysqlHost = hostIn
    text2 += f"Using personal host: {hostIn}. "
  else:
    mysqlHost = variables.BCKP_DEF_DB_HOST
  if userIn:
    mysqlUser = userIn
    text2 += f"Using personal user: {userIn}. "
  else:
    mysqlUser = variables.BCKP_DEF_DB_USER
  if passIn:
    mysqlPass = passIn
    text2 += f"Using personal password. "
  else:
    mysqlPass = variables.BCKP_DEF_DB_PASS
  #check first of all for the personal defined parameters Socket and Port
  #if set both at the same time:
  if portIn and socketIn:
    additional = f"-S{socketIn}"
    text = f"\tBoth personal Socket and Port are defined. Taking Socket as high priority."
    print(text)
    logging.info(text)
  #if not set both, trying to switch to default defined values
  elif not portIn and not socketIn:
    #if both default values are not set - sending alert
    if not variables.BCKP_DEF_DB_SOCKET and not variables.BCKP_DEF_DB_PORT:
      text = f"\tNeither default socket nor default port is set. Can't proceed with DB {nameIn} backup"
      print(text)
      logging.info(text)
      send_to_telegram(text)
    elif variables.BCKP_DEF_DB_SOCKET and not variables.BCKP_DEF_DB_PORT:
      additional = f"-S{variables.BCKP_DEF_DB_SOCKET}"
      text2 += f"Using default SOCKET with DB {nameIn} backup "
      print(text2)
      logging.info(text2)
    elif not variables.BCKP_DEF_DB_SOCKET and variables.BCKP_DEF_DB_PORT:
      additional = f"-h{mysqlHost} -P{variables.BCKP_DEF_DB_PORT}"
      text2 += f"Using default PORT with DB {nameIn} backup "
      print(text2)
      logging.info(text2)
  #if set any of two personal values
  elif portIn and not socketIn:
    additional = f"-h{mysqlHost} -P{portIn}"
    text2 += f"Using personal PORT value with DB {nameIn} backup "
    print(text2)
    logging.info(text2)
  elif not portIn and socketIn:
    additional = f"-S{socketIn}"
    text2 += f"Using personal SOCKET value with DB {nameIn} backup "
    print(text2)
    logging.info(text2)
  #now check if ALL selected
  if dbIn == "ALL":
    if (typeIn in ["Daily-Local", "Daily-Other"] and part_of_day() == "morning"):
      cmd = f"mysqldump -u{mysqlUser} -p{mysqlPass} {additional} --single-transaction --quick --all-databases | gzip > {tofolderIn}/All-databases-morning.sql.gz"
    elif (typeIn in ["Daily-Local", "Daily-Other"] and part_of_day() == "evening"):
      cmd = f"mysqldump -u{mysqlUser} -p{mysqlPass} {additional} --single-transaction --quick --all-databases | gzip > {tofolderIn}/All-databases-evening.sql.gz"
    else:
      cmd = f"mysqldump -u{mysqlUser} -p{mysqlPass} {additional} --single-transaction --quick --all-databases | gzip > {tofolderIn}/All-databases.sql.gz"
    result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
    if "error" in str(result):
      text = f"\tSome error while dumping Daily ALL DB backup of {nameIn}. Error: {result.stderr.strip()}"
      logging.error(text)
      print(text)
      send_to_telegram(text)
    text = f"\tDaily ALL DB Local backup of {nameIn} done successfully!"
    print(text)
    logging.info(text)
  #now check if FETCH selected
  elif dbIn == "FETCH":
    cmd = f'mysql -u{mysqlUser} -p{mysqlPass} {additional} -e "SHOW DATABASES;"'
    result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
    databases = result.stdout.strip().split("\n")[1:]
    if len(databases) == 0:
      text = f"No databases found in the server. Can't proceed with FETCH DB backup"
      print(text)
      logging.info(text)
      send_to_telegram(text)
    else:
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
        result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
        if "error" in str(result):
          text = f"Some error while dumping Daily FETCH DB backup of {db}. Error: {result.stderr.strip()}"
          logging.error(text)
          print(text)
          send_to_telegram(text)
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
    result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
    if "error" in str(result):
      text = f"Some error while dumping Weekly DB backup of {nameIn}. Error: {result.stderr.strip()}"
      logging.error(text)
      print(text)
      send_to_telegram(text)
