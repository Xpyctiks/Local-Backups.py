import os
import re
import socket
from datetime import datetime
from flask import render_template, request, jsonify, current_app
from flask_login import login_required
from functions import variables
from pages import pages_bp

MAX_LINES = 2000
GENERAL_LOG_NAME = "000-general.log"
JOB_LOG_PATTERN = re.compile(r'^\d{2}-\d{2}-\d{4}\.log$')
#Anything accepted from the `date` query param must match this allow-list before it's ever
#joined into a filesystem path, otherwise a value like "../../etc/passwd" would be readable.
ALLOWED_LOG_NAME = re.compile(r'^(\d{2}-\d{2}-\d{4}\.log|000-general\.log)$')

@pages_bp.route("/logs/", methods=["GET"])
@login_required
def logs_page():
  return render_template("template-logs.html", hostname=socket.gethostname(),version=current_app.config.get("VERSION",""))

@pages_bp.route("/logs/api/dates/", methods=["GET"])
@login_required
def logs_api_dates():
  log_folder = variables.LOG_FOLDER
  if not os.path.isdir(log_folder):
    return jsonify({"dates": []})
  job_logs = [f for f in os.listdir(log_folder) if os.path.isfile(os.path.join(log_folder, f)) and JOB_LOG_PATTERN.match(f)]
  job_logs.sort(key=lambda f: datetime.strptime(f, "%d-%m-%Y.log"), reverse=True)
  names = job_logs
  if os.path.isfile(os.path.join(log_folder, GENERAL_LOG_NAME)):
    names = [GENERAL_LOG_NAME] + names
  return jsonify({"dates": names})

@pages_bp.route("/logs/api/", methods=["GET"])
@login_required
def logs_api():
  name = (request.args.get("date") or "").strip()
  if not name:
    name = datetime.now().strftime('%d-%m-%Y') + ".log"
  if not ALLOWED_LOG_NAME.match(name):
    return jsonify({"error": "Invalid log name"}), 400
  log_file = os.path.join(variables.LOG_FOLDER, name)
  if not os.path.exists(log_file):
    return jsonify({"error": "Log not found", "lines": [], "count": 0}), 404
  with open(log_file, "r", encoding="utf-8", errors="replace") as f:
    lines = f.readlines()
  tail = lines[-MAX_LINES:]
  return jsonify({"lines": tail, "count": len(tail), "total": len(lines)})
