import os
import re
from datetime import datetime
from flask import render_template, request, jsonify
from flask_login import login_required
from functions import variables
from pages import pages_bp

MAX_LINES = 2000
DATE_PATTERN = re.compile(r'^\d{2}\.\d{2}\.\d{4}$')

@pages_bp.route("/logs/", methods=["GET"])
@login_required
def logs_page():
  return render_template("template-logs.html")

@pages_bp.route("/logs/api/dates/", methods=["GET"])
@login_required
def logs_api_dates():
  log_folder = variables.LOG_FOLDER
  if not os.path.isdir(log_folder):
    return jsonify({"dates": []})
  files = [f for f in os.listdir(log_folder) if os.path.isfile(os.path.join(log_folder, f)) and DATE_PATTERN.match(f)]
  files.sort(key=lambda f: datetime.strptime(f, "%d.%m.%Y"), reverse=True)
  return jsonify({"dates": files})

@pages_bp.route("/logs/api/", methods=["GET"])
@login_required
def logs_api():
  date = (request.args.get("date") or "").strip()
  if date and not DATE_PATTERN.match(date):
    return jsonify({"error": "Invalid date"}), 400
  log_file_name = date or datetime.now().strftime('%d.%m.%Y')
  log_file = os.path.join(variables.LOG_FOLDER, log_file_name)
  if not os.path.exists(log_file):
    return jsonify({"error": "Log not found", "lines": [], "count": 0}), 404
  with open(log_file, "r", encoding="utf-8", errors="replace") as f:
    lines = f.readlines()
  tail = lines[-MAX_LINES:]
  return jsonify({"lines": tail, "count": len(tail), "total": len(lines)})
