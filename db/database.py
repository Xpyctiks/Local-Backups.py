import re
from datetime import datetime
from flask_login import UserMixin
from sqlalchemy import CheckConstraint
from werkzeug.security import generate_password_hash, check_password_hash
from db.db import db

BACKUP_NAME_PATTERN = re.compile(r'^[A-Za-z0-9 _.\-]+$')

class Settings(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  telegramToken = db.Column(db.String(128), nullable=True, default="")
  telegramChat = db.Column(db.String(32), nullable=True, default="")
  logFolder = db.Column(db.String(255), nullable=False)
  dailyFolder = db.Column(db.String(255), nullable=False, default="Daily")
  weeklyFolder = db.Column(db.String(255), nullable=False, default="Weekly")
  backupFolder = db.Column(db.String(255), nullable=False)
  defaultDbHost = db.Column(db.String(255), nullable=True, default="127.0.0.1")
  defaultDbPort = db.Column(db.String(16), nullable=True, default="3306")
  defaultDbSocket = db.Column(db.String(255), nullable=True, default="")
  defaultDbUser = db.Column(db.String(128), nullable=True, default="root")
  defaultDbPass = db.Column(db.String(255), nullable=True, default="")
  osUser = db.Column(db.String(64), nullable=False, default="root")
  osGroup = db.Column(db.String(64), nullable=False, default="root")
  sessionKey = db.Column(db.String(128), nullable=False)
  autheliaLogoutUrl = db.Column(db.String(255), nullable=True, default="")

class BackupJob(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(128), unique=True, nullable=False)
  scope = db.Column(db.String(16), nullable=False)
  folder = db.Column(db.String(255), nullable=True)
  db_name = db.Column("db", db.String(128), nullable=True)
  dbHost = db.Column(db.String(255), nullable=True)
  dbUser = db.Column(db.String(128), nullable=True)
  dbPassword = db.Column(db.String(255), nullable=True)
  dbSocket = db.Column(db.String(255), nullable=True)
  dbPort = db.Column(db.String(16), nullable=True)
  enabled = db.Column(db.Boolean, nullable=False, default=True)
  created = db.Column(db.DateTime, default=datetime.now)
  updated = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

  __table_args__ = (
    CheckConstraint(
      "((folder IS NOT NULL) + (db IS NOT NULL)) = 1",
      name="ck_backupjob_exactly_one_of_folder_db"
    ),
    CheckConstraint(
      "scope IN ('Local','Other')",
      name="ck_backupjob_scope"
    ),
  )

class User(UserMixin, db.Model):
  id = db.Column(db.Integer, primary_key=True)
  username = db.Column(db.String(80), unique=True, nullable=False)
  password_hash = db.Column(db.String(255), nullable=False)
  created = db.Column(db.DateTime, default=datetime.now)

  def set_password(self, raw_password: str) -> None:
    self.password_hash = generate_password_hash(raw_password)

  def check_password(self, raw_password: str) -> bool:
    return check_password_hash(self.password_hash, raw_password)
