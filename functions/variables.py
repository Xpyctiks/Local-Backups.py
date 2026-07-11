import os

CONFIG_DIR = "/etc/local-backups.py/"
CONFIG_FILE = os.path.join(CONFIG_DIR,"config.json")
DB_FILE = os.path.join(CONFIG_DIR,"local-backups.db")
INITIAL_ADMIN_PASSWORD_FILE = os.path.join(CONFIG_DIR,"initial_admin_password.txt")
PID_FILE = os.path.join("/var/run/","local-backups.pid")
LOCAL_BCKP_LIST = OTHER_BCKP_LIST = []
TELEGRAM_TOKEN = TELEGRAM_CHATID = LOG_FOLDER = BCKP_FOLDER = BCKP_DEF_DB_HOST = BCKP_DEF_DB_PORT = BCKP_DEF_DB_SOCKET = BCKP_DEF_DB_USER = BCKP_DEF_DB_PASS = \
DAILY_FOLDER = WEEKLY_FOLDER = CURR_FOLDER_NAME = USER = GROUP = HOSTNAME = ""
