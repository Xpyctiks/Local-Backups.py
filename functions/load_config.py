import os
import json
import logging
import secrets
from datetime import datetime
from flask import Flask
from db.db import db
from db.database import Settings, BackupJob, User, BACKUP_NAME_PATTERN
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
  with app.app_context():
    db.create_all()
    if fresh:
      migrated = False
      if os.path.exists(variables.CONFIG_FILE):
        migrated = _migrate_legacy_json()
      if not migrated:
        _seed_defaults()
      _seed_admin_user()
      db.session.commit()
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

def _migrate_legacy_json() -> bool:
  #Attempts to migrate the legacy config.json into the database. Returns False (and leaves nothing committed) if the file is invalid.
  try:
    with open(variables.CONFIG_FILE, 'r', encoding='utf8') as file:
      config = json.load(file)
    for key in REQUIRED_LEGACY_KEYS:
      if key not in config:
        print(f"Legacy config.json is missing key '{key}' - skipping automatic migration, default settings will be seeded instead.")
        return False
    settings = Settings(
      id=1,
      telegramToken=(config.get('telegramToken') or '').strip(),
      telegramChat=(config.get('telegramChat') or '').strip(),
      logFolder=(config.get('logFolder') or '').strip(),
      dailyFolder=(config.get('dailyFolder') or '').strip(),
      weeklyFolder=(config.get('weeklyFolder') or '').strip(),
      backupFolder=(config.get('backupFolder') or '').strip(),
      defaultDbHost=(config.get('DefaultDbHost') or '').strip(),
      defaultDbPort=(config.get('DefaultDbPort') or '').strip(),
      defaultDbSocket=(config.get('DefaultDbSocket') or '').strip(),
      defaultDbUser=(config.get('DefaultDbUser') or '').strip(),
      defaultDbPass=(config.get('DefaultDbPass') or '').strip(),
      osUser=(config.get('User') or 'root').strip(),
      osGroup=(config.get('Group') or 'root').strip(),
      sessionKey=secrets.token_hex(32),
      autheliaLogoutUrl="",
    )
    db.session.add(settings)
    migrated_count = 0
    for scope, items_key in (("Local", "LocalServerBackups"), ("Other", "OtherBackups")):
      for item in config.get(items_key, []):
        job = _legacy_item_to_job(item, scope)
        if job is None:
          print(f"Skipping legacy {items_key} item {item!r}: no valid Name/Folder/DB found.")
          continue
        db.session.add(job)
        migrated_count += 1
        print(f"Migrated legacy backup job '{job.name}' ({scope}) from config.json.")
    print(f"Legacy config.json migrated into the database: {migrated_count} backup job(s) created. The original config.json was left untouched on disk as a fallback.")
    return True
  except Exception as msg:
    print(f"Error migrating legacy config.json: {msg}. Default settings will be seeded instead.")
    db.session.rollback()
    return False

def _legacy_item_to_job(item: dict, scope: str):
  name = str(item.get('Name') or '').strip()
  if not name or not BACKUP_NAME_PATTERN.match(name):
    return None
  if item.get('Folder'):
    return BackupJob(name=name, scope=scope, folder=item.get('Folder'))
  if item.get('DB'):
    return BackupJob(
      name=name, scope=scope, db_name=item.get('DB'),
      dbUser=item.get('User') or None, dbHost=item.get('Host') or None,
      dbSocket=item.get('Socket') or None, dbPort=item.get('Port') or None,
      dbPassword=item.get('Password') or None,
    )
  return None

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
    LOG_FILE_NAME=datetime.now().strftime('%d.%m.%Y')
    LOG_FILE=os.path.join(variables.LOG_FOLDER,LOG_FILE_NAME)
    logging.basicConfig(filename=LOG_FILE,level=logging.INFO,format='%(asctime)s - Local-Backups - %(levelname)s - %(message)s',datefmt='%d-%m-%Y %H:%M:%S')
    logging.getLogger("httpx").setLevel(logging.WARNING)
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
