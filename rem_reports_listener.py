#!/usr/local/bin/python3
"""
Two independent run modes live in this one file:
1. Run directly - `./rem_reports_listener.py` (or `python rem_reports_listener.py`):
   daemonizes (classic double-fork) and runs a threaded TCP server that accepts incoming
   job-report connections from other Local-Backups instances, validates each one against the
   RemoteServers table (source IP + personal key must match a row), and records accepted
   reports into RemoteServersStatistics. Pass --foreground to skip daemonizing - required
   under systemd Type=simple, which supervises the process directly and would lose track of
   a self-detached child.
2. Imported by a WSGI server - `gunicorn -c gunicorn_config_listener.py rem_reports_listener:application`:
   serves a small dashboard showing recorded reports by date, plus whether the listener
   daemon (mode 1, quite possibly a separate process/host) is currently running. Login is
   entirely self-contained (own session, own routes) but reads the same User table as the
   rest of the project - if deployed on the same domain as webapp.py, the browser's existing
   session cookie already works here too (both apps sign cookies with the same
   Settings.sessionKey); on a different domain the cookie never arrives, so this app's own
   /login/ page is used, authenticating against the same shared user database.
"""
import os
import sys
import socketserver
import logging
import argparse
from datetime import datetime, timedelta
from flask import request, redirect, session, flash, render_template
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from functions import variables
from functions.load_config import create_app, generate_default_config, load_config
from db.db import db
from db.database import Settings, RemoteServers, RemoteServersStatistics, User

LISTENER_LOG_NAME = "000-reports-listener.log"

app = create_app()
generate_default_config(app)
load_config(app)

def configure_listener_logging() -> None:
  log_file = os.path.join(variables.LOG_FOLDER, LISTENER_LOG_NAME)
  logging.basicConfig(filename=log_file,level=logging.INFO,format='%(asctime)s - Local-Backups-Listener - %(levelname)s - %(message)s',datefmt='%d-%m-%Y %H:%M:%S',force=True)

def listener_is_running() -> bool:
  if not os.path.exists(variables.LISTENER_PID_FILE):
    return False
  try:
    with open(variables.LISTENER_PID_FILE, "r") as f:
      pid = int(f.read().strip())
    return os.path.exists(f"/proc/{pid}")
  except Exception:
    return False

# ---------------------------------------------------------------------------
# TCP daemon (mode 1)
# ---------------------------------------------------------------------------
class ReportHandler(socketserver.BaseRequestHandler):
  def handle(self):
    source_ip = self.client_address[0]
    try:
      chunks = []
      while True:
        chunk = self.request.recv(4096)
        if not chunk:
          break
        chunks.append(chunk)
      raw = b"".join(chunks).decode("utf-8", errors="replace").strip()
    except Exception as msg:
      logging.error(f"rem_reports_listener: failed reading from {source_ip}: {msg}")
      return
    if not raw:
      return
    #Expected wire format: "key,jobtype,message" - split with maxsplit=2 so a comma inside the free-text message (the 3rd field) doesn't get chopped up.
    parts = raw.split(",", 2)
    if len(parts) != 3:
      logging.warning(f"rem_reports_listener: malformed message from {source_ip}: {raw!r}")
      return
    key, jobtype, result = (p.strip() for p in parts)
    with app.app_context():
      sender = RemoteServers.query.filter_by(address=source_ip, personalkey=key).first()
      if not sender:
        logging.warning(f"rem_reports_listener: rejected message from {source_ip} - no RemoteServers row matches this address+key pair. jobtype={jobtype!r}")
        return
      entry = RemoteServersStatistics(name=sender.name, jobtype=jobtype, result=result)
      db.session.add(entry)
      db.session.commit()
      logging.info(f"rem_reports_listener: recorded report from '{sender.name}' ({source_ip}) - jobtype={jobtype}, result={result}")

  def handle_error(self, request, client_address):
    logging.error(f"rem_reports_listener: unhandled error handling connection from {client_address}", exc_info=True)

class ThreadingTCPServerReuse(socketserver.ThreadingMixIn, socketserver.TCPServer):
  allow_reuse_address = True
  daemon_threads = True

def _daemonize() -> None:
  #Classic double-fork daemonization (Stevens' technique). Must run BEFORE anything in this process touches the DB
  if os.fork() > 0:
    os._exit(0)
  os.setsid()
  if os.fork() > 0:
    os._exit(0)
  os.umask(0o027)
  os.chdir("/")
  sys.stdout.flush()
  sys.stderr.flush()
  devnull_fd = os.open(os.devnull, os.O_RDWR)
  os.dup2(devnull_fd, sys.stdin.fileno())
  os.dup2(devnull_fd, sys.stdout.fileno())
  os.dup2(devnull_fd, sys.stderr.fileno())

def run_listener(foreground: bool) -> None:
  if not foreground:
    _daemonize()
    with app.app_context():
      db.engine.dispose()
  configure_listener_logging()
  with app.app_context():
    settings = db.session.get(Settings, 1)
    bind_addr = (settings.reportsListenerBindAddr or "127.0.0.1").strip() if settings else "127.0.0.1"
    try:
      bind_port = int((settings.reportsListenerBindPort or "10555").strip()) if settings else 10555
    except ValueError:
      bind_port = 10555
  os.makedirs(os.path.dirname(variables.LISTENER_PID_FILE) or "/", exist_ok=True)
  with open(variables.LISTENER_PID_FILE, "w") as f:
    f.write(str(os.getpid()))
  logging.info(f"rem_reports_listener: starting, listening on {bind_addr}:{bind_port} (pid={os.getpid()}, foreground={foreground})")
  try:
    server = ThreadingTCPServerReuse((bind_addr, bind_port), ReportHandler)
    server.serve_forever()
  except Exception as msg:
    logging.error(f"rem_reports_listener: fatal error: {msg}")
  finally:
    if os.path.exists(variables.LISTENER_PID_FILE):
      os.remove(variables.LISTENER_PID_FILE)

# ---------------------------------------------------------------------------
# Web dashboard (mode 2, gunicorn) - self-contained auth, shared User table
# ---------------------------------------------------------------------------
application = app
application.config["PERMANENT_SESSION_LIFETIME"] = timedelta(hours=8)
login_manager = LoginManager()
login_manager.login_view = "listener_login_page"
login_manager.init_app(application)

@login_manager.user_loader
def load_user(user_id):
  return db.session.get(User, int(user_id))

@application.route("/login/", methods=["GET"])
def listener_login_page():
  if current_user.is_authenticated:
    return redirect("/")
  return render_template("template-login.html")

@application.route("/login/", methods=["POST"])
def listener_do_login():
  username = (request.form.get("username") or "").strip()
  password = request.form.get("password") or ""
  user = User.query.filter_by(username=username).first()
  if not user or not user.check_password(password):
    flash("Invalid username or password.", "alert alert-danger")
    return redirect("/login/")
  session.clear()
  session.permanent = True
  login_user(user, remember=True, duration=timedelta(hours=8))
  return redirect("/")

@application.route("/logout/", methods=["POST"])
@login_required
def listener_do_logout():
  session.clear()
  logout_user()
  return redirect("/login/")

@application.route("/", methods=["GET"])
@login_required
def listener_dashboard():
  today_str = datetime.now().strftime("%d-%m-%Y")
  date_rows = (
    db.session.query(db.func.strftime("%d-%m-%Y", RemoteServersStatistics.date))
    .distinct()
    .order_by(RemoteServersStatistics.date.desc())
    .all()
  )
  available_dates = [r[0] for r in date_rows if r[0]]
  if today_str not in available_dates:
    available_dates.insert(0, today_str)
  selected_date = (request.args.get("date") or today_str).strip()
  if selected_date not in available_dates:
    selected_date = today_str
  day, month, year = selected_date.split("-")
  range_start = datetime(int(year), int(month), int(day))
  range_end = range_start + timedelta(days=1)
  rows = (
    RemoteServersStatistics.query
    .filter(RemoteServersStatistics.date >= range_start, RemoteServersStatistics.date < range_end)
    .order_by(RemoteServersStatistics.date.desc())
    .all()
  )
  return render_template(
    "template-reports-listener.html",
    rows=rows,
    selected_date=selected_date,
    today_str=today_str,
    available_dates=available_dates,
    listener_running=listener_is_running(),
  )

with application.app_context():
  db.create_all()

if __name__ == "__main__":
  parser = argparse.ArgumentParser(description="Local-Backups remote report listener")
  parser.add_argument("--foreground", action="store_true", help="Do not daemonize - stay attached to the console (use under systemd Type=simple, or for debugging).")
  args = parser.parse_args()
  run_listener(foreground=args.foreground)
