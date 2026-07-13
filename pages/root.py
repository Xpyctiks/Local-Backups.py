import logging
import os
import socket
from flask import render_template, request, redirect, flash
from flask_login import login_required, current_user
from db.db import db
from db.database import BackupJob, BACKUP_NAME_PATTERN
from pages import pages_bp

@pages_bp.route("/", methods=["GET"])
@login_required
def dashboard():
  local_jobs = BackupJob.query.filter_by(scope="Local").order_by(BackupJob.name).all()
  other_jobs = BackupJob.query.filter_by(scope="Other").order_by(BackupJob.name).all()
  return render_template("template-main.html", local_jobs=local_jobs, other_jobs=other_jobs, hostname=socket.gethostname())

@pages_bp.route("/backups/add", methods=["POST"])
@login_required
def backups_add():
  name = (request.form.get("name") or "").strip()
  scope = request.form.get("scope") or ""
  job_type = request.form.get("job_type") or ""
  if scope not in ("Local", "Other"):
    flash("Invalid scope.", "alert alert-danger")
    return redirect("/")
  if not name or not BACKUP_NAME_PATTERN.match(name):
    flash("Name is required and may only contain letters, numbers, spaces, dots, underscores and hyphens.", "alert alert-danger")
    return redirect("/")
  if job_type not in ("folder", "db"):
    flash("Invalid backup type.", "alert alert-danger")
    return redirect("/")
  #Name is only required to be unique per job type - a Folder job and a DB job may share a name.
  same_type_exists = any(
    (existing.folder is not None) == (job_type == "folder")
    for existing in BackupJob.query.filter_by(name=name).all()
  )
  if same_type_exists:
    flash(f"A {'Folder' if job_type == 'folder' else 'Database'} backup job named '{name}' already exists.", "alert alert-danger")
    return redirect("/")
  job = BackupJob(name=name, scope=scope)
  if job_type == "folder":
    folder = (request.form.get("folder") or "").strip()
    if not folder:
      flash("Folder path is required.", "alert alert-danger")
      return redirect("/")
    if not os.path.isdir(folder):
      flash(f"Folder '{folder}' does not exist.", "alert alert-danger")
      return redirect("/")
    job.folder = folder
  else:
    db_name = (request.form.get("db") or "").strip()
    if not db_name:
      flash("Database name (or ALL / FETCH) is required.", "alert alert-danger")
      return redirect("/")
    job.db_name = db_name
    job.dbHost = (request.form.get("dbHost") or "").strip() or None
    job.dbUser = (request.form.get("dbUser") or "").strip() or None
    job.dbPassword = (request.form.get("dbPassword") or "").strip() or None
    job.dbSocket = (request.form.get("dbSocket") or "").strip() or None
    job.dbPort = (request.form.get("dbPort") or "").strip() or None
  db.session.add(job)
  db.session.commit()
  flash(f"Backup job '{name}' added.", "alert alert-success")
  logging.info(f"New job added {job.name} by {current_user.username}")
  return redirect("/")

@pages_bp.route("/backups/<int:job_id>/delete", methods=["POST"])
@login_required
def backups_delete(job_id):
  job = db.session.get(BackupJob, job_id)
  if job:
    db.session.delete(job)
    db.session.commit()
    flash(f"Backup job '{job.name}' deleted.", "alert alert-success")
    logging.info(f"Job {job.name} deleted by {current_user.username}")
  return redirect("/")

@pages_bp.route("/backups/<int:job_id>/toggle", methods=["POST"])
@login_required
def backups_toggle(job_id):
  job = db.session.get(BackupJob, job_id)
  if job:
    job.enabled = not job.enabled
    db.session.commit()
    flash(f"Backup job '{job.name}' {'enabled' if job.enabled else 'disabled'}.", "alert alert-success")
    logging.info(f"Job {job.name} {'enabled' if job.enabled else 'disabled'} by {current_user.username}")
  return redirect("/")
