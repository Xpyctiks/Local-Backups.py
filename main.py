#!/usr/local/bin/python3

import click
from functions.cli_common import app_for_job
from functions.cli_settings import settings_group
from functions.cli_jobs import jobs_group
from functions.cli_remotes import remotes_group
from functions.cli_senders import senders_group
from functions.cli_users import users_group
from functions.load_config import load_config
from functions.daily import daily_local, daily_other
from functions.weekly import weekly_local, weekly_other
from functions.func import start_job

@click.group()
def cli():
  """Local-Backups.py - run scheduled backup jobs (normally via cron), or manage every setting available in the web admin panel from this CLI."""

def _run_job(jobtype: str) -> None:
  app = app_for_job()
  with app.app_context():
    load_config(app)
    start_job(jobtype)
    if jobtype == "Daily-Local":
      daily_local()
    elif jobtype == "Daily-Other":
      daily_other()
    elif jobtype == "Weekly-Local":
      weekly_local()
    elif jobtype == "Weekly-Other":
      weekly_other()

@cli.command(name="Daily-Local")
def daily_local_cmd():
  """Do daily backups of databases for local server only - "LocalServerBackups" part of the config."""
  _run_job("Daily-Local")

@cli.command(name="Daily-Other")
def daily_other_cmd():
  """Do daily backups of any other databases - "OtherBackups" part of the config."""
  _run_job("Daily-Other")

@cli.command(name="Weekly-Local")
def weekly_local_cmd():
  """Do weekly backups of databases and folders for local server only - "LocalServerBackups" part of the config."""
  _run_job("Weekly-Local")

@cli.command(name="Weekly-Other")
def weekly_other_cmd():
  """Do weekly backups of databases and folders for any others - "OtherBackups" part of the config."""
  _run_job("Weekly-Other")

cli.add_command(settings_group)
cli.add_command(jobs_group)
cli.add_command(remotes_group)
cli.add_command(senders_group)
cli.add_command(users_group)

if __name__ == "__main__":
  cli()
