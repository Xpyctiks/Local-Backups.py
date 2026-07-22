import os
import click
from db.db import db
from db.database import BackupJob, BACKUP_NAME_PATTERN
from functions.cli_common import app_for_admin

SCOPES = ["Local", "Other"]

def _describe(job: BackupJob) -> str:
  state = "enabled" if job.enabled else "disabled"
  kind = f"folder: {job.folder}" if job.folder else f"db: {job.db_name}"
  return f"[{job.id}] {job.name} ({job.scope}, {state}) - {kind}"

def _check_name(name: str) -> None:
  if not name or not BACKUP_NAME_PATTERN.match(name):
    raise click.ClickException("Name is required and may only contain letters, numbers, spaces, dots, underscores and hyphens.")

@click.group(name="jobs")
def jobs_group():
  """Manage backup jobs (same as the main dashboard)."""

@jobs_group.command(name="list")
@click.option("--scope", type=click.Choice(SCOPES), default=None, help="Only list jobs in this scope.")
def jobs_list(scope):
  """List configured backup jobs."""
  app = app_for_admin()
  with app.app_context():
    query = BackupJob.query
    if scope:
      query = query.filter_by(scope=scope)
    jobs = query.order_by(BackupJob.scope, BackupJob.name).all()
    if not jobs:
      click.echo("No backup jobs configured.")
      return
    for job in jobs:
      click.echo(_describe(job))

@jobs_group.command(name="add-folder")
@click.argument("name")
@click.argument("folder")
@click.option("--scope", type=click.Choice(SCOPES), required=True, help="LocalServerBackups or OtherBackups.")
def jobs_add_folder(name, folder, scope):
  """Add a Folder backup job."""
  _check_name(name)
  folder = folder.strip()
  if not os.path.isdir(folder):
    raise click.ClickException(f"Folder '{folder}' does not exist.")
  app = app_for_admin()
  with app.app_context():
    if any(j.folder is not None for j in BackupJob.query.filter_by(name=name).all()):
      raise click.ClickException(f"A Folder backup job named '{name}' already exists.")
    job = BackupJob(name=name, scope=scope, folder=folder)
    db.session.add(job)
    db.session.commit()
    click.echo(f"Folder backup job '{name}' added ({_describe(job)}).")

@jobs_group.command(name="add-db")
@click.argument("name")
@click.argument("db_name")
@click.option("--scope", type=click.Choice(SCOPES), required=True, help="LocalServerBackups or OtherBackups.")
@click.option("--host", default=None, help="Override the default DB host for this job.")
@click.option("--port", default=None, help="Override the default DB port for this job.")
@click.option("--socket", "sock", default=None, help="Override the default DB socket for this job.")
@click.option("--user", default=None, help="Override the default DB user for this job.")
@click.option("--password", default=None, help="Override the default DB password for this job.")
def jobs_add_db(name, db_name, scope, host, port, sock, user, password):
  """Add a Database backup job. DB_NAME may also be ALL or FETCH."""
  _check_name(name)
  db_name = db_name.strip()
  if not db_name:
    raise click.ClickException("Database name (or ALL / FETCH) is required.")
  app = app_for_admin()
  with app.app_context():
    if any(j.folder is None for j in BackupJob.query.filter_by(name=name).all()):
      raise click.ClickException(f"A Database backup job named '{name}' already exists.")
    job = BackupJob(
      name=name, scope=scope, db_name=db_name,
      dbHost=(host or "").strip() or None,
      dbUser=(user or "").strip() or None,
      dbPassword=(password or "").strip() or None,
      dbSocket=(sock or "").strip() or None,
      dbPort=(port or "").strip() or None,
    )
    db.session.add(job)
    db.session.commit()
    click.echo(f"Database backup job '{name}' added ({_describe(job)}).")

@jobs_group.command(name="edit-db")
@click.argument("job_id", type=int)
@click.option("--db", "db_name", default=None, help="New database name (or ALL / FETCH).")
@click.option("--host", default=None, help="New DB host override.")
@click.option("--port", default=None, help="New DB port override.")
@click.option("--socket", "sock", default=None, help="New DB socket override.")
@click.option("--user", default=None, help="New DB user override.")
@click.option("--password", default=None, help="New DB password override.")
def jobs_edit_db(job_id, db_name, host, port, sock, user, password):
  """Edit the DB connection details of a Database backup job (its name/scope can't be changed here, same as the web UI)."""
  app = app_for_admin()
  with app.app_context():
    job = db.session.get(BackupJob, job_id)
    if not job:
      raise click.ClickException("Backup job not found.")
    if job.folder is not None:
      raise click.ClickException("This backup job is a Folder job, not a Database job.")
    if db_name is not None:
      db_name = db_name.strip()
      if not db_name:
        raise click.ClickException("Database name (or ALL / FETCH) is required.")
      job.db_name = db_name
    if host is not None:
      job.dbHost = host.strip() or None
    if port is not None:
      job.dbPort = port.strip() or None
    if sock is not None:
      job.dbSocket = sock.strip() or None
    if user is not None:
      job.dbUser = user.strip() or None
    if password is not None:
      job.dbPassword = password.strip() or None
    db.session.commit()
    click.echo(f"Database connection details for '{job.name}' updated ({_describe(job)}).")

@jobs_group.command(name="enable")
@click.argument("job_id", type=int)
def jobs_enable(job_id):
  """Enable a backup job."""
  _set_enabled(job_id, True)

@jobs_group.command(name="disable")
@click.argument("job_id", type=int)
def jobs_disable(job_id):
  """Disable a backup job."""
  _set_enabled(job_id, False)

def _set_enabled(job_id: int, enabled: bool) -> None:
  app = app_for_admin()
  with app.app_context():
    job = db.session.get(BackupJob, job_id)
    if not job:
      raise click.ClickException("Backup job not found.")
    job.enabled = enabled
    db.session.commit()
    click.echo(f"Backup job '{job.name}' {'enabled' if enabled else 'disabled'}.")

@jobs_group.command(name="delete")
@click.argument("job_id", type=int)
@click.confirmation_option(prompt="Are you sure you want to delete this backup job?")
def jobs_delete(job_id):
  """Delete a backup job."""
  app = app_for_admin()
  with app.app_context():
    job = db.session.get(BackupJob, job_id)
    if not job:
      raise click.ClickException("Backup job not found.")
    name = job.name
    db.session.delete(job)
    db.session.commit()
    click.echo(f"Backup job '{name}' deleted.")
