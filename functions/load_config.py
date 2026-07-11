import os
import logging
import secrets
from flask import Flask
from db.db import db
from db.database import Settings, BackupJob, User
from functions import variables
from functions.func import interrupt_job

REQUIRED_LEGACY_KEYS = [
  "telegramToken", "telegramChat", "logFolder", "dailyFolder", "weeklyFolder", "backupFolder", "DefaultDbHost", "DefaultDbPort",
  "DefaultDbSocket", "DefaultDbUser", "DefaultDbPass", "LocalServerBackups", "OtherBackups", "User", "Group"
]

#functions/ is one level below the project root, where templates/ and static/ actually live.
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def create_app() -> Flask:
  app = Flask(
    __name__,
    template_folder=os.path.join(PROJECT_ROOT, "templates"),
    static_folder=os.path.join(PROJECT_ROOT, "static"),
  )
  os.makedirs(variables.CONFIG_DIR, mode=0o770, exist_ok=True)
  app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{variables.DB_FILE}"
  app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
  app.config["SESSION_COOKIE_HTTPONLY"] = True
  app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
  db.init_app(app)
  return app

def generate_default_config(app: Flask) -> bool:
  #Check if the DB file exists. If not - bootstrap it (and migrate legacy config.json if present).
  fresh = not os.path.exists(variables.DB_FILE)
  if fresh:
    os.makedirs(variables.CONFIG_DIR, mode=0o770, exist_ok=True)
    logging.info(f"No DB file exists. Creating the new one!")
  with app.app_context():
    db.create_all()
    if fresh:
      migrated = False
      if not migrated:
        _seed_defaults()
      _seed_admin_user()
      db.session.commit()
      logging.info(f"Kickstart: No DB already exsits! Creating the new one...")
    else:
      logging.info(f"Kickstart: DB already exsits! Using it...")
  return fresh

def _seed_defaults() -> None:
  settings = Settings(
    id=1,
    telegramToken="",
    telegramChat="",
    logFolder=os.path.join(os.path.expanduser(os.getcwd()),'Log'),
    dailyFolder="Daily",
    weeklyFolder="Weekly",
    backupFolder=os.path.join(os.path.expanduser(os.getcwd()),'Backups'),
    defaultDbHost="127.0.0.1",
    defaultDbPort="3306",
    defaultDbSocket="",
    defaultDbUser="root",
    defaultDbPass="123Passw0rd123",
    osUser="root",
    osGroup="root",
    sessionKey=secrets.token_hex(32),
    autheliaLogoutUrl="",
  )
  db.session.add(settings)
  text = f"First launch. Database initialized with default settings at {variables.DB_FILE}. Configure it via the web admin panel, then add backup jobs on the main page."
  print(text)

def _seed_admin_user() -> None:
  password = secrets.token_urlsafe(15)
  admin = User(username="admin")
  admin.set_password(password)
  db.session.add(admin)
  try:
    with open(variables.INITIAL_ADMIN_PASSWORD_FILE, 'w', encoding='utf8') as f:
      f.write(f"username: admin\npassword: {password}\n")
    os.chmod(variables.INITIAL_ADMIN_PASSWORD_FILE, 0o600)
  except Exception as msg:
    print(f"Could not write initial admin password file: {msg}")
  print(f"Default web admin user 'admin' created. Password written to {variables.INITIAL_ADMIN_PASSWORD_FILE} (shown once, save it now): {password}")

def load_config(app: Flask) -> None:
  #Loads Settings + BackupJob rows from the database into functions.variables globals, and refreshes app.config.
  with app.app_context():
    logging.info(f"Kickstart: loading configuration from the existing DB...")
    db.create_all()
    settings = db.session.get(Settings, 1)
    if settings is None:
      text = "Settings row is missing from the database! Can't proceed"
      print(text)
      interrupt_job("Program start")
      return
    variables.TELEGRAM_TOKEN = settings.telegramToken or ""
    variables.TELEGRAM_CHATID = settings.telegramChat or ""
    variables.LOG_FOLDER = settings.logFolder
    if not os.path.exists(variables.LOG_FOLDER):
      os.makedirs(variables.LOG_FOLDER,mode=0o770,exist_ok=True)
      text = f"Created new directory {variables.LOG_FOLDER}"
      print(text)
    logging.basicConfig(filename=os.path.join(variables.LOG_FOLDER,'000-general.log'),level=logging.INFO,format='%(asctime)s - Local-Backups-Web - %(levelname)s - %(message)s',datefmt='%d-%m-%Y %H:%M:%S',force=True)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
    variables.DAILY_FOLDER = settings.dailyFolder
    variables.WEEKLY_FOLDER = settings.weeklyFolder
    variables.BCKP_FOLDER = settings.backupFolder
    if not os.path.exists(variables.BCKP_FOLDER):
      os.makedirs(variables.BCKP_FOLDER,mode=0o770,exist_ok=True)
      text = f"Created new directory {variables.BCKP_FOLDER}"
      print(text)
    variables.BCKP_DEF_DB_HOST = settings.defaultDbHost or ""
    variables.BCKP_DEF_DB_PORT = settings.defaultDbPort or ""
    variables.BCKP_DEF_DB_SOCKET = settings.defaultDbSocket or ""
    variables.BCKP_DEF_DB_USER = settings.defaultDbUser or ""
    variables.BCKP_DEF_DB_PASS = settings.defaultDbPass or ""
    variables.USER = settings.osUser
    variables.GROUP = settings.osGroup
    variables.LOCAL_BCKP_LIST = [_job_to_dict(j) for j in BackupJob.query.filter_by(scope="Local", enabled=True).all()]
    variables.OTHER_BCKP_LIST = [_job_to_dict(j) for j in BackupJob.query.filter_by(scope="Other", enabled=True).all()]
    variables.HOSTNAME = os.uname().nodename
    app.config["SECRET_KEY"] = settings.sessionKey
    app.config["AUTHELIA_LOGOUT_URL"] = settings.autheliaLogoutUrl or ""
    logging.info(f"Kickstart: loading configuration done!")

def _job_to_dict(job: BackupJob) -> dict:
  d = {"Name": job.name}
  if job.folder:
    d["Folder"] = job.folder
  elif job.db_name:
    d["DB"] = job.db_name
    d["User"] = job.dbUser
    d["Host"] = job.dbHost
    d["Socket"] = job.dbSocket
    d["Port"] = job.dbPort
    d["Password"] = job.dbPassword
  return d
